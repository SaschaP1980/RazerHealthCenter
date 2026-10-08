# Razer Synapse + Chroma Health Center v3.0.4

v3.0.4 is a deliberately narrow visual-calibration release for the historical PROTOKOLLE summary card.

## Historical archive surface calibration

- The historical summary card keeps the cyan archive-mode tint introduced in v3.0.3.
- The pre-blended cyan contribution is reduced from roughly 6% to roughly 4% over the normal dark status surface.
- The new `archiveSurface` COLORREF is `0x001b1b0e` (`0x00BBGGRR`).
- `ARCHIVANSICHT • NICHT LIVE`, the cyan historical tab, `HISTORISCHER SYSTEMSTATUS`, `DAUER`, `MESSUNG ABGESCHLOSSEN`, and `13 / 13 Prüfgruppen` remain unchanged.
- The heart/status icon remains unchanged and receives no archive/clock badge.
- Green/yellow/red stored health-result colors remain unchanged.
- Historical session-only lifecycle behavior remains unchanged from v3.0.2/v3.0.3.

## Unchanged platform contracts

- App version: 3.0.4
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

`tools/validate_v304_archive_surface_tint.py`

Canonical v3.0.3 must fail the exact v3.0.4 surface/version contract (RED); v3.0.4 must pass it (GREEN). All prior historical/session, manifest-authority, diagnostic/repair, Setup, Healthcheck, PE and static UI/reference gates remain build-gated.
