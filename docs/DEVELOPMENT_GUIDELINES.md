## RHC-43 — Real reusable interim Publisher implementation checkpoint (2026-10-09)

The source-controlled implementation is now split between [the version-independent source-triggered publisher](../.github/workflows/rhc-reusable-interim-release.yml) and [independent postmerge verification/tag workflow](../.github/workflows/rhc-reusable-interim-postmerge.yml). Both use the pure [rhc_reusable_interim.py](../tools/rhc_reusable_interim.py) eligibility contract, the immutable [downloads verifier](../tools/rhc_downloads.py), real independent Linux double-builds and actual hosted native Windows PowerShell 5.1/NotSigned safety evidence. The existing v3.0.8.1 writer remains historical manual-dispatch-only.

**Execution is not proof:** Before promoting a hotfix PR or reporting any public Release, prove the actual workflow passed on the new main source SHA, its contents-write, actions-write, and pull-requests-write operations genuinely succeeded (or precisely report denied GitHub Actions PR permission and safely recover via an authorized GitHub App), independently verify the staged release PR Linux/native Windows/downloads jobs, and validate final ZIP bytes, public catalog/latest, immutable tag and branch cleanup. A declared permissions entry is NOT evidence of effective permission. A partial staged branch is NOT a published Release.

**Current source checkpoint:** Historic CI trigger fixes are integrated; generic Publisher/Verifier is on Work branch but its real GitHub stage/merge/tag and v3.0.8.2 public downloads have NOT YET BEEN PROVEN. Requalify v3.0.8.2 against advanced main without reusing old candidate evidence. External Phase B remains DEFERRED/NOT_VERIFIED; standard production policy unchanged. Work chat German with English technical terms; GitHub artifacts English.

---
# RHC-43 — Active reusable Development → Build → Release guidance (owner decision 2026-10-09)

> **GitHub language policy:** All new GitHub development documentation, Issues, comments, commit messages, code comments, workflow descriptions and release records must be in **English**. The user-facing chat is **German with English engineering terms**. Retain older German evidence as history rather than silently rewriting timestamps or decisions.

**End-to-end completion means publication, not Candidate success.** When the owner asks to test or perform a complete Development/Deployment/Release cycle, the acceptance boundary is an actual, independently verified immutable download under main/downloads/, consistent source version and CHANGELOG, releases.json/latest.json, source tag, GitHub merge/CI evidence and recorded safe branch cleanup. If any required technical step cannot be completed, report **BLOCKED/INCOMPLETE** with the exact failed run, SHA and missing capability. A successful build, Work Completion or Candidate alone does not complete the task.

**Process authorization versus executable implementation:** The owner has now requested a reusable technical interim-unsigned release mode beginning with v3.0.8.2; see [RHC-43](https://github.com/SaschaP1980/RazerHealthCenter/issues/43) and [Reusable Interim Release Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md). This authorization is **not** permission to claim an unimplemented workflow GREEN. The existing v3.0.8.1-only automation is **historical, manual-dispatch-only**. Do not redirect it to new versions or reuse stale 3.0.8.1 source/tag/download values. Promote the new reusable mode only after focused RED→GREEN contracts, actual hosted Linux/native Windows tests, exact GitHub write permissions, stage/PR/merge and independent remote postverification are proved.

**Safety and trust remain distinct:** Keep the standard production controller and config/rhc-release-policy.json fields unchanged (productionEnabled=false, signingDecision=unknown, rollbackVerified=false) until separately authorized standard production gates exist. The explicit interim mode may defer only the owner-identified **external** physical-device, system rollback, signing/publisher/SmartScreen-trust and administrator ruleset acceptance; log each as DEFERRED/NOT_VERIFIED, never PASS. Require real PowerShell 5.1 repair-safety and Go/PE, two byte-identical binary/ZIP builds, package/history immutability, SHA/version/tag consistency, tested PR/merge and postpublication evidence. Disclose the executable as **unsigned**, publisher unverified and possibly subject to SmartScreen warnings; do not disable Windows security protections.

**Separate concerns:** RHC-41's product Hotfix remains exactly model.go + CHANGELOG.md, independently qualified from RHC-43's infrastructure changes. After CI fixes, source and downloads may use separate verified PR transactions: source promotion to main followed by exactly four immutable downloads paths. Current source version, public latest version and qualified Candidate version must always be read independently; no static version pins or assumption that downloads are empty after first publication. Historical prepublication rehearsal and v3.0.8.1 writer must never gate a later Hotfix PR.

**Observed technical blockers:** [old-version interim workflow #37889334544](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37889334544) and [old prepublication rehearsal #37889334478](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37889334478) genuinely FAILED on RHC-41. Keep the RED evidence. GitHub Actions token PR-creation permissions and some cleanup paths were historically blocked in RHC-33/RHC-34; recheck before claiming fully autonomous publication. Never force a publish, invent CI statuses or bypass a failed mandatory verification.

---
## RHC-34 scoped autonomous interim release (supersedes older standard approval language ONLY for v3.0.8.1)

The 2026-10-09 owner decision in [RHC-33](https://github.com/SaschaP1980/RazerHealthCenter/issues/33) parks external hardware/rollback/unsigned/publisher and admin-ruleset gates, so the RHC-34 interim Develop → Build → Release cycle can run autonomously. Those requirements must remain `DEFERRED/NOT_VERIFIED`, never PASS; physical devices and Razer repair behavior are not changed. `config/rhc-release-policy.json` stays false/unknown/false, because the historical RHC-20 **standard** release controller must remain fail-closed. The new v3.0.8.1-specific interim gate is in `tools/rhc_interim_release.py` and `.github/workflows/rhc-interim-release-v3081.yml`.

Exactly for 3.0.8.1, `main/model.go` and `CHANGELOG.md` are updated and qualified **before** release; the four-download-file PR is a separate subsequent transaction. Do not reuse or replace the historical stale `candidate/v3.0.8.1`; source authority is the verified pre-release main SHA. All ordinary development (Work rolling BOOTSTRAP, exact-SHA Completion, Linux/native Windows real builds, no unsigned-certification claim, error ledger, tested PR merge/cleanup) continues unchanged. On every future version, do not infer that the v3.0.8.1 exception applies; require a documented scope decision/re-enabled parked gates. The read-only `rhc-downloads-verify.yml` remains mandatory for release branch/public main checks. RHC-22 and the parked RHC-33 issue remain OPEN after successful interim release.

---

# RHC — Development guidelines

> **Historischer Standardcontroller (RHC-20):** Nichtpublizierende Candidate-/Release-Qualifikation und reguläre Policy von der späteren echten, aber versionsgebunden autorisierten Interim-Veröffentlichung unterscheiden. Die aktuelle App-Version aus [`model.go`](../model.go), öffentliche Latest-Version aus [`downloads/latest.json`](../downloads/latest.json) und regulären Freigabestand aus [`config/rhc-release-policy.json`](../config/rhc-release-policy.json) live lesen. Ownerentscheidung [RHC-33](https://github.com/SaschaP1980/RazerHealthCenter/issues/33), Release und offene Cleanup-Befunde [RHC-34](https://github.com/SaschaP1980/RazerHealthCenter/issues/34), physische Hardware-/Trust-/Rollback-Gates [RHC-22](https://github.com/SaschaP1980/RazerHealthCenter/issues/22). Ein veröffentlichter Download aktiviert den regulären Controller nicht.

> **Betriebsregel:** Download-Veröffentlichung, Standardpolicy, native Razer-Hardwareprüfung und Postmerge-Branch-Cleanup sind voneinander unabhängige Nachweiskategorien.

## Authority

Use live GitHub `main` plus current Issues as authority. The original source was imported and hosted-verified in PR #2; later RHC-20 implemented a nonpublishing standard controller, and RHC-33/RHC-34 record the owner-authorized interim release and unresolved cleanup. Neither product publication nor runner tests prove physical Razer/rollback approval or activation of the standard production controller.

## Preserve product invariants

The Go Razer Health Center includes PowerShell diagnostic and repair scripts. Functional work must retain explicit repair approval, product-specific least privilege, no automated elevation, narrowly authorized service/user-mode restarts, pre-mutation rechecks, post-mutation read-only verification, PID ambiguity guards and false-GREEN protections. Only regress expected product behavior with a proven test. No production interaction with the user's Razer hardware during hosted CI.

## Version and development path

**RHC-16 four-part app versioning is implemented:** get the **current** `appVersion` and `referenceVersion` from [`model.go`](../model.go) and the latest public download independently from [`downloads/latest.json`](../downloads/latest.json)/[`downloads/releases.json`](../downloads/releases.json). App/Candidate/Release versions follow `MAJOR.MINOR.PATCH.HOTFIX`; historical Golden Source/QA and independent Engine/Razer version domains are not changed. Do not freeze the current app version in this guideline.

- Documentation-only Markdown/Issue metadata with no machine-enforced changes: one atomic lease-guarded reviewed `main` commit; **no** Work branch, `dev-path` label, version, Candidate or Release. The topic of a document does not change its scope.
- Narrow Patch/Hotfix: branchless Fast-Path by default; test a confirmed failure RED where applicable, fix, run relevant focused GREEN/syntax/determinism checks, create **one exact release-ready candidate** on current `main`, inspect complete diff, then hosted Candidate Preflight.
- Major/Minor or substantial risk/migration: persistent `work/RHC-<issue>` with scoped checkpoints, exact-SHA Development Completion and Candidate Entry before any Candidate.
- Process benchmarking Work-Path for an otherwise simple Hotfix requires explicit user permission, a durable exception reason and same exact-SHA qualification gates. Never escalate merely to have more commits.
- For Issue-backed **executable** development select exactly one live-verified `dev-path: fast` or `dev-path: work-branch` label. Labels were provisioned during migration; recheck current catalog before applying. Documentation/backlog work has no `dev-path` requirement.

### Candidate, Issue and test-first requirements (implemented RHC contracts)

Before new Candidates, read the current `tools/rhc_candidate_entry.py` and tests: exact-main ancestry, one atomic Candidate, real `RHC-Issue: N` and valid `Release-Profile: version-only|patch|hotfix` trailers. The standard version-only path modifies `model.go` and `CHANGELOG.md`; hotfix increments the fourth component. [`CHANGELOG.md`](../CHANGELOG.md) already exists at this revision and must still be checked live. Scope-limited owner exceptions cannot silently redefine standard Candidate rules.

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

## RHC-29 Phase A: autonome technische QA ohne Phase B

Der Owner hat am 2026-10-08 nur **Phase A** autorisiert. Der eigenständige, vollständig nichtpublizierende [Phase-A-Arbeitsvertrag](RHC22_PHASE_A.md) nutzt `tools/rhc_phase_a_qa.py` und `.github/workflows/rhc-phase-a-qa.yml`, um nach qualifizierten Linux- und nativen Windows-Prüfungen ein kurzlebiges `TEST-UNSIGNED-NOT-RELEASE`-Actions-Artefakt mit exakter Source-SHA-/ZIP-/EXE-Prüfsumme zu erzeugen. Die Work-Implementierung läuft über [RHC-29](https://github.com/SaschaP1980/RazerHealthCenter/issues/29); das externe [RHC-22](https://github.com/SaschaP1980/RazerHealthCenter/issues/22) bleibt unabgeschlossen. Kein generisches Testartefakt ist Source-, Hardware-, Rollback-, Publisher- oder Owner-Release-Freigabe. Phase B ist **als Tätigkeit ausgesetzt**, die bestehenden Produktions- und Repair-Sicherheitsgates bleiben vollständig aktiv. Keine Modifikation der Policy, des aktiven Main-Rulesets, des veröffentlichten `downloads/`-Index oder der historischen QA-Archive durch Phase A.
