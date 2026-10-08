# RHC-20 — Pipeline implementation boundaries (nonpublishing)

This document records implementation **source contracts**, not a release approval.
Issue: https://github.com/SaschaP1980/RazerHealthCenter/issues/20

## Version domains

The canonical application/reference version comes from both constants in `model.go`
and must be strict `MAJOR.MINOR.PATCH.HOTFIX`. Localized presentation
`locales/de-DE.json._meta.version` and `i18n-manifest.json.catalogVersion`
represent the **same localization catalog version**, validated as strict four-part
notation, equal to each other, and not newer than the product version. They need
not change on a code-only application Hotfix. Historical frozen v3.0.8 QA and
recovery artifacts do not change.

## Work/Candidate (development-only)

`work/RHC-*` push runs full Linux/Windows independent current-source CI. A
`Development-Completion: requested` exact-line trailer triggers the Work
Completion workflow only after the same Work SHA's push-run completes 2/2 GREEN.
Stable job identifiers `rhc/infra/linux` and `rhc/infra/windows` are
required. An open PR's checks do not substitute a push event or the separate
Completion status. The transfer tool `rhc_candidate_from_work.py` accepts
only a specifically verified `version-only` Work with a two-file diff,
authoritative success receipt, and immediately rechecked unmodified refs;
other profiles remain unsupported/fail-closed. Candidate publication and
Product Release approval are distinct.

## RHC-12 release preactivation (no writes)

`tools/rhc12_release_plan.py` implements a **pure** check of immutable
artifact identity, exact Candidate/Release SHA contexts, strict archive
version/size/hash, seven-file reproducibility evidence, trust bound to
that same source/artifact, independent physical device acceptance, and rollback
provenance. The Python tests use **synthetic** evidence for positive cases.
Running this evaluator never stages/merges a Release PR, creates a tag, signs
a Windows EXE, uploads a ZIP, changes `releases.json`/`latest.json`, or
verifies actual physical Razer hardware by itself.

## Explicitly open before production

Current `productionEnabled=false`, `signingDecision=unknown`,
`rollbackVerified=false` must remain unchanged. Required are real signing
or an exact version/source/archive-bound unsigned owner decision,
native Razer acceptance, real rollback/first-release recovery demonstration,
actual `release/vX.Y.Z.H` orchestration, mandatory GitHub main PR/status
rules, and independent postmerge readback. No absent gate may be labeled GREEN.
