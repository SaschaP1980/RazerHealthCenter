# UI / diagnostics recovery revision r6 — Golden detail/progress/export parity

Recovery r6 is based on the natively tested r5 source and incorporates the next
Golden-v1.7.0 findings from direct video, screenshot, and diagnostic-package
comparison.

## UI parity changes

- Info heart: separate 96x96 native icon handle from the Golden-identical
  `app-heart.ico`, rendered at 88x88. The 48x48 header handle is no longer
  upscaled for the Info view.
- Live progress text: Golden semantics restored. During a run the line below the
  progress bar reports the number of not-yet-finalized groups, e.g.
  `Aktuell: 13 Prüfgruppen parallel`, `11 Prüfgruppen parallel`, ... . This does
  not change the engine's real worker limit (4); it is a UI status convention.
- Gate detail panel: continuous state-colored left accent (Acid Green for PASS,
  yellow for HINWEIS, orange for UNKLAR, inferred red for FEHLER/FAILED).
- Gate detail close X: Acid-Green hover state restored.
- Gate detail content is hard-clipped above the bottom button bar.
- Raw details mode now follows Golden: summary and assessment disappear and the
  full middle viewport becomes the scrollable raw finding area. Each finding
  exposes actual value, `Soll:`, `Detail:`, and `Bereich:` lines.
- Raw toggle text is `Rohdetails aus` while raw mode is active.

## Diagnostic / history parity changes

- `EngineOutput-*` is again a Golden-style wrapper containing ToolVersion,
  Started, Duration, ExitCode, RunError, Command, STDOUT and STDERR. History
  duration can therefore be reconstructed from the canonical Duration line.
- Progress files use the Golden `GateProgress-*` name.
- Diagnostic export manifest is schema 4 and named `ExportManifest.json`.
- Current-session packages use Golden directory roles:
  `AppSession/Logs`, `AppSession/Diagnostics`, `LastMeasurement/Logs`, and
  `LastMeasurement/Diagnostics`.
- App-session export includes AppDebug, StartupDebug and UITrace when present.
- A StartupDebug snapshot and persistent UITrace heartbeat log are created for
  the current app session.
- AppDebug logging was expanded with startup/thread, runtime hash, progress,
  engine, tray and export lifecycle information.

## Invariants

The Health Engine 1.3.5 and all Golden-recovered embedded payloads remain
unchanged. The monitor remains read-only with respect to Razer and Windows
configuration. No driver/service/registry/PnP mutation path was added.
