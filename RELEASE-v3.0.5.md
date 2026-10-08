# Razer Synapse + Chroma Health Center v3.0.5

v3.0.5 fixes a false-green Health Center result observed with a degraded Synapse/Chroma user-mode installation state.

## Application registration health guard

- Health Engine 1.4.6 remains unchanged and read-only.
- During each Health run, the Health Center resolves the current official Razer `prod` product manifest in parallel.
- The primary `Razer Synapse` and `Razer Chroma` modules are evaluated only through the exact `current_version_registry_key` / `current_version_registry_value` mappings supplied by Razer.
- A version difference remains informational only. `UPDATE_AVAILABLE` is still cyan INFO and cannot degrade Health.
- If a manifest-defined product registration cannot be read while the base AppEngine gate was PASS, Gate 1 is finalized as `UNKNOWN` and the overall Health Center state becomes `PRÜFUNG UNVOLLSTÄNDIG`, not `GESUND` and not `FEHLER`.
- If the official manifest is unavailable, this guard has no Health impact; the Health check does not require Internet connectivity.
- The composition is persisted as `ApplicationHealthAssessment-<stamp>.json`; final `RazerHealth-*.json` and `GateResult-*.txt` are aligned with the composed result.
- The existing Diagnostic Orchestrator receives the UNKNOWN gate as `UNCLASSIFIED`. No repair is automatically performed or offered as known until a root cause is proven.

## Unchanged platform contracts

- App: 3.0.5
- Health Engine: 1.4.6
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.1.0 native SetupAPI
- Diagnostic Orchestrator: 1.0.0
- Problem Catalog: 1.0.0
- Repair Engine / Catalog: 2.0.0
- Chroma Repair Recipe: 1.1.0
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 4 (additive registration-state diagnostics)
- ExportManifest schema: 4
- Locale: de-DE, 382 UI keys

No repair is automatic. Every mutation requires explicit in-app confirmation, optional UAC is additional, and post-repair verification remains read-only.
