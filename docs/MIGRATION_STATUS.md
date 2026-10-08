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
| M1 | Empty GitHub repository initialized with migration docs, Issue and reusable template | **IN PROGRESS until commit/diff verified** |
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

## Next action

Import the **reviewed complete 321-file source tree** on top of this GitHub bootstrap without introducing runtime changes; verify a source-path and byte-hash manifest; then deliberately dispatch the **manual-only** `RHC Source Intake` workflow and validate hosted output. Only then consider wiring the LBS-style automatic Candidate/Release pipeline to RHC's own Go/PowerShell artifacts.
