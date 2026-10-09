# RHC — Development Guidelines

New GitHub Issues, PRs, comments and normative documents are written in English; user discussion remains German with English technical terms. The current source state comes from Git, never a frozen historical Markdown snapshot. See [Git provenance](GIT_PROVENANCE_CONTRACT.md).

## Change identity and PR-only policy

**Every changed-file change** needs a responsible actual `[RHC-N]` Issue **before work**, and a PR with at least one explicit Issue link in its **body**. PRs may reference multiple Issues, and an Issue may cover several PRs; preserve source-PR versus release-PR separation. Use `Refs #N` for partial progress and `Closes #N` only when real acceptance will be met. Record the PR link, head/merged main SHA, applicable CI, cleanup and completion decision in the Issue or its established Rolling Comment. No routine direct-main changes, even if platform protection permits them.

- **Docs-only path:** create a small `docs/RHC-N-...` branch from a freshly read main commit, modify only Markdown, inspect exact diff, open Issue-linked PR, verify applicable checks, merge exact head and reread main/branch. No product version bump, Candidate, release, `dev-path` label or Work heartbeat. An Issue-only comment does not require a PR.
- **Product Fast-Path:** normal narrow Patch/Hotfix Candidate according to live `tools/rhc_candidate_entry.py` and tests, actual `RHC-Issue: N` commit trailer and `Release-Profile` contract; strict main ancestry and signed/unsigned release separation.
- **Executable Work-Path:** for substantial code/workflow/tool work, use justified `work/RHC-N`, with one existing [Rolling Comment](templates/WORK_PATH_ROLLING_COMMENT.md). Create `BOOTSTRAP` comment first and independently read back **before** creating Work branch/first code commit. Pin fresh main SHA; after branch creation reread its head, update and verify same comment before coding. Keep factual millisecond UTC heartbeats around every **3 minutes** while ACTIVE and meaningful persistent code checkpoints around **10–15 minutes**. Reconstruct all refs/comments after interruption, do not backdate.
- Any change to Go/Python/PowerShell, workflows, tools, tests or machine-readable policy is **not docs-only**. Classification comes from changed paths, not the topic of the issue. Follow real work/candidate/CI rules. Do not invent owner approval for a new product release.

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

An authorized source PR is **not** a product release. The [Release Process](RELEASE_PROCESS.md) and [Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md) require versioned immutable ZIP/catalog, reproducible PE/ZIP, hosted native safety, Git source tag, separate PR provenance and remote readback. Owner acceptance of unsigned/uncertified interim distribution stands **until revoked**; external physical hardware, rollback and publisher trust are DEFERRED/NOT_VERIFIED in that mode, while ordinary signed/certified production policy remains fail-closed.

Historical decisions, version-specific red failures, workflow IDs, hashes and recovery/cleanup belong exclusively in responsible Issues/Rolling Comments and Git, **not** as current-state tables in these guidelines.
