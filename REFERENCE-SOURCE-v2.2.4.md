# Canonical reference source v2.2.4

This source tree is the canonical development reference for v2.2.4 after final
release validation.

Core versions:
- App: 2.2.4
- Health Engine: 1.4.2
- Setup Scanner: 1.0.3
- Device Inventory schema: 2
- Connection History schema: 1
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4

Device identity/role contract:
- Active Health and Setup production logic contains no endpoint PID constants
  assigning product identity or wired/wireless role.
- Present endpoint PIDs are discovered generically from Razer VID 1532 PnP/CIM,
  registry and DriverStore evidence.
- Product identity prefers root USB `DEVPKEY_Device_BusReportedDeviceDesc`.
- Multiple observed PIDs with the same normalized bus identity are one product.
- Observed PIDs may be persisted as runtime data/fingerprint keys; they do not
  carry compile-time semantics.
- Connection role is evidence/confidence based: explicit transport text, then
  conservative paired HID-topology evidence, then persistent transition
  confirmation. Conflicting or insufficient evidence remains generic.
- Persistent learning file: `Setup/RazerConnectionHistory-v1.json`.
- Setup Scanner 1.0.3 uses root-only device-property queries for identity and
  computes topology from the existing PnP enumeration to keep scan cost bounded.

Health Engine 1.4.2 remains capability-driven and unchanged. The v2.2.3
PRIMARY/RUNTIME/SUPPORTING AppEngine evidence architecture also remains
unchanged.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
