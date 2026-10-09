#!/usr/bin/env python3
"""RHC-31: exact historical v3.0.8.1 Candidate eligibility for TEST-ONLY QA.

Never promotes any Candidate: old source SHA is *not* a child of current main.
GitHub statuses are read-only and must be the latest successful actions-bot
result on this exact SHA. Hardware/rollback/Owner approval never inferred.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CANDIDATE_REF = "candidate/v3.0.8.1"
CANDIDATE_SHA = "1b78ca928979e9507863a53ce2e4b25491544d5e"
VERSION = "3.0.8.1"
CONTEXTS = ("rhc/preflight/linux", "rhc/preflight/windows",
            "rhc/preflight/candidate")
HEX40 = re.compile(r"[a-f0-9]{40}\Z")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def qualify(snapshot):
    require(isinstance(snapshot, dict), "missing candidate snapshot")
    sha = snapshot.get("candidate_sha")
    require(sha == CANDIDATE_SHA and HEX40.fullmatch(sha),
            "only exact qualified v3.0.8.1 Candidate is eligible")
    require(snapshot.get("branch_sha") == sha
            and snapshot.get("checkout_sha") == sha,
            "Candidate ref/checkout/source SHA drift")
    require(snapshot.get("version") == VERSION, "QA version is not v3.0.8.1")
    parents = snapshot.get("parent_shas")
    require(isinstance(parents, list) and len(parents) == 1
            and isinstance(parents[0], str) and HEX40.fullmatch(parents[0]),
            "Candidate must be a single-parent atomic commit")
    require(snapshot.get("changed_paths") == ["CHANGELOG.md", "model.go"],
            "Candidate must change exactly two version-only source files")
    for label, content, ver in (
        ("candidate", snapshot.get("model"), VERSION),
        ("parent", snapshot.get("parent_model"), "3.0.8.0"),
    ):
        require(isinstance(content, str), label + " model bytes missing")
        for literal in ("appVersion", "referenceVersion"):
            pattern = r"(?m)^\s*" + literal + r'\s*=\s*"' + re.escape(ver) + r'"'
            require(len(re.findall(pattern, content)) == 1,
                    label + " model " + literal + " wrong or ambiguous")
    changelog = snapshot.get("changelog")
    require(isinstance(changelog, str) and
            "## 3.0.8.1" in changelog and
            "Version-only" in changelog,
            "candidate CHANGELOG/version-only identity invalid")
    p = snapshot.get("policy")
    require(isinstance(p, dict) and
            p.get("productionEnabled") is False and
            p.get("rollbackVerified") is False and
            p.get("signingDecision") == "unknown" and
            p.get("distribution") == "repo-downloads",
            "Phase B production policy must remain disabled")
    statuses = snapshot.get("statuses")
    require(isinstance(statuses, list), "GitHub bot statuses missing")
    recent = {}
    # GitHub /commits/:sha/statuses returns newest first; the first observed
    # row for any context is the effective, authoritative status.
    for row in statuses:
        require(isinstance(row, dict), "invalid commit status item")
        context = row.get("context")
        if isinstance(context, str) and context not in recent:
            recent[context] = row
    for context in CONTEXTS:
        row = recent.get(context)
        require(row is not None and row.get("state") == "success"
                and isinstance(row.get("creator"), dict)
                and row["creator"].get("login") == "github-actions[bot]",
                "missing/failed/untrusted latest Candidate status: " + context)
    return {"sourceSha": sha, "version": VERSION,
            "classification": "TEST_ONLY_NOT_RELEASE",
            "phaseB": "DISABLED", "qualifyingContexts": list(CONTEXTS),
            "candidateBranch": CANDIDATE_REF,
            "currentMainParentage": "NOT_CLAIMED_OLD_CANDIDATE"}


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], check=False,
                            capture_output=True, text=True, encoding="utf-8")
    require(result.returncode == 0, "git Candidate inspection failed: " + " ".join(args))
    return result.stdout.strip()


def inspect(root, sha, statuses):
    root = Path(root).resolve()
    require(root.is_dir() and not root.is_symlink(), "Candidate checkout missing")
    require(sha == CANDIDATE_SHA, "unapproved Candidate SHA")
    checkout = git(root, "rev-parse", "HEAD")
    remote = git(root, "ls-remote", "--exit-code", "origin",
                 "refs/heads/" + CANDIDATE_REF)
    # git ls-remote lines are 'SHA\trefs/heads/...'; exact one ref only.
    parts = remote.split()
    require(len(parts) == 2 and parts[1] == "refs/heads/" + CANDIDATE_REF,
            "unexpected/ambiguous remote Candidate ref")
    parent_line = git(root, "rev-list", "--parents", "-n", "1", "HEAD").split()
    require(parent_line and parent_line[0] == sha,
            "candidate commit changed during inspection")
    parents = parent_line[1:]
    changed = sorted(git(root, "diff-tree", "--no-commit-id", "--name-only",
                         "-r", "HEAD").splitlines())
    require(len(parents) == 1, "Candidate merge or missing parent")
    policy = json.loads((root / "config/rhc-release-policy.json").read_text(
        encoding="utf-8"))
    data = dict(candidate_sha=sha, branch_sha=parts[0], checkout_sha=checkout,
                version=VERSION, parent_shas=parents, changed_paths=changed,
                model=(root / "model.go").read_text(encoding="utf-8"),
                parent_model=git(root, "show", parents[0] + ":model.go"),
                changelog=(root / "CHANGELOG.md").read_text(encoding="utf-8"),
                statuses=statuses, policy=policy)
    return qualify(data)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--source", type=Path, required=True)
    a.add_argument("--sha", required=True)
    a.add_argument("--statuses", type=Path, required=True)
    args = a.parse_args()
    statuses = json.loads(args.statuses.read_text(encoding="utf-8"))
    result = inspect(args.source, args.sha, statuses)
    print("RHC31_CANDIDATE_QA_GATE=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, TypeError, KeyError) as error:
        print("RHC31_CANDIDATE_QA_GATE=BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(1)
