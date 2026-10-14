# RHC-170 — parallel, fail-closed Work commit (nonpublishing)

This operator tool is an extension of [RHC-132](rhc132_work_preflight.py) and
[RHC-166](BOOTSTRAP_ORCHESTRATION.md), NOT a new Issue authorization, version
validator, or substitute for native Windows/Linux/Node24 CI.

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
