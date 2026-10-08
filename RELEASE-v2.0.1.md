# Release v2.0.1

Patch release for PowerShell 5.1 text encoding.

## Fixed
- German umlauts in Health Engine report and JSON no longer become mojibake.
- EngineOutput stdout/stderr capture is explicitly UTF-8.

## Preserved
- Health Engine 1.3.5 canonical embedded bytes and diagnostic logic unchanged.
- Repair Engine 1.0.0 and Gate-8 repair safety contract unchanged.
- de-DE-only presentation i18n and all v2.0.0 UI/diagnostic behavior unchanged.
