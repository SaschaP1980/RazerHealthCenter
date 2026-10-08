#!/usr/bin/env python3
from rhc_release_contracts import version_from_model
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
checks=[]
def ck(name, ok): checks.append((name, bool(ok)))
def txt(rel):
    p=root/rel
    return p.read_text(encoding='utf-8-sig', errors='replace') if p.exists() else ''

model=txt('model.go')
engine=txt('engine.go')
version=txt('versioncheck.go')
guard=txt('health_application_guard.go')
history=txt('history_export.go')
ui=txt('ui.go')
loc=txt('locales/de-DE.json')
build=txt('build.sh')

ck('current application/reference version', f'appVersion                   = "{version_from_model(root)}"' in model and f'referenceVersion             = "{version_from_model(root)}"' in model)
ck('overall incomplete state exists', 'overallIncomplete = "UNCLEAR"' in model)
ck('official manifest registration states are explicit', all(x in version for x in ['SynapseRegistrationState','ChromaRegistrationState','registrationStatePresent','registrationStateUnreadable']))
ck('registry errors retained per product', 'SynapseRegistrationError' in version and 'ChromaRegistrationError' in version)
ck('application health guard exists', 'type ApplicationHealthAssessment struct' in guard and 'RAZER_PRODUCT_REGISTRATION_UNCONFIRMED' in guard)
ck('guard uses official manifest mappings', 'SynapseRegistryKey' in guard and 'ChromaRegistryKey' in guard and 'official-razer-prod-manifest-registration' in guard)
ck('manifest network failure has no registration health impact', 'st.OnlineError' in guard and 'manifestEvaluated' in guard and 'AppEngine-User-Mode-Prüfung bleibt davon unabhängig aktiv' in guard)
ck('version difference does not drive health guard', 'LatestSynapse' not in guard and 'LatestChroma' not in guard and 'versionStateUpdateAvailable' not in guard)
ck('unreadable registration becomes UNKNOWN', 'c.Status = "UNKNOWN"' in guard and 'FinalGateState = "UNKNOWN"' in guard and 'FinalOverall = "UNKNOWN"' in guard)
ck('only passing AppEngine gate is downgraded by guard', 'strings.EqualFold(a.BaseGateState, "PASS")' in guard)
ck('health run resolves manifest in parallel', 'versionCh := make(chan VersionStatus, 1)' in engine and 'versionCh <- collectVersionStatus()' in engine)
ck('guard applied before final snapshot/diagnostic orchestrator', engine.find('applyApplicationHealthAssessment') < engine.find('finalGateSnapshot(states, inspections)') < engine.find('runDiagnosticOrchestrator'))
ck('final diagnostic JSON is patched', 'patchRazerHealthJSON' in guard and 'healthCenterAssessment' in guard and 'root["overall"] = "UNKNOWN"' in guard)
ck('GateResult final result is patched', 'patchGateResult' in guard and 'OVERALL|UNKNOWN' in guard)
ck('assessment sidecar is measurement-addressable', 'ApplicationHealthAssessment-' in guard and 'ApplicationHealthAssessment-' in history)
ck('UNKNOWN gate makes live overall incomplete', 'else if unclear {' in engine and 'a.overall = overallIncomplete' in engine)
ck('incomplete measurement persists UNCLEAR', 'a.lastMeasurement.Overall = "UNCLEAR"' in engine)
ck('incomplete tray state is explicit', 'tray.tip.incomplete' in engine and 'a.iconIdle' in engine)
ck('incomplete summary does not claim functional health', 'if overall == overallIncomplete' in ui and 'overall.incomplete.detail' in ui)
ck('registration strings localized', all(k in loc for k in ['health.registration.synapse.check','health.registration.chroma.check','health.registration.gate.detail']))
ck('validator build-gated', 'validate_v305_false_green_guard.py' in build)

failed=[n for n,o in checks if not o]
for n,o in checks:
    print(('PASS' if o else 'FAIL')+': '+n)
print(f'v3.0.8.0 false-green guard: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed:
    raise SystemExit(1)
