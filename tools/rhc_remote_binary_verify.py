#!/usr/bin/env python3
"""Independent read-only HTTPS byte evidence for any indexed RHC public ZIP.

The GitHub connector cannot transfer large binary archives. A GitHub-hosted
runner fetches the immutable commit-addressed raw URL and verifies the actual
network bytes independently of the checked-out catalog and ZIP. No publication,
artifact mutation, GitHub API token or source rewrite is performed here.
"""
import argparse
import hashlib
import json
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import rhc_downloads as downloads

REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
ORIGIN = "https://raw.githubusercontent.com"
CHUNK = 1024 * 1024


def verify_remote_binary(root, repository, commit_sha, version=None):
    """Return verified HTTP byte evidence; raise/fail closed for every mismatch."""
    if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
        raise ValueError("invalid GitHub repository identity")
    owner, name = repository.split("/")
    if owner in (".", "..") or name in (".", ".."):
        raise ValueError("unsafe repository identity")
    if not isinstance(commit_sha, str) or not SHA_RE.fullmatch(commit_sha) or commit_sha == "0" * 40:
        raise ValueError("invalid immutable 40-hex Git commit")
    if version is not None:
        downloads.norm_version(version)
    root = Path(root).resolve()
    rows = downloads.verify(root / "downloads")
    if not rows:
        raise ValueError("no published release to verify")
    record = next((row for row in rows if row["version"] == version), None) if version else rows[0]
    if record is None:
        raise ValueError("requested release version is not indexed")
    filename = downloads.filename(record["version"])
    if filename != record["file"]:
        raise ValueError("catalog filename mismatch")
    raw_url = (ORIGIN + "/" + repository + "/" + commit_sha + "/downloads/" +
               urllib.parse.quote(filename, safe=""))
    req = urllib.request.Request(raw_url, headers={
        "User-Agent": "RHC-Independent-Public-Binary-Readback/1.0",
        "Accept": "application/octet-stream",
    })
    total = 0
    hasher = hashlib.sha256()
    # Temporary file only; nothing is written to the source/release checkout.
    with tempfile.TemporaryDirectory(prefix="rhc-remote-readback-") as folder:
        path = Path(folder) / filename
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                if response.geturl() != raw_url:
                    raise ValueError("remote ZIP redirected away from immutable raw URL")
                with path.open("wb") as out:
                    while True:
                        chunk = response.read(CHUNK)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > record["size"]:
                            raise ValueError("HTTP ZIP response exceeds indexed size")
                        hasher.update(chunk)
                        out.write(chunk)
        except (OSError, TimeoutError) as exc:
            raise ValueError("HTTPS ZIP fetch failed: " + str(exc)) from exc
        if total != record["size"] or hasher.hexdigest() != record["sha256"]:
            raise ValueError("remote ZIP byte length or SHA-256 differs from indexed immutable ZIP")
        # This independently validates actual *fetched* package contents and
        # embedded SHA256SUMS, not just a catalog entry or Git blob metadata.
        if downloads.portable_zip_check(path) != record["packageFiles"]:
            raise ValueError("remote ZIP seven-file payload mismatch")
    # downloads.verify already proved the checked-out file is catalog-consistent.
    return {
        "result": "PASS", "transport": "HTTPS_GITHUB_RAW_EXACT_COMMIT",
        "repository": repository, "commitSha": commit_sha,
        "version": record["version"], "sourceSha": record["sourceSha"],
        "filename": filename, "bytes": total, "sha256": hasher.hexdigest(),
        "packageFiles": len(record["packageFiles"]), "url": raw_url,
        "scope": "REMOTE_PUBLIC_BINARY_BYTES_ONLY_NOT_SIGNING_OR_HARDWARE",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read-only immutable GitHub raw public ZIP byte audit")
    parser.add_argument("--root", default=".")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--version", default=None,
                        help="Optional indexed four-part version; otherwise current latest")
    args = parser.parse_args()
    result = verify_remote_binary(args.root, args.repository, args.commit_sha, args.version)
    print("RHC_PUBLIC_BINARY_READBACK=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("RHC_PUBLIC_BINARY_READBACK=FAIL: " + str(exc), file=sys.stderr)
        sys.exit(1)
