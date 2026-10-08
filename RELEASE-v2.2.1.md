# Release v2.2.1

v2.2.1 productionizes the Setup scanner fixes validated interactively on native
Windows. Setup Scanner 1.0.1 fixes the PowerShell automatic `$PID` collision,
Windows PowerShell 5.1 generic-list serialization failure, OrderedDictionary
product-grouping bug and StrictMode failures on optional USB/HID Registry
properties.

The resulting native scan correctly separated the current Razer Viper V3 Pro
from the BlackWidow V4 Low-profile HyperSpeed and associated the BlackWidow
alternate connection path from local Windows metadata. No current-device PID or
model requirement is hardcoded into the scanner.

Setup UI/workflow refinements:
- Setup contains only `Setup-Scan starten`; the duplicate/locked health action is removed.
- Health is initiated only from Status. If inventory is absent, the Status action
  starts Setup automatically and resumes the originally requested health run after
  successful profile creation.
- An indeterminate cyan progress bar remains animated for the duration of a Setup scan.
- Setup Scanner debug JSON/TXT is copied into session Diagnostics and included in
  diagnostic exports, including failure cases where the final inventory is not produced.

Health Engine 1.4.0, Repair Engine 1.0.0, Gate-8 repair policy, INFO cyan
semantics and the Synapse/Chroma version-monitor logic remain unchanged.
