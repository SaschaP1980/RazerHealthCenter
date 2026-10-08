# Recovery r8 / Release Candidate 2

Date: 2026-09-09

RC2 is a focused follow-up to RC1. Health Engine 1.3.5, Gate semantics, read-only
invariants, Golden resource payloads, history/export schema and the RC1 visual baseline
are intentionally unchanged.

## RC2 Gate-detail changes

- The scroll viewport now contains the full middle document: `ZUSAMMENFASSUNG`,
  `BEWERTUNG` and `BEFUNDE`. The header (`PRÜFDETAILS`, Gate name, status badge, X)
  and the footer button bar stay fixed.
- Compact and raw detail modes both use continuous pixel scrolling.
- The vertical scrollbar thumb is mouse-draggable. Mouse capture is acquired on
  `WM_LBUTTONDOWN`, thumb position is mapped to the content offset, and capture is
  released on `WM_LBUTTONUP`.
- Dragging is live: every relevant `WM_MOUSEMOVE` updates the content offset and
  forces an immediate repaint; mouse-up only ends the drag state.
- Track clicks center the thumb under the pointer and immediately enter drag mode.
- The close X is larger and positioned further toward the upper-right corner, while
  preserving the Acid Green hover treatment and a generous hit target.
- ESC closes an open Gate-detail panel.

## Preserved invariants

- Health Engine 1.3.5 remains byte-identical to the Golden recovered payload.
- No Razer/Windows service, registry, driver or PnP mutation paths are added.
- Double-buffered GDI rendering and TrackMouseEvent anti-flicker behavior remain.
- RC1 Protocol overall-status wording and vector action icons remain unchanged.
- FAILED/FEHLER left accent remains red as a documented Golden-inferred mapping.
