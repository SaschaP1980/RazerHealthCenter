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

## Issue label taxonomy

Use independent dimensions for **type**, **priority**, **development path**, and optional **work area**. Do not substitute one for another or silently relabel historical closed Issues.

- **Type:** `bug` for a defect in existing behavior; `enhancement` for new capabilities, refactoring and planned process or infrastructure improvements. Select the type that describes the actual issue; `dev-ops` is **not** a type replacement.
- **Priority:** Every open Issue should have exactly one current `priority: critical`, `priority: high`, `priority: medium`, or `priority: low`. Reassess as impact changes; priority is independent of type and other labels.
- **Development path:** `dev-path: fast` and `dev-path: work-branch` are mutually exclusive. Select at most one when an executable change's path is decided; documentation-only changes do not require either.
- **Special disposition:** `wontfix` denotes deliberately not planned work; GitHub open/closed state and closure reason remain separate.
- **Optional work area — `dev-ops`:** Use for CI/CD, GitHub Actions, build/release automation, developer tooling, workflow reliability, infrastructure, and development operations. This label can coexist with `bug`/`enhancement`, one `priority:*`, and an applicable `dev-path:*`; it is not a severity, implementation path, approval, or safety/production-release gate. Do not require it for unrelated product or UI Issues.

The owner-added RHC label's exact GitHub metadata is **name `dev-ops`**, **hex color `c4907e`**, **description `Development Operations or CI/CD related`**. The other nine standard labels originate from the [LenovoBootSelector Issue-label taxonomy](https://github.com/SaschaP1980/LenovoBootSelector/blob/main/docs/GITHUB_HOWTO.md); `dev-ops` is a separately owner-defined, tenth **migration default**, not an invented LenovoBootSelector donor label. The [project migration template](templates/PROJECT_MIGRATION_TEMPLATE.md) documents the full reference catalog and the idempotent provisioning procedure. Documentation alone does not create, delete or reassign any GitHub Issue label.

## Live source, public version and permissions

Read current main head and `model.go` for source version; independently check `downloads/latest.json`/`downloads/releases.json`, actual ZIP/hash and immutable source tag/`sourceSha` for latest public version. These can differ. Don't use old Markdown versions, tags by themselves or green Candidate checks as proof of a new release.

The **project** requires Issue-backed PRs, but that is **not proof of server-enforced required-PR ruleset settings**. Fetch current branch ruleset, required statuses and bypass entries. Deletion/non-fast-forward protection alone allows ordinary fast-forward pushes. Changing admin rulesets is separate explicitly authorized scope.

### One-time GitHub Actions PR writer setup

Only repositories that intentionally need an Actions bot to create PRs should have a repository admin configure **Settings → Actions → General → Workflow permissions**, select **Read and write permissions** and **Allow GitHub Actions to create and approve pull requests**, save, and reread. Apply **least-privilege per-job** permissions; do not approve a bot's own PR.

A settings screenshot, saved checkbox or YAML `permissions:` declaration **does not prove effective token rights**. Run a bounded **nonpublishing** test using the real `GITHUB_TOKEN`: create a scratch draft PR, verify true author/base/head and result independently, then close it unmerged and SHA-lease-delete only its scratch branch. If denied, use a separately approved scoped GitHub App or request appropriate admin setup; never invent permission.

Bot-origin PRs/pushes may not automatically trigger normal GitHub PR workflows. Explicit trusted workflow dispatch and exact-SHA status verification are required where the contract says so. `SKIPPED`, cancelled, stale or no-job YAML events cannot be labeled GREEN.

## Release publisher versus independent postrelease verifier

For a new qualified interim version the Candidate's exact-SHA Linux/native Windows preflight triggers the [reusable single-PR publisher](../.github/workflows/rhc-reusable-interim-release.yml); the publisher merges **one combined** Candidate-source+four-downloads PR, then dispatches [RHC Independent Postrelease Verification](../.github/workflows/rhc-postrelease-verification.yml) on the **merged main SHA**. Its expected inputs are `expected_main_sha`, `expected_source_sha`, `version` and `expected_release_pr`. Independently inspect the `workflow_dispatch` run, its head SHA, event, complete **three-job** result and logs, not just the publisher's green summary. A genuine PASS requires `RHC102_INDEPENDENT_HTTPS=PASS` (actual remote ZIP), `RHC102_INDEPENDENT_WINDOWS=PASS` (hosted native PE/repair safety) and `RHC102_INDEPENDENT_POSTRELEASE=PASS` (aggregate), as well as the publisher's `RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS`. Verify real CI job status/conclusion and matching exact release lineage.

`action_required`, zero jobs, skipped/cancelled jobs, stale commits, pending runs, missing binary evidence and local/checkout-only checks **never** establish that the independent release cycle finished. A GitHub-bot PR webhook is not a replacement for the trusted exact-main `workflow_dispatch`. The verifier's narrow PR-close entry for RHC-102 itself is historical infrastructure acceptance only. If a publisher merged but verification or cleanup failed, report the actual partial state `BLOCKED/NEEDS_ATTENTION`; do not rerun a mutation without readback of remote refs. See [release contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md). A future fresh-release repeatability test remains separate ([RHC-105](https://github.com/SaschaP1980/RazerHealthCenter/issues/105)).

### RHC-110 automatic corrective recheck (no additional release)

The default path is automatic: after merging a reviewed, Issue-backed **verification-only Work PR**, the [verified branch cleanup](../.github/workflows/rhc-branch-cleanup.yml) finishes and [the read-only RHC-110 controller](../.github/workflows/rhc-postrelease-recheck.yml) is notified by a trusted `workflow_run` completion. A bounded hourly schedule can recover missed bot-origin webhook activity; optional manual controller `workflow_dispatch` selects an exact corrective PR without overriding fail-closed guards. The controller checks exact merged `main`/PR/issue/review/Work Linux+Windows jobs, preserves public ZIP and source tag, finds the historical failed RHC-102 run, rejects already-dispatched current-main verification and refuses publication activity.

On eligibility, Actions' limited `actions:write` identity dispatches `rhc-postrelease-verification.yml` on `main` with `expected_main_sha` = corrected current SHA, `expected_source_sha` = original immutable tagged source SHA, `version` = unchanged latest version and `expected_release_pr` = **original** source+downloads PR (never the corrective PR). Confirm the exact genuine three completed-success Linux HTTPS/native Windows/aggregate jobs; a failed or missing job remains BLOCKED. See [RHC-110](https://github.com/SaschaP1980/RazerHealthCenter/issues/110) for actual run IDs; this recovery is read-only and must not backdate the original release's failed postrelease result.

## Independent published ZIP readback when the GitHub connector cannot download binaries

For release auditing and new-chat bootstraps, **do not infer an archive failure from a chat-side binary-download block**. The GitHub connector may read commit, tag and catalog metadata but may refuse a multi-megabyte ZIP. The repository's read-only [Downloads Integrity workflow](../.github/workflows/rhc-downloads-verify.yml) is a separate **nonpublishing audit fallback** and can verify actual published bytes on a hosted Ubuntu runner. It does **not** by itself replace the three-job independent postrelease verifier required for a newly published version.

- First verify current `main` SHA, `downloads/latest.json`, full `releases.json` and expected source tag. The existing local `tools/rhc_downloads.py` checks actual committed ZIP SHA-256, archive size, payload allowlist, embedded checksums and full publication history.
- For **additional independent HTTP transport evidence**, require a real SUCCESS run of **RHC Repository Downloads Integrity (nonpublishing)** at the **identical immutable public main commit**, whose logs show `RHC_PUBLIC_BINARY_READBACK=` with matching version, filename, size, SHA-256 and `commitSha`; verify the run's event (`push` on main or `workflow_dispatch` on main), three-part provenance (catalog, actual remote HTTP bytes, exact Git SHA) and outcome. A PR-only checkout validation is **not** proof of the publicly fetched HTTP artifact.
- For an optional fresh audit, manually run it at **Actions → RHC Repository Downloads Integrity (nonpublishing) → Run workflow → main**; leave optional `version` blank for latest or set the precise indexed four-part version to verify an older published archive. A connected chat without an Actions-dispatch capability must direct the owner to the UI rather than claim it started the job. The Actions job has `contents: read` and publishes nothing.
- The readback tool `tools/rhc_remote_binary_verify.py` fetches the exact GitHub `raw.githubusercontent.com/<owner>/<repo>/<commitSha>/downloads/<version>.zip` URL from an HTTPS runner, checks remote bytes/size/SHA, verifies the seven-file ZIP and `SHA256SUMS.txt`, and fails closed for corrupt/missing/network-blocked responses. No ZIP bytes are uploaded back to ChatGPT; GitHub logs expose only verified metadata.
- Report separately: `CHAT_BINARY_DOWNLOAD_UNAVAILABLE` (chat connector), `CHECKOUT_ZIP_BYTES_VERIFIED` (existing actual git archive validation), and `HOSTED_REMOTE_BYTES_VERIFIED` (real exact-SHA raw HTTP request). An inaccessible or missing/stale/failed hosted job is `HOSTED_REMOTE_BINARY_NOT_VERIFIED` rather than PASS. Tampered, mismatched or unsafe packages are `INTEGRITY_FAILED`. No code path can turn unsigned, external hardware, native rollback, publisher trust or standard signed-production gates to PASS.

Never pin this normative workflow to a current app version, last CI ID or catalog ZIP hash; those must always be obtained from the live GitHub state.

## Validation, publication and cleanup

- Confirm exact main/base/head, Issue links, complete diff, actual hosted Linux and **native Windows PowerShell 5.1** safety results, PR statuses and source ancestry before merge. Merge the expected unchanged head SHA; read back actual merge/main and branch cleanup.
- For Razer repair code preserve explicit user in-app consent, least privilege, PID/allowlist guards, pre-mutation checks and read-only post-repair verification. Do not run actual device repairs in CI.
- Releases use `repo-downloads`: immutable ZIP, latest/releases manifest, source SHA-bound tag, source/release PR provenance and remote postpublication checks. Follow [Release Process](RELEASE_PROCESS.md).
- The owner authorizes technically qualified **unsigned/uncertified interim** releases until expressly revoked, with external hardware/rollback/publisher trust `DEFERRED/NOT_VERIFIED`, not PASS. Standard signed production remains fail-closed under actual live policy.
- After an uncertain GitHub write, reread real remote ref/PR/run before retry; protect divergent/unmerged historical branches and never rewrite an immutable public ZIP or tag. The Work and release branch cleaners have distinct scopes.

Historical details and version-specific test outcomes are found by following **Issue → PR → merged Git commit → manifest/tag** as defined in [Git provenance](GIT_PROVENANCE_CONTRACT.md), not in this manual.

## RHC-76 — process hardening and DevOps incident handling

Owner implementation request: [RHC-76](https://github.com/SaschaP1980/RazerHealthCenter/issues/76).
This maintenance Work-Path is **nonpublishing** and preserves unchanged public
ZIPs, source tags, product version, Razer repair consent/UAC and the standard
signed-production guard.

- **F1 / source→release provenance:** Resolve the responsible Issue solely
  from the real merged source PR on the exact source merge SHA, verified
  original Work-head `RHC-Issue: N` and `Release-Profile: version-only`
  commit trailer, linked PR body and live Issue. Carry the validated identity
  through staged commit, release PR title/body and final merge title; fail
  closed before any release branch push if inconsistent. No static RHC-34.
- **F2 / actual hosted gates:** Bot-created PR workflows can show
  `action_required` and zero jobs. That is **not PASS**. The publisher
  independently dispatches real Infrastructure and Downloads CI and verifies
  exact stage SHA, `workflow_dispatch`, completed success and required real
  hosted jobs, including native Windows. Incomplete/skipped/missing jobs
  are not accepted. Never weaken policy or invent PR webhook green status.
- **F3 / already resolved:** RHC-71, PR #74 independently implemented
  version-neutral read-only HTTPS retrieval of actual public ZIP bytes at an
  immutable Git SHA with SHA256, size, archive and manifest validation. Keep
  this authoritative fallback and its tests; do not rebuild it.
- **F4 / independent Candidate qualification:** Candidate preflight contains
  only nonpublishing Linux/Windows and exact-SHA qualification. Its status
  can be GREEN without an intentionally failing `promotion` job, while
  standard signed production remains separately blocked under
  `productionEnabled=false`, `signingDecision=unknown`,
  `rollbackVerified=false`. No Candidate workflow may publish.
- **F5 / Issue initialization:** Create Issue with neutral temporary title;
  independently fetch the newly allocated GitHub Issue number and rename
  to `[RHC-N]`. Discover installed tool schemas before mutation. The
  supported GitHub connector uses `add_comment_to_issue` for comments.
  Read back saved Issue and full Rolling Comment BEFORE making a Work branch.
  After unknown mutation status, reconcile first rather than retry writes.
- **F6 / null CI steps:** Missing/null `steps` or `jobs` means evidence
  unavailable, not green. `normalize_job_steps` yields an empty evidence
  array; `verify_hosted_jobs` fails closed on a missing or empty job set.
- **F7 / transient logs:** Only read-only GitHub operations may use bounded
  retries on transport/timeouts/rate-limits. Three attempts with bounded
  backoff; persistent errors become `LOGS_UNAVAILABLE`/NOT VERIFIED and
  no log-derived assertion is marked PASS. Never retry uncertain writes.
- **F8 / Node 24 pins:** Reusable publisher artifact upload is pinned to
  upstream `actions/upload-artifact` v6 SHA
  `b7c566a772e6b6bfb58ed0dc250532a479d7789f` and download to
  `actions/download-artifact` v7 SHA
  `37930b1c2abaa49bbe596cd826c3c89aef350131`.
  Upstream exact tags and both `action.yml` files declare
  `runs.using: node24`. Test the real hosted Linux→Windows→stage artifact
  handoffs before claiming the warning remediated. Other action warnings
  require per-workflow inventory; never unpin to `@main`.

Current change does not authorize any new version, Candidate promotion,
artifact publication, release tag or production-policy relaxation.
