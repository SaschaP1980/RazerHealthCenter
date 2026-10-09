# Razer Synapse + Chroma Health Center

Windows diagnostic and repair-assistance application for Razer Synapse and Chroma. Health/diagnostic operations are read-only; any repair requires explicit in-app user confirmation, safety guards and read-only post-repair verification.

## Live version authority

Read the **source/app** version directly from [`model.go`](model.go) (`appVersion` and `referenceVersion`). Read the **latest published Portable** independently from [`downloads/latest.json`](downloads/latest.json) and [`downloads/releases.json`](downloads/releases.json), verifying the real ZIP/hash and immutable version source tag/`sourceSha`. Current `main` may be newer than the tagged release source.

The [standard signed/certified production policy](config/rhc-release-policy.json) is separate from qualified owner-authorized unsigned interim publication; physical Razer hardware, rollback and publisher-trust status must never be invented.

## Project documentation and historical evidence

- [Initial Prompt](docs/INITIAL_PROMPT.md): fully reconstruct the current GitHub state.
- [Git provenance contract](docs/GIT_PROVENANCE_CONTRACT.md): mandatory Issue → changed-file PR → merged Git commit → release catalog/source tag links.
- [Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md), [GitHub Operating Guide](docs/GITHUB_HOWTO.md), [Release Process](docs/RELEASE_PROCESS.md), [Interim Contract](docs/REUSABLE_INTERIM_RELEASE_CONTRACT.md): permanent engineering and safety rules.
- [Migration evidence locator](docs/MIGRATION_STATUS.md): retrieve historical decisions and proof from GitHub Issues, Rolling Comments, PRs and Git; not from frozen status snapshots in normative Markdown.

Component versions and health checks are defined in actual source/tests. The reasons behind past releases and repairs are recorded in the owning GitHub Issues.
