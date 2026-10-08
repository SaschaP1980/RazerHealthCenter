#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys, zipfile

root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=3:
    raise SystemExit('usage: package_portable.py built-exe output.zip')
exe=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
if not exe.is_file(): raise SystemExit(f'missing exe: {exe}')
stage=out.parent/'portable-stage'
if stage.exists(): shutil.rmtree(stage)
stage.mkdir(parents=True)
for d in ('Diagnostics','Diagnostics/Repairs','Exports','Logs','Setup','Runtime','Runtime/diagnostics','Runtime/repair','Runtime/setup','Runtime/assets','Runtime/assets/status','Runtime/assets/ui'):
    (stage/d).mkdir(parents=True, exist_ok=True)
shutil.copy2(exe,stage/'RazerHealthCenter.exe')
for src,dst in [
    (root/'packaging/README.txt',stage/'README.txt'),
    (root/'README-I18N.txt',stage/'README-I18N.txt'),
    (root/'i18n-manifest.json',stage/'i18n-manifest.json'),
    (root/'SAFETY-MODEL.txt',stage/'SAFETY-MODEL.txt'),
    (root/'locales/de-DE.json',stage/'locales/de-DE.json'),
]:
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
# SHA256SUMS covers all regular payload files except itself.
lines=[]
for p in sorted(x for x in stage.rglob('*') if x.is_file()):
    rel=p.relative_to(stage).as_posix()
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    lines.append(f'{h}  {rel}')
(stage/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if out.exists(): out.unlink()
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    # Preserve empty runtime directories explicitly.
    for d in ('Diagnostics','Diagnostics/Repairs','Exports','Logs','Setup','Runtime','Runtime/diagnostics','Runtime/repair','Runtime/setup','Runtime/assets','Runtime/assets/status','Runtime/assets/ui'):
        zi=zipfile.ZipInfo(d+'/'); zi.external_attr=0o40755<<16; z.writestr(zi,b'')
    for p in sorted(x for x in stage.rglob('*') if x.is_file()):
        z.write(p,p.relative_to(stage).as_posix())
print(out)
