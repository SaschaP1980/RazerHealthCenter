# Canonical reference source v2.2.6

This source tree is the canonical development reference for v2.2.6 after static,
package and clean-rebuild validation.

Core versions:
- App: 2.2.6
- Health Engine: 1.4.2
- Setup Scanner: 1.0.5
- Device Inventory schema: 2
- Connection History schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4
- i18n: de-DE, 312 keys

Device identity / role contract:
- Active Health and Setup production logic contains no endpoint PID constants
  assigning product identity, product class or wired/wireless role.
- Present endpoint PIDs are discovered generically from Razer VID 1532 PnP/CIM,
  registry and DriverStore evidence.
- Product identity prefers root USB `DEVPKEY_Device_BusReportedDeviceDesc`.
- Multiple observed PIDs with the same normalized bus identity are one product.
- `ContainerId` is supporting evidence only, not a product merge key.
- Observed PIDs may be persisted as runtime data/fingerprint keys; they do not
  carry compile-time semantics.
- Connection roles may be HIGH from explicit current descriptor evidence or the
  user-guided calibration workflow.
- Guided calibration remains product-scoped, baseline-driven and fail-closed on
  ambiguity/conflict.
- Persistent learning file: `Setup/RazerConnectionHistory-v2.json`.
- Setup Scanner 1.0.5 keeps the root-only product-identity property-query model.

Setup presentation contract added in v2.2.6:
- `presentAtScan=true` is the sole source for Acid-Green connection-PID presence
  highlighting. Historical/known-but-absent paths are visually muted.
- The ready summary reports product count, currently present connection count
  and total known connection count as distinct values.
- Normal Setup scan progress is an indeterminate Acid-Green bar centered inside
  the inventory table at 70% table width; the table is alpha-dimmed during the
  scan.
- Generic product-class presentation is derived from current PnP class evidence,
  not from PID/model constants. Primary physical HID `MI_00` Mouse/Keyboard
  evidence is preferred; ambiguous evidence becomes `device`.
- Mouse/keyboard/generic-device glyphs are vector-drawn by the Win32 UI; no new
  asset files are required.
- The same class glyph is used in the inventory list and guided learning dialog.

Health Engine 1.4.2 remains capability-driven and byte-identical to v2.2.5.
Repair Engine 1.0.0 and the PE resource payload also remain byte-identical.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
