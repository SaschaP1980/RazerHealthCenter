# Razer Synapse + Chroma Health Center v3.0.8.0

**Versioning migration (RHC-16):** This source now uses MAJOR.MINOR.PATCH.HOTFIX. v3.0.8.0 is the first four-component application version. Earlier v3.0.8 artifacts and change descriptions below are historical and remain immutable. No new public release is implied.

v3.0.8 is a narrow health-semantics patch for the AppEngine user-mode diagnostic. A real native Windows measurement showed a fully functional steady-state background runtime with tray, mappings, device middleware and Chroma working while transient `win-synapse` / `win-chroma-app` dashboard renderers were no longer resident. v3.0.7 incorrectly treated those transient UI renderers as mandatory and reported Gate 1 UNKNOWN.

The AppEngine diagnostic is now version 1.0.2. HEALTHY requires the validated Synapse+Chroma run contract, one unambiguous runtime main process using that contract, systray, background manager, lighting engine and generic device middleware. `win-synapse` / `win-chroma-app` remain captured as supporting evidence only. Missing systray still makes the runtime incomplete, preserving detection of the real broken state observed earlier.

## Versions
- App: 3.0.8.0 (MAJOR.MINOR.PATCH.HOTFIX)
- Health Engine: 1.4.6
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.1.0
- Diagnostic Orchestrator: 1.1.0
- Problem Catalog: 1.1.0
- Chroma Diagnostic: 1.0.0
- AppEngine User-Mode Diagnostic: 1.0.2
- Repair Engine/Catalog: 2.1.0
- Chroma Repair: 1.1.0
- AppEngine Recovery: 1.0.0

All repair confirmation, elevation and read-only verification rules remain unchanged.
