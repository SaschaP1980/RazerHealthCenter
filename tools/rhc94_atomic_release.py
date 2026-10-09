#!/usr/bin/env python3
"""RHC-94: fail-closed single-PR Candidate/source/publication provenance.

Read-only contract CLI. GitHub write operations remain exclusively in the
qualified Actions orchestrator, never in this module.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
ISSUE = re.compile(r"(?m)^RHC-Issue: ([1-9][0-9]*)$")
WORK = re.compile(r"(?m)^Work-SHA: ([0-9a-f]{40})$")
PROFILE = re.compile(r"(?m)^Release-Profile: (version-only|patch|hotfix)$")
CONTEXTS = ("rhc/preflight/linux", "rhc/preflight/windows", "rhc/preflight/candidate")
PUBLISH_PATHS = ("downloads/README.md", "downloads/latest.json",
                 "downloads/releases.json")


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def single(pattern, message, label):
    hits = pattern.findall(message or "")
    require(len(hits) == 1, "ambiguous/missing " + label)
    return hits[0]


def trusted_statuses(statuses, contexts):
    require(isinstance(statuses, list), "missing status records")
    latest = {}
    for row in statuses:  # GitHub /statuses is newest first
        if isinstance(row, dict) and row.get("context") in contexts and row["context"] not in latest:
            latest[row["context"]] = row
    require(set(latest) == set(contexts), "missing exact-SHA status")
    for key, row in latest.items():
        require(row.get("state") == "success"
                and (row.get("creator") or {}).get("login") == "github-actions[bot]",
                "untrusted/incomplete exact-SHA status: " + key)
    return True


def qualify_candidate(candidate_sha, base_sha, candidate, work, issue, statuses,
                      completion, current_main, work_head):
    require(all(isinstance(x, str) and SHA.fullmatch(x)
                for x in (candidate_sha, base_sha, current_main, work_head)),
            "invalid SHA")
    require(base_sha == current_main, "main changed before activation")
    require(candidate.get("sha") == candidate_sha
            and candidate.get("parents") == [{"sha": base_sha}],
            "Candidate must be one commit over current main")
    cm = candidate.get("message", "")
    work_sha = single(WORK, cm, "Candidate Work-SHA")
    number = int(single(ISSUE, cm, "Candidate RHC-Issue"))
    profile = single(PROFILE, cm, "Candidate Release-Profile")
    require(work_sha == work_head and work.get("sha") == work_sha,
            "Work ref/commit differs from qualified Candidate")
    wm = work.get("message", "")
    require(int(single(ISSUE, wm, "Work RHC-Issue")) == number
            and single(PROFILE, wm, "Work Release-Profile") == profile
            and wm.count("Development-Completion: requested") == 1,
            "Work and Candidate trailers mismatch")
    require(isinstance(issue, dict) and issue.get("number") == number
            and issue.get("state") == "open" and not issue.get("pull_request"),
            "responsible Issue missing or not open")
    trusted_statuses(statuses, CONTEXTS)
    trusted_statuses(completion, ("development-completion/gate",))
    status = next(x for x in completion if x.get("context") == "development-completion/gate")
    require(status.get("description") == "PASS main=" + base_sha,
            "Work completion pinned to different main")
    require(candidate.get("tree") == work.get("tree"), "Candidate/Work tree differs")
    return dict(result="PASS", candidateSha=candidate_sha, baseMainSha=base_sha,
                workSha=work_sha, issueNumber=number, releaseProfile=profile)


def qualify_stage(qual, stage, pr, release_branch, version, diff_paths):
    sha = qual["candidateSha"]
    base = qual["baseMainSha"]
    require(stage.get("parents") == [{"sha": sha}], "staging parent not exact Candidate")
    require(pr.get("state") == "open" and pr.get("draft") is False
            and pr.get("merged_at") is None and pr.get("headSha") == stage["sha"]
            and pr.get("baseSha") == base and pr.get("headRef") == release_branch,
            "release PR identity/base/head mismatch")
    require(release_branch == "release/v" + version, "unexpected release branch")
    body = pr.get("body", "")
    require(re.findall(r"\b(?:Refs|Closes) #([1-9][0-9]*)\b", body) ==
            [str(qual["issueNumber"])], "PR missing exactly one responsible Issue")
    require("sourceSha " + sha in body and "Work-SHA " + qual["workSha"] in body,
            "combined PR missing exact Candidate/Work source identity")
    require(re.match(r"^\[RHC-" + str(qual["issueNumber"]) + r"\]", pr.get("title", "")),
            "release PR title issue mismatch")
    require(single(ISSUE, stage.get("message", ""), "stage Issue") ==
            str(qual["issueNumber"]), "stage commit issue mismatch")
    require(set(diff_paths) == set(PUBLISH_PATHS) |
            {"downloads/RazerHealthCenter-Portable-v" + version + ".zip"},
            "stage must add exactly four publication paths")
    return {"result": "PASS", "stageSha": stage["sha"], "sourceSha": sha,
            "previousMain": base, "issueNumber": qual["issueNumber"]}


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    require(r.returncode == 0, "git " + " ".join(args) + ": " + r.stderr[:150])
    return r.stdout.strip()


def gh(path):
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo),
            "unknown GitHub repository")
    r = subprocess.run(["gh", "api", "repos/" + repo + "/" + path],
                       capture_output=True, text=True, timeout=40)
    require(r.returncode == 0, "GitHub GET failed: " + r.stderr[:150])
    return json.loads(r.stdout)


def sha_info(value):
    require(SHA.fullmatch(value or ""), "bad source ref SHA")
    c = gh("git/commits/" + value)
    return dict(sha=value, message=c["message"], tree=c["tree"]["sha"],
                parents=[{"sha": p["sha"]} for p in c["parents"]])


def current_candidate():
    source = os.environ.get("GITHUB_SHA", "")
    cand = sha_info(source)
    require(len(cand["parents"]) == 1, "Candidate multi-parent")
    base = cand["parents"][0]["sha"]
    worksha = single(WORK, cand["message"], "Work-SHA")
    work = sha_info(worksha)
    n = int(single(ISSUE, cand["message"], "Issue"))
    state = gh("branches/main")["commit"]["sha"]
    wb = "work/RHC-" + str(n)
    workhead = gh("git/ref/heads/" + wb)["object"]["sha"]
    proof = qualify_candidate(source, base, cand, work, gh("issues/" + str(n)),
                              gh("commits/" + source + "/statuses"),
                              gh("commits/" + worksha + "/statuses"),
                              state, workhead)
    require(git("rev-parse", "HEAD") == source, "checked out wrong Candidate")
    require(git("rev-parse", "HEAD^{tree}") == cand["tree"],
            "tree identity mismatch")
    from rhc_release_contracts import version_from_model
    version = version_from_model(Path("."))
    require(os.environ.get("GITHUB_REF_NAME") == "candidate/v" + version,
            "ref/version mismatch")
    return proof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["validate-candidate", "validate-stage"])
    ap.add_argument("--stage-sha")
    ap.add_argument("--pr", type=int)
    args = ap.parse_args()
    q = current_candidate()
    if args.command == "validate-stage":
        require(SHA.fullmatch(args.stage_sha or ""), "stage SHA missing")
        require(isinstance(args.pr, int) and args.pr > 0, "PR missing")
        from rhc_release_contracts import version_from_model
        version = version_from_model(Path("."))
        p = gh("pulls/" + str(args.pr))
        info = dict(state=p["state"], draft=p["draft"], merged_at=p["merged_at"],
                    headSha=p["head"]["sha"], headRef=p["head"]["ref"],
                    baseSha=p["base"]["sha"], title=p["title"], body=p["body"])
        staged = sha_info(args.stage_sha)
        git("fetch", "--no-tags", "origin", "release/v" + version)
        changed = git("diff", "--name-only", q["candidateSha"], args.stage_sha).splitlines()
        proof = qualify_stage(q, staged, info, "release/v" + version, version, changed)
        print("RHC94_COMBINED_STAGE=" + json.dumps(proof, sort_keys=True))
    else:
        print("RHC94_CANDIDATE_AUTHORITY=" + json.dumps(q, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print("RHC94_CONTRACT=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(1)
