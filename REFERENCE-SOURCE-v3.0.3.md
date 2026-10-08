# Reference Source – v3.0.3

This directory is the complete canonical source snapshot for **Razer Synapse + Chroma Health Center v3.0.3**.

Reference baseline: v3.0.2 session-only historical lifecycle plus the v3.0.3 archive-header simplification and cyan surface polish.

Key source contracts:

- `model.go`: app/reference version 3.0.3; Health Engine remains 1.4.6.
- `ui_state.go`: historical measurement/tab state, log-table selection and log scroll remain process-session only and are not persisted across restart.
- `history_export.go`: current-session historical tab state survives normal list refreshes when the referenced detail-capable measurement still exists.
- `ui.go`: active historical mode keeps cyan tab/tagline context, removes duplicate timestamp/archive-description rows, renders `HISTORISCHER SYSTEMSTATUS` in cyan, uses `DAUER`, static `MESSUNG ABGESCHLOSSEN` + `13 / 13 Prüfgruppen`, and applies a very subtle cyan-tinted archive summary surface. The cyan separator line is removed. Stored health-result colors and the heart/status icon remain unchanged.
- `locales/de-DE.json`: v3.0.3 catalog with 375 presentation keys. Redundant archive-title/subtitle keys are removed; historical duration/gate-count keys are added.
- `tools/validate_v303_archive_header_polish.py`: v3.0.3 RED/GREEN regression for the simplified archive summary card.
- `tools/validate_v302_historical_session_archive.py`: prior session-only lifecycle contract remains build-gated.
- `versioncheck.go`: VersionStatus schema 4 and official Razer prod-manifest informational update semantics remain unchanged.
- `problem.go` / `repair.go` / `SAFETY-MODEL.txt`: diagnostic/problem/repair architecture and explicit-confirmation safety rules remain unchanged.

Historical source and validation files remain for audit/history but are not the v3.0.3 runtime payload unless selected by the current runtime source.

Build with:

```bash
./build.sh <output-directory>
```

The Windows amd64 GUI release executable is `RazerHealthCenter.exe`.
