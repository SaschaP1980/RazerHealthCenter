## Manual first-time setup for new repositories — GitHub Actions PR creation

**Required prerequisite for repositories using an autonomous GitHub Actions workflow that creates pull requests** (such as the RHC reusable interim release publisher). This setting belongs to the repository's initial manual administrator checklist: it is **not enabled automatically** by a workflow, importing source code, cloning a template, creating a branch, or writing `permissions:` into YAML.

1. Sign in to GitHub as a **repository administrator** (or an organization administrator authorized to change Actions settings) and open the new repository.
2. Navigate to **Settings > Actions > General**. Scroll to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Enable **Allow GitHub Actions to create and approve pull requests**.
5. Click **Save**. Reopen the page and confirm that both selected values persisted. If either control is unavailable or disallowed by an organization/enterprise policy, do not claim successful setup: obtain the appropriate administrator decision or configure an explicitly approved, least-privilege GitHub App.
6. Keep individual workflows' `permissions:` blocks as narrow as the job needs (for example, `contents: write` and `pull-requests: write` for the authorized PR writer; `actions: write` only when dispatch is required). The checkbox authorizes PR creation but **does not require, imply, or justify bot approval** of its own PRs.
7. **Verify effective rights separately:** perform a bounded, **nonpublishing** `GITHUB_TOKEN` PR-creation test from a real GitHub Actions job against an expendable, specifically named test branch; read back the actual PR actor, head/base SHA and run result; safely close/delete only verified test refs. A saved UI selection or successful branch push is **not proof of effective permission**. Do not trigger a new product release merely to test this setting.

**Security scope:** These broad default rights are **only for repositories requiring GitHub Actions to create PRs** under the chosen architecture. **Do not enable broad write permissions for repositories that do not need them**; prefer read-only defaults and narrowly scoped job permissions or a dedicated GitHub App instead. Required organization policies take precedence.

**RHC-43 evidence (2026-10-09):** **Owner-confirmed Save on 2026-10-09** — the owner displayed both selected controls and explicitly confirmed clicking Save. **Effective PR creation: NOT YET VERIFIED** after that change. The earlier real `GITHUB_TOKEN` `createPullRequest` denial (release Stage job 113702589715) remains a genuine historical finding, not a currently proven ongoing denial. The v3.0.8.2 release was completed safely using a separately authorized GitHub App for PR creation. Keep [RHC-43](https://github.com/SaschaP1980/RazerHealthCenter/issues/43) open until the new setting's effective write behavior is independently demonstrated.

---
## Active operating status — RHC-43 / English GitHub policy (October 2026)

All new GitHub development communication and normative project documentation are written in **English**; owner-facing conversation remains **German with English engineering terminology**. Read actual current app/reference version from model.go, last public version from downloads/latest.json/releases.json, current main SHA and exact GitHub refs rather than relying on an old frozen version in this guide.

The owner requests a **repeatable technical interim-unsigned Development → Build → Release cycle**, not a one-off v3.0.8.1 publisher. Its implementation, real CI/PR-permission proof and GitHub remote postrelease verification are tracked in [RHC-43](https://github.com/SaschaP1980/RazerHealthCenter/issues/43). RHC-41 is the separate v3.0.8.2 product version-only Work/qualified Candidate. Historical v3.0.8.1 writer/prepublication rehearsal are archived for explicit invocation only; they must not cause ordinary later hotfix PRs to fail. Do not call a Candidate or QA artifact a release, and never override unverified safety/owner/external acceptance as PASS.

See [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md), [RELEASE_PROCESS.md](RELEASE_PROCESS.md) and [REUSABLE_INTERIM_RELEASE_CONTRACT.md](REUSABLE_INTERIM_RELEASE_CONTRACT.md). The old version snapshot in the guide below is historical, not current operating state.

---
# RHC — GitHub operating guide

## Current limitation

Current GitHub `main` is the **development source authority**: app/reference version is `3.0.8.0` after RHC-16. The 321-file v3.0.8 source imported and hosted-tested in PR #2 is **historical Golden evidence**, not current-version build or publication authorization. Production promotion/Release Orchestrator remains disabled. See [`MIGRATION_STATUS.md`](MIGRATION_STATUS.md) and [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md).

## Identity and issues

A newly created GitHub Issue #N uses title prefix `[RHC-N]`; `N` is the actual GitHub Issue number, never a separate allocation. Use `work/RHC-N` only for justified Work-Path cases; normal Hotfixes use branchless Candidate preparation. Labels were provisioned during migration; recheck actual current metadata before assigning `priority: critical|high|medium|low` or `dev-path: fast|work-branch`. Only Issue-backed **executable** work requires one `dev-path`; documentation/backlog does not.

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
- **Distribution architecture** is already selected as RHC-12 `repo-downloads` with read-only catalog checks; full production Candidate promotion, Release Orchestrator, source tag, publication PR/preactivation/postverification, signing or artifact-specific unsigned consent, rollback and native Razer acceptance remain **incomplete**. GitHub Releases/Draft delivery is superseded; no updater.

## Current Candidate and continuity contracts

A fresh chat must follow [`INITIAL_PROMPT.md`](INITIAL_PROMPT.md), all normative documentation and actual executable contracts; simply reading the entry point does not authorize arbitrary Issues/changes. A pure documentation-only diff uses one atomic reviewed guarded `main` commit, without Work-Path, version or Candidate; changed code, workflow, tools, tests or machine-readable inputs are **not** documentation-only.

A Candidate needs changed `model.go` and `CHANGELOG.md` (absent at present), exactly one real `RHC-Issue: N` **including Hotfix**, and `Release-Profile: version-only|patch|hotfix`. `version-only` is exactly the two-file diff; HOTFIX increases component four by one. Unforeseen Candidate failures are corrected, if within scope, on the **same** Candidate branch and re-qualified at its new SHA, never bypassing the deliberately blocked promotion. Issue closure and durable GitHub recovery comments require genuine acceptance and evidence, not old chat memory.

## Public source and security

RHC repository was created publicly. Do not import historical diagnostic logs, forensics dumps, personal exports, executable binaries, signing certificates, user accounts or credentials without content classification. An empty regex scan is not a complete privacy/license review. Preserve repair confirmation, allowlists, UAC specificity and post-repair read-only verification. Never introduce an automated native repair step in CI.

GitHub **Stage-1 branch protection is ACTIVE and verified**: [`RHC - Protect main` ruleset #24701145](https://github.com/SaschaP1980/RazerHealthCenter/rules/24701145) targets `~DEFAULT_BRANCH` (currently `main`) with `deletion` and `non_fast_forward` prohibitions, no bypass exceptions, and `branches/main.protected=true`. This prevents regular branch deletion and force pushes, **not** ordinary fast-forward direct pushes. Required pull requests and status checks are **NOT ENABLED** until the RHC release automation is qualified. Recheck branch rules, Actions write scopes, exact mandatory status contexts, secret management and bot permissions prior to enabling production promotion. The legacy branch protection admin endpoint may return 403 from the integration without invalidating the separate readable ruleset.

## Reporting

Use measured wall time anchored to GitHub Issue creation, candidate-run creation, exact gate GREEN, promotion, Release Verification and Issue closure. Do not conflate user-message timestamps, queue time, agent thinking effort or Actions job-runtime. Every error/retry must identify an observed output and cause class. See the reusable intake template.

## Current application version scheme (RHC-16)

Read `model.go` for the current **four-component** `MAJOR.MINOR.PATCH.HOTFIX` version; first migrated source is `3.0.8.0`. Each new Candidate branch and release archive is `candidate/vX.Y.Z.H`, `release/vX.Y.Z.H` and `RazerHealthCenter-Portable-vX.Y.Z.H.zip`. For a hotfix on 3.0.8.0 use 3.0.8.1 and trailer `Release-Profile: hotfix`; it increments only the HOTFIX component exactly once. Existing v3.0.8 QA artifact is historical and must not be renamed or entered into official release indexes. Historical Golden source intake is pinned to PR #2 HEAD; current source goes through the two independently reproducible Go builds and native Windows safety checks. No production release is enabled by this schema migration.
