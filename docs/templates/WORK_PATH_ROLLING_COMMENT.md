# RHC Work-Path — Single rolling Build & Release recovery comment

Use as soon as a durable `work/RHC-<GitHub Issue number>` Work-Path is explicitly authorized, **even before its branch exists**. Unimplemented hosted or release gates remain `NOT IMPLEMENTED`, not PASS. This template **does** apply to the authorized RHC-3 infrastructure Work-Path while production Candidate/Release is incomplete; it does **not** apply to branchless Fast-Path Patch/Hotfixes or documentation-only work. The initial unborn-repository bootstrap is not a product Work-Path.

**Mandatory BOOTSTRAP gate — before the Work branch exists:**

1. Confirm live Issue, owner approval, exact current main SHA, version source, permitted files and forbidden safety/release actions. An unborn repository may need a minimal repository bootstrap commit first; this does not authorize Work changes.
2. Create this **single Issue Rolling Comment first**, with `Current phase: BOOTSTRAP`, the planned branch `NOT CREATED`, main SHA as last checkpoint, next precise action and a genuinely user-visible chat marker (else `not issued`). Do not create a branch, PR or code/workflow commit first.
3. Re-fetch the saved comment; confirm its ID and complete text, including the **three heartbeat fields derived from one freshly verified UTC instant**: readable `Last heartbeat`, `Local reference (Europe/Berlin)` and the authoritative millisecond-precision `Original ISO timestamp`. Compare the **saved original ISO timestamp**, not the locale-formatted lines, against GitHub `created_at`/`updated_at` (second precision). If creation, clock evidence or readback cannot be confirmed, **STOP** before the first branch mutation.
4. Then verify main remains at the pinned SHA, create the branch, re-fetch its SHA and update **this same comment**. Verify the new comment text before the first code commit; if stale or ambiguous, **BLOCKED**.
5. Refresh the exact checkpoint and next action before consequential writes and after significant commits/tests. After any timeout or interruption, re-read Issue, comment, main/Work refs, PR and CI. Never retry an uncertain write blindly. Late bootstrap is a process failure even when subsequent CI is GREEN.

Ordinary Fast-Paths and one-commit documentation updates do not require this Work-Path Rolling Comment.

Maintain one cumulative Issue comment. **Update each singleton section in place**, never append duplicate stale Candidate/Release sections. Numbered attempt sections are unique by attempt. Retain actual failures, counts and retries even when final status becomes PASS.

**ACTIVE cadence (LBS parity):** Maximum approximately **3 minutes** between verified in-place Rolling Comment heartbeats during active Work-Path execution, independently of whether a code commit is ready. Immediately update before long/high-risk sequences. Minimal truthful liveness text is permitted if nothing new happened; do not create a timer-only Git commit. Exceptions require accurately recorded `WAITING_FOR_GITHUB` plus exact queued/in-progress run, verified `BLOCKED_EXTERNAL`, genuine `IDLE`/`STOPPED`, or terminal `COMPLETED`. ACTIVE older than ~3 minutes is a missed heartbeat; older than ~5 minutes without a verified live workflow means resume as a stopped stream from GitHub Issue/main/Work SHA/checkpoint/CI. Persist a separate coherent code checkpoint within ~10–15 minutes of substantive completed uncommitted work. On closure correct stale branch/status fields and record deviations with evidence.

**Heartbeat contract (mandatory):** On comment creation **and every substantive in-place update**, capture **one fresh, verified, timezone-aware UTC instant with millisecond precision** from a checked clock immediately before submitting the edit. Render all three English-labeled fields below **from that same instant**; never obtain another clock reading to fill the other fields:

- `**Last heartbeat:**` displays `YYYY-MM-DD at HH:mm:ss UTC` (human-readable **UTC**, without milliseconds; omit, do not round, the fractional part).
- `**Local reference (Europe/Berlin):**` displays `DD.MM.YYYY, HH:mm:ss CET` or `CEST` using the **IANA** zone `Europe/Berlin` and **locale** `de-DE`; determine the zone abbreviation by its rules for the instant, not by guessing the season. The local calendar date can differ from UTC.
- `**Original ISO timestamp:**` preserves the **exact unaltered** UTC `YYYY-MM-DDTHH:mm:ss.sssZ` string in inline code; it is the machine-readable authority for automation, freshness, BOOTSTRAP and audit (including milliseconds). Do not reconstruct it from a seconds-only display.

After writing, re-fetch the complete saved comment through GitHub and validate **`Original ISO timestamp`** and the two derived human-readable lines against that one value; compare the **stored original ISO** to independently reported GitHub `created_at`/`updated_at` (the GitHub API reports seconds and normal write latency may differ by a few seconds). Never parse the `de-DE` presentation to determine freshness. If the clock is unverified, write **`unknown — time not verified` in all three fields** and keep the relevant gate `BLOCKED`/`NOT VERIFIED`; never fabricate any of the values. The heartbeat represents **this comment edit**, not the Issue's creation, a workflow event or a dated historical ledger entry. The ~3-minute ACTIVE cadence and every other Work-Path/section/audit requirement remain unchanged.

**Illustrative values only — do not reuse these example timestamps as live heartbeats:**

Summer (`CEST`; one verified instant, milliseconds retained):

```markdown
**Last heartbeat:** 2026-10-10 at 11:02:24 UTC
**Local reference (Europe/Berlin):** 10.10.2026, 13:02:24 CEST
**Original ISO timestamp:** `2026-10-10T11:02:24.267Z`
```

Winter (`CET`; same conversion contract):

```markdown
**Last heartbeat:** 2026-01-15 at 11:02:24 UTC
**Local reference (Europe/Berlin):** 15.01.2026, 12:02:24 CET
**Original ISO timestamp:** `2026-01-15T11:02:24.267Z`
```

UTC-to-local **date rollover** (local date is the next day):

```markdown
**Last heartbeat:** 2026-10-10 at 22:15:09 UTC
**Local reference (Europe/Berlin):** 11.10.2026, 00:15:09 CEST
**Original ISO timestamp:** `2026-10-10T22:15:09.042Z`
```

The `Europe/Berlin` label is a **fixed project reference**, not viewer-specific timezone detection; GitHub Issue Markdown is static and does not personalize this field. Do **not** embed active HTML/JavaScript or silently rewrite historically stored Rolling Comments. When a consumer expects the former ISO value directly after `Last heartbeat`, treat that consumer as incompatible and **STOP for separate executable-change authorization**; do not adjust tests, scripts, workflows or safety gates in this documentation-only change.

For new Issues, GitHub Issue #N becomes `[RHC-N]`, `work/RHC-N` and Work-Chat-ID format `RHC<N>CHAT<12 uppercase random hexadecimal characters>`. Generate one identifier per working chat **after the issue number is known**, using cryptographically secure random bytes; write the literal marker in a normal user-visible assistant message **before** recording it in GitHub. Additional chats get separate markers. Do not invent the ChatGPT internal conversation ID, URL, model-selector setting or reasoning effort; mark unsupported evidence `unknown`/`not issued`.

**Full-template adoption and final structural verification are mandatory:** Instantiate **the complete scaffold below** at BOOTSTRAP, including every displayed heading/label, table and numbered-attempt area. Do not replace it with a self-composed summary or omit sections because a Work-Path is nonpublishing. Maintain each singleton heading **exactly once and in the original order** and revise its fields in place; attempts are chronological and uniquely numbered. For genuinely inapplicable Candidate, Release, hardware or benchmark fields, retain the headings/labels with `NOT APPLICABLE — <specific reason>`; for unknown values say `unknown — not measured` or `NOT VERIFIED`, never synthetic PASS. On terminal audit **compare headings and fields against this complete template**, verify exact GitHub Work/PR/CI/merge/cleanup, document historical bootstrap/heartbeat/template violations even if corrected later, and read back the same issue comment **before Issue closure**. This applies when a former docs-only scope escalates into actual executable Work.

~~~markdown
## RHC-<GitHub Issue number> — Rolling Build & Release State

**Last heartbeat:** <YYYY-MM-DD at HH:mm:ss UTC, derived from the same verified instant>
**Local reference (Europe/Berlin):** <DD.MM.YYYY, HH:mm:ss CET or CEST, de-DE for that instant>
**Original ISO timestamp:** `<YYYY-MM-DDTHH:mm:ss.sssZ from the one freshly verified UTC instant>`
**Agent-State:** ACTIVE | WAITING_FOR_GITHUB | BLOCKED_EXTERNAL | STOPPED | COMPLETED
**Issue:** [RHC-<number>](https://github.com/SaschaP1980/RazerHealthCenter/issues/<number>)
**Base main:** `<SHA>`
**Work branch / exact head:** `work/RHC-<number>` / `<NOT CREATED in BOOTSTRAP | verified SHA | deleted after verified nonpublishing merge or publication>`
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
- Reproducibility, GitHub source provenance, lean binary package, signing/distribution: <verifications or NOT IMPLEMENTED>; historical Source ZIP tests are not a new-version public download
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

For genuinely scoped **nonpublishing** work, `COMPLETED` requires verified PR/main/CI/cleanup with release/native fields honestly OPEN/not applicable; unfulfilled separate parent/external Issues remain open until their real gates pass. A **real product release** requires actual final Release Verification before `COMPLETED`. Update the same comment and correct stale singleton fields before any eligible Issue closure. Do not conceal a missing mandatory RHC-specific gate behind an LBS-green reference.
