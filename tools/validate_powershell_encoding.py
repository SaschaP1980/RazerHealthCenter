#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parents[1]
health=(root/'health-engine-v1.4.6.ps1').read_bytes()
runtime=(root/'runtime.go').read_text(encoding='utf-8')
engine=(root/'engine.go').read_text(encoding='utf-8')
expected='a50203129512b912dee148a572079c928d4964686defaf6b855b544fff889970'
checks={
 'current health engine 1.4.6 hash': hashlib.sha256(health).hexdigest()==expected,
 'health engine remains utf8 without bom': not health.startswith(b'\xef\xbb\xbf') and any(b>=128 for b in health),
 'runtime adds utf8 bom execution copy': 'windowsPowerShellUTF8ScriptBytes' in runtime and '0xEF, 0xBB, 0xBF' in runtime and 'engineRuntimeEncoding=UTF-8-BOM' in runtime,
 'runtime writes normalized engine copy': 'engineRuntime := windowsPowerShellUTF8ScriptBytes(engine)' in runtime and 'os.WriteFile(a.enginePath, engineRuntime' in runtime,
 'powershell console output forced utf8': '[Console]::OutputEncoding = $enc; $OutputEncoding = $enc;' in engine,
 'health invocation uses command prelude': 'buildHealthEngineCommand' in engine and '"-Command", psCommand' in engine,
 'powershell paths single quote escaped': 'quotePowerShellLiteral' in engine and 'strings.ReplaceAll(v, "\'", "\'\'")' in engine,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+': '+k)
if failed: sys.exit(1)
print(f'PowerShell encoding checks: {len(checks)}/{len(checks)}')
