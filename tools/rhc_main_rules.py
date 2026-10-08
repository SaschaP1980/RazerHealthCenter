#!/usr/bin/env python3
"""RHC-20 main ruleset audit/setup: ordinary CI-qualified PR merges, zero Owner Git reviews.

The connected GitHub plugin lacks repository ruleset admin-write operations.
Use an owner-issued, narrowly scoped repository-administration token to apply
explicitly, never GITHUB_TOKEN and never a product release/unsigned consent.
"""
import argparse
import json
import os
import subprocess
import sys

from rhc_release_transaction import validate_main_rules

REPO="SaschaP1980/RazerHealthCenter"
# Main rules must apply to EVERY PR, including ordinary nonrelease development.
# Release-only contexts are enforced separately by rhc_release_finish.py.
CONTEXTS=("rhc/infra/linux","rhc/infra/windows")


def gh(method, path, payload=None):
    cmd=["gh","api","-X",method,"repos/"+REPO+path]
    if payload is not None:
        cmd += ["--input","-"]
    result=subprocess.run(cmd,text=True,capture_output=True,
                          input=json.dumps(payload) if payload is not None else None)
    if result.returncode:
        raise ValueError("GitHub ruleset admin API unavailable: "+result.stderr[-220:])
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ruleset-id",type=int,default=24701145)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    rule=gh("GET","/rulesets/"+str(args.ruleset_id))
    assert rule["enforcement"]=="active" and rule["target"]=="branch"
    conditions=rule.get("conditions",{}).get("ref_name",{}).get("include",[])
    if "~DEFAULT_BRANCH" not in conditions and "refs/heads/main" not in conditions:
        raise ValueError("selected ruleset is NOT actually targeting main")
    before=validate_main_rules(rule.get("rules",[]),list(CONTEXTS))
    if before["effective"]:
        print("RHC_MAIN_REQUIRED_CHECKS="+json.dumps(before,sort_keys=True))
        return
    if not args.apply:
        raise ValueError("BLOCKED_ADMIN: active main ruleset missing PR/check enforcement; "
                         "owner may use --apply with repo-administration token")
    if os.getenv("RHC_OWNER_RULESET_ADMIN")!="EXPLICIT_RULESET_ONLY":
        raise ValueError("Owner did not explicitly authorize admin change")
    # Preserve all existing deletion and non-fast-forward protection rules.
    rest=[x for x in rule.get("rules",[]) if x.get("type") not in
          ("pull_request","required_status_checks")]
    required=[
        {"type":"pull_request","parameters":{
            "dismiss_stale_reviews_on_push":False,
            "require_code_owner_review":False,
            "require_last_push_approval":False,
            "required_approving_review_count":0,
            "required_review_thread_resolution":False}},
        {"type":"required_status_checks","parameters":{
            "strict_required_status_checks_policy":True,
            "required_status_checks":[{"context":c} for c in CONTEXTS]}}]
    body={"name":rule["name"],"target":rule["target"],
          "enforcement":"active","conditions":rule["conditions"],
          "bypass_actors":rule.get("bypass_actors",[]),
          "rules":rest+required}
    gh("PUT","/rulesets/"+str(args.ruleset_id),body)
    after=gh("GET","/rulesets/"+str(args.ruleset_id))
    proof=validate_main_rules(after.get("rules",[]),list(CONTEXTS))
    if not proof["effective"]:
        raise ValueError("GitHub accepted request but required PR/status rules NOT effective")
    print("RHC_MAIN_REQUIRED_CHECKS="+json.dumps(proof,sort_keys=True))


if __name__=="__main__":
    try:main()
    except (ValueError,AssertionError) as e:
        print("RHC_MAIN_REQUIRED_CHECKS=BLOCKED_ADMIN: "+str(e),file=sys.stderr)
        sys.exit(1)
