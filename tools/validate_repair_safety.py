#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
repair=(root/'repair/repair-chroma-services-v1.1.0.ps1').read_text(encoding='utf-8')
health=(root/'health-engine-v1.4.6.ps1').read_text(encoding='utf-8')
diag=(root/'diagnostics/diagnose-chroma-services-v1.0.0.ps1').read_text(encoding='utf-8')
rg=(root/'repair.go').read_text(encoding='utf-8')
pg=(root/'problem.go').read_text(encoding='utf-8')
errors=[]
def req(cond,msg):
    if not cond: errors.append(msg)
req("'Razer Chroma SDK Service'" in repair and "'Razer Chroma SDK Server'" in repair,'repair target allowlist missing')
req(re.search(r'(?im)^\s*Start-Service\s+-Name\s+\$snap\.ServiceName\b',repair) is not None,'exact Start-Service command missing')
req("$snap.StartMode -ne 'Auto'" in repair,'Auto-only refusal missing')
req("$snap.State -eq 'Running'" in repair,'already-running guard missing')
req('ConfirmedByUser=$true' in repair and 'ProblemId=$ProblemId' in repair and 'RecipeId=$RecipeId' in repair,'repair audit identity/confirmation missing')
for token in ['Stop-Service','Restart-Service','Set-Service','New-Service','Remove-Service','Set-ItemProperty','New-ItemProperty','Remove-ItemProperty','Disable-PnpDevice','Enable-PnpDevice','pnputil','devcon','sc.exe config','reg.exe add','reg.exe delete']:
    if token.lower() in repair.lower(): errors.append('forbidden repair mutation token: '+token)
for source,name in [(health,'health engine'),(diag,'deep diagnostic module')]:
    for token in ['Start-Service','Stop-Service','Restart-Service','Set-Service','Set-ItemProperty','New-ItemProperty','Remove-ItemProperty','Disable-PnpDevice','Enable-PnpDevice']:
        if re.search(r'(?im)^\s*'+re.escape(token)+r'\b',source): errors.append(f'{name} mutation token: '+token)
req('$true' in diag and 'ReadOnly=$true' in diag,'deep diagnostic read-only declaration missing')
req((root/'SAFETY-MODEL.txt').exists(),'SAFETY-MODEL.txt missing')
req('repairDialogStage != repairDialogConfirm' in rg,'explicit in-app confirmation gate missing')
req('ConfirmationRequired: true' in pg,'catalog confirmation requirement missing')
req('launchElevatedHelper' not in pg,'diagnostic/problem orchestrator must never launch repairs')
for token in ['validateRepairHelperContract','embedded.ReadFile(def.ScriptAsset)','Diagnostics", "Repairs','pathInside(repairDir, result)','pathInside(repairDir, logPath)','--repair-recipe','--problem-id']:
    req(token in rg,'elevated helper confinement missing '+token)
if errors:
    for e in errors: print('FAIL:',e)
    print(f'repair safety: FAIL ({len(errors)} issue(s))')
    sys.exit(1)
print('repair safety: PASS')
print('repair helper confinement: PASS')
print('explicit confirmation invariant: PASS')
print('deep diagnostics read-only: PASS')
