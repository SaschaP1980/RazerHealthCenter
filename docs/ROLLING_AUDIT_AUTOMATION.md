# RHC-139: incremental evidence journal and guarded Issue closure

## Objective and measured reason

The last fully verified v3.0.8.12 owner-authorized Hotfix, [#129](https://github.com/SaschaP1980/RazerHealthCenter/issues/129),
showed **316 seconds** between the completed-success Publisher and GitHub
Issue closure (19:08:12–19:13:28 UTC). This is a measured overall
postpublisher interval, **not** proof that all 316 seconds are pure writing
overhead. RHC-139 aims to gather genuine evidence incrementally and reuse
one full 13-section canonical Rolling Comment, to minimize final
reconstruction and allow a fast but **fully verified** close.

This is a **nonpublishing infrastructure tool**, not a new release workflow,
privileged GitHub App or an automatic approval mechanism. Wave A comprises
[#138](https://github.com/SaschaP1980/RazerHealthCenter/issues/138)
(full observed owner-to-close timeline), [#132](https://github.com/SaschaP1980/RazerHealthCenter/issues/132)
(Issue/BOOTSTRAP preflight + one atomic version-only Work commit) and
this third independently tested implementation. A *new* real product-version
release requires separate explicit owner authorization.

## How the canonical journal is updated

`tools/rhc139_rolling_audit.py` owns one **existing** canonical Issue
comment ID. The comment must contain **all 13 canonical headings** exactly
once, in the prescribed order, plus its original Issue link and heartbeat.
It never substitutes a shorter summary. Each verified event is stored as a
stable `RHC139_EVENT` entry in **Evidence audit**, keyed by a unique
event identifier. Same key+same verified facts is idempotent; same key with
a different SHA, run, result or job count **blocks**. Existing explanations,
previous failures and attempt logs are preserved.

One single UTC clock instant produces the complete `Last heartbeat`,
`Europe/Berlin` CET/CEST and millisecond ISO timestamp pair. Clocks from
different instants are not mixed. An unknown/missing time is explicitly
`NOT_VERIFIED`. This tool does **not** alter stored historical event
times or hide earlier RED attempts. An evidence record includes only the
Issue number, exact source SHA, real run ID and actual successful job count;
secrets, raw API payloads and user conversations are never journaled.

An event may be recorded **during Work, Candidate, Publisher, Downloads or
postrelease**, after the corresponding run has **actually** completed
successfully on the exact SHA with real successful hosted jobs. This
is separate from final Issue closure. The CLI is plan-only by default:

```sh
python3 -B tools/rhc139_rolling_audit.py \
  --repository SaschaP1980/RazerHealthCenter \
  --comment-id SAVED_CANONICAL_COMMENT_NUMBER \
  --record-json /path/to/verified-event.json
```

Explicit `--apply` performs an existing-authority Issue comment PATCH,
then independently GETs and compares the actual persisted comment.
The event JSON must contain `key`, `issue`, `sha`, `status: success`,
`run_id` and `job_count`. This is a **historical evidence write**, not
permission to publish or certify the product.

## Guarded finalization

Once all scope-specific gates have been successfully verified, a separate
proof JSON can be supplied:

```sh
python3 -B tools/rhc139_rolling_audit.py \
  --repository SaschaP1980/RazerHealthCenter \
  --proof /path/to/exact-issue-acceptance.json
```

Without `--apply` the CLI produces only a **READY_PLAN_ONLY** disposition.
When explicitly invoked with `--apply`, the controller:

1. GETs the exact OPEN Issue and existing canonical comment, validating
   Issue number/comment ID, 13 headings and current status.
2. GETs the exact already-merged PR, frozen Work/source/staged/main SHA,
   verifies the new `main` merge is an **exact two-parent Git graph**
   and checks all scope-required authenticated GitHub workflow runs and
   **every genuine successful hosted job**. It does not trust a label,
   arbitrary JSON `PASS`, PR status alone or a zero-job workflow.
3. For a nonpublishing Issue requires completed Work Infrastructure **3/3**
   (real Linux, native Windows and Node24 transport), independent human
   PR Infrastructure **3/3** and Source Intake **2/2**, merged Work source,
   plus actual successful cleanup **1/1** with Work ref absent (404).
   A skipped version Development Completion is N/A, not PASS.
4. For a **real separately authorized interim version release**, requires
   successful Work Infrastructure **3/3**, immutable Candidate preflight
   **3/3**, Publisher **4/4**, the genuinely separately dispatched
   exact-staged-SHA **Downloads Integrity 1/1**, and independent final public
   RHC-102 **3/3** (Linux HTTPS, native Windows, aggregate) all with matching
   source/stage/main SHAs, event types, workflow identities and
   **trusted github-actions[bot] actor on Candidate, Publisher, Downloads
   and RHC102 workflow_dispatch runs**. The public
   `latest.json` version/sourceSHA/nonempty SHA-256/size and immutable
   `vX.Y.Z.W` source tag must also agree. This verifier does not replace
   the RHC102 public-byte program, which remains the authoritative
   independent HTTPS ZIP/hash contract.
5. GETs the Rolling Comment **again** to detect changes after planning.
   A concurrent revision mismatch blocks before writing. The final update
   preserves all headings and events, transitions the comment to COMPLETED,
   PATCHes and **independently reads back the full exact bytes**, checks the
   Issue is still OPEN and `main` still points to the approved SHA.
6. Only then PATCHes the Issue as CLOSED/completed and independently GETs
   the actual terminal state. The *pre-close* Rolling Comment deliberately
   remains `WAITING_FOR_GITHUB`, not premature `COMPLETED`. After verified
   real closure the tool PATCHes **the same canonical comment again** with
   `Agent-State: COMPLETED` and the **actual GitHub closed_at UTC timestamp**
   and reads back those exact bytes. A failed Issue close cannot leave a
   falsely `COMPLETED` comment. A final readback failure remains
   `BLOCKED/NOT_VERIFIED` even when GitHub has closed the Issue.
   An Issue that GitHub has **already auto-closed prematurely** blocks;
   this tool does not unilaterally reopen historical Issues.

**API limitation:** GitHub Issue comments do not provide a documented,
reliable compare-and-swap write contract. The tool therefore uses repeated
GET/revision comparison before PATCH and strict byte readback after PATCH;
this is **optimistic race detection**, not an assertion of transactional
server-side CAS. A simultaneous writer between last GET and PATCH could
still cause a conflict; this must be surfaced and reconciled manually.
No unlimited retries, credentials escalation, forced closure or hidden
fallback. The existing Comment/Issue must have appropriate write
permissions already; no new token or GitHub App is provisioned.

## Tests and production acceptance

`tests/test_rhc_139_audit_contracts.py` exercises duplicate event keys,
unaltered 13 headings, consistent UTC/CEST, genuine job counts and identities,
wrong SHAs and merge ancestry, skipped/failed/zero-job required gates,
false-green release verifier, missing Downloads/RHC102, stale readback,
GitHub auto-close, and legitimate two-step comment→Issue closure against a
deterministic fake GitHub API gateway.

An accepted RHC139 **source implementation** requires true Linux and native
Windows hosted CI on one frozen Work SHA and separately green
human-created PR CI. It does **not** mean a future versioned
Publisher→Issue closure completed in 60 seconds: this can only be proven
by a **new explicitly owner-approved real version-only release**, measured
by RHC-138. The 60-second target is a KPI hypothesis, not a promise.

The complete original security contract—RHC115 Issue preflight, host-native
PowerShell 5.1 Razer repair/privilege checks, deterministic two EXE + seven-file
ZIP builds, immutable Candidate and older ZIP/tag/catalog, exact-stage
Downloads real hosted job, single atomic Source+Downloads PR, and independent
public HTTPS/native Windows/RHC102 aggregate **3/3**—is untouched.
Never make a skipped or bot-origin `failure` with zero jobs look green.
