# Changelog

## 3.0.8.4 — 2026-10-09

- Version-only HOTFIX: `appVersion` and `referenceVersion` advance from `3.0.8.3` to `3.0.8.4`. No functional, diagnostic, UI, Razer repair or PowerShell changes.
- RHC-72: Owner-authorized full Work-Branch Develop → Build → Candidate → qualified interim unsigned Release and remote verification. This source-only change does not itself constitute a release.

## 3.0.8.3 — 2026-10-09

- Version-only HOTFIX: `appVersion` and `referenceVersion` advance from `3.0.8.2` to `3.0.8.3`. No functional, diagnostic, UI, Razer repair or PowerShell changes.
- RHC-61: Owner-authorized complete Work-Branch Develop → Build → Release verification. A source version change alone does not approve publication; real interim-release gates and remote postmerge verification remain mandatory.

## 3.0.8.2 — 2026-10-09

- Version-only HOTFIX: `appVersion` and `referenceVersion` advance from `3.0.8.1` to `3.0.8.2`. No functional, diagnostic, UI, Razer repair or PowerShell changes.
- RHC-41: Explicit owner-requested Work-Branch process verification; this source bump is not itself a release approval. The existing v3.0.8.1 release files and standard release-policy gates are unchanged.

## 3.0.8.1 — 2026-10-09

- Version-only application HOTFIX: `appVersion` and `referenceVersion` advance from `3.0.8.0` to `3.0.8.1`. No Razer runtime, repair behavior, PowerShell payload, diagnosis or UI change.
- RHC-34: Version is moved onto `main` **before** the separate interim-publication PR. Release source and download ZIP must point to the same exact pre-release main commit; the historical `candidate/v3.0.8.1` remains frozen and must not be reused as a current-main release candidate.
- RHC-33 interim distribution: Windows EXE may be unsigned. Publisher identity, SmartScreen trust, physical Razer-hardware acceptance and target-system rollback are **not verified**, not claimed as passed. The release ZIP must disclose these limitations, retain Linux/native Windows regression checks and immutable source/ZIP hashes, and pass post-publication verification.
- All other product and Razer safety contracts remain unchanged. Original v3.0.8 QA/source archives are preserved.
