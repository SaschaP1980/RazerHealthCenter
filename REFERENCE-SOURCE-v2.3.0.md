# Canonical reference source v2.3.0

This source tree is the canonical development reference for v2.3.0 after static,
package and clean-rebuild validation.

Core versions:
- App: 2.3.0
- Health Engine: 1.4.2
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.0.0
- Device Inventory schema: 2
- Connection History schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4
- i18n: de-DE, 321 keys

Identity / PID contract:
- Active production logic contains no endpoint PID constants assigning product
  identity, device class or wired/wireless role.
- Product identity prefers current USB-root
  `DEVPKEY_Device_BusReportedDeviceDesc`.
- Multiple observed connection PIDs with the same normalized reliable bus
  identity represent one product.
- `ContainerId` is supporting connection evidence only, not a product merge key.
- PIDs may persist as runtime inventory/history observations, never compile-time
  semantics.

Live presence contract added in v2.3.0:
- Persisted `presentAtScan` is historical until a successful current-session
  refresh.
- Acid Green means current verified presence only when `setupLiveFresh=true`.
- Startup runs one fast known-PID probe automatically when a valid inventory is
  available.
- Known-PID live refresh is `Get-PnpDevice -PresentOnly`, probes only known PIDs,
  avoids Registry/DriverStore/INF history, and verifies product identity before
  publishing presence.
- Any live-probe internal error invalidates that refresh rather than converting
  uncertainty into absence.
- Win32 `RegisterDeviceNotificationW` / `WM_DEVICECHANGE` arrival/removal/node
  events schedule a debounced refresh; event bursts can queue one follow-up.
- Device-change events are triggers only and are never semantic evidence.
- Full Setup Scanner 1.0.6 remains authoritative for discovery of new products
  and complete capability inventory.

Guided calibration contract added in v2.3.0:
- Per-step full Setup scans are replaced by a fast target-product state machine:
  prepare baseline -> wait for device event -> verify target delta.
- Target-product probes may observe a previously unknown PID, but current root
  identity must verify it to the selected `productKey`.
- Wired requires exactly one new verified PID relative to baseline.
- Wireless excludes known HIGH wired PIDs and requires exactly one remaining
  verified target connection.
- Unchanged selected-product state means an unrelated event and is ignored.
- Ambiguous delta, weak identity or explicit role conflict does not write history.
- Successful guided roles remain HIGH and use user-guided transition sources.
- Skip remains non-semantic: skipped does not mean unsupported.
- One normal full scan after the guided sequence materializes new PID/capability
  metadata.

Legacy device-class presentation:
- Existing persisted `deviceClass` is preferred.
- Older inventories lacking it may recover mouse/keyboard display class from
  stored MI_00 `mouhid` / `kbdhid` evidence.
- Conflicting evidence falls back to generic `device`.
- The fallback is presentation-only and does not silently rewrite old inventory.

Health Engine 1.4.2 remains capability-driven and unchanged. Repair Engine 1.0.0
remains unchanged. The PE resource payload and existing icon assets are intended
to remain byte-identical to v2.2.6.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
