#!/usr/bin/env python3
from rhc_release_contracts import version_from_model
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
vc=(root/'versioncheck.go').read_text(encoding='utf-8')
ui=(root/'ui.go').read_text(encoding='utf-8')
eng=(root/'health-engine-v1.4.6.ps1').read_text(encoding='utf-8')
hist=(root/'history_export.go').read_text(encoding='utf-8')
model=(root/'model.go').read_text(encoding='utf-8')
loc=(root/'locales/de-DE.json').read_text(encoding='utf-8')
errors=[]
def req(c,m):
    if not c: errors.append(m)
req(f'appVersion                   = "{version_from_model(root)}"' in model,'current application version missing')
req('engineVersion                = "1.4.6"' in model,'engine version 1.4.6 missing')
req('https://discovery3.razerapi.com/api/v1/endpoints' in vc,'official Razer discovery source missing')
req('https://manifest3.razerapi.com/api/v1/releases/' in vc and '/tags/' in vc and '/products?' in vc,'official Razer product-manifest construction missing')
req('insider.razer.com' not in vc,'release-note scraping must not be normative version authority')
req('net/http' in vc and 'http.Client{Timeout: 8 * time.Second}' in vc,'bounded HTTPS manifest fetch missing')
req('name == "prod"' in vc,'dynamic prod discovery selection missing')
req('isSafeManifestHash' in vc and 'url.PathEscape(prodHash)' in vc,'prod hash validation/path escaping missing')
for token in ['q.Set("os"','q.Set("osver"','q.Set("arch"','q.Set("mfr"','q.Set("model"','q.Set("sku"','q.Set("l"']:
    req(token in vc,'manifest machine context query missing: '+token)
req('SystemSKUNumber' in vc and 'Win32_ComputerSystem' in vc,'Razer-style system SKU context missing')
req('SerialNumber' not in vc and 'IdentifyingNumber' not in vc,'version probe must not send serial/unique system identifiers')
req('current_version_registry_key' in vc and 'current_version_registry_value' in vc,'Razer-provided registry mapping missing')
req('probeManifestRegistryValue' in vc and 'RegistryView]::Registry64' in vc and 'RegistryView]::Registry32' in vc and '.OpenSubKey(' in vc,'read-only manifest registry probe missing')
req('SchemaVersion:   4' in vc or 'SchemaVersion: 4' in vc,'VersionStatus schema 4 missing')
req('ManifestProdHash' in vc and 'ManifestURL' in vc and 'ManifestChannel' in vc,'manifest provenance diagnostics missing')
req('SynapseProductVersion' in vc and 'ChromaProductVersion' in vc and 'DisplayVersion' in vc,'top-level manifest version diagnostics missing')
req('compareInstalledToOffered' in vc and 'isComparableManifestVersion' in vc and 'compareVersionNumbers' in vc,'manifest-domain version comparison missing')
req('VersionStatus-' in vc and 'VersionStatus-' in hist,'version status diagnostic artifact/export missing')
req('refreshVersionStatusAsync' in vc,'asynchronous version refresh missing')
req('info.versioncheck.synapse.installed' in ui and 'info.versioncheck.appengine.file' in ui,'version UI missing')
req('Razer prod-Manifest' in loc and 'Systemstatus nicht' in loc,'non-health official manifest wording missing')
req('NEUE VERSION VERFÜGBAR' in loc,'INFO update wording missing')
# UPDATE_AVAILABLE must visually be INFO, never warning.
color=ui[ui.find('func versionStateColor'):ui.find('func (a *App) drawSetupCalibrationModal')]
req('case versionStateUpdateAvailable:' in color and 'return colors.info' in color,'update state must use INFO color')
req("Add-Check 'AppEngine' 'INFO' 'RazerAppEngine package version'" in eng,'AppEngine package informational check missing')
req("Add-Check 'AppEngine' 'INFO' 'RazerAppEngine file version'" in eng,'AppEngine file informational check missing')
req('VersionStatus-' not in eng,'online version status must not alter Health Engine gates')
for token in ['Set-ItemProperty','New-ItemProperty','Remove-ItemProperty','Set-Service','Start-Service','Stop-Service','Restart-Service','Enable-PnpDevice','Disable-PnpDevice']:
    if re.search(r'(?im)^\s*'+re.escape(token)+r'\b',vc): errors.append('version probe mutation token: '+token)
if errors:
    for e in errors: print('FAIL:',e)
    print(f'version check validation: FAIL ({len(errors)} issue(s))')
    sys.exit(1)
print('version check validation: PASS')
