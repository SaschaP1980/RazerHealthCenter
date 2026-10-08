# Razer Synapse + Chroma Health Center (RHC)

This repository is being initialized as the future **single source of truth** for Razer Health Center.

> **Migration status — bootstrap in progress.** The canonical v3.0.8 source has been supplied and verified externally, but source import and GitHub-hosted CI/release qualification must be completed before this repository can be considered the complete project authority. Do not infer production release readiness from this documentation commit.

- Product baseline: **3.0.8**
- GitHub Issue namespace: **RHC-<GitHub issue number>**.
- New-chat entry point: [docs/INITIAL_PROMPT.md](docs/INITIAL_PROMPT.md) (added as part of initial setup).
- Migration plan and verified input evidence: [docs/MIGRATION_STATUS.md](docs/MIGRATION_STATUS.md).
- Reusable onboarding contract: [docs/templates/PROJECT_MIGRATION_TEMPLATE.md](docs/templates/PROJECT_MIGRATION_TEMPLATE.md).
- No product behavior changes, automatic deployments, or v3.0.9 release are authorized by this initial bootstrap.

Build and repair safety policies remain those of the v3.0.8 source. The release machinery must be adapted to Go/Windows rather than copying Lenovo Boot Selector's PowerShell packaging logic.
