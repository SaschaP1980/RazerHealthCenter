# RHC-196: Phase A CI trigger and ordinary PR coverage

This is a **nonpublishing, unmerged proposal**, responsible Issue [#196](https://github.com/SaschaP1980/RazerHealthCenter/issues/196), parent [#190](https://github.com/SaschaP1980/RazerHealthCenter/issues/190).

## Independent upstream and project evidence
GitHub requires approval for workflows triggered by `github-actions[bot]`-created PRs. LBS-110 reproduced `action_required / 0 jobs` while open and `failure / 0 jobs` after close. RHC PR #195 emitted three additional `failure / 0 jobs`: Infrastructure 38708905704, Downloads 38708905657 and Preactivation 38708905572. These remain historical FAIL, never interpreted as PASS. Exact-stage Downloads dispatch 38708897062 ran and passed one real job; Publisher 38708698590 passed 4/4 and independent RHC-102 38708967770 passed actual Linux HTTPS, native Windows and aggregate 3/3.

## Scope and preserved required gates

| Workflow | No longer matches the six-file version-only bot release PR | Ordinary PR matches retained | In-repo Work/main CI preserved |
| --- | --- | --- | --- |
| Infrastructure CI | `model.go` removed from PR paths | Tools, tests, workflow, locale and other source paths | `push: work/RHC-*` with model.go, Linux/native Windows/Node24 |
| Downloads Integrity | `downloads/**` removed from PR paths | Validator, contract tests, release policy and workflow | `push: main` and added `work/RHC-*`; mandatory staged `workflow_dispatch` |
| Release Preactivation | `downloads/**` removed from PR paths | Preactivation validator/tests, workflow and policy | Existing `push: work/RHC-*`, manual dispatch |

Actual required Candidate preflight, native Windows PowerShell 5.1, Go/PE/ZIP/repair safety, Publisher, exact SHA-bound staged Downloads dispatch and independent public RHC-102 are **unchanged**. No `pull_request_target`, elevated credentials, GitHub App, PAT, signing, product changes or release dispatch.

## Coverage risk / mandatory activation decision

**This filter solution is not equivalent for ordinary fork/external PRs that modify exclusively `model.go` or `downloads/**`.** The `work/RHC-*` push event does not occur for foreign forks. Those paths belong to controlled Issue-backed Work/Candidate/Publisher publication by project process, but effective main ruleset currently only protects deletion and non-fast-forward; it does **not** require review/CI before all merges. The changed trigger alone cannot enforce that policy.

**Do not merge this draft or close Issue #196 unless** either (a) the owner separately accepts this specific loss of fork/special-path auto PR coverage as an explicit work-only publication policy with compensating premerge controls, or (b) a separately reviewed, technically enforced, safe replacement for these PR classes is implemented and qualified. Asking for Phase A implementation does not by itself prove that narrower policy consent.

Tests `tests/test_rhc_196_ci_trigger_contracts.py` assert no match for exact historical release PR paths, retention of ordinary tool/policy/workflow PR filters, Work push and manual dispatch, and no unsafe `pull_request_target`. They are pattern-contract tests, not a live GitHub trigger proof. Actual Linux/native Windows Work CI must succeed, then a later **separately authorized** actual release is needed to prove absence of new ancillary zero-job CI on its PR head. Never claim success from zero-job/skipped runs.
