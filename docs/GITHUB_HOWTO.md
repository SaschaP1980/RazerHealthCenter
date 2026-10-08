# RHC — GitHub operating guide

## Current limitation

GitHub `main` is now the **canonical source-of-truth for RHC v3.0.8 source**: 321 original files were imported in PR #2 and exact-byte/Windows-build CI passed. The **future production release pipeline is not activated**; do not mistake the source-intake workflow for release authorization. See `docs/MIGRATION_STATUS.md`.

## Identity and issues

A newly created GitHub Issue #N uses title prefix `[RHC-N]`; `N` is the actual GitHub Issue number, never a separate allocation. Use `work/RHC-N` only for justified Work-Path cases; normal Hotfixes use branchless Candidate preparation. Important labels once provisioned: `priority: high|medium|low`, `dev-path: fast|work-branch`; do not claim labels exist before querying GitHub.

Use the Issue for acceptance, observed failures, causal evidence and performance measurements. For Work-Path, maintain exactly **one cumulative Rolling Build & Release comment**; use searchable `RHC<N>CHAT<12 random uppercase hex characters>` markers posted in the working chat (only after issue number known), preserve original marker through handoffs. IDs are search markers, not private-chat URLs. The normal Fast-Path does **not** require Work-Path rolling heartbeats.

## Every new engineering session

1. Query current `main` and `docs/INITIAL_PROMPT.md`, then repo governance, current Issue and comments.
2. Check whether source import is complete and hosted gates are authoritative.
3. Check version from `model.go`, not LBS `bin/version.json`; classify release level, scope and safety impact.
4. Check remote state immediately before writes; commit atomic reviewed diffs without overwriting concurrent changes.
5. Never invent a GitHub Action run, status, test total, release package URL, tag or SHA. Cite exact hosted logs for machine gate claims.

## Nonpublishing foundation verified; production pipeline remains disabled

Infrastructure PR [#4](https://github.com/SaschaP1980/RazerHealthCenter/pull/4) merged deterministic Go/Windows package checks, hosted Linux/Windows matrix, Work-Path exact-SHA Development Completion, strict atomic Candidate Entry and a release-policy rehearsal. Production policy remains `productionEnabled=false`; Candidate promotion deliberately fails and no Release Orchestrator, tag/pointer activation or postpublication verification is enabled. The frozen original v3.0.8 source and EXE remain historical Golden evidence. RHC-16 migrates current app/reference to four-part 3.0.8.0 while keeping QA archives unchanged.

## Target pipeline, not yet production enabled

- Source intake: exact source manifest and hashes, archive-exclusion policy, Go 1.23.2 Windows binary from clean source, diagnostic/repair validators and PS5.1 evidence.
- Fast-path Candidate: one release-ready current-main-parent candidate commit, complete scope inspected, initial authoritative Linux and Windows gates. No intermediate checkpoint history.
- Work-path Candidate: recoverable `work/RHC-N` checkpoints plus exact-SHA Development Completion, one mutable rolling Issue comment, then a clean current-main-parent Candidate with work provenance.
- Candidate promotion: current-main ancestry and both hosted gates rechecked at exact candidate SHA. Fail closed on stale refs, missing status, version collision or mismatched code.
- Release: reproducible package & source checks, source tag and exact package integrity, single PR, preactivation check that public latest still points to prior version, merge as sole activation switch, postrelease verification and safe branch cleanup.
- Production publishing and the new version metadata/update distribution policy are **not yet implemented**. Do not infer RHC update-pointer semantics from LBS.

## Public source and security

RHC repository was created publicly. Do not import historical diagnostic logs, forensics dumps, personal exports, executable binaries, signing certificates, user accounts or credentials without content classification. An empty regex scan is not a complete privacy/license review. Preserve repair confirmation, allowlists, UAC specificity and post-repair read-only verification. Never introduce an automated native repair step in CI.

GitHub **Stage-1 branch protection is ACTIVE and verified**: [`RHC - Protect main` ruleset #24701145](https://github.com/SaschaP1980/RazerHealthCenter/rules/24701145) targets `~DEFAULT_BRANCH` (currently `main`) with `deletion` and `non_fast_forward` prohibitions, no bypass exceptions, and `branches/main.protected=true`. This prevents regular branch deletion and force pushes, **not** ordinary fast-forward direct pushes. Required pull requests and status checks are **NOT ENABLED** until the RHC release automation is qualified. Recheck branch rules, Actions write scopes, exact mandatory status contexts, secret management and bot permissions prior to enabling production promotion. The legacy branch protection admin endpoint may return 403 from the integration without invalidating the separate readable ruleset.

## Reporting

Use measured wall time anchored to GitHub Issue creation, candidate-run creation, exact gate GREEN, promotion, Release Verification and Issue closure. Do not conflate user-message timestamps, queue time, agent thinking effort or Actions job-runtime. Every error/retry must identify an observed output and cause class. See the reusable intake template.

## Current application version scheme (RHC-16)

Read `model.go` for the current **four-component** `MAJOR.MINOR.PATCH.HOTFIX` version; first migrated source is `3.0.8.0`. Each new Candidate branch and release archive is `candidate/vX.Y.Z.H`, `release/vX.Y.Z.H` and `RazerHealthCenter-Portable-vX.Y.Z.H.zip`. For a hotfix on 3.0.8.0 use 3.0.8.1 and trailer `Release-Profile: hotfix`; it increments only the HOTFIX component exactly once. Existing v3.0.8 QA artifact is historical and must not be renamed or entered into official release indexes. Historical Golden source intake is pinned to PR #2 HEAD; current source goes through the two independently reproducible Go builds and native Windows safety checks. No production release is enabled by this schema migration.
