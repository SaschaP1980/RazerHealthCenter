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

## Continuation — 2026-10-08 (Chat RHC20CHAT236C9E999A7A)

The RHC-20 Work-Path retained the same branch and Draft PR #21. Actual resumed implementation milestones:

- Added a focused **test-first RED** on `84a7cc610cbc57994b2f60e93d05db25478c48a9`: [Linux Actions run #37798149161](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37798149161), five failed assertions due to absent Candidate `workflow_dispatch` and missing `rhc/preflight/*` contexts. Expected RED is never counted as GREEN.
- Candidate Preflight now supports explicit `workflow_dispatch` and writes **exact SHA statuses** `rhc/preflight/linux`, `rhc/preflight/windows`, `rhc/preflight/candidate` only after their respective successful hosted OS checks. **The promotion job still deliberately exits 1**, and `config/rhc-release-policy.json` is unchanged.
- `rhc-candidate-from-work.yml` now filters event commits for both `Release-Profile: version-only` and `Development-Completion: requested` in addition to same-repository origin and successful Work Completion. This prevents infrastructure-only Work paths from reaching the Candidate writer.
- Candidate Linux now runs **two separate clean Go/PE builds** and compares the EXE bytes; independently packages source/portable archives twice and compares the archive bytes. This is workflow source now; a real future Candidate run is required to qualify it end-to-end.
- The Work→Candidate creator enforces the exact two-literal `model.go` version diff against separately fetched main/work file bytes, before any write; other model edits cause a hard error. Five fully mocked API transaction tests exercise a positive nonpublishing candidate, stale main, absent Completion, source modification, existing candidate, partial dispatch and no blind retry. No real candidate was generated.
- New `.github/workflows/rhc-release-preactivation.yml` is **strictly read-only** and independently runs the RHC-12 pure adversarial release fixtures, immutable QA/downloads verification and a negative test showing that the actual `productionEnabled=false` policy rejects the preactivation fixture. [Push #37799708401](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37799708401) and [PR #37799721368](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37799721368) are both actual SUCCESS. These green checks **do not prove** signed/unsigned publisher consent, real Razer hardware, real rollback or a published artifact.

### Remaining fail-closed boundaries

- Candidate `workflow_dispatch`, permission/status publication and independent Go builds have been added to PR #21, **but a real Candidate v3.0.8.1 has not been created or run**. Candidate-to-Release orchestration still requires an independent exact-SHA qualification and a separately authorized source/tag/package release transaction.
- Full RHC-12 production `repo-downloads` publisher, mandatory GitHub Ruleset PR/status protection, physical Windows/Razer acceptance, verified rollback and exact artifact-bound signing or unsigned approval remain OPEN. The pure RHC-12 plan and the read-only workflow cannot perform or substitute these actions.
- `main` remains `efcac9ee5a99940c8c2f85f779404f4eae524cfa`, application `3.0.8.0`. RHC-18 PR #19 stays separate/Draft, RHC-20 PR #21 stays Draft until explicitly qualified for review and safe merge. No ZIP, tag, latest pointer, product/version/policy change or Razer repair occurred.
- The source of truth for exact final Work SHA, hosted Linux/Windows results, Work Completion result, liveness/deviations and remaining acceptance gates is the [single RHC-20 Rolling Comment](https://github.com/SaschaP1980/RazerHealthCenter/issues/20#issuecomment-6062346819). Do not infer current GREEN or Completion from a previous SHA.

## Variant B — 2026-10-08: technical completion versus external product acceptance

- [Issue #20](https://github.com/SaschaP1980/RazerHealthCenter/issues/20) now closes only after real Work/Fast/Candidate E2E and fully tested, **nonpublishing** release orchestration, exact SHA/status/recovery contracts, documentation and verified GitHub merge/cleanup; only the final qualified PR may contain the GitHub issue-closing directive. It is **NOT yet technically complete**.
- [New Issue #22](https://github.com/SaschaP1980/RazerHealthCenter/issues/22) remains separately OPEN for independent physical Windows/Razer testing, native rollback/first-release recovery, exact version/source/artifact-bound signer or unsigned owner authorization, actual production enablement and first real release. No CI-only result can waive these external decisions.
- [PR #21](https://github.com/SaschaP1980/RazerHealthCenter/pull/21) MERGED (not Draft) at `main=7166335dbc418debb19d7ad00f96e448fc9a46fd`; verified old work branch removed by [cleanup #37803299106](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37803299106).
- [PR #23](https://github.com/SaschaP1980/RazerHealthCenter/pull/23) is a **separate in-progress nonpublishing technical release rehearsal**: independent current PE binaries and exact seven-file ZIPs, disposable copied download history, 3 tamper scenarios, original historical QA retained. The first Linux/push rehearsal was GREEN but full Windows infrastructure initially RED because the Python test wrote a Unicode README under Windows default CP1252; explicit UTF-8 fixture correction is present, final SHA-hosted Windows proof is **pending**. This PR has no GitHub issue-closing directive because major candidate/release work is outstanding.
- Current production remains **BLOCKED** by actual `productionEnabled=false`, `signingDecision=unknown` and `rollbackVerified=false`. No product ZIP, tag or official `latest.json` may be created by technical CI.

## RHC-20 latest technical implementation (2026-10-08)

Candidate version 3.0.8.1 is real and qualified: Work `62f065c414475287f529d11279adc0bf865d9a44`, Candidate `1b78ca928979e9507863a53ce2e4b25491544d5e`, exact Linux/Windows/Candidate statuses all SUCCESS. Production promotion deliberately blocked. New Work branch from `main=d1285d5adb8de744207f8e6f017d02e5d9ed10bc` adds fail-closed Candidate recovery, pure release PR/approval/replay/postverify contracts, an owner-gated real GitHub Release PR builder and finalize path, exact SHA native Linux/Windows release status workflow, and main ruleset admin-only setup/audit. Synthetic mocked approval is NOT real signed/unsigned or native hardware evidence.

Current main ruleset 24701145 enforces deletion/non-fast-forward only. Owner admin correction with no manual GitHub review required cannot be activated using installed connector; report it as an explicit external issue #22 blocker. Real policy `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`. RHC-20 must not be closed until CI and all technical completion requirements truly pass; no tags/official ZIP/latest were created.
