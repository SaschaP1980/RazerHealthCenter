# Release v2.2.4

v2.2.4 removes the remaining endpoint-PID role hardcoding from the active Setup
Scanner and replaces it with generic product identity plus conservative role
learning.

Changes:
- App version 2.2.4; Health Engine remains 1.4.2; Repair Engine remains 1.0.0.
- Setup Scanner advances to 1.0.3.
- The active Setup Scanner contains no endpoint PID constants for product
  identity or connection-role assignment.
- Product identity prefers the physical USB root's
  `DEVPKEY_Device_BusReportedDeviceDesc`. Connections with the same normalized
  current bus identity are grouped into one product even when they use different
  observed PIDs/ContainerIds.
- Identity probing is production-optimized: one root-only
  `Get-PnpDeviceProperty` call per present PID, not the experimental deep
  per-interface property sweep.
- The old `VerifiedConnectionTypes` map and its four-state PID evidence marker
  are removed from active production code.
- Connection roles now carry provenance and confidence.
  - explicit dongle/receiver or wired/cable descriptor wording => HIGH;
  - paired HID-collection topology asymmetry => MEDIUM;
  - a later one-path/two-path transition of the same learned pair can promote
    the evidence to HIGH;
  - conflicts/insufficient evidence remain generic `usb-device`.
- `Setup/RazerConnectionHistory-v1.json` persistently stores observed
  connection identity, role evidence, topology and the previous product/presence
  snapshot. Observed PIDs are stored only as data keys/fingerprints.
- The Setup UI labels `Wireless-Dongle` / `USB-Kabel` only for medium/high role
  confidence, independent of any fixed PID source marker.
- The connection-history file is included in diagnostic exports.
- Device Inventory schema remains 2; the new identity/role/topology fields are
  backward-compatible enrichments. Health consumes the same capability contract.

Native evidence leading to this change:
- Viper wired and wireless paths independently exposed the same bus-reported
  product description and were therefore generically clusterable.
- BlackWidow wired and wireless paths independently exposed the same bus-reported
  product description and were likewise generically clusterable.
- Both tested paired products showed a stable additional-HID-collection
  asymmetry on the receiver path; this is deliberately treated as heuristic
  evidence rather than a product/PID rule.

The v2.2.3 AppEngine evidence-role fix remains unchanged.
