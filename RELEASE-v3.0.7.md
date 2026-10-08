# Razer Synapse + Chroma Health Center v3.0.7

v3.0.7 fixes a Windows PowerShell 5.1 compatibility defect in the AppEngine user-mode diagnostic added in v3.0.6.

## Fixed false incomplete result

On a healthy recovered system, the v3.0.6 diagnostic could terminate with `System.ArgumentException: Argument types do not match`. The Health Center then correctly treated the diagnostic itself as unreadable, but the resulting Gate 1 UNKNOWN / `PRÜFUNG UNVOLLSTÄNDIG` was a false positive caused by the diagnostic implementation rather than the Razer runtime.

The AppEngine diagnostic is now version 1.0.1 and uses native PowerShell arrays for process/error collection and JSON output. The problematic Generic.List-to-array materialization path has been removed.

## Unchanged architecture and safety

- Health Engine: 1.4.6
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.1.0 native SetupAPI
- Diagnostic Orchestrator: 1.1.0
- Problem Catalog: 1.1.0
- AppEngine User-Mode Diagnostic: 1.0.1
- Repair Engine / Catalog: 2.1.0
- AppEngine Recovery Recipe: 1.0.0
- Chroma Diagnostic Module: 1.0.0
- Chroma Repair Recipe: 1.1.0
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 4
- ExportManifest schema: 4
- Locale: de-DE, 413 UI keys

Registry32/Registry64 handling from v3.0.6 is unchanged. No repair is automatic. Every mutation requires explicit in-app confirmation, and post-repair success still requires read-only verification.
