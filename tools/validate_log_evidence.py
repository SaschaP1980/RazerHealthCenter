#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
eng=(root/'health-engine-v1.4.6.ps1').read_text(encoding='utf-8')
go=(root/'engine.go').read_text(encoding='utf-8')
model=(root/'model.go').read_text(encoding='utf-8')

def req(cond,msg):
    if not cond:
        print('FAIL:',msg)
        sys.exit(1)
    print('PASS:',msg)

req("QueryMode='runtime-tail-8000'" in eng, 'fixed tail is explicitly runtime-only')
req("[ValidateSet('PRIMARY','RUNTIME','SUPPORTING')]" in eng and 'EvidenceRole = $EvidenceRole' in eng, 'checks carry evidence-role metadata')
req("'SUPPORTING'" in eng and 'Add-ModuleLogCheck' in eng, 'module log evidence is classified as supporting')
req("Add-Check 'AppEngine log' 'INFO' \"$Kind $ModuleName\"" in eng, 'module log evidence is informational, not health severity')
req("7 { return @($Checks | Where-Object { $_.Section -eq 'Chroma registry (32-bit)' }) }" in eng, 'gate 7 severity uses direct registry evidence only')
req("10 { return @($Checks | Where-Object { $_.Section -eq 'Services' -and $_.Check -match 'Game Manager' }) }" in eng, 'gate 10 severity uses direct service evidence only')
req("11 { return @($Checks | Where-Object { $_.Section -eq 'RzComDriver' }) }" in eng, 'gate 11 severity uses direct RzCom evidence only')
req("Where-Object { $_.EvidenceRole -ne 'SUPPORTING' }" in eng, 'PowerShell gate severity excludes supporting evidence generically')
req("$decisiveChecks = @($Checks | Where-Object { $_.EvidenceRole -ne 'SUPPORTING' })" in eng, 'raw diagnostic excludes supporting evidence generically')
req('EvidenceRole string `json:"EvidenceRole,omitempty"`' in model, 'Go result model preserves evidence role')
req('strings.EqualFold(strings.TrimSpace(c.EvidenceRole), "SUPPORTING")' in go, 'Go gate display ignores supporting evidence generically')
req('section == "chroma registry (32-bit)"' in go and 'section == "services" && strings.Contains(check, "game manager")' in go and 'section == "rzcomdriver"' in go, 'Go gate inspection scopes are direct-source for gates 7/10/11')
req("'UNKNOWN' \"$Kind $ModuleName\"" not in eng and "'FAIL' \"$Kind $ModuleName\"" not in eng and "'WARN' \"$Kind $ModuleName\"" not in eng, 'module-log absence/parse/version state cannot create UNKNOWN/WARN/FAIL')
print('Log evidence architecture checks: 13/13')
