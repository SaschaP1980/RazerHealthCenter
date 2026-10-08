#!/usr/bin/env python3
"""Validate exact v3.0.8 source identity after a byte-preserving GitHub import.

This is a migration-only reference gate, not a future release or repair test.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

GOLDEN_ARCHIVE_SHA = 'f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495'
GOLDEN_TREE_FINGERPRINT = 'adbfc9de536bd0ca8a1b69163ffdf080fe0b46b083b42ca498b8fafeb18703db'
EXPECTED_COUNT = 321
MANIFEST_PATH = 'docs/migration/RHC-v3.0.8-source-file-manifest.json'


def run(root: Path) -> None:
    manifest_path = root / MANIFEST_PATH
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    if data.get('schemaVersion') != 1 or data.get('kind') != 'source-intake-file-manifest':
        raise ValueError('unexpected import manifest schema/kind')
    if data.get('sourceArchiveSha256') != GOLDEN_ARCHIVE_SHA:
        raise ValueError('original Source ZIP identity mismatch')
    records = data.get('files')
    if not isinstance(records, list) or len(records) != EXPECTED_COUNT or data.get('sourceFileCount') != EXPECTED_COUNT:
        raise ValueError('source file count mismatch')
    names = set()
    casefold_names = set()
    fingerprint_lines = []
    for entry in records:
        if not isinstance(entry, dict) or set(entry) != {'path', 'size', 'sha256'}:
            raise ValueError('unexpected manifest record fields')
        name = entry['path']
        if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name:
            raise ValueError('invalid source path')
        pure = PurePosixPath(name)
        if (pure.is_absolute() or pure.as_posix() != name or
            any(part in ('.', '..', '.git', '') for part in pure.parts) or
            name in names or name.casefold() in casefold_names):
            raise ValueError('invalid / colliding ZIP path: ' + name)
        names.add(name)
        casefold_names.add(name.casefold())
        source = root.joinpath(*pure.parts)
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(root):
            raise ValueError('missing, unsafe or symlinked source file: ' + name)
        raw = source.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if type(entry['size']) is not int or entry['size'] != len(raw) or entry['sha256'] != sha:
            raise ValueError('source mismatch at: ' + name)
        fingerprint_lines.append(f'{name}\0{len(raw)}\0{sha}\n')
    if not {'go.mod', 'model.go', 'build.sh', 'resources/app_rsrc.bin', 'resources/app_rsrc.json'}.issubset(names):
        raise ValueError('required source files missing')
    fingerprint = hashlib.sha256(''.join(sorted(fingerprint_lines)).encode('utf-8')).hexdigest()
    if fingerprint != GOLDEN_TREE_FINGERPRINT:
        raise ValueError('source inventory golden fingerprint mismatch: '+fingerprint)
    print('RHC_SOURCE_INTAKE_MANIFEST=PASS files=321 fingerprint='+fingerprint)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    args = parser.parse_args()
    try:
        run(args.root.resolve())
    except Exception as exc:
        print('RHC_SOURCE_INTAKE_MANIFEST=FAIL: '+str(exc), file=sys.stderr)
        sys.exit(1)
