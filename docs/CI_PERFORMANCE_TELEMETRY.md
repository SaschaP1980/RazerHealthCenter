# RHC-131 — read-only CI timing and benchmark evidence

This document describes a **measurement utility, not a release gate**. The
real unsigned interim-release eligibility checks remain unchanged: Work exact
SHA and Development Completion, Linux/native Windows, independent PE and
seven-file ZIP reproducibility, immutable Candidate, single combined
Source+Downloads release PR, separately authenticated exact-staged-SHA
Downloads Integrity `workflow_dispatch` with a real hosted success job,
immutable tag/catalog/history and independent RHC-102 public HTTPS/native
Windows/aggregate **3/3**. A timing report can **never** authorize promotion.

## Design / sources of truth

- `tools/rhc131_timing.py` accepts **real** GitHub Actions workflow run,
  workflow job and step JSON, either from supplied offline fixtures or from
  **GET-only** calls to the GitHub REST API through `gh api`. There is no
  permission to edit issues, create commits, dispatch, merge or publish.
- Schema `1` JSON includes Issue/version (if supplied), frozen Work,
  Candidate, staged and published SHAs, workflow run/event/attempt/actor
  **class** (not account identity), real job IDs, OS, status, conclusions and
  timestamps. JSON/TSV emit only allowlisted evidence fields, not raw GitHub
  API payloads, tokens, emails, runner hostnames, environment variables,
  source snippets or logs.
- `runs[].observed_updated_at` is the GitHub Actions **updated_at** field.
  It is **not** an actual completed_at timestamp. The observable run-window
  metric is therefore a GitHub state-change bound, not the causal critical
  path. Job.started_at/completed_at and each step's own timestamps are
  authoritative *for those job and step durations only*.
- `measurement.observed_wall_seconds` is the time from the earliest run
  creation to the latest observed completed-run update **only if every
  included run is terminal**. `sum_job_seconds` adds truly timed hosted
  jobs. `job_active_union_seconds` merges overlapping job intervals and
  `job_overlap_seconds` explicitly separates parallel execution from
  summing job CPU/runner time; union is **not** a critical-path DAG.
  `nonbusy_span_seconds` is an observed gap, **not** necessarily idle
  scheduler or GitHub polling time.
- The **exact causal critical path remains `NOT_VERIFIED`**, exposed as
  `critical_path_exact_seconds: null`. A possible job-duration lower bound
  is provided separately. No false precision or invented latency is allowed.
- Step-level category timings use the **actual GitHub step timestamps**, not
  newly recorded guessed per-command timings. Names such as
  `Compile and validate...` are correctly classified **mixed**, not split
  into fabricated Go compiler / validator seconds.
- `build.sh` on the hosted Ubuntu compiler emits lightweight
  `RHC131_PHASE start=... label=go_build` and
  `RHC131_PHASE end=... label=go_build` markers for the existing validation,
  Go tests, i18n guard, vet, compile, resource patch, PE validation, UI guard
  and checksum commands. The original commands and their failure semantics
  are byte-for-byte unchanged. `parse_phase_markers()` parses **optional**
  trusted logs offline; a missing end marker is missing time, never `0` or
  PASS. Existing GitHub job steps already separate substantial Candidate,
  Publisher and independent postrelease phases, so adding duplicate
  instrumentation inside every YAML workflow is unnecessary.
- For reruns the tool retrieves **all attempt job pages**, not just the
  latest. It reports failed previous-attempt hosted job seconds separately
  from latest-attempt job seconds. GitHub's first-run `created_at` is **not**
  a rerun's re-queue instant: rerun job queue duration is `null`.
- Missing/malformed/negative timestamps, wrong source SHA, truncated or
  missing job evidence, pending/skipped jobs, API failures or zero-job runs
  never receive a fabricated performance `0` or a synthetic PASS.
  Automated bot-created optional PR `failure`/0-job records are classified
  `SUPPLEMENTARY_ZERO_JOB_FAILURE`, while zero-job required dispatches
  remain `NO_HOSTED_JOB_NOT_VERIFIED`. See [#114](https://github.com/SaschaP1980/RazerHealthCenter/issues/114).

## Usage: explicit read-only GitHub workflow

In **Actions → RHC-131 CI Timing Audit (read-only) → Run workflow**, enter
comma-separated **completed run IDs** (1–25); optional Issue, four-part
version and exact SHAs add audit metadata. The workflow has **only**
`workflow_dispatch`, `contents: read` and `actions: read`; it doesn't
participate in Work/Candidate/Publisher/Release Verification and doesn't
change public files. It runs the RHC-131 regression tests, fetches real
run/attempt/job/step metadata, then provides an artifact containing:

- `rhc131-timing.json` — complete versioned, machine-readable evidence;
- `rhc131-timing.tsv` — a short per-run filtered comparison table;
- `rhc131-summary.txt` — human-facing real wall/summed/overlap/retry metrics.

The report artifact is retained for seven days. Copy the relevant result,
run ID, source SHA and limitations into the responsible Issue Rolling Comment
for long-term audit. **Do not mistake the report artifact ZIP for a new RHC
product release**. A manual audit run is not a substitute for a new actual
signed/unsigned release, and never changes its acceptance status.

Alternatively, using a workstation with an authenticated **read-only**
GitHub CLI:

```sh
python3 -B tools/rhc131_timing.py \
  --repository SaschaP1980/RazerHealthCenter \
  --run-ids 38077977604,38077977625,38078230959,38078329081,38078501688,38078536667 \
  --issue 129 --version 3.0.8.12 \
  --out-dir /tmp/rhc131-timing
```

For reproducible offline testing, supply a JSON file with `runs` (array)
and `jobs_by_run` (mapping from each run ID to GitHub-style
`{"total_count": 3, "jobs": [...]}`). Use `--fixture path.json` instead
of `--run-ids`. A supplied `--expected-sha` filters metrics to that
particular stage's exact source SHA while retaining `SHA_MISMATCH` records
as discrepancies; omit this flag when intentionally comparing different
Work/Candidate/stage/main SHAs in one full cycle.

## v3.0.8.12 historical baseline / Lenovo limitations

The verified [#129](https://github.com/SaschaP1980/RazerHealthCenter/issues/129)
public release shows Issue 18:56:57Z → publisher complete 19:08:12Z
(11m15s), Candidate `#38078230959` created 19:02:52Z → completed
19:04:22Z (~90s), Publisher `#38078329081` created 19:04:18Z →
completed 19:08:12Z (~234s), and RHC-102 `#38078536667` created
19:07:23Z → completed 19:08:02Z (~39s). The Candidate/Publisher timelines
overlap and include GitHub queues, Windows/Ubuntu setup and other activities;
**do not add them as sequential compile timings**. The Work Infra
`#38077977604` and Development Completion `#38077977625` each
required a second attempt after a genuine Issue metadata contract failure.
The three supplementary PR failures had 0 hosted jobs and remain in #114.

The Lenovo Boot Selector 4m13.6s Work-Bench result represents a PowerShell-
centric, much smaller distribution and a different hosted release boundary.
It is context, **not** a controlled RHC speed comparator or evidence that
any release gate can be removed. Future #132–#136 speed claims need one
comparable clean baseline, repeat runs, and this report's attempt/uncertainty
fields. Phase markers added now are only available on future new CI builds;
they cannot retroactively recover unknown v3.0.8.12 compiler seconds.

## Implementation and acceptance boundary

#131 changes only CI timing and documentation, not release decisions or
resource/signing/repair code. Real hosted Linux and separate native Windows
Work CI must be green for the exact final commit before merging this
nonpublishing PR. The telemetry workflow itself is opt-in; a future
product-version release must be separately authorized. Exact causal DAG,
GitHub internal job dispatch latency, physical Razer hardware and signing
remain `NOT_VERIFIED` unless independently measured. Historical evidence
must never be rewritten to look green.
