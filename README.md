# Razer Synapse + Chroma Health Center

**Live version authorities:** application version from [`model.go`](model.go) (`appVersion`, `referenceVersion`); latest **published** Portable version from [`downloads/latest.json`](downloads/latest.json), verified against [`downloads/releases.json`](downloads/releases.json), actual ZIP and source tag. These may differ. The **standard production policy** is independent and lives in [`config/rhc-release-policy.json`](config/rhc-release-policy.json). A real owner-authorized interim publication does not activate this standard policy. App versioning uses `MAJOR.MINOR.PATCH.HOTFIX`; prior three-component release evidence is historical.

v3.0.8 is a narrow health-semantics patch for the AppEngine user-mode diagnostic. A real native Windows measurement showed a fully functional steady-state background runtime with tray, mappings, device middleware and Chroma working while transient `win-synapse` / `win-chroma-app` dashboard renderers were no longer resident. v3.0.7 incorrectly treated those transient UI renderers as mandatory and reported Gate 1 UNKNOWN.

The AppEngine diagnostic is now version 1.0.2. HEALTHY requires the validated Synapse+Chroma run contract, one unambiguous runtime main process using that contract, systray, background manager, lighting engine and generic device middleware. `win-synapse` / `win-chroma-app` remain captured as supporting evidence only. Missing systray still makes the runtime incomplete, preserving detection of the real broken state observed earlier.

## Historical component version snapshot and current application authority
- Current app/reference: [`model.go`](model.go); latest public Portable: [`downloads/latest.json`](downloads/latest.json). The component versions below record the original source snapshot.
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
