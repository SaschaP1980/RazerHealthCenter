#!/usr/bin/env python3
"""Exact-SHA automatic *nonpublishing* version-only Work -> Candidate transfer.

Fail closed on missing identity, status, policy, ancestry, or ambiguous writes.
No tag, product download, signing change, release pointer, or Razer repair.
"""
import base64
import json
import os
import re
import subprocess
import sys

from rhc_release_contracts import SEMVER, VERSION_PATTERN, require
from rhc_orchestration_contracts import validate_candidate

SHA = re.compile(r"[0-9a-f]{40}\Z")
WORK = re.compile(r"work/RHC-([1-9][0-9]*)\Z")


def model_version(content):
    rows = VERSION_PATTERN.findall(content)
    values = dict(rows)
    require(len(rows) == 2 and len(values) == 2, "model versions missing/duplicated")
    v = values.get("appVersion", "")
    require(bool(SEMVER.fullmatch(v)) and values.get("referenceVersion") == v,
            "model versions invalid/mismatched")
    return v


def enforce_version_only_model_edit(original, updated):
    """Prove the entire Go model diff changes *only* both version literals."""
    old_version = model_version(original)
    new_version = model_version(updated)
    replacements = [0]
    def replace(match):
        require(match.group(2) == old_version, "unexpected model version before change")
        replacements[0] += 1
        return match.group(1) + new_version + match.group(3)
    pattern = re.compile(r'(^[ \t]*(?:appVersion|referenceVersion)[ \t]*=[ \t]*")([^"]+)(")', re.M)
    predicted = pattern.sub(replace, original)
    require(replacements[0] == 2 and predicted == updated,
            "model.go has changes beyond its two version literals")
    return True


def validate_plan(s):
    branch = s.get("workBranch", "")
    match = WORK.fullmatch(branch)
    require(match is not None, "invalid Work branch")
    issue = match.group(1)
    main, work, tree = (s.get(k) for k in ("mainSha", "workSha", "treeSha"))
    require(all(isinstance(v, str) and SHA.fullmatch(v) for v in (main, work, tree)),
            "invalid exact source SHA")
    require(main != work and s.get("compareStatus") == "ahead"
            and s.get("behindBy") == 0
            and isinstance(s.get("aheadBy"), int) and 1 <= s["aheadBy"] <= 100,
            "main/Work ancestry mismatch")
    p = s.get("policy", {})
    require(p.get("productionEnabled") is False and p.get("distribution") == "repo-downloads"
            and p.get("signingDecision") == "unknown"
            and p.get("rollbackVerified") is False, "release policy unexpectedly altered")
    require(s.get("candidateExists") is False, "candidate exists: no blind retry")
    message = s.get("message", "")
    for trailer in ("RHC-Issue: " + issue, "Release-Profile: version-only",
                    "Development-Completion: requested"):
        require(len(re.findall("^" + re.escape(trailer) + "$", message, re.M)) == 1,
                "missing or ambiguous work trailer: " + trailer)
    statuses = s.get("statuses", [])
    require(isinstance(statuses, list), "missing statuses")
    latest = next((x for x in statuses
                   if x.get("context") == "development-completion/gate"), None)
    require(isinstance(latest, dict) and latest.get("state") == "success"
            and latest.get("description") == "PASS main=" + main
            and latest.get("creator", {}).get("login") == "github-actions[bot]",
            "untrusted/stale Work completion")
    files = s.get("files")
    require(isinstance(files, list) and len(files) == 2
            and all(x.get("status") in ("added", "modified") for x in files),
            "unsafe Work diff")
    names = [x.get("filename") for x in files]
    before, after = s.get("mainVersion"), s.get("workVersion")
    require(isinstance(before, str) and bool(SEMVER.fullmatch(before))
            and isinstance(after, str) and bool(SEMVER.fullmatch(after)),
            "invalid target/main version")
    a, b = tuple(map(int, after.split("."))), tuple(map(int, before.split(".")))
    require(a[:3] == b[:3] and a[3] == b[3] + 1, "not next HOTFIX")
    validate_candidate(previous=before, version=after, changed_paths=names,
                       release_profile="version-only", current_main_parent=True)
    return dict(branch="candidate/v" + after, version=after, issue=issue,
                baseMainSha=main, workSha=work, workTreeSha=tree)


def gh(method, path, payload=None, optional404=False):
    command = ["gh", "api", "-X", method, "repos/" + os.environ["GITHUB_REPOSITORY"] + path]
    if payload is not None:
        command += ["--input", "-"]
    p = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                       text=True, capture_output=True)
    if optional404 and p.returncode != 0 and "HTTP 404" in p.stderr:
        return None
    require(p.returncode == 0, "GitHub API " + method + " " + path + " failed: " +
            p.stderr[-250:])
    return json.loads(p.stdout) if p.stdout.strip() else {}


def remote_model(ref):
    obj = gh("GET", "/contents/model.go?ref=" + ref)
    require(obj.get("encoding") == "base64", "model content unavailable")
    return base64.b64decode(obj["content"]).decode("utf-8")


def remote_version(ref):
    return model_version(remote_model(ref))


def main():
    branch = os.environ.get("WORK_BRANCH", "")
    expected = os.environ.get("WORK_SHA", "")
    require(WORK.fullmatch(branch) is not None
            and SHA.fullmatch(expected) is not None, "invalid workflow inputs")
    require(bool(os.environ.get("GH_TOKEN")), "missing GitHub token")
    main_sha = gh("GET", "/branches/main")["commit"]["sha"]
    work_sha = gh("GET", "/git/ref/heads/" + branch)["object"]["sha"]
    require(work_sha == expected, "work head changed")
    commit = gh("GET", "/git/commits/" + work_sha)
    comparison = gh("GET", "/compare/" + main_sha + "..." + work_sha)
    statuses = gh("GET", "/commits/" + work_sha + "/status")
    work_model = remote_model(work_sha)
    main_model = remote_model(main_sha)
    enforce_version_only_model_edit(main_model, work_model)
    version = model_version(work_model)
    candidate_ref = "candidate/v" + version
    existing = gh("GET", "/git/ref/heads/" + candidate_ref, optional404=True)
    policy_obj = gh("GET", "/contents/config/rhc-release-policy.json?ref=" + main_sha)
    require(policy_obj.get("encoding") == "base64", "policy unreadable")
    policy = json.loads(base64.b64decode(policy_obj["content"]))
    plan = validate_plan(dict(workBranch=branch, mainSha=main_sha, workSha=work_sha,
        treeSha=commit["tree"]["sha"], message=commit["message"],
        compareStatus=comparison["status"], behindBy=comparison["behind_by"],
        aheadBy=comparison["ahead_by"], files=comparison["files"],
        mainVersion=model_version(main_model), workVersion=version,
        statuses=statuses["statuses"], policy=policy,
        candidateExists=existing is not None))
    # Exclusive mutation boundary; verify live refs again before any write.
    require(gh("GET", "/branches/main")["commit"]["sha"] == main_sha, "main moved")
    require(gh("GET", "/git/ref/heads/" + branch)["object"]["sha"] == work_sha,
            "Work changed before candidate creation")
    message = ("chore(RHC-" + plan["issue"] + "): candidate v" + version +
               " from exact verified Work\n\nWork-SHA: " + work_sha +
               "\nMain-SHA: " + main_sha + "\n\nRHC-Issue: " + plan["issue"] +
               "\nRelease-Profile: version-only")
    new = gh("POST", "/git/commits", dict(message=message,
                tree=plan["workTreeSha"], parents=[main_sha]))
    sha = new.get("sha", "")
    require(bool(SHA.fullmatch(sha)), "candidate commit unverified")
    # POST /git/refs creates a ref only if it did not previously exist.
    gh("POST", "/git/refs", {"ref": "refs/heads/" + candidate_ref, "sha": sha})
    actual = gh("GET", "/git/ref/heads/" + candidate_ref)
    new_commit = gh("GET", "/git/commits/" + sha)
    require(actual.get("object", {}).get("sha") == sha
            and new_commit["tree"]["sha"] == plan["workTreeSha"]
            and [v["sha"] for v in new_commit["parents"]] == [main_sha],
            "candidate readback differs: manual recovery required")
    # GITHUB_TOKEN pushes don't trigger downstream push CI: explicit dispatch.
    gh("POST", "/actions/workflows/rhc-candidate-preflight.yml/dispatches",
       {"ref": candidate_ref})
    print("RHC_WORK_TO_CANDIDATE=" + json.dumps(dict(plan, candidateSha=sha,
          status="CANDIDATE_STAGED_PREFLIGHT_DISPATCHED"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print("RHC_WORK_TO_CANDIDATE=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(1)
