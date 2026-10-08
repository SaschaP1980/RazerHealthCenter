# Release v2.3.9

- App: 2.3.9
- Health Engine: 1.4.5 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 342 UI keys

## SETUP connection presentation

The `VERBINDUNGS-PIDs` column is now role-first whenever the connection role is
known with medium/high confidence. The visible form is `Typ · PID`, for example
`USB-Kabel · 00C0` or `Wireless-Dongle · 00C1`.

Within one product row, connections are sorted deterministically by presentation
role: `USB-Kabel` first, then `Wireless-Dongle`, then unknown/generic entries.
Entries with the same role class are ordered by PID. Unknown/untyped entries
remain PID-only rather than receiving a guessed label.

The complete live-present entry remains Acid Green; known but currently absent
entries remain muted. The live-refresh sweep and its hidden-text behavior are
unchanged.

This is a presentation-only change. Product identity, connection-role learning,
PID/history persistence, native SetupAPI presence detection, per-product
Healthcheck participation and Health Engine 1.4.5 semantics are unchanged.

## Regression contract

`tools/validate_connection_presentation_v239.py` is part of `build.sh`.
Against the exact canonical v2.3.8 source it is RED (0/10); against v2.3.9 it is
GREEN (10/10). The contract covers role-first formatting, deterministic role
sorting, unknown-last behavior, PID tie-breaks and unchanged live Acid-Green
rendering of the whole typed entry.
