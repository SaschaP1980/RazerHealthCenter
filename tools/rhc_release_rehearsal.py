#!/usr/bin/env python3
"""Nonpublishing seven-file RHC release staging, isolated from repository/downloads."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import rhc_downloads as d
from rhc_release_contracts import version_from_model, require


def inventory(root):
    return {x.relative_to(root).as_posix(): hashlib.sha256(x.read_bytes()).hexdigest()
            for x in Path(root).rglob("*") if x.is_file()}


def rehearse(root, exe1, exe2, stage, source_sha):
    root, stage = Path(root).resolve(), Path(stage).resolve()
    a, b = Path(exe1).resolve(), Path(exe2).resolve()
    require(root.is_dir() and stage != root
            and not stage.is_relative_to(root) and not root.is_relative_to(stage),
            "stage must be outside source")
    require(not stage.exists(), "stage already exists: no blind retry")
    require(all(x.is_file() and x.name == "RazerHealthCenter.exe" and
                not x.is_symlink() and not x.is_relative_to(root) for x in (a, b)),
            "two external executable outputs required")
    require(a != b and a.read_bytes() == b.read_bytes(), "PE build bytes differ")
    require(isinstance(source_sha, str) and d.COMMIT.fullmatch(source_sha),
            "invalid source commit SHA")
    policy = json.loads((root/"config/rhc-release-policy.json").read_text())
    require(policy.get("productionEnabled") is False and
            policy.get("signingDecision") == "unknown" and
            policy.get("rollbackVerified") is False and
            policy.get("distribution") == "repo-downloads",
            "rehearsal requires blocked real production policy")
    original = root/"downloads"
    d.verify(original)
    original_files = inventory(original)
    require(not (original/"latest.json").exists(),
            "existing production latest pointer is not a rehearsal fixture")
    version = version_from_model(root)
    stage.mkdir(parents=True)
    one, two = stage/"a", stage/"b"
    one.mkdir()
    two.mkdir()
    first, second = one/d.filename(version), two/d.filename(version)
    d.make_lean_zip(root, a, first)
    d.make_lean_zip(root, b, second)
    require(first.read_bytes() == second.read_bytes(),
            "independent seven-file ZIP bytes differ")
    shadow = stage/"downloads"
    shutil.copytree(original, shadow)
    record = d.stage_release(shadow, first, version,
                             "2026-10-08T00:00:00Z", source_sha)
    require(d.verify(shadow) == [record], "staged catalog mismatch")
    for name in ("pointer", "orphan", "tamper"):
        broken = stage/("invalid-"+name)
        shutil.copytree(shadow, broken)
        if name == "pointer":
            (broken/"latest.json").write_text("{}", encoding="utf-8")
        elif name == "orphan":
            (broken/"unindexed.zip").write_bytes(b"orphan")
        else:
            (broken/record["file"]).write_bytes(b"tampered")
        try:
            d.verify(broken)
        except ValueError:
            pass
        else:
            raise ValueError("unsafe staged catalog accepted: "+name)
    require(d.verify(shadow) == [record], "good staged catalog was corrupted")
    d.verify(original)
    require(inventory(original) == original_files and
            not (original/"latest.json").exists(),
            "repository downloads changed during sandbox test")
    return {"result": "PASS_NONPUBLISHING_ONLY", "version": version,
            "sourceSha": source_sha, "sha256": record["sha256"],
            "size": record["size"], "files": len(record["packageFiles"]),
            "negativeCases": 3, "repositoryDownloadsModified": False}


if __name__ == "__main__":
    try:
        p = argparse.ArgumentParser()
        for name in ("root", "first-exe", "second-exe", "stage-root", "source-sha"):
            p.add_argument("--"+name, required=True)
        args = vars(p.parse_args())
        result = rehearse(args["root"], args["first_exe"],
                          args["second_exe"], args["stage_root"], args["source_sha"])
        print("RHC20_RELEASE_REHEARSAL="+json.dumps(result, sort_keys=True))
    except (ValueError, OSError) as exc:
        print("RHC20_RELEASE_REHEARSAL=BLOCKED: "+str(exc), file=sys.stderr)
        sys.exit(1)
