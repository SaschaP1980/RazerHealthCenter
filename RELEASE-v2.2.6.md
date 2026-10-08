# Release v2.2.6

v2.2.6 refines the Setup user experience while preserving the PID-free product
identity and guided wired/wireless learning architecture validated in v2.2.5.

Changes:
- App version advances to 2.2.6.
- Health Engine remains 1.4.2; Repair Engine remains 1.0.0.
- Setup Scanner advances to 1.0.5.
- Device Inventory schema remains 2.
- Connection History remains schema 2 at
  `Setup/RazerConnectionHistory-v2.json`.
- Normal Setup-scan progress is no longer rendered as the cyan strip in the
  profile card. The current inventory table stays visible but is alpha-dimmed,
  while a centered indeterminate Acid-Green progress bar spans 70% of the
  `Erkanntes Razer-Setup` table width.
- The normal scan detail is simplified to the user-facing text:
  `Razer-Geräte und deren bekannte Verbindungswege werden inventarisiert.`
- The ready summary now distinguishes the number of currently present
  connection paths from all known connection paths.
- In the connection-PID column, `presentAtScan=true` PIDs are rendered in Acid
  Green. Known but currently absent paths are muted. Learned role labels remain
  visible.
- Setup Scanner 1.0.5 derives an optional generic `deviceClass` from current PnP
  evidence. It prefers the primary physical HID `MI_00` interface and supports
  only `mouse`, `keyboard` or conservative fallback `device`.
- Device-class detection contains no endpoint-PID or product/model-name mapping.
  Composite devices exposing conflicting primary evidence fall back to the
  generic device class rather than being guessed.
- The Setup inventory table shows a compact mouse/keyboard/generic-device glyph
  before each product name.
- The same device-class glyph is shown in the guided `Verbindungen einlernen`
  dialog.
- The indeterminate progress accent inside guided learning is Acid Green for
  visual consistency.
- Guided wired/wireless role learning, ambiguity handling, skip behavior and
  persistent schema-2 calibration semantics remain unchanged.

Native status:
- The v2.2.5 guided role-learning workflow was successfully exercised on the
  user's Viper V3 Pro and BlackWidow V4 Low-profile HyperSpeed before this
  release.
- Native Windows acceptance of the new v2.2.6 presence coloring, centered scan
  overlay and generic device-class glyphs remains pending after installation of
  this build.
