# Reference Source – v3.0.2

This directory is the complete canonical source snapshot for **Razer Synapse +
Chroma Health Center v3.0.2**.

Reference baseline: v3.0.1 authoritative Razer-manifest/version-evidence model
plus the v3.0.2 historical-session/archive-mode correction.

Key source contracts:

- `model.go`: app/reference version 3.0.2; Health Engine remains 1.4.6.
- `ui_state.go`: historical measurement/tab state, log-table selection and log
  scroll initialize fresh on process start and are not persisted to disk.
- `history_export.go`: current-session historical tab state survives normal list
  refreshes when the referenced detail-capable measurement still exists.
- `ui.go`: active historical mode uses cyan archive framing, a dedicated archive
  header and static completion information; no historical LIVE progress bar;
  stored health-result colors and the heart/status icon remain unchanged.
- `locales/de-DE.json`: v3.0.2 catalog with 375 presentation keys.
- `tools/validate_v302_historical_session_archive.py`: v3.0.2 RED/GREEN
  regression for session-only lifecycle and archive-mode presentation.
- `versioncheck.go`: VersionStatus schema 4 and official Razer prod-manifest
  informational update semantics from v3.0.1 remain unchanged.
- `problem.go` / `repair.go` / `SAFETY-MODEL.txt`: diagnostic/problem/repair
  architecture and explicit-confirmation safety rules remain unchanged.

Historical source and validation files remain for audit/history but are not the
v3.0.2 runtime payload unless selected by the current runtime source.

Build with:

```bash
./build.sh <output-directory>
```

The Windows amd64 GUI release executable is `RazerHealthCenter.exe`.
