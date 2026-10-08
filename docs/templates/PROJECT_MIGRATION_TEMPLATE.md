# Reusable GitHub project migration template (v0.1)

**Purpose:** establish an existing product's source, build, safety contracts and release policy as auditable GitHub authority **without changing product behavior or silently publishing a release**. This template is *product-neutral*. Use `docs/MIGRATION_STATUS.md` and RHC-1 as its first real-world case study.

## Mandatory intake variables

| Field | Record verified value or `unknown` |
| --- | --- |
| Repository URL, visibility, owner permissions | <repo; visibility; access evidence> |
| Short project code and issue numbering rule | <e.g. RHC; actual GitHub Issue #N> |
| Product version(s) and actual source of version authority | <path, exact semantics> |
| Source/archive locations, SHA-256, file manifest and historical proof | <bytes/hash/count> |
| Language/toolchain version/dependencies | <names/versions; clean rebuild> |
| Native target OS/arch, signing, updater, installer/portable format | <grounded> |
| Product safety boundaries and prohibited CI side effects | <contracts> |
| Required hosted operating systems and validation matrix | <test names and counts> |
| Release and source package retention/distribution | <target, immutable assets> |
| Repository initialization, branch policy, token scopes, secrets | <observed configuration> |
| Previous exact baseline hashes, PR/Issue, recovery state | <evidence> |

## Stage 0 — Preserve provenance, authorize migration

- Obtain **complete** canonical source and release archives, build logs, regression reports and handover. Verify hashes against declared manifests. Distinguish supplied reports from newly rerun tests.
- Confirm whether the GitHub repository is public. Scan source and historical logs for secrets/PII; document scan limits and inspect relevant files. Do not upload sensitive material into public history; removing it later does not erase history.
- Freeze product-version and behavior scope. Initial repository bootstrap is not permission for an application update, firmware/service modification, signing decision or production release.
- Create one migration Issue with acceptance gates and known limitations. Use actual GitHub Issue #N, rename to `[<CODE>-N]`, and document path decisions and unresolved questions.

## Stage 1 — Safely initialize GitHub

- Check whether `main` has a commit. If unborn, use a simple first README commit; do not call `compare`/`update_ref` with fabricated base SHA. Read new head/tree after initialization.
- Create new-chat entry point, current status, development path guidelines, release target design and this migration template. Do not label bootstrap docs as the complete source of truth.
- Track file/checksum inventory, source tree and release-binary hash separately. Prevent Git storage of local build outputs, private logs, caches, secrets and platform-specific generated intermediates unless deliberately canonical.
- **Protect the default branch as an explicit setup gate:** the owner should configure an ACTIVE GitHub branch ruleset targeting `~DEFAULT_BRANCH` (or the exact intended branch); block deletions and non-fast-forward/force pushes, with no bypass actors by default. Re-query the full ruleset detail and `branches/<default>` to confirm effective enforcement. A UI screenshot of selected unsaved checkboxes or a missing warning is **not** proof of activation. If an integration cannot read the legacy branch-protection endpoint (403), use the readable ruleset and effective `protected` branch flag instead; record residual visibility limitations.
- **Split baseline protection from merge-gate enforcement:** do not turn on mandatory PRs/required status contexts until the target project's release workflow and required checks are implemented and tested. Stage 1 protects history/deletion only; ordinary direct fast-forward pushes remain possible and must not be described as blocked.

## Stage 2 — Validate the original product before import

- Extract into a clean directory with ZipSlip/path guard. Check file count and duplicates, encoding, execute bits, BOM and line endings.
- Run the exact existing build/validation entry point on pinned toolchain with no network unless required/approved. Classify cold toolchain setup versus tests. Preserve first-attempt failures and retry evidence.
- Confirm binary SHA match on a clean rebuild; if not byte-identical, isolate deterministic inputs, signing, PE metadata, resource ordering, time, locale and toolchain. Do not silently lower the gate to semantic equivalence.
- When cross-compiled, run separate hosted native OS compatibility tests; never count static source checks as firmware/hardware E2E.

## Stage 3 — Import the complete reviewed source

- Use **a byte-preserving transfer mechanism**. A GitHub connector that only accepts inline text is insufficient for a binary-containing 321-file source archive. Do not claim GitHub is authoritative until every approved file and binary build input can be fetched from GitHub.
- Compare each imported path, size and SHA-256 to the locked extraction manifest, identify intentional exclusions and verify **zero unintended source edits**.
- Confirm `go.mod`/build entry, platform resources, locale and repair scripts exist at canonical relative paths. Keep historical release ZIPs out of source tree unless deliberate and immutable.

## Stage 4 — Hosted intake gates, no release

- Add manual-only `workflow_dispatch` source-intake smoke at first. Use pinned toolchain and least-privilege read-only workflow permissions. Check full existing tests and byte-identical baseline EXE.
- Hosted Linux builds and hosted native Windows/PS5.1 gates are **distinct** evidence. A workflow SKIPPED or a local PASS cannot substitute for a hosted required status.
- Verify job logs, exit status, output hashes and workflow metadata; add failing-test characterization for defects. Once independently GREEN, add protected PR gates intentionally.

## Stage 5 — Adapt, do not clone, the release architecture

- Preserve process *invariants*: one atomic Fast-Path Candidate for small fixes; Work-Branch + cumulative ledger + exact-SHA Development Completion for risky work; mandatory parallel hosted candidate gates; promotion fail-closed; independently reproducible release; single PR/merge activation; postrelease verification, safe cleanup.
- Change only product-specific implementation: version inputs, build/runtime tooling, native OS and architecture, package format, signing, update-pointer policy, anti-tampering validation and safety tests. The donor project's output artifacts are **not** the target product's inputs.
- Formalize failure injection: stale main, mismatched candidate SHA/status, protected-file changes, missing tag or package, signature/hash mismatch, double releases, PR preactivation failure, Work-Branch moving during cleanup.

## Stage 6 — Qualify and activate CI/CD explicitly

- Prove real hosted Linux and Windows gate totals, timings and exact SHA. Measure queue/setup/build/test and orchestration separately. Re-read the ACTIVE main-branch ruleset (matching branch, deletion and non-fast-forward, bypass actors) and the effective `protected` flag; then validate how required PRs/status checks interact with the actual Candidate promotion and Release merge, including bot permissions and fail-closed checks. Only enable mandatory PRs/status rules when their intended workflows and checks have passed on the exact SHA.
- Only after tests and user authorization enable promotion and production publishing. Keep manual review or fail-closed gates for high-risk policies (signing, updater, repair behavior, destructive migration).
- Record first release separately from baseline migration. No fake source-tag or release ZIP just to make dashboards green.

## Stage 7 — Completion and handover

- Confirm GitHub contains full trusted source and build instructions; verify clean checkout can recover any required product state.
- Keep final acceptance table: PASS, BLOCKED, OPEN with exact evidence links and counts; file paths and hashes; actual main SHA, issues, PRs, workflow runs, version and build artifacts.
- Publish unresolved risks and lessons in GitHub, not only a chat. Do not close the migration Issue until all mandatory gates in its scope have passed.

## Lessons / template update rule

After every genuine problem, add **observed symptom → evidence → root cause or uncertainty → smallest correction → preventive rule/test → whether retrospective claims must be corrected**. Update this template with a generalized gate, not an RHC-specific hack. Do not assert a cause solely because a retry succeeded.

### Reusable CI staging and transport guards

- A new PR which does not yet contain the imported product source is **not** a qualified Candidate or migration; hosted smoke gates should fail closed. To avoid wasting Windows runners and red-but-expected checks, first stage complete reviewed bytes, then open the source-import PR when possible.
- For GitHub Actions, check the live hosted runner's Node runtime warnings and the official action metadata. Prefer pinned full commit SHAs of supported versions, and record the versions/rationale; do not blindly retain another project's old action majors.
- A ZIP/file kit under ChatGPT is not a commit, GitHub Action artifact, or GitHub source-of-truth. Require an actual repository head, complete source manifest, exact file-byte comparison, and hosted tests before migrating the authority claim.
- When source is sensitive and the target GitHub repo is public, the authorization to build locally does **not** imply consent to expose historical logs or forensic data publicly.

### Source-byte and reproducible-build controls (new migration lessons)

- A Git blob may exactly match its imported ZIP bytes while a Windows Git checkout rewrites line endings. For byte-frozen imports, choose a committed `.gitattributes` policy **before** cross-OS hash validation, and compare the exact source manifest on all required OSes. In RHC, `* -text` prevents conversions; a normal software development project may need a more selective policy.
- Go builds inside Git worktrees can embed VCS revision/time/dirty metadata by default. An archive-origin golden executable generally has none. Explicitly evaluate `GOFLAGS=-buildvcs=false` or an equivalent `-buildvcs=false` option and confirm the exact binary hash; do not compensate with weaker semantic hash comparisons.
- A temporary automation that pushes back to its own branch must guard against **the trigger's exact SHA**, not a pre-workflow historical head. Respect GitHub's `GITHUB_TOKEN` event recursion rules and dispatch qualification explicitly when needed.
- Remove temporary write-enabled import workflows from the final reviewed tree. Permanent source-intake workflows should remain read-only, and final SHA qualification must occur **after** any such cleanup.

### First-case lessons (RHC, 2026-10-08)

1. **Unborn repository:** `main` can be designated as default while GET branch returns 404 and refs return 409. Bootstrap initial commit before any SHA-lease workflow.
2. **Migration channel mismatch:** a text-only GitHub mutation connector is not proof of ability to import binary assets, source ZIPs or large nested trees. Separate repository bootstrap from verified source transfer; use a manifest-verified importer and a reviewed PR for source intake.
3. **Cold Go toolchain:** first `build.sh` timed out after reaching i18n guard; subsequent guard and full warm rerun passed with exact 3.0.8 reference hash. Budget toolchain setup and log timeout truthfully.
4. **Archive topology matters:** RHC Source ZIP = 321 files; Portable ZIP = 7 files and 12 empty runtime directories; validate both file and directory contracts.
5. **Public repository:** regex secret scan returning no matches is only an initial signal, not legal/privacy clearance for historical logs/forensic data.
6. **Version-authority mismatch:** RHC's `model.go` app/reference version and Go Windows build cannot be replaced by LBS `bin/version.json` or PowerShell release logic.
7. **Unproven deployment:** initial local deterministic build is strong source evidence but still **not** hosted Windows or real hardware verification. Never promote local-only PASS to release-green status.
8. **README conflict:** migration source can include a canonical root README while GitHub bootstrap already has a different README. Require exact collision detection, explicit disposition and original file byte preservation.
9. **GitHub policy visibility:** a repository may expose zero rulesets yet branch-protection reads may return 403 through integration credentials. Mark required branch protection **unverified** until owner-visible review, rather than assuming permissions from successful writes.
10. **Public history is hard to undo:** enforce a real operator review of historical logs/forensics and license/privacy scope before source import; false-positive-free regex scans are not proof of safe publication.

11. **Hosted success is a per-SHA statement:** source verification and platform builds must pass on the exact final PR head before merge; post-merge documentation may record that source success but must not claim a new release.
12. **Temporary elevated workflow lifetime:** remove one-shot write-enabled source staging workflows *before* qualification of the final mergeable PR tree; the remaining permanent intake workflow should be read-only.
13. **Source packaging after archive upload:** a user may upload a canonical Source ZIP at repository root. If source packaging blindly traverses the entire repo, the next Source ZIP may recursively include its own archived source and private provenance files. Establish explicit packaging inclusion/exclusion and deterministic metadata **before** enabling release automation.

14. **Default branch protected flag vs ruleset detail:** a newly created repository can show an unprotected `main` while its build pipeline is already rigorous. The owner-created RHC Stage-1 ruleset was verified via `rulesets/<id>`: `active`, `~DEFAULT_BRANCH`, `deletion`, `non_fast_forward`, empty bypass, and `branches/main.protected=true`. Required PR and status checks remained deliberately open. Record the full effective rules, not just the banner or a successful UI save.

**Maintenance rule:** this template is expected to evolve in small reviewable documentation commits after each migration and each confirmed issue.
