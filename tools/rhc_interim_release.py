#!/usr/bin/env python3
"""RHC-34 v3.0.8.1-only interim release qualification (pure, fail-closed).

The normal RHC-22 production flow remains unchanged and blocked. This
alternate explicitly noncertified path NEVER upgrades Phase B evidence, nor
turns productionEnabled/rollbackVerified/signingDecision on.
"""
import argparse
import json
import re
import sys

VERSION="3.0.8.1"
SHA40=re.compile(r"[0-9a-f]{40}\Z")
SHA64=re.compile(r"[0-9a-f]{64}\Z")
DISCLOSURE=("Interim release v3.0.8.1: unsigned Windows executable; publisher "
            "not verified. Windows Defender SmartScreen may warn about an "
            "unknown publisher. Razer physical-hardware acceptance and native "
            "rollback have NOT been verified. Do not disable Windows protection.")
PHASE_B={"hardware":"DEFERRED", "rollback":"DEFERRED",
         "publisherTrust":"NOT_VERIFIED", "rulesetAdmin":"DEFERRED"}
CHANGED=["downloads/README.md",
         "downloads/RazerHealthCenter-Portable-v3.0.8.1.zip",
         "downloads/latest.json", "downloads/releases.json"]


def must(ok,reason):
    if not ok:
        raise ValueError(reason)


def qualify(s):
    must(isinstance(s,dict),"interim release snapshot absent")
    must(s.get("version")==VERSION and s.get("changelogVersion")==VERSION,
         "interim exception only for exact 3.0.8.1 source/changelog")
    sha=s.get("sourceSha")
    must(isinstance(sha,str) and SHA40.fullmatch(sha)
         and sha==s.get("mainSha"),
         "interim source must be identical to main already at 3.0.8.1")
    policy=s.get("policy")
    must(isinstance(policy,dict) and
         policy.get("productionEnabled") is False
         and policy.get("rollbackVerified") is False
         and policy.get("signingDecision")=="unknown"
         and policy.get("distribution")=="repo-downloads",
         "standard production policy unexpectedly modified")
    must(s.get("phaseB")==PHASE_B,"Phase B evidence must be explicitly deferred")
    must(s.get("linux")=="SUCCESS" and s.get("nativeWindows")=="SUCCESS",
         "independent Linux/native Windows qualification missing")
    must(s.get("exeSignature")=="NotSigned",
         "actual unsigned EXE signature must match disclosure")
    must(s.get("archiveFile")=="RazerHealthCenter-Portable-v"+VERSION+".zip"
         and s.get("archiveFiles")==7
         and s.get("archiveReproducible") is True,
         "non-reproducible, mislabeled or unsafe ZIP")
    digest=s.get("archiveSha256")
    must(isinstance(digest,str) and SHA64.fullmatch(digest),
         "actual seven-file archive SHA-256 absent")
    must(s.get("existingTag") is False and s.get("existingArchive") is False
         and s.get("previousReleases")==0,
         "release already published or old immutable history at risk")
    return {
        "version":VERSION, "sourceSha":sha,
        "archiveSha256":digest,
        "archiveFile":s["archiveFile"],
        "classification":"INTERIM_UNSIGNED_UNCERTIFIED_RELEASE",
        "disclosure":DISCLOSURE,
        "phaseBVerified":False,
        "phaseB":dict(PHASE_B),
        "releaseChangedPaths":list(CHANGED),
        "status":"ELIGIBLE_FOR_INTERIM_RELEASE_NOT_PUBLISHED",
    }


def main():
    ap=argparse.ArgumentParser(description="Bounded v3.0.8.1 interim release evidence gate")
    ap.add_argument("--snapshot",required=True)
    args=ap.parse_args()
    with open(args.snapshot,encoding="utf-8") as f:
        snapshot=json.load(f)
    print("RHC34_INTERIM_GATE="+json.dumps(qualify(snapshot),sort_keys=True))


if __name__=="__main__":
    try:
        main()
    except (ValueError,KeyError,TypeError,OSError) as e:
        print("RHC34_INTERIM_GATE=BLOCKED: "+str(e),file=sys.stderr)
        sys.exit(1)
