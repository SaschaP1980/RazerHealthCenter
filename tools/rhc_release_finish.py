#!/usr/bin/env python3
"""Owner-gated RHC repo-downloads Release PR merge/tag/postverify controller.

This is never called from automatic Candidate processing. No wildcard approval:
all three release statuses, actual RHC22 owner consent, the exact ZIP digest,
the protected main PR rule, and native Razer/rollback must be independently
true before any remote write. Unknown GitHub writes yield ATTENTION, not retry.
"""
import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

import rhc_downloads as downloads
from rhc_release_contracts import require
from rhc_release_transaction import RELEASE, hash40, trusted_contexts
from rhc_release_live import gh, branch, required_main_rules
from rhc_release_verify import inspect


def blob_bytes(blob_sha):
    require(hash40(blob_sha), "missing remote blob SHA")
    result = gh("GET", "/git/blobs/" + blob_sha)
    require(result.get("encoding") == "base64", "remote blob not byte-readable")
    return base64.b64decode(result["content"])


def tree_map(commit_sha):
    require(hash40(commit_sha), "bad remote tree parent")
    root = gh("GET", "/git/commits/" + commit_sha)
    tree = gh("GET", "/git/trees/" + root["tree"]["sha"] + "?recursive=1")
    require(tree.get("truncated") is False, "GitHub tree truncated; cannot postverify")
    return {x["path"]: x["sha"] for x in tree["tree"] if x["type"] == "blob"}


def check_live_staged_release(root, ref, sha):
    """READ-ONLY full premerge check (approval still exact, statuses creator bot)."""
    require(os.getenv("RHC_REAL_PUBLICATION_APPROVED") == "EXPLICIT_OWNER_RHC22"
            and os.getenv("GH_TOKEN"), "owner release action not explicitly enabled")
    state = inspect(root, ref, sha)
    require(branch(ref)["object"]["sha"] == sha, "release branch advanced")
    trusted_contexts(gh("GET", "/commits/" + sha + "/statuses"), RELEASE)
    required_main_rules()
    current = gh("GET", "/branches/main")["commit"]["sha"]
    require(current == state["mainSha"], "main advanced after staged approval")
    pr = gh("GET", "/pulls/" + str(state["pr"]))
    require(pr.get("state") == "open" and pr.get("merged") is False
            and pr["head"]["sha"] == sha and pr["base"]["sha"] == current
            and pr["head"]["ref"] == ref, "release PR moved or previously merged")
    return state


def verify_merged_release(*, main_before, release_sha, candidate_sha,
                          version, zip_sha):
    """Read actual remote main/tree/tag/history/ZIP, no optimistic merge success."""
    main = gh("GET", "/branches/main")["commit"]["sha"]
    require(hash40(main), "postmerge main SHA absent")
    commit = gh("GET", "/git/commits/" + main)
    require([x["sha"] for x in commit["parents"]] == [main_before, release_sha],
            "release PR not merged atomically on exact previous main")
    tagged = gh("GET", "/git/ref/tags/v" + version)
    require(tagged["object"]["sha"] == candidate_sha,
            "source tag doesn't point to exact qualified Candidate")
    before = tree_map(main_before)
    after = tree_map(main)
    changed = {k for k in (set(before) | set(after)) if before.get(k) != after.get(k)}
    allowed = {"downloads/" + downloads.filename(version),
               "downloads/releases.json", "downloads/latest.json", "downloads/README.md"}
    require(changed == allowed, "postmerge changed previous binary/history/source paths")
    archive = blob_bytes(after["downloads/" + downloads.filename(version)])
    require(hashlib.sha256(archive).hexdigest() == zip_sha,
            "public ZIP bytes do not match approved ZIP hash")
    latest = json.loads(blob_bytes(after["downloads/latest.json"]))
    catalog = json.loads(blob_bytes(after["downloads/releases.json"]))
    require(latest == catalog["releases"][0]
            and latest["version"] == version
            and latest["sourceSha"] == candidate_sha
            and latest["sha256"] == zip_sha
            and latest["size"] == len(archive),
            "public releases index or latest pointer drift")
    require(gh("GET", "/branches/main")["commit"]["sha"] == main,
            "main advanced during postmerge readback")
    return {"result": "MERGE_AND_BYTES_VERIFIED", "version": version,
            "mainSha": main, "sha256": zip_sha, "sourceSha": candidate_sha}


def finish(root, branch_name, release_sha):
    evidence = check_live_staged_release(root, branch_name, release_sha)
    old_main, source = evidence["mainSha"], evidence["candidateSha"]
    v, sha = evidence["version"], evidence["sha256"]
    # The tag is created only after everything is approved and proven.
    # If the merge later fails this preexisting tag is an ATTENTION checkpoint,
    # never a reason to rerun writes blindly.
    require(gh("GET", "/git/ref/tags/v" + v, allow404=True) is None,
            "source tag already exists; inspect manually")
    require(gh("GET", "/branches/main")["commit"]["sha"] == old_main
            and branch(branch_name)["object"]["sha"] == release_sha,
            "concurrent GitHub change before publication")
    gh("POST", "/git/refs", {"ref": "refs/tags/v" + v, "sha": source})
    require(gh("GET", "/git/ref/tags/v" + v)["object"]["sha"] == source,
            "tag create uncertain; do not retry")
    merged = gh("PUT", "/pulls/" + str(evidence["pr"]) + "/merge",
                {"sha": release_sha, "merge_method": "merge",
                 "commit_title": "Release Razer Health Center v" + v,
                 "commit_message": "Owner-authorized exact RHC22 archive and source. "
                                   "No inferred native/signing/rollback approvals."})
    require(merged.get("merged") is True and hash40(merged.get("sha")),
            "release PR merge ambiguous; inspect GitHub before retry")
    check = verify_merged_release(main_before=old_main, release_sha=release_sha,
                                  candidate_sha=source, version=v, zip_sha=sha)
    # Remove only unchanged verified merged release branch; do not rely on token
    # recursion automatically firing a branch-cleanup workflow.
    require(branch(branch_name)["object"]["sha"] == release_sha,
            "release branch changed; cannot safely clean")
    gh("DELETE", "/git/refs/heads/" + branch_name)
    require(branch(branch_name) is None, "release cleanup unverified")
    check["releaseBranchRemoved"] = True
    check["result"] = "PUBLISHED_VERIFIED"
    return check


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--release-branch", required=True)
    p.add_argument("--release-sha", required=True)
    args = p.parse_args()
    print("RHC_RELEASE_FINAL=" + json.dumps(finish(
        args.root, args.release_branch, args.release_sha), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as err:
        print("RHC_RELEASE_FINAL=BLOCKED_ATTENTION: " + str(err), file=sys.stderr)
        sys.exit(1)
