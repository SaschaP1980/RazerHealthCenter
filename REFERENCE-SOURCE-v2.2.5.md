# Canonical reference source v2.2.5

This source tree is the canonical development reference for v2.2.5 after final
release validation.

Core versions:
- App: 2.2.5
- Health Engine: 1.4.2
- Setup Scanner: 1.0.4
- Device Inventory schema: 2
- Connection History schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4
- i18n: de-DE, 312 keys

Device identity/role contract:
- Active Health and Setup production logic contains no endpoint PID constants
  assigning product identity or wired/wireless role.
- Present endpoint PIDs are discovered generically from Razer VID 1532 PnP/CIM,
  registry and DriverStore evidence.
- Product identity prefers root USB `DEVPKEY_Device_BusReportedDeviceDesc`.
- Multiple observed PIDs with the same normalized bus identity are one product.
- `ContainerId` is supporting evidence only, not a product merge key.
- Observed PIDs may be persisted as runtime data/fingerprint keys; they do not
  carry compile-time semantics.
- Passive HID-asymmetry and incidental one-path/two-path role learning from
  v2.2.4 is disabled as semantic evidence.
- Connection roles may be HIGH from explicit current descriptor evidence or
  from the user-guided calibration workflow.
- Guided calibration is product-scoped, baseline-driven and fails closed on
  ambiguity/conflict; no failed guided scan writes new role history.
- Persistent learning file: `Setup/RazerConnectionHistory-v2.json`.
- Schema 2 stores `calibrated` / `calibratedAt`; schema 1 is accepted only as
  migration input and old passive topology roles are not trusted as calibrated.
- Setup Scanner 1.0.4 keeps the root-only property-query performance model.

Health Engine 1.4.2 remains capability-driven and unchanged. The v2.2.3
PRIMARY/RUNTIME/SUPPORTING AppEngine evidence architecture also remains
unchanged.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
