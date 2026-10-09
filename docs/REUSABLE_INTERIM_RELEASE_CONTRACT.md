## Active RHC-43 version-independent interim Publisher contract — 2026-10-09

[Reusable Publisher workflow](../.github/workflows/rhc-reusable-interim-release.yml) triggers on a main model.go version change; [Postmerge remote verification/tag workflow](../.github/workflows/rhc-reusable-interim-postmerge.yml) binds actual merged download ZIP, catalog, tag and NotSigned PowerShell proof. Both retain source SHA and old release-history immutability; the separate standard production controller stays fail-closed.

**A source-controlled workflow is not an executed release.** Require actual GitHub Actions write/PR/dispatch permission evidence, trusted hosted Linux/native Windows test results at correct source and staged SHA, real PR/merge, postpublish remote readback and safe cleanup before RELEASE VERIFIED. A denied GitHub-token createPullRequest or unverified tag triggers BLOCKED/NEEDS_ATTENTION; do not synthesize approvals, bypass negative checks or inherit the historical one-version exception. Release status must be read live from model.go and the main/downloads latest/releases ZIP, not inferred from this text.

---
# RHC-43 — Reusable autonomous interim release: implementation and verification contract

**Language:** All new GitHub issues, pull requests, documentation, code, commit messages, GitHub Actions log summaries and release notes are authored in **English**. The owner speaks German in chat with English engineering terminology.

## Source and governance

- Authoritative inputs must be live GitHub main and issues plus real executable tools/tests: current model.go appVersion/referenceVersion and CHANGELOG; current downloads/latest.json and append-only downloads/releases.json; exact existing tags, refs, PR states and immutable ZIP hashes; current config/rhc-release-policy.json.
- The original RHC-34 release mechanism was intentionally limited to **v3.0.8.1**. Source tag v3.0.8.1 and previously distributed ZIP are immutable historic evidence. Reusable mode is a new implementation owned by [RHC-43](https://github.com/SaschaP1980/RazerHealthCenter/issues/43).
- The current issue-backed product hotfix is separately owned by [RHC-41](https://github.com/SaschaP1980/RazerHealthCenter/issues/41) and [PR #42](https://github.com/SaschaP1980/RazerHealthCenter/pull/42). It changes only two model.go version constants and the CHANGELOG; never hide infrastructure changes in its version-only two-path diff.
- The standard production controller remains fail-closed with productionEnabled=false, signingDecision=unknown and rollbackVerified=false. Phase B remains OPEN/PAUSED under RHC-22 and RHC-33; the explicit interim unsigned/uncertified mode is separate, not a disguised production approval. Future reinstatement of Phase B requires a fresh specific owner decision.

## Minimum real pipeline

1. **Scope and bootstrap:** On an explicit request for a full Development → Deployment → Release cycle, verify current main, previous public latest, existing archives, candidate refs, issues and exact change scope. Follow an owner-requested Work-Path with BOOTSTRAP-before-branch Rolling Comment, readbacks, native Work Linux/Windows, completion and Candidate; otherwise the normal Fast-Path. Do not create duplicate candidate tags/refs.
2. **Version:** The next HOTFIX increments component four by exactly one, with appVersion and referenceVersion agreeing. A new version must be strictly newer than actual public latest and cannot reuse a previous tag/ZIP. Other Razer/engine/migration versions are separate.
3. **Evidence:** Run permanent regression contracts, Go test/vet, all build.sh safety validators, two independent byte-identical Windows PE builds and identical seven-file portable ZIPs, plus real native hosted Windows PowerShell 5.1 parser/repair-safety and an actual Get-AuthenticodeSignature check. Hosted static/crossbuild and physical Razer testing remain separate evidence classes.
4. **Uncertified trust:** The interim classification must report unsigned status (NotSigned), unknown publisher, possible SmartScreen warning, and physical Razer/rollback/owner signature/manually administered protection as DEFERRED/NOT_VERIFIED. Never claim that an unsigned interim ZIP is signed, publisher-certified or hardware-qualified. No automatic Razer repair, privilege elevation or PID-unknown bypass.
5. **Source-first promotion:** A qualified version-only source PR can be merged into main in a separate tested transaction, then source SHA freezes. A subsequent release PR changes exactly four downloads paths, not a duplicate source model; requires exact source reference, current main parent, tested status and old-history integrity.
6. **Publication:** Stage a *new* immutable seven-file ZIP with canonical filename, releases.json history and latest.json pointer, README trust notice; verify all previous archives unchanged. Test and explicitly authorize required GitHub App/Actions PR/dispatch permissions and exact hosted release-branch Linux/native Windows/downloads checks before remote writes. GitHub-token-recursion suppression requires explicit supported dispatch; a permission error stops the flow and is retained as evidence.
7. **Postrelease verification:** Merge only a uniquely selected exact verified PR with unchanged head/source, then create or independently verify the correct immutable tag pointing to pre-release main/source SHA. Re-fetch actual GitHub main/merge SHA and parents, model.go/CHANGELOG, released ZIP blob bytes or exact hash/size, releases.json/latest.json, old archives, SHA-bound provenance and branch cleanup. Safe, lease-checked cleanup is a distinct status and never assumed successful merely from merge.
8. **Completion:** Claim RELEASE VERIFIED only after publication and independent postpublication checks; otherwise mark BLOCKED/INCOMPLETE with exact failed workflow/job/SHA/issue and recover read-only before retries.

## RHC-41 concrete failures to retain

- [Legacy v3.0.8.1 interim run #37889334544](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37889334544): FAILED because v3.0.8.2 source PR unexpectedly triggered a one-version-only writer. This is a workflow event-scope bug, not evidence that v3.0.8.2 is an invalid hotfix.
- [Prepublication rehearsal #37889334478](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37889334478): FAILED because a legitimate published latest.json invalidated the historical empty-catalog fixture; retain the negative assertion but remove its inappropriate ordinary-new-version PR trigger.
- [Work Linux/native Windows + Completion](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37889269575) succeeded; [Candidate #37889390987](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37889390987) showed 3/3 exact-SHA success and deliberately failed ordinary Promotion. Do not conflate the blocked standard production job with failed OS safety or a completed interim publication.
- The new first RED test file was initially named outside the real test discovery glob; host CI did not execute it. It was renamed to match tests/test_rhc_*_contracts.py, and genuine 2-test RED against the old workflow triggers was then observed on hosted Linux run [#37890655272](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37890655272). Test discovery is part of evidence, not an administrative detail.

## Implementation versus approval matrix

| Contract | Current status |
| --- | --- |
| Reusable interim-mode owner process direction | AUTHORIZED FOR IMPLEMENTATION |
| Existing historical v3.0.8.1 public release | ALREADY PUBLISHED, IMMUTABLE |
| Current v3.0.8.2 Work/Candidate technical gates | PASS, NONPUBLISHING |
| RHC-43 focused regression and CI trigger hygiene | IN PROGRESS — verify final SHA |
| Reusable real GitHub stage/PR/merge/postverify writer | **NOT YET QUALIFIED** |
| Current v3.0.8.2 main/latest ZIP/source tag | **NOT PUBLISHED/VERIFIED** |
| Physical Razer acceptance, publisher trust, rollback | DEFERRED / NOT VERIFIED |
| Standard production policy | DISABLED, UNCHANGED |

Do not remove this explicit implementation-status distinction merely because documentation has been updated.
