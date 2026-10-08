# RHC Work-Path — Single rolling Build & Release recovery comment

Use as soon as a durable `work/RHC-<GitHub Issue number>` Work-Path is explicitly authorized, **even before its branch exists**. Unimplemented hosted or release gates remain `NOT IMPLEMENTED`, not PASS. This template does **not** apply to ordinary Fast-Path Patch/Hotfixes or to the initial migration while Candidate/Release automation is not yet installed.

**Mandatory BOOTSTRAP gate — before the Work branch exists:**

1. Confirm live Issue, owner approval, exact current main SHA, version source, permitted files and forbidden safety/release actions. An unborn repository may need a minimal repository bootstrap commit first; this does not authorize Work changes.
2. Create this **single Issue Rolling Comment first**, with `Current phase: BOOTSTRAP`, the planned branch `NOT CREATED`, main SHA as last checkpoint, next precise action and a genuinely user-visible chat marker (else `not issued`). Do not create a branch, PR or code/workflow commit first.
3. Re-fetch the saved comment; confirm its ID, text, fresh ISO 8601 UTC timestamp with milliseconds and GitHub `created_at`/`updated_at`. If creation, time or readback cannot be confirmed, **STOP** before the first branch mutation.
4. Then verify main remains at the pinned SHA, create the branch, re-fetch its SHA and update **this same comment**. Verify the new comment text before the first code commit; if stale or ambiguous, **BLOCKED**.
5. Refresh the exact checkpoint and next action before consequential writes and after significant commits/tests. After any timeout or interruption, re-read Issue, comment, main/Work refs, PR and CI. Never retry an uncertain write blindly. Late bootstrap is a process failure even when subsequent CI is GREEN.

Ordinary Fast-Paths and one-commit documentation updates do not require this Work-Path Rolling Comment.

Maintain one cumulative Issue comment. **Update each singleton section in place**, never append duplicate stale Candidate/Release sections. Numbered attempt sections are unique by attempt. Retain actual failures, counts and retries even when final status becomes PASS.

**Heartbeat contract (mandatory):** On comment creation **and every substantive in-place update**, set `**Last heartbeat:**` to a **fresh, actual ISO 8601 UTC timestamp including date, time, seconds and milliseconds**, e.g. `2026-10-08T07:24:41.763Z`. Obtain the timestamp from a checked, timezone-aware current-time source immediately before submitting the edit; do not synthesize a clock time from the calendar date or from Issue/Workflow run dates. After the write, re-read the comment through GitHub and compare the stored heartbeat with its independently reported `updated_at` (GitHub API time has second precision and may differ by a few seconds). If the current time cannot be verified, use `unknown — time not verified` rather than a date-only placeholder or invented time. Preserve historical event times separately in the chronological ledger; **Last heartbeat is the current edit's heartbeat**, not the original issue creation or an old run timestamp.

For new Issues, GitHub Issue #N becomes `[RHC-N]`, `work/RHC-N` and Work-Chat-ID format `RHC<N>CHAT<12 uppercase random hexadecimal characters>`. Generate one identifier per working chat **after the issue number is known**, using cryptographically secure random bytes; write the literal marker in a normal user-visible assistant message **before** recording it in GitHub. Additional chats get separate markers. Do not invent the ChatGPT internal conversation ID, URL, model-selector setting or reasoning effort; mark unsupported evidence `unknown`/`not issued`.

~~~markdown
## RHC-<GitHub Issue number> — Rolling Build & Release State

**Last heartbeat:** <actual ISO 8601 UTC timestamp with milliseconds, YYYY-MM-DDTHH:mm:ss.sssZ>
**Agent-State:** ACTIVE | WAITING_FOR_GITHUB | BLOCKED_EXTERNAL | STOPPED | COMPLETED
**Issue:** [RHC-<number>](https://github.com/SaschaP1980/RazerHealthCenter/issues/<number>)
**Base main:** `<SHA>`
**Work branch / exact head:** `work/RHC-<number>` / `<NOT CREATED in BOOTSTRAP | verified SHA | deleted after publication>`
**Last checkpoint:** `<verified main SHA in BOOTSTRAP | verified Work SHA after branch creation>`
**Bootstrap readback:** `<GitHub comment ID + verified creation/readback | NOT VERIFIED — STOP>`
**Version:** <product version from model.go or later verified authority>
**Current phase:** <phase>
**Next action:** <exact evidence-based action>

### Chat origin

- Execution platform: ChatGPT | other | unknown
- Originating Work-Chat-ID: `<RHC<number>CHAT<12 random uppercase hex> | not issued>`
- Marker posted as a visible message in that chat: yes | no | unverified
- Additional execution chats: none | <chronological markers and provenance>
- Search confirmation: user-confirmed | unverified | unavailable

### Work-Path authorization and scope

- Development-path decision: <Major/Minor; substantial risk; or explicit user-authorized benchmark exception>
- Work-Branch-Reason: <exact reason>
- Allowed diff: <explicit path inventory>
- Forbidden changes: <explicitly preserve Razer repair confirmation, privilege/UAC, device/state, generic middleware and false-GREEN safety>
- Protected/deletion intent: <exact derivation from final diff, or NOT CONFIGURED with consequence>

### Benchmark configuration

- Assistant-declared model: <value or unknown>; provenance: <assistant declaration/runtime/user>
- User-selected model: <value or unknown>; provenance: <user-reported/runtime>
- Reasoning effort: <Medium | High | other | unknown>; provenance: <user-reported/runtime>
- Workload and confounders: <scope, environment, runner policies, Work/Fast differences>
- User authorization UTC: <verified | unknown>; Issue creation UTC: <separate measured value>

### Validation plan and coverage

- Focused RED (confirmed bugs only): <test, original exact SHA, actual fail>
- Focused GREEN: <test and pass count>
- Python validation: <exact tools/results/counts>
- Go version, test/vet: <actual environment and results>
- Windows PowerShell 5.1 hosted parser/safety: <run, actual PS version, exact totals>
- Windows amd64 build, PE/resources: <run, exact SHA and results>
- Determinism / source package / portable directory layout: <actual hashes and counts>
- Source safety invariants: <specific checks; never substitute static for native hardware>
- Real Razer hardware E2E: <PASS with evidence | OPEN/N/A with reason>
- Work-Path Development Completion: <exact frozen Work SHA, hosted run and status>
- Candidate-Entry: PASS | BLOCKED; <required gate-specific evidence>

### Measurement ledger

| Event | UTC | Run/ref/SHA/primary evidence |
| --- | --- | --- |
| User authorized scope | <known/unknown> | <reference> |
| Issue created | <UTC> | <issue> |
| Rolling Comment BOOTSTRAP created/read back | <UTC> | <verified comment ID, heartbeat and main SHA; BEFORE branch> |
| Work branch created | <UTC/unknown> | <ref and SHA> |
| First branch-head and rolling-comment update verified | <UTC/unknown> | <actual Work SHA / existing comment ID> |
| Final checkpoint frozen | <UTC/unknown> | <SHA> |
| Development Completion request/run | <UTC/unknown> | <run id> |
| Development Completion GREEN | <UTC/unknown> | <exact summary> |
| Candidate commit/ref | <UTC/unknown> | <SHA and ref> |
| Candidate workflow created | <UTC/unknown> | <run id> |
| Linux gate GREEN | <UTC/unknown> | <job id> |
| Windows gate GREEN | <UTC/unknown> | <job id> |
| Promotion complete | <UTC/unknown> | <job> |
| Release run created | <UTC/unknown> | <run> |
| Pre-activation PASS | <UTC/unknown> | <exact summary> |
| Merge / public activation | <UTC/unknown> | <PR, main SHA> |
| Release Verification PASS | <UTC/unknown> | <exact summary> |
| Issue closed | <UTC/unknown> | <issue> |

### Development Completion attempts

#### Attempt 1 — <PASS | FAIL | running | not started>

- Frozen Work SHA: <SHA>
- Hosted run, job totals and logs: <exact evidence>
- Corrections/reruns: <observed events>
- Work-Branch head and main ancestry still current: <verified or BLOCKED>

### Candidate Entry

- Decision: PASS | BLOCKED
- Exact source tree, protected diff, version, hashes and mandatory evidence: <details>
- Missing, stale or N/A evidence and consequence: <details>

### Candidate attempts

#### Candidate 1 — <PASS | FAIL | not started>

- Exact candidate SHA/ref: <SHA/ref>
- Linux validation: <actual results>
- Windows/native validation: <actual results>
- `CANDIDATE_TIMING_SUMMARY`: <actual hosted run or NOT IMPLEMENTED>
- Gate queue/setup/test/critical path: <measured values or unknown>
- Corrections: <actual scope and new SHA, never a parallel candidate>

### Release

- Release run/status: <id, status, exact candidate SHA>
- Reproducibility, source archive, binary package, signing/distribution: <verifications>
- Public version pointer contract: <verified RHC-specific pointer or NOT CONFIGURED>
- Pre-activation proof: <exact pass summary, prior public version>
- Single PR/merge: <PR, head, merge main SHA>
- Tag/source SHA: <tag and ZIP-free source commit>
- Release statuses: <pass/expected, exact contexts>
- Branch cleanup: <candidate/release/work refs and verified states>

### Final Release Verification

- Verification summary: PASS | FAIL | NOT AVAILABLE
- Published version, package filename, bytes, SHA-256: <verified>
- Source package hash/tree: <verified>
- Runtime safety, known pending native acceptance: <precise scope>
- Issue completion eligibility: <yes/no and evidence>

### Performance result

- Issue creation -> final verification: <duration>
- Candidate run creation -> Candidate gates GREEN: <duration>
- Candidate GREEN -> promotion completion: <duration>
- Promotion -> Release Verification: <duration>
- Queue vs runner setup vs validations vs orchestration gaps: <separately measured>
- Comparability/confounders: <release/runner/environment scope>

### Evidence audit

- Reviewed Issue, comments, commits/trees, hosted runs/jobs/logs and hashes: <exact references>
- Validator totals and attempts: <all counts, including failures, or unavailable>
- Every error/timeout/limitation: <observed evidence, primary classification and correction>
- Distinguish Issue start, candidate SHA creation, workflow creation, gate GREEN, promotion, verification and Issue close.
- Chat ID and reasoning-effort provenance: <visible marker / user-reported vs unknown>
- Singleton headings unique, attempt indexes unique, terminal state consistent: <PASS/BLOCKED>
- Unresolved concerns: <none or explicit blockers>

### Plan-conformance assessment

**PASS | PASS WITH CORRECTION | FAIL | NOT READY**

- Expected process vs actual deviations: <details>
- Safety contract and non-production limits: <details>
- Next owner/action or final completion: <details>
~~~

On success, update this **same** comment to `Agent-State: COMPLETED` after final Release Verification; correct stale "pending" in completed singleton sections before Issue closure. Do not conceal a missing mandatory RHC-specific gate behind an LBS-green reference.
