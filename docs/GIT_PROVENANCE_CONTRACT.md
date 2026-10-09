# RHC — Git provenance and Issue–PR traceability

This **version-neutral** contract defines an evidence chain. Live Git/GitHub and machine-readable release records are the technical authorities; Issues and their Rolling Comments own historical *why*, decisions, observed failures, CI evidence and approval.

## Source and release are separate states

- Source version: read `appVersion` and `referenceVersion` from `model.go` on the verified current `main`.
- Published version: read `downloads/latest.json`, reconcile `downloads/releases.json` and verify the real immutable Portable ZIP (size, SHA-256 and internal checksums). Verify that the release `sourceSha` equals the immutable version tag target.
- The newest `main` commit, version tag, Candidate branch, latest public download and release PR head can **differ**. A tag, commit subject, README, or green Candidate is not publication proof.
- Trace source and release through actual commits and merged PRs; verify PR head, merge SHA, ancestry and associated Issue(s). Historical releases may have separate source and release PRs; RHC-94 releases MUST use one combined source+downloads PR, with exact Candidate sourceSha and one atomic public activation merge. PR changes answer **what**; Issues/rolling evidence answer **why**.

## Mandatory future process

1. **Create/select a real Issue before any changed-file work**, titled `[RHC-N]` using GitHub's allocated number. Record owner scope, constraints, acceptance and risks. Reuse existing ownership rather than duplicating Issues.
2. **Every new changed-file PR**, including documentation, infrastructure, product source and publication, must explicitly link at least one responsible Issue in its **body**, not just its title. Use `Refs #N` for a partial scope; `Closes #N` only if actual acceptance will be complete at merge. Multiple Issue or PR references are legitimate when explicit. Preserve required `RHC-Issue: N` commit trailers for executable Candidate workflows.
3. PR body must identify changed-file scope, frozen source/base/head, relevant tests/CI, release/safety impact, and any source/release PR linkage. Atomic interim release PRs link the responsible Issue, the qualified Candidate `sourceSha`, its exact Work-SHA where applicable, and all four published downloads; no preceding source-only PR is required. Older two-PR history remains historically valid.
4. Documentation-only changes follow a **lightweight Issue-backed documentation branch + reviewed PR**: no product version bump, Candidate, Work-Path heartbeat, or release. No routine direct-to-main commit, even where technically permitted.
5. After verified merge, record PR URL, exact head/merge/main SHA, actual checks, cleanup and disposition in the responsible Issue or established Rolling Comment. Close Issues only after all their scoped criteria are satisfied. Keep prior RED attempts as historical truth.

## Limits and historical exceptions

The no-direct-main and Issue–PR requirements are **project policy**, not proof of server-side required-PR protection. Read live rulesets and report missing technical enforcement. No administrative ruleset or permission modification is authorized implicitly.

Older direct commits, PR bodies without Issue links and abandoned refs remain **authentic legacy gaps**. Do not fabricate historical PRs, rewrite immutable tags/releases, or silently delete unmerged branches to create a false complete chain.

Only explicit technical schema/placeholders such as `MAJOR.MINOR.PATCH.HOTFIX` belong in normative Markdown. Dated versions, ZIP hashes, status tables, run IDs and Issue finalization narratives belong in Issues, Rolling Comments, PRs, Git and catalogs, **not** mirrored here.

## Reconstruction check

Read current main/tree/model.go, downloads catalog/actual ZIP/tag/source SHA, merged PR(s), related Issue(s)/Rolling Comments, exact-SHA Linux/native Windows CI, release-merge/branch cleanup and distinct external trust/hardware status. Report any missing provenance edge as missing; never infer that hosted tests prove real Razer hardware, verified publisher, rollback or a signed production release.
