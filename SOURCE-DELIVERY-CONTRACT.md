# Source Delivery Contract — current and historical requirements

## Current RHC-12 / RHC-16 delivery authority

**GitHub source is canonical:** every future authorized four-part application version must have an independently buildable, **exact-source-SHA/tag-pinned** complete snapshot of Go code, Health/Repair Engines, PowerShell scripts, PE resources, assets, locales, validators, build scripts and documentation. Source provenance, cache/archive exclusion and reproducibility remain mandatory release gates.

The **single required user-facing binary package** is one immutable **lean seven-file** `main/downloads/RazerHealthCenter-Portable-vMAJOR.MINOR.PATCH.HOTFIX.zip`. No extra Source ZIP, nested ZIP, empty runtime folders or separate EXE. One verified atomic Release-PR merge advances the exact qualified Candidate bytes of `model.go` and `CHANGELOG.md` **and** adds the ZIP while simultaneously updating `downloads/releases.json`, `downloads/latest.json` and `downloads/README.md`. Six repository paths change; the distributed Portable ZIP retains exactly seven runtime files. The source tag remains pinned to the qualified Candidate commit. See [current release process](docs/RELEASE_PROCESS.md).

**No production release authorized:** `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`; Candidate promotion, Release Orchestrator and real hardware acceptance remain incomplete. Original historical v3.0.8 Source ZIP and archived v3.0.8 TEST / UNSIGNED QA are not official new-version downloads.

## Superseded pre-RHC-12 source-ZIP delivery rule (historical)

The original source handover required **two** distributable ZIPs per version: one Portable ZIP with runtime folder structure, and one independently buildable **Source ZIP** containing Go, Health/Repair Engines, assets, PE resources, locales, validators, build scripts and documentation. A standalone EXE was not required. This **separate distributed Source ZIP requirement was explicitly superseded by RHC-12**; independently buildable **GitHub source** remains mandatory. Historical reproducible Source-ZIP tests in `tools/rhc_release_contracts.py` still serve as nonpublishing test fixtures, not as the production download contract.
