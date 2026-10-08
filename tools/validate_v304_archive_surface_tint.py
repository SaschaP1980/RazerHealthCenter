#!/usr/bin/env python3
from pathlib import Path
import json, sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

def read(name):
    return (root / name).read_text(encoding='utf-8')

ui = read('ui.go')
model = read('model.go')
build = read('build.sh')
manifest = json.loads(read('i18n-manifest.json'))
locale_doc = json.loads(read('locales/de-DE.json'))
checks = []

def ck(name, ok):
    checks.append((name, bool(ok)))

ck('app/reference version 3.0.8',
   'appVersion                   = "3.0.8"' in model and
   'referenceVersion             = "3.0.8"' in model)
ck('catalog version 3.0.8', manifest.get('catalogVersion') == '3.0.8')
ck('locale metadata version 3.0.8', locale_doc.get('_meta', {}).get('version') == '3.0.8')
ck('archive surface is exact 4-percent preblend', 'archiveSurface' in ui and '0x001b1b0e' in ui)
ck('old 6-percent archive surface is absent', '0x00201f0e' not in ui)
ck('archive comment documents roughly 4 percent', 'roughly 4% translucent cyan' in ui)
ck('historical card still uses archive surface', 'roundBox(hdc, box, 8, colors.archiveSurface, colors.border, 1)' in ui)
ck('v3.0.8 validator is build gated', 'validate_v304_archive_surface_tint.py' in build)
ck('v3.0.3 archive semantics validator remains build gated', 'validate_v303_archive_header_polish.py' in build)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(('PASS: ' if ok else 'FAIL: ') + name)
print(f'v3.0.8 archive surface tint regression: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed:
    sys.exit(1)
