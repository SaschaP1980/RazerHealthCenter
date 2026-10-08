#!/usr/bin/env python3
"""Read-only live GH-bound release-branch preflight. No publication or token writes."""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import rhc_downloads as d
from rhc_release_contracts import require, version_from_model
from rhc_release_transaction import CANDIDATE, hash40, trusted_contexts
from rhc_release_live import gh, branch, record_approval, content_json, required_main_rules

RELEASE = re.compile(r"release/v(\d+\.\d+\.\d+\.\d+)\Z")


def git(*cmd):
    p = subprocess.run(["git", *cmd], capture_output=True, text=True)
    require(p.returncode == 0, "git read failed: " + " ".join(cmd) + p.stderr[-150:])
    return p.stdout.strip()


def inspect(root, expected_branch, expected_sha):
    require(os.environ.get("GITHUB_REPOSITORY") == "SaschaP1980/RazerHealthCenter",
            "wrong repo")
    match = RELEASE.fullmatch(expected_branch or "")
    require(match is not None and hash40(expected_sha), "wrong release ref/SHA")
    version = match.group(1)
    require(root.resolve().is_dir() and version_from_model(root) == version,
            "release checkout/version mismatch")
    require(git("rev-parse", "HEAD") == expected_sha, "checkout does not match GitHub commit")
    remote = branch(expected_branch)
    require(remote and remote["object"]["sha"] == expected_sha,
            "release branch moved while checking")
    commit = gh("GET", "/git/commits/" + expected_sha)
    msg, parents = commit["message"], [p["sha"] for p in commit["parents"]]
    require(len(parents) == 1, "release commit must have single main parent")
    main_sha = gh("GET", "/branches/main")["commit"]["sha"]
    require(parents == [main_sha], "main advanced/invalid release ancestry")
    m = re.findall(r"^Source-SHA: ([0-9a-f]{40})$", msg, re.M)
    c = re.findall(r"^Owner-Approval-Comment: ([1-9][0-9]*)$", msg, re.M)
    require(len(m) == 1 and len(c) == 1, "missing exact source/owner trailers")
    candidate = m[0]
    src = branch("candidate/v" + version)
    require(src and src["object"]["sha"] == candidate, "candidate source no longer pinned")
    p = gh("GET", "/git/commits/" + candidate)
    require([x["sha"] for x in p["parents"]] == [main_sha],
            "candidate source lineage invalid")
    trusted_contexts(gh("GET", "/commits/" + candidate + "/statuses"), CANDIDATE)
    policy = content_json("config/rhc-release-policy.json", main_sha)
    require(policy.get("productionEnabled") is True and
            policy.get("rollbackVerified") is True and
            policy.get("distribution") == "repo-downloads" and
            policy.get("signingDecision") in ("unsigned-approved","signed-verified"),
            "release policy not authorized")
    required_main_rules()
    old = gh("GET", "/git/ref/tags/v" + version, allow404=True)
    require(old is None, "release tag already exists")
    pr = gh("GET", "/pulls?head=SaschaP1980:" + expected_branch + "&state=open")
    require(len(pr) == 1 and pr[0]["base"]["sha"] == main_sha
            and pr[0]["head"]["sha"] == expected_sha,
            "release PR head/base mismatch")
    diff = gh("GET", "/compare/" + main_sha + "..." + expected_sha)
    expected = {
        "downloads/" + d.filename(version), "downloads/releases.json",
        "downloads/latest.json", "downloads/README.md"}
    require(diff["behind_by"] == 0 and diff["ahead_by"] == 1
            and set(x["filename"] for x in diff["files"]) == expected
            and all(x["status"] in ("added", "modified") for x in diff["files"]),
            "release PR changed unrelated source or previous archives")
    local = root / "downloads"
    history = d.verify(local)
    require(history and history[0]["version"] == version
            and history[0]["sourceSha"] == candidate,
            "latest catalog/source differs from release")
    record = history[0]
    require(hashlib.sha256((local / record["file"]).read_bytes()).hexdigest()
            == record["sha256"], "ZIP hash mismatch")
    approval = record_approval(int(c[0]), version, candidate,
                               record["sha256"], policy)
    require(gh("GET", "/branches/main")["commit"]["sha"] == main_sha
            and branch(expected_branch)["object"]["sha"] == expected_sha,
            "main/release changed during preflight")
    return {"result": "RELEASE_BRANCH_PREACTIVATION_VALID", "version": version,
            "mainSha": main_sha, "candidateSha": candidate,
            "releaseSha": expected_sha, "sha256": record["sha256"],
            "archive": record["file"], "ownerApproval": approval["id"],
            "pr": pr[0]["number"], "signingDecision": policy["signingDecision"]}


if __name__ == "__main__":
    try:
        actual = inspect(Path("."), os.environ.get("RELEASE_BRANCH"),
                         os.environ.get("RELEASE_SHA"))
        print("RHC_RELEASE_BRANCH_CHECK=" + json.dumps(actual, sort_keys=True))
    except (ValueError, OSError, TypeError, KeyError) as e:
        print("RHC_RELEASE_BRANCH_CHECK=BLOCKED: " + str(e), file=sys.stderr)
        sys.exit(1)
