# Canonical reference source v2.2.0

This source tree is the canonical development reference for Razer Synapse +
Chroma Health Monitor v2.2.0 after final release validation.

Core versions:
- App: 2.2.0
- Health Engine: 1.4.0
- Setup Scanner: 1.0.0
- Repair Engine: 1.0.0
- Device Inventory schema: 1
- VersionStatus schema: 3
- ExportManifest schema: 4

Key architecture invariant: no health run is allowed without a valid persistent
Setup device inventory. Active health logic obtains endpoint/product identities
from that inventory rather than a source-code PID/product allowlist.

The complete Source ZIP is independently buildable and must reproduce the
release EXE byte-for-byte under the validated build environment.
