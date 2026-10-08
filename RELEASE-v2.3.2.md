# Release v2.3.2

v2.3.2 refines the Setup live-presence presentation and Gate 4 detail UX on top
of the native-validated v2.3.1 live probe / WM_DEVICECHANGE architecture.

Changes:
- App version advances to 2.3.2.
- Health Engine remains 1.4.3 byte-identical.
- Setup Scanner remains 1.0.6 byte-identical.
- Fast Setup Live Probe remains 1.0.1 byte-identical.
- Repair Engine remains 1.0.0 byte-identical.
- During every fast known-PID refresh, persisted/current prior presence is marked
  stale until the probe completes; product PID cells are muted and show a
  per-product indeterminate Acid-Green progress bar inside the connection column.
- After a successful refresh, both the live PID and its learned role description
  (for example Wireless-Dongle or USB-Kabel) render in Acid Green. Known inactive
  connections remain neutral/muted.
- Gate 4 normal presentation enriches `physical nodes` findings with product name,
  learned connection role and current verified live alternative. Example: an
  inactive USB cable path can explicitly explain that the same product is
  currently connected via its Wireless-Dongle. Engine/raw/copy evidence is not
  rewritten.
- Gate-detail documents receive explicit bottom scroll reserve so the final text
  line remains fully readable above the fixed Rohdetails/Kopieren button row.
- The protocol range header no longer includes the redundant "Mausrad zum
  Scrollen" hint; scrolling behavior is unchanged.
- de-DE catalog advances to 328 keys.

Safety / semantic contract:
- no endpoint PID or model constant assigns product identity, device class or
  connection role;
- Windows device events remain triggers only;
- live presence still requires the current root identity to verify against the
  stored productKey;
- guided Wired/Wireless learning semantics are unchanged and remain fail-closed;
- Gate 4 health severity and raw diagnostic semantics are unchanged. The new
  connection wording is presentation-only.

Native acceptance focus:
- observe startup and WM_DEVICECHANGE refresh overlays in each product PID cell;
- verify PID plus role label switches to Acid Green only after a successful live
  refresh;
- verify Gate 4 wording matches the actual active alternative path;
- verify the last line of every detail popover remains readable at maximum scroll.
