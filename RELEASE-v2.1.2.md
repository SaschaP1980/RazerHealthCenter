# Release v2.1.2

## Fixed

- Corrected the remaining local public-version derivation bug from v2.1.1.
- RazerAppEngine top-level metadata observed on the native system reports
  `version: 0.0.86` for Synapse and `version: 0.0.63` for Chroma while the
  active local AppEngine package is `app-4.0.699`. v2.1.1 treated the raw
  `0.0.x` product metadata as a complete product version and therefore showed a
  false `UPDATE VERFÜGBAR`.
- v2.1.2 now derives the local public release entirely from local installation
  evidence:
  - leading product major from the active `RazerAppEngine\app-X.Y.Z` package;
  - product-specific release tail from the exact top-level dashboard metadata;
  - `buildVersion` from the same top-level product metadata.
- Known-good derivations:
  - AppEngine `4.0.699` + Synapse raw `0.0.86` + build `2608311115`
    -> `4.0.86.2608311115`;
  - AppEngine `4.0.699` + Chroma raw `0.0.63` + build `2608271424`
    -> `4.0.63.2608271424`.
- No online version is used to construct a local version. The Razer online
  release remains an independent comparison source only.
- Raw product version, buildVersion and derivation method are persisted in
  `VersionStatus` schema 3 for diagnostic traceability.

## Safety / guards

- Derivation is allowed only for exact top-level Synapse/Chroma dashboard
  metadata. Module URLs remain rejected.
- Raw derivation requires the observed `0.0.<product>` shape, a plausible
  buildVersion and a valid non-zero major from the local AppEngine package.
- Already complete local public release versions are accepted without rewriting.
- Generic ARP/Uninstall DisplayVersion values remain excluded.
- AppEngine package and FileVersion remain separate informational fields.

## Unchanged

- Info footer layout from v2.1.1.
- Health Engine 1.3.6 and all 13 health gates.
- Repair Engine 1.0.0 and Gate-8 repair safety model.
- de-DE-only i18n policy and delivery contract.
