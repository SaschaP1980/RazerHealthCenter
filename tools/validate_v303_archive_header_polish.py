#!/usr/bin/env python3
from rhc_release_contracts import version_from_model
from pathlib import Path
import json, sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

def read(name):
    return (root / name).read_text(encoding='utf-8')

ui = read('ui.go')
model = read('model.go')
build = read('build.sh')
loc = json.loads(read('locales/de-DE.json'))['strings']
manifest = json.loads(read('i18n-manifest.json'))
checks = []

def ck(name, ok):
    checks.append((name, bool(ok)))

ck('current application/reference version',
   f'appVersion                   = "{version_from_model(root)}"' in model and
   f'referenceVersion             = "{version_from_model(root)}"' in model)
ck('catalog version 3.0.8.0', manifest.get('catalogVersion') == '3.0.8.0')
ck('redundant archive title removed from catalog', 'logs.historical.archive_title' not in loc)
ck('redundant archive subtitle removed from catalog', 'logs.historical.archive_subtitle' not in loc)
ck('historical duration localized as DAUER', loc.get('logs.historical.duration') == 'DAUER')
ck('historical gate count localized', loc.get('logs.historical.gate_count') == '{done} / {total} Prüfgruppen')
ck('archive tagline remains cyan context',
   loc.get('app.tagline.archive') == 'ARCHIVANSICHT  •  NICHT LIVE' and
   'taglineColor = colors.info' in ui)
ck('historical tab remains cyan', 'historicalTabColor := colors.info' in ui)
ck('dedicated subtle archive surface exists', 'archiveSurface' in ui and '0x001b1b0e' in ui)

start = ui.find('func (a *App) drawHistoricalMeasurementView')
end = ui.find('\nfunc (a *App) drawLogsView', start)
hist = ui[start:end] if start >= 0 and end > start else ''

ck('historical draw function found', bool(hist))
ck('archive card uses cyan-tinted surface',
   'roundBox(hdc, box, 8, colors.archiveSurface, colors.border, 1)' in hist)
ck('no redundant archive title rendered', 'logs.historical.archive_title' not in hist)
ck('no redundant archive subtitle rendered', 'logs.historical.archive_subtitle' not in hist)
ck('no cyan separator line over heart',
   'line(hdc, 120, 151, right-8, 151, 1, archiveModeColor)' not in hist)

needle = 'tr("logs.historical.system_label")'
pos = hist.find(needle)
ck('historical system label uses cyan',
   pos >= 0 and 'archiveModeColor' in hist[pos:pos + 240])
ck('historical heart remains normal result icon',
   'drawIcon(hdc, icon, 130, 138, 82, 82)' in hist and
   'icon := a.iconStatusReady' in hist and
   'icon = a.iconStatusPass' in hist and
   'icon = a.iconStatusFail' in hist)
ck('stored overall keeps health result color', 'stateColor(m.Overall)' in hist)
ck('historical uses DAUER not live runtime label',
   'logs.historical.duration' in hist and 'status.runtime_label' not in hist)

needle = 'tr("logs.historical.completed")'
pos = hist.find(needle)
ck('completion label is neutral result text',
   pos >= 0 and 'colors.text2' in hist[pos:pos + 260])
ck('completion count says Prüfgruppen',
   'logs.historical.gate_count' in hist and 'gate.progress.completed' not in hist)
ck('live-style progress remains absent',
   'status.progress.percent' not in hist and 'bar := rect{' not in hist)
ck('v3.0.8.0 validator is build gated', 'validate_v303_archive_header_polish.py' in build)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(('PASS: ' if ok else 'FAIL: ') + name)
print(f'v3.0.8.0 archive header polish regression: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed:
    sys.exit(1)
