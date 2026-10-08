# Release v2.1.0

## Added

- Informational version monitor in the Info view.
- Installed Synapse and Chroma DisplayVersion detection from Windows uninstall
  metadata when available.
- AppEngine package version and FileVersion displayed separately.
- Latest stable Synapse/Chroma lookup from official Razer Insider release pages.
- CURRENT / UPDATE AVAILABLE / AHEAD / UNKNOWN comparison semantics.
- Session diagnostic artifact `VersionStatus-<session>.json`.

## Changed

- Health Engine updated from 1.3.5 to 1.3.6.
- Removed the semantically invalid comparison of AppEngine FileVersion against
  historical package baseline `4.0.699`.
- AppEngine package and file versions are now informational checks and do not by
  themselves create Gate-1 hints.

## Unchanged

- 13 health gates.
- Diagnostic read-only model.
- Repair Engine 1.0.0 and Gate-8 repair safety model.
- de-DE-only i18n policy; no language switching.

## Build-time official release observation

On 2026-09-09 the official Razer Insider stable release area exposed:

- Synapse for Windows: `4.0.86.2608311115`
- Chroma for Windows: `4.0.63.2608271424`

The application does not hard-code these values; it retrieves the current
stable pair at runtime and treats retrieval failure as informational/unknown.
