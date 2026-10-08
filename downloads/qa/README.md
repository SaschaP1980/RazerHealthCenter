# Razer Health Center v3.0.8 — TEST / UNSIGNED

**TEST BUILD ONLY — NOT AN OFFICIAL RELEASE.** This file is published for manual Windows/Razer acceptance testing. It is not a production release, not a signed installer, and not the `latest.json` release.

**Windows security:** `RazerHealthCenter.exe` has no Authenticode signature. Windows Defender SmartScreen or other security tools may warn about an unknown publisher. Do not disable security protection to use this test; only run this file if you trust its GitHub source and have verified the archive hash.

## Package

- [RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip](RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip) — original successful GitHub Actions artifact (unmodified).
- ZIP size: **8,696,796 bytes**.
- ZIP SHA-256: `277757f4a09fa12791e2912c3a59f32f277ef8b65756b5f0dd491516738f97c0`.
- Windows EXE SHA-256: `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`.
- Build source commit: [`09bcc0bff174739e3945f072a346bd036a7f3e4d`](https://github.com/SaschaP1980/RazerHealthCenter/commit/09bcc0bff174739e3945f072a346bd036a7f3e4d).
- Provenance: [successful GitHub Actions run #37761207280](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37761207280), artifact ID `11542516436`.
- Platform: Windows x64. ZIP contains exactly seven Portable files, `locales/de-DE.json` in its locale subfolder and no nested ZIP or Source ZIP.

## Verify before manual testing

After downloading the ZIP, run a read-only PowerShell hash check:

```powershell
(Get-FileHash .\RazerHealthCenter-Portable-v3.0.8-TEST-UNSIGNED.zip -Algorithm SHA256).Hash.ToLowerInvariant()
```

Compare its output to the SHA-256 above. Extract the ZIP once. Internal `SHA256SUMS.txt` lists the checksums for the Portable runtime files. The health/repair functions remain subject to explicit safety controls; this hosted build does **not** constitute native Razer hardware acceptance.

**Status:** QA archive only. Official `downloads/releases.json` remains empty and `downloads/latest.json` is absent. This archived TEST binary is never silently promoted to an official release.
