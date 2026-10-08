from pathlib import Path
import re, sys, json
from rhc_release_contracts import version_from_model, SEMVER
root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
checks=[]
def ck(name, cond): checks.append((name,bool(cond)))
def txt(name):
    p=root/name
    return p.read_text(encoding='utf-8', errors='ignore') if p.exists() else ''
model=txt('model.go')
appdiag=txt('appengine_diagnostic.go')
script=txt('diagnostics/diagnose-appengine-usermode-v1.0.2.ps1')
build=txt('build.sh')
loc=txt('locales/de-DE.json')
manifest=txt('i18n-manifest.json')
try:
    current_version=version_from_model(root)
except (OSError, ValueError):
    current_version=None
ck('app/reference version valid and equal', current_version is not None)
ck('diagnostic module version 1.0.2', 'appEngineDiagnosticModuleVersion = "1.0.2"' in appdiag)
ck('diagnostic script name 1.0.2', 'diagnose-appengine-usermode-v1.0.2.ps1' in appdiag)
ck('diagnostic asset exists', len(script) > 2000)
ck('script module version 1.0.2', "$moduleVersion='1.0.2'" in script)
ck('PS51 native arrays retained', '$errors=@()' in script and '$rows=@()' in script and 'Collections.Generic.List' not in script)
ck('systray evidence', '$systray=' in script and 'SystrayPresent=$systrayPresent' in script)
ck('background-manager evidence', '$backgroundManager=' in script and 'BackgroundManagerPresent=$backgroundManagerPresent' in script)
ck('lighting-engine evidence', '$lightingEngine=' in script and 'LightingEnginePresent=$lightingEnginePresent' in script)
ck('generic device middleware evidence', "$deviceMiddleware=[bool](@($pages|?{$_ -match '(?i)^win-usb_.*_mw$'}).Count -gt 0)" in script and 'DeviceMiddlewarePresent=$deviceMiddlewarePresent' in script)
ck('dashboard evidence retained as supporting', 'SynapsePresent=$synapsePresent' in script and 'ChromaPresent=$chromaPresent' in script)
health_lines='\n'.join(line.strip() for line in script.splitlines() if 'runtimeState=' in line and 'HEALTHY' in line)
ck('healthy requires persistent background contract', all(tok in health_lines for tok in ['$runValid','$contractMain','$systray','$backgroundManager','$lightingEngine','$deviceMiddleware']))
ck('healthy does not require synapse dashboard renderer', '$synapse' not in health_lines)
ck('healthy does not require chroma dashboard renderer', '$chroma' not in health_lines)
ck('missing systray still prevents healthy', '$systray' in health_lines)
ck('no PID-specific runtime requirement', all(pid not in health_lines and pid not in script for pid in ['5426_716','5426_192','product 716']))
ck('Go exposes new evidence fields', all(x in appdiag for x in ['BackgroundManagerPresent','LightingEnginePresent','DeviceMiddlewarePresent']))
ck('read-only contract retained', 'ReadOnly=$true' in script and all(x not in script for x in ['Set-ItemProperty','New-ItemProperty','Remove-ItemProperty','Start-Service','Stop-Service','Restart-Service','Set-Service','Stop-Process','Start-Process']))
ck('validator build gated', 'validate_v308_background_runtime_semantics.py' in build)
try:
    locale_version=json.loads(loc)['_meta']['version']
    catalog_version=json.loads(manifest)['catalogVersion']
    catalog_valid=(isinstance(locale_version,str) and
        SEMVER.fullmatch(locale_version) is not None and
        catalog_version==locale_version and current_version is not None and
        tuple(map(int,locale_version.split('.'))) <= tuple(map(int,current_version.split('.'))))
except (ValueError, KeyError, TypeError):
    catalog_valid=False
ck('locale and manifest catalog versions match and do not exceed app', catalog_valid)
passed=sum(v for _,v in checks)
for name,ok in checks: print(('PASS' if ok else 'FAIL')+' | '+name)
print(f'{passed}/{len(checks)} PASS')
sys.exit(0 if passed==len(checks) else 1)
