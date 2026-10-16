# RHC-212 — End-to-end performance timeline instrumentation (nonpublishing)

Responsible [RHC-212](https://github.com/SaschaP1980/RazerHealthCenter/issues/212), references [RHC-190](https://github.com/SaschaP1980/RazerHealthCenter/issues/190) and [RHC-202](https://github.com/SaschaP1980/RazerHealthCenter/issues/202).

## What was actually added

- tools/rhc190_e2e_timeline.py is a standard-library Python, read-only, fail-closed audit. Live mode uses only allowlisted GitHub CLI API GET requests for one exact Issue, the supplied Candidate/Publisher/RHC102 run IDs, their **real hosted jobs**, and the merged release PR. It never dispatches workflows, creates refs, closes Issues, modifies files or releases. The same function accepts an explicit offline fixture for adversarial tests.
- tools/rhc190_e2e_client_observer.mjs is a *portable, opt-in* synchronous observation wrapper. The caller **must invoke beginFirstTool as the very first statement in the first real tool call**, before any awaited GET or mutating action, and bracket the actual checked, authorized connector ref write. The tool is NOT automatically loaded into ChatGPT, and importing it later does not retroactively capture first-tool time.
- tests/test_rhc_212_e2e_timeline_contracts.py rejects fabricated success, foreign SHAs, duplicate/skipped/partial or stale hosted jobs, wrong PR merged commit, corrupt clocks, secret-shaped client fields, and false KPI classifications.

## RHC-214: explicit Fast-Path connector entry and bounded GitHub clock calibration

**Runtime reality:** the repository cannot install an intercepting hook into ChatGPT or make the first tool happen automatically in new chats. The `tools/rhc214_instrumented_fastpath.mjs` adapter is invocable in an operator with a persistent JS runtime, and its `startInstrumentedFastPath(tools)` call must be the **very first executable statement of the first tool invocation**. The supported ChatGPT connector-script environment cannot dynamically import repository modules or persist JS objects between separate tool calls; the operator must inline the reviewed entrypoint/observer inside **one actual first-tool orchestration**, not import them later and claim first-tool capture. Standalone Node can import both modules normally. The adapter does not publish a product or relax existing RHC-115/116, version-only Candidate/ref and RHC-158 gates.

The exact flow for a **separately owner-authorized new Fast-Path product version**, not a test run:

1. In the FIRST tool call, start the adapter *before any awaited GET*. No Issue number is needed yet.
2. Through `createProvisionalIssue({title,body,labels})`, perform one real authorized GitHub Issue create and independent provisional GET, and capture first-tool/client Issue-create send/ack plus real GitHub `created_at`.
3. Canonicalize the Issue title using the existing exact RHC-115/116 flow, verify its final title/state and separately verify exact source/main, commit trailers and version-only diff. `verifyCanonicalIssue(number)` independently GETs the Issue and binds the originally unknown ID.
4. Only after the Candidate commit is independently proven safe and the authorized branch name is exact, replace the existing **one GitHub Candidate branch create/readback** with `createVerifiedCandidateRef(refName, candidateSha)`. The adapter performs the one GitHub create and remote SHA GET and measures the whole mutation/readback interval. It does not create a dummy Candidate or bypass CI.
5. Immediately call `persistObservation(candidateSha)` while still in that JS invocation. It creates **one** `RHC190_CLIENT_OBSERVATION_V2={...}` Issue comment with the allowlisted timing fields, and independently reconciles the exact comment by GET. An uncertain write is never blindly retried.
6. The ordinary untouched Candidate/Publisher/source+downloads merge/independent RHC102/closure proceeds through its existing gates. Later `tools/rhc190_e2e_timeline.py --client-from-issue ...` independently GETs the one archived Issue comment alongside exact CI/PR/hosted-job timestamps and recalculates the clock bounds. Use this only once all required real release inputs exist.

**Clock calculation:** If the authenticated Issue was created while a client-side tool-call bracket `[issue_send,issue_reply]` was active, and its GitHub UTC `created_at` is recorded in whole seconds `S`, then the *GitHub-minus-client UTC offset* is conservatively bounded by `[S - issue_reply, (S + 1 second) - issue_send]`. Both bounds are independently recomputed from the actual persisted GitHub Issue and observation. Use them to compute intervals for first-tool→CI and actual ref event→CI. The ref instant can occur anywhere within its exact connector-write plus readback bracket; it has no GitHub REST `created_at`. Drift, swapped Issue ID, wrong SHA, invalid order, huge offset range, missing/multiple comments or changed data fail closed. A local monotonic timer checks the ref-write bracket, but does **not** certify UTC clock rate across distinct ChatGPT tool invocations.

**Classification remains conditional.** Even a numerically bounded `<=45s` or `<=120s` result is `CONDITIONAL_BOUND_WITHIN_TARGET_NOT_HOST_ATTESTED`, not independently proven host first-tool or exact Git-server ref timing. Missing observations stay NULL/`NOT_VERIFIED`; historical releases #204/#208/#210 cannot retroactively gain a first-tool/ref timestamp. Reliable **independent host attestation** needs supported ChatGPT host entry instrumentation/clock source beyond this repository and is not implemented by a GitHub merge.

## Read-only audit for a future separately authorized, actually instrumented release

On a machine with an existing authenticated read-only GitHub CLI account and the repository source:

~~~bash
export GH_TOKEN='(already configured externally, never printed)'
python3 -B tools/rhc190_e2e_timeline.py \
  --repository SaschaP1980/RazerHealthCenter \
  --issue ISSUE_NUMBER \
  --candidate-sha EXACT_SOURCE_COMMIT \
  --main-sha EXACT_MERGED_PUBLIC_MAIN \
  --candidate-run REAL_CANDIDATE_RUN \
  --publisher-run REAL_PUBLISHER_RUN \
  --rhc102-run REAL_PUBLIC_VERIFIER_RUN \
  --pr REAL_MERGED_RELEASE_PR \
  --out timeline.json
~~~

Never paste a token into Issues, logs, JSON, or CLI parameters. `--client-from-issue` is **GET-only** and requires exactly one stored, valid `RHC190_CLIENT_OBSERVATION_V2` comment; it blocks on duplicates/missing evidence. `--client-observation real-client.json` remains a separate opt-in compatibility option. Without either, historical server-only evidence continues to work and leaves client fields absent.

### Operator call-site sketch (opt-in; not a release command)

```javascript
// FIRST statement in the FIRST real connector tool invocation.
// Import using an actual supported Node runtime, or inline the reviewed
// adapter/observer functions into a single ChatGPT connector-script invocation.
const measured = startInstrumentedFastPath(tools);
// Use existing RHC-115/116 real Issue initialization, NOT an invented mock:
const created = await measured.createProvisionalIssue(authorizedIssueSpec);
await existingCanonicalRenameAndReadback(created.number);
await measured.verifyCanonicalIssue(created.number);
// Existing full version-only source, exact-main, safety/trailers gates stay in force.
const candidateSha = await existingAuthorizedExactSourcePreparationAndReadback();
// Instead of raw connector create_branch, make exactly one checked ref mutation:
await measured.createVerifiedCandidateRef("candidate/vX.Y.Z.H",candidateSha);
const recorded = await measured.persistObservation(candidateSha);
// Continue original hosted release pipeline; no arbitrary extra pushes/releases.
```

The snippet intentionally leaves all authorization, source preparation and release gates delegated to existing validated code. It is **not** directly runnable end-to-end without those real integrations. The host must invoke the adapter at first tool entry, not at the moment a future release is already underway.

## Benchmarks and interpretation

Three previously authorized, full fast-path releases are documented in their original canonical ledgers: [Run 1, #204](https://github.com/SaschaP1980/RazerHealthCenter/issues/204), [Run 2, #208](https://github.com/SaschaP1980/RazerHealthCenter/issues/208), [Run 3, #210](https://github.com/SaschaP1980/RazerHealthCenter/issues/210). Their Issue→Candidate CI were 189 / 161 / 161 s; Issue→RHC102 PASS 520 / 438 / 444 s **as recorded at run update**, median 444 s. These values are from their original evidence and not reclassified as first-tool→CI. Run #204 Issue closure required a real failure/recovery and is contaminated. The separate RHC-202 3× hosted GET-only preflight samples (final median 3137.871 ms) were NOT three full release flows.

The new collector can audit authentic historical server intervals using exact run IDs. However, historical first-tool and ref-write brackets were not captured and remain null forever. Do not backfill using Issue creation or CI timestamps. To establish future statistically useful p95, collect sufficient *independent comparable runs* with consistent clock authority, and retain outlier/failed attempts rather than discarding them.

## Nonpublishing acceptance

Product appVersion, CHANGELOG, distribution archives/catalog and signing/rollback policy stay unchanged; no new version authorized. The Work-path change qualifies only its Python logic and applicable hosted Linux/native Windows CI. It cannot by itself establish a new release or validate the currently unavailable native client-module import path. Parent RHC-190 and RHC-202 remain open for true first-tool and ref timestamp capture/integration and measured cross-path improvements.
