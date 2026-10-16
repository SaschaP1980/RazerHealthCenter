#!/usr/bin/env python3
"""RHC-212: nonpublishing, GET-only, evidence-classified release timing audit.

Client tool/ref observations are optional; GitHub does NOT timestamp ref creation.
Historical data never gains a synthetic first-tool, ref-created or p95 value.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = "RHC190_E2E_TIMELINE_V1"
CLIENT = "RHC190_CLIENT_TOOL_OBSERVATION_V1"
REPO = "SaschaP1980/RazerHealthCenter"
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_CLIENT_AGE_SECONDS = 86400

def need(ok, reason):
    if not ok:
        raise ValueError("RHC190_E2E_BLOCKED: " + reason)

def dt(value):
    if value is None:
        return None
    need(isinstance(value, str) and bool(re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|\+00:00)", value)),
        "timestamp is not an exact UTC ISO 8601 instant")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("RHC190_E2E_BLOCKED: invalid UTC time") from exc
    need(result.utcoffset().total_seconds() == 0, "non-UTC offset")
    return result.astimezone(timezone.utc)

def span(a, b):
    x, y = dt(a), dt(b)
    if x is None or y is None or y < x:
        return None
    return round((y-x).total_seconds(), 3)

def secure_run(run, sha, *, event, path):
    need(isinstance(run, dict) and type(run.get("id")) is int and run["id"] > 0,
         "workflow run identity missing")
    need(run.get("head_sha") == sha and run.get("event") == event and
         run.get("status") == "completed" and run.get("conclusion") == "success" and
         type(run.get("run_attempt", 1)) is int and run.get("run_attempt", 1) > 0,
         "real exact-SHA completed-success workflow run required")
    need(run.get("path") == path, "unexpected exact workflow definition path")
    need(dt(run.get("created_at")) is not None and dt(run.get("updated_at")) is not None and
         span(run["created_at"],run["updated_at"]) is not None,
         "workflow creation/update clock unverified")

def secure_jobs(page, run, expected):
    need(isinstance(page, dict) and page.get("total_count") == expected and
         isinstance(page.get("jobs"), list) and len(page["jobs"]) == expected,
         "real hosted jobs missing, skipped or truncated")
    ids=set()
    for j in page["jobs"]:
        need(isinstance(j, dict) and type(j.get("id")) is int and j["id"] > 0 and
             j["id"] not in ids and j.get("run_id") in (None, run["id"]) and
             j.get("head_sha",run["head_sha"]) == run["head_sha"] and
             j.get("status") == "completed" and j.get("conclusion") == "success" and
             type(j.get("run_attempt",run.get("run_attempt",1))) is int and
             j.get("run_attempt",run.get("run_attempt",1)) == run.get("run_attempt",1) and
             dt(j.get("completed_at")) is not None,
             "hosted job failed, foreign, duplicate, missing completion or stale attempt")
        ids.add(j["id"])
    names=[str(j.get("name","")) for j in page["jobs"]]
    need(len(set(names))==expected and all(names), "ambiguous hosted job roles")

def client_values(raw, *, issue, candidate_sha, ci_time):
    empty = dict(first_tool_utc=None, ref_write_start_utc=None,
                 ref_write_ack_utc=None, ref_write_duration_ms=None,
                 first_tool_to_ci_seconds=None, ref_to_ci_lower_seconds=None,
                 ref_to_ci_upper_seconds=None, provenance="NOT_SUPPLIED",
                 kpi_first_tool_120s="NOT_VERIFIED",
                 kpi_ref_to_ci_45s="NOT_VERIFIED")
    if raw is None:
        return empty
    need(isinstance(raw,dict) and raw.get("schema")==CLIENT and
         raw.get("issue")==issue and raw.get("candidate_sha")==candidate_sha,
         "client observation wrong schema/issue/SHA")
    need(set(raw).issubset({"schema","issue","candidate_sha","first_tool_utc",
          "ref_write_start_utc","ref_write_ack_utc","ref_write_duration_ms",
          "capture_method"}), "client observation includes unapproved fields")
    need(raw.get("capture_method")=="CLIENT_INSTRUMENTED_TOOL_ENTRY_AND_REF_WRITE_BRACKET",
         "first tool timestamp not attested by capture method")
    first=raw.get("first_tool_utc")
    ref_start=raw.get("ref_write_start_utc")
    ref_ack=raw.get("ref_write_ack_utc")
    need(first is not None and ref_start is not None and ref_ack is not None,
         "incomplete client timing bracket")
    for x in (first,ref_start,ref_ack):
        dt(x)
    need(span(first,ref_start) is not None and span(ref_start,ref_ack) is not None and
         span(first,ref_ack) <= MAX_CLIENT_AGE_SECONDS,
         "client clock order invalid")
    ms=raw.get("ref_write_duration_ms")
    need(type(ms) in (int,float) and 0 <= ms <= 120000 and
         abs(ms/1000-span(ref_start,ref_ack)) <= 2,
         "monotonic ref duration disagrees with UTC bracket")
    # Cross-host UTC offsets cannot be attested with the supplied client clock.
    # Keep observations separate, even if numbers look below the KPI thresholds.
    lower=span(ref_ack,ci_time)
    upper=span(ref_start,ci_time)
    return dict(first_tool_utc=first,ref_write_start_utc=ref_start,
        ref_write_ack_utc=ref_ack,ref_write_duration_ms=ms,
        first_tool_to_ci_seconds=span(first,ci_time),
        ref_to_ci_lower_seconds=lower,ref_to_ci_upper_seconds=upper,
        provenance="CLIENT_OBSERVED_NOT_INDEPENDENTLY_CLOCK_SYNCED",
        kpi_first_tool_120s="NOT_VERIFIED_CLOCK_DOMAIN",
        kpi_ref_to_ci_45s="NOT_VERIFIED_REF_INSTANT_AND_CLOCK_DOMAIN")

def build_report(raw):
    need(isinstance(raw,dict) and raw.get("repository")==REPO and
         type(raw.get("issue_number")) is int and raw["issue_number"]>0 and
         isinstance(raw.get("candidate_sha"),str) and SHA.fullmatch(raw["candidate_sha"]) and
         isinstance(raw.get("main_sha"),str) and SHA.fullmatch(raw["main_sha"]),
         "invalid repository / issue / frozen SHAs")
    n,sha,main=raw["issue_number"],raw["candidate_sha"],raw["main_sha"]
    issue=raw.get("issue")
    need(isinstance(issue,dict) and issue.get("number")==n and
         issue.get("title","").startswith("[RHC-"+str(n)+"] ") and
         "pull_request" not in issue, "issue number/identity mismatch")
    opened=issue.get("created_at")
    need(dt(opened) is not None,"Issue server creation timestamp absent")
    candidate,publisher,verifier=(raw.get(key) for key in ("candidate","publisher","rhc102"))
    secure_run(candidate,sha,event="push",path=".github/workflows/rhc-candidate-preflight.yml")
    secure_run(publisher,sha,event="workflow_dispatch",path=".github/workflows/rhc-reusable-interim-release.yml")
    secure_run(verifier,main,event="workflow_dispatch",
               path=".github/workflows/rhc-postrelease-verification.yml")
    for key,run,count in (("candidate_jobs",candidate,3),("publisher_jobs",publisher,4),
                          ("rhc102_jobs",verifier,3)):
        secure_jobs(raw.get(key),run,count)
    pr=raw.get("pr")
    need(isinstance(pr,dict) and pr.get("merged") is True and
         pr.get("state")=="closed" and pr.get("merge_commit_sha")==main and
         pr.get("base",{}).get("ref")=="main" and
         type(pr.get("number")) is int and pr["number"]>0 and
         dt(pr.get("merged_at")) is not None,
         "wrong unmerged source+downloads PR or merged main SHA")
    need(span(opened,candidate["created_at"]) is not None and
         span(opened,pr["merged_at"]) is not None and
         span(opened,verifier["created_at"]) is not None and
         span(pr["merged_at"],verifier["updated_at"]) is not None,
         "impossible Issue/CI/merge/verifier chronology")
    # Run.updated_at may include metadata edits: not proof of exact terminal moment.
    # Last actual independent hosted verifier job is a better lower bound for success.
    finish=max(j["completed_at"] for j in raw["rhc102_jobs"]["jobs"])
    need(span(verifier["created_at"],finish) is not None and
         span(pr["merged_at"],finish) is not None,
         "verifier has no consistent hosted-job terminal time")
    closed=issue.get("closed_at")
    if closed is not None:
        need(issue.get("state")=="closed" and span(opened,closed) is not None and
             span(finish,closed) is not None,
             "Issue closure not actually later than public verification")
    else:
        need(issue.get("state")=="open","Issue open/closed state inconsistent")
    client=client_values(raw.get("client_observation"),issue=n,
                         candidate_sha=sha,ci_time=candidate["created_at"])
    return dict(schema=SCHEMA,scope="READ_ONLY_NONPUBLISHING_AUDIT",
        issue=n,candidate_sha=sha,main_sha=main,
        workflow_ids={"candidate":candidate["id"],"publisher":publisher["id"],
                      "rhc102":verifier["id"]},release_pr=pr["number"],
        server_times={"issue_created_utc":opened,"candidate_ci_created_utc":candidate["created_at"],
                      "candidate_ci_observed_updated_utc":candidate["updated_at"],
                      "pr_merged_utc":pr["merged_at"],"rhc102_run_observed_updated_utc":verifier["updated_at"],
                      "rhc102_last_hosted_job_completed_utc":finish,"issue_closed_utc":closed},
        server_metrics={"issue_to_ci_seconds":span(opened,candidate["created_at"]),
            "issue_to_pr_merge_seconds":span(opened,pr["merged_at"]),
            "issue_to_verifier_last_job_seconds":span(opened,finish),
            "issue_to_verifier_run_updated_seconds":span(opened,verifier["updated_at"]),
            "issue_to_close_seconds":span(opened,closed),
            "verifier_last_job_to_issue_close_seconds":span(finish,closed)},
        client_observation=client,
        actual_ref_created_utc=None,
        actual_ref_created_provenance="NOT_AVAILABLE_IN_GITHUB_REST",
        original_first_tool_to_ci_kpi="NOT_VERIFIED" if raw.get("client_observation") is None else
           "CLIENT_ONLY_CLOCK_SYNC_NOT_VERIFIED",
        p95_seconds=None,
        public_verification="PASS_3_REAL_HOSTED_JOBS_GITHUB_SERVER",
        runtime_hardware_signing_rollback="NOT_APPLICABLE_NO_HARDWARE_ATTESTATION")

def _get(repo,path):
    need(repo==REPO and re.fullmatch(
        r"(?:issues/[1-9]\d*|actions/runs/[1-9]\d*(?:/jobs\?per_page=100)?|pulls/[1-9]\d*)",path),
         "API route not on allowlist")
    need(bool(os.environ.get("GH_TOKEN")),"no scoped token for GET")
    result=subprocess.run(["gh","api","--method","GET","repos/"+repo+"/"+path],
                          capture_output=True,text=True,timeout=25,check=False)
    need(result.returncode==0,"authenticated API readback failed")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError("RHC190_E2E_BLOCKED: invalid API JSON") from exc

def live_fixture(repo,n,sha,main,candidate,publisher,verifier,pr):
    args={"repository":repo,"issue_number":n,"candidate_sha":sha,"main_sha":main,
          "issue":_get(repo,"issues/"+str(n)),"pr":_get(repo,"pulls/"+str(pr))}
    for name,id_ in (("candidate",candidate),("publisher",publisher),("rhc102",verifier)):
        args[name]=_get(repo,"actions/runs/"+str(id_))
        args[name+"_jobs"]=_get(repo,"actions/runs/"+str(id_)+"/jobs?per_page=100")
    return args

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture",help="audited offline fixture JSON, never an authoritative live run")
    p.add_argument("--repository",default=REPO)
    p.add_argument("--issue",type=int)
    p.add_argument("--candidate-sha")
    p.add_argument("--main-sha")
    p.add_argument("--candidate-run",type=int)
    p.add_argument("--publisher-run",type=int)
    p.add_argument("--rhc102-run",type=int)
    p.add_argument("--pr",type=int)
    p.add_argument("--client-observation",help="optional genuine first-tool/ref-write client JSON")
    p.add_argument("--out",required=True)
    args=p.parse_args(argv)
    try:
        if args.fixture:
            need(not any(x is not None for x in
                (args.issue,args.candidate_sha,args.main_sha,args.candidate_run,
                 args.publisher_run,args.rhc102_run,args.pr)),"mixed fixture/live mode")
            raw=json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        else:
            need(args.repository==REPO and
                 all(x is not None for x in (args.issue,args.candidate_sha,
                     args.main_sha,args.candidate_run,args.publisher_run,args.rhc102_run,args.pr)) and
                 SHA.fullmatch(args.candidate_sha or "") and
                 SHA.fullmatch(args.main_sha or ""), "incomplete live identifier set")
            raw=live_fixture(args.repository,args.issue,args.candidate_sha,args.main_sha,
                             args.candidate_run,args.publisher_run,args.rhc102_run,args.pr)
        if args.client_observation:
            need("client_observation" not in raw,"duplicate observer injection")
            raw["client_observation"]=json.loads(Path(args.client_observation).read_text(encoding="utf-8"))
        report=build_report(raw)
        out=Path(args.out)
        need(out.suffix==".json" and not out.exists(),"refuse unsafe output overwrite")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print("RHC190_E2E_AUDIT=PASS_EVIDENCE_CLASSIFIED issue="+str(report["issue"]) +
              " first_tool="+report["original_first_tool_to_ci_kpi"]+
              " ref_creation=NOT_VERIFIED")
        return 0
    except (ValueError,TypeError,KeyError,OSError,subprocess.TimeoutExpired):
        print("RHC190_E2E_AUDIT=BLOCKED_NOT_VERIFIED",file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())
