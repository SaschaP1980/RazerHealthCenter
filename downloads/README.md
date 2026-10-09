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
| 3.0.8.3 | [RazerHealthCenter-Portable-v3.0.8.3.zip](RazerHealthCenter-Portable-v3.0.8.3.zip) | 8619978 | `40a7e166dc3cd1c88e4c3a16fb2494c05613b4316e64295c3b73bf131dce72bb` | `01716998f13c1b45dfa256ef73956c5cfb3162e6` |
| 3.0.8.2 | [RazerHealthCenter-Portable-v3.0.8.2.zip](RazerHealthCenter-Portable-v3.0.8.2.zip) | 8619982 | `f18d43cb0350ac9c20d9988ae2e0d8271e74086a807dfe53f4d2e92e7dcb86e0` | `b43c8f25f1f4190c8bf709c2bbefe6550aa920cd` |
| 3.0.8.1 | [RazerHealthCenter-Portable-v3.0.8.1.zip](RazerHealthCenter-Portable-v3.0.8.1.zip) | 8619984 | `c7a7ac150d236e85710454c61c806a6f3f4fb400d5309487ecbb88746f28c4c8` | `75b9209a90a192dba5f22665720a048195dc6881` |

## Unsigned test builds (not official releases)

An independently verified v3.0.8 **TEST / UNSIGNED** build is archived under [qa/](qa/README.md).
QA archives are excluded from releases.json and latest.json and are not production releases.

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
