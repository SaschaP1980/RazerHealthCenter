# Release v2.3.7

- App: 2.3.7
- Health Engine: 1.4.4
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 338 UI keys

## Per-product Healthcheck participation

- The SETUP table column is now `HEALTHCHECK`.
- Clicking a product row toggles `AKTIV` / `DEAKTIVIERT` for the next Healthcheck.
- Active device glyph/status are Acid Green; inactive glyph/status are muted grey.
- Live connection PID/role colors remain independent from Healthcheck selection.
- The selection is persisted per product in the schema-2 inventory and survives
  restart. A later Setup scan preserves choices for recognized products; newly
  discovered products default active.
- Any toggle immediately invalidates the current dashboard result to UNGEPRÜFT;
  historical measurement logs remain intact.
- If all products are disabled, neither a Setup scan nor Healthcheck starts; an
  app-native dark modal requires at least one active product.

## Health Engine 1.4.4

Product-specific checks consume only products with `required=true` and the
connections attached to those products. Inventory-global `logicalProductIds` are
not gate-determining during partial product selection because schema 2 cannot
reliably attribute them to individual productKeys. No endpoint PID/model rules
were added.

## Guided Learning / UI

- New `Gerät überspringen` skips all remaining interactive learning steps for the
  current product and advances to the next product without rolling back roles
  already learned in the session.
- Existing `Überspringen` remains a current-step skip.
- The bottom SETUP card subtitles are shortened to
  `Razer-Produkte neu inventarisieren` and
  `Wired/Wireless eindeutig zuordnen`.
