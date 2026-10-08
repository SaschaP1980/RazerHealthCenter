#!/usr/bin/env python3
from pathlib import Path
import json, sys

root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
def read(rel): return (root/rel).read_text(encoding='utf-8')
model=read('model.go'); eng=read('engine.go'); ui=read('ui.go'); health=read('health-engine-v1.4.6.ps1') if (root/'health-engine-v1.4.6.ps1').exists() else ''
locale=json.loads(read('locales/de-DE.json'))['strings']; build=read('build.sh')
checks=[]
def add(name, cond): checks.append((name,bool(cond)))

add('app version 3.0.8', 'appVersion                   = "3.0.8"' in model and 'referenceVersion             = "3.0.8"' in model)
add('health engine version 1.4.6', 'engineVersion                = "1.4.6"' in model and "$ScriptVersion = '1.4.6'" in health)
add('Gate 3 evaluates issues rather than requiring positive count', "$issues = @($c | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'UNKNOWN' })" in health and '$passed = ($issues.Count -eq 0)' in health)
add('Gate 3 zero-requirement detail is explicit', 'Für die aktuell aktivierten Produkte ist kein RzDev/RzCommon-Filterstack erforderlich.' in health)
add('Gate 3 emits structured INFO when not applicable', "Add-Check 'Kernel drivers' 'INFO' 'RzDev/RzCommon requirement'" in health and 'kein RzDev/RzCommon-Filterstack erforderlich' in health)
add('real Kernel driver FAIL/UNKNOWN remains gate determining', "3 { return @($Checks | Where-Object { $_.Section -eq 'Kernel drivers' }) }" in health and "if ($EngineStatus -eq 'FAILED') { return 'FAILED' }" in health)
add('Gate 3 JSON checks remain mapped to UI inspection', 'case 2:' in eng and 'return section == "kernel drivers"' in eng)
add('final snapshot sanitizer exists', 'func finalGateSnapshot(' in eng and 'states[i] = "UNKNOWN"' in eng and 'display[i] = gateUnclear' in eng)
add('completed health worker uses final snapshot sanitizer', 'states, display := finalGateSnapshot(states, inspections)' in eng)
add('detail status reads live final display', 'states := a.liveGateDisplay' in ui and 'a.drawGateDetailPopover(hdc, detail, states[detail]' in ui and 'drawStatusBadge(hdc, a, state' in ui)
add('structured failure detail regression is in build gate', 'test_structured_failure_details_v238.py' in build)
add('finalization regression is in build gate', 'validate_gate_finalization_v238.py' in build)
add('new structured field labels are localized', all(k in locale for k in ['popover.finding.actual','popover.finding.expected','popover.finding.detail','popover.finding.section']))
production=(health+'\n'+eng+'\n'+ui).lower()
add('no endpoint PID/model-specific semantics added', not any(t in production for t in ['00c0','00c1','02c9','02cc','viper v3 pro','blackwidow']))

failed=[n for n,ok in checks if not ok]
for n,ok in checks: print(('PASS' if ok else 'FAIL')+': '+n)
print(f'v3.0.8 Gate applicability/finalization checks: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
