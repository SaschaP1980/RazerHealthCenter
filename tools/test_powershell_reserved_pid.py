#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
runtime = (root / 'runtime.go').read_text(encoding='utf-8')

# Production PowerShell payloads only. Discover the embedded/runtime scripts so
# this guard does not become stale on the next component-version bump.
active = set((root / 'setup').glob('*.ps1')) | set((root / 'repair').glob('*.ps1'))
for rel in re.findall(r'embedded\.ReadFile\("([^"]+\.ps1)"\)', runtime):
    p = root / rel
    if p.is_file():
        active.add(p)

# PowerShell variables are case-insensitive. $PID is a read-only automatic
# variable, so assigning to $pid or using it as a foreach target fails at
# runtime with "Cannot overwrite variable PID because it is read-only or constant."
write_patterns = [
    re.compile(r'(?i)\$pid\s*(?:=|\+=|-=|\*=|/=|%=|\+\+|--)'),
    re.compile(r'(?i)foreach\s*\(\s*\$pid\b'),
]

violations = []
for path in sorted(active):
    for lineno, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if any(p.search(line) for p in write_patterns):
            violations.append(f'{path.relative_to(root)}:{lineno}: {line.strip()}')

if violations:
    print('FAIL: production PowerShell writes to reserved automatic variable $PID (case-insensitive):')
    for v in violations:
        print('  ' + v)
    sys.exit(1)

print(f'PASS: no reserved $PID write collision in {len(active)} production PowerShell payload(s)')
