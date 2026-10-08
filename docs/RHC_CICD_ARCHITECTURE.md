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

A future RHC Candidate Preflight must check same-issue branch/path, exact `model.go` version, prior `main` ancestry, protected file diff, Go/Linux and Windows statuses for the **same SHA**, and no tag collision. Successful Work-Path Development Completion cannot be assumed from a successful read-only infrastructure smoke.

A future Release Orchestrator must prove: matching candidate statuses and PR head; independently rebuilt and bit-identical source/portable ZIPs; signed/unsigned Windows distribution explicit decision; staged pointer or GitHub Release activation contract; preactivation invariants; **one** reviewed merge; postpublication exact checks; safe cleanup. Inability to publish or use the required bot token means BLOCKED, never PASS.

## Evidence and acceptance

- Local test-first contract: original baseline lacks `rhc_release_contracts` → RED; code added → 6/6 GREEN; golden 3.0.8 standalone local Source+Portable ZIPs twice are byteidentical; original source untouched.
- GitHub-hosted `rhc-infrastructure-ci.yml` Linux/Windows GREEN needed for this checkpoint, with run ID, checksums and actual durations.
- Candidate promotion / automatic release: **NOT IMPLEMENTED**, M4 is **PARTIAL** until implemented and tested end-to-end on a later authorized version.
- Migration RHC-1 M5 (mandatory PR/status, signing and rollback) and M6 (Razer native device acceptance) remain OPEN.
