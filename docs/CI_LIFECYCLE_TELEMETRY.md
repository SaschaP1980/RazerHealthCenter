# RHC-138: owner-to-close lifecycle telemetry (nonpublishing)

## Why this exists

The last verified version-only RHC v3.0.8.12 release (#129) took **991 s
(16m31s) from GitHub Issue creation to Issue closure**, but the observed
user request came before Issue creation and the answer after closure.
Those two chat timestamps are **NOT VERIFIED** in GitHub. The owner's
approximately 20-minute perception cannot be reported as an exact measured
figure. RHC-131 measured actual hosted workflow/job/step durations; RHC-138
adds an **event timeline across GitHub workflows and human/operator gaps**
without representing guessed time as fact.

## Baseline from real #129 evidence

| Event | Verified observation (UTC) |
| --- | --- |
| Issue created | 2026-10-10T18:56:57Z |
| First Work CI created | 18:59:12Z, +135 s |
| Development Completion GREEN | 19:02:36Z, +204 s after Work CI (included issue taxonomy retry) |
| Candidate transfer/preflight | 19:02:37Z through 19:04:22Z, 105 s |
| Publisher created → completed | 19:04:18Z through 19:08:12Z, 234 s |
| Publisher completed → Issue closed | 19:08:12Z through 19:13:28Z, 316 s |
| Entire Issue-created → closed | **991 s** |
| Owner request → final assistant message | **NOT VERIFIED** |

Candidate preflight and Publisher **overlap** (19:04:18–19:04:22 UTC).
These intervals must not be added as independent critical-path work.
The observed 316-second postpublisher gap is **not** measured 316 seconds
of writing: it includes unknown GitHub/network/agent documentation, audit
and reconciliation. Validating actual safety gates is not wasted time.

## Instrumentation and reproducible usage

`tools/rhc138_lifecycle.py` builds a **versioned JSON** report with event
identities, immutable GitHub timestamps and Sha/Issue-scoped filtering;
a TSV event timeline; and a human summary. It has no write APIs, tokens in
output, release actions or automation authority. Missing dates return
`null` / `NOT_VERIFIED`, not zero. Non-GitHub chat boundaries require
separately attested real message timestamps and IDs (never assistant guesses).

Offline, using individually verified evidence or test fixtures:

```shell
python3 -B tools/rhc138_lifecycle.py \
  --fixture /path/to/verified-events.json \
  --out-dir /tmp/rhc138-report
```

For read-only live Issue and separately selected hosted run times:

```shell
python3 -B tools/rhc138_lifecycle.py \
  --repository SaschaP1980/RazerHealthCenter --issue 129 \
  --run-map /path/to/verified-run-map.json \
  --out-dir /tmp/rhc138-live
```

The `run-map` is a JSON object keyed by a recognized phase label (e.g.
`first_work_ci_created`, `publisher_green`) with a **verified GitHub
run ID**. The GitHub CLI must already be authenticated with *read-only*
access. The collector only uses GET and independently checks actual
Issue/Actions run identities; a workflow's `updated_at` is an **observed
state-change bound**, not a native completed_at. For release acceptance
use original required-job verifiers instead, never this report.

JSON input example:

```json
{
  "issue": 129,
  "events": [
    {"event":"issue_created","at":"2026-10-10T18:56:57Z","issue":129,
     "sha":null,"source":"github","evidence_id":"issue:129","status":"success"},
    {"event":"issue_closed","at":"2026-10-10T19:13:28Z","issue":129,
     "sha":null,"source":"github","evidence_id":"issue:129:close:1","status":"success"}
  ]
}
```

Supported event sources are restricted to real GitHub records and explicitly
attested owner/user-message boundaries; no private message bodies, tokens,
GitHub API response dumps, personal names or arbitrary environment data.
The report captures event provenance not any sensitive content.

Per-Issue time boundaries:
- `owner_authorized` and `final_user_notification` only count when real,
  independently attested, origin-specific message IDs and timestamps are
  available. Otherwise `owner_request_to_final_message=null`.
- Issue closure/reopening is read from actual Issue timeline event IDs.
  Multiple closures remain visible; the **last** verified close ends the
  Issue-to-close span. An earlier auto-close followed by reopening is
  reported as `premature_close_count`.
- Red attempts remain explicitly red and contribute to retry count; the
  final green run does not overwrite previous failure history.
- Supplemental bot-created `pull_request` zero-job `failure` is an
  actual event but **never** a substitute for an authenticated required
  Downloads/Windows/RHC102 hosted job.
- A missing or invalid event, unrelated Issue, mismatching frozen SHA,
  contradictory immutable event ID or negative chronology is excluded or
  causes a fail-closed report error, not fabricated evidence.

The exact **causal DAG critical path** and **operator active-work seconds**
remain `null`: GitHub timestamps alone cannot establish where an agent
was writing vs waiting. A wall-clock gap is labeled an **observation**, not
attributed savings. #132 targets initial qualification; #139 targets
incremental 13-section rolling audit and safe final closure.

## Non-negotiable operating constraints

This is a **nonpublishing** infrastructure tool. It does not alter
`model.go`, the current v3.0.8.12 ZIP/tag/catalog or any release workflows.
All real Work Linux/native Windows PowerShell 5.1 safety, deterministic
PE/seven-file ZIP builds, atomic one-PR source+downloads transaction,
authenticated exact-stage Downloads real hosted job and independent RHC102
public HTTPS/native Windows/aggregate **3/3** remain mandatory and fail
closed. Neither the script nor any JSON/TSV report is a release approval.

For #142 Wave A the goal is comparable first-attempt, genuinely authorized
hotfix evidence with distinct Issue-to-close and owner-to-final-message
timings. Avoid conflating the 991 s retry baseline with clean runs. A fresh
version release needs separate user authorization.
