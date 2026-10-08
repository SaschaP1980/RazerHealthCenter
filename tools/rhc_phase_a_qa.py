#!/usr/bin/env python3
"""RHC-29: fail-closed QA ZIP plus provenance; ALWAYS nonpublishing.

This is NOT an Owner-approved release controller. Only produces an ephemeral
GitHub Actions TEST/UNSIGNED artifact outside the checkout. The RHC-22
hardware, rollback, signer/owner consent and production gates remain OPEN.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import rhc_downloads as downloads
from rhc_release_contracts import require, version_from_model

SCHEMA_VERSION = 1
CLASSIFICATION = "TEST_ONLY_NOT_RELEASE"
PHASE_B = {
    "status": "DISABLED",
    "hardwareAcceptance": "NOT_VERIFIED",
    "rollback": "NOT_VERIFIED",
    "ownerTrustApproval": "NOT_AUTHORIZED",
    "productionRelease": "BLOCKED",
    "githubRulesetAdministration": "NOT_MODIFIED",
}
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inventory(path):
    """Read-only SHA fingerprint for all tracked/public download bytes."""
    p = Path(path)
    return {
        f.relative_to(p).as_posix(): digest(f.read_bytes())
        for f in p.rglob("*") if f.is_file()
    }


def checkout_sha(root):
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False)
    require(result.returncode == 0, "checkout source SHA unavailable")
    return result.stdout.strip()


def verify_source_and_policy(root, source_sha):
    root = Path(root).resolve()
    require(root.is_dir(), "missing QA source checkout")
    require(isinstance(source_sha, str) and SHA40.fullmatch(source_sha),
            "source SHA must be exact 40-hex commit")
    require(checkout_sha(root) == source_sha,
            "source SHA does not match exact checked-out Git commit")
    policy = json.loads((root / "config/rhc-release-policy.json").read_text(
        encoding="utf-8"))
    require(policy.get("productionEnabled") is False
            and policy.get("rollbackVerified") is False
            and policy.get("signingDecision") == "unknown"
            and policy.get("distribution") == "repo-downloads",
            "QA Phase A forbidden when actual production policy is enabled")
    downloads.verify(root / "downloads")
    require(not (root / "downloads/latest.json").exists(),
            "Phase A cannot use live product release index")
    return version_from_model(root)


def archive_name(version, sha):
    require(isinstance(source := sha, str) and SHA40.fullmatch(source),
            "source SHA must be exact 40-hex commit")
    return ("RazerHealthCenter-Portable-v" + version +
            "-TEST-UNSIGNED-" + source[:12] + ".zip")


def stage(root, exe_a, exe_b, stage, source_sha):
    root, stage = Path(root).resolve(), Path(stage).resolve()
    a, b = Path(exe_a).resolve(), Path(exe_b).resolve()
    require(stage != root and not stage.is_relative_to(root)
            and not root.is_relative_to(stage), "QA stage must be outside source")
    require(not stage.exists(), "QA stage already exists; inspect before retry")
    require(a != b and all(x.is_file() and not x.is_symlink()
            and x.name == "RazerHealthCenter.exe" and not x.is_relative_to(root)
            for x in (a, b)), "two independent executable outputs outside source required")
    require(a.read_bytes() == b.read_bytes(), "independent executable PE bytes differ")
    version = verify_source_and_policy(root, source_sha)
    original = inventory(root / "downloads")
    name = archive_name(version, source_sha)
    require(stage.parent.is_dir(), "missing external stage parent")
    with tempfile.TemporaryDirectory(prefix="rhc29-stage-", dir=stage.parent) as tmp:
        first, second = Path(tmp) / "first.zip", Path(tmp) / "second.zip"
        downloads.make_lean_zip(root, a, first)
        downloads.make_lean_zip(root, b, second)
        require(first.read_bytes() == second.read_bytes(),
                "independent seven-file QA ZIP bytes differ")
        data = first.read_bytes()
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "classification": CLASSIFICATION,
            "message": "TEST / UNSIGNED / NOT AN OFFICIAL RELEASE",
            "version": version,
            "sourceSha": source_sha,
            "archive": {
                "file": name,
                "sha256": digest(data),
                "size": len(data),
                "files": downloads.portable_zip_check(first),
            },
            "exeSha256": digest(a.read_bytes()),
            "buildEvidence": "TWO_BYTE_IDENTICAL_PE_BUILDS_AND_LEAN_ZIPS",
            "nativeWindowsEvidence": "SEE_EXACT_SHA_ACTIONS_RUN_NOT_HARDWARE",
            "phaseB": dict(PHASE_B),
        }
        require(inventory(root / "downloads") == original,
                "repository downloads changed during technical QA staging")
        stage.mkdir()
        shutil.copyfile(first, stage / name)
        (stage / "qa-evidence.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
    require(verify(root, stage, source_sha) == manifest,
            "staged QA evidence did not survive independent verification")
    return manifest


def verify(root, stage, source_sha):
    root, stage = Path(root).resolve(), Path(stage).resolve()
    require(stage != root and not stage.is_relative_to(root)
            and not root.is_relative_to(stage), "QA stage must be outside source")
    version = verify_source_and_policy(root, source_sha)
    require(stage.is_dir() and not stage.is_symlink(), "QA stage missing or linked")
    manifest_file = stage / "qa-evidence.json"
    require(manifest_file.is_file() and not manifest_file.is_symlink(),
            "QA evidence missing/unsafe")
    info = json.loads(manifest_file.read_text(encoding="utf-8"))
    require(isinstance(info, dict)
            and set(info) == {"schemaVersion", "classification", "message", "version",
                               "sourceSha", "archive", "exeSha256", "buildEvidence",
                               "nativeWindowsEvidence", "phaseB"},
            "QA evidence schema changed")
    require(info["schemaVersion"] == SCHEMA_VERSION
            and info["classification"] == CLASSIFICATION
            and info["message"] == "TEST / UNSIGNED / NOT AN OFFICIAL RELEASE"
            and info["sourceSha"] == source_sha
            and info["version"] == version
            and info["phaseB"] == PHASE_B
            and info["buildEvidence"] == "TWO_BYTE_IDENTICAL_PE_BUILDS_AND_LEAN_ZIPS"
            and info["nativeWindowsEvidence"] == "SEE_EXACT_SHA_ACTIONS_RUN_NOT_HARDWARE",
            "QA report falsely claims release/Phase B or mismatched source")
    archive_info = info["archive"]
    require(isinstance(archive_info, dict)
            and set(archive_info) == {"file", "sha256", "size", "files"}
            and archive_info["file"] == archive_name(version, source_sha)
            and isinstance(archive_info["sha256"], str)
            and SHA64.fullmatch(archive_info["sha256"])
            and isinstance(archive_info["size"], int)
            and not isinstance(archive_info["size"], bool)
            and archive_info["size"] > 0,
            "QA archive identity invalid")
    require({p.name for p in stage.iterdir()}
            == {"qa-evidence.json", archive_info["file"]},
            "unexpected QA stage content")
    file = stage / archive_info["file"]
    require(file.is_file() and not file.is_symlink(), "QA archive missing/unsafe")
    data = file.read_bytes()
    require(len(data) == archive_info["size"]
            and digest(data) == archive_info["sha256"], "QA ZIP hash/size mismatch")
    require(downloads.portable_zip_check(file) == archive_info["files"],
            "QA ZIP manifest/checksums or strict 7-file allowlist failed")
    import zipfile
    with zipfile.ZipFile(file) as z:
        exe_sha = digest(z.read("RazerHealthCenter.exe"))
    require(isinstance(info["exeSha256"], str)
            and SHA64.fullmatch(info["exeSha256"])
            and exe_sha == info["exeSha256"],
            "QA executable digest mismatch")
    return info


def cli():
    p = argparse.ArgumentParser(description="RHC-29 isolated TEST-ONLY QA evidence")
    p.add_argument("action", choices=["stage", "verify"])
    p.add_argument("--root", required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--exe-a")
    p.add_argument("--exe-b")
    args = p.parse_args()
    if args.action == "stage":
        require(args.exe_a and args.exe_b, "two independent EXE paths required")
        value = stage(args.root, args.exe_a, args.exe_b, args.stage, args.source_sha)
    else:
        value = verify(args.root, args.stage, args.source_sha)
    print("RHC29_QA_PHASE_A=" + json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    try:
        cli()
    except (OSError, ValueError, TypeError, KeyError, ImportError) as err:
        print("RHC29_QA_PHASE_A=BLOCKED: " + str(err), file=sys.stderr)
        sys.exit(1)
