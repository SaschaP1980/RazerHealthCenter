# Razer Synapse + Chroma Health Center v3.0.3

v3.0.3 is a focused UI polish release for the historical PROTOKOLLE detail view. It reduces duplicated archive copy while preserving the strong separation between archive mode and LIVE status introduced in v3.0.2.

## Historical archive header polish

- The historical timestamp remains in the cyan measurement tab and is no longer repeated in the summary card.
- The redundant `HISTORISCHE MESSUNG · <timestamp>` and `Gespeicherter Messstand · keine Live-Daten` rows are removed.
- `HISTORISCHER SYSTEMSTATUS` is rendered in cyan.
- Historical `LAUFZEIT` is renamed to `DAUER`.
- Static completion information is simplified to `MESSUNG ABGESCHLOSSEN` plus `13 / 13 Prüfgruppen`.
- The cyan separator line above the heart/status content is removed.
- The historical summary card receives a very subtle cyan-tinted dark background, implemented as a pre-blended color equivalent to roughly 6% translucent cyan over the normal status surface. This preserves rounded native GDI edges cleanly.
- The heart/status icon is unchanged and receives no archive/clock badge.
- Green/yellow/red result colors are unchanged and continue to represent only the stored health result.

## Session lifecycle unchanged from v3.0.2

Historical tabs remain session-only. After a complete app restart, PROTOKOLLE starts with only its permanent tab, no historical measurement open or active, no restored table selection and scroll position zero. Within the same running process, the historical tab remains available across normal measurement-list refreshes and tab switching.

## Unchanged platform contracts

- App version: 3.0.3
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

No repair is automatic. Every mutation still requires explicit in-app user confirmation; UAC is additional where required and post-repair read-only verification remains mandatory.

## Validation

New build-gated regression:

`tools/validate_v303_archive_header_polish.py`

Canonical v3.0.2 fails the new presentation contract with 5/22 PASS (RED). v3.0.3 passes 22/22 (GREEN). The existing v3.0.2 historical session/archive regression remains GREEN, as do the historical detail, manifest authority, diagnostic/repair, Setup, guided-learning, Healthcheck, PE and static UI/reference gates.
