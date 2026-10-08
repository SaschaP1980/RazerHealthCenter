# RHC-3 — Candidate, Build, Deployment and Release architecture

**Status:** IN DEVELOPMENT / NONPUBLISHING. Implementation on `work/RHC-3`. App is **3.0.8**, original 321 source blobs untouched. Never infer that RHC production releases are active because this file or read-only qualification workflows exist.

## What is reused from Lenovo Boot Selector

The transferable contracts are a GitHub-current-SHA authority, exact Work-Branch checkpoint recovery and Development Completion for major work, **one** atomic Fast-Path Candidate for small Hotfixes, simultaneous Linux and Windows gates, status/commit/ancestry verification before promotion, a reproducible output package, one PR merge as publication activation, preactivation and postrelease evidence, cleanup, and measured queue/setup/build/test/orchestration intervals. No LBS application source, version JSON, WinForms/PowerShell runtime packaging or update-pointer is imported.

## RHC Go/Windows-specific mapping

- App/reference version from `model.go`, exact three-component semver. Candidate must advance beyond the true previous `main` version; 3.0.8 cannot publish on the infrastructure migration branch.
- Go 1.23.2; original `build.sh` must complete all static, Go and PE/resource tests. Use `GOFLAGS=-buildvcs=false` for a reproducible archive-origin v3.0.8 Windows GUI build.
- Hosted Windows 2025 must execute **real Windows PowerShell 5.1**, Go tests/vet, diagnostic/repair source checks. No live Razer hardware manipulation or repair invocation.
- Existing original `tools/package_source.py` is not release-safe after the original ZIP was uploaded to the repository root: it traverses and repackages the archived ZIP. New `tools/rhc_release_contracts.py` instead packages only an explicit tracked-source allowlist with fixed timestamps/permissions and disallows root original archives, forensics, historical build logs, EXEs and cache/temporary files.
- Portable package retains the original six user payload items plus its `SHA256SUMS.txt` and exactly 12 empty runtime directories. Both package outputs reproducible on repeat builds.
- The migration reference golden executable is `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`; this applies specifically to **v3.0.8**, never to future release versions.

## Explicit fail-closed publication barrier

**Distribution policy, Windows trust/signing decision, update-pointer contract, immutable artifact/version retention and rollback are not owner-approved.** Therefore the Work-Path infrastructure workflow is read-only and CANNOT publish GitHub Releases, tags, candidate/release branches or update pointers, and has no write scopes.

The staged [RHC Candidate Preflight](../.github/workflows/rhc-candidate-preflight.yml) runs on `candidate/v*` with **read-only** parallel Linux Go/package and native Windows PS5.1 jobs. `tools/rhc_candidate_entry.py` requires a single-commit exact-current-main candidate, strictly higher `model.go` app/reference version, unique `Release-Profile: version-only|patch` and `RHC-Issue: N` commit trailers, explicit scope validation and no forbidden secret/binary changes. The promotion job **always fails closed** and writes no release branch or tag until separate production activation is implemented. These Candidate branch paths have **not** been end-to-end qualified on a future release version.

`tools/rhc_orchestration_contracts.py` implements adversarial *pure* state-validation contracts for Candidate scope, stale Work-SHA/main completion, missing/non-success statuses, release policy and preactivation mismatch. [RHC Release Contract Rehearsal](../.github/workflows/rhc-release-rehearsal.yml) explicitly confirms `config/rhc-release-policy.json.productionEnabled=false` and has no publishing rights. The production Release Orchestrator must **still be built** after policy decisions: exact Candidate statuses and PR head; independent reproducible ZIP rebuild; trusted Windows distribution; staged pointer or immutable GitHub Release contract; preactivation; one reviewed activation PR; postrelease checks and cleanup. A successful read-only rehearsal is never a production release.

## Evidence and acceptance

- Local test-first contract: original baseline lacks `rhc_release_contracts` → RED; code added → 6/6 GREEN; golden 3.0.8 standalone local Source+Portable ZIPs twice are byteidentical; original source untouched.
- Hosted [Infrastructure Qualification run #37739340380](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37739340380) Linux and Windows both GREEN on checkpoint `517e4801989474780b8173dee5035d5f5a03b3e0`, and later [run #37739956526](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37739956526) GREEN for extended contract tests. Run #37739956589 independently verified the **no-publish** release-rehearsal guard. Latest final Work-head qualification and exact-SHA Development Completion remain pending.
- A Work-Path request must end with literal `Development-Completion: requested`. The workflow only records `development-completion/gate=success` after independent 2/2 hosted jobs completed on the **same unchanged Work SHA** while current `main` remains unchanged. Failed/skipped/invalid workflows do not count.
- Candidate promotion / automatic release: **NOT IMPLEMENTED**, M4 is **PARTIAL** until implemented and tested end-to-end on a later authorized version.
- Migration RHC-1 M5 (mandatory PR/status, signing and rollback) and M6 (Razer native device acceptance) remain OPEN.
