# Razer Health Center — versioned Portable downloads

This directory is the durable, immutable build archive (LBS model).
Source code is versioned in GitHub and is **not** bundled in these ZIP files.
A Windows Portable ZIP contains only the runnable payload, directly unpackable once.
Published ZIPs must never be replaced or deleted; corrected builds get new versions.
The index and pointer are updated together with exactly one new ZIP by a verified PR merge.
Unreleased/unsigned QA artifacts from GitHub Actions are **not** official entries here.

## Builds

| Version | Portable ZIP | Size (bytes) | SHA-256 | Source commit |
| --- | --- | ---: | --- | --- |
| 3.0.8.11 | [RazerHealthCenter-Portable-v3.0.8.11.zip](RazerHealthCenter-Portable-v3.0.8.11.zip) | 8619978 | `93240b03e95d491f20adac2ca7e729ccb301864358b4b33e5030a32887c86efb` | `aaa1d85962380cd0995c48d90b5082f60135c958` |
| 3.0.8.10 | [RazerHealthCenter-Portable-v3.0.8.10.zip](RazerHealthCenter-Portable-v3.0.8.10.zip) | 8619990 | `0b34adda0c8dfcacb2f60c6755b04ac25a61143ecb04f13a0345e9f61f6c33aa` | `f9d1de6833b8959836d0a74e9e0cc6b83f366be6` |
| 3.0.8.9 | [RazerHealthCenter-Portable-v3.0.8.9.zip](RazerHealthCenter-Portable-v3.0.8.9.zip) | 8619985 | `642487db0b0cf09b54fc7b2572b55c54b84ab3f84fd4ba0129a608ce1e13ebea` | `c7e55f89b9c2a324cd9489b52633b658c6053471` |
| 3.0.8.8 | [RazerHealthCenter-Portable-v3.0.8.8.zip](RazerHealthCenter-Portable-v3.0.8.8.zip) | 8619982 | `67d4289f26b7f6b3ca1078a936aa840e9a58529e375156b9bcb5f3213eded4e1` | `83d894a8c556ab83286c7a0569032fd2ab4728b9` |
| 3.0.8.7 | [RazerHealthCenter-Portable-v3.0.8.7.zip](RazerHealthCenter-Portable-v3.0.8.7.zip) | 8619985 | `250a3a14fff0b76ef0cbef7a5753642e3a854554851e12a9655339311cff6843` | `5489f35d93c6313438c1ef3df81b50cf8aee6cf1` |
| 3.0.8.6 | [RazerHealthCenter-Portable-v3.0.8.6.zip](RazerHealthCenter-Portable-v3.0.8.6.zip) | 8619984 | `0f1d83135577a14cc60c83def4c9f7558d584cd2f3f92c6f8247ec0abf4bbc43` | `be87156880e3820f10237d4cafcb0b8812eaf325` |
| 3.0.8.5 | [RazerHealthCenter-Portable-v3.0.8.5.zip](RazerHealthCenter-Portable-v3.0.8.5.zip) | 8619985 | `ae681e4ec9ce3f337d437ae31d41494e59ff88dcddbd5f6fb94b617e94fb9aa1` | `182197e845bfd252988f27f417c4cd0f12092667` |
| 3.0.8.4 | [RazerHealthCenter-Portable-v3.0.8.4.zip](RazerHealthCenter-Portable-v3.0.8.4.zip) | 8619984 | `c84268bae98087bc5f6290e765f33fb822ed03c74764d0218ff057803be0f845` | `6284cdde8c2817d688bbed8ed921f72395ac06cc` |
| 3.0.8.3 | [RazerHealthCenter-Portable-v3.0.8.3.zip](RazerHealthCenter-Portable-v3.0.8.3.zip) | 8619978 | `40a7e166dc3cd1c88e4c3a16fb2494c05613b4316e64295c3b73bf131dce72bb` | `01716998f13c1b45dfa256ef73956c5cfb3162e6` |
| 3.0.8.2 | [RazerHealthCenter-Portable-v3.0.8.2.zip](RazerHealthCenter-Portable-v3.0.8.2.zip) | 8619982 | `f18d43cb0350ac9c20d9988ae2e0d8271e74086a807dfe53f4d2e92e7dcb86e0` | `b43c8f25f1f4190c8bf709c2bbefe6550aa920cd` |
| 3.0.8.1 | [RazerHealthCenter-Portable-v3.0.8.1.zip](RazerHealthCenter-Portable-v3.0.8.1.zip) | 8619984 | `c7a7ac150d236e85710454c61c806a6f3f4fb400d5309487ecbb88746f28c4c8` | `75b9209a90a192dba5f22665720a048195dc6881` |

## Unsigned test builds (not official releases)

An independently verified v3.0.8 **TEST / UNSIGNED** build is archived under [qa/](qa/README.md).
QA archives are excluded from releases.json and latest.json and are not production releases.

## v3.0.8.11 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.10 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.9 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.8 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.7 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.6 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.5 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.4 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.3 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.2 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.

## v3.0.8.1 interim-release disclosure (RHC-33)

**UNSIGNED WINDOWS EXECUTABLE. PUBLISHER NOT VERIFIED.**
This version is published under a documented temporary autonomous
release path with Razer physical-device acceptance, native rollback,
and Windows signing/SmartScreen owner approval deferred, NOT passed.
Windows Defender SmartScreen may warn about an unknown publisher.
Do not disable Windows security protection; verify the exact source
commit, ZIP SHA-256 and internal SHA256SUMS before using this build.
This disclosure does not mean Razer hardware behavior has been certified.
