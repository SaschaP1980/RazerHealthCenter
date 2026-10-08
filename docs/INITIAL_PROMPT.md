# RHC — Initial Prompt

> New-chat entry point: **Read** `https://github.com/SaschaP1980/RazerHealthCenter/blob/main/docs/INITIAL_PROMPT.md`.
> This is an operational project bootstrap, not an instruction to deploy without authorization.

## 1. Authority and current migration phase

Repository: `SaschaP1980/RazerHealthCenter`. Every new session must check the current GitHub `main` SHA, branch tree, active Issues and pull requests, plus `docs/MIGRATION_STATUS.md`. Previous chat history, local extracted ZIPs and remembered versions are **not** an authority. **During migration**, do not claim GitHub is a complete single source of truth until the complete v3.0.8 source import and hosted gates have been verified.

Current verified product baseline at initial bootstrap: **v3.0.8**. GitHub source import: **not yet complete**. No new product release is authorized.

## 2. Mandatory discovery

1. Read current `main`, `README.md`, this file, `docs/MIGRATION_STATUS.md`, `docs/RELEASE_PROCESS.md`, `docs/DEVELOPMENT_GUIDELINES.md`, `docs/GITHUB_HOWTO.md` and the current migration Issue [RHC-1](https://github.com/SaschaP1980/RazerHealthCenter/issues/1) including its comments.
2. If the full source is present, read `go.mod`, `build.sh`, `model.go`, `SAFETY-MODEL.txt`, `SOURCE-DELIVERY-CONTRACT.md` and relevant `tools/` scripts before choosing a change path. Otherwise report this as a **blocking missing-source condition**, not a successful bootstrap.
3. Distinguish verified local evidence from GitHub-hosted checks, Windows-native tests and real Razer hardware tests. They are not interchangeable.
4. Before any mutation, re-read `main`; use guarded commits or PRs, review exact scope, and avoid concurrent-state overwrites.

## 3. RHC-specific identity and safety

- Issue identity: GitHub Issue #N becomes `[RHC-N]`. Work branch when explicitly justified: `work/RHC-N`. Never use LBS prefix or create a second issue counter.
- Work-Path chat search markers (when an Issue-backed Work-Path is selected): `RHC<N>CHAT<12 random uppercase hex digits>`. Emit in an ordinary user-visible chat message and record in one cumulative Issue recovery comment. Do not claim to read private ChatGPT conversation IDs.
- Current RHC version format is `3.0.8`; the authoritative embedded version constants reside in `model.go` (`appVersion` and `referenceVersion`). Do not import LBS's four-component version schema or PowerShell-generated runtime assumptions.
- RHC is a Go Windows amd64 GUI application with bundled PowerShell diagnostic/repair scripts. No repair may run or elevate without the product's explicit confirmation and authorization checks. Preserve read-only verification, manifest registration checks, gate semantics and fail-closed behavior.
- Fast path for small patches/hotfixes: one complete atomic candidate with focused checks, then authoritative hosted Candidate gates; no product checkpoint chain. Work path for major changes or explicitly justified complex work: recoverable work branch, checkpoint ledger, exact-SHA Development Completion, then Candidate. **These are target policies; their hosted automation is not yet enabled.**
- Do not open a release, write `downloads/latest.json`, add production tags, or claim deployment during initial migration.

## 4. Finish with an evidence-oriented status

Report: current GitHub source completeness; current product version; live workflows and their actually verified results; open safety/CI/migration gates; current Issue/PR; and the next concrete action. A pass from a placeholder or manual-only workflow must not be presented as a published release.
