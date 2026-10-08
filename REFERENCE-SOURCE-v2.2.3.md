# Canonical reference source v2.2.3

This source tree is the canonical development reference for v2.2.3 after final
release validation.

Core versions:
- App: 2.2.3
- Health Engine: 1.4.2
- Setup Scanner: 1.0.2
- Device Inventory schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4

Evidence architecture:
- `PRIMARY` = direct current system evidence; gate-determining.
- `RUNTIME` = recent, time-sensitive runtime evidence.
- `SUPPORTING` = correlative context; never independently gate-determining.

The AppEngine `main.log` probe intentionally keeps a bounded 8,000-line recent
window, now named `runtime-tail-8000`. It is used for runtime observations such
as `isPowerOn` and `missing ffi handler`. Module/install messages observed in
that window are informational supporting evidence only.

Gates 7, 10 and 11 use direct current sources for their health decision:
- Gate 7: 32-bit Chroma registry component evidence.
- Gate 10: Razer Game Manager service state.
- Gate 11: RzComDriver driver/PnP evidence plus installation registration.

Therefore log rotation or growth beyond 8,000 lines cannot turn an otherwise
directly verified healthy module into `UNKLAR`. This contract is enforced in
both Health Engine 1.4.2 and the Go-side gate display path.

The v2.2.2 capability-aware device inventory remains unchanged, including the
four-state native verification of BlackWidow PID 02C9 = Wireless-Dongle and
PID 02CC = wired USB in the Setup profile layer only.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
