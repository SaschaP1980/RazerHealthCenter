#!/usr/bin/env python3
"""RHC-43: reusable unsigned/uncertified *eligibility* gate (no GitHub writes).

This module is NOT a publisher. Publication, hosted native Windows evidence
and remote GitHub postverification are separate mandatory actions.
The standard production policy remains fail-closed.
"""
import argparse
import json
import re
import sys

VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")

PHASE_B = {"hardware": "DEFERRED", "rollback": "DEFERRED",
           "publisherTrust": "NOT_VERIFIED", "rulesetAdmin": "DEFERRED"}
POLICY = {"productionEnabled": False, "rollbackVerified": False,
          "signingDecision": "unknown", "distribution": "repo-downloads"}


def require(ok, explanation):
    if not ok:
        raise ValueError(explanation)


def parts(value):
    require(isinstance(value, str) and VERSION.fullmatch(value),
            "invalid four-part version")
    return tuple(int(n) for n in value.split("."))


def qualify(snapshot):
    """Validate exact process evidence; never claim or perform public release."""
    require(isinstance(snapshot, dict), "missing reusable interim evidence")
    require(snapshot.get("mode") == "interim-unsigned",
            "only explicit interim unsigned mode may use this contract")
    issue = snapshot.get("issue")
    require(type(issue) is int and issue > 0 and
            snapshot.get("ownerProcessAuthorized") is True,
            "explicit owner process authorization and valid Issue required")

    version = snapshot.get("version")
    current = parts(version)
    previous = snapshot.get("previousLatestVersion")
    prior = parts(previous)
    require(current[:3] == prior[:3] and current[3] == prior[3] + 1,
            "target must be exactly next four-part HOTFIX after public latest")
    require(snapshot.get("releaseProfile") == "version-only",
            "only the version-only release profile is qualified")
    require(snapshot.get("referenceVersion") == version
            and snapshot.get("changelogVersion") == version,
            "app/reference/changelog version drift")

    sha = snapshot.get("sourceSha")
    require(isinstance(sha, str) and SHA40.fullmatch(sha)
            and sha == snapshot.get("mainSha"),
            "source SHA must equal frozen version-ready main")
    require(snapshot.get("policy") == POLICY,
            "standard production policy must remain false/unknown/false")
    require(snapshot.get("phaseB") == PHASE_B,
            "external Phase B must remain explicitly unverified/deferred")

    require(snapshot.get("linux") == "SUCCESS"
            and snapshot.get("nativeWindows") == "SUCCESS",
            "independent hosted Linux and native Windows qualification missing")
    require(snapshot.get("exeSignature") == "NotSigned",
            "unsigned executable signature must be measured as NotSigned")
    require(snapshot.get("twoIndependentPeBuilds") is True
            and snapshot.get("twoIndependentZipBuilds") is True
            and snapshot.get("archiveReproducible") is True,
            "two independent bit-identical PE and ZIP builds required")

    archive = "RazerHealthCenter-Portable-v" + version + ".zip"
    require(snapshot.get("archiveFile") == archive
            and type(snapshot.get("archiveFiles")) is int
            and snapshot["archiveFiles"] == 7
            and type(snapshot.get("archiveSize")) is int
            and snapshot["archiveSize"] > 0,
            "canonical immutable seven-file Portable archive required")
    require(isinstance(snapshot.get("archiveSha256"), str)
            and SHA64.fullmatch(snapshot["archiveSha256"]),
            "archive SHA-256 must be actual 64-digit digest")
    require(isinstance(snapshot.get("exeSha256"), str)
            and SHA64.fullmatch(snapshot["exeSha256"]),
            "EXE SHA-256 must be actual 64-digit digest")
    require(type(snapshot.get("previousReleaseCount")) is int
            and snapshot["previousReleaseCount"] >= 1
            and snapshot.get("previousHistoryIntact") is True,
            "existing public release history must be verified and unchanged")
    require(snapshot.get("existingTag") is False
            and snapshot.get("existingArchive") is False,
            "target version already has tag or archive")

    notice = (
        "Interim release v" + version +
        ": unsigned Windows executable; publisher not verified. "
        "Windows Defender SmartScreen may warn about an unknown publisher. "
        "Physical Razer hardware acceptance and native rollback have NOT "
        "been verified. Do not disable Windows security protection."
    )
    return {
        "status": "ELIGIBLE_NOT_PUBLISHED",
        "classification": "INTERIM_UNSIGNED_UNCERTIFIED_RELEASE",
        "version": version,
        "previousLatestVersion": previous,
        "sourceSha": sha,
        "archiveFile": archive,
        "archiveSha256": snapshot["archiveSha256"],
        "exeSha256": snapshot["exeSha256"],
        "disclosure": notice,
        "phaseBVerified": False,
        "phaseB": dict(PHASE_B),
        "releaseChangedPaths": [
            "downloads/README.md", "downloads/" + archive,
            "downloads/latest.json", "downloads/releases.json"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="RHC-43 read-only reusable interim eligibility; never publishes")
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    with open(args.snapshot, encoding="utf-8") as handle:
        snapshot = json.load(handle)
    print("RHC43_INTERIM_ELIGIBILITY=" + json.dumps(
        qualify(snapshot), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        print("RHC43_INTERIM_ELIGIBILITY=BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(1)
