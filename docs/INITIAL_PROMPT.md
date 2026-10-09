# RHC — Initial Prompt: full live GitHub bootstrap

This **version-neutral entry point** directs a complete **read-only** GitHub bootstrap when a new chat is given this file's URL. Do not choose backlog, create Issues/branches, run mutating workflows, commit, tag or publish without a separate user instruction. Discuss with the owner in German using English technical terms; new GitHub documentation and collaboration are in English.

## Read current GitHub state, not a checkpoint

Use the connected GitHub repository `SaschaP1980/RazerHealthCenter` and current `main`. Read its exact SHA and **complete untruncated recursive tree**, current branches/heads, Issues (open and relevant closed) with full Rolling Comments, open/merged PRs, authentic GitHub Actions jobs/checks at their own SHAs, effective rulesets and permissions where available. Treat earlier chat, archived statuses, old Issue ACTIVE headers and historical files as evidence only.

Reconstruct independently:

1. **Current source/app:** live `main/model.go` constants `appVersion` and `referenceVersion`, plus current `CHANGELOG.md`. Never use the latest commit title as the version.
2. **Latest public release:** `downloads/latest.json` together with append-only `downloads/releases.json`, actual archived ZIP bytes/hash/size, and the immutable version source tag. Validate `sourceSha` and tag target. `main` may be ahead of the published source; a tag, Candidate or QA package alone does not prove publication.
3. **Change provenance:** real Git commit/merge lineage → source and release PRs → explicitly linked responsible Issues → historical decisions, RED/GREEN and run results in Issue Rolling Comments. Follow [Git provenance contract](GIT_PROVENANCE_CONTRACT.md). Report absent PR links or old direct commits truthfully, without inventing a chain.
4. **Release permission:** live `config/rhc-release-policy.json`, current executable tests/workflows, and latest owner Issue decisions. The standard signed/certified controller is separate from owner-authorized interim unsigned distribution. External Razer hardware/rollback/publisher trust may be DEFERRED without being PASS.

## Independent public ZIP byte evidence without a chat-side binary download

The connected GitHub API may reject direct binary ZIP downloads (large/non-UTF-8 payload). **This is a chat transport limitation, not an integrity failure.** Never invent a local checksum or conclude the public ZIP is corrupt merely because the connector cannot return its binary bytes. Instead, use the version-neutral hosted read-only fallback:

1. Independently read the **current main SHA** and `downloads/latest.json` / `downloads/releases.json`, validate the indexed archive name, expected SHA-256, size and immutable source tag. Keep the source/tag evidence separate from the binary evidence.
2. Inspect the actual GitHub Actions **[RHC Repository Downloads Integrity (nonpublishing)](../.github/workflows/rhc-downloads-verify.yml)** workflow and find a **completed SUCCESS** `push` or `workflow_dispatch` run pinned to **that exact main commit SHA**, with successful job `Validate ZIP manifest and unmodified release history`. Its logs must contain `RHC_PUBLIC_BINARY_READBACK=` with `result=PASS`, selected `version`, `filename`, `bytes`, `sha256`, `commitSha`, `transport=HTTPS_GITHUB_RAW_EXACT_COMMIT` and `scope=REMOTE_PUBLIC_BINARY_BYTES_ONLY_NOT_SIGNING_OR_HARDWARE`. Verify these against the live catalog. This runner **independently fetched the immutable HTTP ZIP bytes**, checked exact length/SHA and the internal seven-file checksums; ChatGPT itself did **not** download the ZIP.
3. If no matching fresh run exists, do not substitute a prior-version run or an unexecuted workflow definition. The owner may use **Actions → RHC Repository Downloads Integrity (nonpublishing) → Run workflow → main**, with `version` blank for latest or a four-part indexed version for history. After execution, independently read back its exact main SHA, jobs and logs. If workflow invocation is unavailable to the connected chat, state the blocker and present the owner UI steps; do not claim dispatch or PASS.
4. Keep evidence classes distinct: `HOSTED_REMOTE_BYTES_VERIFIED` requires a real successful exact-SHA **HTTPS readback**, `CHECKOUT_ZIP_BYTES_VERIFIED` covers the existing real Git-checkout archive validator, and `CHAT_BINARY_DOWNLOAD_UNAVAILABLE` means only that ChatGPT cannot itself fetch the bytes. If hosted fetch fails/is SKIPPED/stale or lacks a matching digest, say `HOSTED_REMOTE_BINARY_NOT_VERIFIED` or `INTEGRITY_FAILED` as appropriate, not PASS. A trusted Windows publisher, physical Razer acceptance, signing and rollback remain separate checks.

This fallback works without hardcoded version numbers, downloads, tag names, Issue numbers or run IDs and does not require a product build, repository mutation or new release.

## Recursively read actual documentation and code

Enumerate **every** `docs/**/*.md` in the live Git tree, including templates, archives and new nested files. Read each document completely before development/release judgments; do not rely on a frozen inventory or fixed document count. Canonical operating contracts are:

- [Git provenance](GIT_PROVENANCE_CONTRACT.md): Issue–PR traceability and version-to-source relationships.
- [Development Guidelines](DEVELOPMENT_GUIDELINES.md): docs-only PRs, Fast-/Work-Paths, rolling recovery and test-first.
- [GitHub How-To](GITHUB_HOWTO.md): permissions, branch protection, Issues, CI and reporting.
- [Release Process](RELEASE_PROCESS.md) and [Reusable Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md): immutable packaging, technical release checks, standard/interim boundaries.
- [Migration Evidence Locator](MIGRATION_STATUS.md), [Rolling Comment Template](templates/WORK_PATH_ROLLING_COMMENT.md), [Project Migration Template](templates/PROJECT_MIGRATION_TEMPLATE.md) and all other files discovered live. Explicitly historical documents are not automatically current policy.

Read current `README.md`, `go.mod`, `build.sh`, `model.go`, `SAFETY-MODEL.txt`, `SOURCE-DELIVERY-CONTRACT.md`, `config/rhc-release-policy.json`, relevant `tools/` and `tests/` (especially Candidate, downloads, branch cleanup and release validators), and **all** `.github/workflows/*.yml`. Check real trigger/permission scope, negative tests, source and staged SHA, Linux Windows crossbuild, hosted native Windows PowerShell 5.1, Candidate, Development Completion, interim publisher/postmerge, downloads verification and cleanup. Executable contracts outrank outdated historical prose. Never invent an LBS-only tool or a passing test.

## Development and safety rules

**Every future changed-file PR requires at least one responsible `[RHC-N]` Issue linked in its PR body.** For documentation-only scope use a lightweight Issue-backed branch and PR, without a product Candidate/Work-Path/version increment; no routine direct-main docs commit. Work-Path executable changes require **creating the complete, unabridged [Rolling Comment template](templates/WORK_PATH_ROLLING_COMMENT.md) as one persisted BOOTSTRAP Issue comment before the branch and first code change**, independently read back, then maintaining every original section, heartbeat, measurement ledger and exact-SHA evidence in that same comment. **Before Issue closure, audit all required headings/fields and true N/A reasons against the complete template; a self-composed abbreviated summary is noncompliant.** Product Candidates require actual executable `RHC-Issue: N` and `Release-Profile` contracts. Issue-only decisions without changed files do not need a PR.

Confirmed executable defects require meaningful unfixed-SHA RED then focused GREEN and a real consumer test. Differentiate local/static, hosted Linux Windows build, **hosted native Windows** and real physical Razer tests. Do not treat skipped, cancelled, failed or stale status as PASS. Version format `MAJOR.MINOR.PATCH.HOTFIX` is a schema, not a current version.

Diagnostics must remain read-only. Razer repairs need explicit in-app confirmation, validated payload/recipe/PID/allowlist, least privilege and pre-mutation checks with read-only postrepair verification. Ambiguity must not yield false HEALTHY. CI must not perform actual user-machine repairs.

The standing owner direction permits technically qualified **unsigned/uncertified interim releases until expressly revoked**. Disclose unknown publisher/SmartScreen risk, mark external physical Razer/rollback/trust tests DEFERRED/NOT_VERIFIED and keep the separate standard signed-production policy fail-closed. Preserve real hosted Linux/native Windows repair safety, deterministic PE/ZIP builds, immutable previous releases, staged release PR/merge, source-tag readback and lease-checked cleanup. No new release is authorized merely by reading this file.

### Default interpretation of a subsequent new-version build command

A **link-only initial bootstrap is read-only** and must not start a release. After initialization, a separate **owner command to build/create/increment a new application version** is **implicitly an authorization for the full autonomous Develop → Build → Candidate → public interim Release → postrelease verification**, even if "release" is not written. Do not ask the owner to repeat publication permission for each new qualifying version: the existing **until-revoked unsigned/uncertified interim authorization** applies. A requested Work-Branch Path remains mandatory with the **complete pre-branch Rolling Comment template**, Development Completion and real exact-SHA Linux/hosted-native-Windows qualification. Successful completion requires the new immutable ZIP in `main/downloads/`, updated latest/releases catalog and README, source tag, source and publication PRs, verified remote bytes/history and actual branch cleanup; a green build/Candidate is not the requested final result.

This default does **not** apply to merely reading this prompt, a docs/QA/test task, recompiling an unchanged version or an express build-only/no-publish direction. A revoked authorization or missing/failed gate must yield `BLOCKED/NEEDS_ATTENTION`, never fabricated publication. Do not weaken the distinct signed production policy, Razer repair safety or external `DEFERRED/NOT_VERIFIED` disclosures. See [Development Guidelines](DEVELOPMENT_GUIDELINES.md), [Release Process](RELEASE_PROCESS.md) and [Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md).

## Recovery and reporting

Before a risky write, and after interruption, independently reload exact main/target refs, Issue/Rolling Comment, PR head, CI status and policy. An Actions YAML permission is not proof of effective API rights; verify actual create-PR/dispatch behavior if needed. Required PR policy may not be enforced by the present GitHub ruleset; verify live and report the gap.

For bootstrap, report live main SHA, source version, published version/ZIP/source tag or verified absence, standard policy versus interim mode, active branches/PRs/Issues, precise CI evidence, externally deferred gates and any conflicts/gaps. Include GitHub links. **Never insert current-version numbers, release hashes, old run IDs or terminal Issue status snapshots into this document.**
