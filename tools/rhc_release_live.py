#!/usr/bin/env python3
"""RHC-20 gated Release-PR controller. NEVER automatic from a Candidate pass.

The only write path is explicit 'stage' with an immutable, owner-comment-bound
approval verified live in issue 22 and a truly enabled policy + effective main
ruleset. 'finish' rechecks every gate, hosted statuses, and actual PR metadata.
No approval can be inferred from fixtures, CI or ChatGPT/user convenience.
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import rhc_downloads as downloads
from rhc_release_contracts import require, version_from_model
from rhc_release_transaction import (
    CANDIDATE, RELEASE, hash40, hash64,
    trusted_contexts, validate_main_rules,
)

OWNER = "SaschaP1980"
REPO = OWNER + "/RazerHealthCenter"
# Main branch rules apply to all PRs. Release-only contexts remain an
# independent exact-SHA prerequisite enforced in rhc_release_finish.py.
MAIN_CONTEXTS = ["rhc/infra/linux", "rhc/infra/windows"]


def gh(method, endpoint, payload=None, allow404=False):
    """gh api, explicit JSON payload; uncertain writes never auto-replayed."""
    cmd = ["gh", "api", "-X", method, "repos/" + REPO + endpoint]
    if payload is not None:
        cmd += ["--input", "-"]
    done = subprocess.run(cmd, text=True,
                          input=json.dumps(payload) if payload is not None else None,
                          capture_output=True, check=False)
    if allow404 and done.returncode and "HTTP 404" in done.stderr:
        return None
    require(done.returncode == 0,
            "GitHub " + method + " " + endpoint +
            " ambiguous/failure: " + done.stderr[-250:] + ". Inspect before retry.")
    return json.loads(done.stdout) if done.stdout.strip() else {}


def branch(branch):
    return gh("GET", "/git/ref/heads/" + branch, allow404=True)


def content_json(path, ref):
    require(hash40(ref), "missing exact content source SHA")
    resp = gh("GET", "/contents/" + path + "?ref=" + ref)
    require(resp.get("encoding") == "base64", "unreadable GitHub content " + path)
    return json.loads(base64.b64decode(resp["content"]))


def record_approval(issue_comment_id, version, candidate_sha, archive_sha, policy):
    """Owner alone may explicitly authorize exact artefact and all native evidence."""
    require(isinstance(issue_comment_id, int) and issue_comment_id > 0,
            "missing concrete owner Issue #22 comment ID")
    comment = gh("GET", "/issues/comments/" + str(issue_comment_id))
    require(comment.get("user", {}).get("login") == OWNER
            and comment.get("issue_url", "").endswith("/issues/22"),
            "release acceptance not authored by repository Owner on RHC-22")
    data = comment.get("body", "")
    token = ("RHC-RELEASE-APPROVAL version=" + version +
             " sourceSha=" + candidate_sha +
             " archiveSha256=" + archive_sha +
             " signing=" + policy["signingDecision"])
    require(token in data and data.count(token) == 1,
            "no unique version/source/ZIP/signing-bound approval in Issue #22")
    require("NATIVE-RAZER-ACCEPTANCE=VERIFIED" in data
            and "NATIVE-ROLLBACK=VERIFIED" in data
            and "FIRST-RELEASE-RECOVERY=VERIFIED" in data,
            "physical Razer and native rollback records absent in owner approval")
    if policy["signingDecision"] == "unsigned-approved":
        require("UNSIGNED-SMARTSCREEN-RISK=EXPLICITLY-ACCEPTED" in data,
                "owner has not explicitly accepted SmartScreen/unknown publisher risk")
    else:
        require("AUTHENTICODE-CERT-CHAIN=VERIFIED" in data
                and "AUTHENTICODE-PUBLISHER=" in data,
                "verified Authenticode publisher absent")
    return {"id": issue_comment_id, "owner": OWNER,
            "url": comment.get("html_url"), "version": version,
            "sourceSha": candidate_sha, "archiveSha256": archive_sha}


def required_main_rules():
    rulesets = gh("GET", "/rulesets")
    active = [r for r in rulesets if r.get("enforcement") == "active"]
    evidence = [gh("GET", "/rulesets/" + str(r["id"])) for r in active]
    # Do not combine independent rulesets to fabricate effective checks: one
    # active ruleset must target main and enforce PR + ALL required checks.
    for rule in evidence:
        conditions = rule.get("conditions", {}).get("ref_name", {})
        include = conditions.get("include", [])
        if "~DEFAULT_BRANCH" not in include and "refs/heads/main" not in include:
            continue
        verdict = validate_main_rules(rule.get("rules", []), MAIN_CONTEXTS)
        if verdict["effective"]:
            return {"rulesetId": rule["id"], "result": "EFFECTIVE"}
    raise ValueError("Main requires owner/admin configured PR + hosted status rules; "
                     "existing deletion/non_fast_forward alone is not enough")


def validate_prewrite(root, candidate_sha, expected_main, version,
                      artifact1, artifact2, owner_comment_id):
    """Reads only; does not create a branch/blob/tag or permit synthetic gates."""
    require(os.getenv("GITHUB_REPOSITORY") == REPO and os.getenv("GH_TOKEN"),
            "trusted repository token needed")
    require(hash40(candidate_sha) and hash40(expected_main),
            "exact Candidate/Main SHAs required")
    root = Path(root).resolve()
    require(root.is_dir(), "source root missing")
    require(version == version_from_model(root), "source checkout/version mismatch")
    require(gh("GET", "/branches/main")["commit"]["sha"] == expected_main,
            "main advanced before staging")
    cbranch = "candidate/v" + version
    candidate = branch(cbranch)
    require(candidate and candidate["object"]["sha"] == candidate_sha,
            "candidate ref drift")
    commit = gh("GET", "/git/commits/" + candidate_sha)
    require([x["sha"] for x in commit.get("parents", [])] == [expected_main],
            "candidate no longer a single current-main child")
    # The Release PR must promote EXACTLY the Candidate's two application
    # source changes alongside its ZIP/catalog. Otherwise main/model.go
    # remains an older version than the published package, and future
    # Candidate ancestry/version checks become inconsistent.
    diff = gh("GET", "/compare/" + expected_main + "..." + candidate_sha)
    require(diff.get("ahead_by") == 1 and diff.get("behind_by") == 0
            and {x.get("filename") for x in diff.get("files", [])}
                == {"model.go", "CHANGELOG.md"}
            and {x.get("status") for x in diff["files"]}
                <= {"added", "modified"},
            "Candidate source differs from exact two-file version-only contract")
    trusted_contexts(gh("GET", "/commits/" + candidate_sha + "/statuses"), CANDIDATE)
    policy = content_json("config/rhc-release-policy.json", expected_main)
    require(policy.get("productionEnabled") is True
            and policy.get("rollbackVerified") is True
            and policy.get("distribution") == "repo-downloads"
            and policy.get("signingDecision") in ("signed-verified", "unsigned-approved"),
            "real production activation missing")
    required_main_rules()
    require(branch("release/v" + version) is None,
            "release branch already exists; inspect, NEVER blind retry")
    require(gh("GET", "/git/ref/tags/v" + version, allow404=True) is None,
            "immutable source tag already exists")
    src = root / "downloads"
    downloads.verify(src)
    require(not (src / downloads.filename(version)).exists(),
            "version already public or previously staged")
    a, b = Path(artifact1).resolve(), Path(artifact2).resolve()
    require(a != b and all(x.is_file() and not x.is_symlink() and
            x.name == "RazerHealthCenter.exe" and not x.is_relative_to(root)
            for x in (a, b)), "two external independent executable outputs required")
    require(a.read_bytes() == b.read_bytes(), "independent PE builds disagree")
    return policy


def dry_shadow_release(root, candidate_sha, version, exe_a, exe_b,
                       stage, published_utc):
    """Disposable, byte-verified, single-transaction local staging, no network."""
    root, stage = Path(root).resolve(), Path(stage).resolve()
    require(not stage.exists() and not stage.is_relative_to(root)
            and not root.is_relative_to(stage),
            "unsafe staging path / existing transaction")
    stage.mkdir(parents=True)
    dest1, dest2 = stage / "build1", stage / "build2"
    dest1.mkdir()
    dest2.mkdir()
    a, b = dest1 / downloads.filename(version), dest2 / downloads.filename(version)
    downloads.make_lean_zip(root, exe_a, a)
    downloads.make_lean_zip(root, exe_b, b)
    require(a.read_bytes() == b.read_bytes(), "release ZIP bytes not reproducible")
    shadow = stage / "downloads"
    shutil.copytree(root / "downloads", shadow)
    before = {p.relative_to(root / "downloads").as_posix():
              hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (root / "downloads").rglob("*") if p.is_file()}
    record = downloads.stage_release(shadow, a, version, published_utc,
                                     candidate_sha)
    after = {p.relative_to(root / "downloads").as_posix():
             hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (root / "downloads").rglob("*") if p.is_file()}
    require(before == after, "original public downloads were mutated")
    require(downloads.verify(shadow)[0] == record, "shadow read-back incomplete")
    return record, shadow


def git_blob(data, binary):
    if binary:
        payload = {"content": base64.b64encode(data).decode("ascii"),
                   "encoding": "base64"}
    else:
        payload = {"content": data.decode("utf-8"), "encoding": "utf-8"}
    result = gh("POST", "/git/blobs", payload)
    require(hash40(result.get("sha")), "Git blob upload cannot be verified")
    return result["sha"]


def stage(args):
    """Write-enabled only AFTER full owner/GitHub/hardware/rollback hard-gate."""
    require(os.getenv("RHC_REAL_PUBLICATION_APPROVED") == "EXPLICIT_OWNER_RHC22",
            "publication mode not expressly enabled")
    policy = validate_prewrite(args.root, args.candidate_sha, args.main_sha,
                               args.version, args.exe_a, args.exe_b,
                               args.owner_comment_id)
    # No commit/branch even after synthetic tests; actual owner-bound approval
    # checked against the computed package hash BEFORE first GitHub write.
    with tempfile.TemporaryDirectory(prefix="rhc-release-exact-") as tmp:
        record, staged = dry_shadow_release(
            args.root, args.candidate_sha, args.version,
            args.exe_a, args.exe_b, Path(tmp) / "shadow-stage", args.published_utc)
        approval = record_approval(args.owner_comment_id, args.version,
                                   args.candidate_sha, record["sha256"], policy)
        require(gh("GET", "/branches/main")["commit"]["sha"] == args.main_sha
                and branch("release/v" + args.version) is None,
                "race on main or release ref before write")
        prior = gh("GET", "/git/commits/" + args.main_sha)
        # A single Release PR/merge atomically advances the app source
        # and publishes the matching immutable ZIP plus three index files.
        # Only the exact Candidate source files are copied into the main
        # parent tree; never copy unrelated Work or build artifacts.
        files = [("model.go", Path(args.root) / "model.go"),
                 ("CHANGELOG.md", Path(args.root) / "CHANGELOG.md")]
        files += [("downloads/" + file.name, file)
                  for file in (staged / record["file"],
                               staged / "releases.json",
                               staged / "latest.json",
                               staged / "README.md")]
        objects = []
        for relative, file in files:
            require(file.is_file() and not file.is_symlink(),
                    "missing or unsafe release source: " + relative)
            objects.append({"path": relative, "mode": "100644", "type": "blob",
                            "sha": git_blob(file.read_bytes(), file.suffix == ".zip")})
        tree = gh("POST", "/git/trees", {"base_tree": prior["tree"]["sha"],
                                       "tree": objects})["sha"]
        require(hash40(tree), "release tree invalid")
        commit = gh("POST", "/git/commits", {
            "message": "chore(release): stage immutable " + args.version +
                       "\n\nSource-SHA: " + args.candidate_sha +
                       "\nOwner-Approval-Comment: " + str(approval["id"]) +
                       "\nRHC-Issue: 22",
            "tree": tree, "parents": [args.main_sha]})["sha"]
        require(hash40(commit), "release commit invalid")
        gh("POST", "/git/refs",
           {"ref": "refs/heads/release/v" + args.version, "sha": commit})
        checked = branch("release/v" + args.version)
        require(checked and checked["object"]["sha"] == commit,
                "release branch ambiguous after create; do not retry")
        pr = gh("POST", "/pulls", {
            "title": "[Release v" + args.version + "] Owner-authorized immutable RHC ZIP",
            "head": "release/v" + args.version, "base": "main",
            "draft": True,
            "body": "RHC-22 owner approval: " + approval["url"] +
                    "\nCandidate-SHA: " + args.candidate_sha +
                    "\nArchive-SHA256: " + record["sha256"] +
                    "\nManual/automated merge must independently qualify "
                    "release/status/physical and hash gates; no issue-closing directives."})
        require(isinstance(pr.get("number"), int), "PR creation uncertain: inspect")
        # GITHUB_TOKEN-created branch/PR events do not reliably trigger CI.
        # An explicit workflow_dispatch is essential for exact release SHA gates.
        gh("POST", "/actions/workflows/rhc-release-preflight.yml/dispatches",
           {"ref": "release/v" + args.version})
        # GITHUB_TOKEN-created PRs do not reliably fire pull_request CI.
        # The main Ruleset requires the common Linux+Windows jobs even for
        # a Release PR; explicitly dispatch them on this exact release ref.
        gh("POST", "/actions/workflows/rhc-infrastructure-ci.yml/dispatches",
           {"ref": "release/v" + args.version})
        return {"result": "STAGED_PUBLIC_BRANCH_NOT_YET_MERGED",
                "pr": pr["number"], "releaseSha": commit, "version": args.version,
                "candidateSha": args.candidate_sha, "archiveSha256": record["sha256"],
                "ownerApproval": approval["id"]}


def cli():
    p = argparse.ArgumentParser(description="RHC-20 gated owner-authorized release staging")
    p.add_argument("action", choices=["stage"])
    for flag in ("root", "exe-a", "exe-b", "candidate-sha",
                 "main-sha", "version", "published-utc"):
        p.add_argument("--" + flag, required=True)
    p.add_argument("--owner-comment-id", type=int, required=True)
    a = p.parse_args()
    if a.action == "stage":
        print("RHC_RELEASE_STAGE=" + json.dumps(stage(a), sort_keys=True))


if __name__ == "__main__":
    try:
        cli()
    except (ValueError, OSError, KeyError, TypeError) as e:
        print("RHC_RELEASE_STAGE=BLOCKED_ATTENTION: " + str(e), file=sys.stderr)
        sys.exit(1)
