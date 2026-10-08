# Release v2.3.5

- App: 2.3.5
- Health Engine: 1.4.3 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 (native SetupAPI)
- Repair Engine: 1.0.0 (unchanged)

## Change

The live connection hot path no longer launches PowerShell. Startup, WM_DEVICECHANGE refreshes and guided target-product baseline/delta checks now use native Windows SetupAPI from Go. Known-PID mode filters the persisted PID target set against currently present USB roots and reads BusReportedDeviceDesc only for matching Razer roots. Guided target-product mode can still discover a new current Razer PID and verifies it against the selected productKey.

PnP event bursts are quiet-window debounced by generation before the probe begins. Events received during the short native probe retain at most one follow-up. AppDebug and SetupLiveProbe diagnostics now expose requested/present/changed PID sets, USB-node count, matched-root count and probe duration.

No full Setup, Health, Repair, connection-role, persistence or Gate semantics are changed.
