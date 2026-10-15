#!/usr/bin/env python3
"""RHC-202: fail-closed aggregation of 3 genuine hosted read-only preflight samples."""
import argparse
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys

SCHEMA="RHC190_PHASE_D_PREFLIGHT_V1"
EXPECTED=("readonly-preflight-1","readonly-preflight-2","readonly-preflight-3")
SHA=re.compile(r"[0-9a-f]{40}\Z")


def need(ok,why):
    if not ok:
        raise ValueError("RHC190_PHASE_D_AGGREGATE_BLOCKED: "+why)


def require_hosted_jobs(page):
    need(isinstance(page,dict) and page.get("total_count")==4 and
         isinstance(page.get("jobs"),list) and len(page["jobs"])==4,
         "expected 3 real independent probe jobs and 1 aggregator")
    jobs=page["jobs"]
    need(len({x.get("id") for x in jobs if isinstance(x,dict)})==4,
         "duplicated hosted job identity")
    for name in EXPECTED:
        hits=[x for x in jobs if isinstance(x,dict) and x.get("name")==name]
        need(len(hits)==1 and type(hits[0].get("id")) is int and hits[0]["id"]>0 and
             hits[0].get("status")=="completed" and
             hits[0].get("conclusion")=="success",
             "required genuine hosted probe job not completed-success: "+name)
    extra=[x for x in jobs if x.get("name") not in EXPECTED]
    need(len(extra)==1 and extra[0].get("name")=="aggregate-independent-preflight",
         "unexpected hosted job in workflow")
    return True


def aggregate_samples(rows,*,repository,main_sha,work_sha,issue,run_id,run_attempt):
    need(isinstance(rows,list) and len(rows)==3,
         "require three separate actual sample files")
    need(sorted(x.get("sample") for x in rows if isinstance(x,dict))==[1,2,3],
         "three unique sample indexes absent")
    versions=set()
    durations=[]
    for s in rows:
        need(s.get("schema")==SCHEMA and
             s.get("classification")=="REAL_API_PREFLIGHT_ONLY" and
             s.get("repository")==repository and
             s.get("issue")==issue and
             s.get("main_sha")==main_sha and s.get("work_sha")==work_sha and
             s.get("run_id")==run_id and s.get("run_attempt")==run_attempt and
             s.get("actual_work_ci") in ("CREATED_NOT_GREEN","NOT_OBSERVED"),
             "mismatched sample source, event or false-green classification")
        ms=s.get("total_ms")
        need(type(ms) in (int,float) and 0<=ms<=300000,
             "sample monotonic timing absent or invalid")
        durations.append(ms)
        versions.add(s.get("version"))
    need(len(versions)==1 and
         bool(re.fullmatch(r"\d+\.\d+\.\d+\.\d+",next(iter(versions)))),
         "version drift between samples")
    return dict(schema="RHC190_PHASE_D_AGGREGATE_V1",repository=repository,
                issue=issue,main_sha=main_sha,work_sha=work_sha,
                version=next(iter(versions)),run_id=run_id,run_attempt=run_attempt,
                sample_count=3,sample_ms=[round(x,3) for x in durations],
                min_ms=round(min(durations),3),max_ms=round(max(durations),3),
                median_ms=round(statistics.median(durations),3),
                p95_ms=None,end_to_end_ms=None,
                actual_branchless_push_to_ci_seconds=None,
                actual_candidate_publisher_rhc102_seconds=None,
                evidence="THREE_REAL_HOSTED_GET_ONLY_PREFLIGHT_SAMPLES",
                release_authority="NONE",
                disclaimer="Not three full Fast-Path releases; no first ChatGPT tool to CI measurements")


def get(path):
    need(os.environ.get("GH_TOKEN"),"missing read-only GitHub token")
    proc=subprocess.run(["gh","api","--method","GET",path],text=True,
                        capture_output=True,timeout=20,check=False)
    need(proc.returncode==0,"real GitHub run/job readback failed")
    return json.loads(proc.stdout)


def cli(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("repository","main-sha","work-sha","root","out"):
        p.add_argument("--"+arg,required=True)
    p.add_argument("--issue",type=int,required=True)
    args=p.parse_args(argv)
    try:
        need(os.environ.get("GITHUB_ACTIONS")=="true" and
             os.environ.get("GITHUB_REPOSITORY")==args.repository and
             os.environ.get("GITHUB_SHA")==args.work_sha and
             bool(SHA.fullmatch(args.main_sha)) and bool(SHA.fullmatch(args.work_sha)),
             "runner/work/main SHA not bound to authenticated source")
        run_id=int(os.environ.get("GITHUB_RUN_ID","0"))
        run_attempt=int(os.environ.get("GITHUB_RUN_ATTEMPT","0"))
        need(run_id>0 and run_attempt>0,"hosted run/attempt missing")
        files=sorted(Path(args.root).rglob("rhc190-phase-d-sample-*.json"))
        need(len(files)==3 and len({x.name for x in files})==3,
             "missing/duplicated artifact files")
        samples=[json.loads(x.read_text(encoding="utf-8")) for x in files]
        result=aggregate_samples(samples,repository=args.repository,issue=args.issue,
                                 main_sha=args.main_sha,work_sha=args.work_sha,
                                 run_id=run_id,run_attempt=run_attempt)
        route="repos/"+args.repository+"/actions/runs/"+str(run_id)
        workflow=get(route)
        need(workflow.get("id")==run_id and
             workflow.get("head_sha")==args.work_sha and
             workflow.get("head_branch")=="work/RHC-"+str(args.issue) and
             workflow.get("name")=="RHC-190 Phase D Read-only Operator Benchmarks" and
             workflow.get("path")==".github/workflows/rhc190-phase-d-operator.yml" and
             workflow.get("event") in ("push","workflow_dispatch") and
             workflow.get("run_attempt")==run_attempt and
             (workflow.get("head_repository") or {}).get("full_name")==args.repository,
             "wrong independent GitHub-hosted probe workflow/run")
        jobs=get(route+"/jobs?per_page=100")
        require_hosted_jobs(jobs)
        dest=Path(args.out)
        need(dest.name=="rhc190-phase-d-three-samples.json" and
             not dest.exists(),"unsafe aggregate file overwrite")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("RHC190_PHASE_D_THREE_REAL_HOSTED_PREFLIGHTS=PASS "+
              json.dumps({"run_id":run_id,"sample_ms":result["sample_ms"],
                          "median_ms":result["median_ms"],"min_ms":result["min_ms"],
                          "max_ms":result["max_ms"],
                          "full_fast_path":"NOT_VERIFIED"},sort_keys=True))
        return 0
    except (ValueError,TypeError,OSError,KeyError,subprocess.TimeoutExpired):
        print("RHC190_PHASE_D_AGGREGATE=BLOCKED_NOT_VERIFIED",file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(cli())
