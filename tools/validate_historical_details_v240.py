#!/usr/bin/env python3
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
model=(root/'model.go').read_text(encoding='utf-8')
ui=(root/'ui.go').read_text(encoding='utf-8')
hist=(root/'history_export.go').read_text(encoding='utf-8')
state=(root/'ui_state.go').read_text(encoding='utf-8') if (root/'ui_state.go').exists() else ''
win=(root/'win32.go').read_text(encoding='utf-8')
main=(root/'main.go').read_text(encoding='utf-8')
loc=(root/'locales/de-DE.json').read_text(encoding='utf-8')
build=(root/'build.sh').read_text(encoding='utf-8')
checks=[]
def add(name, ok):
    checks.append((name, bool(ok)))
add('app version 3.0.8.0', 'appVersion                   = "3.0.8.0"' in model and 'referenceVersion             = "3.0.8.0"' in model)
add('historical measurement stores gate snapshot', 'DetailAvailable' in model and 'GateStates' in model and 'GateInspections' in model)
add('detail capability is validated from historical engine JSON', 'historicalDetailSnapshot' in hist and 'len(r.Gates) < gateCount' in hist)
add('old or incomplete measurements remain listable', 'DetailUnavailableReason' in hist and 'logs.detail_unavailable.invalid' in hist)
add('single historical tab state exists', 'logHistoricalStamp' in model and 'logHistoricalOpen' in model and 'logHistoricalActive' in model)
add('historical tab state is session-only across restart', 'loadUIState()' in main and 'json:"historicalLogStamp' not in state and 'json:"historicalActive' not in state and 'a.logHistoricalStamp = ""' in state and 'a.logHistoricalOpen = false' in state and 'a.logHistoricalActive = false' in state)
add('historical UI state is never persisted to disk', 'os.WriteFile' not in state and 'json.Marshal' not in state and 'persistLogsUIState' not in state)
add('table selection and scroll reset at process startup', 'a.logSelected = -1' in state and 'a.logScroll = 0' in state)
add('double click opens historical measurement', 'csDblClks' in win and 'case wmLButtonDblClk:' in ui and 'handleDoubleClick' in ui and 'openHistoricalMeasurement(idx)' in ui)
add('details button exists and is gated by detail availability', 'action.show_details' in ui and 'm.DetailAvailable' in ui and 'drawCompactLogButton' in ui)
add('historical tab has close control and two-tab switching', 'logHistoricalCloseRect' in ui and 'closeHistoricalMeasurement' in ui and 'setHistoricalLogActive' in ui)
add('historical tab uses cyan archive mode color', 'historicalTabColor := colors.info' in ui)
add('historical view reuses gate detail popover read-only', 'drawGateDetailPopover(hdc, detail, m.GateStates[detail], m.GateInspections[detail], false, false)' in ui)
add('historical detail disables repair path', 'if allowRepair {' in ui and 'repairAvailableForGateFindings' in ui)
add('historical Gate 4 avoids current live presentation enrichment', 'idx == 3 && livePresentation' in ui)
add('historical package targets opened measurement', 'exportHistoricalMeasurement' in hist and 'a.logHistoricalStamp' in hist)
add('historical package excludes current mutable setup snapshots', 'sessionDiagnosticSources(selected.AppSession, false)' in hist and 'includeCurrentMutableSetup' in hist)
add('historical view keeps package and folder actions', 'action.create_package.sub.historical' in ui and 'a.exportHistoricalMeasurement()' in ui and 'a.openExports()' in ui)
add('current status wording changed', 'AKTUELLER SYSTEMSTATUS' in loc)
add('historical status wording exists', 'HISTORISCHER SYSTEMSTATUS' in loc)
add('validator is build-gated', 'validate_historical_details_v240.py' in build)
failed=[name for name,ok in checks if not ok]
for name,ok in checks:
    print(('PASS: ' if ok else 'FAIL: ')+name)
print(f'v3.0.8.0 historical measurement regression checks: {len(checks)-len(failed)}/{len(checks)}')
if failed:
    raise SystemExit(1)
