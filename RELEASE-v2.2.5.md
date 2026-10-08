# Release v2.2.5

v2.2.5 replaces incidental connection-role learning with a controlled,
user-guided calibration workflow while preserving the PID-free product identity
architecture introduced in v2.2.4.

Changes:
- App version advances to 2.2.5.
- Health Engine remains 1.4.2; Repair Engine remains 1.0.0.
- Setup Scanner advances to 1.0.4.
- Device Inventory schema remains 2.
- Connection History advances to schema 2 and file
  `Setup/RazerConnectionHistory-v2.json`.
- A legacy `RazerConnectionHistory-v1.json` can be read as migration input.
- The Setup page adds `Verbindungen einlernen` after a valid inventory exists.
- Each detected product is calibrated separately with a guided wired step and a
  guided wireless step; either step may be skipped without marking the transport
  unsupported.
- Each guided scan receives a copy of the pre-step inventory as its baseline and
  is scoped to one exact `productKey`.
- Unambiguous controlled transitions/reference states persist HIGH-confidence
  sources:
  - `user-guided-wired-transition`
  - `user-guided-wired-reference`
  - `user-guided-wireless-transition`
  - `user-guided-wireless-reference`
- Ambiguous target state, missing target, missing baseline or explicit current
  descriptor conflict fails closed. No new role is learned and failed guided
  runs do not advance connection history.
- Passive `topology-hid-collection-asymmetry` and
  `topology-transition-confirmed` role assignment is removed from production.
  HID/USB topology metrics remain diagnostic data only.
- Explicit current descriptor wording remains valid HIGH-confidence evidence.
- Schema 2 stores whether a historical role is calibrated and when it was
  calibrated. Old passive schema-1 role evidence is not reused as ground truth.
- Runtime role reuse remains protected by matching current product identity / `productKey`.
- No endpoint PID or tested product model is compiled into active product/role
  semantics.

This release intentionally requires native Windows acceptance testing of the new
wizard with the actual Viper V3 Pro and BlackWidow V4 Low-profile HyperSpeed
connection states before the guided assignments are considered field-validated.
