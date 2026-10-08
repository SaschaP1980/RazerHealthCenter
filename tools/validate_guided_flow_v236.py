#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sg = (root / 'setupscan.go').read_text(encoding='utf-8')
dm = (root / 'device_monitor.go').read_text(encoding='utf-8')
ui = (root / 'ui.go').read_text(encoding='utf-8')
model = (root / 'model.go').read_text(encoding='utf-8')
locale = (root / 'locales/de-DE.json').read_text(encoding='utf-8')

def section(text: str, start: str, end: str) -> str:
    i = text.find(start)
    j = text.find(end, i + 1)
    if i < 0 or j < 0:
        return ''
    return text[i:j]

device_change = section(dm, 'func (a *App) handleWindowsDeviceChange', 'func livePIDSet')
skip_step = section(sg, 'func (a *App) skipCurrentCalibrationStep', 'func (a *App) advanceCalibrationProductLocked')
checks = {
    'wireless confirmation stage exists': 'setupCalibrationWirelessConfirm' in sg,
    'flow is device-profile driven': 'calibrationWirelessFlowLocked' in dm and 'setupProductDeviceClass(a.inventory, product)' in dm,
    'mouse keeps automatic cable transition': 'setupProductDeviceClass(a.inventory, product) == "mouse"' in dm and 'return setupWirelessFlowEventTransition' in dm,
    'non-mouse defaults to explicit confirmation': 'return setupWirelessFlowUserConfirm' in dm,
    'confirmation stage cannot be auto-completed by WM_DEVICECHANGE': 'setupCalibrationWirelessConfirm' not in device_change,
    'explicit wireless confirmation action exists': 'confirmCurrentWirelessCalibration' in dm and 'runWirelessCalibrationConfirmation' in dm and 'a.confirmCurrentWirelessCalibration()' in ui,
    'confirmed wireless evidence is distinct': 'user-guided-wireless-confirmation' in dm,
    'confirmation requires learned wired path to be absent': 'setup.calibration.error.wired_still_present' in dm and 'a.knownRolePIDs(productKey, "wired-usb")' in dm,
    'confirmation UI explains optional hardware switch': 'setup.calibration.confirm.wireless' in ui and 'Falls ein separater Modusschalter vorhanden ist' in locale,
    'completion no longer launches full setup scan': 'a.startSetupScan()' not in dm,
    'skip completion no longer launches full setup scan': 'a.startSetupScan()' not in skip_step,
    'new PID metadata remains explicit advisory': 'setupCalibrationNeedsInventoryRefresh' in model and 'setup.calibration.complete.inventory_refresh' in ui,
    'no known endpoint PID/model rule': not any(token in (dm + '\n' + sg).lower() for token in ['00c0','00c1','02c9','02cc','viper v3 pro','blackwidow']),
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL') + ': ' + name)
print(f'guided flow v2.3.6 regression checks: {len(checks)-len(failed)}/{len(checks)}')
if failed:
    sys.exit(1)
