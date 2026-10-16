# RHC-212 — End-to-end performance timeline instrumentation (nonpublishing)

Responsible [RHC-212](https://github.com/SaschaP1980/RazerHealthCenter/issues/212), references [RHC-190](https://github.com/SaschaP1980/RazerHealthCenter/issues/190) and [RHC-202](https://github.com/SaschaP1980/RazerHealthCenter/issues/202).

## What was actually added

- tools/rhc190_e2e_timeline.py is a standard-library Python, read-only, fail-closed audit. Live mode uses only allowlisted GitHub CLI API GET requests for one exact Issue, the supplied Candidate/Publisher/RHC102 run IDs, their **real hosted jobs**, and the merged release PR. It never dispatches workflows, creates refs, closes Issues, modifies files or releases. The same function accepts an explicit offline fixture for adversarial tests.
- tools/rhc190_e2e_client_observer.mjs is a *portable, opt-in* synchronous observation wrapper. The caller **must invoke beginFirstTool as the very first statement in the first real tool call**, before any awaited GET or mutating action, and bracket the actual checked, authorized connector ref write. The tool is NOT automatically loaded into ChatGPT, and importing it later does not retroactively capture first-tool time.
- tests/test_rhc_212_e2e_timeline_contracts.py rejects fabricated success, foreign SHAs, duplicate/skipped/partial or stale hosted jobs, wrong PR merged commit, corrupt clocks, secret-shaped client fields, and false KPI classifications.

## Four separate evidence clocks, no synthetic event

| Event | Source / recorded field | Authority |
| --- | --- | --- |
| First actual ChatGPT tool entered | client observer first_tool_utc, only if initialized at first tool statement | Client-observed; **not** independently certified GitHub time |
| GitHub ref mutation started / returned | observer ref_write_start_utc / ref_write_ack_utc; duration measured with local monotonic clock | Client-observed bracket; actual server ref-created instant **not present in GitHub REST** |
| Candidate CI created, PR merge, Issue open/close | GitHub Workflow created_at, PR merged_at, Issue created_at / closed_at | Authoritative GitHub server timestamps for those events |
| Public verifier success | exact source/main workflow completed-success AND three distinct hosted jobs, with last job completed_at | Authenticated GitHub-hosted proof of all jobs; run.updated_at remains a mutable **observation timestamp**, not exact completion |

Both ref-write bracket bounds (start→CI and ack→CI) are returned only when observations exist and have consistent order. Local monotonic ref duration is NOT proof of remote GitHub-created instant. Client and GitHub server UTC clocks have no certified offset: crossing their clock domains does not prove the original 45s ref→CI or 120s first-tool→CI thresholds. KPI fields remain NOT_VERIFIED, including with client observations, until separate trusted clock calibration and a first-tool entry contract exist. Inconsistencies fail closed. Three historical release samples cannot yield a defensible p95.

Candidate, Publisher and RHC102 are bound to exact source/main SHAs, required event types and **3/4/3 actually successful hosted jobs**; the Issue and merge PR are bound to the supplied main SHA. This script does not decide whether signed production, native hardware, Razer repair, rollback or policy accepted; those are out of scope.

## Run the read-only audit for a future separately authorized real release

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

Never paste actual GH_TOKEN into Issue, logs, JSON, or CLI parameters. For an *actual* new run, the caller may additionally supply --client-observation real-client.json created by an already-instrumented first connector tool. For privacy/safety, the observation contains only exact SHA/Issue and bounded timestamps. The portable observer requires deliberate integration at actual entry, e.g. in a fully authorized client orchestrator:

~~~javascript
// Must be the first executable statement of the FIRST real tool call.
// Merely reading this documentation or loading it later cannot capture the event.
const tracker = beginFirstTool({ issue: REAL_ISSUE_NUMBER });
// ... safe authenticated preflight and prepare EXACT immutable commit ...
await tracker.bracketExactRefWrite(
  () => authenticatedConnectorRefLeaseUpdate(EXACT_SHA, EXPECTED_OLD_SHA)
);
// Only after the operation actually succeeds and readback confirms correctness:
const observation = tracker.exportEvidence(EXACT_SHA);
~~~

This is an *integration example*, not an automatically enabled production hook; the client is responsible for proving it started at the actual first tool and for securely transporting the JSON. Passing JSON without a trusted observer origin is not an independent host attestation.

## Benchmarks and interpretation

Three previously authorized, full fast-path releases are documented in their original canonical ledgers: [Run 1, #204](https://github.com/SaschaP1980/RazerHealthCenter/issues/204), [Run 2, #208](https://github.com/SaschaP1980/RazerHealthCenter/issues/208), [Run 3, #210](https://github.com/SaschaP1980/RazerHealthCenter/issues/210). Their Issue→Candidate CI were 189 / 161 / 161 s; Issue→RHC102 PASS 520 / 438 / 444 s **as recorded at run update**, median 444 s. These values are from their original evidence and not reclassified as first-tool→CI. Run #204 Issue closure required a real failure/recovery and is contaminated. The separate RHC-202 3× hosted GET-only preflight samples (final median 3137.871 ms) were NOT three full release flows.

The new collector can audit authentic historical server intervals using exact run IDs. However, historical first-tool and ref-write brackets were not captured and remain null forever. Do not backfill using Issue creation or CI timestamps. To establish future statistically useful p95, collect sufficient *independent comparable runs* with consistent clock authority, and retain outlier/failed attempts rather than discarding them.

## Nonpublishing acceptance

Product appVersion, CHANGELOG, distribution archives/catalog and signing/rollback policy stay unchanged; no new version authorized. The Work-path change qualifies only its Python logic and applicable hosted Linux/native Windows CI. It cannot by itself establish a new release or validate the currently unavailable native client-module import path. Parent RHC-190 and RHC-202 remain open for true first-tool and ref timestamp capture/integration and measured cross-path improvements.
