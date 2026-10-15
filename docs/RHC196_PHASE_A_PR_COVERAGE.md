# RHC-196: Phase A CI trigger and ordinary PR coverage

This is an **owner-authorized nonpublishing Phase A implementation**, responsible Issue [#196](https://github.com/SaschaP1980/RazerHealthCenter/issues/196), parent [#190](https://github.com/SaschaP1980/RazerHealthCenter/issues/190).

## Independent upstream and project evidence
GitHub requires approval for workflows triggered by `github-actions[bot]`-created PRs. LBS-110 reproduced `action_required / 0 jobs` while open and `failure / 0 jobs` after close. RHC PR #195 emitted three additional `failure / 0 jobs`: Infrastructure 38708905704, Downloads 38708905657 and Preactivation 38708905572. These remain historical FAIL, never interpreted as PASS. Exact-stage Downloads dispatch 38708897062 ran and passed one real job; Publisher 38708698590 passed 4/4 and independent RHC-102 38708967770 passed actual Linux HTTPS, native Windows and aggregate 3/3.

## Scope and preserved required gates

| Workflow | No longer matches the six-file version-only bot release PR | Ordinary PR matches retained | In-repo Work/main CI preserved |
| --- | --- | --- | --- |
| Infrastructure CI | `model.go` removed from PR paths | Tools, tests, workflow, locale and other source paths | `push: work/RHC-*` with model.go, Linux/native Windows/Node24 |
| Downloads Integrity | `downloads/**` removed from PR paths | Validator, contract tests, release policy and workflow | `push: main` and added `work/RHC-*`; mandatory staged `workflow_dispatch` |
| Release Preactivation | `downloads/**` removed from PR paths | Preactivation validator/tests, workflow and policy | Existing `push: work/RHC-*`, manual dispatch |

Actual required Candidate preflight, native Windows PowerShell 5.1, Go/PE/ZIP/repair safety, Publisher, exact SHA-bound staged Downloads dispatch and independent public RHC-102 are **unchanged**. No `pull_request_target`, elevated credentials, GitHub App, PAT, signing, product changes or release dispatch.

## Owner-approved LBS-style coverage policy (Phase A)

**Explicit owner decision: "Möglichkeit 1 – Einfachere Lösung. Das ist der LBS Ansatz."** This selects the simpler LBS-110 approach and **intentionally accepts** the loss of these additional `pull_request` checks for external/fork PRs that exclusively modify `model.go` or `downloads/**`. Their `work/RHC-*` push checks are available **only** on authorized same-repository Work branches. The repo's `main` ruleset currently prevents deletion/non-fastforward but **does not itself enforce required CI/review**; these filters do not make foreign forks secure by equivalence.

For any actual changes to those reserved product-version/public-download paths, use the owner-authorized canonical Issue-backed Work/Fast Candidate, exact-source Linux/native Windows qualification, safely staged Downloads dispatch, Publisher and independent public HTTPS/native-Windows RHC-102. Changes that do **not** follow those trusted pathways cannot be treated as qualified merely because GitHub permits a merge. Never label a zero-job run PASS. The owner consciously accepts the special-path external PR-check tradeoff rather than adding an App/PAT, `pull_request_target`, or a separate validation workflow. This authorization is for supplementary CI triggers, not production policy or relaxation of mandatory release gates.

**Completion boundary:** merging a qualified nonpublishing CI change is permitted following actual Work Development Completion and PR/merge readback. A future **separately owner-authorized real release** must independently confirm that no unwanted supplementary bot-release PR runs were created at its exact staged head; until then the live bot-PR acceptance is `NOT YET VERIFIED`, not PASS.

Tests `tests/test_rhc_196_ci_trigger_contracts.py` assert no match for exact historical release PR paths, retention of ordinary tool/policy/workflow PR filters, Work push and manual dispatch, and no unsafe `pull_request_target`. They are pattern-contract tests, not a live GitHub trigger proof. Actual Linux/native Windows Work CI and Development Completion must succeed before merge, then a later **separately authorized** actual release is needed to prove absence of new ancillary zero-job CI on its PR head. Never claim success from zero-job/skipped runs.
