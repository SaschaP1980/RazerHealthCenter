# RazerHealthCenter — default repository agent workflow

This is an operator instruction for coding agents using this GitHub repository.
It is **not** a server-side GitHub Action or an authorization to release.

1. Read the live `main` SHA, [development guidelines](docs/DEVELOPMENT_GUIDELINES.md), and current Issue/PR/CI evidence. An initial bootstrap URL alone is read-only.
2. After a **separately explicit owner request** for a new **version-only** hotfix using `work/RHC-N`, the **default commit orchestration is RHC-170**: [default operator execution](docs/RHC-170-ATOMIC-WORK-PIPELINE.md#default-operator-execution-for-version-only-work-rhc-180).
3. Initialize and verify the numbered [RHC-N] Issue/taxonomy, saved original full 13-heading Rolling Comment **before** branch, frozen main, exact Work branch, and independently read back the post-branch same comment **before mutation**.
4. If a clean local Git checkout **and authenticated `gh` CLI** exist, execute the actual `tools/rhc170_atomic_work_pipeline.py` with explicit `--owner-authorized-new-version --apply --push` after all guards. Otherwise, when the already connected GitHub provider supports authenticated create-tree, create-commit and lease-checked ref update, use the [RHC-170-aligned connector atomic path](docs/RHC-170-ATOMIC-WORK-PIPELINE.md#connector-native-atomic-path-without-an-extra-github-app). Clearly label this as `CONNECTOR_ATOMIC_EQUIVALENT`, **not** a Python CLI execution. No extra one-off GitHub App or secret is needed for this existing authenticated connector pathway.
5. Never represent a `GITHUB_TOKEN`-authored GitHub Actions push as ordinary push-triggered Work-CI; GitHub suppresses those recursive push events. Verify genuine Work push-event Infrastructure/Development Completion, Candidate/Publisher, independent RHC102 and guarded closure at exact SHAs.
6. If the connector lacks the required atomic ref lease or no authorized executor exists, **STOP and report BLOCKED**, not silent serial write fallback or credential improvisation.
7. Non-version-only code, documentation and QA requests retain their correct fast/Work paths; do not use RHC-170's *version-only* two-file writer for unrelated changes.

**Scope and honesty:** Repository instructions establish the default for cooperating agents; they do **not** automatically launch a runner, change GitHub permissions, or prove an end-to-end speedup. Record real elapsed metrics for each future owner-approved hotfix. Existing Razer hardware, signing, rollback and safety constraints remain untouched.
