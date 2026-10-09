# RHC — Migration Evidence Locator

This is **not** a second chronological migration ledger. Historical migration decisions, precise versions/SHAs, failures, tests and outcomes live in the responsible GitHub Issues, their Rolling Comments, authentic merged PRs, Git history and Actions. Preserve those records rather than duplicating terminal snapshots here.

## Reconstruct the migration and current gate state

1. Fetch current `main` and full Git tree; read `model.go`, actual source, `config/rhc-release-policy.json`, active CI code and relevant GitHub rulesets.
2. Enumerate open and relevant closed Issues (including original source import, Candidate/CI design, release distribution, licensing, branding, interim release and external acceptance) with their complete rolling/recovery comments. Follow actual linked PRs and their source/base/merge ancestry. A dated historical Issue statement is not automatically current policy.
3. Read `downloads/latest.json` and `downloads/releases.json`, verify immutable ZIP bytes/hash and source version tag target/`sourceSha`. The latest public version may refer to an earlier source commit than today's main.
4. Determine any migration gates `M0–M6` from their owning Issue acceptance criteria and actual CI/source/PR evidence; independently classify hosted Go/Linux, native Windows/PowerShell safety, source import, publication/cleanup, platform protection and **real physical** Razer/rollback/trusted publisher. Report external physical hardware, native rollback and trusted publisher acceptance explicitly as **DEFERRED/NOT_VERIFIED** until independently proven; never treat these as PASS or ordinary standard production as enabled merely because an interim package is public.
5. Distinguish closed/superseded Issues and preserved unmerged branches from still-active work. If a prior direct commit has no Issue-backed PR, preserve that fact as a historic provenance gap rather than fabricating a PR or rebasing immutable history.

Follow [Initial Prompt](INITIAL_PROMPT.md), [Git provenance contract](GIT_PROVENANCE_CONTRACT.md) and [Release Process](RELEASE_PROCESS.md). Older migration playbooks, dry-run notes and `docs/recovery-history/` are explicitly **historical reference** material; their frozen versions and CI results are not present-day operating authority.
