# Release v2.3.3

v2.3.3 is a focused Setup live-refresh presentation correction on top of v2.3.2.
The event-driven live probe, identity verification, guided learning and Health
semantics are unchanged.

Changes:
- App version advances to 2.3.3.
- Health Engine remains 1.4.3 byte-identical.
- Setup Scanner remains 1.0.6 byte-identical.
- Fast Setup Live Probe remains 1.0.1 byte-identical.
- Repair Engine remains 1.0.0 byte-identical.
- The per-product Acid-Green live-refresh indicator in the
  `VERBINDUNGS-PIDs` column is now a true overlay in the same vertical text band
  as the PID/role string. It no longer renders as a second line underneath the
  connection text and therefore adds no visual row height.
- While refreshing, PID/role text remains visible in its muted stale-state color
  beneath the overlay. After the probe succeeds, the overlay disappears and the
  verified live PID plus role label use the normal Acid-Green presence styling.
- All Gate 4 context wording, detail bottom-scroll reserve and protocol-header
  cleanup introduced in v2.3.2 remain unchanged.
- de-DE catalog remains at 328 keys; no user-facing string changes were needed.

Safety / semantic contract:
- no endpoint PID or model constant assigns product identity, device class or
  connection role;
- Windows device events remain triggers only;
- live presence still requires current root identity verification against the
  stored productKey;
- guided Wired/Wireless learning remains fail-closed;
- this release changes only the rendering geometry of the refresh indicator.

Native acceptance focus:
- during startup and WM_DEVICECHANGE refreshes, verify the moving Acid-Green
  indicator passes directly through the PID/role text band rather than below it;
- verify row height and table layout do not shift while refreshing;
- verify the overlay disappears completely after refresh completion and the
  final live PID/role coloring remains correct.
