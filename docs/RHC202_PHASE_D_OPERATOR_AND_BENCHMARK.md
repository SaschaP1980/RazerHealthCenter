# RHC-202 Phase D — genuinely invocable, GET-only operator and benchmark boundary

Responsible [RHC-202](https://github.com/SaschaP1980/RazerHealthCenter/issues/202); parent [RHC-190](https://github.com/SaschaP1980/RazerHealthCenter/issues/190). No product release is authorized by the Phase D implementation request.

## Executable mechanism and real authorization

**Native hosted executor (actually invocable):** [`.github/workflows/rhc190-phase-d-operator.yml`](../.github/workflows/rhc190-phase-d-operator.yml), triggered by an authenticated real GitHub **push limited to** `work/RHC-202` with named read-only source/workflow paths. It can also be **manually invoked on a selected existing issue-specific Work ref** through GitHub Actions `workflow_dispatch` using the exact already-pinned current main SHA and Issue. The workflow checks out source with `persist-credentials: false`; its only permissions are `contents: read`, `issues: read`, `actions: read`. No App/PAT or `pull_request_target`. Run `python3 -B tools/rhc190_phase_d_operator.py` via the actual Ubuntu runner with the pre-existing scoped `GH_TOKEN`; it only invokes fixed, allowlisted **GET** endpoints on canonical owner/repo. No shell/API routes are derived from unvalidated user-provided paths and no JSON API response bodies, token or username are logged.

**Connector-native fallback:** If ChatGPT's attached provider is the only authenticated mutation surface, use a single bounded `functions.exec` orchestration of *explicitly available normalized GitHub API operations*, with parallel independent read-only authority snapshot, pinned parent/tree, canonical Issue metadata and original 13-heading BOOTSTRAP readback, exactly one optional exact two-file commit and expected-SHA lease, then real remote readback of Work CI creation. Record `CONNECTOR_ATOMIC_EQUIVALENT`. The GitHub connector **cannot dynamically import** `tools/rhc186_connector_fastpath.mjs` from repository, and no code copied into the chat becomes a tested native ESM import. No secret extraction or extra GitHub App/PAT. This fallback remains under a **separate explicit product-version authorization** for any version commit, not authorized here.

**Critical trigger constraint:** GitHub Actions `GITHUB_TOKEN`-created branch pushes ordinarily do not recursively trigger the real mandatory Work Infrastructure/Development Completion events. A hosted Python worker using its read-scoped token is therefore **not** a substitution for the authenticated connector's Work ref lease push; the native executor here is intentionally read-only. A preflight result cannot promote a Candidate, publish, close an Issue, or self-award GREEN status.

## Boundaries and honest measurements

Three independently scheduled matrix jobs (`readonly-preflight-1`, `-2`, `-3`) each read real `main`, responsible Issue, original canonical 13-section Rolling Comment, exact pinned `work/RHC-N` ref, immutable source `model.go` and `CHANGELOG.md`, current published `downloads/latest.json`, and source-bound Work CI listing. Source, Issue taxonomy, public/version/Changelog consistency and exact branch SHA are mandatory. Job time is measured using `time.perf_counter` **on each hosted Linux runner**, with fixed `gh api --method GET` commands. GitHub API response timestamps and the runner monotonic timeline are explicitly different authorities. The Work run listing proves at most **creation**, never CI success.

After all three matrix jobs actually complete, a separate fourth real hosted job GETs the authentic workflow run and jobs API, requiring **three distinct executed-success sample jobs** and the exact expected aggregator identity before merging artifact JSON. It reports individual milliseconds and median/min/max; `p95_ms=null`, `end_to_end_ms=null`, `actual_branchless_push_to_ci_seconds=null` and `actual_candidate_publisher_rhc102_seconds=null`. A missing/zero-job/skipped/mixed-source/duplicate sample never supplies benchmark PASS. The report stays in a 7-day Actions artifact, with no binary ZIP.

**This is NOT a 3-run end-to-end branchless release benchmark.** It measures only hosted GET-based operator-preflight overhead, not ChatGPT's first tool → Issue initialization, mutating Candidate-source atomic commit, actual CI creation latency, total Candidate/Publisher/real HTTPS/native Windows RHC-102, issue close, or version release cost. The original RHC-190 <=45s branch→CI and <=120s first-tool→CI goals remain aspirational and **NOT VERIFIED** without three independent real fully authorized, comparable release/branchless operator flows with exact GitHub server and client timestamps. Avoid pretending 3 matrix jobs are 3 full release lifecycles. The owner has not requested a specific new application version.

## First genuine hosted preflight measurement (nonpublishing, exact Green SHA)

[GitHub Actions run #38766240901](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/38766240901), on exact initial GREEN Work SHA `6910e16fe586954a0b9fa654b5c5200cfc757f98`, created `2026-10-15T16:06:57Z`, workflow reported completed-success with **three distinct actual hosted Linux probe jobs** `readonly-preflight-1/2/3` and **one completed-success aggregate job**. The worker's actual summary:
- sample 1: **4060.516 ms**;
- sample 2: **2614.419 ms**;
- sample 3: **8071.472 ms**;
- **median 4060.516 ms**, min 2614.419 ms, max 8071.472 ms;
- schema `RHC190_PHASE_D_AGGREGATE_V1`, classification `REAL_API_PREFLIGHT_ONLY`, full Fast-Path **NOT VERIFIED**; p95 and full issue→CI → release times null.

The first RED Work SHA `e3c569de2733bdd529e9eecf64908bcf9dd97255` intentionally failed [read-only dry-run #38765551071](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/38765551071) with `ModuleNotFoundError: No module named 'rhc190_phase_d_operator'`; historical failure remains FAILURE. The current final source commit and actual hosted matrix/CI status are recorded in canonical Issue #202. **The initial GREEN measurement and any final-ref measurement must not be combined into a claimed full Hotfix release speedup.**

## Threat model and failure policy

The initial Work bootstrap/Issue order and 13-heading contract are not weakened, and release safety is unmodified. Ref drift, unknown Issue, wrong labels, stale model/public version, missing actual Work run, unknown GH token, disallowed endpoint, failure to upload/aggregate artifacts or an ambiguous hosted run fail closed. Read-only preflight must never write Git objects, publish packages, dispatch a release, mutate main/Issue, or attempt a recovered credential token. Work/Candidate still require actual distinct Linux, **native Windows PS5.1** and Node24/qualifier gates; Publisher still requires independent ZIP determinism, combined source+downloads PR, public RHC-102 HTTPS+Windows 3/3 and canonical Issue closure. Production remains `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false`; physical Razer/rollback/publisher trust remain DEFERRED.

## Next independently authorizable acceptance

A future requested, concrete four-part Patch/Hotfix version can exercise the existing **branchless Fast-Path** with its canonical Issue, owner approval and full published safety gates; only then can pre-CI and end-to-end performance be compared across **three separate real version/release runs**. Do not spend real hotfix numbers merely to meet a statistic. RHC-190 and RHC-191 remain open until their unmet conditions are authentically verified.
