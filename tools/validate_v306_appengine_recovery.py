from rhc_release_contracts import version_from_model
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
checks=[]
def ck(name, cond): checks.append((name,bool(cond)))

def txt(name):
    p=root/name
    return p.read_text(encoding='utf-8', errors='ignore') if p.exists() else ''

v=txt('versioncheck.go'); h=txt('health_application_guard.go'); p=txt('problem.go'); r=txt('repair.go'); rt=txt('runtime.go'); m=txt('model.go'); ui=txt('ui.go'); loc=txt('locales/de-DE.json'); main=txt('main.go')
repair=txt('repair/repair-appengine-runtime-v1.0.0.ps1')
diag=txt('diagnostics/diagnose-appengine-usermode-v1.0.2.ps1')

ck('current application version', f'appVersion                   = "{version_from_model(root)}"' in txt('model.go'))
ck('registry view fields', 'SynapseRegistryView' in v and 'ChromaRegistryView' in v)
ck('explicit registry64', 'RegistryView]::Registry64' in v)
ck('explicit registry32', 'RegistryView]::Registry32' in v)
ck('registry probe returns view', 'registryValueProbe' in v and 'View' in v)
ck('health records registry view', 'RegistryView' in h or 'registryView' in h)
ck('appengine diagnostic asset', len(diag)>1000 and 'ReadOnly' in diag and 'RuntimeState' in diag)
ck('appengine diagnostic runtime', 'diagnosticAppEnginePath' in rt and 'appEngineDiagnosticScriptName' in rt)
ck('appengine diagnostic model', 'AppEngineDiagnosticResult' in p)
ck('appengine health guard', 'appEngineHealthCheck' in h and 'APPENGINE_USERMODE_RUNTIME_INCOMPLETE' in h)
ck('appengine problem id', 'RHC.APPENGINE.USERMODE.RUNTIME_INCOMPLETE' in p)
ck('appengine repair id', 'RHC.REPAIR.APPENGINE.CONTROLLED_RUNTIME_RECOVERY' in p)
ck('appengine repair catalog no elevation', 'repairAppEngineControlledRecovery' in p and 'RequiresElevation:    false' in p)
ck('appengine repair asset', len(repair)>2000 and 'START_ONLY_RECOVERY' in repair and 'FULL_RUNTIME_RESTART' in repair)
ck('repair no registry mutation', all(x not in repair for x in ['Set-ItemProperty','New-ItemProperty','Remove-ItemProperty']))
ck('repair no service mutation', all(x not in repair for x in ['Start-Service','Stop-Service','Set-Service','Restart-Service']))
ck('repair full contract', all(x in repair for x in ['apps=synapse,chroma-app','launch-force-hidden=synapse,chroma-app','autoStart=1']))
ck('repair no broad chroma installer heuristic', 'chromaInstallerError' not in repair)
ck('definition chooses runtime script', 'RuntimeFile' in r and 'ScriptAsset' in r)
ck('non elevated repair helper supported', 'RequiresElevation' in r and 'launchRepairHelper' in r)
ck('repair verification switches by recipe', 'verifyAppEngineRepairOutcome' in r)
ck('dynamic repair ui', 'repair.appengine.' in ui or 'repairDefinitionByID(recipeID)' in ui)
ck('appengine locale strings', 'repair.appengine.confirm.title' in loc and 'problem.appengine.runtime_incomplete.title' in loc)
ck('absolute confirmation retained', 'repairDialogConfirm' in r and 'ConfirmationRequired' in r)
ck('orchestrator cannot auto repair', 'startRepair' not in p and 'launchElevatedHelper' not in p)

passed=sum(v for _,v in checks)
for name,ok in checks: print(('PASS' if ok else 'FAIL')+' | '+name)
print(f'{passed}/{len(checks)} PASS')
sys.exit(0 if passed==len(checks) else 1)
