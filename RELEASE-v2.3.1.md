# Release v2.3.1

v2.3.1 fixes the native Windows startup/live-probe failure found during the first
field test of v2.3.0.

Native failure evidence from v2.3.0:
- `RegisterDeviceNotificationW` registration succeeded.
- the immediate startup live refresh failed before producing presence data with:
  `Cannot overwrite variable PID because it is read-only or constant.`
- root cause: PowerShell variable names are case-insensitive, so the local `$pid`
  write targets in `setup-razer-live-v1.0.0.ps1` collided with the read-only
  automatic `$PID` process variable.

Fixes:
- App version advances to 2.3.1.
- Fast Setup Live Probe advances from 1.0.0 to 1.0.1.
- all live-probe local PID variables are renamed to `$devicePid`.
- a permanent regression guard discovers the actual embedded/production
  PowerShell payloads and rejects assignment/foreach targets named `$pid` in any
  casing before every canonical build.
- the same guard found the identical latent collision in the active Health Engine
  fallback `Test-ConnectionUsesRazerStack`; Health Engine advances from 1.4.2 to
  1.4.3 with only that local-variable rename. Gate and evidence semantics remain
  unchanged.
- Setup Scanner remains 1.0.6; Repair Engine remains 1.0.0.
- Device Inventory schema remains 2; Connection History remains schema 2.
- Fast live presence, WM_DEVICECHANGE debouncing and event-driven guided learning
  architecture otherwise remain unchanged from v2.3.0.

Regression rule:
- RED was demonstrated against the unmodified v2.3.0 production sources before
  any fix: four live-probe write/foreach targets and one Health Engine fallback
  assignment were detected.
- GREEN was demonstrated after the rename with the same persistent guard.

Native status:
- the v2.3.0 diagnostic package proves the original live probe failed at runtime
  for the reserved `$PID` reason while Windows notification registration itself
  succeeded.
- v2.3.1 therefore still requires the normal native acceptance test for startup
  live presence, cable arrival/removal refresh and event-driven guided learning.
