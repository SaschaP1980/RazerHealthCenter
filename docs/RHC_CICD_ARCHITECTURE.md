# RHC — Candidate, CI and Release Architecture

This is a **version-neutral architecture description**. For live version and published source provenance use [Initial Prompt](INITIAL_PROMPT.md), [Git provenance contract](GIT_PROVENANCE_CONTRACT.md) and the current executable source. Concrete migration/release versions, CI run IDs, original design decisions and failures are recorded in the responsible GitHub Issues and Rolling Comments, not here.

## GitHub change graph

Every new changed-file PR, including documentation-only, must link its responsible GitHub `[RHC-N]` Issue in the PR body. A documentation-only Issue-backed lightweight PR does not require Candidate, Work-Path or product release. Product and workflow changes follow the current [Development Guidelines](DEVELOPMENT_GUIDELINES.md) and genuine exact-SHA validation. The no-direct-main rule is a process requirement, not assumed server-side protection.

## Build and Candidate

- Read source/reference version from live `model.go`; use `MAJOR.MINOR.PATCH.HOTFIX` and current `tools/rhc_candidate_entry.py` profiles, ancestry, `RHC-Issue: N` and `Release-Profile` requirements. Candidate and public release versions are distinct.
- For substantial source changes, freeze verified Work SHA, use a persisted BOOTSTRAP-before-branch Rolling Comment, Work Linux/Windows checks and authentic Development Completion. Small executable Hotfixes use the qualified Fast-Path. A source PR and a later publication PR may be distinct.
- Linux double Go/Windows PE builds must be deterministic. Hosted **native Windows PowerShell 5.1** tests are independent checks for source safety, diagnostic/repair contracts and Authenticode status. Physical Razer device/rollback acceptance is a different evidence class.
- Run live actual validators and negative tests; no stale Candidate status, synthetic green context or intentionally blocked **standard production** promotion qualifies an interim release by itself.

## Publication and protection

Distribution uses immutable seven-file Portable ZIPs in `main/downloads/`, append-only `releases.json`, canonical `latest.json` and independent `sourceSha`/immutable versioned Git tag proof; source remains in tagged Git, not a nested Source ZIP. Every release PR references its source PR(s) and owning Issue(s), real stages and SHA-bound CI. A qualified **interim source-first** release can publish via a separate four-download-file PR; the standard signed/certified controller has its own stricter source-plus-downloads contracts. Refer to [Release Process](RELEASE_PROCESS.md) and [Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md), never a historical rehearsal as the current writer.

The owner permits technically qualified unsigned/uncertified interim distribution until explicitly revoked while external hardware, rollback and trusted signer/SmartScreen acceptance remain DEFERRED/NOT_VERIFIED. The standard production policy stays fail-closed. Never disable Razer in-app repair consent or Windows protection to satisfy CI.

Verify actual GitHub ruleset/PR/required-status enforcement and `GITHUB_TOKEN` API rights, don't infer effective permissions from YAML. Require exact staging branch/merge provenance, independent ZIP/catalog/tag remote readback and exact-lease release-branch cleanup. An already public package with incomplete tag/cleanup is a distinct recovery state, not a fresh release. Historical CI failures and owner decisions are archived in Issues; new releases need new exact-SHA proof.
