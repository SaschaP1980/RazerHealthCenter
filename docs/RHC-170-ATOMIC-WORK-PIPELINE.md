# RHC-170 — parallel, fail-closed Work commit (nonpublishing)

This operator tool is an extension of [RHC-132](rhc132_work_preflight.py) and
[RHC-166](BOOTSTRAP_ORCHESTRATION.md), NOT a new Issue authorization, version
validator, or substitute for native Windows/Linux/Node24 CI.

## Default operator execution for version-only Work (RHC-180)

The permanent optimized path lives **before** the existing push-triggered Work CI. The GitHub-hosted one-off `rhc170-authenticated-cli.yml` runner and its short-lived GitHub App were retired after the successful v3.0.8.20 experiment; **they are not requirements or defaults**. RHC-170's actual script and adversarial tests remain on `main`. Do **not** bring back the retired workflow merely to operate on Work branches. Branch permission and CI permissions already exist in the authenticated GitHub provider used by the normal operator.

**Trigger/authorization:** This policy is selected by the operator after an *explicit owner instruction* to create a new four-component **version-only** release. Merely opening the bootstrap document or a PR **does not** authorize any mutation. Complete RHC-115/RHC-116 canonical Issue verification and exactly one `Owner-approved version-only target: X.Y.Z.H` line. Persist/read back all 13 headings, UTC/Berlin/frozen creation clocks and visible Work-Chat-ID in one canonical Rolling Comment **before Work branch creation**; independently GET-verify Work ref at a pinned freshly observed main and read back the updated **same** Rolling Comment *before* any source mutation. Snapshot reads never relax those sequential barriers.

**Execution selection (no extra credential assumed):**

| Available executor | Required normal method | Evidence label |
| --- | --- | --- |
| Authenticated local `git` + `gh` and clean exact Work checkout | Invoke `tools/rhc170_atomic_work_pipeline.py --apply --push --owner-authorized-new-version` with correct Issue, comment, pinned main, branch-created-at and repository; verify real push and native CI | `RHC170_TRUE_CLI` only with actual hosted/local CLI logs |
| Only the authenticated connected GitHub provider (ChatGPT connector), with exact-parent `create_tree`, `create_commit` and lease-checked `update_ref(expected_sha)` | Run the **connector-native atomic path** below in one bounded orchestrated operation using the existing connector identity; independently verify all remote results | `CONNECTOR_ATOMIC_EQUIVALENT`, **not** CLI, no reuse of CLI timing |
| Neither executor can guarantee the exact lease/authoritative readbacks | STOP and disclose missing capability; do not improvise permissions, serial mutation or a `GITHUB_TOKEN` workflow | `BLOCKED` |

### Connector-native atomic path without an extra GitHub App

This is the standard **operator implementation for a connector-only ChatGPT chat**, not an Actions workflow and not a separate GitHub token. Make the following dependency graph explicit when orchestrating GitHub-provider tool calls (parallelize **independent reads only**):

1. **Independent parallel immutable-authority snapshot.** In one bounded orchestrator invocation use `Promise.all` for authenticated GET/readbacks of Issue (number/title/body/creation-time taxonomy), original full Rolling Comment (ID/body/`created_at`/`updated_at`), current main SHA, Work ref SHA, plus `model.go` and `CHANGELOG.md` at the **pinned main SHA**. A parallel GET is not transactional; require equality to the approved frozen main, initial Work ref, and exactly one target version in the real saved Issue. Reuse existing RHC-132 strict `model.go` version/CHANGELOG transform and all fail-closed RHC-170 preflight requirements; if the operator cannot faithfully perform those validators, STOP instead of claiming parity.
2. **Strict local pure preparation and precommit barrier.** Prepare **only** `model.go` (both constants advance by the exact owner-approved component) and one prepended `CHANGELOG.md` entry; preserve all other content. Independently re-GET Issue, original comment, main and Work and require unchanged validated authority. Validate new source diff **before a ref mutation**, including no hidden extra paths. Never create or update an Issue/branch here (they already exist).
3. **One atomic Git history transaction** using the existing connector's Git Object APIs: `create_tree(base_tree_sha=<exact pinned main tree>, tree_elements=[{path:"model.go",mode:"100644",type:"blob",content:<validated bytes>},{path:"CHANGELOG.md",mode:"100644",type:"blob",content:<validated bytes>}])`; `create_commit(parent_sha=<exact pinned main SHA>,tree_sha=<new tree>, message=<RHC-132 exact trailers>)`. **Before** moving the Work ref, independently inspect compare/diff (exactly 1 new commit, 0 behind, exactly two paths, versions/heading as intended) and re-GET main/Work/Issue/comment again. There must be **exactly one** initial ref advance: `update_ref(branch_name="work/RHC-N",sha=<intended Work commit>,expected_sha=<frozen main>,force=false)`. Do not retry an ambiguous Git write without independent reconciliation; no direct main write and no general force push.
4. **Postpush exact-SHA readback and actual CI evidence.** Independently GET Work ref and main and require Work == intended SHA while main remains pinned. Confirm genuine **`event=push`** Work Infra and Development Completion runs on that exact SHA, created after the ref advance; `CREATED_NOT_GREEN` is not successful testing. Wait for actual Linux/native Windows/Node24 and Development Completion completed-success before Candidate, Publisher, staged downloads, independently fetched HTTPS/Windows RHC102 and RHC158 verified closure. All existing CI and release gates stay **unchanged**.
5. **Record provenance/timings** in the existing Rolling Comment (single sequential writer): path `CONNECTOR_ATOMIC_EQUIVALENT`, first tool/branch observed UTC, prepush/Work CI creation GitHub `created_at`, Work SHA, real run IDs, success/failure, queue/setup/validation distinct where measured. **Never** present the 4.684-second *authentic CLI* benchmark from #176 as this connector runtime's measured latency; never imply a CLI executed when no `gh` process ran.

**Authentication distinction:** A GitHub provider connected to the operator can create/advance a Work ref with its existing scoped privileges and trigger the ordinary native `push` workflows (this was observed in previous authenticated connector commits). Those connector credentials are **not** available as a shell `GH_TOKEN`. By contrast, pushes from the standard **GitHub Actions `GITHUB_TOKEN`** normally suppress recursive push workflows. The connector fast path does **not** depend on an App token in a GitHub-hosted runner, `workflow_dispatch` fallback, PAT, or additional owner secrets. If provider write/lease functionality is unavailable, do **not** assume equivalent permissions.

**Enforcement boundary:** This is the required operating protocol for cooperating agents reading `AGENTS.md`/`INITIAL_PROMPT.md`/`DEVELOPMENT_GUIDELINES.md`. Merely merging documentation cannot technically force an external agent to choose this method, nor is it a new automatic GitHub event hook. Full server-side enforcement or replacing assistant startup would require a separately tested executable change with its own scoped authorization. Only a subsequent normally requested version-only hotfix can demonstrate actual repeatable adoption and comparable **end-to-end** acceleration.

## Actual prior bottleneck and target

The verified v3.0.8.18 stopwatch [RHC-168](https://github.com/SaschaP1980/RazerHealthCenter/issues/168)
recorded \`2026-10-11T18:20:49.142Z\` as the **client-side response
observation** to Work branch creation, and \`18:22:59Z\` as the real GitHub
Work-CI created_at: **129.858 seconds** between them. Almost all of this
time was ChatGPT↔GitHub source read, blob/tree/commit creation and ref
readbacks. The last Work ref update to GitHub Work-CI creation took ~1 second.
The ≤45-second postbranch goal is **experimental, NOT MET or VERIFIED by this
code implementation**. The separate first-tool→Work-CI ≤120-second overall
target in #157 remains unverified.

## Safe dependency graph

1. **Already established externally:** Owner-created canonical Issue, 13-section
   prebranch BOOTSTRAP saved/read back, exact pinned public main, Work branch
   created at that SHA and original saved Rolling Comment verified and updated
   **before** any code commit. A new product version must be separately
   owner-approved. No Issue, branch, or release is created by this tool.
2. **Parallel read-only stage:** the one CLI process concurrently GETs Issue,
   same original Rolling Comment, main SHA, Work SHA and locally reads
   model.go and CHANGELOG.md. These six requests are NOT an atomic server
   snapshot. Feed the results together into the **existing**
   \`rhc132_work_preflight.plan()\` validator, including comment’s UTC/Berlin
   clocks and frozen creation proof.
3. **Second mandatory concurrent readback barrier:** Before any commit,
   independently GET Issue/comment/main/Work again and require unchanged
   authoritative state. The saved Issue body must include **exactly one**
   \`Owner-approved version-only target: X.Y.Z.W\` matching the planned next
   version and the operator must explicitly pass
   \`--owner-authorized-new-version --apply\`.
4. **One local atomic RHC132 commit:** RHC132 independently checks clean
   working tree, exact HEAD and branch, validates both source originals,
   stages **only CHANGELOG.md and model.go**, checks diff and commits one
   exact-parent version-only SHA. No separate remote blob, remote tree or
   model-mediated REST call is required.
5. **One safely guarded remote push (only with --push):** Independently
   reread Issue/comment/main/Work once more. Use one
   \`git push --force-with-lease=refs/heads/work/RHC-N:<pinned-main-SHA>
   origin HEAD:refs/heads/work/RHC-N\`. The local commit is already a
   verified direct child of that parent, making this operation an
   allowed fast-forward only when the exact old remote SHA still matches.
   Never issue a generic force push.
6. **Independent final readback:** Check actual main is still pinned and
   remote Work equals the exact intended new SHA. An ambiguous push
   response is **never retried**; instead independent readback alone decides
   success. Foreign, stale, unexpected or missing readback → blocked. No
   direct GitHub Issue/Comment PATCH in this driver; the human/operator
   updates the existing Rolling Comment serially with the emitted evidence.
7. **Actual Work CI must be separately observed:** the normal push-triggered
   hosted Infrastructure Linux/native Windows/Node24 and Development
   Completion run. Optional read-only \`--observe-ci-for-sha\` verifies
   **one exact** \`push\` run of each required workflow, actual GitHub
   \`created_at\`, SHA and internally consistent state. Its output explicitly
   says \`WORK_CI_CREATED_NOT_GREEN\`, *not* that hosted tests passed.

This script does not dispatch Candidate, Publisher, production releases,
edit \`downloads/\`, change application code outside the two version fields,
relax Razer privilege/UAC/repair safety, or mark any CI job green.

## Example invocation from clean checked-out Work branch

For the **future separately owner-authorized version-only Release Issue**
that contains exactly one line \`Owner-approved version-only target: X.Y.Z.W\`,
after its full canonical BOOTSTRAP and Work branch are verified:

    python3 -B tools/rhc170_atomic_work_pipeline.py \
       --repository SaschaP1980/RazerHealthCenter \
       --issue N --comment-id ID \
       --base-main-sha FULL_40_HEX_SHA \
       --branch-created-at 2026-10-14T09:08:20.205Z \
       --root . --day 2026-10-14

This is read-only \`PLAN_ONLY\`. Add
\`--owner-authorized-new-version --apply --push\` only for that separately
approved future new-version Work run. The \`--branch-created-at\` value must
be an observed honest instant, not an invented GitHub ref.created_at field.
The driver requires local \`git\` and authenticated \`gh\` CLI installed,
the correct clean Work branch checked out with \`origin\` and all source files
at the pinned SHA. It is **not run merely by installing or importing**.

The source of truth is still Github exact refs; after a successful push
request the normal Actions events are independently fetched by:

    python3 -B tools/rhc170_atomic_work_pipeline.py \
       --repository SaschaP1980/RazerHealthCenter \
       --issue N --comment-id ID \
       --base-main-sha FULL_40_HEX_SHA \
       --branch-created-at 2026-10-14T09:08:20.205Z \
       --observe-ci-for-sha FULL_NEW_WORK_SHA \
       --push-observed-utc 2026-10-14T09:09:00Z

Those runs must complete honestly before downstream Candidate. This separate
step deliberately does not busy-poll or invent CI timings.

## Timing, tests and acceptance

Output includes bounded per-operation \`observed_start_utc\`,
\`observed_end_utc\`, elapsed milliseconds and
\`CLIENT_OBSERVED_NOT_GITHUB_SERVER\` provenance for concurrent GETs.
It explicitly leaves \`actual_work_ci_created_at=NOT_OBSERVED\` until
the separate real run readback. Do not add overlapping Windows/Linux job
durations; do not equate simulated tests with an authorized real release.

Test-first [RHC-170](https://github.com/SaschaP1980/RazerHealthCenter/issues/170):
genuine Linux/native Windows RED from missing module, adversarial GREEN
covering stale SHAs, mismatched version/Issue/comment/clock, parallel reads,
unauthorized mutation, lost push replies, races before commit/push,
no extra writes, and duplicate/foreign/old GitHub runs. Native GitHub
Work and PR CI must pass. A **later separate owner-approved new version**
is required to measure whether the ≤45-second postbranch stretch goal is
real. No product release accompanies this implementation.
