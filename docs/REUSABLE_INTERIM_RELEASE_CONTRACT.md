# RHC — Reusable Interim Unsigned Release Contract

The implementation operates on the **current** four-part application version (`MAJOR.MINOR.PATCH.HOTFIX`) and verified prior public release, **never** on hard-coded package names, tags, source SHAs, CI run IDs or historical Issue completion states. For exact source/PR/Issue ancestry see [Git provenance](GIT_PROVENANCE_CONTRACT.md).

## Owner authorization and safety

**UNTIL EXPLICITLY REVOKED**, the owner authorizes qualified **unsigned/uncertified interim** releases. The separate signed/certified production controller stays fail-closed under live `config/rhc-release-policy.json` (standard values `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false` until separately authorized); do not set `productionEnabled`, `signingDecision` or `rollbackVerified` to favorable values without their separate required evidence. Physical Razer hardware tests, real system rollback, publisher identity/signature and SmartScreen publisher-trust remain `DEFERRED/NOT_VERIFIED` and are **NOT A RELEASE BLOCKER** in the explicitly qualified interim path, but must not be reported PASS.

Diagnostics are read-only. Razer repairs require explicit in-app confirmation, allowlist/PID/payload checks, pre-mutation rechecks, least privilege and read-only postrepair verification. CI never performs a real Razer repair. Public download notices must disclose unsigned executable, unknown publisher and possible SmartScreen prompts. Never disable Windows security protections.

## Standing default: new-version build requests imply a qualified interim release

The owner's **post-bootstrap instruction to build/create/increment a new application version** also authorizes, by default, publishing that qualified version using this **full autonomous unsigned interim release transaction**; no explicit additional "release" wording, per-version approval or renewed standing authorization is required. If a Work-Branch Path was requested, obey its Issue/complete BOOTSTRAP Rolling Comment/Work/Development Completion/Candidate gates. Successful delivery means the immutable versioned public `main/downloads/` ZIP, updated `latest.json`, append-only `releases.json`, `README.md`, exact source tag, one verified combined Candidate-source+downloads PR and final cleanup **all actually pass**; Candidate or build GREEN alone is not release completion.

This is **not** a trigger for a link-only `INITIAL_PROMPT.md` read-only bootstrap, unchanged-version build, docs-only work, internal QA/test artifacts or an express `build-only / no release` request. Explicit revocation, any failing or unverifiable hosted/native/safety/signature-state/catalog/tag/PR gate or unsupported GitHub permission means `BLOCKED/NEEDS_ATTENTION`, not inferred PASS or a partial distribution. Signed/certified standard production remains independently fail-closed, and external hardware/rollback/publisher trust remains `DEFERRED/NOT_VERIFIED` and openly disclosed for qualified unsigned interim releases.

## Mandatory repeatable transaction

1. Read live `main`, app/reference version, previous `downloads/latest.json`, full `downloads/releases.json`, real older ZIPs and version source tags, relevant Issues, PRs, refs and active workflow contracts. Target must be a strictly new public version with no duplicated tag/ZIP or conflicting branch.
2. Qualify the exact ZIP-free Candidate source SHA against current-main parent and, for Work-Path, prebranch persisted/readback BOOTSTRAP, genuine completed Work Linux/native-Windows qualification, Work-SHA and tree identity. Do not merge a separate source PR first.
3. Test two independent byte-identical PE and lean seven-file ZIP builds with SHA/manifest and prior archive immutability. Qualify actual hosted Linux build and separately **hosted native Windows PowerShell 5.1** parser, Go tests, repair-safety, Authenticode state and SHA-qualified provenance. A synthetic/failing/skipped/stale status is not a gate.
4. Stage **exactly four downloads publication files on the verified Candidate source commit**. Open **one combined Source+Downloads release PR** against the exact unchanged previous main, with responsible Issue, Candidate sourceSha and Work-SHA provenance. The combined PR contains the qualified source diff plus exactly four publication files. Independently validate real qualified Linux/native Windows and exact-stage downloads CI; no source-only PR is permissible.
5. Merge only the frozen validated combined source+downloads release head. Verify/create immutable version source tag at frozen source SHA. Independently reread public main merge/parents, actual ZIP/blob hash/size, latest/releases catalog, old release history, source tag/sha link and release branch cleanup with exact SHA lease. Generic Work cleanup is not release-branch cleanup.
6. Mark `RELEASE VERIFIED` only after successful real remote postpublication and tag/cleanup verification. For partial writes, preserve public bytes and perform readback-first bounded recovery; report exact failed workflow/sha and `BLOCKED/NEEDS_ATTENTION`. Do not infer future permission, tag or CI SUCCESS from an earlier version.

Every source/release PR links responsible Issues. Historical version-specific owner decisions, failures, CI/ZIP SHAs, mitigation and final outcomes live in those Issues' Rolling Comments, merged PRs and immutable Git history; this normative document stores **no** duplicated historical evidence.

Project process requires PRs, but current GitHub ruleset may not technically enforce required PRs: always read live effective protections. No unapproved admin permissions/policy modifications, self-approval or direct main bypass.

## RHC-98: Immutable retry after a failed unpublished Candidate

An existing Candidate source commit and branch remain immutable forensic evidence,
even after a failed publisher. A same-version retry is allowed only while the public
latest version remains unchanged, with no target tag, published ZIP, release branch
or prior retry branch and an actually completed FAILURE of the original publisher.
The previous exact publisher SHA and hosted job readback MUST prove Linux and native
Windows succeeded, staging failed, and finalization was skipped. A synthetic or
zero-job failure is insufficient. All checks fail closed before the first write.

A fresh Issue-backed full Work-Path on the current main must change only model.go
version literals and the truthful CHANGELOG.md. Its final message must contain
RHC-Issue, Release-Profile: version-only, Development-Completion: requested,
Recovery-Attempt: 1, Recovery-Original-Candidate: <SHA>, and
Recovery-Original-Run: <ID> with exact unique values. The hosted Development
Completion gate must cover precisely this new Work source and its current main.

A separate candidate/v<version>-retry1 commit has a single current-main parent and
the exact new Work tree. It is created once by the usual GitHub Candidate transfer,
and dispatched to the ordinary Linux/native Windows Candidate preflight and publisher.
Neither the original Candidate nor its Work ref may be overwritten or deleted.
The new publisher must revalidate the original failed run and the new real exact-SHA
statuses; prior successful hosted jobs are history, not transferable release approval.

The single-PR postmerge verifier checks two merge parents: previous public main
and staged PR. Staged PR has the ZIP-free Candidate as its sole parent; Candidate
has previous main as its sole parent. The combined public diff is exactly
model.go, CHANGELOG.md and the four canonical downloads paths. Tag points to
the ZIP-free Candidate, older ZIPs and catalogs stay append-only, and remote
public HTTPS ZIP hashing remains mandatory. Interim unsigned disclaimers, native
hardware/rollback/publisher trust NOT VERIFIED and standard production policy
false/unknown/false remain unchanged.
