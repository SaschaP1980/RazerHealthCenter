# Razer Synapse + Chroma Health Center v3.0.2

v3.0.2 fixes the lifecycle and visual mode semantics of historical measurements
in PROTOKOLLE. It is a UI/session-state patch on top of v3.0.1; Health Engine
1.4.6, VersionStatus schema 4, diagnostic/problem/repair architecture and all
repair-safety rules remain unchanged.

## Session-only historical tab state

A historical measurement tab now exists only for the lifetime of the current app
process.

After a complete application restart:

- only the permanent PROTOKOLLE tab is open and active;
- no historical measurement is open or active;
- log-table selection starts unselected and scroll starts at the initial position;
- `HistoricalLogStamp` / `HistoricalActive` are no longer serialized or restored
  through `UIState-v1.json` or another persistent state file.

Within one running process, normal measurement-list refreshes still preserve an
already opened historical measurement and its active/inactive tab state.

## Historical archive presentation

The historical measurement view is now deliberately distinct from LIVE status:

- top-right mode label is cyan `ARCHIVANSICHT  •  NICHT LIVE`;
- historical tab text and active underline use cyan as archive-mode color;
- a prominent cyan `HISTORISCHE MESSUNG · <timestamp>` header is shown with
  `Gespeicherter Messstand · keine Live-Daten`;
- the LIVE-style 100% progress bar is removed from historical mode;
- static `MESSUNG ABGESCHLOSSEN`, runtime and 13/13 completion information are
  shown instead;
- `HISTORISCHER SYSTEMSTATUS` is visually stronger.

The recorded health result itself is not recolored. Green/yellow/red keep their
existing health meaning. The heart/status icon is intentionally unchanged and no
clock/archive badge is added.

## Unchanged v3.0.1 contracts

- App version: 3.0.2
- Health Engine: 1.4.6
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.1.0 native SetupAPI
- Diagnostic Orchestrator: 1.0.0
- Problem Catalog: 1.0.0
- Repair Engine / Catalog: 2.0.0
- Chroma Repair Recipe: 1.1.0
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 4
- ExportManifest schema: 4
- Locale: de-DE, 375 UI keys

No repair is automatic. Every mutation still requires explicit in-app user
confirmation; UAC is additional where required and post-repair read-only
verification remains mandatory.

## Validation

New build-gated regression:

`tools/validate_v302_historical_session_archive.py`

The unchanged v3.0.1 source fails the new contract (RED). v3.0.2 passes all 19
checks (GREEN), in addition to the complete existing regression/build suite.
