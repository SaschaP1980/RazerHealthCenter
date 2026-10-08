# Canonical reference source v2.3.2

This source tree is the canonical development reference for v2.3.2 after static,
package and clean-rebuild validation.

Core versions:
- App: 2.3.2
- Health Engine: 1.4.3
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.0.1
- Device Inventory schema: 2
- Connection History schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4
- i18n: de-DE, 328 keys

Live-presence presentation contract:
- persisted `presentAtScan` is historical until a successful current-session
  refresh;
- starting a new live refresh marks the previous state stale immediately;
- known-PID refresh values remain visible but muted while the probe runs;
- each product row overlays an indeterminate Acid-Green progress bar in the
  `VERBINDUNGS-PIDs` cell during that refresh;
- a successfully verified present connection renders both PID and role label in
  Acid Green; inactive known paths remain muted.

Gate 4 presentation contract:
- the Health Engine 1.4.3 output is unchanged;
- raw details and clipboard copy continue to use the original structured engine
  evidence unchanged;
- only the normal Gate 4 finding presentation may enrich a physical-node finding
  using Setup product name, learned connection role and a current live-presence
  result;
- when one path is inactive while another verified path of the same product is
  live, the INFO finding explains the expected alternative connection instead of
  displaying only `0 present`.

Detail-scroll contract:
- the normal and raw detail documents both include bottom scroll reserve;
- at maximum scroll the final line must be fully visible above the fixed action
  buttons.

Protocol contract:
- the visible range counter remains;
- the explanatory `Mausrad zum Scrollen` suffix is removed;
- scrolling behavior is unchanged.

Identity/PID contract remains unchanged from v2.3.1:
- no endpoint PID constant assigns product identity, device class or connection
  role in active production logic;
- product identity prefers root `DEVPKEY_Device_BusReportedDeviceDesc`;
- PIDs are runtime observations only;
- `ContainerId` remains supporting evidence, not a product merge key.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
