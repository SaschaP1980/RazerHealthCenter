#!/usr/bin/env python3
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sg = (root/'setupscan.go').read_text(encoding='utf-8')
dm = (root/'device_monitor.go').read_text(encoding='utf-8')
ui = (root/'ui.go').read_text(encoding='utf-8')
loc = (root/'locales/de-DE.json').read_text(encoding='utf-8')
build = (root/'build.sh').read_text(encoding='utf-8')

def section(text, start, end):
    i=text.find(start); j=text.find(end, i+1)
    return text[i:j] if i>=0 and j>=0 else ''

verify = section(dm, 'func (a *App) runCalibrationVerification', 'func (a *App) confirmCurrentWirelessCalibration')
confirm = section(dm, 'func (a *App) runWirelessCalibrationConfirmation', 'func (a *App) selectCalibrationCandidate')
advance = section(sg, 'func (a *App) continueCalibrationSuccess', 'func (a *App) advanceCalibrationProductLocked')
checks = {
    'wired success stage exists': 'setupCalibrationWiredSuccess' in sg,
    'wireless success stage exists': 'setupCalibrationWirelessSuccess' in sg,
    'prompt title is recognition-oriented': '1. USB-Verbindung erkennen' in loc and '2. Wireless-Verbindung erkennen' in loc,
    'wired prompt is neutral before baseline': 'Um die USB-Verbindung mit diesem Gerät zu erkennen, starte den Lernschritt.' in loc,
    'wireless prompt is neutral before baseline': 'Um die Wireless-Verbindung mit diesem Gerät zu erkennen, starte den Lernschritt.' in loc,
    'physical USB instruction exists only as waiting copy': 'Schließe dieses Gerät per USB-Kabel an und stelle, falls vorhanden, auf kabelgebundenen Betrieb.' in loc,
    'separate USB waiting status exists': 'Warte auf USB-Verbindung' in loc,
    'separate wireless waiting status exists': 'Warte auf Wireless-Verbindung' in loc,
    'wired commit stops on success stage': 'a.setupCalibrationStage = setupCalibrationWiredSuccess' in verify,
    'event wireless commit stops on success stage': 'a.setupCalibrationStage = setupCalibrationWirelessSuccess' in verify,
    'confirmed wireless commit stops on success stage': 'a.setupCalibrationStage = setupCalibrationWirelessSuccess' in confirm,
    'success result is retained for acknowledgement': 'setupCalibrationSuccessPID' in dm and 'setupCalibrationSuccessRole' in dm,
    'success acknowledgement action exists': 'continueCalibrationSuccess' in sg and 'a.continueCalibrationSuccess()' in ui,
    'wired acknowledgement enters wireless prompt': 'setupCalibrationWiredSuccess' in advance and 'setupCalibrationWirelessPrompt' in advance,
    'wireless acknowledgement advances product': 'setupCalibrationWirelessSuccess' in advance and 'advanceCalibrationProductLocked' in advance,
    'success copy is explicit': 'USB-Verbindung erfolgreich erkannt' in loc and 'Wireless-Verbindung erfolgreich erkannt' in loc,
    'continue button is localized': 'action.continue' in loc and 'tr("action.continue")' in ui,
    'mouse auto wireless flow retained': 'setupProductDeviceClass(a.inventory, product) == "mouse"' in dm and 'setupWirelessFlowEventTransition' in dm,
    'non-mouse confirmation flow retained': 'setupWirelessFlowUserConfirm' in dm and 'confirmCurrentWirelessCalibration' in dm,
    'new validator is build-gated': 'validate_guided_ux_v2310.py' in build,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+': '+k)
print(f'Guided UX v2.3.10 checks: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
