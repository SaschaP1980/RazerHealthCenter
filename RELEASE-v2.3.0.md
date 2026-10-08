# Release v2.3.0

v2.3.0 changes Setup connection state from saved-snapshot presentation to an
event-driven live model and reuses the same fast infrastructure for guided
wired/wireless learning.

Changes:
- App version advances to 2.3.0 under the project-specific Major-version rule.
- Health Engine remains 1.4.2; Repair Engine remains 1.0.0.
- Setup Scanner advances to 1.0.6.
- New Fast Setup Live Probe 1.0.0.
- Device Inventory schema remains 2.
- Connection History remains schema 2 at
  `Setup/RazerConnectionHistory-v2.json`.
- Runtime locale remains de-DE and expands to 321 UI keys.
- Loaded inventory presence is explicitly stale until a current-session live
  refresh succeeds. Historical `presentAtScan=true` cannot itself make a PID
  Acid Green after app start.
- On startup with a valid inventory, a fast present-only probe automatically
  checks the already-known PIDs and verifies present connections against current
  root `BusReportedDeviceDesc` / `productKey` evidence.
- The known-PID live path avoids Registry history, DriverStore and INF traversal.
- `RegisterDeviceNotificationW` subscribes the Win32 window to device-interface
  changes. Arrival/removal/node-change events schedule a debounced fast refresh;
  the Windows event is a trigger, never identity or role evidence.
- PnP event bursts preserve a follow-up verification so an early probe while PnP
  is settling cannot strand the UI or learning assistant on a transient state.
- Probe-level errors fail closed; an incomplete probe does not publish a false
  live snapshot.
- Old inventories without `deviceClass` can recover mouse/keyboard presentation
  conservatively from stored MI_00 / `mouhid` / `kbdhid` PnP evidence without
  modifying the persisted file and without PID/model mappings.
- `Verbindungen einlernen` now captures a fast product-specific baseline, waits
  for a Windows device-change event, then performs a target-product delta probe.
- The guided target probe can discover a currently present connection PID not yet
  known to the inventory, but only when current root identity verifies to the
  selected `productKey`.
- Wired learning accepts exactly one unambiguous newly appeared verified PID.
  Wireless learning excludes the already-known HIGH wired PID and accepts
  exactly one remaining verified target connection.
- Unrelated device events are ignored. Ambiguity, weak/missing identity and
  explicit descriptor-role conflict remain fail-closed.
- Successful guided roles remain HIGH with
  `user-guided-wired-transition` / `user-guided-wireless-transition`.
- After a guided sequence, one normal full Setup scan materializes newly learned
  connection/capability metadata. The interactive steps themselves use the fast
  path.
- Normal full Setup scanning remains responsible for new product discovery and
  comprehensive PnP/Registry/DriverStore/capability inventory.

Native status:
- The v2.2.5 guided role-learning workflow was field-tested successfully on the
  user's Viper V3 Pro and BlackWidow V4 Low-profile HyperSpeed.
- v2.3.0's Windows device-notification and live-probe runtime behavior is built,
  statically/cross-build validated and still requires native Windows acceptance.
