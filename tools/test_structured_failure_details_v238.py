#!/usr/bin/env python3
from pathlib import Path
import json, sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
ui = (root/'ui.go').read_text(encoding='utf-8')
engine = (root/'engine.go').read_text(encoding='utf-8')
checks=[]
def add(name, cond): checks.append((name, bool(cond)))

# Contract fixture for the exact regression: a final failed Gate 3 with a
# structured Kernel drivers JSON finding. Such a result must never render the
# generic no-structured fallback.
fixture = {
    'gates': [{'Name':'x','Status':'PASS','Detail':''}, {'Name':'x','Status':'PASS','Detail':''},
              {'Name':'Kernel-Treiber RzDev / RzCommon','Status':'FAILED','Detail':'1 relevante Prüfung fehlgeschlagen.'}],
    'checks': [{
        'Section':'Kernel drivers','Status':'FAIL','Check':'RzDev_abcd service',
        'Actual':'Missing / not installed','Expected':'vorhanden; StartMode Manual',
        'Detail':'Service konnte nicht geöffnet werden.','EvidenceRole':'PRIMARY'
    }]
}
# Mirror only the stable ownership contract from gateCheckBelongs: Gate 3 owns
# every check in the Kernel drivers section.
gate3 = [c for c in fixture['checks'] if c['Section'].strip().lower() == 'kernel drivers']
add('fixture contains final failed Gate 3', fixture['gates'][2]['Status'] == 'FAILED')
add('fixture contains structured Gate 3 failure', len(gate3) == 1 and gate3[0]['Status'] == 'FAIL')
add('Gate 3 ownership maps Kernel drivers checks', 'case 2:' in engine and 'return section == "kernel drivers"' in engine)

helper_start = ui.find('func structuredFindingLines(c EngineCheck) []string')
helper_end = ui.find('\nfunc ', helper_start + 5) if helper_start >= 0 else -1
helper = ui[helper_start:helper_end if helper_end > helper_start else len(ui)] if helper_start >= 0 else ''
add('normal structured-finding renderer exists', helper_start >= 0)
add('failure/unknown renderer uses actual JSON value', 'c.Actual' in helper)
add('failure/unknown renderer uses expected JSON value', 'c.Expected' in helper)
add('failure/unknown renderer uses detail JSON value', 'c.Detail' in helper)
add('failure/unknown renderer uses section/source JSON value', 'c.Section' in helper)
add('full expansion is limited to FAIL or UNKNOWN', '"FAIL"' in helper and '"UNKNOWN"' in helper)
add('normal popover uses structured renderer', 'structuredFindingLines(c)' in ui)
# Fallback remains legitimate only when there really are no mapped checks.
add('generic no-structured fallback is guarded by zero checks', 'if !inspection.Available || len(checks) == 0 {' in ui and 'popover.result.no_structured' in ui)

failed=[name for name,ok in checks if not ok]
for name,ok in checks:
    print(('PASS' if ok else 'FAIL')+': '+name)
print(f'v2.3.8 structured failure details regression: {len(checks)-len(failed)}/{len(checks)}')
if failed:
    sys.exit(1)
