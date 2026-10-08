# Reference Source – v3.0.4

This directory is the complete canonical source snapshot for **Razer Synapse + Chroma Health Center v3.0.4**.

Reference baseline: v3.0.3 archive-header simplification plus a single visual calibration of the historical summary surface from roughly 6% to roughly 4% cyan contribution.

Key source contracts:

- `model.go`: app/reference version 3.0.4; Health Engine remains 1.4.6.
- `ui.go`: historical archive semantics from v3.0.3 remain unchanged. `archiveSurface` is the pre-blended COLORREF `0x001b1b0e`, approximately 4% cyan over the normal dark status surface. The heart/status icon and stored green/yellow/red result colors remain unchanged.
- `ui_state.go`: historical measurement/tab state, log-table selection and log scroll remain process-session only and are not persisted across restart.
- `history_export.go`: current-session historical tab state survives normal list refreshes when the referenced detail-capable measurement still exists.
- `locales/de-DE.json`: v3.0.4 catalog; presentation copy is unchanged from v3.0.3 apart from catalog metadata.
- `tools/validate_v304_archive_surface_tint.py`: v3.0.4 RED/GREEN regression for the exact 4% archive-surface design token.
- `tools/validate_v303_archive_header_polish.py`: prior archive-header presentation semantics remain build-gated.
- `tools/validate_v302_historical_session_archive.py`: prior session-only lifecycle contract remains build-gated.
- `versioncheck.go`: VersionStatus schema 4 and official Razer prod-manifest informational update semantics remain unchanged.
- `problem.go` / `repair.go` / `SAFETY-MODEL.txt`: diagnostic/problem/repair architecture and explicit-confirmation safety rules remain unchanged.

Historical source and validation files remain for audit/history but are not the v3.0.4 runtime payload unless selected by the current runtime source.

Build with:

```bash
./build.sh <output-directory>
```

The Windows amd64 GUI release executable is `RazerHealthCenter.exe`.
