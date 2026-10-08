# Release v2.2.2

v2.2.2 fixes the false FAILED state observed after the first successful generic
Setup inventory.

Native diagnostics showed that Viper V3 Pro PID 00C1 legitimately uses Microsoft
Inbox HID INF files and does not expose the BlackWidow RzDev/RZVIRTUAL/RZCONTROL
stack. v2.2.1 therefore produced false failures in DriverStore, RZVIRTUAL /
RZCONTROL and Upper-/LowerFilters.

Changes:
- Setup Scanner 1.0.2 / inventory schema 2 records per-connection driver domain
  and stack capabilities.
- Microsoft Inbox INF files are separated from Razer-owned DriverStore INF files.
- Gate 2 validates only Razer `rzdevu_*`/`rzcommonu.inf` packages.
- Gates 5 and 6 are capability-aware and mark non-applicable Windows-Inbox paths
  as INFO instead of FAIL/UNKNOWN.
- PID 02C9 is recorded as the verified BlackWidow Wireless-Dongle path.
- PID 02CC is recorded as the verified BlackWidow wired USB path.
- The Setup table exposes the verified connection labels without guessing roles
  for unrelated devices.
- Existing schema-1 inventories are intentionally invalidated; v2.2.2 performs a
  new read-only Setup scan before Health.

Health Engine 1.4.1, Setup Scanner 1.0.2 and the schema-2 profile remain fully
read-only toward Razer/Windows. Repair Engine 1.0.0 is unchanged.
