# RHC-132: version-only Work preflight and one atomic commit

## Scope and security objective

Historically [RHC-129](https://github.com/SaschaP1980/RazerHealthCenter/issues/129)
needed two Work pushes (the first `model.go` only, the second
`CHANGELOG.md`) and encountered a **real RHC115 Issue-title vs dev-ops-label
INITIALIZATION_BLOCKED** with extra hosted CI attempts. The last recorded
Issue-created → first Work CI interval was **135 seconds**, but that
includes GitHub APIs, comment readback and user/agent actions; it is not
135 seconds of compiler work. RHC-132 eliminates *avoidable incomplete
Work commits*, and makes the existing Issue/BOOTSTRAP gates explicit.
It cannot promise a measured ≤60 s interval without a separately authorized
clean real version-only Release and [#138](https://github.com/SaschaP1980/RazerHealthCenter/issues/138)
E2E event tracking.

`tools/rhc132_work_preflight.py` is **a local opt-in CLI**, not a new
privileged GitHub Action or a global interception of GitHub UI. It uses
the existing trusted RHC115/RHC116 `rhc_issue_init.verify_initialized_issue`
contract on an **independent saved Issue GET**, not on a convenient create
response. The Issue must be OPEN, exact `[RHC-N]` with CI/dev-ops title
taxonomy, exactly one priority/type/path label and one explicit
`Development path: dev-path: work-branch — ...` decision.

A full canonical Rolling Comment must already exist **before the Work
branch**. The CLI reads the saved comment ID over GitHub GET, verifies
all 13 singleton headings, correct Issue/Work identity, one common
ISO/UTC/Europe-Berlin heartbeat, its original time close to comment
creation, and an affirmative BOOTSTRAP readback. Missing/bad clocks, the
wrong Issue or a comment created after the branch all **block**.
Limit: a persisted sentence stating that a readback was performed is
still not independent cryptographic proof of the user's original reading;
the live Work-Path operator must perform and record that actual GET
before branch creation.

## Operating sequence

1. Obtain specific owner authorization for a **new version-only Hotfix**
   on a previously created Issue. Check the current `main` SHA, source
   `appVersion`, `referenceVersion`, current `CHANGELOG.md`, Issue
   metadata and existing immutable public version source/tag/ZIP.
2. Post the full canonical Rolling Comment and perform a real GitHub
   **readback before branch creation**. Create `work/RHC-N` at pinned
   current `main`, then reread the Work ref and update/reread the same
   comment before code changes.
3. Clone/check out that exact Work branch in a **clean local Git
   worktree** with an authenticated GitHub CLI, same original HEAD as
   pinned main. Default command is a **nonmutating plan**:

```sh
python3 -B tools/rhc132_work_preflight.py \
  --repository SaschaP1980/RazerHealthCenter \
  --issue N --comment-id SAVED_COMMENT_ID \
  --base-main-sha PINNED_MAIN_40_HEX_SHA \
  --branch-created-at VERIFIED_ISO_UTC \
  --root .
```

4. Only after independently verifying the plan, explicitly invoke
   `--apply --push`. This writes exactly the two version constants in
   `model.go` and one new top `CHANGELOG.md` version-only entry,
   stages **exactly both files**, runs Git cached diff/check, then makes
   **one Git commit** with three canonical trailers and pushes the
   single commit to the existing Work ref. Right before pushing it reads
   `main` and the Work ref **again**, blocking on stale ancestry.
   Git's non-force push itself rejects a changed remote Work head.

The two version constants must already match, and the changelog's
current top release must equal their source version. Exactly the fourth
numeric part increases by one; no MAJOR/MINOR/PATCH change and no
product behavior, Razer repair, UAC/privilege, Windows safety,
publisher workflow, ZIP, download pointer or tag changes. Untracked
or modified files, mismatched source bytes, wrong branch or HEAD, a
stale main or unexpected staged path always block. There is **no
implicit retry** after uncertain GitHub API or push failure; reconcile
the exact Git ref/commit first. On a failed precommit operation original
local source bytes are restored. If Git commit succeeds but remote
main moves, the local commit remains for explicit reconciliation and
is **not** automatically pushed.

## Contract tests / nonpublishing proof

`tests/test_rhc_132_work_preflight_contracts.py` exercises metadata,
Issue and label area consistency, missing 13 headings, wrong UTC/CEST,
comment too late, version and Git SHA mismatch, dirty worktree, and an
actual throwaway Git repository where one commit has exactly **two
paths and one parent**. The real fixture Git repository is local only;
it does not change the live RHC product version.

Passing a Work preflight is **not** a new Candidate or publication
approval. The genuine hosted Work Linux/native Windows+Node24 CI,
exact frozen Development Completion, Candidate Linux/native Windows,
double reproducible Windows GUI/PE + seven-file ZIP, authenticated
separately dispatched exact-stage Downloads job, single combined
Source+Downloads release PR, immutable tags and old ZIPs, and
independent public RHC102 3/3 remain fully mandatory.

This infrastructure PR is **not** authorization to call the `--apply
--push` option for an actual new Hotfix. Only a fresh explicit owner
instruction can authorize a real version or release. Separate
RHC-139 work will automate final canonical audit; it does not belong
inside this atomic version-commit tool.
