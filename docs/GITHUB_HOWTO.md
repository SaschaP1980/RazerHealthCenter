# RHC — GitHub operating guide

## Current limitation

GitHub is the intended canonical project authority. **The source import is pending**; do not mistake initial process documentation for complete project contents. See `docs/MIGRATION_STATUS.md`.

## Identity and issues

A newly created GitHub Issue #N uses title prefix `[RHC-N]`; `N` is the actual GitHub Issue number, never a separate allocation. Use `work/RHC-N` only for justified Work-Path cases; normal Hotfixes use branchless Candidate preparation. Important labels once provisioned: `priority: high|medium|low`, `dev-path: fast|work-branch`; do not claim labels exist before querying GitHub.

Use the Issue for acceptance, observed failures, causal evidence and performance measurements. For Work-Path, maintain exactly **one cumulative Rolling Build & Release comment**; use searchable `RHC<N>CHAT<12 random uppercase hex characters>` markers posted in the working chat (only after issue number known), preserve original marker through handoffs. IDs are search markers, not private-chat URLs. The normal Fast-Path does **not** require Work-Path rolling heartbeats.

## Every new engineering session

1. Query current `main` and `docs/INITIAL_PROMPT.md`, then repo governance, current Issue and comments.
2. Check whether source import is complete and hosted gates are authoritative.
3. Check version from `model.go`, not LBS `bin/version.json`; classify release level, scope and safety impact.
4. Check remote state immediately before writes; commit atomic reviewed diffs without overwriting concurrent changes.
5. Never invent a GitHub Action run, status, test total, release package URL, tag or SHA. Cite exact hosted logs for machine gate claims.

## Target pipeline, not yet production enabled

- Source intake: exact source manifest and hashes, archive-exclusion policy, Go 1.23.2 Windows binary from clean source, diagnostic/repair validators and PS5.1 evidence.
- Fast-path Candidate: one release-ready current-main-parent candidate commit, complete scope inspected, initial authoritative Linux and Windows gates. No intermediate checkpoint history.
- Work-path Candidate: recoverable `work/RHC-N` checkpoints plus exact-SHA Development Completion, one mutable rolling Issue comment, then a clean current-main-parent Candidate with work provenance.
- Candidate promotion: current-main ancestry and both hosted gates rechecked at exact candidate SHA. Fail closed on stale refs, missing status, version collision or mismatched code.
- Release: reproducible package & source checks, source tag and exact package integrity, single PR, preactivation check that public latest still points to prior version, merge as sole activation switch, postrelease verification and safe branch cleanup.
- Production publishing and the new version metadata/update distribution policy are **not yet implemented**. Do not infer RHC update-pointer semantics from LBS.

## Public source and security

RHC repository was created publicly. Do not import historical diagnostic logs, forensics dumps, personal exports, executable binaries, signing certificates, user accounts or credentials without content classification. An empty regex scan is not a complete privacy/license review. Preserve repair confirmation, allowlists, UAC specificity and post-repair read-only verification. Never introduce an automated native repair step in CI.

GitHub repository administrator configuration (branch protection, Actions write scopes, required status checks, secret management) requires independent inspection and potentially explicit owner configuration. A connected GitHub App's write permission does not prove branch protection is configured.

## Reporting

Use measured wall time anchored to GitHub Issue creation, candidate-run creation, exact gate GREEN, promotion, Release Verification and Issue closure. Do not conflate user-message timestamps, queue time, agent thinking effort or Actions job-runtime. Every error/retry must identify an observed output and cause class. See the reusable intake template.
