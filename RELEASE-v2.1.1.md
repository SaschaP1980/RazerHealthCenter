# Release v2.1.1

## Fixed

- Corrected local Synapse/Chroma version detection. v2.1.0 could incorrectly
  reuse an internal Razer/AppEngine `DisplayVersion` such as `4.0.699` and
  compare it with the public Synapse/Chroma release domain.
- Generic uninstall `DisplayVersion` values are no longer used for public
  Synapse/Chroma version comparison.
- Local versions now come only from product-specific RazerAppEngine build
  metadata for the exact Synapse and Chroma dashboard apps.
- Added a strict public-release-domain guard. Incompatible values such as
  `4.0.699` and `4.0.699.99` produce `UNKLAR` rather than a false
  `NEUER ALS VERÖFFENTLICHT`.
- Module build metadata (for example Chroma Connect) cannot be mistaken for the
  top-level Synapse/Chroma product version.

## UI

- Shifted `DIAGNOSEUMFANG` further left.
- Shifted `VERSION` further right.
- Widened the `SICHERHEITSMODELL` footer column so
  `Diagnose read-only · Reparatur nur nach Bestätigung + UAC` remains on one
  line at the canonical 1180×800 layout.

## Unchanged

- Health Engine 1.3.6.
- 13 health gates and read-only diagnostic model.
- Repair Engine 1.0.0 and Gate-8 repair safety model.
- Official Razer online release lookup remains informational and health-neutral.
- de-DE-only i18n policy; no language switching.
