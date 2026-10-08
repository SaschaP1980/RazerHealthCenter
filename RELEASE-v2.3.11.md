# Release v2.3.11

- App: 2.3.11
- Health Engine: 1.4.5 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 348 UI keys

## Synapse-style tray menu

The tray icon context menu now uses a custom owner-drawn presentation instead of
the default Windows popup style. It keeps the same product palette as the main
application and is designed to feel consistent with Synapse:

- branded dark header row with app icon and `RAZER SYNAPSE + CHROMA` /
  `HEALTH MONITOR`;
- Acid-Green hover accent strip and dark hover background for selectable rows;
- custom-drawn separators and muted disabled entries;
- branded icon / glyph rendering per command;
- new direct action `Fenster anzeigen`.

Existing tray actions `Systemprüfung starten`, `Ergebnis öffnen`,
`Protokolle anzeigen`, `Diagnose exportieren` and `Beenden` retain their prior
behavior and gating rules.

## Regression contract

`tools/validate_tray_menu_v2311.py` is part of `build.sh`. It is RED on the exact
canonical v2.3.10 source and GREEN on v2.3.11. The contract covers owner-draw menu
constants, measure/draw handling, branded header row, custom separator, green hover
accent, return-command popup flow and the new `Fenster anzeigen` action.
