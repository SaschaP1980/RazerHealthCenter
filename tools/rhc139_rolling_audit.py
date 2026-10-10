#!/usr/bin/env python3
"""RHC-139: canonical 13-section rolling journal and fail-closed Issue closure.

No automatic GitHub Action. Planning is read-only; --apply explicitly requires
a credential with existing Issue-write authority. No extra App/permission,
release dispatch, code version mutation, ZIP publication or gate bypass.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from rhc132_work_preflight import berlin

HEADINGS = (
    "Chat origin", "Work-Path authorization and scope", "Benchmark configuration",
    "Validation plan and coverage", "Measurement ledger",
    "Development Completion attempts", "Candidate Entry", "Candidate attempts",
    "Release", "Final Release Verification", "Performance result",
    "Evidence audit", "Plan-conformance assessment",
)
SHA = re.compile(r"^[0-9a-f]{40}$")
KEY = re.compile(r"^[A-Za-z0-9_-]{1,120}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VERS = re.compile(r"^[0-9]+(?:\.[0-9]+){3}$")
RECORD = re.compile(r"(?m)^- RHC139_EVENT (\{[^\n]*\})$")


def require(ok, msg):
    if not ok:
        raise ValueError("RHC139_AUDIT_BLOCKED: " + msg)


def canonical(body):
    require(isinstance(body, str), "saved canonical comment absent")
    titles = re.findall(r"(?m)^### (.+)$", body)
    require(titles == list(HEADINGS), "exactly 13 canonical singleton headings required")
    for h in ("Last heartbeat", "Local reference (Europe/Berlin)",
              "Original ISO timestamp", "Agent-State", "Issue",
              "Current phase", "Next action"):
        require(re.search(r"(?m)^\*\*" + re.escape(h) + r":\*\* .+$", body)
                is not None, "required Rolling header absent: " + h)
    return True


def _set_line(body, field, value):
    p = re.compile(r"(?m)^\*\*" + re.escape(field) + r":\*\* .+$")
    require(len(p.findall(body)) == 1, "ambiguous canonical header " + field)
    return p.sub(lambda _: "**" + field + ":** " + value, body, count=1)


def _normalize(record):
    require(isinstance(record, dict), "invalid evidence event")
    needed = ("key", "issue", "sha", "status", "run_id", "job_count")
    require(all(k in record for k in needed), "incomplete evidence event")
    require(isinstance(record["key"], str) and KEY.fullmatch(record["key"]),
            "unsafe journal event identity")
    require(type(record["issue"]) is int and record["issue"] > 0,
            "event Issue mismatch")
    require(isinstance(record["sha"], str) and SHA.fullmatch(record["sha"]),
            "event SHA missing")
    require(record["status"] == "success", "no failure/skip accepted as audit PASS")
    require(type(record["run_id"]) is int and record["run_id"] > 0,
            "actual hosted run ID required")
    require(type(record["job_count"]) is int and record["job_count"] > 0,
            "real hosted successful jobs required")
    return {k:record[k] for k in needed}


def render_event(body, record, now):
    canonical(body)
    event = _normalize(record)
    require(isinstance(now, datetime) and now.tzinfo is not None and
            now.utcoffset() is not None, "unknown audit clock")
    # Same event ID may not be assigned different SHA/status/jobs.
    for serialized in RECORD.findall(body):
        old = json.loads(serialized)
        if old.get("key") == event["key"]:
            require(old == event, "conflicting persistent event key")
            return body
    timestamp = now.astimezone(timezone.utc)
    iso = timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    body = _set_line(body, "Last heartbeat",
                     timestamp.strftime("%Y-%m-%d at %H:%M:%S UTC"))
    body = _set_line(body, "Local reference (Europe/Berlin)", berlin(timestamp))
    body = _set_line(body, "Original ISO timestamp", chr(96) + iso + chr(96))
    # Insert ONLY inside the existing Evidence audit section.
    insertion = "- RHC139_EVENT " + json.dumps(
        event, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n"
    tag = "### Plan-conformance assessment"
    require(body.count(tag) == 1, "missing final canonical section")
    body = body.replace(tag, insertion + "\n" + tag, 1)
    canonical(body)
    return body


def _jobs(gateway, rid, count, sha, event, name_fragments, categories):
    run = gateway.get_run(rid)
    require(type(run.get("id")) is int and run["id"] == rid, "run ID mismatch")
    require(run.get("head_sha") == sha and run.get("event") == event,
            "wrong run SHA/event")
    require(run.get("status") == "completed" and
            run.get("conclusion") == "success", "run not completed success")
    name = str(run.get("name", "")).lower()
    require(all(term.lower() in name for term in name_fragments),
            "wrong workflow identity")
    jobs = gateway.get_jobs(rid)
    require(isinstance(jobs, list) and len(jobs) == count,
            "missing/zero/skipped actual hosted jobs")
    require(len({x.get("id") for x in jobs}) == len(jobs)
            and all(type(x.get("id")) is int and x["id"] > 0
                    and x.get("status") == "completed"
                    and x.get("conclusion") == "success" for x in jobs),
            "job identities/statuses not all genuine successful")
    labels = [str(x.get("name","")).lower() for x in jobs]
    require(all(any(cat.lower() in name for name in labels)
                for cat in categories), "actual native OS/aggregate job missing")
    return count


def verify_acceptance(gateway, proof):
    require(isinstance(proof, dict), "proof missing")
    issue = proof.get("issue")
    require(type(issue) is int and issue > 0, "Issue number missing")
    mode = proof.get("mode")
    require(mode in ("nonpublishing", "release"), "unknown closure mode")
    sha_keys = ("work_sha","base_sha","merged_sha")
    require(all(isinstance(proof.get(k), str) and SHA.fullmatch(proof[k])
                for k in sha_keys), "missing frozen Work/base/merged SHA")
    pr_num = proof.get("pr")
    require(type(pr_num) is int and pr_num > 0, "specific merged PR required")
    pr = gateway.get_pr(pr_num)
    require(pr.get("number") == pr_num and pr.get("merged") is True
            and pr.get("state") == "closed"
            and pr.get("merge_commit_sha") == proof["merged_sha"],
            "PR not exact merged commit")
    require((pr.get("base") or {}).get("sha") == proof["base_sha"]
            and (pr.get("head") or {}).get("sha") ==
            (proof.get("stage_sha") if mode == "release" else proof["work_sha"]),
            "PR base/head SHA mismatched")
    require(gateway.get_main_sha() == proof["merged_sha"], "main not merged source")
    require(gateway.get_merge_parents(proof["merged_sha"]) ==
            [proof["base_sha"], (proof.get("stage_sha")
                                if mode == "release" else proof["work_sha"])],
            "exact two-parent merge ancestry absent")
    runs = proof.get("run_ids")
    require(isinstance(runs, dict), "no authorized run mapping")
    if mode == "nonpublishing":
        expected = {
            "work": (3,proof["work_sha"],"push",["Infrastructure"],["linux","windows","artifact"]),
            "pr_infra": (3,proof["work_sha"],"pull_request",["Infrastructure"],["linux","windows","artifact"]),
            "pr_source": (2,proof["work_sha"],"pull_request",["Source Intake"],["linux","windows"]),
            "cleanup": (1,proof["merged_sha"],"workflow_run",["Branch Cleanup"],["cleanup"]),
        }
        require(gateway.get_work_branch(f"work/RHC-{issue}") is None,
                "unmerged Work ref still live")
    else:
        require(all(isinstance(proof.get(k),str) and SHA.fullmatch(proof[k])
                    for k in ("stage_sha","source_sha")) and
                isinstance(proof.get("version"),str) and
                VERS.fullmatch(proof["version"]), "release proof incomplete")
        expected={
            "work":(3,proof["work_sha"],"push",["Infrastructure"],["linux","windows","artifact"]),
            "candidate":(3,proof["source_sha"],"workflow_dispatch",["Candidate"],["linux","windows","aggregate"]),
            "publisher":(4,proof["source_sha"],"workflow_dispatch",["Interim"],["linux","windows","stage","final"]),
            "downloads":(1,proof["stage_sha"],"workflow_dispatch",["Downloads"],[]),
            "rhc102":(3,proof["merged_sha"],"workflow_dispatch",["Postrelease"],["linux","windows","aggregate"]),
        }
        latest=gateway.get_latest()
        require(latest.get("version")==proof["version"] and
                latest.get("sourceSha")==proof["source_sha"] and
                isinstance(latest.get("sha256"),str) and
                SHA.fullmatch(latest["sha256"]) and
                type(latest.get("size")) is int and latest["size"]>0,
                "public latest ZIP/hash/source not verified")
        require(gateway.get_tag("v"+proof["version"])==proof["source_sha"],
                "immutable version source tag mismatched")
    require(set(runs)==set(expected), "missing/unexpected required gate")
    result=[]
    for key,(count,sha,event,parts,cats) in expected.items():
        run_id=runs[key]
        require(type(run_id) is int and run_id>0, "invalid required run ID")
        _jobs(gateway,run_id,count,sha,event,parts,cats)
        result.append({"key":key+"-"+str(run_id),"issue":issue,
                       "sha":sha,"status":"success","run_id":run_id,
                       "job_count":count})
    return result


def finalize(gateway, proof, *, now, apply=False):
    issue_id = proof.get("issue")
    comment_id = proof.get("comment_id")
    require(type(comment_id) is int and comment_id>0, "canonical comment ID missing")
    issue = gateway.get_issue(issue_id)
    require(issue.get("number")==issue_id and issue.get("state")=="open",
            "Issue auto-closed, wrong identity or no permission")
    before=gateway.get_comment(comment_id)
    require(before.get("id")==comment_id and
            f"issues/{issue_id}" in before.get("body",""), "wrong saved comment")
    canonical(before["body"])
    events=verify_acceptance(gateway,proof)
    # Optimistic double read: GitHub Issue comments API has no guaranteed
    # if-match CAS semantics. A concurrent mutation must not be ignored.
    again=gateway.get_comment(comment_id)
    require(before.get("body")==again.get("body") and
            before.get("updated_at")==again.get("updated_at"),
            "concurrent Rolling Comment revision changed")
    updated=before["body"]
    for event in events:
        updated=render_event(updated,event,now)
    # Never write a terminal COMPLETED before the Issue close actually
    # succeeds. An API error must leave visibly pending evidence, not a
    # false-GREEN finished canonical comment.
    updated=_set_line(updated,"Agent-State","WAITING_FOR_GITHUB")
    updated=_set_line(updated,"Current phase","GATES VERIFIED — waiting for real Issue close")
    updated=_set_line(updated,"Next action","Read back canonical comment and close exact Issue; then mark COMPLETED")
    canonical(updated)
    result={"status":"READY_PLAN_ONLY", "issue":issue_id, "comment_id":comment_id,
            "mode":proof["mode"],"run_count":len(events)}
    if not apply:
        return result
    # One more exact-check immediately before first remote write.
    final_pre=gateway.get_comment(comment_id)
    require(final_pre.get("body")==before["body"] and
            final_pre.get("updated_at")==before.get("updated_at"),
            "comment changed before patch")
    gateway.update_comment(comment_id,updated)
    actual=gateway.get_comment(comment_id)
    require(actual.get("body")==updated, "saved Rolling Comment readback disagrees")
    canonical(actual["body"])
    require(gateway.get_issue(issue_id).get("state")=="open", "Issue state changed")
    require(gateway.get_main_sha()==proof["merged_sha"], "main moved during audit")
    gateway.update_issue(issue_id,"closed")
    closed=gateway.get_issue(issue_id)
    require(closed.get("state")=="closed" and
            closed.get("state_reason")=="completed", "Issue close state not verified")
    closed_at=closed.get("closed_at")
    require(isinstance(closed_at,str) and bool(closed_at),
            "GitHub did not return exact Issue closure clock")
    try:
        close_instant=datetime.fromisoformat(
            closed_at.replace("Z","+00:00")).astimezone(timezone.utc)
    except (TypeError,ValueError) as exc:
        raise ValueError("invalid saved Issue closure timestamp") from exc
    require(gateway.get_comment(comment_id).get("body")==updated,
            "rolling comment changed after Issue close")
    complete=_set_line(updated,"Agent-State","COMPLETED")
    complete=_set_line(complete,"Current phase",
                       "COMPLETED — GitHub Issue CLOSED/completed and independently read back")
    complete=_set_line(complete,"Next action","No pending action for completed Issue")
    complete=_set_line(complete,"Last heartbeat",
                       close_instant.strftime("%Y-%m-%d at %H:%M:%S UTC"))
    complete=_set_line(complete,"Local reference (Europe/Berlin)",
                       berlin(close_instant))
    iso=close_instant.isoformat(timespec="milliseconds").replace("+00:00","Z")
    complete=_set_line(complete,"Original ISO timestamp",chr(96)+iso+chr(96))
    closure={"issue":issue_id,"closed_at":closed_at,
             "merge_sha":proof["merged_sha"],"status":"completed"}
    require(complete.count("### Plan-conformance assessment")==1,
            "missing final canonical heading")
    complete=complete.replace("### Plan-conformance assessment",
            "- RHC139_ISSUE_CLOSED "+json.dumps(closure,sort_keys=True)+"\\n\\n"+
            "### Plan-conformance assessment",1)
    canonical(complete)
    gateway.update_comment(comment_id,complete)
    require(gateway.get_comment(comment_id).get("body")==complete,
            "final CLOSED/completed Rolling Comment readback failed")
    return dict(result,status="COMPLETED",closed_at=closed_at)



def record_verified_event(gateway, comment_id, record, *, now, apply=False):
    """Incremental append-only journal; no Issue close, no release authority.

    Every event is checked against a *real* GitHub completed-success run with
    the exact SHA and actual hosted jobs. Idempotent replay is a no-op;
    changed evidence with the same event key always blocks.
    """
    event = _normalize(record)
    issue = gateway.get_issue(event["issue"])
    require(issue.get("number") == event["issue"] and
            issue.get("state") == "open", "event Issue not open or mismatched")
    saved = gateway.get_comment(comment_id)
    require(saved.get("id") == comment_id and
            f"issues/{event['issue']}" in saved.get("body", ""),
            "wrong persisted Issue Rolling Comment")
    canonical(saved["body"])
    _jobs(gateway,event["run_id"],event["job_count"],event["sha"],
          gateway.get_run(event["run_id"]).get("event"),[],[])
    before = gateway.get_comment(comment_id)
    require(saved.get("body")==before.get("body") and
            saved.get("updated_at")==before.get("updated_at"),
            "concurrent Rolling Comment update")
    rendered = render_event(saved["body"],event,now)
    if rendered == saved["body"]:
        return {"status":"ALREADY_RECORDED","event_key":event["key"]}
    if not apply:
        return {"status":"READY_PLAN_ONLY","event_key":event["key"]}
    fresh = gateway.get_comment(comment_id)
    require(fresh.get("body")==saved["body"] and
            fresh.get("updated_at")==saved.get("updated_at"),
            "journal changed before saved update")
    gateway.update_comment(comment_id,rendered)
    readback = gateway.get_comment(comment_id)
    require(readback.get("body")==rendered,
            "persisted incremental journal readback mismatch")
    canonical(readback["body"])
    return {"status":"RECORDED","event_key":event["key"]}


class GitHubGateway:
    """Explicitly provided existing gh auth, no new App/token and no dispatch."""
    def __init__(self,repository):
        require(isinstance(repository,str) and REPO.fullmatch(repository),
                "invalid GitHub owner/repo")
        self.repo=repository
    def api(self,verb,path,data=None,allow404=False):
        require(verb in ("GET","PATCH"), "unapproved GitHub verb")
        require(re.fullmatch(r"[A-Za-z0-9/?=&_.-]+",path) is not None,
                "unapproved API path")
        cmd=["gh","api","-X",verb,f"repos/{self.repo}/{path}"]
        if data is not None:
            cmd+=["--input","-"]
        r=subprocess.run(cmd,input=json.dumps(data) if data is not None else None,
                         capture_output=True,text=True,timeout=45)
        if r.returncode:
            if allow404 and "404" in r.stderr:
                return None
            raise ValueError("GitHub API evidence/readback unavailable")
        return json.loads(r.stdout)
    def get_issue(self,n):return self.api("GET",f"issues/{n}")
    def get_comment(self,n):return self.api("GET",f"issues/comments/{n}")
    def get_run(self,n):return self.api("GET",f"actions/runs/{n}")
    def get_pr(self,n):return self.api("GET",f"pulls/{n}")
    def get_main_sha(self):return self.api("GET","git/ref/heads/main")["object"]["sha"]
    def get_merge_parents(self,sha):
        return [x["sha"] for x in self.api("GET",f"git/commits/{sha}")["parents"]]
    def get_work_branch(self,ref):
        x=self.api("GET",f"git/ref/heads/{ref}",allow404=True)
        return None if x is None else x["object"]["sha"]
    def get_jobs(self,n):
        page,out=1,[]
        while page<=10:
            response=self.api("GET",f"actions/runs/{n}/jobs?per_page=100&page={page}")
            require(isinstance(response.get("jobs"),list),"job page unavailable")
            out+=response["jobs"]
            if len(response["jobs"])<100:
                require(response.get("total_count")==len(out),
                        "truncated job count")
                break
            page+=1
        require(page<=10,"job pagination truncated")
        return out
    def get_latest(self):
        blob=self.api("GET","contents/downloads/latest.json?ref=main")
        require(blob.get("encoding")=="base64","latest JSON content unavailable")
        return json.loads(base64.b64decode(blob["content"]).decode("utf-8"))
    def get_tag(self,name):
        return self.api("GET",f"git/ref/tags/{name}")["object"]["sha"]
    def update_comment(self,n,body):
        return self.api("PATCH",f"issues/comments/{n}",{"body":body})
    def update_issue(self,n,state):
        return self.api("PATCH",f"issues/{n}",
                        {"state":state,"state_reason":"completed"})


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixture",type=Path,help="offline proof+snapshot, plan only")
    ap.add_argument("--repository")
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--proof",type=Path,
                       help="complete Issue closure proof with exact hosted run IDs")
    group.add_argument("--record-json",type=Path,
                       help="one incremental already-hosted event; no Issue close")
    ap.add_argument("--comment-id",type=int,
                    help="required for --record-json")
    ap.add_argument("--apply",action="store_true",
                    help="EXPLICIT verified Issue comment PATCH/close; no product publication")
    args=ap.parse_args(argv)
    try:
        now=datetime.now(timezone.utc)
        if args.fixture:
            require(not args.apply,"offline fixture cannot mutate GitHub")
            print("RHC139_FIXTURE_NOT_VERIFIED_NO_GITHUB_WRITES")
            return 0
        require(bool(args.repository),"existing authenticated GitHub repo required")
        gateway=GitHubGateway(args.repository)
        if args.record_json:
            require(type(args.comment_id) is int and args.comment_id>0,
                    "comment ID required for incremental record")
            record=json.loads(args.record_json.read_text(encoding="utf-8"))
            result=record_verified_event(gateway,args.comment_id,record,
                                         now=now,apply=args.apply)
        else:
            proof=json.loads(args.proof.read_text(encoding="utf-8"))
            result=finalize(gateway,proof,now=now,apply=args.apply)
        print("RHC139_AUDIT="+json.dumps(result,sort_keys=True))
        return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError,
            subprocess.TimeoutExpired):
        print("RHC139_AUDIT_BLOCKED_NOT_VERIFIED — no automatic replay",file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(main())
