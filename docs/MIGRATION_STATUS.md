## Final migration disposition — 2026-10-09

**Current authority:** GitHub main, live model.go, downloads/catalog/tags and validated hosted runs. Dated records below remain historical, not current release policy.

- **RHC-1: COMPLETED** — original 321-file byte-preserving source intake [PR #2](https://github.com/SaschaP1980/RazerHealthCenter/pull/2), golden Windows EXE and native Windows PowerShell 5.1 safety [CI #37737410046](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737410046), migration lessons/governance, actual GitHub Actions PR rights later [smoke #37903545748](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37903545748).
- **RHC-3: SUPERSEDED** — nonpublishing Candidate/Work/Go/Windows infrastructure and current reusable interim publishing supersede the legacy GitHub Draft proposal. Preserve `work/RHC-3` unchanged: **four non-main commits** affecting QA artifact transport in the historical infrastructure workflow. Do not silently merge or discard those commits.
- **RHC-34: COMPLETED after verified historical ref cleanup** — 3.0.8.1 public seven-file portable ZIP SHA-256 `c7a7ac150d236e85710454c61c806a6f3f4fb400d5309487ecbb88746f28c4c8`, immutable source tag `v3.0.8.1` = `75b9209a90a192dba5f22665720a048195dc6881`, downloads catalog. Four obsolete, already merged RHC-34 Work refs are reconciled only by [SHA-bound cleanup workflow](../.github/workflows/rhc34-historical-ref-cleanup.yml); close only after independent remote absence verification. Historical RHC-34 cleanup REDs are preserved.
- Later release v3.0.8.2 was verified by [RHC-43 real postrelease recovery #37899579163](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37899579163); the default `GITHUB_TOKEN` bot-created a nonpublishing [PR #52](https://github.com/SaschaP1980/RazerHealthCenter/pull/52) in [run #37903545748](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37903545748), then closed it and deleted its scratch ref.
- Owner-approved unsigned/uncertified interim releases remain allowed **until explicitly revoked**. Real hardware, native rollback and signing/publisher/SmartScreen acceptance are **DEFERRED / NOT_VERIFIED**, **not interim release blockers**. RHC-22 and RHC-33 remain OPEN; standard policy `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`. Rights/licensing RHC-6 and branding RHC-8 remain OPEN.

### Current migration gate disposition

| Gate | Current verified position |
| --- | --- |
| M0–M3 | **PASS** — source inventory, byte identity, golden EXE and hosted Linux/native Windows intake |
| M4 | **PASS** — Candidate and tested interim technical release pipeline through v3.0.8.2, without enabling standard production |
| M5 | **PARTIAL** — bot PR create, ruleset, releases and ref cleanup proven; external rollback/Windows publisher/administrative production conditions DEFERRED / NOT_VERIFIED |
| M6 | **DEFERRED / NOT_VERIFIED** — physical Razer hardware and native rollback tracked under RHC-22/33 |

---
## Live source, public download, standard policy and cleanup are separate

**Current state: always resolve live.** App/reference from [`model.go`](../model.go), latest published version from [`downloads/latest.json`](../downloads/latest.json) and [`downloads/releases.json`](../downloads/releases.json) with real ZIP/Source-Tag proof, standard policy from [`config/rhc-release-policy.json`](../config/rhc-release-policy.json). The separately owner-authorized interim cycle is traced in [RHC-33](https://github.com/SaschaP1980/RazerHealthCenter/issues/33), [RHC-34](https://github.com/SaschaP1980/RazerHealthCenter/issues/34) and its [release retrospective](RHC_V3_0_8_1_RELEASE_RETROSPEKTIVE_2026-10-09.md). A published ZIP does not activate the standard production controller.

**Verified at this documentation update:** an actual unsigned interim Portable ZIP is listed in the public releases catalog and has a matching original source tag. The standard policy remains `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`; physical Razer/rollback/publisher acceptance and administrative required-PR gates are `DEFERRED/NOT_VERIFIED`. The **historical** v3.0.8.1 postmerge cleanup did fail; later independent postrelease/tag/ref recovery succeeded for v3.0.8.2. Final cleanup of four merged legacy RHC-34 Work refs has its own specialist SHA-lease gate. The historical snapshots below are not current-version authority.

---

# RHC migration — historical source import and version-transition evidence

**Historische Momentaufnahme, nicht aktuelle Versionsautorität:** Originalquelle/Golden-Prüfungen via PR #2, Entscheidung `repo-downloads` in RHC-12, vierteiliges Versionsschema durch RHC-16, nichtpublizierender Standardcontroller über RHC-20 PR #28. Die spätere eng autorisierte Interim-Veröffentlichung sowie offen gebliebener Cleanup stehen in RHC-33/RHC-34. Für gegenwärtige Quellen, Downloads und Freigaben die Live-Verweise oben verwenden.

## Authority transition

- Destination: [RazerHealthCenter](https://github.com/SaschaP1980/RazerHealthCenter), default branch `main`.
- Migration tracking Issue: [RHC-1](https://github.com/SaschaP1980/RazerHealthCenter/issues/1).
- Historical **v3.0.8 source-intake** [PR #2](https://github.com/SaschaP1980/RazerHealthCenter/pull/2), head `2a28a08ba75ecb404df03847cdf1e5eaba941acd`, merge `daf3e4994f108299c9ed9aa47bbaf48b2ae720d9`. Current build authority is **live `main` plus `model.go`**, not the old ZIP/EXE hash.
- Prior Lenovo Boot Selector process is a **pattern**, never the runtime/build authority for RHC. Use the generic migration template in `docs/templates/PROJECT_MIGRATION_TEMPLATE.md`.
Historical source and reproducibility gates remain traceable in GitHub. RHC-20 PR #28 is the standard **nonpublishing** controller; later owner-authorized interim publication and remaining cleanup are tracked separately in RHC-33/RHC-34. Actual ZIP/catalog/tag, CI and postmerge cleanup require individual proof.

### Later decisions governing new operations

RHC-12 replaced GitHub Releases/Draft with `repo-downloads`; RHC-16 established the four-component app version schema while Golden Source/QA remains frozen. RHC-5's old Work checkpoint became history after [PR #9](https://github.com/SaschaP1980/RazerHealthCenter/pull/9). Later actual distributions and owner exceptions must be obtained from the live catalog and issues. Current [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md), policy and machine contracts prevail.

## Verified input identity (2026-10-08)

| Artifact | SHA-256 | Observation |
| --- | --- | --- |
| v3.0.8 Source ZIP | `f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495` | 4,627,837 bytes; **321 regular files**; ZIP CRC/integrity PASS |
| v3.0.8 Portable ZIP | `30df1141c660d6fc50969aeb7c3a388f350d4977f7c5aa7c1fa3d3ba087e3ea7` | 8,621,194 bytes; 7 regular files plus 12 explicit directories; ZIP CRC/integrity PASS |
| Release and local rebuilt EXE | `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a` | Cross-built Windows amd64 GUI EXE is byte-identical to supplied reference |
| Source-side AppEngine diagnostic 1.0.2 | `4ac0f44212a5c53db932f6033a6fa53fa0c60a9b5b7a125f9485e17a39bd6121` | From supplied v3.0.8 handover; not remeasured independently during bootstrap |
| Source-side AppEngine recovery 1.0.0 | `ff53cdabcd7c046c25e15ca30419986ace3012532b05e83a9b681e28de6f738a` | From supplied v3.0.8 handover; not remeasured independently during bootstrap |

Independent local validation used **Go 1.23.2 Linux/amd64** with `GOPROXY=off`, `GOSUMDB=off` and `GOTOOLCHAIN=local`. The source `build.sh` completed its Python static/regression validators, `go test .`, the i18n guard, Windows cross-platform `go vet`, Windows amd64 `go build -trimpath -ldflags='-H windowsgui'`, resource injection and PE validation. The full clean rerun reproduced the exact reference EXE SHA-256 above. These initial numbers were local evidence. They have since been supplemented by GitHub-hosted [run #37737410046](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737410046), which verified the exact 321-file source inventory on both Linux and Windows, reproduced the golden Windows amd64 EXE SHA-256, parsed 15/15 PowerShell source files in native Windows PowerShell 5.1, and passed Go test/vet and repair safety checks. **Physical Razer hardware acceptance is still pending.**

The supplied 3.0.8 package-validation report says 15/15 PASS, the regression-background-runtime report says 20/20 GREEN versus 3/20 on v3.0.7, and original full validation 20.20 seconds / clean rebuild 18.74 seconds. These numbers are **provided historical reports** and must not be mislabeled as newly hosted results.

## Historical v3.0.8 product/build characteristics at original intake

- `go.mod`: module `razerhealthmonitor`, Go **1.23.2**, no external dependency entries/go.sum.
- `model.go`: `appVersion = "3.0.8"` and `referenceVersion = "3.0.8"`.
- Root `build.sh`: mandatory existing Python validation scripts, `go test .`, i18n guard, Windows cross-`go vet`, reproducible Windows GUI build, `tools/patch_rsrc.py` and `tools/validate_pe.py`.
- `tools/package_portable.py`: fixed payload plus explicitly retained empty runtime directories; `tools/package_source.py`: ZIP source packaging excluding `.git`, `dist`, `portable-stage`, Python bytecode/cache.
- v3.0.8 keeps confirmation before mutation; AppEngine Health's steady-state requires persistent runtime/systray/background/lighting/generic middleware rather than transient dashboards; missing systray must prevent HEALTHY. Do not relax this or use product-name/PID heuristics as a shortcut.

## Acceptance gates

| ID | Gate | Current state |
| --- | --- | --- |
| M0 | Intake hashes, ZIP integrity, safe extraction and independent local EXE reproduction | **PASS (local)** |
| M1 | Empty GitHub repository initialized with migration docs, Issue and reusable template | **PASS — GitHub commits and exact trees verified** |
| M2 | 321-file source tree imported to `main` with exact original content-byte identity | **PASS — PR #2 merged, original source SHA inventory verified on both hosted OSes** |
| M3 | GitHub-hosted source intake reproduces golden EXE; Linux and native Windows PS5.1 checks | **PASS — run #37737410046, Linux and Windows jobs both success on exact head** |
| M4 | RHC-specific Candidate, Release, preactivation and postrelease machinery built, tested fail-closed | **PASS for owner-approved interim technical pipeline — real public releases v3.0.8.1/v3.0.8.2, reproducible Go/ZIP and exact source-tags; standard signed-production policy remains intentionally disabled** |
| M5 | GitHub Actions permissions, branch policies, release-asset distribution, secrets, rollback verified | **PARTIAL — real GITHUB_TOKEN createPullRequest via PR #52, active main ruleset, immutable repo-downloads and verified tag/ref cleanup; separate external hardware/rollback/signing/production approvals DEFERRED / NOT_VERIFIED in RHC-22/33** |
| M6 | Real native Windows/Razer acceptance for v3.0.8 false-positive fix | **DEFERRED / NOT_VERIFIED — physical Razer-device and native rollback acceptance remain parked in RHC-22/33** |

**Current release permission:** standing owner approval for unsigned/uncertified interim publication until expressly revoked; actual v3.0.8.1/v3.0.8.2 public ZIP/catalog/source tags verified. Separate signed production authorization is NOT granted.

## Observed initial migration problems and responses

1. **Empty Git repo:** `branches/main` returned 404 and Git refs 409 until the first README commit initialized `main`. Template must explicitly bootstrap an unborn default branch rather than assuming a base SHA.
2. **No container network DNS to GitHub:** local `git ls-remote` failed DNS. The connected GitHub repository integration could write the initial README. A complete raw source transfer needs a verified channel capable of moving source and binary assets byte-for-byte; do not substitute a metadata-only commit.
3. **Cold Go compilation overran the first interactive build command:** validation scripts and `go test` progressed, and `go run ./tools/i18n_guard .` was reached, but that command timed out. The i18n guard and Windows cross-build passed separately; a warmed complete `build.sh` rerun passed. **Do not record the timed-out attempt as a completed gate.** Template distinguishes cold toolchain setup time from true validator failure.
4. **Source/package structure:** Source ZIP contains **321 files**, while Portable ZIP contains 7 regular files and empty directories. Use a file manifest and preservation rules, not an assumption that both ZIPs have similar structures.
5. **Source safety audit:** A preliminary *heuristic* scan of readable source files found no private-key, credential-token, personal Windows-user-path or email patterns. This is not a comprehensive secret audit or proof of safe public publication; inspect historical logs/forensics and public-repository policy before full source import.

## Bootstrap state verified on GitHub

- First initializing README commit: `7246bec962a63ea097d7ff4b6fa35be60afab954`.
- Reviewed 9-file governance and manual-only intake workflow commit: `411fd17d3427c3d571e159ca8d8e5a7ffea251c9`. Exactly nine intended added paths in the corresponding GitHub commit comparison.
- RHC-specific rolling-comment template added; reusable migration playbook and tested fail-closed ZIP intake helper were committed separately. Import helper blob SHA `3d7497f94c6fa18d75930cf906970a7fddfff0f2` matches the locally tested helper byte-for-byte.
- Helper simulation: missing README replacement flag blocked, dry run PASS without mutation, missing public-publication review blocked, explicit staged import wrote **321/321 source file bytes** with hash match. **Simulation was in an isolated local Git checkout, NOT source import into this GitHub repository.**
- Portable ZIP internal SHA256SUMS: **6/6 checks independently PASS**. Product source ZIP remains external intake material until PR migration.
- **Historical bootstrap observation (before owner configuration):** GitHub repository rulesets query returned **zero rulesets**; branch-protection endpoint returned **403 Resource not accessible by integration**. Superseded by the active Stage-1 Ruleset verification documented below. The 403 endpoint is not needed for reading the actual ruleset.
- GitHub Actions workflow-list / label-list endpoints could not be queried through the connector due to endpoint validation. Workflow YAML exists on `main`, but **no hosted workflow was executed** and the custom RHC label taxonomy is not confirmed provisioned.
- A public-source privacy/license review is **OPEN**; no v3.0.8 source upload or release was performed. The exact PR-based procedure is in [SOURCE_IMPORT_PLAYBOOK.md](SOURCE_IMPORT_PLAYBOOK.md).

## Second-phase source-import preparation (GitHub Draft PR #2)

- **Draft PR:** [RHC-1 source import](https://github.com/SaschaP1980/RazerHealthCenter/pull/2), branch `import/RHC-1-v3.0.8`; source baseline still **NOT UPLOADED**.
- Import-checkpoint commit `02c2c186ab75801be5a94e047faccc88e98a0777`; subsequent CI-action modernization commit `f9f5afd5988d451a42419f8ff2b5d2df10c540b1`.
- RHC golden source inventory: **321** files; canonical fingerprint `adbfc9de536bd0ca8a1b69163ffdf080fe0b46b083b42ca498b8fafeb18703db`.
- New `tools/verify_source_intake.py`: source/archive identity, path, byte-size and file SHA verification; isolated test results **4/4 expected** (unaltered PASS, tampered file FAIL, tampered manifest FAIL, missing source FAIL).
- Updated `tools/import_source_archive.py` accepts an explicit pinned expected branch, still refuses unreviewed writes and unexpected file conflicts. Isolated branch-specific execution: dry-run PASS, unreviewed apply REFUSED, reviewed local apply **321/321 byte-identical**, generated manifest verification PASS.
- GitHub [Actions run #37735881073](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37735881073) intentionally failed because the PR lacks source: Linux `SOURCE_INTAKE_BLOCKED: missing go.mod`; Windows `RHC_SOURCE_INTAKE_MANIFEST=FAIL` missing the manifest. These are **expected fail-closed signals**, not successful Go/Windows product tests.
- GitHub log also showed a Node.js 20 deprecation warning for `actions/checkout@v4` and `actions/setup-go@v5`. The PR now uses SHA-pinned Node 24 versions, `checkout v7.0.1`/`setup-go v7.0.0`. Hosted [run #37736021306](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37736021306) reproduced the expected missing-source failures, with **no such Node 20 warning**.
- The complete import cannot be pushed from the available container: `git ls-remote` failed DNS resolution of github.com; connector writes are suitable for ordinary text/Git objects but do not provide a verified 4.6 MB binary-archive transfer. A full locally verified GitHub import kit is available as a conversation artifact; an authenticated computer with Git network access must push the reviewed source to this Draft PR.
- **All source/hosted-build PASS claims remain BLOCKED.** Do not merge Draft PR #2, tag, or publish until all 321 exact source files exist on the PR branch and both hosted OS gates PASS.

## Owner upload and verified branch-source staging

- The owner uploaded the canonical `Razer-Synapse-Chroma-Health-Center-Source-v3.0.8.zip`, 321-file original inventory, SHA256SUMS and handover to public `main` in `f789132d31bb7e96b4fdca5d4ed0510fdbc2a3c7`. This is archive material, not yet individual canonical files on `main`.
- One-shot [run #37737103537](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737103537) verified the uploaded ZIP SHA-256 and all 321 per-file bytes/fingerprint, merged the owner's current `main` into `import/RHC-1-v3.0.8`, imported 321 files plus a 321-file manifest, and **pushed the exact source files to Draft PR #2**. No production release/tag was created.
- Earlier staging [run #37737052502](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737052502) failed at the final push guard because it compared against an outdated branch SHA rather than the triggering commit; corrected to an exact `GITHUB_SHA` lease, then reverified. This was an orchestration implementation defect, not source data failure.
- Full-source [qualification run #37737117960](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737117960) verified Linux source manifest PASS (321 files). Windows strict manifest check failed on `BUILD-FULL-v3.0.6.log` because Git Windows checkout applied line-ending normalization; original Git blob SHA matches the source ZIP byte-for-byte. The next Candidate explicitly uses `.gitattributes: * -text` to preserve source bytes across operating systems.
- Linux full source `build.sh` source/regression tests ran, but the EXE SHA mismatched the golden reference. Controlled local Go 1.23.2 characterization proved the cause: builds inside Git repositories automatically include Go VCS metadata, whereas the golden source-archive EXE does not. Building with `GOFLAGS=-buildvcs=false` restored the exact golden EXE SHA `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`. CI now sets the flag explicitly without altering product source or build.sh.
- The transient write-capable staging workflow is removed from the proposed final source tree after its successful import. The permanent **read-only, nonpublishing** source-intake workflow is re-executed on the exact final PR commit; previous failed runs remain evidence, not accepted gates.

## Source migration finalized in GitHub

- The owner uploaded the original source archive and 321-file inventory to public `main`; a restricted one-shot GitHub Action validated and staged the exact archive contents into PR #2. Initial staging failures and corrections are preserved in the migration ledger.
- [Final GitHub Actions run #37737410046](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737410046) completed **success** against PR head `2a28a08ba75ecb404df03847cdf1e5eaba941acd`. Linux: 321/321 manifest PASS, full `build.sh` PASS, golden Windows GUI EXE `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a` PASS. Windows: 321/321 manifest PASS, PS5.1 parser **15 files PASS**, Go native test/vet PASS, AppEngine recovery **25/25 PASS**, repair safety PASS.
- PR #2 [merged](https://github.com/SaschaP1980/RazerHealthCenter/pull/2) at **2026-10-08T06:27:14Z**; `main` now contains all source files individually, plus original ZIP provenance. The postmerge source tree remains version **3.0.8**; no runtime/version mutations, production release or public update-pointer activation occurred.
- The temporary **write-capable** source staging workflow was removed before the final exact-SHA qualification; the remaining `rhc-source-intake.yml` workflow has only `contents: read` and **cannot publish**.
- RHC uses `.gitattributes` to preserve all original file bytes across Windows/Linux and explicit `GOFLAGS=-buildvcs=false` for the archive-based golden EXE test. Both were validated on GitHub runners.
- **Important outstanding packaging risk:** Owner-uploaded original ZIP, original inventory and extra import documents remain at repository root. Existing `tools/package_source.py` recursively packages most repo files and currently does not exclude ZIP inputs; its policy needs an explicit reproducibility/security correction **before any future production Source ZIP is published**. Do not alter the original v3.0.8 byte-frozen source files during baseline import.
- **Policy snapshot at source-migration merge time (historical):** no rulesets were then observed and branch-protection API returned 403. This is superseded by the Stage-1 Ruleset verification documented below. No owner-supplied attestation of external license/privacy clearance for the already-public archive; automated credential heuristics are not a comprehensive legal audit.
- Source import is complete; **RHC-1 remains OPEN** for M4–M6 (release machinery, repository security/distribution policy, and real native acceptance).

## Stage-1 main branch protection — independently verified

- Repository owner enabled [`RHC - Protect main` ruleset #24701145](https://github.com/SaschaP1980/RazerHealthCenter/rules/24701145) on **2026-10-08**, target `branch`, `enforcement: active`, conditions `ref_name.include: ["~DEFAULT_BRANCH"]` (currently `main`).
- Rules **exactly** `deletion` (no matching branch deletion) and `non_fast_forward` (force-push blocked). GitHub's live `branches/main` endpoint reports `protected: true`.
- `bypass_actors: []`, `current_user_can_bypass: never`; no exemptions configured. Normal fast-forward ref updates remain allowed because the ruleset does not restrict updates.
- **Explicitly not enabled yet:** required PRs, required status checks, linear history and signed commits. Set these only alongside a validated RHC Candidate/Release orchestration and exact status contexts; the existing v3.0.8 source-intake workflow is not a general release gate. Stage 1 is **not** protection against an arbitrary direct fast-forward push.
- The GitHub integration still receives HTTP 403 on the legacy `branches/main/protection` admin endpoint, but the ruleset detail is readable and authoritative; do not misclassify the verified ruleset as unknown.
- Next review in M5: choose whether `~DEFAULT_BRANCH` tracking is sufficient or whether an explicit literal `main` ref must remain protected even if repository default changes. Configure/fail-test PR/status/automation behavior, permissions, secrets and rollback separately.

## RHC-3 CI/CD migration Work-Path checkpoint (not activated)

- [RHC-3](https://github.com/SaschaP1980/RazerHealthCenter/issues/3) uses a persistent `work/RHC-3` branch and one cumulative recovery comment. User-visible Work-Chat-ID recorded there. Entire original **321-file v3.0.8 source baseline remains frozen**; all changes are new tools/tests/CI and migration documentation.
- Source/Portable deterministic ZIP builder `tools/rhc_release_contracts.py` explicitly whitelists tracked build inputs, excludes the uploaded root Source ZIP, historical logs, forensics, binary payloads and cache, retains the 7 original Portable regular files plus **12 empty runtime directories**, and uses fixed ZIP metadata. Offline RED/6-test GREEN; two independent local output pairs were byte-identical.
- Pure exact-SHA Candidate, Work Completion, hosted-status and preactivation safety contracts `tools/rhc_orchestration_contracts.py` added; the combined local adversarial suite is **11/11 PASS**. The source-model version remains exactly `3.0.8`; any Candidate for the same/downgraded version is rejected.
- Hosted [Infrastructure Qualification #37739340380](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37739340380) PASS with true Linux full Go build/EXE golden hash/reproducible Source+Portable outputs and native Windows PowerShell 5.1/Go/Razer repair safety checks. [Extended test run #37739956526](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37739956526) PASS; [Release Contract Rehearsal #37739956589](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37739956589) PASS verifying actual production policy is `disabled`. None of these runs published a Release.
- A **read-only** RHC Candidate Preflight is staged for a future strictly newer `candidate/vX.Y.Z`; Linux/Windows jobs check exact parentage, issue/profile trailers, full build and safety, while the terminal promotion job deliberately blocks. No Candidate branch or release version exists.
- First attempted Development Completion YAML was rejected by GitHub before job creation [#37740064959](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37740064959): an unquoted Actions expression contained colon+space. A corrected YAML parsing form launched a job, but the substring trigger was also falsely activated by a commit **mentioning** the marker in a fix explanation [#37740289526](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37740289526); its strict marker check correctly rejected it. The final trigger requires the explicit message trailer at the end. Future migrations must lint YAML and test marker selection, not just workflow existence.
- **Formerly open in this checkpoint, now verified:** exact frozen Work-SHA Development Completion and PR evaluation/merge in PR #4. **Still open:** actual next-version Candidate lifecycle/promotion; signed/unsigned distribution decision; GitHub Release or update-pointer/retention/rollback contract; mandatory PR/status rules; native Razer hardware E2E. No v3.0.9, tag, GitHub Release or public latest pointer created.

## RHC-3 hosted Work-Path and infrastructure PR completed (no publication)

- Frozen Work request SHA `be71e47c91a56222763db81ca452e14904a909f7`, same tree as preceding checkpoint; exact `main` at request: `38a13d3996fc46fdd83cc9e12592ebfb96226d18`. No original Go, PowerShell, resource, asset or build.sh files changed; **16 CI/tool/test/config/doc paths only**.
- [GitHub Work CI #37740741287](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37740741287): Linux source inventory, full original v3.0.8 Go build, EXE golden SHA, reproducible Source/Portable ZIPs, and Python integration contracts **15/15 PASS**. Native Windows 2025 PowerShell 5.1 parser 15 files, Go/vet, repair safety and Python contracts **15/15 PASS**.
- [Development Completion #37740741265](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37740741265): `development-completion/gate=success` recorded on **that exact Work SHA**, verified current-main ancestry, frozen Work ref and previously successful 2/2 hosted jobs without rebuilding the same Work twice.
- [PR #4](https://github.com/SaschaP1980/RazerHealthCenter/pull/4) independently triggered [original Source Intake #37740941297](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37740941297) and [Infrastructure Qualification #37740941296](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37740941296). All **four Linux/Windows PR jobs PASS** on frozen reviewed head. Seven pre-merge conditions independently rechecked, no app version/runtime change.
- PR #4 merged **2026-10-08T07:03:30Z**, merge SHA `3a36e3cb3ba3f46a278a35150d0998ef004b1cdc`; RHC 3.0.8 source authority maintained. `config/rhc-release-policy.json.productionEnabled` remains `false`. Work-branch cleanup and release-branch lifecycle are **not** yet automated.
- RHC now has a *nonpublishing Candidate Preflight*, determinism checks, Work-Path Development Completion and read-only Release Contract Rehearsal. This is an **infrastructure milestone**, not a production release. Actual release promotion, signed/unsigned trust selection, distribution/pointer, preactivation/merge, postrelease verification/rollback remain M4/M5 blockers.

## Approved GitHub Release distribution architecture (2026-10-08)

- Owner selected GitHub Releases as the **sole canonical public artifact/version store**, with a read-only LBS-inspired downloads overview sourced from published GitHub Releases; **no separate `latest.json` or automatic updater** at first.
- The safe RHC-specific sequencing differs from the historical LBS repository-pointer approach: candidate verification → independently rebuilt and verified Source/Portable ZIPs → fully populated Draft GitHub Release → prepublication checks → single reviewed PR merge to `main` → final Draft/merged-source checks → **publish Draft as sole public activation** → postrelease hash, tag, provenance, listing and cleanup verification.
- `config/rhc-release-policy.json.distribution` is now `github-release`, but **`productionEnabled=false`**, `signingDecision=unknown`, and `rollbackVerified=false`. This is a policy decision, not a production-ready gate.
- Immutability for **published** GitHub Releases is preferred but not assumed active: verify repository setting/capability and test handling of publication failures and non-rewritable releases before enabling production.
- Next engineering scope: design/fail-test exact-SHA Draft publication state machine, RHC release artifact names/sha manifests, source tag/merge consistency and idempotent recovery; then obtain explicit Windows signing/trust and rollback choices and configure minimum CI permissions. Do not release v3.0.9 merely to test setup.

## Unsigned Windows release planning — owner input (2026-10-08)

- Owner reports **no current code-signing certificate**. This is a fact about certificate availability, **not** approval for distributing an unsigned executable.
- Future unsigned path is explicitly **per-version and per-artifact approval required**, with approved source SHA, archive SHA-256/size, documented lack of Authenticode identity, and rollback/privacy/security conditions. `signingDecision=unknown`; `productionEnabled=false`; `rollbackVerified=false` are unchanged.
- [RHC-5](https://github.com/SaschaP1980/RazerHealthCenter/issues/5) tracks the nonpublishing exact-SHA release simulation and negative tests. The [detailed implementation plan](RHC_RELEASE_DRY_RUN_PLAN.md) specifies pure Draft/Publish fixtures, no GitHub write scopes, no actual Draft/tag/Release, all-or-nothing readiness and idempotent interrupted-run recovery.
- M4 remains PARTIAL, M5 remains PARTIAL, M6 remains OPEN. **No GitHub Release resources, tags, product version increments or released EXEs** are permitted by this plan.

## Next action (historical GitHub-Releases plan, superseded by RHC-12)

GitHub Releases distribution has been selected. Next design and nonpublishing-qualify Candidate promotion, Draft Release staging, prepublication checks, source PR merge, immutable Release activation, postrelease verification and failure recovery; separately settle signing/trust, immutable setting and rollback before any real deployment. Keep RHC-3 and parent RHC-1 open; no v3.0.9 and no native repair changes.

## Distribution decision superseded — RHC-12 (2026-10-08, later owner instruction)

The earlier same-day GitHub Releases-only distribution agreement recorded above was explicitly **superseded** by the owner. The current authority is `config/rhc-release-policy.json.distribution=repo-downloads` and `docs/RELEASE_PROCESS.md`. Use LenovoBootSelector's source-controlled immutable historical release ZIPs and `downloads/README.md`, `downloads/releases.json`, `downloads/latest.json` (latest only after an authorized release), in a single merge activation. Source remains in GitHub; runtime ZIP has seven files and no nested/source archive.

RHC-12 implements a read-only catalog/ZIP checksum validator, staging helpers, adversarial tests and baseline empty catalog. It **does not** publish the earlier unsigned v3.0.8 test artifact, change the product version, create a tag, override release policy or declare production release GREEN. Archive publisher/orchestrator and owner-specific signing/unsigned decisions, native Razer acceptance and rollback remain OPEN. Earlier M5 entries and GitHub Releases/Draft notes above are historical, not present-day instructions.

## RHC-16 — app version namespace changes to MAJOR.MINOR.PATCH.HOTFIX (2026-10-08)

Latest owner instruction moves **current app/reference version** from historical three-part v3.0.8 to four-part **v3.0.8.0**, without publication. Historical 321-file source archive SHA, fingerprint and pinned v3.0.8 EXE hash are immutable, validated on the original exact SHA rather than silently rebaselined to new bytes. QA `downloads/qa/RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip` remains original with unchanged SHA, while future official `candidate/v3.0.8.1` and `release/v3.0.8.1` refer to four-digit versions (with `hotfix` profile semantics). Engine / legacy History and third-party Razer versions remain unaffected. No main/latest release advance is implied by this schema migration.

## RHC-20 release automation 2026-10-08

The real v3.0.8.1 Candidate was qualified on GitHub Actions; production promotion intentionally failed. New Candidate recovery and Release PR/ZIP/status controllers exist without actual publication. Main ruleset ID 24701145 still lacks required PR/status checks; owner-admin configuration and real hardware/rollback/signed-or-unsigned consent remain external Issue #22 gates. Historical v3.0.8 QA binaries/metadata and `downloads/latest.json` remain untouched.

## RHC-20 final technical acceptance — 2026-10-08 (authoritative over earlier dated snapshots)

- [RHC-20](https://github.com/SaschaP1980/RazerHealthCenter/issues/20) closed automatically after [final technical PR #28](https://github.com/SaschaP1980/RazerHealthCenter/pull/28) merged at `main=6fd6c20ddb0123546674370c5f873ea059450db1`, exact Work head `8b135a1e087f10c2d6867960edecb556ac6febae`. Merge has two verified parents: prior `main=e0ac1a0457e6205c1cb9f690c4be03437b541ada` and final Work head. Automatic [cleanup run #37849138759](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37849138759) succeeded and deleted only verified merged `work/RHC-20`.
- Exact Work-source hosted [Infrastructure #37848692744](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37848692744) **Linux + native Windows SUCCESS**, **150 Python tests** on Linux, two independent identical Go/PE builds and reproducible package bytes; [Development Completion #37848692656](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37848692656) **SUCCESS** with bot-created exact SHA `development-completion/gate=success`. The independent [RHC-5 read-only Dry Run #37848692758](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37848692758) passed. After PR creation, new same-head [Infra PR #37848895156](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37848895156), [historical Source Intake #37848895124](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37848895124) and [real-byte isolated nonpublishing Rehearsal #37848895148](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37848895148) all completed SUCCESS; the historic intake is a separate Golden evidence class.
- New permanent RED→GREEN regression guards cover true two-parent release merge and closed PR, Draft→Ready verification before any source-tag creation, exact Candidate source-byte promotion **together with** the immutable seven-file ZIP/catalog (six changed repository paths), bot-created PR explicit Common/Release status dispatch, fail-closed stale/conflicting approval, source/ZIP tampering, previous-release-history preservation, and owner-executable main Ruleset configuration. The positive GitHub Release controller API/PR/postmerge tests are **synthetic/mock**, the independent PE/ZIP rehearsal is real-byte but **not publishing**. No live Owner-authorized release PR, real source tag or successful production promotion was tested or claimed.
- **RHC-1 migration gate classification:** M0–M3 PASS; M4 **nonpublishing technical automation acceptance PASS** while any actual production exercise remains outside #20; M5 **PARTIAL** (distribution chosen; main required PR/status Ruleset absent, trust/rollback not authorized); M6 **OPEN** (physical Windows/Razer hardware). Older M4 table entries describing the pre-RHC-20 pipeline as unimplemented are historical, not current state.
- **External #22 BLOCKED/OPEN:** active main Ruleset #24701145 still enforces deletion/non_fast_forward only. The least-privilege owner-admin setup + independent contract tests have been delivered but actual GitHub administration was not performed. Version remains `3.0.8.0` in `model.go`; `config/rhc-release-policy.json` is `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`, `distribution=repo-downloads`; `downloads/releases.json` empty, no official `downloads/latest.json`, product tag or released Windows binary. Physical native device testing, real first-release recovery/rollback, Windows Signing or explicit bound Unsigned consent and first actual release remain exclusively RHC-22 responsibilities.
