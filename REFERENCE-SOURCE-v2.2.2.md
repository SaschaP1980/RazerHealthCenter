# Canonical reference source v2.2.2

This source tree is the canonical development reference for v2.2.2 after final release
validation.

Core versions:
- App: 2.2.2
- Health Engine: 1.4.1
- Setup Scanner: 1.0.2
- Device Inventory schema: 2
- Repair Engine: 1.0.0
- VersionStatus schema: 3
- ExportManifest schema: 4

v2.2.2 is the capability-aware follow-up to the v2.2 inventory architecture.
Setup now distinguishes Windows Inbox HID paths from Razer filter-stack paths and
persists per-connection binding/filter capabilities. Health Gates 2-6 consume
those capabilities instead of assuming a BlackWidow-style stack for every PID.

The BlackWidow roles PID 02C9 = Wireless-Dongle and PID 02CC = wired USB were
verified through four controlled native scans on 2026-09-10 and are encoded only
in the Setup profile layer. Viper V3 Pro PID 00C1 remains generically discovered
and is classified from live driver evidence as a Windows-Inbox-HID path.

The complete Source ZIP must independently reproduce the release EXE byte-for-
byte under the validated build environment.
