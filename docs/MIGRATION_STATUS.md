# RHC v3.0.8 — Migration state and evidence ledger

**Status: SOURCE BASELINE MIGRATED AND HOSTED-VERIFIED.** The exact 321-file v3.0.8 source is now on GitHub `main` after PR #2. RHC production Candidate/Release automation, branch protection, updater/signing policy and physical Razer acceptance are **not yet approved or complete**. This is not a product release manifest.

## Authority transition

- Destination: [RazerHealthCenter](https://github.com/SaschaP1980/RazerHealthCenter), default branch `main`.
- Migration tracking Issue: [RHC-1](https://github.com/SaschaP1980/RazerHealthCenter/issues/1).
- Current canonical development **source** baseline: **v3.0.8** in `main`, merged from [PR #2](https://github.com/SaschaP1980/RazerHealthCenter/pull/2), final source-qualified PR head `2a28a08ba75ecb404df03847cdf1e5eaba941acd`, merge commit `daf3e4994f108299c9ed9aa47bbaf48b2ae720d9`. Original ZIP and portable archives remain provenance, not build authority.
- Prior Lenovo Boot Selector process is a **pattern**, never the runtime/build authority for RHC. Use the generic migration template in `docs/templates/PROJECT_MIGRATION_TEMPLATE.md`.
- The complete source and hosted reproducibility checks are now recoverable from GitHub. **Release/distribution authority remains a separate unimplemented phase**; do not infer a published RHC release from source verification.

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

## Product/build characteristics verified from the source

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
| M4 | RHC-specific Candidate, Release, preactivation and postrelease machinery built, tested fail-closed | **NOT IMPLEMENTED** |
| M5 | GitHub Actions permissions, branch policies, release-asset distribution, secrets, rollback verified | **NOT CONFIGURED / NOT VERIFIED** |
| M6 | Real native Windows/Razer acceptance for v3.0.8 false-positive fix | **OPEN in provided handover** |

**Release permission:** none. No synthetic production tag, no `downloads/latest.json` activation and no attempt to mark M2–M6 GREEN because M0 or M1 passed.

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
- GitHub repository rulesets query returned **zero rulesets**. Branch-protection query returned **403 Resource not accessible by integration**; required protection is **unverified**, not inferred from connector write ability.
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
- Repository policy remains unverified: no rulesets observed, branch protection API returned 403 for the integration; no owner-supplied attestation of external license/privacy clearance for the already-public archive. This is not a claim of a comprehensive legal audit.
- Source import is complete; **RHC-1 remains OPEN** for M4–M6 (release machinery, repository security/distribution policy, and real native acceptance).

## Next action

Proceed to M4–M6 only after a separate explicit scope decision: design/qualify RHC's secure Candidate, reproducible Source/Portable packages, release statuses and postrelease verification; validate branch/ruleset/Actions permissions and signing/updater choices. Do not publish v3.0.9 or alter native repair semantics as part of source migration.
