# Release v2.4.0

- App: 2.4.0
- Health Engine: 1.4.5 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 355 UI keys

## Historical measurement tab

PROTOKOLLE now has one reusable historical measurement tab next to the permanent
PROTOKOLLE tab. `Details anzeigen` and row double-click open the selected
measurement. The tab label is timestamped and rendered in the measurement result
color; its X closes only the historical tab and returns to PROTOKOLLE.

The historical tab displays the stored overall result, duration, completed 13/13
gates and per-gate Prüfdetails. It is strictly read-only: no repair action is
available and Gate 4 does not substitute current live device presentation data.

## State behavior

- historical tab stamp/open state + active logs subview persist across restart;
- restore occurs only while the referenced measurement is still present,
  readable and detail-capable;
- logs table selection and scroll position persist only for the current app
  session and reset after full process exit;
- switching to STATUS/SETUP/INFO and back preserves the session logs state.

## Compatibility fallback

Old or incomplete measurements remain visible in the logs list when possible.
If the stored engine JSON cannot supply a complete 13-gate final snapshot,
`Details anzeigen` is disabled and AUSGEWÄHLTE MESSUNG explains why the
historical detail view is unavailable.

## Historical package export

The two PROTOKOLLE actions remain present in the historical tab:

- `Diagnosepaket erstellen` exports the opened historical measurement plus its
  resolved app-session evidence;
- `Paketordner öffnen` opens the normal Exports folder.

Current mutable Setup inventory/history/live-probe files are not injected into a
historical package because they may no longer describe the old measurement.

## Status wording

The live status page now uses `AKTUELLER SYSTEMSTATUS` for the page heading and
small label above the heart. Historical measurement details use
`HISTORISCHER SYSTEMSTATUS`.

## Regression contract

`tools/validate_historical_details_v240.py` is build-gated with 21 checks and
verifies the single-tab model, persistence boundary, repeat-safe Windows UI-state
writes, double-click/details opening, read-only historical detail path, old-log
fallback, historical package scoping and status wording. RED against the pristine
v2.3.12 baseline is 1/21 as expected; GREEN on v2.4.0 is 21/21. Both regression
captures are included in the source release.
