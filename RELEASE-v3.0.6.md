# Razer Synapse + Chroma Health Center v3.0.6

v3.0.6 closes the remaining false-incomplete registry-view bug and integrates a controlled AppEngine user-mode recovery derived from the real failure investigated on 16 September 2026.

## Registry views

- Official Razer manifest registry mappings are read in both `Registry64` and `Registry32`.
- A value found in either view is `PRESENT` and the actual view is recorded.
- No hard-coded product path or endpoint PID is used.
- Version differences remain informational only.

## Gate 1 user-mode validation

- New read-only AppEngine diagnostic module 1.0.0 validates the versioned runtime and expected Synapse/Chroma/systray renderer contract.
- Missing/incomplete user-mode initialization can no longer remain `GESUND` merely because some `RazerAppEngine.exe` process exists.
- Known missing/incomplete runtime states map to `RHC.APPENGINE.USERMODE.RUNTIME_INCOMPLETE`.
- Ambiguous states remain `UNCLASSIFIED`; there is no heuristic repair fallback.

## Controlled AppEngine recovery

- New repair recipe `RHC.REPAIR.APPENGINE.CONTROLLED_RUNTIME_RECOVERY` 1.0.0.
- Explicit in-app confirmation is mandatory before any mutation.
- No automatic UAC/elevation is requested.
- `START_ONLY_RECOVERY`: starts the validated existing Synapse+Chroma HKCU launch contract when no AppEngine process is active.
- `FULL_RUNTIME_RESTART`: only when a unique signed versioned runtime/main process is unambiguously identified; it stops only that validated AppEngine runtime stack and relaunches through the existing launch contract.
- The repair does not modify services, drivers, registry values, installed packages, or Razer files/configuration.
- Exit code 0 is insufficient: success requires a separate read-only AppEngine diagnostic confirming runtime, Synapse, Chroma and systray.

## Platform versions

- App: 3.0.6
- Health Engine: 1.4.6
- Setup Scanner: 1.0.6
- Fast Setup Live Probe: 1.1.0 native SetupAPI
- Diagnostic Orchestrator: 1.1.0
- Problem Catalog: 1.1.0
- AppEngine User-Mode Diagnostic: 1.0.0
- Repair Engine / Catalog: 2.1.0
- AppEngine Recovery Recipe: 1.0.0
- Chroma Diagnostic Module: 1.0.0
- Chroma Repair Recipe: 1.1.0
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 4 (additive registry-view diagnostics)
- ExportManifest schema: 4
- Locale: de-DE, 413 UI keys

No repair is automatic. Every mutation requires explicit in-app confirmation. UAC, where required by a different recipe, remains additional and never substitutes for confirmation.
