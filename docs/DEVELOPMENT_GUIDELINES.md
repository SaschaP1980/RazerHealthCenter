# RHC — Development Guidelines

New GitHub Issues, PRs, comments and normative documents are written in English; user discussion remains German with English technical terms. The current source state comes from Git, never a frozen historical Markdown snapshot. See [Git provenance](GIT_PROVENANCE_CONTRACT.md).

## Change identity and PR-only policy

**Every changed-file change** needs a responsible actual `[RHC-N]` Issue **before work**, and a PR with at least one explicit Issue link in its **body**. PRs may reference multiple Issues, and an Issue may cover several PRs; for atomic interim releases preserve one combined Candidate-source+downloads PR with provenance. Use `Refs #N` for partial progress and `Closes #N` only when real acceptance will be met. Record the PR link, head/merged main SHA, applicable CI, cleanup and completion decision in the Issue or its established Rolling Comment. No routine direct-main changes, even if platform protection permits them.

- **Docs-only path:** create a small `docs/RHC-N-...` branch from a freshly read main commit, modify only Markdown, inspect exact diff, open Issue-linked PR, verify applicable checks, merge exact head and reread main/branch. No product version bump, Candidate, release, `dev-path` label or Work heartbeat. An Issue-only comment does not require a PR.
- **Product Fast-Path:** normal narrow Patch/Hotfix Candidate according to live `tools/rhc_candidate_entry.py` and tests, actual `RHC-Issue: N` commit trailer and `Release-Profile` contract; strict main ancestry and signed/unsigned release separation.
- **Executable Work-Path:** for substantial code/workflow/tool work, use justified `work/RHC-N`, with one existing [Rolling Comment](templates/WORK_PATH_ROLLING_COMMENT.md). Create `BOOTSTRAP` comment first and independently read back **before** creating Work branch/first code commit. Pin fresh main SHA; after branch creation reread its head, update and verify same comment before coding. Keep one fresh millisecond-precision **`Original ISO timestamp`** with derived readable UTC **`Last heartbeat`** and `de-DE` **`Local reference (Europe/Berlin)`** around every **3 minutes** while ACTIVE; maintain meaningful persistent code checkpoints around **10–15 minutes**. Reconstruct all refs/comments after interruption, do not backdate.
- Any change to Go/Python/PowerShell, workflows, tools, tests or machine-readable policy is **not docs-only**. Classification comes from changed paths, not the topic of the issue. Follow real work/candidate/CI rules. Do not invent owner approval for a new product release.

### RHC-115: authoritative GitHub Issue initialization is a blocking precondition

For every **new** Issue, use the two-phase, single-create repository tool
`tools/rhc_issue_init.py init` or an equivalent client implementing its complete
contract: unique provisional title, real GitHub-assigned number, rename to
`[RHC-N] Descriptive subject`, and independently GET-verified number, exact
final title, saved body and open state. Verify existing Issues with
`python3 tools/rhc_issue_init.py verify --repository OWNER/REPO --issue N`
**before** creating a Work/docs branch, editing files, opening a PR or running
a Candidate/release writer. Stop on `INITIALIZATION_BLOCKED / NEEDS_CORRECTION`;
never recreate after a missing or ambiguous create response, or retry an
uncertain PATCH before GET reconciliation. Continue on readback PASS only.

Executable controls enforce this in Development Completion, Work-to-Candidate
transfer, RHC-94 candidate publisher and version-only source provenance. They
are additional defenses, not a substitute for checking **before the first
branch/file mutation**. GitHub's web UI and unrelated API clients are outside
this CLI's interception scope; repository workflows cannot claim global
creation-time or branch-time blocking. Legacy Issue audit is read-only; no
historic titles are silently repaired. Separate RHC-116 label/path hardening
remains an independently tracked implementation.

### Mandatory full Work-Path Rolling Comment (no abbreviated substitutes)

For **every authorized Work-Path**, read [the canonical Rolling Comment template](templates/WORK_PATH_ROLLING_COMMENT.md) and **instantiate its entire fenced Markdown scaffold** in the one Issue comment **at BOOTSTRAP, before the Work branch or first executable change**. The template is the required format, not an optional example or merely a linked reference. Do **not** replace it with an ad hoc short progress note. Preserve the exact top-level title, all named singleton headings **once, in their prescribed order**, field labels, measurement table, numbered attempt sections, and closing evidence/conformance sections. Record actual base/main SHA, issue, authorization, scope, branch `NOT CREATED` and checkpoint; independently verify the stored comment ID, all three same-instant heartbeat fields and the **exact millisecond `Original ISO timestamp`** against GitHub `created_at`/`updated_at` before any branch mutation. Use the ISO field, **not the human-readable UTC or local text**, as the freshness/readback authority.

Keep **that same comment ID** throughout Work execution. Populate fields with real GitHub source/PR/CI/runner/timing evidence as it becomes available, retaining earlier REDs, corrections and the time-based status history in the ledger. Where an entire phase is genuinely inapplicable (e.g. Candidate, public Release or native hardware on a nonpublishing documentation/test Work-Path), retain its headings and required field lines and explicitly mark `NOT APPLICABLE — <reason>` rather than deleting them or asserting PASS. Use `unknown — not measured` or `NOT VERIFIED` for missing timestamps, model-selector/effort metadata, counts and source evidence; **never** backfill invented values, chat markers or heartbeat times. Status, last checkpoint, GitHub run IDs and branch disposition must agree with their live readback.

**Mandatory pre-closure structural audit:** compare the actual persisted comment against the complete current [template](templates/WORK_PATH_ROLLING_COMMENT.md): title, section order, all singleton/field names, exactly one instance of each singleton, numbered attempt chronology and applicable/N/A classification. Independently verify actual Development Completion, PR/merge SHA, GitHub job outcomes, cleanup and final `COMPLETED` state, and include a measurement/evidence audit and plan-conformance verdict **before closing** the Issue. If any required element is missing or inconsistent, correct the *same* comment in place and read it back; otherwise record `BLOCKED`, not template-compliant completion. If an earlier Work run already violated the bootstrap/heartbeat/template requirements, explicitly retain the process nonconformance; late correction does not retroactively make that historical phase compliant.

This template requirement applies to Work-Path (including a documentation request **escalated to executable Work-Path**); it does **not** impose a Work Rolling Comment on a genuinely Markdown-only lightweight documentation PR. Use the canonical template's `YYYY-MM-DD at HH:mm:ss UTC`, fixed-zone `DD.MM.YYYY, HH:mm:ss CET/CEST` (`Europe/Berlin`, `de-DE`), and unmodified `YYYY-MM-DDTHH:mm:ss.sssZ` triplet for future substantive updates; do not mass-reformat historical comments or imply GitHub viewer-local detection. If executable consumers rely on the former ISO directly after `Last heartbeat`, seek separately authorized executable scope rather than silently changing code.

## Default public release for an owner-requested new version

**Implicit end-to-end release authorization:** After the initial read-only repository bootstrap, an explicit owner instruction to **build, create or increment a new application version** (for example, "build a hotfix, increment only HOTFIX and use Work-Branch Path") authorizes **the complete autonomous Develop → Build → Candidate → Release → final verification lifecycle by default**, even if the owner never uses the words "release" or "publish". Do not ask for a separate release instruction or repeat the existing until-revoked **unsigned/uncertified interim** publication approval for each qualifying version. A successful source build, source-PR merge or green Candidate is **not** completion: target a real immutable Portable ZIP under `main/downloads/`, updated `downloads/latest.json`, `downloads/releases.json` and `downloads/README.md`, the matching immutable source tag, single combined source+downloads PR provenance, remote postmerge readback and verified branch cleanup. Use the existing eligible automated publisher and exact current GitHub source/CI authority; do not infer any release result.

**Intent boundaries:** Supplying only an `INITIAL_PROMPT.md` URL remains strictly **read-only**. Docs-only work, exploratory discussion, tests or QA artifacts, and building/rebuilding an **unchanged** already-versioned binary do **not** imply publication. An explicit `build-only`, `QA-only`, `do not publish` or owner revocation overrides the default. If any required gate, effective permission, matching source identity, tagged ZIP/catalog provenance or safety qualification is failed, stale, skipped, unresolved or unavailable, **STOP at BLOCKED/NEEDS_ATTENTION**; do not silently downgrade to a successful build-only outcome, bypass a safety gate, or partially publish. Existing standard signed/certified production remains separately **fail-closed**; do not alter its machine policy. Physical Razer hardware, rollback and publisher trust remain `DEFERRED/NOT_VERIFIED` (not PASS) only in the explicitly qualified unsigned interim release profile, with visible unsigned/SmartScreen disclosure.

**Path adherence:** When the owner explicitly requests the **Work-Branch Path** for a new version, execute its complete Issue-backed pre-branch BOOTSTRAP Rolling Comment and verified Work-branch lifecycle, Development Completion, version/Candidate contracts, one verified combined Candidate-source+downloads release PR and final Issue ledger. Version increments must respect the requested component and live executable changed-file allowlist; do not introduce unrelated functional changes.

### Release completion is more than publisher completion

A separately authorized **new-version** build proceeds through the qualified Candidate and **one** combined source+downloads PR, then independent hosted RHC-102 postrelease verification. Before reporting release completion, read back exact immutable `main` and Candidate source SHAs, version source tag, ZIP bytes/catalog, Issue/PR lineage and branch cleanup; additionally require a real exact-`main`-SHA `workflow_dispatch` run of [RHC Independent Postrelease Verification](../.github/workflows/rhc-postrelease-verification.yml) with successful Linux HTTPS readback, hosted native Windows safety and aggregate jobs. The explicit `RHC102_INDEPENDENT_HTTPS=PASS`, `RHC102_INDEPENDENT_WINDOWS=PASS`, `RHC102_INDEPENDENT_POSTRELEASE=PASS` and publisher `RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS` gates must be green; `PASS_POSTRELEASE_PENDING`, skipped/`action_required`/zero-job or stale runs are not a final PASS. Do not interpret a successful prior-version postrelease audit as proof of future-release repeatability ([RHC-105](https://github.com/SaschaP1980/RazerHealthCenter/issues/105)).

**Scope separation:** a documentation-only Issue-backed branch/PR does not initiate a Candidate, Work-Path rolling comment or publication. Review the existing focused [RHC-94 wiring tests](../tests/test_rhc94_atomic_orchestration_wiring.py), [RHC-102 hosted wiring tests](../tests/test_rhc102_wiring_contracts.py) and [RHC-102 provenance negative tests](../tests/test_rhc102_release_contracts.py) before adding duplicates. If an actual uncovered executable regression is found, use a separately justified test-first executable scope with the required RED/GREEN, consumer and CI evidence rather than changing workflows under a documentation-only PR.

### Automated read-only postrelease rechecks for separately reviewed corrections

For an actual failed independent RHC-102 verifier after a **genuinely published** interim release, do not repair history by rerunning the Candidate/publisher or altering published ZIP/tag/catalogs. Use [the RHC-110 nonpublishing controller](../.github/workflows/rhc-postrelease-recheck.yml) only after an Issue-backed corrective Work-Path PR has exact-head owner review/approval, hosted Linux/native Windows Infrastructure proof and a verified main merge. The controller is triggered by completed verified cleanup with a bounded hourly fallback, not by assuming a bot-origin PR webhook has jobs. Its Action write scope is **only** dispatch to the existing RHC-102 verifier; this follow-up requires real hosted HTTPS+Windows+aggregate 3/3 PASS and never retroactively relabels the initial failing release as no-workaround GREEN.

Every substantive executable correction must be test-first RED→GREEN with the complete Rolling Comment instantiated **before** its Work branch. Check test discovery patterns carefully: an undiscovered test cannot qualify as RED or GREEN. Preserve the original failed run, test-coverage mistakes, all corrective attempts and the final exact-SHA CI/cleanup evidence in the same Issue ledger. A documentation-only or irrelevant PR must not initiate a postrelease audit or any publication.

## Test-first, CI and precise history

Confirmed executable defects should have a focused meaningful RED on the unfixed frozen SHA, then the same GREEN after the fix. If RED is not reproducible, report that limitation. Run real consumers/CLI as appropriate; syntax checking alone does not prove integration. Check `python3 -m unittest discover -s tests -p 'test_rhc_*_contracts.py' -v`, `go test .`, `build.sh`, i18n/PE/resources and actual native Windows PowerShell 5.1 repair-safety gates according to live executable contracts.

The four **separate** evidence classes are local/static, hosted Linux crossbuilding Windows binaries, hosted **native Windows**, and physical Razer/rollback testing. Missing, failed, SKIPPED, cancelled or stale-SHA results are not PASS. Before each source/PR/Candidate/merge milestone, read current main/branch head, actual CI jobs and complete diff. Work requires verified Development Completion, Candidate Entry and appropriate current-main ancestry. Never quietly reuse an old Candidate success for a new source SHA.

App version schema is `MAJOR.MINOR.PATCH.HOTFIX`; read the live app/reference fields from `model.go`. Read public version separately from downloads catalog/ZIP and matching source tag; do not hardcode or confuse them. Independent component versions are unrelated. Standard Candidate release profiles and allowed source-file changes are enforced by current executable validators; an issue-specific exception is not a global override.

### GitHub Actions PR-creation permission

For **manual repository setup** of GitHub Actions PR writers, see [GITHUB_HOWTO.md](GITHUB_HOWTO.md). **GitHub Actions PR-creation permission** must be verified by a real, bounded **nonpublishing** PR smoke test, not assumed from YAML or a saved settings control. Recheck the capability on each target repository.

## Safe PR/merge and recovery

Verify Issue link(s), PR base and frozen head, source ancestry, exact files, applicable Linux/native Windows/safety checks, current ruleset and effective GitHub API permissions **before merging**. `GITHUB_TOKEN`-generated refs may require explicitly dispatched trusted CI; a YAML permissions declaration is not evidence. Use expected-head SHA merge, reread actual main and verified SHA-lease cleanup, preserve unrelated/divergent refs. Record real red/green and any cleanup failure in the owning Issue.

No-direct-main/Issue–PR traceability is a **project process rule**, not proof of live GitHub ruleset enforcement. Administrative required-PR/status-protection changes require separate authorization.

## Product safety and release boundaries

Health, diagnostics and setup remain read-only against Razer/Windows. Every repair requires explicit in-app user confirmation, validated recipe/payload/allowlist/PID, precise pre-mutation checks, least privilege and post-repair read-only verification. Do not auto-repair on CI or infer HEALTHY from ambiguous user-mode states.

An authorized source PR is **not** a product release. The [Release Process](RELEASE_PROCESS.md) and [Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md) require versioned immutable ZIP/catalog, reproducible PE/ZIP, hosted native safety, Git source tag, single combined PR provenance and remote readback. Owner acceptance of unsigned/uncertified interim distribution stands **until revoked**; external physical hardware, rollback and publisher trust are DEFERRED/NOT_VERIFIED in that mode, while ordinary signed/certified production policy remains fail-closed.

Historical decisions, version-specific red failures, workflow IDs, hashes and recovery/cleanup belong exclusively in responsible Issues/Rolling Comments and Git, **not** as current-state tables in these guidelines.


## RHC-94: single combined interim source+downloads PR

For an explicitly qualified version-only Candidate, a successful final exact-SHA Linux/native-Windows Candidate preflight dispatches the owner-authorized unsigned interim orchestrator on that Candidate ref. The publisher confirms the exact current main parent, Work tree and Development Completion, live Issue, trusted Candidate bot statuses, independently reproducible PE/ZIP and Windows Authenticode/repair-safety. Its only public activation is merging ONE PR carrying both the Candidate source diff and the four published downloads files. Do not create an interim source-only PR beforehand. An unchanged production/signing/rollback policy is mandatory; external hardware remains unverified. Never convert the release to a Fast-Path when the owner explicitly required Work-Path.
