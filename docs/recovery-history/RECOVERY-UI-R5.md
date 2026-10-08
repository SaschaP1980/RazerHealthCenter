# UI Recovery revision r5 — Golden interaction/scale parity pass

Recovery r5 is based on the natively tested r4 Golden-UI reconstruction and the
follow-up before/after videos supplied on 2026-09-09.

This revision targets the remaining visible interaction differences without
changing the Health Engine or the read-only diagnostic model.

## Scale corrections

Compared with r4, the Golden references use visibly larger navigation symbols,
action symbols and small UI typography. r5 therefore increases the relevant
Segoe UI sizes selectively rather than scaling the entire layout:

- sidebar icons: 24 -> 28 px
- sidebar labels: 7 -> 8 pt, semibold
- body/body-semibold: 9 -> 10 pt
- small labels: 8 -> 9 pt
- tiny/table/status labels: 7 -> 8 pt
- action titles: 10 -> 11 pt
- action glyphs: dedicated 20 pt `Segoe UI Symbol` font

The 1180 x 800 Golden client geometry and table/action-card rectangles remain
unchanged.

## Golden heartbeat animation

r4 used a forward-only status pulse (`0..7 -> 0`). r5 restores the Golden
ping-pong sequence:

`0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 6 -> 5 -> 4 -> 3 -> 2 -> 1 -> 0 ...`

The checking repaint timer is 125 ms so individual heartbeat frames are not
systematically skipped.

## Hover-state reconstruction

The Golden videos show different hover semantics for different control types.
r5 keeps these states separate:

- **Sidebar view switch:** inactive hover gets a dark-green surface, green icon
  and green text plus a subtle left accent; the active view retains the stronger
  active fill and bright 3 px accent.
- **Large action cards:** hover gets a visibly greener surface, 2 px neon-green
  border and green action symbol while preserving white title text.
- **Gate/history rows:** hover uses a restrained green-tinted row surface;
  selected rows remain stronger and retain the status-colored left strip.
- **Detail/modal buttons:** hover is intentionally subtler: green border/text and
  only a slight surface lift.

The modal suppresses hover feedback on the dimmed background.

## Paint invariants retained

The r4 anti-flicker path remains unchanged: complete offscreen rendering through
`CreateCompatibleDC` / `CreateCompatibleBitmap`, one final `BitBlt`,
`WM_ERASEBKGND` suppression and `TrackMouseEvent`/`WM_MOUSELEAVE` tracking.

Native Windows comparison against Golden v1.7.0 is still required for r5.
