#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
checks=[]
def ck(name, ok): checks.append((name, bool(ok)))
def txt(rel):
    p=root/rel
    return p.read_text(encoding='utf-8-sig', errors='replace') if p.exists() else ''

model=txt('model.go')
runtime=txt('runtime.go')
vc=txt('versioncheck.go')
ui=txt('ui.go')
loc=txt('locales/de-DE.json')
build=txt('build.sh')
eng=txt('health-engine-v1.4.6.ps1')

ck('app/reference version 3.0.8', 'appVersion                   = "3.0.8"' in model and 'referenceVersion             = "3.0.8"' in model)
ck('health engine 1.4.6 selected', 'engineVersion                = "1.4.6"' in model and 'health-engine-v1.4.6.ps1' in runtime)
ck('health engine 1.4.6 exists', bool(eng))
ck('no static Known-Good baseline object', '$Baseline = ' not in eng and '$Baseline=' not in eng)
ck('old Chroma baseline absent', '4.0.1.08260816' not in eng and '4.0.1.07221608' not in eng)
ck('old local SHA256 baselines absent', 'CE2F7204D755E96E82887909288E0A6E3EB9566467C31994D3D393D946204700' not in eng and '418747688ECABBCEB438EC1C18109C0F3640044A2F83AF2C6C0F74906A63F6A4' not in eng)
ck('Chroma registry versions informational/non-normative', "keine normative Sollversion" in eng and "'WARN' $r.Name" not in eng)
ck('kernel version not baseline WARN', 'baseline version' not in eng)
ck('LampArray hash mismatch not normative', 'Known-good baseline hash' not in eng and 'Hash weicht vom dokumentierten Baselinewert ab' not in eng)
ck('installer cache no local known-good hash verdict', 'Known-good hash + gueltige Razer-Signatur' not in eng)
ck('official discovery endpoint', 'https://discovery3.razerapi.com/api/v1/endpoints' in vc)
ck('official manifest endpoint construction', 'https://manifest3.razerapi.com/api/v1/releases/' in vc and 'razerManifestChannel = "prod"' in vc and '"/tags/"' in vc and '"/products?"' in vc)
ck('no Razer Insider release-note authority', 'insider.razer.com' not in vc)
ck('VersionStatus schema 4', ('SchemaVersion:   4' in vc or 'SchemaVersion: 4' in vc))
ck('manifest registry mapping used', 'current_version_registry_key' in vc and 'current_version_registry_value' in vc)
ck('prod hash is discovered not hardcoded', 'ManifestProdHash' in vc and 'name == "prod"' in vc.lower())
ck('update remains INFO color', 'case versionStateUpdateAvailable:' in ui and 'return colors.info' in ui[ui.find('func versionStateColor'):ui.find('func (a *App) drawSetupCalibrationModal')])
ck('update label explicitly new version available', 'NEUE VERSION VERFÜGBAR' in loc)
ck('manifest source text', 'Razer prod-Manifest' in loc)
ck('validator build-gated', 'validate_v301_manifest_authority.py' in build)

failed=[n for n,o in checks if not o]
for n,o in checks:
    print(('PASS' if o else 'FAIL')+': '+n)
print(f'v3.0.8 manifest authority regression: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed:
    raise SystemExit(1)
