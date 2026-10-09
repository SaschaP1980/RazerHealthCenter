#!/usr/bin/env python3
"""RHC-102: independent, read-only postpublication Git/ZIP source authority.

Runs only against an already published immutable main checkout. No tag, PR,
download or safety policy is ever mutated. Also handles infrastructure commits
after the version release by walking the main first-parent history.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import rhc_downloads
from rhc_release_contracts import version_from_model

HEX = re.compile(r"[0-9a-f]{40}\Z")
RELEASE_PATHS = {
    "model.go", "CHANGELOG.md", "downloads/README.md",
    "downloads/latest.json", "downloads/releases.json",
}
POLICY = dict(productionEnabled=False, rollbackVerified=False,
              signingDecision="unknown", distribution="repo-downloads")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def execute(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True,
                       text=True, timeout=60, check=False)
    require(p.returncode == 0, "git command failed: " + " ".join(args) +
            " " + p.stderr[:180])
    return p.stdout.strip()


def verify_commit_shape(graph, latest, current_version):
    """Pure, negative-testable graph and release-package provenance gate."""
    for key in ("main", "releaseMerge", "previousMain", "staged", "source"):
        require(isinstance(graph.get(key), str)
                and HEX.fullmatch(graph[key]), "invalid graph SHA: " + key)
    require(graph["source"] == latest["sourceSha"], "catalog source mismatch")
    require(graph["mergeParents"] == [graph["previousMain"], graph["staged"]],
            "release main must merge exact stage")
    require(graph["stagedParents"] == [graph["source"]],
            "release stage must have only ZIP-free Candidate as parent")
    require(graph["sourceParents"] == [graph["previousMain"]],
            "Candidate must descend directly from prior public main")
    require(graph["mergeTree"] == graph["stagedTree"],
            "public merge tree must exactly match stage")
    version = latest["version"]
    require(version == current_version and latest["tag"] == "v" + version,
            "current app/catalog/tag version mismatch")
    require(graph["tagSha"] == graph["source"], "tag not exact source Candidate")
    require(graph["previousVersion"] != version,
            "unchanged version is not a published update")
    expected = RELEASE_PATHS | {"downloads/RazerHealthCenter-Portable-v" +
                                 version + ".zip"}
    require(set(graph["releasePaths"]) == expected and
            len(graph["releasePaths"]) == 6,
            "release merged unexpected source/download paths")
    require(graph["laterSourceOrDownloadsDiff"] == [],
            "source/download archive mutated after public release merge")
    require(graph["oldZipDiff"] == [], "previous public ZIP contents mutated")
    return dict(result="PASS", mainSha=graph["main"],
                releaseMergeSha=graph["releaseMerge"],
                sourceSha=graph["source"], stagedSha=graph["staged"],
                version=version, sourceTag="v" + version,
                combinedPaths=len(expected))


def commit_parents(root, sha):
    values = execute(root, "rev-list", "--parents", "-n", "1", sha).split()
    require(values and values[0] == sha, "missing commit parents: " + sha)
    return values[1:]


def verify_live(root, expected_main="", expected_source="", expected_version=""):
    root = Path(root).resolve()
    main = execute(root, "rev-parse", "HEAD")
    require(HEX.fullmatch(main), "invalid current checkout")
    if expected_main:
        require(main == expected_main, "expected pinned public main drift")
    require(execute(root, "ls-remote", "origin", "refs/heads/main")
            .split()[0] == main, "live public main changed while verifying")
    require(execute(root, "status", "--porcelain", "--untracked-files=all") == "",
            "dirty release checkout")
    rows = rhc_downloads.verify(root / "downloads")
    latest = json.loads((root / "downloads/latest.json").read_text(encoding="utf-8"))
    require(rows and rows[0] == latest, "latest catalog and releases history mismatch")
    if expected_source:
        require(latest["sourceSha"] == expected_source,
                "expected publisher source mismatch")
    if expected_version:
        require(latest["version"] == expected_version,
                "expected product version mismatch")
    policy = json.loads((root / "config/rhc-release-policy.json").read_text())
    for key, value in POLICY.items():
        require(policy.get(key) == value, "unsafe production policy: " + key)
    version = version_from_model(root)
    source = latest["sourceSha"]
    require(HEX.fullmatch(source), "invalid source SHA")
    merges = execute(root, "rev-list", "--first-parent", "--merges", "HEAD").splitlines()
    matches = []
    for merge in merges:
        pp = commit_parents(root, merge)
        if len(pp) != 2:
            continue
        stage = pp[1]
        if commit_parents(root, stage) == [source]:
            matches.append((merge, pp[0], stage))
    require(len(matches) == 1, "not exactly one original published release merge")
    merged, previous, stage = matches[0]
    require(execute(root, "merge-base", "--is-ancestor", merged, "HEAD") == "",
            "release merge not ancestor of current public main")
    tag = execute(root, "ls-remote", "origin", "refs/tags/v" + latest["version"])
    require(tag, "immutable source version tag unavailable")
    tagsha = tag.split()[0]
    def diff(a, b, *paths):
        return execute(root, "diff", "--name-only", a, b, "--", *paths).splitlines()
    ptext = execute(root, "show", previous + ":model.go")
    versions = re.findall(r'(?m)^\s*appVersion\s*=\s*"([0-9.]+)"', ptext)
    require(len(versions) == 1, "previous main version unreadable")
    previous_files = execute(root, "ls-tree", "-r", "--name-only",
                             previous, "--", "downloads").splitlines()
    oldzips = [n for n in previous_files if n.endswith(".zip")]
    require(oldzips, "missing historical ZIP archive inventory")
    graph = dict(main=main, releaseMerge=merged, previousMain=previous,
                 staged=stage, source=source, mergeParents=commit_parents(root, merged),
                 stagedParents=commit_parents(root, stage),
                 sourceParents=commit_parents(root, source),
                 mergeTree=execute(root, "rev-parse", merged + "^{tree}"),
                 stagedTree=execute(root, "rev-parse", stage + "^{tree}"),
                 tagSha=tagsha, previousVersion=versions[0],
                 releasePaths=diff(previous, merged),
                 laterSourceOrDownloadsDiff=diff(merged, main, "model.go",
                                                   "CHANGELOG.md", "downloads"),
                 oldZipDiff=diff(previous, main, *oldzips))
    proof = verify_commit_shape(graph, latest, version)
    proof.update(previousVersion=versions[0],
                 unchangedHistoricalZIPs=len(oldzips), releaseHistory=len(rows),
                 publicZipBytes=latest["size"], publicZipSha256=latest["sha256"])
    require(execute(root, "ls-remote", "origin", "refs/heads/main")
            .split()[0] == main, "public main changed at final readback")
    return proof


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--expected-main", default="")
    parser.add_argument("--expected-source", default="")
    parser.add_argument("--expected-version", default="")
    args = parser.parse_args()
    result = verify_live(args.root, args.expected_main, args.expected_source,
                         args.expected_version)
    print("RHC102_POSTRELEASE_PROVENANCE=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError, KeyError) as exc:
        print("RHC102_POSTRELEASE_PROVENANCE=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(1)
