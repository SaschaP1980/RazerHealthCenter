# RHC — Candidate, CI and Release Architecture

This is a **version-neutral architecture description**. For live version and published source provenance use [Initial Prompt](INITIAL_PROMPT.md), [Git provenance contract](GIT_PROVENANCE_CONTRACT.md) and the current executable source. Concrete migration/release versions, CI run IDs, original design decisions and failures are recorded in the responsible GitHub Issues and Rolling Comments, not here.

## GitHub change graph

Every new changed-file PR, including documentation-only, must link its responsible GitHub `[RHC-N]` Issue in the PR body. A documentation-only Issue-backed lightweight PR does not require Candidate, Work-Path or product release. Product and workflow changes follow the current [Development Guidelines](DEVELOPMENT_GUIDELINES.md) and genuine exact-SHA validation. The no-direct-main rule is a process requirement, not assumed server-side protection.

## Build and Candidate

- Read source/reference version from live `model.go`; use `MAJOR.MINOR.PATCH.HOTFIX` and current `tools/rhc_candidate_entry.py` profiles, ancestry, `RHC-Issue: N` and `Release-Profile` requirements. Candidate and public release versions are distinct.
- For substantial source changes, freeze verified Work SHA, use a persisted BOOTSTRAP-before-branch Rolling Comment, Work Linux/Windows checks and authentic Development Completion. Small executable Hotfixes use the qualified Fast-Path. For owner-authorized unsigned interim releases from RHC-94 onward, one combined Candidate source+downloads PR is required; historical two-PR publication is not the current architecture.
- Linux double Go/Windows PE builds must be deterministic. Hosted **native Windows PowerShell 5.1** tests are independent checks for source safety, diagnostic/repair contracts and Authenticode status. Physical Razer device/rollback acceptance is a different evidence class.
- Run live actual validators and negative tests; no stale Candidate status, synthetic green context or intentionally blocked **standard production** promotion qualifies an interim release by itself.

## RHC-110 — controlled read-only corrective postrelease audit

After an authorized **verification-only** corrective PR has merged, GitHub Actions can independently re-run RHC-102 without rebuilding or republishing. The controller [rhc-postrelease-recheck.yml](../.github/workflows/rhc-postrelease-recheck.yml) runs upon the completed [verified merged-branch cleanup](../.github/workflows/rhc-branch-cleanup.yml) workflow (`workflow_run`), with an hourly bounded `schedule` sweep if GitHub suppressed a bot-origin PR/push event. An optional `workflow_dispatch` is for owner recovery and **does not override** safety or deduplication. It runs on the trusted default-branch checkout, never PR-owned code.

The [RHC-110 validator](../tools/rhc_postrelease_recheck.py) reconstructs exact current main Git ancestry, published source and version tag, unchanged `downloads/latest.json` and `releases.json`, actual canonical ZIP bytes, original combined release PR, responsible Issue and recorded exact-correction-head owner review/approval. It requires real completed-success Linux + native Windows + cross-platform Infrastructure jobs on the corrective Work SHA, an actual original failed independent three-job postrelease run and a successful one-job merged-branch cleanup event. Subsequent-to-publication changes are strictly allowlisted to verification tests/tools/workflows and their operational documentation; **model.go, CHANGELOG.md, downloads, safety policy and publisher workflows are forbidden**.

Only after these read-only gates does the controller use its narrowly scoped `actions:write` token to dispatch the **existing RHC-102 verifier** on the exact corrected `main` SHA. It supplies the *unchanged* published version, original source SHA and original release PR. A single concurrency group and exact-main dispatch deduplication prevent accidental repeat attempts; stale, missing, skipped, zero-job, failed or wrong-run evidence is **not PASS**. The verifier still requires actual public HTTPS ZIP bytes, native Windows/PowerShell 5.1 safety and all three completed-success jobs. No new Candidate, ZIP, release PR, tag, branch deletion or Razer repair is authorized by the recheck. Later success is a **post-correction audit only** and cannot erase the historical failed initial release. Log run IDs and deviations in the owning Issue Rolling Comment, not in version-neutral docs.

## Publication and protection

Distribution uses immutable seven-file Portable ZIPs in `main/downloads/`, append-only `releases.json`, canonical `latest.json` and independent `sourceSha`/immutable versioned Git tag proof; source remains in tagged Git, not a nested Source ZIP. Every current interim release PR references its responsible Issue, exact Candidate sourceSha and Work-SHA when applicable, real stages and SHA-bound CI. A qualified Candidate is one commit based on previous public main; four downloads files are committed on top of it in a single PR and activated together in one merge. The standard signed/certified controller stays separate, fail-closed. Refer to [Release Process](RELEASE_PROCESS.md) and [Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md), never a historical rehearsal as the current writer.

The owner permits technically qualified unsigned/uncertified interim distribution until explicitly revoked while external hardware, rollback and trusted signer/SmartScreen acceptance remain DEFERRED/NOT_VERIFIED. The standard production policy stays fail-closed. Never disable Razer in-app repair consent or Windows protection to satisfy CI.

Verify actual GitHub ruleset/PR/required-status enforcement and `GITHUB_TOKEN` API rights, don't infer effective permissions from YAML. Require exact staging branch/merge provenance, independent ZIP/catalog/tag remote readback and exact-lease release-branch cleanup. An already public package with incomplete tag/cleanup is a distinct recovery state, not a fresh release. Historical CI failures and owner decisions are archived in Issues; new releases need new exact-SHA proof.


## RHC-190: LBS-aligned product development path (October 2026)

Owner's decision: **Major/Minor → Issue-backed Work-Branch by default**;
**Patch/Hotfix → atomic branchless Fast-Path by default**, with an explicitly
documented Work-Path escalation for substantial risk or a process benchmark.
The four-digit release syntax is already implemented (#16); separate Hotfix
increment/reset and migration semantics remain #191, not a reason to rewrite
historical \`3.0.8.*\` versions. This infrastructure change is NOT a product release.

A branchless Candidate is **one commit on the exact current main** and carries
exactly one \`Development-Path: fast\`, \`RHC-Issue: N\`, and
\`Release-Profile: version-only|patch|hotfix\` trailer. Its canonical open Issue
must have an independently read-back \`dev-path: fast\` disposition and label.
Its numeric version MUST change neither MAJOR nor MINOR, and the complete diff
must pass existing content-profile and safe-path validators. The alternative
Work-Path retains its original \`Work-SHA\`, tree identity and independently
qualified exact-SHA Development Completion. The publisher fails closed if the
Candidate source, Issue disposition, native Windows/Linux status, immutable
source SHA or public main parent differs.

The staged publisher still creates **one exact source+four-download-path PR**,
then requires real hosted Downloads CI, immutable package/hash/catalog
verification, and independent RHC-102 postrelease verification (three actual
Linux HTTPS, native Windows and aggregate jobs). Standard signed production
remains BLOCKED by policy; user-confirmed repair and read-only restrictions
remain intact. Only **after** RHC-102 3/3 success may the publisher remove
the exactly matching canonical \`candidate/vVERSION\` ref; the immutable source
tag is retained. Work-Branch cleanup remains exact-SHA-guarded when relevant.
The separate least-privilege closure job checks five actual run roles for
Work-Path releases or four for branchless fast releases; it never fabricates a
Work run/rolling journal for a fast release.

### Invocable operator and honest benchmark

The only proven ChatGPT-connected mutation boundary is authenticated
**connector operations**, individually leased and read back. This is
\`CONNECTOR_ATOMIC_EQUIVALENT\`, not a native \`git/gh\` CLI and NOT proof that
a repository ESM script was invoked from the conversation. Prefer a true
authenticated checked-out \`git/gh\` command runner only where independently
demonstrated; do not assume unapproved GitHub Apps, PATs, secrets, shell
credentials or recursive bot-created push triggers. A fast Candidate created
by a genuine authenticated connector push may start Candidate Preflight via
\`push\`; a trusted bot Candidate can use the existing explicit
\`workflow_dispatch\` path. Both must produce the same *actual* mandatory
hosted jobs and exact-SHA statuses. An ambiguous write is reconciled by GET,
not replayed.

**Nonpublishing validation first:** compare exact issue/main/tree lineage,
focused RED→GREEN assertions and actual Linux/native Windows Work CI before
merging infrastructure changes. For a future owner-authorized performance
benchmark, record per-run first tool, Issue readback, Candidate ref creation,
push, Actions \`created_at/started_at/completed_at\`, queue, setup and test
elapsed separately. Require **at least three comparable actual runs** and
report every failed/zero-job event as recorded, not PASS. Existing #188 speed
targets are hypotheses; this implementation does **not** claim a measured
fast-path speed-up or a successful real product fast release. The pending
zero-job PR-event classification, reliable repeatability and three-sample
benchmarks remain open under #190; never remove legitimate untrusted-PR
security checks merely to conceal optional red UI noise.
