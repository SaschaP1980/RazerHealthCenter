#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
setup=(root/'setup/setup-razer-inventory-v1.0.6.ps1').read_text(encoding='utf-8')
sg=(root/'setupscan.go').read_text(encoding='utf-8')
dm=(root/'device_monitor.go').read_text(encoding='utf-8')
ui=(root/'ui.go').read_text(encoding='utf-8')
main=(root/'main.go').read_text(encoding='utf-8')
win=(root/'win32.go').read_text(encoding='utf-8')
runtime=(root/'runtime.go').read_text(encoding='utf-8')
locale=(root/'locales/de-DE.json').read_text(encoding='utf-8')
model=(root/'model.go').read_text(encoding='utf-8')
device_change_handler=dm[dm.index('func (a *App) handleWindowsDeviceChange'):dm.index('func livePIDSet')]
checks={
 'app/scanner versions':'appVersion                   = "3.0.8"' in model and "$ScanVersion = '1.0.6'" in setup and 'setupScanVersion = "1.0.6"' in sg,
 'native live probe version':'setupLiveProbeVersion = "1.1.0"' in dm,
 'native SetupAPI enumeration':all(x in dm for x in ['procSetupDiGetClassDevsW.Call','procSetupDiEnumDeviceInfo.Call','utf16("USB")','digcfPresent|digcfAllClasses']),
 'live PowerShell removed from active setup':not any((root/'setup').glob('setup-razer-live-*.ps1')) and 'setupLiveScriptPath' not in model and 'setupLiveScriptPath' not in runtime,
 'known PID target set':'knownSetupPIDsLocked' in dm and 'knownSet[pid] = true' in dm and 'if targetProductKey == "" && !knownSet[pid]' in dm,
 'present USB roots only':'razerUSBRootPID' in dm and 'USB\\VID_1532&PID_' in dm and 'id[len(prefix)+4] !=' in dm,
 'root identity verification':'devpkeyDeviceBusReportedDeviceDesc' in dm and 'bus-reported-device-description' in dm and 'IdentityVerified' in dm,
 'target-product discovery native':'result.Mode = "target-product"' in dm and 'targetProductKey != ""' in dm and 'strings.EqualFold(productKey, targetProductKey)' in dm,
 'native probe diagnostics':all(x in dm for x in ['Implementation:   "native-setupapi-usb"','RequestedPIDs','EnumeratedUSBNodes','MatchedRazerRoots','SetupLiveProbe-v1.1.0.json']),
 'probe errors fail closed':'live probe incomplete' in dm and 'len(result.Errors) > 0' in dm,
 'pnp burst debounce generation':'setupLiveRefreshGeneration++' in dm and 'generation != a.setupLiveRefreshGeneration' in dm,
 'pnp active follow-up bounded':'setupLiveRefreshQueued = true' in dm and 'Preserve at most one follow-up' in dm,
 'device notification registration':'RegisterDeviceNotificationW' in win and 'deviceNotifyAllInterfaces' in win,
 'wm device change':'wmDeviceChange' in win and 'handleWindowsDeviceChange' in ui,
 'arrival/removal events':all(x in win for x in ['dbtDeviceArrival','dbtDeviceRemoveComplete','dbtDevNodesChanged']),
 'startup live refresh':'requestLivePresenceRefresh("startup"' in main,
 'debounced event refresh':'800*time.Millisecond' in dm and 'requestLivePresenceRefresh' in dm,
 'historical snapshot not green':'liveFresh && ok && c.PresentAtScan' in ui,
 'snapshot wording':'setup.state.snapshot.detail' in ui and 'Letzter Inventurstand geladen. Setup-Scan starten, um aktuelle Verbindungen zu prüfen.' in locale,
 'old inventory class recovery':'storedConnectionDeviceClass' in sg and 'mouhid' in sg and 'kbdhid' in sg and '&MI_00' in sg,
 'wizard state machine':all(x in sg for x in ['setupCalibrationWiredPreparing','setupCalibrationWiredWaiting','setupCalibrationWiredVerifying','setupCalibrationWirelessPreparing','setupCalibrationWirelessWaiting','setupCalibrationWirelessConfirm','setupCalibrationWirelessVerifying']),
 'wizard arms native baseline':'runCalibrationBaseline' in dm and 'setupCalibrationBaseline' in dm and 'runSetupLiveProbe(productKey, nil)' in dm,
 'wizard waits for OS event':'setupCalibrationWiredWaiting' in dm and 'requestCalibrationVerification' in dm,
 'unrelated event ignored':'device event unrelated/no target delta' in dm and 'samePIDSet' in dm,
 'wired exact delta':'newPIDs' in dm and 'len(newPIDs) == 1' in dm,
 'wireless excludes wired role':'knownRolePIDs(productKey, "wired-usb")' in dm,
 'wireless flow derives from device profile':'calibrationWirelessFlowLocked' in dm and 'setupProductDeviceClass(a.inventory, product) == "mouse"' in dm and 'setupWirelessFlowUserConfirm' in dm,
 'mouse wireless remains event driven':'setupWirelessFlowEventTransition' in dm and 'setupCalibrationWirelessWaiting' in dm,
 'non-mouse wireless requires confirmation':'setupCalibrationWirelessConfirm' in dm and 'confirmCurrentWirelessCalibration' in dm and 'runWirelessCalibrationConfirmation' in dm,
 'confirmation cannot auto-complete on device event':'setupCalibrationWirelessConfirm' not in device_change_handler,
 'confirmation is user initiated':'setup.calibration.action.wireless_confirm' in ui and 'a.confirmCurrentWirelessCalibration()' in ui,
 'confirmation has distinct evidence source':'user-guided-wireless-confirmation' in dm,
 'confirmation rejects still-active wired path':'setup.calibration.error.wired_still_present' in dm and 'a.knownRolePIDs(productKey, "wired-usb")' in dm,
 'identity fail closed':'IdentityVerified' in dm and 'guided connection identity is not verified' in dm,
 'explicit evidence conflict':'candidate.ExplicitRole' in dm and 'explicit role evidence conflicts' in dm,
 'runtime role history':'commitGuidedConnectionRole' in dm and 'calibratedAt' in dm and 'Calibrated = true' in dm,
 'guided sources':all(x in dm for x in ['user-guided-wired-transition','user-guided-wireless-transition','user-guided-wireless-confirmation']),
 'history pid candidates':'Runtime-learned PIDs are app-owned observations' in setup and '$pids.Add($historyPid)' in setup,
 'no automatic post-learning full scan':'a.startSetupScan()' not in dm and 'complete && learned > 0' not in sg,
 'new pid metadata is advisory only':'setupCalibrationNeedsInventoryRefresh' in model and 'setup.calibration.complete.inventory_refresh' in ui and 'inventoryRefreshRecommended=%t' in dm,
 'wizard skip supported':'skipCurrentCalibrationStep' in sg and 'action.skip' in ui,
 'guided UI localized':all(k in locale for k in ['setup.calibration.waiting.wired','setup.calibration.waiting.wireless','setup.calibration.waiting.wireless.auto','setup.calibration.confirm.wireless','setup.calibration.action.wireless_confirm','setup.calibration.preparing','setup.calibration.verifying']),
 'passive topology roles disabled':'topology-hid-collection-asymmetry' not in setup and 'topology-transition-confirmed' not in setup,
 'no endpoint PID/model semantics':not any(t.lower() in (setup+'\n'+dm).lower() for t in ['00c0','00c1','02c9','02cc','viper v3 pro','blackwidow']),
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+': '+k)
print(f'guided/live calibration checks: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
