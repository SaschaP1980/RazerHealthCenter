# Release v2.2.3

v2.2.3 fixes the architectural misuse of the fixed AppEngine `main.log` tail as
module/install completeness evidence.

The 8,000-line tail remains intentionally bounded, but its scope is now explicit:
it is only a **recent runtime-evidence window** for time-sensitive observations
such as `isPowerOn` and `missing ffi handler`. Module/install declarations found
in that window are retained only as `SUPPORTING` context.

Changes:
- Health Engine 1.4.2 introduces explicit evidence roles: `PRIMARY`, `RUNTIME`
  and `SUPPORTING`.
- Gates 7, 10 and 11 are decided from current direct system evidence:
  Chroma Registry, Game Manager Service, and RzComDriver/installation evidence.
- Missing, rotated-out, stale, unparsable or version-divergent AppEngine module
  log lines cannot independently create `UNKNOWN`, `WARN` or `FAIL`.
- Correlative module log observations remain visible as INFO diagnostics and are
  preserved in JSON with `EvidenceRole=SUPPORTING`.
- PowerShell gate severity, raw diagnostic severity and Go gate display all
  generically ignore `SUPPORTING` evidence when determining health severity.
- The log probe reports `runtime-tail-8000`, documenting that the fixed tail is
  not a module/install inventory mechanism.

Setup Scanner 1.0.2, Device Inventory schema 2, the verified BlackWidow PID-role
mapping and Repair Engine 1.0.0 are unchanged. Diagnostics remain read-only
against Razer/Windows.
