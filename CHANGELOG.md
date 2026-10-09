# Changelog

## 3.0.8.1 — 2026-10-09

- Version-only application HOTFIX: `appVersion` and `referenceVersion` advance from `3.0.8.0` to `3.0.8.1`. No Razer runtime, repair behavior, PowerShell payload, diagnosis or UI change.
- RHC-34: Version is moved onto `main` **before** the separate interim-publication PR. Release source and download ZIP must point to the same exact pre-release main commit; the historical `candidate/v3.0.8.1` remains frozen and must not be reused as a current-main release candidate.
- RHC-33 interim distribution: Windows EXE may be unsigned. Publisher identity, SmartScreen trust, physical Razer-hardware acceptance and target-system rollback are **not verified**, not claimed as passed. The release ZIP must disclose these limitations, retain Linux/native Windows regression checks and immutable source/ZIP hashes, and pass post-publication verification.
- All other product and Razer safety contracts remain unchanged. Original v3.0.8 QA/source archives are preserved.
