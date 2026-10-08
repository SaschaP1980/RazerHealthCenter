# Canonical reference source v2.3.1

This source tree is the canonical development reference for v2.3.1 after static,
package and clean-rebuild validation.

Core versions:
- App: 2.3.1
- Health Engine: 1.4.3
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.0.1
- Device Inventory schema: 2
- Connection History schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4
- i18n: de-DE, 321 keys

v2.3.1 regression contract:
- Production PowerShell payloads must never assign to or use `$pid` as a foreach
  target because PowerShell resolves it case-insensitively to the read-only
  automatic `$PID` variable.
- `tools/test_powershell_reserved_pid.py` discovers production payloads from the
  runtime embed references plus active setup/repair payloads and is executed by
  `build.sh` before the other validators.
- The RED fixture is the original v2.3.0 source, where the guard detects the live
  probe collision and the same latent Health Engine fallback collision.
- v2.3.1 uses `$devicePid` for those locals and the guard is GREEN.

Live presence contract:
- Persisted `presentAtScan` is historical until a successful current-session
  refresh.
- Startup runs one fast known-PID probe automatically when a valid inventory is
  available.
- Known-PID refresh is present-only and avoids Registry/DriverStore/INF history.
- A currently present connection is published only after current root product
  identity verifies to the stored `productKey`.
- `RegisterDeviceNotificationW` / `WM_DEVICECHANGE` events are triggers only;
  they never establish identity or role themselves.
- Probe errors fail closed.

Guided learning contract:
- Per-product baseline and target-delta checks reuse the fast live probe.
- Target mode may discover a previously unknown present PID only when current
  root identity verifies it to the selected `productKey`.
- Wired requires exactly one new verified connection; wireless excludes the
  already-known HIGH wired connection and requires exactly one remaining verified
  target connection.
- ambiguity, weak identity and explicit descriptor-role conflict write no role.

Identity/PID contract:
- no endpoint PID constant assigns product identity, device class or connection
  role in active production logic.
- product identity prefers root `DEVPKEY_Device_BusReportedDeviceDesc`.
- PIDs are runtime observations only.
- `ContainerId` is supporting evidence, not a product merge key.

Health Engine 1.4.3:
- read-only and capability-driven as in 1.4.2;
- only the fallback local variable in `Test-ConnectionUsesRazerStack` changes
  from `$pid` to `$devicePid` to avoid the reserved-variable collision;
- gate, evidence-role and capability semantics are unchanged.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
