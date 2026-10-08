# Reference Source v3.0.7

Canonical base: Razer Synapse + Chroma Health Center v3.0.6.

v3.0.7 is a narrow reliability patch for the read-only AppEngine user-mode diagnostic introduced in v3.0.6. A real native Windows run showed that the diagnostic could fail under Windows PowerShell 5.1 with `System.ArgumentException: Argument types do not match`, which incorrectly downgraded an otherwise healthy Gate 1 to UNKNOWN / `PRÜFUNG UNVOLLSTÄNDIG`.

## PowerShell 5.1 compatibility correction

`RHC.DIAG.APPENGINE.USERMODE` is versioned from 1.0.0 to 1.0.1 and the active payload is now `diagnostics/diagnose-appengine-usermode-v1.0.1.ps1`.

The module no longer uses `Collections.Generic.List[...]` containers that are later materialized with PowerShell array-subexpression syntax. The process and error collections are native PowerShell arrays from creation through JSON serialization. This removes the observed PS 5.1 type-binding failure while preserving the same read-only evidence model, launch-contract checks, runtime-state classification, and output schema.

## Unchanged behavior

- Registry64/Registry32 manifest mapping from v3.0.6 is unchanged.
- Gate 1 is still downgraded only when AppEngine user-mode evidence is genuinely missing, incomplete, ambiguous, or unreadable.
- `RHC.APPENGINE.USERMODE.RUNTIME_INCOMPLETE` and `RHC.REPAIR.APPENGINE.CONTROLLED_RUNTIME_RECOVERY` remain unchanged.
- Every repair remains explicitly confirmation-required.
- The AppEngine recovery still does not request automatic elevation and does not modify services, drivers, registry values, installed packages, or Razer files.
- The Chroma service repair remains separately catalogued and UAC-required after explicit confirmation.
