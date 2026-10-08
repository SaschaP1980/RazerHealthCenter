from rhc_release_contracts import version_from_model
from pathlib import Path
import sys
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
ck('current application version', f'appVersion                   = "{version_from_model(root)}"' in model and f'referenceVersion             = "{version_from_model(root)}"' in model)
ck('diagnostic module version 1.0.2', 'appEngineDiagnosticModuleVersion = "1.0.2"' in appdiag)
ck('diagnostic script name 1.0.2', 'diagnose-appengine-usermode-v1.0.2.ps1' in appdiag)
ck('new diagnostic asset exists', len(script) > 1500)
ck('script declares module version 1.0.2', "$moduleVersion='1.0.2'" in script)
ck('no generic list strings', 'Collections.Generic.List' not in script and 'System.Collections.Generic.List' not in script)
ck('native errors array', '$errors=@()' in script)
ck('native rows array', '$rows=@()' in script)
ck('errors appended PS51 safe', '$errors+=' in script)
ck('rows appended PS51 safe', '$rows+=' in script)
ck('result errors direct array', 'Errors=$errors' in script and 'Errors=@($errors)' not in script)
ck('result processes direct array', 'Processes=$rows' in script and 'Processes=@($rows)' not in script)
ck('read-only contract retained', 'ReadOnly=$true' in script and 'RuntimeState=$runtimeState' in script)
ck('run contract retained', all(x in script for x in ['apps=synapse,chroma-app','launch-force-hidden=synapse,chroma-app','autoStart=1']))
ck('runtime health evidence retained', all(x in script for x in ['SystrayPresent','SynapsePresent','ChromaPresent','KeyboardMiddlewarePresent']))
ck('no mutation cmdlets', all(x not in script for x in ['Set-ItemProperty','New-ItemProperty','Remove-ItemProperty','Start-Service','Stop-Service','Restart-Service','Set-Service','Stop-Process','Start-Process']))
ck('validator build gated', 'validate_v307_ps51_appengine_diagnostic.py' in build)
ck('locale version 3.0.8.0', '"version": "3.0.8.0"' in loc)
ck('manifest version 3.0.8.0', '"catalogVersion": "3.0.8.0"' in manifest)
passed=sum(v for _,v in checks)
for name,ok in checks: print(('PASS' if ok else 'FAIL')+' | '+name)
print(f'{passed}/{len(checks)} PASS')
sys.exit(0 if passed==len(checks) else 1)
