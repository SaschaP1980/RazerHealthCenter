#!/usr/bin/env python3
from pathlib import Path
import json, sys
root=Path(__file__).resolve().parents[1]
ui=(root/'ui.go').read_text(encoding='utf-8')
setupscan=(root/'setupscan.go').read_text(encoding='utf-8')
engine=(root/'engine.go').read_text(encoding='utf-8')
model=(root/'model.go').read_text(encoding='utf-8')
hist=(root/'history_export.go').read_text(encoding='utf-8')
runtime=(root/'runtime.go').read_text(encoding='utf-8')
problem=(root/'problem.go').read_text(encoding='utf-8')
trace=(root/'trace.go').read_text(encoding='utf-8')
main=(root/'main.go').read_text(encoding='utf-8')
win32=(root/'win32.go').read_text(encoding='utf-8')
i18n=(root/'i18n.go').read_text(encoding='utf-8')
manifest=json.loads((root/'i18n-manifest.json').read_text(encoding='utf-8'))
checks={
 'v3.0.8.0 version':'appVersion                   = "3.0.8.0"' in model and 'referenceVersion             = "3.0.8.0"' in model,
 'canonical source no recovered app version':'recovered-r8-rc2' not in model,
 'de runtime locale':'activeLocale = "de-DE"' in i18n and manifest.get('runtimeLocale')=='de-DE',
 'language switch disabled':manifest.get('languageSwitchingImplemented') is False,
 'de source of truth':manifest.get('sourceOfTruth')=='locales/de-DE.json',
 'de embedded locale':'//go:embed locales/de-DE.json' in i18n,
 'golden sidebar width':'sidebarW      = 88' in ui,
 'golden header height':'headerH       = 72' in ui,
 'larger sidebar icons':'28, 28' in ui and 'drawIcon(hdc, icon, 31, y+8, 28, 28)' in ui,
 'ping pong pulse helper':'func pulseFrameIndex' in ui and 'return 14 - step' in ui,
 'high resolution info heart':'iconAppInfo' in model and '96, 96' in ui and 'a.iconAppInfo, 569, 143, 88, 88' in ui,
 'localized progress semantics':'trn("gate.progress.parallel"' in engine,
 'progress not gate name':'current = p[4]' not in engine,
 'gate progress name':'GateProgress-' in engine and 'GateProgress-' in hist,
 'detail left accent':'p.Left + 4' in ui and 'stateColor(state)' in ui,
 'detail failed red':'case "FAILED", "FEHLER", "FAIL":' in ui and 'return colors.failure' in ui,
 'large detail close font':'fontDetailClose' in model and 'createFont(a.dpi, 22' in ui,
 'detail close hover':'hoverDetailClose' in model and 'closeColor = colors.green' in ui,
 'detail viewport clip':'contentBottom = 646' in ui,
 'raw variable block height':'lineHeights := [4]int{}' in ui and 'measureWrappedTextHeight' in ui,
 'raw word wrap':'dtWordBreak|dtNoPrefix' in ui and 'wrapTextToWidth' in ui,
 'raw pixel scrolling':'detailScroll += step' in ui,
 'raw clip region':'procIntersectClipRect.Call' in ui and 'procSaveDC.Call' in ui and 'procRestoreDC.Call' in ui,
 'raw labels from i18n':all(x in ui for x in ['popover.raw.expected','popover.raw.detail','popover.raw.section']),
 'popover consumes interior clicks':'Never fall through to the gate row behind it' in ui,
 'whole middle viewport scroll':'whole middle content (summary + assessment + findings)' in ui,
 'scrollbar drag state':'detailScrollDragging' in model and 'detailScrollDragOffset' in model,
 'scrollbar live mouse move':'handleDetailScrollDrag' in ui and 'procUpdateWindow.Call(a.hwnd)' in ui,
 'scrollbar capture':'procSetCapture' in win32 and 'procReleaseCapture' in win32,
 'escape closes detail':'if wParam == vkEscape {' in ui and 'app.closeRepairDialog()' in ui and 'app.closeDetailPopover()' in ui,
 'vector export icon':'func drawExportPackageIcon' in ui,
 'vector open folder icon':'func drawOpenFolderIcon' in ui and 'north-east/open arrow' in ui,
 'history overall normalized':'normalizeMeasurementStatus' in hist and 'measurementStatusText' in hist,
 'double buffer memory dc':'procCreateCompatibleDC.Call' in ui,
 'double buffer bitmap':'procCreateCompatibleBitmap.Call' in ui,
 'single publish BitBlt':'procBitBlt.Call' in ui,
 'erase suppression':'case wmEraseBkgnd:' in ui and 'return 1' in ui,
 'TrackMouseEvent':'procTrackMouseEvent.Call' in ui,
 'all gates canonical checking':'a.liveGateDisplay[i] = gateChecking' in engine,
 'engine output metadata':all(x in engine for x in ['ToolVersion:', 'Started:', 'Duration:', 'ExitCode:', 'RunError:', '=== STDOUT ===', '=== STDERR ===']),
 'engine separate stderr':'cmd.Stderr = &stderr' in engine,
 'schema 4 export':'SchemaVersion:' in hist and '4,' in hist[hist.find('SchemaVersion:'):hist.find('SchemaVersion:')+40],
 'export manifest':'ExportManifest.json' in hist,
 'app session paths':all(x in hist for x in ['AppSession/Logs/', 'AppSession/Diagnostics/']),
 'startup debug':'StartupDebug-' in runtime and 'writeStartupDebug' in main,
 'ui trace exported':'UITrace-' in trace and 'UITrace-' in hist,
 'ui trace heartbeat':'HEARTBEAT ping=' in trace,
 'tray result uses i18n':'tray.menu.result' in ui,
 'custom export modal uses i18n':all(x in ui for x in ['modal.export.success.title','action.open_folder','action.close']),
 'gate names from i18n':'gateNameKeys' in model and 'func gateName(' in model and 'Razer AppEngine", "Razer DriverStore' not in model,
 'gate details from i18n':'gateDetailKeys' in model and 'func gateDetail(' in model,
 'window title from i18n':'app.window_title' in ui and 'mainWindowTitle' not in win32,
 'app name from i18n':'func appName() string { return tr("app.title") }' in model,
 'structured runtime root':'runtimeAssetPath' in runtime and 'filepath.Join(a.runtimeDir, rel)' in runtime and 'Runtime is ephemeral and app-owned' in runtime,
 'structured runtime asset dirs':(root/'assets/status').is_dir() and (root/'assets/ui').is_dir() and 'statusRoot := filepath.Join(assetRoot, "status")' in ui and 'uiRoot := filepath.Join(assetRoot, "ui")' in ui,
 'portable structured runtime dirs':all(x in (root/'tools/package_portable.py').read_text(encoding='utf-8') for x in ['Runtime/assets','Runtime/assets/status','Runtime/assets/ui']),
 'safety model file':(root/'SAFETY-MODEL.txt').exists(),
 'repair source present':(root/'repair/repair-chroma-services-v1.1.0.ps1').exists(),
 'repair/setup/diagnostics embedded':'//go:embed health-engine-v1.4.6.ps1 diagnostics repair setup assets' in runtime,
 'repair runtime path':'Runtime/repair' in (root/'tools/package_portable.py').read_text(encoding='utf-8') and 'repairScriptPath' in runtime,
 'repair helper main':'--repair-helper' in main and 'runRepairHelperMain' in main,
 'repair narrow gate':'repairGateChromaServices    = 7' in (root/'repair.go').read_text(encoding='utf-8'),
 'repair target allowlist':all(x in (root/'repair.go').read_text(encoding='utf-8') for x in ['Razer Chroma SDK Service','Razer Chroma SDK Server']),
 'repair exact eligibility':all(x in problem for x in ['isServiceState(diagSvc, "Running", "Auto")','isServiceState(streamSvc, "Stopped", "Manual")','isServiceState(s, "Stopped", "Auto")','isServiceState(s, "Running", "Auto")']),
 'repair UAC':'launchElevatedHelper(strings.Join(params, " "))' in (root/'repair.go').read_text(encoding='utf-8') and 'RequiresElevation' in (root/'problem.go').read_text(encoding='utf-8'),
 'repair result audit':'Diagnostics\\Repairs' in (root/'SAFETY-MODEL.txt').read_text(encoding='utf-8') and 'AppSession/Repairs/' in hist,
 'repair 5 second check':'Start-Sleep -Seconds 5' in (root/'repair/repair-chroma-services-v1.1.0.ps1').read_text(encoding='utf-8'),
 'repair modal':'drawRepairModal' in ui and 'repairDialogConfirm' in (root/'repair.go').read_text(encoding='utf-8'),
 'repair recheck action':'action.repair.recheck' in ui,
 'repair i18n keys':'repair.confirm.title' in (root/'locales/de-DE.json').read_text(encoding='utf-8'),
 'version check source':(root/'versioncheck.go').exists() and 'https://discovery3.razerapi.com/api/v1/endpoints' in (root/'versioncheck.go').read_text(encoding='utf-8') and 'https://manifest3.razerapi.com/api/v1/releases/' in (root/'versioncheck.go').read_text(encoding='utf-8'),
 'version check async':'refreshVersionStatusAsync' in (root/'versioncheck.go').read_text(encoding='utf-8') and 'a.refreshVersionStatusAsync()' in main,
 'version check does not alter health':'VersionStatus-' not in (root/'health-engine-v1.4.6.ps1').read_text(encoding='utf-8'),
 'appengine version domains separate':all(x in (root/'health-engine-v1.4.6.ps1').read_text(encoding='utf-8') for x in ['RazerAppEngine package version','RazerAppEngine file version','nicht mit der Paketversion vergleichen']),
 'version status exported':'VersionStatus-' in hist and 'AppSession/Diagnostics/' in hist,
 'version ui':'info.versioncheck.synapse.installed' in ui and 'info.versioncheck.appengine.file' in ui,
 'version local product metadata':'https://apps.razer.com/synapse/dashboard' in (root/'versionparse.go').read_text(encoding='utf-8') and 'https://apps.razer.com/chroma-app/dashboard' in (root/'versionparse.go').read_text(encoding='utf-8'),
 'version domain guard':'compareInstalledToOffered' in (root/'versioncheck.go').read_text(encoding='utf-8') and 'isComparableManifestVersion' in (root/'versioncheck.go').read_text(encoding='utf-8') and 'current_version_registry_key' in (root/'versioncheck.go').read_text(encoding='utf-8'),
 'info footer widened security':'footerValueRects := []rect{{145, 640, 365, 668}, {380, 640, 890, 668}, {925, 640, 1110, 668}}' in ui and 'dtCenter|dtVCenter|dtSingleLine|dtNoPrefix' in ui,
 'setup view first':'items := []string{tr("nav.setup"), tr("nav.status"), tr("nav.logs"), tr("nav.info")}' in ui and 'case 0:\n\t\ta.drawSetupView' in ui,
 'setup health gate':'HEALTH blocked setupReady=false' in engine and 'a.startSetupScan()' in engine and 'setupContinueHealth' in model,
 'setup persistent profile':'RazerDeviceInventory-v2.json' in main and 'setupDir' in model,
 'setup runtime script':'setup/setup-razer-inventory-v1.0.6.ps1' in runtime and 'Runtime/setup' in (root/'tools/package_portable.py').read_text(encoding='utf-8'),
 'setup exported':'AppSession/Setup/' in hist and 'SetupScan-' in hist,
 'setup guided calibration action':'secondary := rect{406, actionTop, 686, actionBottom}' in ui and 'action.setup_calibrate' in ui and 'openSetupCalibration' in ui,
 'setup progress animation':'drawSetupScanOverlay' in ui and 'barW := tableW * 70 / 100' in ui and 'colors.green' in ui and 'checking || setupScanning' in ui and 'procSetTimer.Call(a.hwnd, 1, 125, 0)' in (root/'setupscan.go').read_text(encoding='utf-8'),
 'setup debug exported':'SetupScannerDebug-' in hist and 'copySetupDebugArtifact' in (root/'setupscan.go').read_text(encoding='utf-8'),
 'device gate generic':'gate.devices.name' in model and 'gate.blackwidow.name' not in model,
 'setup present typed entry color':'drawSetupConnectionSummary' in ui and 'entryColor = colors.green' in ui and 'c.PresentAtScan' in ui,
 'setup inventory fade':'darkenRect(hdc, table, 128)' in ui,
 'setup device-class icons':'drawSetupDeviceClassIcon' in ui and 'setupProductDeviceClass(inv, product)' in ui and 'storedConnectionDeviceClass' in setupscan,
 'setup live role and PID acid green':'drawPart(role+" · ", entryColor)' in ui and 'drawPart(pid, entryColor)' in ui and 'entryColor = colors.green' in ui,
 'setup live per-row refresh overlay':'drawSetupLiveRefreshBar' in ui and 'drawSetupConnectionSummary(hdc, a, inv, product' in ui and 'liveRefreshing' in ui,
 'setup live refresh overlays text band':'centerY := int(r.Top+r.Bottom) / 2' in ui and 'int32(centerY - 3)' in ui and 'int32(centerY + 3)' in ui and 'r.Bottom - 7' not in ui,
 'setup live refresh hides stale cell text':'if refreshing {' in ui and 'drawSetupLiveRefreshBar(hdc, r)' in ui and 'return' in ui[ui.find('func drawSetupConnectionSummary'):ui.find('func darkenRect')],
 'setup live refresh animation timer':'setupLiveRefreshTimerID = 2' in (root/'device_monitor.go').read_text(encoding='utf-8') and 'procSetTimer.Call(a.hwnd, setupLiveRefreshTimerID, 125, 0)' in (root/'device_monitor.go').read_text(encoding='utf-8') and 'procKillTimer.Call(a.hwnd, setupLiveRefreshTimerID)' in (root/'device_monitor.go').read_text(encoding='utf-8'),
 'gate4 contextual connection presentation':'gateDevicePresentationChecks' in ui and 'if !raw && idx == 3' in ui and 'gate.devices.connection.inactive.alternative' in ui,
 'detail bottom scroll reserve':'detailBottomScrollReserve = 52' in ui and 'totalH += detailBottomScrollReserve' in ui,
 'logs wheel hint removed':'Mausrad zum Scrollen' not in (root/'locales/de-DE.json').read_text(encoding='utf-8'),
 'info cyan':'0x00ffc800' in ui and 'case "INFO":' in ui and 'return colors.info' in ui,
 'info no pseudo expected':'popover.info.classification' in ui and 'popover.raw.info_expected' in ui,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+': '+k)
checks.update({
 'powershell runtime bom shim':'windowsPowerShellUTF8ScriptBytes' in runtime and 'engineRuntimeEncoding=UTF-8-BOM' in runtime,
 'powershell stdout utf8':'[Console]::OutputEncoding = $enc; $OutputEncoding = $enc;' in engine and '"-Command", psCommand' in engine,
})
failed=[k for k,v in checks.items() if not v]
for k,v in list(checks.items())[-2:]: print(('PASS' if v else 'FAIL')+': '+k)
print(f'v3.0.8.0 static recovery/reference checks: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
