# RHC — Release process contract (migration target)

## Current state: NOT ACTIVATED

Do not create a production RHC release from this document alone. RHC v3.0.8 **source import and exact Linux/Windows hosted qualification have completed** (PR #2; GitHub Actions run #37737410046), and the **read-only Candidate Preflight, exact-SHA Development Completion and Release Contract Rehearsal are now merged on `main` by PR #4**. However **the production Release Orchestrator and publication activation do not yet exist**. This document is the target process adapted from LBS's audited architecture, not permission to release.

## Source-native build contract

- Product: Go Windows amd64 GUI `RazerHealthCenter.exe`, with embedded diagnostic/repair resources and PS5.1 scripts.
- Initial baseline: Go 1.23.2; `model.go` owns `appVersion`/`referenceVersion` (3.0.8); `build.sh` executes existing permanent validators, `go test .`, i18n guard, Windows cross-`go vet`, `go build -trimpath`, resource patch, PE validation.
- Canonical intake EXE SHA-256 `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`; this is a golden **v3.0.8 baseline check**, not a hard-coded SHA for all future versions.
- The historical `tools/package_portable.py`/`tools/package_source.py` are retained as the unchanged v3.0.8 source; the old Source packager would accidentally recurse into the owner-uploaded original Source ZIP. Use new `tools/rhc_release_contracts.py` for future release staging: tracked-source allowlist, explicit exclusion of archives/logs/forensics, fixed ZIP timestamps/modes, six Portable payload sources plus SHA256SUMS and 12 explicit directories. Two independent package runs must be bit-identical.
- Windows-native PS5.1 parser/diagnostic contracts must be tested without executing live repair mutations. Real Razer device tests are separately operator-run acceptance, not hosted Actions.

## Future candidate contract (requires implementation)

For a narrow Patch/Hotfix, prepare one complete clean candidate from exact current `main`, including version, required documentation/release metadata and all generated inputs required by RHC packaging. Inspect exact tree/protected diff, then expose `candidate/vX.Y.Z`. Candidate Linux/Windows validations start in parallel on identical SHA; failing or unknown gates prevent release-branch creation. No unnecessary checkpoint commits for Fast-Path. A Work-Path has a separate frozen SHA and mandatory Development Completion before Candidate, preserving one cumulative `RHC` Issue ledger.

A GREEN Candidate promotion must check exact status provenance, tree/branch identity, latest current-main ancestry, no preexisting tags/branches, and strict scope/repair safety. Only the gated promotion may create `release/vX.Y.Z`; never create production release branches manually. The release orchestrator must rebuild independently from the pinned candidate, confirm EXE and source/portable package reproducibility, derive ZIP-free source tag, publish package with verified SHA/size, stage a single PR and run a **preactivation verification** before merge. The single reviewed source PR merge advances canonical `main`, **but is NOT public binary release activation**. For RHC's selected GitHub Releases distribution, the public activation point is publishing the completely verified Draft GitHub Release after the merge and prepublication checks. Never publish a half-populated Release. Postrelease verification must cross-check release statuses, PR, `main`, version pointer if adopted, exact tag/source, packages, integrity, cleanup and reproducibility. Only after PASS may the issue be closed.

**RHC-specific decisions still open:** Windows executable signing/trust; actual GitHub immutable-releases repository configuration and its verification; failure rollback and asset retention; branch policy and workflow token permissions; GitHub Release tag/source handling and Windows runner versions. **Distribution is decided**: GitHub Releases are canonical; no independently managed update pointer or automatic updater is planned initially. Resolve remaining items in separate tested changes with owner acceptance.

## Approved distribution contract — GitHub Releases plus derived catalog

**Owner architecture decision (2026-10-08):** `distribution=github-release` is selected in `config/rhc-release-policy.json`. `productionEnabled=false` remains a hard safety barrier. This is authorization to **design and test the distribution path**, not to publish any version.

- **GitHub Releases** is the sole canonical store for published Windows Portable and dedicated Source ZIPs, SHA-256 manifest, release notes, and machine-verifiable release evidence. Source remains versioned on `main`; avoid committing new compiled artifacts/ZIPs into source history.
- A **LBS-style download catalog** is only a derived read-only index of published GitHub Releases and their release assets; no duplicate ZIPs, independent version pointer, or conflicting `downloads/latest.json`. Start with GitHub's own Releases list/latest release for manual downloads. A generated UI/catalog can follow once the API/data rules are tested.
- **Single-publication transaction:** current-main-parent Candidate passes exact-SHA Linux/Windows checks; bounded promotion and a separately rebuilt Release pass; create a private/Draft GitHub Release with all expected assets and checksums; verify source commit/tag target and draft asset completeness; merge the single reviewed release source PR into `main`; independently verify merged source SHA and draft assets; **publish the verified Draft as the sole public activation event**; postpublication verify tag, release metadata, assets, sizes/SHA256, provenance, and the latest-release reference. Never activate during staging.
- **Immutable Release safety:** before enabling production, inspect and, if supported/approved, enable GitHub's immutable-release protection in repository settings; verify its behavior for Draft vs published assets/tag and test conflict/error handling. Do not claim the setting is active merely because it is desirable. Published artifacts must never be silently replaced; a failure after publication requires a controlled new-version corrective release rather than rewriting an immutable release.
- **Windows trust policy:** code signing and permitted unsigned-release policy are **undecided**. An executable and its own ZIP SHA256SUMS are integrity evidence, **not** equivalent to authenticode signing. No public activation until signing/trust acceptance is explicit and tested.
- **Rollback and retention:** define independently verified rollback/recovery when Draft, PR, merge, asset upload, publication or latest-release verification fails. Prior published releases must remain obtainable. Specify partial-failure decision ownership and idempotent recovery prior to production enablement.
- **No auto-updater initially:** the GitHub `/releases/latest` UI can serve manual download navigation. An automatic updater with signed manifest, installation consent and additional trust gates is a separate future design.

## Nonpublishing RHC-3 orchestration staging

- `rhc-infrastructure-ci.yml` runs hosted Linux full v3.0.8 Go/PE golden, deterministic ZIPs and native Windows PowerShell 5.1 plus Go/safety tests.
- `rhc-development-completion.yml` is an exact Work-Branch request gate. A fully qualified Work SHA can be stamped only with completed identical-sha Linux/Windows evidence and fresh `main` ancestry.
- `rhc-candidate-preflight.yml` triggers only for `candidate/vX.Y.Z`: a one-commit current-main-parent Candidate, higher three-part version, scoped release profile, issue trailer and full Linux/Windows tests. Its terminal promotion explicitly FAILS CLOSED; no release branch creation.
- `rhc-release-rehearsal.yml` runs adversarial tests and asserts `config/rhc-release-policy.json.productionEnabled=false`, with `contents: read` and no publishing action. A rehearsal PASS does **not** mean Release Verification PASS.
- A future production orchestrator must be independently built and end-to-end tested after the owner chooses distribution/update semantics and Windows signing/rollback. No new release can be published while the actual workflows have no publication privileges.

## Migration gate

The read-only `.github/workflows/rhc-source-intake.yml` is an exact v3.0.8 baseline-validation workflow (PR/one-off import-branch push/manual dispatch), *not* a Candidate/Release workflow and cannot publish. Source intake and hosted Linux/Windows qualification are PASS, but branch/security policy, reproducible post-import source packaging and production CI/CD safeguards are still OPEN.
