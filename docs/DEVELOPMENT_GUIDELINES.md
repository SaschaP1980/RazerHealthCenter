# RHC — Development guidelines

> **Variante B / 2026-10-08:** [RHC-20](https://github.com/SaschaP1980/RazerHealthCenter/issues/20) umfasst die vollständig geprüfte **technische, bis zur gesonderten Freigabe nichtpublizierende** Candidate-/Release-Automatisierung. Native Razer-Geräteabnahme, Rollback-/First-Release-Recovery, konkrete Source-/ZIP-gebundene Signatur-/Unsigned-Owner-Zustimmung und tatsächliche Produktionsaktivierung/Erstveröffentlichung liegen **ausschließlich in [Issue #22](https://github.com/SaschaP1980/RazerHealthCenter/issues/22)**. Die GitHub-Schließreferenz darf erst im letzten vollständig technisch GREEN geprüften PR aktiviert werden und ausschließlich #20, **niemals #22**, schließen oder die reale Produktionspolicy automatisch freigeben. Der Owner führt keine manuellen GitHub Reviews für normale, technisch qualifizierte PRs durch; Merge und Cleanup sind autonom nach tatsächlichen Gates. `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false` bleiben bis zu getrennten externen Belegen gültig.

> **Target operating contract; production release automation is not ready until the migration acceptance gates are met.**

## Authority

Use current GitHub `main` plus Issues as the canonical working record: **source import and hosted baseline verification completed in PR #2**. The separate production Candidate/Release infrastructure is still unimplemented; `docs/MIGRATION_STATUS.md` records those open gates. Never use another project's main branch or private conversation memory as RHC runtime authority.

## Preserve product invariants

The Go Razer Health Center includes PowerShell diagnostic and repair scripts. Functional work must retain explicit repair approval, product-specific least privilege, no automated elevation, narrowly authorized service/user-mode restarts, pre-mutation rechecks, post-mutation read-only verification, PID ambiguity guards and false-GREEN protections. Only regress expected product behavior with a proven test. No production interaction with the user's Razer hardware during hosted CI.

## Version and development path

**RHC-16 is complete:** `model.go` app/reference is `3.0.8.0`, and current/new app, Candidate and Release versions use strict `MAJOR.MINOR.PATCH.HOTFIX`. Original three-part v3.0.8 Source/QA stays historical; Engine/History/Razer version domains remain separate. The earlier instruction not to use four components is superseded.

- Documentation-only Markdown/Issue metadata with no machine-enforced changes: one atomic lease-guarded reviewed `main` commit; **no** Work branch, `dev-path` label, version, Candidate or Release. The topic of a document does not change its scope.
- Narrow Patch/Hotfix: branchless Fast-Path by default; test a confirmed failure RED where applicable, fix, run relevant focused GREEN/syntax/determinism checks, create **one exact release-ready candidate** on current `main`, inspect complete diff, then hosted Candidate Preflight.
- Major/Minor or substantial risk/migration: persistent `work/RHC-<issue>` with scoped checkpoints, exact-SHA Development Completion and Candidate Entry before any Candidate.
- Process benchmarking Work-Path for an otherwise simple Hotfix requires explicit user permission, a durable exception reason and same exact-SHA qualification gates. Never escalate merely to have more commits.
- For Issue-backed **executable** development select exactly one live-verified `dev-path: fast` or `dev-path: work-branch` label. Labels were provisioned during migration; recheck current catalog before applying. Documentation/backlog work has no `dev-path` requirement.

### Candidate, Issue and test-first requirements (implemented RHC contracts)

Today `tools/rhc_candidate_entry.py` requires exact current-`main` parentage, a single atomic Candidate commit, one actual `RHC-Issue: N` trailer (**also for Hotfix**) and one `Release-Profile: version-only|patch|hotfix` trailer. Both `model.go` and `CHANGELOG.md` must change; `version-only` changes **exactly** those two paths, and `hotfix` increases only the fourth number by one. `CHANGELOG.md` does not yet exist on `main`; a future authorized Candidate must add it in scope. Do not import LBS' different Issue/profile semantics.

A confirmed defect gets a **permanent focused RED test against the exact unfixed SHA**, then a fix and the same test GREEN; a deliberately failing Candidate is never the RED test. For changed validators, Python tools and workflows, select a non-destructive real CLI/consumer smoke, not just syntax. Preserve Go, PowerShell 5.1, repair-safety, PE/ZIP reproducibility and four distinct evidence categories (local, hosted Linux, hosted native Windows, physical Razer). Issue closure follows its verified acceptance gates; unresolved parent RHC-1/RHC-3 remain open.

## Work-Path rolling record

**Work-Path bootstrap is a fail-closed prerequisite, not end-of-run paperwork.** For any authorized Issue-backed Work-Path:

1. Verify Issue, owner authorization, fresh main SHA, version and approved/forbidden paths; an unborn repo may require an initial minimal bootstrap commit solely to obtain a real main SHA.
2. **Before the Work branch, first code/workflow change, Work PR or related CI**, create the **single** Issue Rolling Comment in phase `BOOTSTRAP` with planned branch `NOT CREATED`, main SHA checkpoint, scope, risks and exact next action.
3. Read the comment back through GitHub; validate its ID, persisted content, actual millisecond UTC heartbeat and `created_at`/`updated_at`. If absent, inconsistent or unverifiable, **STOP** before branch creation.
4. Create the Work branch from the still-current SHA, re-read its head, update and re-read the **same comment before the first code commit**. If this fails, **BLOCKED**.
5. Refresh exact work/main/CI checkpoints before consequential next actions and after significant commits. After interruptions re-fetch authoritative state instead of guessing. Record late initial comments as process violations regardless of GREEN tests.

### Active heartbeat cadence and restart detection (LBS parity)

The single Work-Path Issue Rolling Comment is a **time-based liveness and recovery record in addition to event-driven checkpoint updates**. While the agent is actively implementing, keep `Agent-State: ACTIVE` and update **that same comment** so its verified, freshly timestamped `Last heartbeat` never becomes more than approximately **3 minutes old**. Never create a new comment or a Git commit solely to satisfy a heartbeat. Each in-place edit must retain all previous recovery-relevant evidence and be read back after writing; serialize comment mutations.

Prefer useful new findings, decision points, completed checks, errors and fixes. If no substantive state changed, write a concise truthful ACTIVE/liveness update with last confirmed main/Work SHA, currently running task and next exact action. Update before a long/high-risk tool sequence. No need to wait for a code commit or CI result; such sequences may last longer than the heartbeat interval.

Pause the ACTIVE cadence **only** when the Rolling Comment truthfully records `Agent-State: WAITING_FOR_GITHUB` with a verified independently running/queued workflow and exact run ID, `BLOCKED_EXTERNAL` with observed outage and last verified state, `IDLE`/`STOPPED` with work actually suspended, or `COMPLETED` after all authorized terminal verification (for nonpublishing work: PR/main/CI/cleanup, with publication and hardware gates honestly marked not applicable/open). A queued workflow without an exact run ID is not a verified waiting exception. On resuming, return to ACTIVE and refresh the heartbeat immediately.

An ACTIVE heartbeat older than approximately **3 minutes** is a missed heartbeat. If older than approximately **5 minutes**, with no identified live queued/in-progress workflow, **treat the interactive stream as stopped**, not as proof it is still running. On recovery, re-read the Issue/complete rolling comment, current main and Work refs, latest coherent checkpoint and referenced CI runs before any new mutation. Never infer progress from an old ACTIVE status.

**Durable implementation checkpoints are separate from liveness heartbeats.** Following LBS, persist a coherent Work-Branch checkpoint before more than approximately **10–15 minutes of substantive completed implementation** could be lost to transient agent context, and before a long/high-risk sequence when suitable. A checkpoint may be intermediate/RED if explicitly marked; it is not an excuse to skip focused validation or wait for the entire CI matrix. Its commit message identifies Issue/version, main/work SHA, completed work, executed/not-yet-run validation, risks and next action. Prefer one meaningful implementation/checkpoint commit instead of extra no-op metadata commits. A fresh agent must be able to continue without prior chat.

**Terminal audit:** before closing an Issue, the single cumulative comment must have `Agent-State: COMPLETED`, true Work-branch status (including actual deletion), exact merged main and PR, verified machine-test totals/known limitations, failure/correction history, a measurement/evidence audit, and no stale ACTIVE/pending fields. Record any missed heartbeat or checkpoint interval as a process deviation; later GREEN tests do not erase it.

This gate does **not** apply to routine one-commit documentation Fast-Paths. See [Rolling Comment template](templates/WORK_PATH_ROLLING_COMMENT.md) and [migration bootstrap rule](templates/PROJECT_MIGRATION_TEMPLATE.md).

Exactly one cumulative issue comment, updated *in place*, records RHC Issue, base SHA, Work SHA, last checkpoint, target version, allowed diff, risk, validator totals, timings, failures, recovery, Candidate, Release, cleanup and final verification. Singleton headings must not be duplicated. User-visible Work-Chat-ID `RHC<N>CHAT<12 uppercase random hexadecimal digits>` is emitted once per execution chat and recorded; on transfer append a new ID without overwriting origin. Search indexing is not guaranteed. A missing ID is `not issued`, never fabricated. A Work-Path rolling record is not the normal Fast-Path report.

## Autonomous verified cleanup after merge

The owner grants routine development/merge/cleanup authority within the approved work scope, once mandatory CI/quality gates are GREEN. Routine merges do **not** require repeated chat confirmation. Explicit new product/release/signing approvals remain separate. GitHub's global Automatically delete head branches option can remain OFF.

GitHub Actions workflow `.github/workflows/rhc-branch-cleanup.yml` runs after a merged PR to `main`. It uses the dedicated `contents: write` permission strictly for branch ref deletion. The app/source build, CI rehearsal and release-policy workflows remain read-only.

`tools/rhc_branch_cleanup.py` checks the PR's closed/merged status, matching source/target repository, limited branch naming, exact recorded PR head SHA, actual merge commit presence and head ancestry in fresh `main`, and remote branch equality. It deletes only with a Git atomic `--force-with-lease` for the exact reviewed SHA; post-deletion absence is required. A changed, foreign, still-open, squashed-without-ancestry or ambiguous branch fails closed. An already removed branch is an idempotent PASS.

RHC-10 [PR #11](https://github.com/SaschaP1980/RazerHealthCenter/pull/11) **was merged**; its one-time historical catch-up scope covered merged PR #2 (`import/RHC-1-v3.0.8`) and PR #9 (`work/RHC-5`). Any claim that those exact refs were deleted must come from the actual cleanup Actions run **and** a fresh branch-list readback, never just from PR merge or this description. Active `work/RHC-3` and unmerged `license/RHC-6-gpl3` remain protected from that catch-up; any later state change must be checked live.

Manual `workflow_dispatch` with a merged PR number is reserved for fault recovery by the assistant; do not ask the owner to click GitHub for normal development. Do not apply cleanup to candidate/release refs until their separate, verified release orchestration lifecycle is implemented.

## Canonical distribution after RHC-12 owner decision

Use RHC-12's `repo-downloads` model derived from LenovoBootSelector: immutable **lean seven-file** released Portable ZIPs under `main/downloads/`, an append-only `downloads/releases.json` history, generated `downloads/README.md` and a `downloads/latest.json` pointer only once a version has been published. Source is in GitHub and does not belong in the Portable ZIP. New versions must be strictly increasing and previous ZIPs byte-unchanged; tests use `tools/rhc_downloads.py` and a read-only hosted downloads CI workflow. A verified Release PR changes exactly the qualified Candidate's two source-version files (`model.go`, `CHANGELOG.md`) plus the four download/catalog files, atomically moving both app version and public latest; this does not add a Source ZIP. Distinct exact-SHA Linux/Windows infra and Release preflight checks are dispatched explicitly for GitHub-token-created Release PRs. The former GitHub Releases/Draft mechanism was superseded and remains a historical rehearsal only. An Actions QA artifact is not a released package.

Do not create tags, publish a ZIP, advance `latest.json` or enable production release until the real Candidate/Release orchestrator, native/device gates, version-scoped signing/unsigned approval and rollback evidence pass. Routine code/CI merges remain autonomous; release authorization stays distinct.

## RHC-16 four-component application versioning

Current authoritative `model.go` values are both `3.0.8.0`; all future app/release versions must be exactly `MAJOR.MINOR.PATCH.HOTFIX`. HOTFIX starts at 0. Hotfix releases require `Release-Profile: hotfix` and increase only the fourth component by exactly one; a new PATCH resets HOTFIX to 0. Candidate/ref validators reject legacy three-part names. Razer Synapse, Chroma, engine, setup and migration-history version domains are separate and must not be reformatted. Existing unsigned QA `3.0.8` download is immutable and not a production version; canonical `downloads/releases.json` remains empty until a separately authorized release. Historical 321-file/EXE Golden verification stays pinned to the original source ref; current four-part release verification requires current SHA independent builds.

## Validation sequence

1. Read exact current base; identify allowed code/file changes and protected repair/firmware boundaries.
2. Run the focused established Python/Go tests for touched components; for confirmed bugs use RED against the unchanged original basis, then GREEN.
3. Preserve existing `build.sh` validator chain. Go and PowerShell/Windows native checks must be distinguishable. Do not claim Linux cross-build equals native PowerShell 5.1 or physical Razer E2E.
4. Run hosted GitHub Candidate checks on the exact SHA; recheck statuses and parentage before promotion.
5. Publish only through an explicitly implemented and verified RHC release orchestrator with reproducibility, preactivation, single PR/merge, postrelease verification and cleanup.
6. No publication when any mandatory safety/release gate is missing, stale, uncertain or FAILED.

Evidence is additive: retain actual failed attempts, corrections and lesson learned; a later GREEN does not erase an earlier failure.

## RHC-20 release technical authority and recoverability

Autonomously merge normal Work PRs only after real exact-SHA GREEN Linux/Windows gates; no human GitHub code review required. Candidate recovery is read-only (`RHC_CANDIDATE_RECOVERY=READ_ONLY`, `EXPECTED_MAIN_SHA`, `WORK_BRANCH`, `WORK_SHA`): existing refs, live trusted statuses and lost/uncertain dispatch must not provoke a blind replay. No Candidate success authorizes public distribution.

The new Release stage/finish scripts require a separate exact-archive Owner RHC22 consent, native hardware/rollback, signing or specifically approved unsigned+SmartScreen risk, active production policy and effective main PR/status rules. Hosted source/portable/verification statuses are pinned to the Release HEAD, not a synthetic PR merge SHA. Uncertain GitHub writes return ATTENTION. Main ruleset 24701145 currently lacks PR/required checks; this external admin configuration is tracked in #22 and cannot be reported as complete.
