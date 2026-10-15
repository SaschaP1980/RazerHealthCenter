# RHC-200 — Phase C: RHC-110 non-applicability and guarded RHC-158 closure

Scope/owner: [RHC-200](https://github.com/SaschaP1980/RazerHealthCenter/issues/200), parent [RHC-190](https://github.com/SaschaP1980/RazerHealthCenter/issues/190). NONPUBLISHING implementation. No new product version, Candidate, ZIP/catalog, tag, repair/UAC, signing/production policy, GitHub App/PAT or extra privileged workflow.

## RHC-110: avoid false corrective audits after successful public RHC-102

Historic evidence: Phase A main merge caused [#38723531768](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/38723531768) and Phase B [#38727306493](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/38727306493). Both genuinely executed one failed recheck job: `original failed exact-release verifier missing`. Public v3.0.8.24 RHC-102 had independently succeeded 3/3, therefore no corrective RHC-102 was eligible. Those historical failures remain FAILURE, never PASS.

At an automatic cleanup `workflow_run` or hourly schedule only, the new classifier obtains the latest actual published release provenance and matches one uniquely identified original postrelease verification run using **exact historical release merge SHA and four-part version**. It recognizes N/A only with authenticated RHC-102 `workflow_dispatch`, trusted `github-actions[bot]` identity, completed-success, positive run attempt and **three separate actually executed completed-success jobs** with exact Linux HTTPS, native Windows and aggregate names. Then it prints `RHC110_RECHECK=NO_DISPATCH_NA` and does not dispatch new workflows. Missing/failed original audits **never** become N/A; zero-job, skipped, inconsistent or duplicated historical runs BLOCK. Manual `workflow_dispatch` never receives this shortcut. Existing corrective-work owner review, source SHA, main/tag, safety, earlier real failure and dedupe gates remain in force for eligible recoveries.

This is an explicitly documented N/A, **not a retroactive green status** for any historical failure.

## RHC-158 / RHC-139: fail-closed diagnostic and retry/reconciliation

The closure worker previously logged only `RHC158_CLOSURE_BLOCKED_NOT_VERIFIED`. It now emits a stable `code` / `exception` with no raw exception payload, credentials, API response or private Issue body. Known predicate families include `ROLLING_PREWRITE_CONFLICT`, `POSTWRITE_READBACK_UNVERIFIED`, `PUBLISHER_WAIT_TIMEOUT`, `HOSTED_GATE_NOT_VERIFIED` and `ELIGIBILITY_OR_AUDIT_BLOCKED`.

**Only** the two existing optimistic concurrency checks strictly *before the first comment PATCH* can retry, at most three times. Before every retry the worker independently recollects full release/source/Work/Issue/PR/tag and five actual hosted run proofs and requires exact proof equality and the Issue still open. An ambiguous postwrite/failed readback is NEVER blindly retried, because the first remote write may have succeeded. GitHub comments PATCH offers no guaranteed compare-and-swap transaction; concurrency is therefore still fail-closed, not falsely claimed atomic.

If the real Issue was already closed/completed but the final `COMPLETED` journal write was interrupted, a retry may repair only an existing `WAITING_FOR_GITHUB` canonical journal with exactly the same five individually verified RHC-139 events, unchanged authenticated merge/main identity, matching Issue closed_at and repeated comment readbacks. It **does not close the Issue a second time**, rewrite event history, synthesize gates or assume an unknown API failure succeeded. A completed terminal journal remains idempotent no-write on a duplicate event.

## Proof requirements, remaining limitations

Negative-test RED commit precedes implementation. Actual hosted Work Infrastructure Linux/native Windows/Node24, Development Completion and PR Infrastructure must pass exact final SHA. The workflow's permission profile remains `issues: write` / read-only other scopes for closure, and `actions: write` only for the guarded RHC-110 independent verifier dispatch. Untrusted `pull_request_target` and bypasses prohibited.

**Live automated false-noise avoidance** must be checked on a later relevant nonpublishing merge; **genuine later release Issue-close race** requires a separately authorized real product release, which Phase C does not trigger. Do not invent an observed release improvement or closure latency metric. The existing unsigned interim v3.0.8.24 and published immutable ZIP/source tag stay unchanged. Parent RHC-190 Phase D and RHC-191 semantics remain separate.
