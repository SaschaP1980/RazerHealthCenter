# Reference Source v3.0.6

Canonical base: Razer Synapse + Chroma Health Center v3.0.5.

v3.0.6 fixes the Windows registry-view handling introduced by the v3.0.5 application-registration guard and adds the first catalogued AppEngine user-mode recovery based on the real September 16 failure/recovery evidence.

## Registry-view correction

The `current_version_registry_key` / `current_version_registry_value` mapping from the official Razer prod manifest is now queried against both Windows registry views explicitly (`Registry64`, `Registry32`). A readable value in either view is `PRESENT`; the resolved view is persisted in VersionStatus and the application assessment. The manifest path is not rewritten with a hard-coded `WOW6432Node` insertion.

## AppEngine user-mode health diagnostic

New read-only module: `RHC.DIAG.APPENGINE.USERMODE` 1.0.0 / `diagnostics/diagnose-appengine-usermode-v1.0.0.ps1`.

It validates the existing HKCU RazerAppEngine launch contract, identifies the versioned `app-*` runtime, the unique main process, and the expected Synapse/Chroma/systray renderer contract. A missing or incomplete user-mode runtime converts a base PASS Gate 1 into UNKNOWN / `PRÜFUNG UNVOLLSTÄNDIG`. Ambiguous runtime states remain unclassified and never receive a guessed repair.

## Catalogued AppEngine recovery

New problem ID: `RHC.APPENGINE.USERMODE.RUNTIME_INCOMPLETE`.
New repair ID: `RHC.REPAIR.APPENGINE.CONTROLLED_RUNTIME_RECOVERY` 1.0.0.
Payload: `repair/repair-appengine-runtime-v1.0.0.ps1`.

The recipe is confirmation-required and does not request elevation. If no AppEngine process is active it uses `START_ONLY_RECOVERY`; if one unique signed versioned runtime is active it uses `FULL_RUNTIME_RESTART`. It changes no services, drivers, registry values, installation state, or Razer files. Post-repair success requires a separate read-only AppEngine diagnostic to confirm the full Synapse/Chroma/systray runtime contract.

The real native test that justified production integration was the non-elevated `START_ONLY_RECOVERY` path, which restored tray, keyboard volume wheel, programmed key mappings, and Chroma. `FULL_RUNTIME_RESTART` remains tightly preconditioned and requires native acceptance in v3.0.6.
