# Canonical Source Reference v2.1.1

v2.1.1 supersedes v2.1.0 as the active source/development baseline.

Version-detection correction:

- Synapse/Chroma local public versions are no longer read from generic Windows
  uninstall `DisplayVersion` entries.
- Local public versions are accepted only from product-specific RazerAppEngine
  build metadata tied to the exact top-level dashboard URLs:
  - `https://apps.razer.com/synapse/dashboard/`
  - `https://apps.razer.com/chroma-app/dashboard/`
- `version` + `buildVersion` are combined into the public release domain
  (`x.y.z.<build>`). Module URLs such as `/synapse/chroma-connect/` are rejected.
- A strict version-domain guard prevents internal values such as `4.0.699` or
  `4.0.699.99` from being compared with public Synapse/Chroma release versions.
  If no trustworthy local release metadata is available, the UI shows `UNKLAR`.
- AppEngine package and FileVersion remain separate informational values.

Info-view footer layout:

- `DIAGNOSEUMFANG` moved left;
- `VERSION` moved right;
- `SICHERHEITSMODELL` receives the wider center column and its detail renders
  single-line.

Health Engine 1.3.6 and Repair Engine 1.0.0 are unchanged. The 13-gate health
model, repair safety model, de-DE-only i18n policy and delivery contract remain
unchanged.

This complete Source ZIP is the canonical reference for all future development.
