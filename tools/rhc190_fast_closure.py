#!/usr/bin/env python3
"""RHC-190: exact-source four-run closure for a branchless product Fast-Path.

Work-Path releases continue to use the separate RHC-139 five-run rolling audit.
This worker cannot publish products or change branches, tags or downloads.
"""
import json
import re

from rhc_issue_init import issue_taxonomy

HEX = re.compile(r"[0-9a-f]{40}\Z")
RECORD = "RHC190_FAST_CLOSURE="


def close_fast(g, publisher_id, expected_source_sha, *, apply=False):
    from rhc158_release_closure import (
        need, trailer, commit, trusted_run, find_run, closure_seconds
    )
    pub = g.get_run(publisher_id)
    sha = pub.get("head_sha")
    need(type(publisher_id) is int and publisher_id > 0 and
         isinstance(sha, str) and HEX.fullmatch(sha) and
         sha == expected_source_sha, "fast publisher source mismatch")
    latest = g.get_latest()
    version = latest.get("version") if isinstance(latest, dict) else None
    need(isinstance(version, str) and
         re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", version) and
         latest.get("sourceSha") == sha and
         isinstance(latest.get("sha256"), str) and
         re.fullmatch(r"[0-9a-f]{64}", latest["sha256"]) and
         type(latest.get("size")) is int and latest["size"] > 0,
         "fast public release metadata invalid")
    need(pub.get("head_branch") == "candidate/v" + version,
         "fast publisher is not the canonical Candidate")
    trusted_run(g, pub, sha, "RHC Reusable Interim Unsigned Release",
                "workflow_dispatch", 4, bot=True)
    need(g.get_tag("v" + version) == sha, "immutable source tag mismatch")
    cand = commit(g, sha)
    base = cand["parents"][0]["sha"]
    message = cand["message"]
    need(len(re.findall(r"(?m)^Development-Path: fast$", message)) == 1
         and not re.search(r"(?m)^Work-SHA:", message)
         and trailer(message, "Main-SHA") == base,
         "fast provenance missing or forged Work marker")
    number = int(trailer(message, "RHC-Issue"))
    issue = g.get_issue(number)
    need(issue.get("number") == number
         and issue.get("state") in ("open", "closed")
         and issue.get("title", "").startswith(f"[RHC-{number}] "),
         "fast Issue identity invalid")
    need(issue_taxonomy(issue, for_development=True)["path"] == "dev-path: fast",
         "fast Issue is not authorized for branchless release")
    main = g.get_main_sha()
    prs = g.list_release_prs(main)
    need(isinstance(prs, list) and len(prs) == 1,
         "unique merged fast PR missing")
    pr = g.get_pr(prs[0]["number"])
    staged = pr.get("head", {}).get("sha")
    need(pr.get("merged") is True and pr.get("state") == "closed"
         and pr.get("merge_commit_sha") == main
         and pr.get("base", {}).get("sha") == base
         and isinstance(staged, str) and HEX.fullmatch(staged)
         and g.get_merge_parents(main) == [base, staged]
         and re.search(r"\b(?:Refs|Closes) #" + str(number) + r"\b",
                       pr.get("body") or "")
         and "sourceSha " + sha in (pr.get("body") or "")
         and "Development-Path fast" in (pr.get("body") or ""),
         "fast PR source/main provenance mismatch")
    stage = commit(g, staged)
    need(stage["parents"][0]["sha"] == sha
         and stage["tree"]["sha"] != cand["tree"]["sha"],
         "fast stage must descend from exact Candidate")
    name = "RHC Candidate Preflight (nonpublishing)"
    candidates = []
    for event in ("push", "workflow_dispatch"):
        runs = g.find_success_runs(sha, event)
        need(isinstance(runs, list), "fast Candidate runs unavailable")
        candidates.extend(r for r in runs if r.get("name") == name)
    need(len(candidates) == 1, "missing/ambiguous fast Candidate actual run")
    candidate_run = candidates[0]
    event = candidate_run.get("event")
    need(event in ("push", "workflow_dispatch"), "invalid Candidate trigger")
    candidate_id = trusted_run(g, candidate_run, sha, name, event, 3,
                               bot=(event == "workflow_dispatch"))
    ids = dict(candidate=candidate_id, publisher=publisher_id,
               downloads=find_run(g, staged, "downloads"),
               rhc102=find_run(g, main, "rhc102"))
    need(len(set(ids.values())) == 4,
         "independent hosted qualification missing")
    record = dict(issue=number, version=version, mainSha=main,
                  sourceSha=sha, pr=pr["number"], runIds=ids,
                  validation="ACTUAL_CANDIDATE_3_PUBLISHER_4_DOWNLOADS_1_RHC102_3")
    message = RECORD + json.dumps(record, sort_keys=True)
    comments = g.list_issue_comments(number)
    need(isinstance(comments, list) and len(comments) < 100,
         "fast Issue comments truncated")
    earlier = [c for c in comments if str(c.get("body","")).startswith(RECORD)]
    need(len(earlier) <= 1 and
         all(c.get("body") == message for c in earlier),
         "conflicting fast release closure record")
    if issue["state"] == "closed":
        need(issue.get("state_reason") == "completed" and
             isinstance(issue.get("closed_at"), str) and len(earlier) == 1,
             "fast Issue already closed without proof")
        state, closed = "ALREADY_COMPLETED", issue["closed_at"]
    elif not apply:
        state, closed = "READY_PLAN_ONLY", None
    else:
        if not earlier:
            try:
                g.create_fast_audit_comment(number, message)
            except Exception:
                pass  # Reconcile uncertain write through GET; never repeat.
        verified = g.list_issue_comments(number)
        saved = [c for c in verified if c.get("body") == message]
        need(len(saved) == 1 and type(saved[0].get("id")) is int
             and sum(str(c.get("body","")).startswith(RECORD) for c in verified) == 1,
             "fast closure comment not verified")
        need(g.get_issue(number).get("state") == "open",
             "fast Issue state changed")
        g.update_issue(number, "closed")
        closed_issue = g.get_issue(number)
        need(closed_issue.get("state") == "closed"
             and closed_issue.get("state_reason") == "completed"
             and isinstance(closed_issue.get("closed_at"), str)
             and any(c.get("body") == message for c in g.list_issue_comments(number)),
             "fast Issue close or audit readback failed")
        state, closed = "COMPLETED", closed_issue["closed_at"]
    elapsed = (closure_seconds(pub.get("updated_at"), closed)
               if closed is not None else None)
    return dict(status=state, issue=number, publisher=publisher_id,
                pr=pr["number"], closed_at=closed, source_sha=sha,
                publisher_to_issue_close_seconds=elapsed,
                closure_kpi="NOT_VERIFIED" if elapsed is None else
                ("MET" if elapsed <= 60 else "ABOVE_TARGET"))
