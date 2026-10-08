# RHC — Release process contract (migration target)

## Current state: NOT ACTIVATED

Do not create a production RHC release from this document alone. The initial GitHub repository is being bootstrapped; all source files and hosted CI have not yet been imported/qualified. This document is the target process adapted from LBS's audited deployment architecture, not evidence that an RHC Release Orchestrator already exists.

## Source-native build contract

- Product: Go Windows amd64 GUI `RazerHealthCenter.exe`, with embedded diagnostic/repair resources and PS5.1 scripts.
- Initial baseline: Go 1.23.2; `model.go` owns `appVersion`/`referenceVersion` (3.0.8); `build.sh` executes existing permanent validators, `go test .`, i18n guard, Windows cross-`go vet`, `go build -trimpath`, resource patch, PE validation.
- Canonical intake EXE SHA-256 `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`; this is a golden **v3.0.8 baseline check**, not a hard-coded SHA for all future versions.
- Portable/source packaging owned by `tools/package_portable.py` and `tools/package_source.py`. Portable includes empty runtime directories plus internal file checksums; Source excludes output directories, EXEs and caches. Exact archive byte reproducibility requires controlling timestamps/archive metadata or comparing logical manifests unless byte determinism is independently demonstrated.
- Windows-native PS5.1 parser/diagnostic contracts must be tested without executing live repair mutations. Real Razer device tests are separately operator-run acceptance, not hosted Actions.

## Future candidate contract (requires implementation)

For a narrow Patch/Hotfix, prepare one complete clean candidate from exact current `main`, including version, required documentation/release metadata and all generated inputs required by RHC packaging. Inspect exact tree/protected diff, then expose `candidate/vX.Y.Z`. Candidate Linux/Windows validations start in parallel on identical SHA; failing or unknown gates prevent release-branch creation. No unnecessary checkpoint commits for Fast-Path. A Work-Path has a separate frozen SHA and mandatory Development Completion before Candidate, preserving one cumulative `RHC` Issue ledger.

A GREEN Candidate promotion must check exact status provenance, tree/branch identity, latest current-main ancestry, no preexisting tags/branches, and strict scope/repair safety. Only the gated promotion may create `release/vX.Y.Z`; never create production release branches manually. The release orchestrator must rebuild independently from the pinned candidate, confirm EXE and source/portable package reproducibility, derive ZIP-free source tag, publish package with verified SHA/size, stage a single PR and run a **preactivation verification** before merge. One PR merge is the public activation point. Postrelease verification must cross-check release statuses, PR, `main`, version pointer if adopted, exact tag/source, packages, integrity, cleanup and reproducibility. Only after PASS may the issue be closed.

**RHC-specific decisions still open:** output release distribution and updater pointer contract (do not copy `downloads/latest.json` blindly); signing and trusted Windows distribution; failure rollback and asset retention; branch policy and workflow token permissions; release tags and Windows runner versions. Resolve these through separate tested repository changes and owner acceptance.

## Migration gate

The manual-only `.github/workflows/rhc-source-intake.yml` is *not* a candidate or release workflow and cannot publish. Its baseline EXE hash check intentionally applies to v3.0.8 only. Do not enable new automatic deployment until RHC-1 source-intake, hosted build, policy and security checks have passed.
