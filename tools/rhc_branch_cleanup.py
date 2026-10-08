#!/usr/bin/env python3
"""Lease-guarded RHC post-merge branch cleanup. Default dry-run."""
import argparse
import json
import os
import re
import subprocess
import sys

SHA = re.compile(r"[0-9a-f]{40}\Z")
BRANCH = re.compile(r"(?:work/RHC-[1-9][0-9]*|import/RHC-[1-9][0-9]*-v[0-9]+(?:\.[0-9]+)*|license/RHC-[1-9][0-9]*-[a-z0-9-]+)\Z")


class Blocked(RuntimeError):
    pass


def need(value, explanation):
    if not value:
        raise Blocked(explanation)


def command(args):
    p = subprocess.run(args, capture_output=True, text=True, check=False)
    if p.returncode:
        raise Blocked("command failed; no cleanup claimed: "
                      + " ".join(args[:2]) + " status=" + str(p.returncode)
                      + " " + p.stderr.strip()[:350])
    return p.stdout


def api(path):
    return json.loads(command(["gh", "api", path]))


def remote_ref(branch, run=command):
    rows = [s.split() for s in run(["git", "ls-remote", "--heads", "origin",
                                    "refs/heads/" + branch]).splitlines() if s.strip()]
    need(len(rows) <= 1, "ambiguous remote ref")
    if not rows:
        return None
    need(len(rows[0]) == 2 and rows[0][1] == "refs/heads/" + branch
         and SHA.fullmatch(rows[0][0]), "invalid remote ref")
    return rows[0][0]


def ancestor(older, newer, repo, get=api):
    v = get("repos/" + repo + "/compare/" + older + "..." + newer)
    return (v.get("behind_by") == 0
            and (v.get("merge_base_commit") or {}).get("sha") == older
            and v.get("status") in ("ahead", "identical"))


def verified_pr(pr, repo):
    need(pr.get("state") == "closed" and pr.get("merged") is True
         and bool(pr.get("merged_at")), "PR not merged")
    head, base = pr.get("head") or {}, pr.get("base") or {}
    need(base.get("ref") == "main"
         and (base.get("repo") or {}).get("full_name") == repo, "not target main")
    need((head.get("repo") or {}).get("full_name") == repo, "foreign PR head")
    branch = head.get("ref")
    need(isinstance(branch, str) and BRANCH.fullmatch(branch), "unsafe branch name")
    head_sha, merge_sha = head.get("sha"), pr.get("merge_commit_sha")
    need(isinstance(head_sha, str) and SHA.fullmatch(head_sha), "bad head SHA")
    need(isinstance(merge_sha, str) and SHA.fullmatch(merge_sha), "bad merge SHA")
    return branch, head_sha, merge_sha


def cleanup(number, repo, execute=False, get=api, run=command):
    need(isinstance(number, int) and 0 < number <= 100000000, "bad PR number")
    need(isinstance(repo, str)
         and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo), "bad repo")
    pr = get("repos/" + repo + "/pulls/" + str(number))
    need(pr.get("number") == number, "wrong PR returned")
    branch, expected, merge = verified_pr(pr, repo)
    main = (get("repos/" + repo + "/branches/main").get("commit") or {}).get("sha")
    need(isinstance(main, str) and SHA.fullmatch(main), "bad current main SHA")
    need(ancestor(expected, main, repo, get), "head not contained in main")
    need(ancestor(merge, main, repo, get), "merged commit not in main")
    live = remote_ref(branch, run)
    if live is None:
        result = "already-absent"
    else:
        need(live == expected, "branch advanced; do not delete")
        if execute:
            # Lease guarantees no intervening branch-head update can be deleted.
            run(["git", "push", "--force-with-lease=refs/heads/" + branch + ":" + expected,
                 "origin", ":refs/heads/" + branch])
            need(remote_ref(branch, run) is None, "branch still exists after push")
            result = "deleted"
        else:
            result = "would-delete"
    summary = dict(result="PASS", pr=number, branch=branch, head=expected,
                   merge=merge, main=main, status=result)
    print("RHC_BRANCH_CLEANUP=" + json.dumps(summary, sort_keys=True))
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pr", type=int, required=True)
    p.add_argument("--execute", action="store_true")
    opts = p.parse_args()
    need(bool(os.environ.get("GH_TOKEN")), "missing GH_TOKEN")
    cleanup(opts.pr, os.environ.get("GITHUB_REPOSITORY", ""), execute=opts.execute)


if __name__ == "__main__":
    try:
        main()
    except (Blocked, ValueError, KeyError, OSError) as exc:
        print("RHC_BRANCH_CLEANUP=BLOCKED " + str(exc), file=sys.stderr)
        sys.exit(1)
