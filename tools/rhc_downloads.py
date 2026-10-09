#!/usr/bin/env python3
"""RHC repository-downloads catalog contracts; no GitHub publishing API.

Current CLI only VALIDATES committed download archives. The staging helpers
prepare files on a local release branch after external release authorization;
they never mutate a GitHub ref, push a tag or publish on their own.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import rhc_release_contracts as release

CATALOG_SCHEMA = 1
ZIP_PREFIX = "RazerHealthCenter-Portable-v"
SEMVER = release.SEMVER  # Single strict four-part application/release version contract.
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
EXPECTED_FILES = frozenset({"RazerHealthCenter.exe", "SHA256SUMS.txt", *release.PORTABLE_ASSETS})
EXPECTED_DIRS = frozenset(name + "/" for name in release.PORTABLE_DIRS)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def norm_version(value):
    require(isinstance(value, str) and SEMVER.fullmatch(value), "invalid semver")
    return tuple(map(int, value.split(".")))


def filename(version):
    norm_version(version)
    return ZIP_PREFIX + version + ".zip"


def timestamp(value):
    require(isinstance(value, str) and bool(value) and value.endswith("Z"),
            "publishedUtc must be UTC ISO-8601 with Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid publication timestamp") from exc
    require(parsed.tzinfo == timezone.utc, "publishedUtc must be UTC")
    return value


def catalog_read(downloads):
    loc = Path(downloads)
    obj = json.loads((loc / "releases.json").read_text(encoding="utf-8"))
    require(isinstance(obj, dict) and set(obj) == {"schemaVersion", "releases"}
            and obj["schemaVersion"] == CATALOG_SCHEMA
            and isinstance(obj["releases"], list), "invalid release history schema")
    return obj["releases"]


def portable_zip_check(path, *, strict_lean=True):
    archive = Path(path)
    require(archive.is_file() and not archive.is_symlink(), "missing portable ZIP")
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)) and z.testzip() is None,
                "duplicate or CRC-broken ZIP")
        names_regular = {n for n in names if not n.endswith("/")}
        names_dir = {n for n in names if n.endswith("/")}
        require(names_regular == EXPECTED_FILES, "portable payload allowlist mismatch")
        require(not names_dir if strict_lean else names_dir <= EXPECTED_DIRS,
                "unexpected or nested ZIP directory entries")
        for info in infos:
            part = PurePosixPath(info.filename)
            require(not part.is_absolute() and ".." not in part.parts
                    and "\\" not in info.filename and ":" not in info.filename
                    and info.filename == part.as_posix() + ("/" if info.is_dir() else "")
                    and not info.flag_bits & 0x1, "unsafe ZIP entry")
        payload = {n: z.read(n) for n in names_regular}
    require(payload["RazerHealthCenter.exe"].startswith(b"MZ"), "invalid Windows PE")
    require(not any(n.lower().endswith(".zip") for n in names_regular),
            "nested ZIP prohibited")
    expected = "".join(
        f"{hashlib.sha256(payload[n]).hexdigest()}  {n}\n"
        for n in sorted(names_regular - {"SHA256SUMS.txt"})
    ).encode("utf-8")
    require(payload["SHA256SUMS.txt"] == expected,
            "internal SHA256SUMS content invalid")
    return sorted(names_regular)


def make_lean_zip(root, exe, output):
    """Canonical directly extractable seven-file ZIP; no empty runtime dirs."""
    root, exe, output = Path(root).resolve(), Path(exe).resolve(), Path(output).resolve()
    require(exe.is_file() and exe.name == "RazerHealthCenter.exe", "invalid EXE path")
    require(root not in output.parents and output != exe, "ZIP output inside source")
    payload = {"RazerHealthCenter.exe": exe.read_bytes()}
    require(payload["RazerHealthCenter.exe"].startswith(b"MZ"), "invalid Windows PE")
    for target, origin in release.PORTABLE_ASSETS.items():
        f = root.joinpath(*PurePosixPath(origin).parts)
        require(f.is_file() and not f.is_symlink() and f.resolve().is_relative_to(root),
                "missing or unsafe portable asset: " + target)
        payload[target] = f.read_bytes()
    payload["SHA256SUMS.txt"] = "".join(
        f"{hashlib.sha256(payload[n]).hexdigest()}  {n}\n"
        for n in sorted(payload)
    ).encode("utf-8")
    with zipfile.ZipFile(output, "w") as z:
        for name in sorted(payload):
            release.zip_entry(z, name, payload[name])
    portable_zip_check(output)
    return output


def make_record(archive, version, utc, source_sha):
    """Stage metadata for a later authorized immutable publication transaction."""
    require(isinstance(source_sha, str) and COMMIT.fullmatch(source_sha),
            "invalid pinned source SHA")
    archive = Path(archive)
    require(archive.name == filename(version), "unexpected release ZIP filename")
    files = portable_zip_check(archive)
    data = archive.read_bytes()
    return {
        "schemaVersion": CATALOG_SCHEMA, "version": version, "tag": "v" + version,
        "file": archive.name, "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data), "publishedUtc": timestamp(utc),
        "sourceSha": source_sha, "packageFiles": files
    }


def render_readme(rows):
    head = [
        "# Razer Health Center — versioned Portable downloads",
        "",
        "This directory is the durable, immutable build archive (LBS model).",
        "Source code is versioned in GitHub and is **not** bundled in these ZIP files.",
        "A Windows Portable ZIP contains only the runnable payload, directly unpackable once.",
        "Published ZIPs must never be replaced or deleted; corrected builds get new versions.",
        "The index and pointer are updated together with exactly one new ZIP by a verified PR merge.",
        "Unreleased/unsigned QA artifacts from GitHub Actions are **not** official entries here.",
        "",
        "## Builds", "",
        "| Version | Portable ZIP | Size (bytes) | SHA-256 | Source commit |",
        "| --- | --- | ---: | --- | --- |"
    ]
    for row in rows:
        head.append(
            f"| {row['version']} | [{row['file']}]({row['file']}) "
            f"| {row['size']} | \`{row['sha256']}\` | \`{row['sourceSha']}\` |"
        )
    if not rows:
        head.append("| No authorized published build yet | — | — | — | — |")
    head.extend([
        "",
        "## Unsigned test builds (not official releases)",
        "",
        "An independently verified v3.0.8 **TEST / UNSIGNED** build is archived under [qa/](qa/README.md).",
        "QA archives are excluded from releases.json and latest.json and are not production releases.",
    ])
    if any(row["version"] == "3.0.8.1" for row in rows):
        head.extend([
            "",
            "## v3.0.8.1 interim-release disclosure (RHC-33)",
            "",
            "**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**",
            "This version is published under a documented temporary autonomous",
            "release path with Razer physical-device acceptance, native rollback,",
            "and Windows signing/SmartScreen owner approval deferred, NOT passed.",
            "Windows Defender SmartScreen may warn about an unknown publisher.",
            "Do not disable Windows security protection; verify the exact source",
            "commit, ZIP SHA-256 and internal SHA256SUMS before using this build.",
            "This disclosure does not mean Razer hardware behavior has been certified.",
        ])
    return "\n".join(head) + "\n"


QA_MANIFEST = {"schemaVersion":1,"classification":"TEST / UNSIGNED","officialRelease":False,"signed":False,"version":"3.0.8","file":"RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip","size":8696796,"sha256":"277757f4a09fa12791e2912c3a59f32f277ef8b65756b5f0dd491516738f97c0","exeSha256":"6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a","sourceCommit":"09bcc0bff174739e3945f072a346bd036a7f3e4d","sourceRunId":37761207280,"sourceArtifactId":11542516436}
QA_README = "# Razer Health Center v3.0.8 — TEST / UNSIGNED\n\n**TEST BUILD ONLY — NOT AN OFFICIAL RELEASE.** This file is published for manual Windows/Razer acceptance testing. It is not a production release, not a signed installer, and not the `latest.json` release.\n\n**Windows security:** `RazerHealthCenter.exe` has no Authenticode signature. Windows Defender SmartScreen or other security tools may warn about an unknown publisher. Do not disable security protection to use this test; only run this file if you trust its GitHub source and have verified the archive hash.\n\n## Package\n\n- [RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip](RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip) — original successful GitHub Actions artifact (unmodified).\n- ZIP size: **8,696,796 bytes**.\n- ZIP SHA-256: `277757f4a09fa12791e2912c3a59f32f277ef8b65756b5f0dd491516738f97c0`.\n- Windows EXE SHA-256: `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`.\n- Build source commit: [`09bcc0bff174739e3945f072a346bd036a7f3e4d`](https://github.com/SaschaP1980/RazerHealthCenter/commit/09bcc0bff174739e3945f072a346bd036a7f3e4d).\n- Provenance: [successful GitHub Actions run #37761207280](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37761207280), artifact ID `11542516436`.\n- Platform: Windows x64. ZIP contains exactly seven Portable files, `locales/de-DE.json` in its locale subfolder and no nested ZIP or Source ZIP.\n\n## Verify before manual testing\n\nAfter downloading the ZIP, run a read-only PowerShell hash check:\n\n```powershell\n(Get-FileHash .\\RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip -Algorithm SHA256).Hash.ToLowerInvariant()\n```\n\nCompare its output to the SHA-256 above. Extract the ZIP once. Internal `SHA256SUMS.txt` lists the checksums for the Portable runtime files. The health/repair functions remain subject to explicit safety controls; this hosted build does **not** constitute native Razer hardware acceptance.\n\n**Status:** QA archive only. Official `downloads/releases.json` remains empty and `downloads/latest.json` is absent. This archived TEST binary is never silently promoted to an official release.\n"

def verify_qa_archive(downloads):
    """Verify explicitly approved, immutable original TEST/UNSIGNED artifact."""
    qa = Path(downloads) / "qa"
    if not qa.exists():
        return 0  # Keeps unit-test fixtures and initial unreleased catalog valid.
    require(qa.is_dir() and not qa.is_symlink(), "QA archive path invalid")
    expected_names = {"README.md", "manifest.json", QA_MANIFEST["file"]}
    require({p.name for p in qa.iterdir()} == expected_names,
            "unexpected or missing QA archive contents")
    for filename in expected_names:
        require((qa / filename).is_file() and not (qa / filename).is_symlink(),
                "QA file missing or symlinked")
    record = json.loads((qa / "manifest.json").read_text(encoding="utf-8"))
    require(record == QA_MANIFEST, "QA metadata differs from pinned approved artifact")
    require((qa / "README.md").read_text(encoding="utf-8") == QA_README,
            "QA disclosure / README changed")
    package = qa / QA_MANIFEST["file"]
    raw = package.read_bytes()
    require(len(raw) == QA_MANIFEST["size"]
            and hashlib.sha256(raw).hexdigest() == QA_MANIFEST["sha256"],
            "QA test artifact archive hash or size mismatch")
    require(portable_zip_check(package) == sorted(EXPECTED_FILES),
            "QA Portable ZIP payload is not seven expected files")
    with zipfile.ZipFile(package) as z:
        exe_hash = hashlib.sha256(z.read("RazerHealthCenter.exe")).hexdigest()
    require(exe_hash == QA_MANIFEST["exeSha256"],
            "QA executable SHA mismatch")
    return 1


def verify(downloads):
    """Read-only full catalog/pointer/history/physical ZIP coherence check."""
    d = Path(downloads).resolve()
    require(d.is_dir() and not d.is_symlink(), "missing downloads directory")
    rows = catalog_read(d)
    require(rows == sorted(rows, key=lambda row: norm_version(row["version"]), reverse=True),
            "release records must be newest first")
    require(len({row["version"] for row in rows}) == len(rows),
            "duplicate release version")
    seen_files, seen_tags = set(), set()
    for row in rows:
        require(isinstance(row, dict)
                and set(row) == {"schemaVersion", "version", "tag", "file", "sha256",
                                 "size", "publishedUtc", "sourceSha", "packageFiles"}
                and row["schemaVersion"] == CATALOG_SCHEMA,
                "invalid release record")
        version = row["version"]
        norm_version(version)
        require(row["tag"] == "v" + version and row["file"] == filename(version),
                "release name/tag mismatch")
        require(row["file"] not in seen_files and row["tag"] not in seen_tags,
                "duplicate release name/tag")
        seen_files.add(row["file"])
        seen_tags.add(row["tag"])
        require(isinstance(row["sourceSha"], str) and COMMIT.fullmatch(row["sourceSha"]),
                "invalid source SHA")
        timestamp(row["publishedUtc"])
        require(isinstance(row["sha256"], str) and DIGEST.fullmatch(row["sha256"]),
                "invalid release digest")
        require(isinstance(row["size"], int) and not isinstance(row["size"], bool)
                and row["size"] > 0, "invalid release ZIP size")
        path = d / row["file"]
        require(path.is_file() and not path.is_symlink(), "missing versioned artifact")
        data = path.read_bytes()
        require(len(data) == row["size"]
                and hashlib.sha256(data).hexdigest() == row["sha256"],
                "release ZIP hash or size drift")
        require(portable_zip_check(path) == row["packageFiles"],
                "release ZIP file list drift")
    actual_zip_names = {p.name for p in d.glob("*.zip")}
    require(actual_zip_names == seen_files, "unindexed/removed versioned ZIP detected")
    latest = d / "latest.json"
    if rows:
        require(latest.is_file() and not latest.is_symlink(),
                "missing published latest pointer")
        pointer = json.loads(latest.read_text(encoding="utf-8"))
        require(pointer == rows[0], "latest pointer mismatch")
    else:
        require(not latest.exists(), "latest pointer must not exist before first release")
    require((d / "README.md").read_text(encoding="utf-8") == render_readme(rows),
            "README history drift")
    qa_count = verify_qa_archive(d)
    require({p.name for p in d.iterdir()} == {
        "README.md", "releases.json", *seen_files,
        *(["latest.json"] if rows else []),
        *(["qa"] if qa_count else [])
    }, "unexpected downloads contents")
    print("RHC_DOWNLOADS_VERIFY=" + json.dumps({
        "result": "PASS", "released": len(rows), "latest": rows[0]["version"] if rows else None,
        "files": len(seen_files), "qa": qa_count}, sort_keys=True))
    return rows


def stage_release(downloads, artifact, version, utc, source_sha):
    """Local staging ONLY. Caller must separately enforce actual release approval."""
    d = Path(downloads).resolve()
    old = verify(d)
    require(not old or norm_version(version) > norm_version(old[0]["version"]),
            "release version must increase")
    target = d / filename(version)
    require(not target.exists(), "immutable ZIP already exists")
    record = make_record(Path(artifact), version, utc, source_sha)
    target.write_bytes(Path(artifact).read_bytes())
    rows = [record, *old]
    (d / "releases.json").write_text(
        json.dumps({"schemaVersion": CATALOG_SCHEMA, "releases": rows},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (d / "latest.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (d / "README.md").write_text(render_readme(rows), encoding="utf-8")
    verify(d)
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--downloads", type=Path, default=Path("downloads"))
    args = p.parse_args()
    verify(args.downloads)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("RHC_DOWNLOADS_VERIFY=FAIL: " + str(exc), file=sys.stderr)
        sys.exit(1)
