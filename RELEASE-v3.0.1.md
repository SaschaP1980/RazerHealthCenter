# Razer Synapse + Chroma Health Center v3.0.1

v3.0.1 corrects the authority model for version and hash evidence. A version or
hash observed on a previously healthy installation is no longer treated as a
normative Soll value. Official Razer updater manifest data is now the only
online manufacturer source used for Synapse/Chroma offered-version comparison.

## Health Engine 1.4.6

- Removes static local Known-Good versions from normative gate evaluation.
- Gate 3 no longer creates a warning solely because an RzDev/RzCommon version
  differs from a historical local baseline.
- Gate 7 still verifies presence/readability of expected internal Chroma registry
  version entries, but their concrete version strings are inventory only.
- LampArray/runtime hashes remain INFO/SUPPORTING evidence and cannot degrade
  health merely by differing from a local Known-Good hash.
- Version-specific cached-installer Known-Good hash comparisons are removed.
- Official manifest download-package checksums are not reinterpreted as Soll
  hashes for installed runtime files.

## Official Razer prod-manifest version monitor

VersionStatus schema 4 replaces release-note scraping with the updater path used
by Razer itself:

1. Resolve the current `prod` hash from
   `https://discovery3.razerapi.com/api/v1/endpoints`.
2. Build the system-specific `manifest3.razerapi.com` product request from OS,
   architecture, manufacturer, model, system SKU and UI locale. No serial number
   or equivalent unique machine identifier is sent.
3. Select the primary `Razer Synapse` and `Razer Chroma` modules.
4. Read local installed versions from the exact registry key/value mapping
   supplied in the Razer manifest.
5. Compare only the matching module-version domain.

Result semantics:

- local older than offered version → cyan INFO `NEUE VERSION VERFÜGBAR`;
- equal → current;
- local newer → informational `NEUER ALS MANIFEST`;
- unavailable/uncomparable → version-monitor unknown only.

None of these version-monitor states degrade the 13-gate Health status. The
observed Razer product manifest provides no proven minimum/required/mandatory
version semantics and no normative internal Chroma SDK Root/Core versions.

## Repair safety unchanged

No repair is automatic. Every repair still requires explicit in-app user
confirmation before any mutation. UAC is additional where needed and never
replaces that confirmation. Post-repair read-only verification remains mandatory.

## Validation

The release adds `tools/validate_v301_manifest_authority.py`. The captured RED
baseline fails against the pre-change v3.0.0 authority model; the v3.0.1 source
must pass all 20 manifest-authority checks in addition to the complete existing
regression/build suite.
