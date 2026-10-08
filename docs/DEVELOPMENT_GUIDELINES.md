# RHC — Development guidelines

> **Target operating contract; production release automation is not ready until the migration acceptance gates are met.**

## Authority

Use current GitHub `main` plus Issues as the canonical working record: **source import and hosted baseline verification completed in PR #2**. The separate production Candidate/Release infrastructure is still unimplemented; `docs/MIGRATION_STATUS.md` records those open gates. Never use another project's main branch or private conversation memory as RHC runtime authority.

## Preserve product invariants

The Go Razer Health Center includes PowerShell diagnostic and repair scripts. Functional work must retain explicit repair approval, product-specific least privilege, no automated elevation, narrowly authorized service/user-mode restarts, pre-mutation rechecks, post-mutation read-only verification, PID ambiguity guards and false-GREEN protections. Only regress expected product behavior with a proven test. No production interaction with the user's Razer hardware during hosted CI.

## Version and development path

Current version input is `model.go` with `appVersion` and `referenceVersion`; release level uses the product's actual version contract, not LBS's 4-part version by default. Any later schema change requires an explicit tested migration.

- Documentation-only: one atomic documented change on a fresh verified base; no product version bump, Candidate or Release.
- Narrow Patch/Hotfix: branchless Fast-Path by default; test a confirmed failure RED where applicable, fix, run relevant focused GREEN/syntax/determinism checks, create **one exact release-ready candidate** on current `main`, inspect complete diff, then hosted Candidate Preflight.
- Major/Minor or substantial risk/migration: persistent `work/RHC-<issue>` with scoped checkpoints, exact-SHA Development Completion and Candidate Entry before any Candidate.
- Process benchmarking Work-Path for an otherwise simple Hotfix requires explicit user permission, a durable exception reason and same exact-SHA qualification gates. Never escalate merely to have more commits.
- For Issue-backed implementation use exactly one valid `dev-path: fast` or `dev-path: work-branch` label once labels are installed.

## Work-Path rolling record

**Work-Path bootstrap is a fail-closed prerequisite, not end-of-run paperwork.** For any authorized Issue-backed Work-Path:

1. Verify Issue, owner authorization, fresh main SHA, version and approved/forbidden paths; an unborn repo may require an initial minimal bootstrap commit solely to obtain a real main SHA.
2. **Before the Work branch, first code/workflow change, Work PR or related CI**, create the **single** Issue Rolling Comment in phase `BOOTSTRAP` with planned branch `NOT CREATED`, main SHA checkpoint, scope, risks and exact next action.
3. Read the comment back through GitHub; validate its ID, persisted content, actual millisecond UTC heartbeat and `created_at`/`updated_at`. If absent, inconsistent or unverifiable, **STOP** before branch creation.
4. Create the Work branch from the still-current SHA, re-read its head, update and re-read the **same comment before the first code commit**. If this fails, **BLOCKED**.
5. Refresh exact work/main/CI checkpoints before consequential next actions and after significant commits. After interruptions re-fetch authoritative state instead of guessing. Record late initial comments as process violations regardless of GREEN tests.

This gate does **not** apply to routine one-commit documentation Fast-Paths. See [Rolling Comment template](templates/WORK_PATH_ROLLING_COMMENT.md) and [migration bootstrap rule](templates/PROJECT_MIGRATION_TEMPLATE.md).

Exactly one cumulative issue comment, updated *in place*, records RHC Issue, base SHA, Work SHA, last checkpoint, target version, allowed diff, risk, validator totals, timings, failures, recovery, Candidate, Release, cleanup and final verification. Singleton headings must not be duplicated. User-visible Work-Chat-ID `RHC<N>CHAT<12 uppercase random hexadecimal digits>` is emitted once per execution chat and recorded; on transfer append a new ID without overwriting origin. Search indexing is not guaranteed. A missing ID is `not issued`, never fabricated. A Work-Path rolling record is not the normal Fast-Path report.

## Validation sequence

1. Read exact current base; identify allowed code/file changes and protected repair/firmware boundaries.
2. Run the focused established Python/Go tests for touched components; for confirmed bugs use RED against the unchanged original basis, then GREEN.
3. Preserve existing `build.sh` validator chain. Go and PowerShell/Windows native checks must be distinguishable. Do not claim Linux cross-build equals native PowerShell 5.1 or physical Razer E2E.
4. Run hosted GitHub Candidate checks on the exact SHA; recheck statuses and parentage before promotion.
5. Publish only through an explicitly implemented and verified RHC release orchestrator with reproducibility, preactivation, single PR/merge, postrelease verification and cleanup.
6. No publication when any mandatory safety/release gate is missing, stale, uncertain or FAILED.

Evidence is additive: retain actual failed attempts, corrections and lesson learned; a later GREEN does not erase an earlier failure.
