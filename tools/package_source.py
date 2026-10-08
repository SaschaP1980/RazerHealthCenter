#!/usr/bin/env python3
from pathlib import Path
import sys, zipfile

root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2:
    raise SystemExit('usage: package_source.py output.zip')
out=Path(sys.argv[1]).resolve()
exclude_dirs={'.git','dist','portable-stage','__pycache__','.pytest_cache'}
exclude_suffixes={'.pyc','.pyo'}
files=[]
for p in root.rglob('*'):
    rel=p.relative_to(root)
    if any(part in exclude_dirs for part in rel.parts): continue
    if not p.is_file(): continue
    if p.resolve()==out: continue
    if p.suffix in exclude_suffixes: continue
    files.append((rel.as_posix(),p))
if out.exists(): out.unlink()
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for rel,p in sorted(files): z.write(p,rel)
print(f'{out} ({len(files)} files)')
