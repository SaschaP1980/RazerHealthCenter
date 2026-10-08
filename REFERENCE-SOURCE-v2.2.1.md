# Canonical reference source v2.2.1

This source tree is the canonical development reference for Razer Synapse +
Chroma Health Monitor v2.2.1 after final release validation.

Core versions:
- App: 2.2.1
- Health Engine: 1.4.0
- Setup Scanner: 1.0.1
- Repair Engine: 1.0.0
- Device Inventory schema: 1
- VersionStatus schema: 3
- ExportManifest schema: 4

Setup Scanner 1.0.1 is the productionized form of the native-tested scanner
that correctly inventoried the current Razer Viper V3 Pro (PID 00C1),
BlackWidow V4 Low-profile HyperSpeed active path (PID 02C9) and the known
alternate BlackWidow path (PID 02CC) without hardcoding those values into the
scanner source. Product grouping is derived from discovered Windows metadata.

Health remains inventory-gated. The Setup page has one action only: Setup Scan.
Health is started from Status; a missing profile automatically triggers Setup and
resumes Health after a valid inventory is persisted. Setup scanning uses an
indeterminate progress animation. Scanner debug JSON/TXT artifacts are preserved
into session Diagnostics for export on both successful and failed runs.

The complete Source ZIP is independently buildable and must reproduce the
release EXE byte-for-byte under the validated build environment.
