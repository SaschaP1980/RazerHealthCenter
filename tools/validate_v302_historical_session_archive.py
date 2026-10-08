#!/usr/bin/env python3
from pathlib import Path
import json, sys, re
root=Path(__file__).resolve().parents[1]

def read(name): return (root/name).read_text(encoding='utf-8')
model=read('model.go')
ui=read('ui.go')
state=read('ui_state.go')
hist=read('history_export.go')
main=read('main.go')
locdoc=json.loads(read('locales/de-DE.json'))
loc=locdoc['strings']
build=read('build.sh')
checks=[]
def ck(name, ok): checks.append((name,bool(ok)))

ck('app/reference version 3.0.8', 'appVersion                   = "3.0.8"' in model and 'referenceVersion             = "3.0.8"' in model)
ck('historical persistence fields removed', 'json:"historicalLogStamp' not in state and 'json:"historicalActive' not in state and 'persistedUIState' not in state)
ck('startup explicitly resets historical session state', all(x in state for x in ['a.logHistoricalStamp = ""','a.logHistoricalOpen = false','a.logHistoricalActive = false']))
ck('historical state is not written to persistent UI state', 'os.WriteFile' not in state and 'json.Marshal' not in state)
ck('opening historical measurement is session only', 'a.persistLogsUIState()' not in state)
ck('refresh preserves open historical measurement inside current session', 'restoreStamp := a.logHistoricalStamp' in hist and 'a.logHistoricalOpen = true' in hist and 'a.logHistoricalActive = restoreActive' in hist)
ck('archive mode tagline localized', loc.get('app.tagline.archive') == 'ARCHIVANSICHT  •  NICHT LIVE')
ck('static completion label localized', loc.get('logs.historical.completed') == 'MESSUNG ABGESCHLOSSEN')
ck('shell switches archive tagline only for active historical log', 'archiveMode := view == 2 && a.logHistoricalOpen && a.logHistoricalActive' in ui and 'tr("app.tagline.archive")' in ui and 'colors.info' in ui)
ck('historical tab uses cyan mode color', 'historicalTabColor := colors.info' in ui and 'fill(hdc, rect{hist.Left, pageUnderline, hist.Right, pageUnderline + 3}, historicalTabColor)' in ui)
ck('archive summary avoids redundant banner copy', 'logs.historical.archive_title' not in ui and 'logs.historical.archive_subtitle' not in ui)
ck('archive banner uses cyan mode color', 'archiveModeColor := colors.info' in ui)
ck('historical status result keeps health result color', 'stateColor(m.Overall)' in ui and 'overallLabel := measurementDisplayStatus(m.Overall)' in ui)
ck('historical heart remains normal status icon', 'drawIcon(hdc, icon,' in ui and 'icon := a.iconStatusReady' in ui and 'icon = a.iconStatusPass' in ui and 'icon = a.iconStatusFail' in ui)
# Isolate historical draw function to ensure progress bar was removed there.
m=re.search(r'func \(a \*App\) drawHistoricalMeasurementView\(.*?\n}\n\nfunc \(a \*App\) drawLogsView', ui, re.S)
historical_fn=m.group(0) if m else ''
ck('historical live progress bar removed', 'status.progress.percent' not in historical_fn and 'bar := rect{' not in historical_fn)
ck('historical uses static completion information', 'tr("logs.historical.completed")' in historical_fn and 'logs.historical.gate_count' in historical_fn and 'formatClock(m.Duration)' in historical_fn)
ck('v3.0.8 validator is build gated', 'validate_v302_historical_session_archive.py' in build)

failed=[n for n,o in checks if not o]
for n,o in checks: print(('PASS: ' if o else 'FAIL: ')+n)
print(f'v3.0.8 historical session/archive regression: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed: sys.exit(1)
