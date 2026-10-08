# Canonical reference source v2.3.3

This source tree is the canonical development reference for v2.3.3 after static,
Windows-amd64 build, packaging and clean-rebuild validation.

Component versions:
- App: 2.3.3
- Health Engine: 1.4.3
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.0.1
- Repair Engine: 1.0.0
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 328 UI keys

v2.3.3 is intentionally narrow: the Setup per-product live-refresh progress
indicator is rendered as an overlay centered in the same vertical text band as
the PID/role display. It no longer occupies a separate visual line below the
text. All live-presence, product-identity, guided-learning and Health semantics
remain those of v2.3.2/v2.3.1.
