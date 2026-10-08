#!/usr/bin/env python3
"""Non-publishing RHC release contracts. No GitHub mutation, repair, signing or publish."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
PORTABLE_DIRS = (
    'Diagnostics', 'Diagnostics/Repairs', 'Exports', 'Logs', 'Setup',
    'Runtime', 'Runtime/diagnostics', 'Runtime/repair', 'Runtime/setup',
    'Runtime/assets', 'Runtime/assets/status', 'Runtime/assets/ui',
)
PORTABLE_ASSETS = {
    'LICENSE': 'LICENSE',
    'README.txt': 'packaging/README.txt',
    'README-I18N.txt': 'README-I18N.txt',
    'i18n-manifest.json': 'i18n-manifest.json',
    'SAFETY-MODEL.txt': 'SAFETY-MODEL.txt',
    'locales/de-DE.json': 'locales/de-DE.json',
}
SOURCE_TOP = {'LICENSE', 'go.mod', 'build.sh', 'README.md', 'README-I18N.txt',
              'i18n-manifest.json', 'SAFETY-MODEL.txt', 'SOURCE-DELIVERY-CONTRACT.md',
              '.gitattributes', '.gitignore'}
SOURCE_DIRS = {'assets', 'diagnostics', 'repair', 'setup', 'locales', 'packaging',
               'resources', 'tools', 'docs', 'tests', '.github'}
SEMVER = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z')
VERSION_PATTERN = re.compile(r'^\s*(appVersion|referenceVersion)\s*=\s*"([^"]+)"\s*$', re.M)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def version_from_model(root):
    model = (Path(root) / 'model.go').read_text(encoding='utf-8')
    found = VERSION_PATTERN.findall(model)
    values = {k: v for k, v in found}
    require(len(found) == 2 and set(values) == {'appVersion', 'referenceVersion'},
            'model.go must declare exactly one appVersion and referenceVersion')
    require(SEMVER.fullmatch(values['appVersion']), 'invalid appVersion semver')
    require(values['referenceVersion'] == values['appVersion'], 'model.go version divergence')
    return values['appVersion']


def assert_future_version(candidate, base):
    require(SEMVER.fullmatch(candidate) and SEMVER.fullmatch(base), 'bad semver')
    a, b = tuple(map(int, candidate.split('.'))), tuple(map(int, base.split('.')))
    require(a > b, 'candidate must advance beyond main version')
    return True


def tracked(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'],
                            capture_output=True, check=True)
    return [x.decode('utf-8') for x in result.stdout.split(b'\0') if x]


def permitted_source(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or '..' in p.parts or '\\' in name
            or ':' in name or '\x00' in name or p.as_posix() != name):
        return False
    if name.lower().endswith(('.zip', '.exe', '.pyc', '.pyo', '.log')):
        return False
    if any(part in {'.git', '__pycache__', '.pytest_cache', 'dist', 'portable-stage',
                    'forensics', 'runtime', 'exports'} for part in p.parts):
        return False
    if len(p.parts) == 1:
        return name in SOURCE_TOP or name.endswith(('.go', '.ps1'))
    return p.parts[0] in SOURCE_DIRS


def zip_entry(z, name, data, *, directory=False):
    info = zipfile.ZipInfo(name + ('/' if directory else ''), FIXED_TIME)
    info.create_system = 3
    info.external_attr = (0o40755 if directory else 0o100644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, b'' if directory else data, compress_type=zipfile.ZIP_DEFLATED,
               compresslevel=9)


def source_zip(root, output, *, source_paths=None):
    root = Path(root).resolve()
    paths = list(source_paths if source_paths is not None else tracked(root))
    require(len(paths) == len(set(paths)), 'duplicate tracked source path')
    accepted = sorted(p for p in paths if permitted_source(p))
    require({'LICENSE', 'go.mod', 'model.go', 'build.sh', 'tools/rhc_release_contracts.py'} <= set(accepted),
            'mandatory build source missing')
    require(len(accepted) >= 20, 'source inventory unexpectedly small')
    require(not any(p.lower().endswith(('.zip', '.exe', '.log')) for p in accepted),
            'unsafe output inclusion')
    output = Path(output).resolve()
    require(output != root and root not in output.parents, 'source output must be outside repository')
    with zipfile.ZipFile(output, 'w') as z:
        for name in accepted:
            file = root.joinpath(*PurePosixPath(name).parts)
            require(file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(root),
                    'unsafe or missing file: ' + name)
            zip_entry(z, name, file.read_bytes())
    return {'fileCount': len(accepted), 'sha256': sha(output.read_bytes()), 'size': output.stat().st_size,
            'files': accepted}


def portable_zip(root, exe, output):
    root, exe, output = Path(root).resolve(), Path(exe).resolve(), Path(output).resolve()
    require(exe.is_file() and exe.name == 'RazerHealthCenter.exe', 'expected Windows GUI exe')
    require(output != exe and root not in output.parents, 'portable output must be outside source tree')
    payload = {'RazerHealthCenter.exe': exe.read_bytes()}
    require(payload['RazerHealthCenter.exe'][:2] == b'MZ', 'invalid PE header')
    for target, source in PORTABLE_ASSETS.items():
        file = root.joinpath(*PurePosixPath(source).parts)
        require(file.is_file() and not file.is_symlink(), 'missing portable asset: ' + source)
        payload[target] = file.read_bytes()
    sums = ''.join(f'{sha(payload[name])}  {name}\n' for name in sorted(payload)).encode('utf-8')
    payload['SHA256SUMS.txt'] = sums
    with zipfile.ZipFile(output, 'w') as z:
        for d in PORTABLE_DIRS:
            zip_entry(z, d, b'', directory=True)
        for name, data in sorted(payload.items()):
            zip_entry(z, name, data)
    return {'fileCount': len(payload), 'directoryCount': len(PORTABLE_DIRS),
            'sha256': sha(output.read_bytes()), 'size': output.stat().st_size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--base-version', help='when set, candidate must strictly increase from main')
    args = parser.parse_args()
    root = args.root.resolve()
    version = version_from_model(root)
    if args.base_version is not None:
        assert_future_version(version, args.base_version)
    if args.out is None:
        print('RHC_RELEASE_CONTRACTS=' + json.dumps({'result': 'PASS', 'version': version}))
        return
    require(args.exe is not None, '--exe required for packaging')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = source_zip(root, out / f'RazerHealthCenter-Source-v{version}.zip')
    portable = portable_zip(root, args.exe, out / f'RazerHealthCenter-Portable-v{version}.zip')
    print('RHC_RELEASE_PACKAGE_SUMMARY=' + json.dumps(
        {'result': 'PASS', 'version': version, 'source': source, 'portable': portable}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('RHC_RELEASE_CONTRACTS=FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
