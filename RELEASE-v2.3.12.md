# Release v2.3.12

- App: 2.3.12
- Health Engine: 1.4.5 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 348 UI keys

## Rounded Synapse-style tray menu

The tray icon context menu keeps the Synapse dark styling from v2.3.11 but no
longer uses the visible white Windows popup outline. Instead, the menu now opens
inside its own custom dark popup window with rounded corners so it visually fits
much better next to the native Synapse tray menus.

What stays the same:

- branded header row with app icon and `RAZER SYNAPSE + CHROMA` /
  `HEALTH MONITOR`;
- Acid-Green hover accent strip and branded command icons;
- direct `Fenster anzeigen` action;
- the existing enabled / disabled logic for `Systemprüfung starten`,
  `Ergebnis öffnen`, `Protokolle anzeigen`, `Diagnose exportieren` and
  `Beenden`.

What changes internally:

- the old owner-drawn `TrackPopupMenu` path is replaced by a dedicated popup
  window class for the tray menu;
- the popup uses a rounded window region and paints its own background, rows,
  separators and hover states;
- the popup closes on focus loss, right click re-toggle and `ESC`.

## Regression contract

`tools/validate_tray_menu_v2312.py` is part of `build.sh`. It verifies the new
custom tray-menu popup class, rounded-window path, branded header, green hover
accent, direct `Fenster anzeigen` action and close semantics.
