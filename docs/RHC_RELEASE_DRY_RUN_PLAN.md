# RHC-5 — GitHub Release Dry-Run and unsigned publication approval

**Status: PLAN ONLY / NO PUBLISHING.** [RHC-5](https://github.com/SaschaP1980/RazerHealthCenter/issues/5) tracks the future implementation and hosted verification of this plan. This document does not turn on any workflow or relax an authorization gate. `model.go` remains at v3.0.8.

## Owner decision and release authority

- No Windows code-signing certificate is currently available (owner-reported 2026-10-08).
- The canonical distribution choice remains **GitHub Releases** (published Source/Portable ZIPs, checksums, release notes, evidence); a LBS-style catalog is **derived read-only** from published Releases, not a second public file store/update pointer.
- An **unsigned release is a proposal, not approval**. The current authoritative policy stays `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`. Existing `publication_policy()` therefore refuses a production run.
- SHA-256 checksums, deterministic builds and GitHub attestations establish integrity/provenance according to their separate scopes. They do not add a publisher signature to the EXE, grant a Windows Authenticode identity or guarantee absence of SmartScreen warnings. Never instruct the product to bypass user/OS security prompts.

## The first implementation: pure nonpublishing state-machine simulation

Implement and test in a dedicated reviewed RHC Work branch after authorization of implementation work. The test workflow uses read-only permissions (`contents: read`, with `actions: read` only if actually needed); it has **no upload/Release/tag/branch mutation API call, credential with write scope, dispatch-to-publishing workflow or persisted Draft object**.

| State | Evidence required before advancing | Dry-run action |
| --- | --- | --- |
| `candidate-qualified` | New three-component version, exact current-main parent, Issue and release-profile trailers, Linux + Windows GREEN at same candidate SHA, no tag/version collision | Inspect fixture/read-only snapshots; reject stale/ambiguous evidence |
| `release-built` | Independent Go 1.23.2 Windows GUI build, mandatory Python/Go/PS5.1 safety tests | Execute original build without runtime repair mutations |
| `artifacts-verified` | Bit-identical Source and Portable ZIP pairs, exact filenames/sizes/SHA-256; no nested source ZIP/logs/forensics; Portable SHA256SUMS and empty directories validated | Save test manifest only as ordinary ephemeral job output, not a public Release |
| `merge-ready` | One reviewed source PR, protected diff, latest main ancestry and correct target version | Simulate preactivation and a single accepted PR merge; no real merge |
| `main-merged` | Simulated final main merge SHA and release intent | Re-evaluate source/tag target and no new competing main/version |
| `draft-ready` | Complete expected assets, release notes, verification evidence and final source SHA | Simulate a Draft object in memory/fixtures; **do not call GitHub create Release** |
| `publish-ready` | All exact-version, tag, source, artifacts, unsigned/signing approval and rollback guards GREEN | Assert `productionEnabled=false` prevents real publication, even if simulated inputs GREEN |
| `published-verified` | A *simulated* immutable publication event, asset provenance, final URLs/latest classification and recovery result | Test pure verification contracts; never create/publish actual GitHub Releases |

This first rehearsal must not create even a **Draft**, because creating one requires GitHub write access and may involve tag state. Staging real artifacts is a **later, separately authorized** integration phase.

## Event order for a future actual release (not authorized here)

1. Qualify the versioned Candidate and independent release packages on exact pinned SHAs. Temporary build artifacts may reside in private/nonpublic CI artifacts with bounded retention.
2. Premerge gate rechecks source/current-main ancestry, complete archives and approved release scope. One reviewed source PR merge advances `main` but **does not publish binaries**.
3. After merge, re-fetch the final `main` commit and verify its code/version against the Candidate. Only then create the version-specific Git tag / GitHub Release **Draft referencing the final merged source commit**, attach every asset, SHA256SUMS, release notes and evidence. This ordering avoids guessing the merge SHA when staging the Draft.
4. Independently verify Draft completeness, actual tag target, source-to-binary provenance, version uniqueness, asset sizes/checksums, current GitHub release-immutability settings and unsigned-specific explicit approval.
5. **Publish the verified Draft** as the sole public binary activation. Published immutable releases/tags/assets must not be rewritten. Verify published release and asset digests, provenance/attestation where supported and GitHub latest-release navigation after activation. <https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository>
6. Only after actual postpublication PASS close the version Issue and clean up temporary refs. A failed publication or postpublication test is a durable attention state, not success.

## Explicit unsigned-release authorization gate

Until a dedicated version Issue contains all of the following, the orchestrator **must refuse** unsigned publication:

- Explicit owner approval for that particular `vX.Y.Z` release; record approver and decision timestamp in its Issue.
- Exact **final merged source SHA**, source tag/version and **each** Source/Portable artifact SHA-256 and size, with matching independent hosted build evidence.
- A direct acknowledgement that the Windows executable is **not Authenticode-signed**, that checksums do not establish publisher identity, and that Windows/SmartScreen may show warnings. No instructions to bypass protections.
- Explicit expected README/release-note disclosure, approved manual integrity verification method, and confirmation that rollback/recovery and repository release protection requirements have been met.

The eventual release gate should validate a machine-readable signed-off approval record tied to version, final SHA and digests; a generic `unsigned-approved` string alone is insufficient. A per-version new consent is needed for a changed artifact SHA/commit. **This document and RHC-5 do not grant that consent.**

## Failure injection and restart guarantees

| Failure scenario | Expected result |
| --- | --- |
| Candidate SHA stale, main advanced, wrong PR head/version/tag | BLOCKED; no publication step |
| One hosted OS gate absent/failed/pending or status from another SHA | BLOCKED |
| Source/Portable hash/size mismatch, missing asset, duplicate name, incorrect tag target | BLOCKED |
| Ref or Release already exists, concurrent orchestrator retries, API throttling/timeout | Detect conflict; resume using matching pinned identity only, otherwise BLOCKED |
| Runner stops before source merge | No actual source or release activation; retry read-only validation |
| Source PR merged but Draft creation/upload fails | Public release stays absent; record durable unpublished-version state; supervised idempotent recovery, **never silently mark complete** |
| Draft incomplete or unsigned approval missing | Leave unpublished; no publish request |
| Publish partially succeeds or network times out | Query authoritative GitHub release state before any retry; never create duplicate public version |
| Immutable Release published but verification fails | Mark critical attention; preserve immutable assets, do not replace or delete; publish corrective **new version** after separate authorization |
| Previous working release needed | Keep prior immutable published assets retrievable; decide manual selection/recovery policy before release activation |

## Mandatory validation and performance evidence

- Characterization/negative tests must show the baseline publication policy fails closed. Add actual independent failing-input cases before accepting final GREEN.
- Validate workflow YAML, correct read-only token scopes and absence of write/mutation endpoints. Do not interpret zero-job invalid Actions YAML as a test failure.
- Hosted Linux original Go build/reproducibility and Windows-native PS5.1/Go/Razer diagnostic/repair safety must both pass on **one exact Work SHA**; Work Development Completion uses its actual status. A successful dry-run is **not** a published release.
- Measure Issue creation, Work freeze, queue start/end, setup, build, packaging, preactivation simulation, verification and recovery, including failed attempts; record in one cumulative RHC rolling comment.
- Acceptance: **zero** public Releases, Drafts, source tags, release refs, auto-update pointers, EXE/version modifications or production token grants. Until the separate owner decision, no real GitHub Release resource is to be created.

## Blockers after the dry-run

Real integration additionally needs (1) explicit unsigned approval for each version or verified code signing, (2) verified release immutability setting (applies to future releases), (3) branch PR/status restrictions and bot/minimum permissions, (4) rollback/retention validation and (5) owner-authorized release test. RHC-1 M5/M6 and RHC-3 M4 stay open until independently proven. This plan deliberately does not claim hardware acceptance or authorize v3.0.9.
