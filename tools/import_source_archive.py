#!/usr/bin/env python3
"""Fail-closed, byte-preserving source ZIP intake (never pushes or releases)."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError('git ' + ' '.join(args) + ' failed: ' + p.stderr.strip())
    return p.stdout.strip()


def validated_entries(z: zipfile.ZipFile):
    names = set()
    entries = []
    for info in z.infolist():
        if info.is_dir():
            continue
        name = info.filename
        p = PurePosixPath(name)
        if (not name or name.startswith('/') or '\\' in name or ':' in name or
                any(part in ('.', '..', '.git', '') for part in p.parts) or
                p.as_posix() != name or name in names):
            raise RuntimeError('invalid/duplicate ZIP path: ' + repr(name))
        names.add(name)
        entries.append((p, info))
    return sorted(entries, key=lambda x: x[0].as_posix())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--expected-archive-sha256', required=True)
    ap.add_argument('--expected-file-count', type=int, required=True)
    ap.add_argument('--expected-head', help='optional verified current branch SHA lease')
    ap.add_argument('--expected-branch', default='main', help='exact branch being imported; default: main')
    ap.add_argument('--apply', action='store_true', help='write source files, still never commits or pushes')
    ap.add_argument('--public-source-reviewed', action='store_true',
                    help='explicit acknowledgement that historical logs/forensics have been reviewed before public import')
    ap.add_argument('--replace-bootstrap-readme', action='store_true',
                    help='explicitly replace bootstrap README with exact source README from the archive')
    ns = ap.parse_args()
    repo = ns.repo.resolve()
    if not ns.archive.is_file() or not repo.is_dir():
        raise RuntimeError('archive or repository path missing')
    if git(repo, 'rev-parse', '--show-toplevel') != str(repo):
        raise RuntimeError('repo must point to the checked-out Git repository root')
    if git(repo, 'branch', '--show-current') != ns.expected_branch:
        raise RuntimeError('source intake requires checked-out expected branch (no implicit checkout)')
    if git(repo, 'status', '--porcelain'):
        raise RuntimeError('Git working tree must be completely clean before import')
    head = git(repo, 'rev-parse', 'HEAD')
    if ns.expected_head and head != ns.expected_head:
        raise RuntimeError('main SHA lease mismatch: ' + head)
    archive_bytes = ns.archive.read_bytes()
    archive_hash = digest(archive_bytes)
    if archive_hash != ns.expected_archive_sha256.lower():
        raise RuntimeError('source archive SHA-256 mismatch: ' + archive_hash)
    with zipfile.ZipFile(ns.archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('ZIP CRC integrity FAILED')
        entries = validated_entries(z)
        if len(entries) != ns.expected_file_count:
            raise RuntimeError('source file count mismatch: ' + str(len(entries)))
        if not any(str(p) == 'go.mod' for p, _ in entries):
            raise RuntimeError('missing Go module root')
        if not any(str(p) == 'build.sh' for p, _ in entries):
            raise RuntimeError('missing canonical build entry')
        planned = []
        for p, info in entries:
            dest = repo.joinpath(*p.parts)
            if not dest.resolve().is_relative_to(repo):
                raise RuntimeError('path escapes repository or follows external symlink: ' + str(p))
            data = z.read(info)
            if dest.exists() and dest.read_bytes() != data:
                if str(p) != 'README.md' or not ns.replace_bootstrap_readme:
                    raise RuntimeError('unexpected existing-file conflict: ' + str(p))
            planned.append((p, data))
        manifest = {
            'schemaVersion': 1, 'kind': 'source-intake-file-manifest',
            'sourceArchiveSha256': archive_hash, 'sourceFileCount': len(planned),
            'importBaseMainSha': head,
            'files': [{'path':str(p), 'size':len(data), 'sha256':digest(data)} for p,data in planned]
        }
        print('SOURCE_INTAKE_CHECK=PASS archive_sha256=' + archive_hash +
              ' source_files=' + str(len(planned)) + ' head=' + head)
        if not ns.apply:
            print('SOURCE_INTAKE_MODE=DRY_RUN; no files written')
            print('To apply: add --apply --public-source-reviewed --replace-bootstrap-readme')
            return 0
        if not ns.public_source_reviewed or not ns.replace_bootstrap_readme:
            raise RuntimeError('public-source review and README replacement require explicit acknowledgement')
        for p,data in planned:
            dest = repo.joinpath(*p.parts)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
            if p.name == 'build.sh':
                dest.chmod(dest.stat().st_mode | 0o111)
        target = repo/'docs'/'migration'/'RHC-v3.0.8-source-file-manifest.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n', encoding='utf-8')
        for p,data in planned:
            if repo.joinpath(*p.parts).read_bytes()!=data:
                raise RuntimeError('post-write byte mismatch: '+str(p))
        print('SOURCE_INTAKE_APPLIED=PASS file_count='+str(len(planned)))
        print('Review git diff, commit and push explicitly; script never commits/releases.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SOURCE_INTAKE=BLOCKED: '+str(e),file=sys.stderr)
        sys.exit(1)
