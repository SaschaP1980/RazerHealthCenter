#!/usr/bin/env python3
"""RHC-202 read-only *actually invocable* GitHub Actions/native gh CLI preflight.

No publication authority. Reports ONLY host-side authenticated GET timings:
never first ChatGPT tool -> Work push/CI, nor complete Fast-Path/release time.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

SCHEMA="RHC190_PHASE_D_PREFLIGHT_V1"
SHA=re.compile(r"[0-9a-f]{40}\Z")
REPO_RE=re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
VERSION=re.compile(r"\d+\.\d+\.\d+\.\d+\Z")
HEADINGS=("Chat origin","Work-Path authorization and scope","Benchmark configuration",
"Validation plan and coverage","Measurement ledger","Development Completion attempts",
"Candidate Entry","Candidate attempts","Release","Final Release Verification",
"Performance result","Evidence audit","Plan-conformance assessment")
READ_PATHS=(
    r"branches/main",
    r"issues/[1-9][0-9]*",
    r"issues/[1-9][0-9]*/comments\?per_page=100",
    r"branches/work/RHC-[1-9][0-9]*",
    r"contents/(?:model\.go|CHANGELOG\.md|downloads/latest\.json)\?ref=[0-9a-f]{40}",
    r"actions/runs\?head_sha=[0-9a-f]{40}&per_page=100",
)


def require(ok, reason):
    if not ok:
        raise ValueError("RHC190_PHASE_D_BLOCKED: "+reason)


def safe_api_route(path,repository):
    require(isinstance(repository,str) and bool(REPO_RE.fullmatch(repository)),
            "invalid requested repository")
    prefix="repos/"+repository+"/"
    require(isinstance(path,str) and path.startswith(prefix)
            and any(re.fullmatch(pattern,path[len(prefix):]) for pattern in READ_PATHS),
            "only approved repository GET paths permitted")
    return path


def github_get(path,repository):
    safe_api_route(path,repository)
    require(os.environ.get("GH_TOKEN"),"read-only GH_TOKEN unavailable")
    proc=subprocess.run(["gh","api","--method","GET",path],
                        capture_output=True,text=True,timeout=20,check=False)
    # Never leak gh stderr, raw API/credential material or JSON payload.
    require(proc.returncode==0,"authenticated GitHub GET failed")
    try:
        return json.loads(proc.stdout)
    except (TypeError,ValueError) as exc:
        raise ValueError("RHC190_PHASE_D_BLOCKED: malformed GitHub JSON") from exc


def require_identity(main,issue,comments,work,repository,number,main_sha,work_sha):
    require(main.get("commit",{}).get("sha")==main_sha,
            "current main SHA differs from owner-pinned main")
    require(work.get("commit",{}).get("sha")==work_sha,
            "current Work ref differs from expected SHA")
    require(issue.get("number")==number and
            issue.get("title","").startswith("[RHC-"+str(number)+"] ") and
            issue.get("state")=="open" and "pull_request" not in issue,
            "canonical Issue identity/state incorrect")
    labels=[x.get("name") for x in issue.get("labels",[]) if isinstance(x,dict)]
    require(len(labels)==len(set(labels)) and
            len(set(labels)&{"bug","enhancement"})==1 and
            len([x for x in labels if isinstance(x,str) and x.startswith("priority: ")])==1 and
            "dev-path: work-branch" in labels and "dev-ops" in labels,
            "missing required Issue taxonomy")
    require("Development path: dev-path: work-branch" in issue.get("body",""),
            "responsible Work path absent")
    require(isinstance(comments,list) and 0<len(comments)<100,
            "ambiguous or missing complete canonical comment list")
    marker="**Issue:** [RHC-"+str(number)+"](https://github.com/"+repository+"/issues/"+str(number)+")"
    matching=[x for x in comments if marker in str(x.get("body",""))]
    require(len(matching)==1 and type(matching[0].get("id")) is int and matching[0]["id"]>0,
            "canonical Rolling comment absent or duplicated")
    titles=re.findall(r"(?m)^### (.+)$",matching[0]["body"])
    require(tuple(titles)==HEADINGS,"not thirteen exact Rolling Comment sections")
    return matching[0]["id"]


def decode_file(obj):
    require(isinstance(obj,dict) and obj.get("encoding")=="base64"
            and isinstance(obj.get("content"),str)
            and bool(SHA.fullmatch(str(obj.get("sha")))),
            "unverified file blob metadata")
    try:
        return base64.b64decode(obj["content"],validate=False).decode("utf-8")
    except (ValueError,UnicodeDecodeError) as exc:
        raise ValueError("RHC190_PHASE_D_BLOCKED: invalid code file encoding") from exc


def measured(getter,repository,uri,clock):
    route="repos/"+repository+"/"+uri
    safe_api_route(route,repository)
    before=clock()
    payload=getter(route)
    elapsed=clock()-before
    require(isinstance(elapsed,(float,int)) and 0<=elapsed<=120,
            "monotonic API call measurement invalid")
    require(payload is not None,"GitHub API response absent")
    return payload,round(1000*elapsed,3)


def measure(getter,*,repository,issue,main_sha,work_sha,sample,run_id,run_attempt,
            clock=time.perf_counter,utc=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00","Z")):
    require(isinstance(repository,str) and repository=="SaschaP1980/RazerHealthCenter"
            and isinstance(issue,int) and issue>0 and
            isinstance(main_sha,str) and bool(SHA.fullmatch(main_sha)) and
            isinstance(work_sha,str) and bool(SHA.fullmatch(work_sha)) and
            sample in (1,2,3) and type(run_id) is int and run_id>0 and
            type(run_attempt) is int and run_attempt>0,
            "untrusted initial probe scope or run identity")
    source_start=utc()
    ticks=clock()
    mapping=(
       ("main","branches/main"),
       ("issue",f"issues/{issue}"),
       ("comments",f"issues/{issue}/comments?per_page=100"),
       ("work",f"branches/work/RHC-{issue}"),
       ("model",f"contents/model.go?ref={main_sha}"),
       ("changelog",f"contents/CHANGELOG.md?ref={main_sha}"),
       ("latest",f"contents/downloads/latest.json?ref={main_sha}"),
       ("runs",f"actions/runs?head_sha={work_sha}&per_page=100"),
    )
    responses={};durations={}
    for name,route in mapping:
        responses[name],durations[name]=measured(getter,repository,route,clock)
    comment_id=require_identity(responses["main"],responses["issue"],responses["comments"],
                                responses["work"],repository,issue,main_sha,work_sha)
    model=decode_file(responses["model"])
    log=decode_file(responses["changelog"])
    latest=json.loads(decode_file(responses["latest"]))
    values=re.findall(r'(?m)^\s*(?:appVersion|referenceVersion)\s*=\s*"([0-9]+(?:\.[0-9]+){3})"',model)
    require(len(values)==2 and values[0]==values[1]
            and bool(VERSION.fullmatch(values[0])),"product source version not synchronized")
    version=values[0]
    require(log.startswith("# Changelog\n\n## "+version+" — ")
            and latest.get("version")==version and
            isinstance(latest.get("sourceSha"),str) and bool(SHA.fullmatch(latest["sourceSha"]))
            and isinstance(latest.get("sha256"),str) and bool(re.fullmatch(r"[0-9a-f]{64}",latest["sha256"]))
            and type(latest.get("size")) is int and latest["size"]>0,
            "model/Changelog/public release baseline not aligned")
    collection=responses["runs"]
    require(isinstance(collection,dict) and
            isinstance(collection.get("total_count"),int) and
            collection["total_count"]<100 and
            isinstance(collection.get("workflow_runs"),list),
            "hosted Work CI discovery truncated/ambiguous")
    matches=[x for x in collection["workflow_runs"] if
             x.get("name")=="RHC Infrastructure Qualification (nonpublishing)" and
             x.get("head_sha")==work_sha and x.get("event")=="push"]
    require(len(matches)<=1,"duplicate or ambiguous real Work CI runs")
    status="NOT_OBSERVED"
    if matches:
        require(type(matches[0].get("id")) is int and matches[0]["id"]>0,
                "hosted CI run id absent")
        status="CREATED_NOT_GREEN"  # created is not proof of passed jobs
    end=clock()
    require(0<=end-ticks<=300,"invalid whole probe duration")
    return dict(schema=SCHEMA,sample=sample,repository=repository,
                issue=issue,main_sha=main_sha,work_sha=work_sha,
                version=version,comment_id=comment_id,
                run_id=run_id,run_attempt=run_attempt,
                classification="REAL_API_PREFLIGHT_ONLY",
                time_source="HOST_MONOTONIC_API_CALLS_NOT_CI_DISPATCH",
                source_start_utc=source_start,total_ms=round(1000*(end-ticks),3),
                api_ms=durations,actual_work_ci=status)


def cli(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository",required=True)
    parser.add_argument("--issue",required=True,type=int)
    parser.add_argument("--main-sha",required=True)
    parser.add_argument("--work-sha",required=True)
    parser.add_argument("--sample",required=True,type=int)
    parser.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    try:
        require(os.environ.get("GITHUB_ACTIONS")=="true","not a real hosted Action")
        require(os.environ.get("GITHUB_SHA")==args.work_sha and
                os.environ.get("GITHUB_REPOSITORY")==args.repository,
                "runner SHA/repo identity mismatch")
        run_id=int(os.environ.get("GITHUB_RUN_ID","0"))
        attempt=int(os.environ.get("GITHUB_RUN_ATTEMPT","0"))
        result=measure(lambda path:github_get(path,args.repository),
           repository=args.repository,issue=args.issue,main_sha=args.main_sha,
           work_sha=args.work_sha,sample=args.sample,run_id=run_id,
           run_attempt=attempt)
        dest=Path(args.out)
        require(dest.name=="rhc190-phase-d-sample-"+str(args.sample)+".json"
                and not dest.exists(),"unsafe output path/overwrite")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print("RHC190_PHASE_D_PREFLIGHT=PASS sample="+str(args.sample)+
              " classification=REAL_API_PREFLIGHT_ONLY elapsed_ms="+str(result["total_ms"]))
        return 0
    except (ValueError,TypeError,KeyError,OSError,subprocess.TimeoutExpired) as error:
        # Hide any raw backend error message to prevent accidental secret leakage.
        print("RHC190_PHASE_D_PREFLIGHT=BLOCKED_NOT_VERIFIED",file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(cli())
