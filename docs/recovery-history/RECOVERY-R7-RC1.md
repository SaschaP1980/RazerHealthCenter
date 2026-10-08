# Recovery r7 / Release Candidate 1 — 2026-09-09

This revision is the first **Release Candidate** of the recovered v1.7.0 source.
It is based on the natively exercised r6 build plus the final findings collected
from direct Golden-v1.7.0 / Recovery video and screenshot comparison.

## Gate detail fixes

- Raw detail rows are no longer fixed-height/single-line. `Ist`, `Soll`, `Detail`
  and `Bereich` are wrapped to the real viewport width and each finding gets a
  dynamically measured height.
- Raw mode now uses pixel scrolling and a proportional scrollbar, so long paths
  and descriptions can be fully read while the content remains clipped above
  the footer buttons.
- The close X is larger and has a larger hit target; Acid-Green hover remains.
- Every click inside the open Gate-detail panel is consumed by that panel. Only
  its explicit controls trigger actions; clicks can no longer select a Gate row
  behind the popover.
- The status-accent left border remains: PASS/healthy Acid Green, HINWEIS yellow,
  UNKLAR orange, FEHLER/FAILED inferred red.

## Protocol result semantics

Historical **measurement** results now use overall health terminology instead of
Gate terminology:

- `GESUND`
- `HINWEIS`
- `UNKLAR`
- `FEHLER`

The same overall label is used in the table and in `AUSGEWÄHLTE MESSUNG`.
`OverallLabel` from the engine result is preferred; machine values are only used
as fallback mapping.

## Action icons

- `Diagnose exportieren` and `Diagnosepaket erstellen` share a crisp GDI-vector
  tray/up-arrow icon rather than a font glyph.
- `Paketordner öffnen` uses a new folder + north-east/open-arrow icon. Its design
  is based on the user-approved generated concept stored under
  `design/package-folder-open-concept.png`, but the runtime rendering is vector
  GDI so it remains sharp at every DPI.

## Preserved invariants

- Health Engine 1.3.5 unchanged.
- Golden-recovered embedded runtime payloads unchanged.
- Read-only toward Razer/Windows state.
- Golden-compatible GDI double-buffering / no flicker path retained.
- Golden progress wording, Ping-Pong heart, schema-4 diagnostic export,
  StartupDebug/UITrace/AppDebug and Golden raw-detail semantics retained.

## Release status

RC1 is **not final/stable until native Windows acceptance passes**. The Golden
v1.7.0 executable remains the behavioral reference.
