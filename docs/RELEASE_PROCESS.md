# RHC — Release Process

This is a **version-neutral operating contract**, not a release history. For the actual release, read Git/GitHub and `model.go`, `downloads/latest.json`, `downloads/releases.json`, ZIP bytes and immutable source tag, then trace source/release PRs to owning Issues. See [Git provenance](GIT_PROVENANCE_CONTRACT.md) and [Interim Contract](REUSABLE_INTERIM_RELEASE_CONTRACT.md).

## Live source, release, PR and Issue chain

- Current application source: `appVersion`/`referenceVersion` in `main/model.go`, with the actual Git source commit and CHANGELOG context; the app version is **not** inferred from the latest commit subject.
- Latest published release: `downloads/latest.json` reconciled with `downloads/releases.json`, actual immutable ZIP SHA-256/size/internal checksums and matching `vX.Y.Z.H` source tag at `sourceSha`. Public source SHA can be older than today's main.
- For every source or release PR, verify its actual merged head/parents and explicit responsible `[RHC-N]` Issue references; each Issue/Rolling Comment is the historical why/decision/test ledger. A tag, green Candidate or documentation title alone does not prove publication.
- Every changed-file PR including documentation is Issue-backed. Docs-only changes use a lightweight PR, not a product Candidate or release. No routine direct-to-main commits; effective platform PR ruleset enforcement must be independently checked rather than assumed.

### GitHub Actions PR-creation permission

For new repositories, [GITHUB_HOWTO.md](GITHUB_HOWTO.md) defines **manual repository setup** and the mandatory **GitHub Actions PR-creation permission** check through a real, scoped **nonpublishing** PR test. Verify effective permissions independently before relying on autonomous staging.

## Package and release safety

Use the executable `tools/rhc_downloads.py` and current validators for reproducible lean ZIPs, version/provenance and append-only history. The current runtime payload allowlist contains **seven files**: `RazerHealthCenter.exe`, `README.txt`, `README-I18N.txt`, `SAFETY-MODEL.txt`, `SHA256SUMS.txt`, `i18n-manifest.json`, `locales/de-DE.json`. A separately authorized and tested contract change is needed to alter this set.

Distribution is tracked `main/downloads/`, **not GitHub Releases assets**. Source lives in Git at the version tag; the public ZIP contains no nested Source ZIP or QA/forensics data. A newly published version adds an immutable `downloads/RazerHealthCenter-Portable-vX.Y.Z.H.zip` and updates `downloads/README.md`, `downloads/releases.json` and `downloads/latest.json`; prior published ZIP bytes and catalog history must remain unchanged. `downloads/qa/` denotes historical TEST/UNSIGNED builds, not latest public releases.

App/release version format is `MAJOR.MINOR.PATCH.HOTFIX`. Read the current authoritative source and real prior public latest before computing the next legal version. Never force a historic binary hash onto a different current source SHA.

## Standard versus separate interim release path

**Standard signed/certified production** remains fail-closed under actual live `config/rhc-release-policy.json` and its required owner approval, effective main protection, verified rollback, publisher/signing and exact technical CI. Do not change those machine values merely to publish.

**Interim unsigned/uncertified release** is separately authorized by the owner **until explicitly revoked**. Physical Razer hardware tests, actual native rollback and trusted publisher/signing/SmartScreen acceptance stay `DEFERRED/NOT_VERIFIED`, not release blockers **in this distinct mode**. Never report them PASS or present an interim ZIP as signed/certified. Disclose an unsigned Windows EXE, unknown publisher and possible SmartScreen warnings. Hosted Linux and native Windows PowerShell 5.1/repair safety, PE/ZIP determinism, catalog/tag/provenance, PR checks and final remote verification are still compulsory.

## Default trigger: an owner-requested new version includes publication

Once a user has separately instructed creation, build or increment of a **new** RHC product version after read-only bootstrap, interpret that version request as **authorization for this entire source → Candidate → public interim publication → verification transaction**, without requiring the user to type "release" or separately approve the next qualified unsigned/uncertified interim release. Follow any explicitly specified Work-Branch Path (with its mandatory full BOOTSTRAP Rolling Comment) and all source/Candidate, Linux/native Windows security, release PR and remote verification gates. The new version is delivered only when the *actual immutable ZIP under `main/downloads/`*, updated latest/releases/README, matching immutable source tag, exact source+release PR provenance and cleanup have been verified; a build artifact or successful Candidate is not a published release.

This implicit trigger **excludes** link-only initial readback, documentation work, unchanged-version rebuilds, QA/test runs and explicit instructions to build only or not publish. Owner revocation and any failed/missing qualification **block** publication and must be recorded rather than silently changing the goal. It does not activate or weaken the standard signed/certified production policy or convert external Razer hardware, rollback, signature and SmartScreen trust `DEFERRED/NOT_VERIFIED` into PASS. The existing until-revoked authorization applies **only** to the separate qualified, visibly unsigned interim path.

## Verified source-to-publication transaction

1. Qualify an Issue-backed source change with applicable Fast-/Work-/Candidate entry and exact-SHA Linux/native Windows security gates. Work-Path requires the pre-branch BOOTSTRAP Rolling Comment and Development Completion. A source-first **interim** PR may merge `model.go`/`CHANGELOG.md` first; freeze the real merged main **sourceSha**. A separate publication PR then changes exactly **four downloads paths**, linking its Issue(s) and qualifying source PR/Issue. The independently governed ordinary standard-production flow may instead require an atomic **six-path** source + downloads PR. Never interchange these semantics to avoid a gate.
2. Prove two independent byte-identical Windows GUI PE builds and two identical Portable ZIPs; validate correct version, files, hashes, old history immutability and unambiguous source tag. Run real hosted native Windows 2025/PowerShell 5.1 including read-only Razer safety and Get-AuthenticodeSignature, distinct from Linux crossbuild.
3. Stage only a unique, scoped, one-parent release branch/PR. Check actual effective GitHub PR/dispatch/write permissions, main/ref SHA leases, exact staged head, Linux/native Windows/downloads/release checks. GitHub Actions bot pushes may suppress normal PR workflows; dispatch trusted checks when expressly permitted.
4. Merge only unchanged, approved exact head with necessary statuses. Create or independently verify immutable version tag at **frozen sourceSha**. Read back actual public main merge/parents, ZIP SHA-256/size/bytes, releases history, latest pointer, tag identity, PR/Issue links and exact-lease **release-branch cleanup**. The generic Work cleaner is not authorized to delete release branches.
5. Report `RELEASE VERIFIED` **only** when remote public outcome and required postrelease finalization are true. Partial publication/failed tag/cleanup is a separate `BLOCKED/NEEDS_ATTENTION` recovery state. Never edit previous ZIP bytes or silently retry uncertain writes.

Historically failed actions, concrete version-specific permissions and actual source/package/CI hashes are documented in their responsible Issues and Rolling Comments, **not mirrored here**.
