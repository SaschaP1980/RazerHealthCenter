# RHC — GitHub Operating Guide

This guide specifies **reusable GitHub procedures**, not a pinned repository version or past CI report. Begin with [Initial Prompt](INITIAL_PROMPT.md), then [Git provenance contract](GIT_PROVENANCE_CONTRACT.md). Historical owner decisions, failures and exact run/commit evidence belong in their Issues and Rolling Comments.

## Issue/PR relationship for every change

- First select/create the real responsible Issue `[RHC-N]` and define permitted scope, acceptance criteria and safety/release boundary. Reuse an existing Issue for ongoing work.
- Every changed-file PR, including pure documentation, must **explicitly link at least one responsible Issue in its body**. A title prefix alone does not suffice. Use `Refs #N` for partial scope and `Closes #N` only when verified acceptance is complete. For source/release pairs crosslink the source PR and `sourceSha`.
- Docs-only work uses lightweight `docs/RHC-N-...` branch + exact reviewed PR/merge. It does **not** require Candidate, product version change, Work Rolling heartbeat or release. Direct-to-main updates are no longer the default procedure.
- Major executable work uses a justified `work/RHC-N` and the one persistent Rolling Comment with verified BOOTSTRAP **before** branch/first code commit. Maintain real UTC timestamps, evidence and final disposition. Candidate validators still require actual `RHC-Issue: N` and `Release-Profile` trailers where applicable.
- Record the actual PR URL, head/merged main SHA, tests, cleanup and Issue closure in the Issue or its existing Rolling Comment. If an old direct commit lacks a PR, preserve it as historic gap rather than inventing a mapping.

### Manual first-time setup for new repositories

A **repository administrator** opens **Settings > Actions > General**, finds **Workflow permissions**, selects **Read and write permissions** and **Allow GitHub Actions to create and approve pull requests** only where that architecture is required, then clicks **Save** and independently rereads the setting. A screenshot or saved control is **not proof of effective permission**. Independently verify a scoped actual `GITHUB_TOKEN` PR creation with a nonpublishing test, and clean up only the test's verified refs. Do not enable broad write permissions for repositories that do not need them.

## Live source, public version and permissions

Read current main head and `model.go` for source version; independently check `downloads/latest.json`/`downloads/releases.json`, actual ZIP/hash and immutable source tag/`sourceSha` for latest public version. These can differ. Don't use old Markdown versions, tags by themselves or green Candidate checks as proof of a new release.

The **project** requires Issue-backed PRs, but that is **not proof of server-enforced required-PR ruleset settings**. Fetch current branch ruleset, required statuses and bypass entries. Deletion/non-fast-forward protection alone allows ordinary fast-forward pushes. Changing admin rulesets is separate explicitly authorized scope.

### One-time GitHub Actions PR writer setup

Only repositories that intentionally need an Actions bot to create PRs should have a repository admin configure **Settings → Actions → General → Workflow permissions**, select **Read and write permissions** and **Allow GitHub Actions to create and approve pull requests**, save, and reread. Apply **least-privilege per-job** permissions; do not approve a bot's own PR.

A settings screenshot, saved checkbox or YAML `permissions:` declaration **does not prove effective token rights**. Run a bounded **nonpublishing** test using the real `GITHUB_TOKEN`: create a scratch draft PR, verify true author/base/head and result independently, then close it unmerged and SHA-lease-delete only its scratch branch. If denied, use a separately approved scoped GitHub App or request appropriate admin setup; never invent permission.

Bot-origin PRs/pushes may not automatically trigger normal GitHub PR workflows. Explicit trusted workflow dispatch and exact-SHA status verification are required where the contract says so. `SKIPPED`, cancelled, stale or no-job YAML events cannot be labeled GREEN.

## Validation, publication and cleanup

- Confirm exact main/base/head, Issue links, complete diff, actual hosted Linux and **native Windows PowerShell 5.1** safety results, PR statuses and source ancestry before merge. Merge the expected unchanged head SHA; read back actual merge/main and branch cleanup.
- For Razer repair code preserve explicit user in-app consent, least privilege, PID/allowlist guards, pre-mutation checks and read-only post-repair verification. Do not run actual device repairs in CI.
- Releases use `repo-downloads`: immutable ZIP, latest/releases manifest, source SHA-bound tag, source/release PR provenance and remote postpublication checks. Follow [Release Process](RELEASE_PROCESS.md).
- The owner authorizes technically qualified **unsigned/uncertified interim** releases until expressly revoked, with external hardware/rollback/publisher trust `DEFERRED/NOT_VERIFIED`, not PASS. Standard signed production remains fail-closed under actual live policy.
- After an uncertain GitHub write, reread real remote ref/PR/run before retry; protect divergent/unmerged historical branches and never rewrite an immutable public ZIP or tag. The Work and release branch cleaners have distinct scopes.

Historical details and version-specific test outcomes are found by following **Issue → PR → merged Git commit → manifest/tag** as defined in [Git provenance](GIT_PROVENANCE_CONTRACT.md), not in this manual.
