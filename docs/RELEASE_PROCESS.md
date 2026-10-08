# RHC — LBS-style repository-downloads release contract

> **Variante B / 2026-10-08:** [RHC-20](https://github.com/SaschaP1980/RazerHealthCenter/issues/20) umfasst die vollständig geprüfte **technische, bis zur gesonderten Freigabe nichtpublizierende** Candidate-/Release-Automatisierung. Native Razer-Geräteabnahme, Rollback-/First-Release-Recovery, konkrete Source-/ZIP-gebundene Signatur-/Unsigned-Owner-Zustimmung und tatsächliche Produktionsaktivierung/Erstveröffentlichung liegen **ausschließlich in [Issue #22](https://github.com/SaschaP1980/RazerHealthCenter/issues/22)**. Die GitHub-Schließreferenz darf erst im letzten vollständig technisch GREEN geprüften PR aktiviert werden und ausschließlich #20, **niemals #22**, schließen oder die reale Produktionspolicy automatisch freigeben. Der Owner führt keine manuellen GitHub Reviews für normale, technisch qualifizierte PRs durch; Merge und Cleanup sind autonom nach tatsächlichen Gates. `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false` bleiben bis zu getrennten externen Belegen gültig.

## Current state — architecture selected, production NOT ACTIVATED

**Owner decision (2026-10-08; RHC-12):** RHC uses the same immutable `main/downloads/` release-history architecture as LenovoBootSelector. This supersedes the earlier same-day GitHub-Releases-only proposal. `config/rhc-release-policy.json.distribution=repo-downloads` is authoritative. The former GitHub Releases / Draft state machine in the RHC-5 nonpublishing dry-run is **historical simulation only**, not a current publication blueprint.

**RHC-16 version format (2026-10-08):** all **current application and production Candidate/Release versions** use strict four-part `MAJOR.MINOR.PATCH.HOTFIX`, starting with `3.0.8.0`. Increment a hotfix to `3.0.8.1`; increment PATCH to `3.0.9.0`. Reject three-part/new candidate refs. Frozen historic v3.0.8 QA/source remain byte-identical and retain their original names. This migration is not a production release.

**No public release is authorized yet:** `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`. The existing unsigned v3.0.8 QA build in GitHub Actions is NOT entered in the public release history, is NOT a production release and does not create `latest.json`. The preserved QA artifact remains v3.0.8; current application source is migrated to 3.0.8.0.

## Current RHC Candidate / documentation boundary

Current `tools/rhc_candidate_entry.py` requires changed `model.go` **and** `CHANGELOG.md`, one real `RHC-Issue: N` trailer **also for Hotfix**, and one `Release-Profile: version-only|patch|hotfix`. `version-only` changes **only** those two paths; `hotfix` increments only the fourth version component. `CHANGELOG.md` is absent on `main` and must be added for a future approved Candidate, never bypassed. These RHC executable contracts differ from LBS.

Documentation-/Issue-metadata-only diffs have **no** Work branch, version, Candidate or Release and use one reviewed atomic `main` commit. Machine-consumed policy/workflow/test/code/tool changes are not documentation-only. Scoped “Implementiere”/“Baue” instructions do **not** approve unsigned Windows publishing or disable separate rollout/rollback/native Razer gates.

## Canonical build and distribution

- Source authority: GitHub `main`; `model.go` owns `appVersion` and `referenceVersion` (four-part MAJOR.MINOR.PATCH.HOTFIX). Exact source commits and historical tags determine build provenance.
- Go Windows x64 GUI `RazerHealthCenter.exe`, with embedded diagnostic and repair resources; use pinned Go 1.23.2, existing permanent `build.sh` validators and real native Windows PS5.1 tests. Hosted checks do not substitute for operator native Razer hardware acceptance.
- Single download ZIP per authorized version: `downloads/RazerHealthCenter-Portable-vMAJOR.MINOR.PATCH.HOTFIX.zip` with **exactly seven runtime files** including the EXE, `README.txt`, `README-I18N.txt`, `SAFETY-MODEL.txt`, `i18n-manifest.json`, `locales/de-DE.json`, and `SHA256SUMS.txt`. One extraction only; no nested ZIP, separate Source ZIP, unused runtime folders or diagnostics. The application creates ephemeral runtime folders itself.
- Permanent immutable index: `downloads/README.md` (human-readable), `downloads/releases.json` (newest-first history), `downloads/latest.json` (canonical published newest entry). Before the first authorized release the history is empty and `latest.json` MUST be absent.
- `tools/rhc_downloads.py` constructs bit-reproducible lean ZIPs and validates actual ZIP bytes, strict file allowlist, SHA-256/size, internal checksums, historical records, newest-version pointer and README consistency. `tools/rhc_release_contracts.py` retains its older v3.0.8 reproducibility/source tests; future production ZIP staging must use the *lean* publisher contract.
- GitHub Releases API/assets are not canonical and no automatic updater is included now. Later manual download or updater links may refer to the GitHub `main/downloads/latest.json` catalog.

## Explicitly approved one-off TEST / UNSIGNED QA archive (RHC-14)

The owner separately authorized durable hosting of the already-successful v3.0.8 GitHub Actions artifact **as a TEST build only**. It resides under [`downloads/qa/`](../downloads/qa/README.md), not in the official `downloads/*.zip` history and not in `releases.json` or `latest.json`. Its unsigned Windows status, exact original archive and EXE SHA-256, successful source Work SHA and Actions run ID are pinned in `qa/manifest.json`; archive metadata and disclosures are read-only-verified on every catalog CI run. A one-time ephemeral write-enabled work-branch workflow imported the exact existing original ZIP; that workflow must not remain on `main`.

This explicit test-only publication does **not** meet product release gates, imply Windows publisher trust, certify native Razer hardware, create a tag, enable production policy or set the update pointer. Future production releases still require separate gated Candidate/Release orchestration and exact-artifact signing/unsigned authorization.

## Future release transaction — requires implementation and explicit production gates

1. Build a strictly newer version on the appropriate Fast/Work path from an exact approved current-`main` parent; establish real Candidate SHA, scope, no secrets and no unsafe repair changes. Linux Go/PE and Windows PS5.1 run independently on exact same SHA with validated Candidate statuses.
2. The separately permissioned Release Orchestrator independently rebuilds twice and proves byte-identical lean Portable ZIPs, no source archive or test fixture data, exact SHA-256, version, file inventory, and frozen source-tag identity. It must verify the version has not previously been published, that historical ZIPs are unchanged and source tag is archive/cache-free.
3. Require explicit `productionEnabled=true`, verified rollback, suitable signed Windows publisher identity **or** exact version/source/ZIP-hash-specific owner consent for unsignable Windows binaries including SmartScreen disclosure. Unknowns block. Confirm authorized GitHub permissions, concurrency, required hosted statuses and retained previous releases before any mutation.
4. Stage exactly one new immutable ZIP plus matching `releases.json`, `latest.json`, and `README.md` in a single bounded `release/vMAJOR.MINOR.PATCH.HOTFIX` branch. Do not modify/delete any earlier ZIP. Strict local `tools/rhc_downloads.py` validation and remote exact-SHA preactivation check are mandatory.
5. After verified preactivation, create the source tag with exact provenance, merge a single reviewed Release PR into `main`; **this merge atomically makes ZIP and latest pointer public**. The already-implemented merged-branch cleanup checks and removes unchanged Work/release branches as supported; release-specific temporary branch lifecycle must be added and independently verified.
6. Independently re-read new `main`, real package bytes and SHA, latest pointer, full history, source tag, required status contexts, PR, and actual branch cleanup. Do not claim successful release until post-merge verification passes. If publication partially fails, preserve prior immutable ZIPs and block re-running a version; recover with authorized new version where appropriate.

**Current boundary:** RHC-12 selects and validates the archive format and guarded catalog only. Full production Candidate promotion, Release Orchestrator, signed/unsigned approvals, native hardware acceptance, rollback proof and actual first four-component `vX.Y.Z.H` release remain separate requirements under RHC-3/RHC-1. A green nonpublishing rehearsal is not publication authority.

## Historical release dry-run

RHC-5's former GitHub Releases/Draft fixture model is retained as evidence of failure-mode simulation, not executed as a real Draft, tag or publish. See [RHC-5 dry-run history](RHC_RELEASE_DRY_RUN_PLAN.md). It must not override the newer owner-selected `repo-downloads` distribution contract.

## Historical baseline versus current build (RHC-16)

The frozen original v3.0.8 source intake is audited from immutable original Work commit `2a28a08ba75ecb404df03847cdf1e5eaba941acd` (321-file manifest and original golden EXE SHA remain checked in the separate intake workflow). Active four-component `3.0.8.0` builds must instead pass independent reproducible binary and package checks on the **current** source SHA, Linux and native Windows regression checks and strict current version validators. Comparing new 3.0.8.0 bytes against the historical v3.0.8 EXE SHA is invalid and must never be represented as a current release gate. The QA `downloads/qa/...v3.0.8-TEST-UNSIGNED.zip`, its SHA and `downloads/releases.json` remain untouched.

## RHC-20 technical release controller (2026-10-08)

Actual Candidate `candidate/v3.0.8.1` is qualified under exact SHA `1b78ca928979e9507863a53ce2e4b25491544d5e`, but the final Candidate promotion intentionally FAILS while production is disabled. This is not a product release.

`tools/rhc_release_live.py stage` requires the explicit RHC22 Owner issue comment with version, source SHA, ZIP SHA-256, native Razer hardware and rollback records, signed verification or explicit unsigned SmartScreen acknowledgement; a separate live policy enablement and effective main PR/CI rules are independently checked BEFORE any public branch or Git blob write. A single immutable ZIP plus releases.json/latest.json/README is staged on an owner-authorized release branch and PR; `rhc-release-preflight.yml` must be explicitly dispatched (GITHUB_TOKEN-created refs may not generate push workflows). That workflow sets source/portable/verification statuses on the exact Release branch commit only after real Linux double PE/ZIP builds and native Windows PS5.1/trust checks. It never merges or publishes.

`tools/rhc_release_finish.py` is a separate, explicitly authorized merge/tag/postverify action: it rechecks RHC22 evidence and hosted statuses, verifies the exact public ZIP bytes, latest pointer, history and tag, and cleans only unchanged merged release branches. An uncertain GitHub action is `BLOCKED_ATTENTION`, not a reason to blindly retry. `tools/rhc_candidate_from_work.py` also has a read-only checkpoint recovery path.

Main ruleset ID 24701145 **currently only blocks deletion/force push**. Owner admin must separately activate effective required PR/CI checks via `RHC_OWNER_RULESET_ADMIN=EXPLICIT_RULESET_ONLY python tools/rhc_main_rules.py --apply` using a GitHub repository-admin token; `python tools/rhc_main_rules.py` audits. No manual GitHub reviews are required, but missing admin configuration MUST NOT be called GREEN. Current production policy remains false/unknown/false, no real ZIP, Tag, release branch or latest is approved. Native Razer/rollback/signed-or-unsigned owner consent and first public release stay in Issue #22.
