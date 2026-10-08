# RHC v3.0.8 — Migration state and evidence ledger

**Status: SOURCE INTAKE NOT COMPLETE.** This document records verified inputs and the repository setup separately; it is **not** a product release manifest or a claim that all source bytes are present in GitHub.

## Authority transition

- Destination: [RazerHealthCenter](https://github.com/SaschaP1980/RazerHealthCenter), default branch `main`.
- Migration tracking Issue: [RHC-1](https://github.com/SaschaP1980/RazerHealthCenter/issues/1).
- Current source-release baseline: **v3.0.8**. The user-provided source and portable archives remain historical intake evidence until all files are committed and independently qualified from GitHub.
- Prior Lenovo Boot Selector process is a **pattern**, never the runtime/build authority for RHC. Use the generic migration template in `docs/templates/PROJECT_MIGRATION_TEMPLATE.md`.
- This repository's initial README and process documents establish the *destination* authority, not yet the *complete* source-of-truth state.

## Verified input identity (2026-10-08)

| Artifact | SHA-256 | Observation |
| --- | --- | --- |
| v3.0.8 Source ZIP | `f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495` | 4,627,837 bytes; **321 regular files**; ZIP CRC/integrity PASS |
| v3.0.8 Portable ZIP | `30df1141c660d6fc50969aeb7c3a388f350d4977f7c5aa7c1fa3d3ba087e3ea7` | 8,621,194 bytes; 7 regular files plus 12 explicit directories; ZIP CRC/integrity PASS |
| Release and local rebuilt EXE | `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a` | Cross-built Windows amd64 GUI EXE is byte-identical to supplied reference |
| Source-side AppEngine diagnostic 1.0.2 | `4ac0f44212a5c53db932f6033a6fa53fa0c60a9b5b7a125f9485e17a39bd6121` | From supplied v3.0.8 handover; not remeasured independently during bootstrap |
| Source-side AppEngine recovery 1.0.0 | `ff53cdabcd7c046c25e15ca30419986ace3012532b05e83a9b681e28de6f738a` | From supplied v3.0.8 handover; not remeasured independently during bootstrap |

Independent local validation used **Go 1.23.2 Linux/amd64** with `GOPROXY=off`, `GOSUMDB=off` and `GOTOOLCHAIN=local`. The source `build.sh` completed its Python static/regression validators, `go test .`, the i18n guard, Windows cross-platform `go vet`, Windows amd64 `go build -trimpath -ldflags='-H windowsgui'`, resource injection and PE validation. The full clean rerun reproduced the exact reference EXE SHA-256 above. **This is local evidence, not yet a GitHub-hosted Actions run.** Windows-native PowerShell 5.1 and real Razer hardware acceptance are separately pending.

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
| M2 | Complete reviewed source tree imported to GitHub with original content byte equality | **BLOCKED / not imported** |
| M3 | GitHub-hosted source intake reproduces the golden EXE; Linux and Windows checks | **NOT RUN** |
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

## Next action

Import the **reviewed complete 321-file source tree** into the existing Draft PR #2 using the verified branch-specific importer, review all publicly published content, and push the source manifest. The PR-triggered Linux and Windows intake workflow will run automatically. Only after both hosted tests PASS and a verified source-byte audit may PR #2 merge; then plan the RHC-specific production Candidate/Release pipeline separately.
