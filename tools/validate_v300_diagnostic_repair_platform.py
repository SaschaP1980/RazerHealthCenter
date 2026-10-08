#!/usr/bin/env python3
from pathlib import Path
import argparse,re,sys,json
p=argparse.ArgumentParser(); p.add_argument('root', nargs='?', default=str(Path(__file__).resolve().parents[1])); a=p.parse_args(); root=Path(a.root)
checks=[]
def ck(name, cond): checks.append((name,bool(cond)))
def text(rel):
    p=root/rel
    return p.read_text(encoding='utf-8') if p.exists() else ''
model=text('model.go'); runtime=text('runtime.go'); engine=text('engine.go'); repair=text('repair.go'); prob=text('problem.go'); build=text('build.sh'); pack=text('tools/package_portable.py'); loc=text('locales/de-DE.json'); safety=text('SAFETY-MODEL.txt')
ck('app version 3.0.8', 'appVersion                   = "3.0.8"' in model and 'referenceVersion             = "3.0.8"' in model)
ck('Health Center product rename', 'Razer Synapse + Chroma Health Center' in loc and 'HEALTH CENTER' in loc)
ck('Health Center executable packaging', 'RazerHealthCenter.exe' in build and 'RazerHealthCenter.exe' in pack)
ck('problem platform source exists', (root/'problem.go').exists())
ck('structured ProblemFinding model', 'type ProblemFinding struct' in prob and 'ProblemID' in prob and 'Classification' in prob and 'RepairID' in prob)
ck('problem catalog versioned', 'problemCatalogVersion' in prob and 'ProblemDefinition' in prob)
ck('unclassified findings supported', 'UNCLASSIFIED' in prob and 'unclassified' in prob.lower())
ck('diagnostic orchestrator versioned', 'diagnosticOrchestratorVersion' in prob and 'runDiagnosticOrchestrator' in prob)
ck('read-only Chroma diagnostic module', (root/'diagnostics/diagnose-chroma-services-v1.0.0.ps1').exists())
diag=text('diagnostics/diagnose-chroma-services-v1.0.0.ps1').lower()
ck('diagnostic module has no mutation commands', bool(diag) and all(tok not in diag for tok in ['start-service','stop-service','restart-service','set-service','set-itemproperty','new-itemproperty','remove-itemproperty','disable-pnpdevice','enable-pnpdevice']))
ck('runtime embeds diagnostics', 'diagnostics' in runtime and 'diagnose-chroma-services-v1.0.0.ps1' in runtime)
ck('health run invokes diagnostic orchestrator', 'runDiagnosticOrchestrator' in engine)
ck('problem findings persisted per measurement', 'ProblemFindings-' in prob and 'ProblemSnapshot' in prob)
ck('measurement collection recognizes findings', 'ProblemFindings-' in text('history_export.go'))
ck('repair catalog exists', 'type RepairDefinition struct' in prob and 'repairCatalog' in prob)
ck('all repair definitions require confirmation', 'ConfirmationRequired: true' in prob)
ck('known Gate 8 problem id', 'RHC.CHROMA.SDK_SERVICES.STOPPED_AUTO' in prob)
ck('Gate 8 maps to repair recipe', 'RHC.REPAIR.CHROMA.START_STOPPED_AUTO' in prob)
ck('repair helper accepts recipe id', '--repair-recipe' in repair and 'validateRepairHelperContract' in repair)
ck('repair audit records explicit confirmation', 'ConfirmedByUser' in repair and 'ProblemID' in repair and 'RecipeID' in repair)
ck('post-repair diagnostic verification', 'verifyRepairOutcome' in repair and 'VerificationStatus' in repair)
ck('no automatic repair from orchestrator', 'startRepair' not in prob and 'launchElevatedHelper' not in prob)
ck('safety model forbids automatic repairs', 'niemals automatisch' in safety.lower() and 'bestätig' in safety.lower())
ck('v3 validator build-gated', 'validate_v300_diagnostic_repair_platform.py' in build)
passed=sum(v for _,v in checks)
for n,v in checks: print(('PASS' if v else 'FAIL')+': '+n)
print(f'v3.0.8 diagnostic/repair platform: {passed}/{len(checks)} PASS')
sys.exit(0 if passed==len(checks) else 1)
