# RHC-166 — guarded Issue-to-Work bootstrap orchestration

This **nonpublishing** tool joins the existing RHC-115 two-phase Issue
initialization and RHC-132 exact-Work preflight without weakening either
validator. It is a workflow entrypoint, not a publication pathway.

## Scope and safety

- Default is read-only PLAN_ONLY. It verifies a current pinned public main,
  the scope's one documented Development path, creation-time labels and the
  full repository Rolling template, and does not mutate GitHub.
- Explicit --apply uses RHC-115's single provisional Issue creation, unique
  GET/search and canonical [RHC-N] rename. It can instead verify a preexisting
  exact numbered Issue via --existing-issue; it will never silently duplicate.
- It then creates exactly one complete 13-heading canonical Rolling Comment
  **before** the Work branch. It independently re-fetches comment ID/body,
  frozen creation timestamp and all headings, records the saved readback
  in the same comment, and verifies a fresh pinned main. Only then does it
  create work/RHC-N, reread the ref, update and verify the same comment.
- Uncertain Issue/comment/branch writes are NOT retried blindly. An ambiguous
  comment response is reconciled by a unique exact-body list+GET; ambiguous
  comment PATCH is reconciled by a GET; missing, duplicate, foreign, stale
  or changed refs cause BLOCKED. Branch creation cannot resolve unknown
  clock/identity by guessing. The one real branch-creation timestamp reported
  by this tool is the **client observation after the GitHub call**, not a
  GitHub server ref.created_at (the refs API exposes no such field).
- The separate established RHC-132 version-only preflight remains the sole
  validator/committer for model.go and CHANGELOG.md. The new module exports
  version_only_plan which delegates to it; this command does not commit or
  push, auto-start Development Completion or dispatch an interim release.
  A **separate owner-authorized NEW VERSION request** is needed before using
  RHC-132's --apply --push on the pinned newly initialized Work branch.

## Authenticated operator example

With a GitHub CLI authenticated for the repository, a valid Issue body
including exactly one Development path declaration, and a genuinely
**visible** chat marker matching the eventually assigned Issue number:

    python3 -B tools/rhc_bootstrap_orchestrator.py \
      --repository SaschaP1980/RazerHealthCenter \
      --subject "GitHub CI Work initialization acceleration" \
      --body-file /path/to/owner-approved-issue-body.md \
      --pinned-main-sha <exact-fresh-public-main-SHA> \
      --marker RHC166CHAT7B41A38C11E9 \
      --label enhancement --label "priority: high" \
      --label "dev-path: work-branch" --label dev-ops

This is a plan only. Add --apply **only after** explicit owner authorization,
and use a marker whose number is either a known --existing-issue or guaranteed
by a separately initialized Issue. For a **new unknown Issue number**, the
marker must first be corrected to match the actual GitHub-assigned number;
the tool fails closed before any Work branch when it does not match.
A practical new-Issue workflow is: create/verify the Issue using RHC-115
first, post the actual marker visibly, then invoke this tool with
--existing-issue N --apply. No blind retries if initialization or comment
creation partially succeeded. Always inspect Issue and comment first.

## Performance measurements, limitations and acceptance

The previous owner-authorized v3.0.8.15 run showed 272.980 seconds first tool
observation to Work CI; a 120-second target is proposed in RHC-157. The next
actual owner-approved version-only Work/CI run must record first tool clock,
Issue created_at, canonical comment created_at/updated_at, branch readback,
Work commit/push, GitHub hosted CI created_at and any retransmits. Save
the report alongside issue with exact source SHA and timings.

This nonpublishing tool/PR demonstrates contract correctness, not speed.
It does **not** independently prove the <=120-second end-to-end target, a
reproducible p50/p95 or the full owner-message-to-screen time. Use at least
three comparable later real releases, each separately approved, before claiming
repeatability. GitHub native Windows, Linux, Dev Completion, Candidate,
Publisher, staged Downloads and HTTPS+Windows RHC102 all remain distinct
real safety gates and cannot be skipped or relabeled.
