#!/usr/bin/env python3
"""RHC-158: guarded nonpublishing operator for post-Publisher Issue closure.

No release, PR, tag, branch, download or product mutation. Existing RHC-139
performs the only opt-in canonical comment PATCH and completed Issue closure.
"""
import argparse
from datetime import datetime, timezone
import json
import re
import subprocess
import sys
import time
import rhc139_rolling_audit as audit

ROLLING_ID_MARKER = "**Issue:** [RHC-{issue}](https://github.com/SaschaP1980/RazerHealthCenter/issues/{issue})"
SHA = re.compile(r"^[0-9a-f]{40}$")
VERS = re.compile(r"^[0-9]+(?:\.[0-9]+){3}$")
ROLES = {
    "work": ("RHC Infrastructure Qualification (nonpublishing)", "push", 3),
    "candidate": ("RHC Candidate Preflight (nonpublishing)", "workflow_dispatch", 3),
    "downloads": ("RHC Repository Downloads Integrity (nonpublishing)", "workflow_dispatch", 1),
    "rhc102": ("RHC POSTRELEASE", "workflow_dispatch", 3)
}


def need(test, reason):
    if not test:
        raise ValueError("RHC158_CLOSURE_BLOCKED: " + reason)


def trailer(message, key):
    values = re.findall(r"(?m)^" + re.escape(key) + r": ([^\r\n]+)$", str(message))
    need(len(values) == 1, "missing or duplicate " + key)
    return values[0]


def commit(g, sha):
    need(isinstance(sha, str) and SHA.fullmatch(sha), "malformed Git SHA")
    item = g.get_git_commit(sha)
    need(isinstance(item, dict) and item.get("sha") == sha, "Git commit mismatch")
    parents = item.get("parents")
    need(isinstance(parents, list) and len(parents) == 1 and
         SHA.fullmatch(str(parents[0].get("sha"))), "nonlinear commit ancestry")
    need(SHA.fullmatch(str((item.get("tree") or {}).get("sha"))),
         "missing Git source tree")
    return item


def trusted_run(g, row, sha, name, event, count, bot=False):
    need(isinstance(row, dict) and type(row.get("id")) is int and row["id"] > 0,
         "missing run identifier")
    observed = g.get_run(row["id"])
    # Collection and detailed GET have different legitimate optional metadata.
    # Compare immutable security-bearing fields, never entire API JSON objects.
    critical = ("id", "head_sha", "event", "name", "status",
                "conclusion", "run_attempt", "head_branch")
    need(isinstance(observed, dict) and
         all(observed.get(key) == row.get(key) for key in critical) and
         (observed.get("actor") or {}).get("login") ==
         (row.get("actor") or {}).get("login"),
         "run discovery/readback identity mismatch")
    need(row.get("head_sha") == sha and row.get("event") == event and
         row.get("status") == "completed" and row.get("conclusion") == "success",
         "wrong SHA/event or not completed-success")
    need(row.get("name") == name or
         (name == "RHC POSTRELEASE" and
          str(row.get("name", "")).startswith("RHC POSTRELEASE v")),
         "wrong hosted workflow")
    need(type(row.get("run_attempt")) is int and row["run_attempt"] > 0,
         "missing actual run attempt")
    if bot:
        need((row.get("actor") or {}).get("login") == "github-actions[bot]",
             "untrusted workflow dispatch actor")
    jobs = g.get_jobs(row["id"])
    need(isinstance(jobs, list) and len(jobs) == count and
         len({j.get("id") for j in jobs}) == count and
         all(type(j.get("id")) is int and j["id"] > 0 and
             j.get("status") == "completed" and j.get("conclusion") == "success"
             for j in jobs), "required real hosted jobs incomplete/duplicate")
    return row["id"]


def find_run(g, sha, role):
    name, event, count = ROLES[role]
    rows = g.find_success_runs(sha, event)
    need(isinstance(rows, list), "run listing unavailable")
    matches = [row for row in rows if row.get("name") == name or
               (name == "RHC POSTRELEASE" and
                str(row.get("name", "")).startswith("RHC POSTRELEASE v"))]
    need(len(matches) == 1, "missing or ambiguous exact required run")
    return trusted_run(g, matches[0], sha, name, event, count,
                       bot=(role != "work"))


def collect_release_proof(g, publisher_run_id, allow_completed=False):
    need(type(publisher_run_id) is int and publisher_run_id > 0,
         "invalid publisher id")
    pub = g.get_run(publisher_run_id)
    need(isinstance(pub, dict) and pub.get("id") == publisher_run_id,
         "wrong Publisher identity")
    source_sha = pub.get("head_sha")
    need(isinstance(source_sha, str) and SHA.fullmatch(source_sha),
         "publisher SHA missing")
    latest = g.get_latest()
    version = latest.get("version") if isinstance(latest, dict) else None
    need(isinstance(version, str) and VERS.fullmatch(version) and
         latest.get("sourceSha") == source_sha and
         isinstance(latest.get("sha256"), str) and
         re.fullmatch(r"[0-9a-f]{64}", latest["sha256"]) and
         type(latest.get("size")) is int and latest["size"] > 0,
         "public version/size/checksum/source mismatch")
    need(pub.get("head_branch") == "candidate/v" + version,
         "publisher not on exact candidate branch")
    trusted_run(g, pub, source_sha, "RHC Reusable Interim Unsigned Release",
                "workflow_dispatch", 4, bot=True)
    need(g.get_tag("v" + version) == source_sha, "immutable tag mismatch")
    candidate = commit(g, source_sha)
    base_sha = candidate["parents"][0]["sha"]
    need(("candidate v" + version) in str(candidate.get("message", "")).splitlines()[0],
         "candidate commit version mismatch")
    work_sha = trailer(candidate.get("message"), "Work-SHA")
    need(SHA.fullmatch(work_sha), "invalid Work SHA")
    need(trailer(candidate["message"], "Main-SHA") == base_sha,
         "candidate main pin mismatch")
    owner = trailer(candidate["message"], "RHC-Issue")
    need(re.fullmatch(r"[1-9][0-9]*", owner), "missing responsible Issue")
    issue_id = int(owner)
    work = commit(g, work_sha)
    need(work["parents"][0]["sha"] == base_sha and
         work["tree"]["sha"] == candidate["tree"]["sha"] and
         trailer(work.get("message"), "RHC-Issue") == owner,
         "Work/Candidate tree, Issue or parent mismatch")
    issue = g.get_issue(issue_id)
    need(issue.get("number") == issue_id and
         (issue.get("state") == "open" or
          (allow_completed and issue.get("state") == "closed")) and
         str(issue.get("title", "")).startswith("[RHC-" + owner + "] "),
         "canonical Issue state/identity not valid")
    merged_sha = g.get_main_sha()
    need(isinstance(merged_sha, str) and SHA.fullmatch(merged_sha),
         "public main not authoritative")
    prs = g.list_release_prs(merged_sha)
    need(isinstance(prs, list) and len(prs) == 1 and
         type(prs[0].get("number")) is int, "unique merged PR missing")
    pr_num = prs[0]["number"]
    pr = g.get_pr(pr_num)
    need(pr.get("merged") is True and pr.get("state") == "closed" and
         pr.get("merge_commit_sha") == merged_sha, "PR merge not verified")
    stage_sha = (pr.get("head") or {}).get("sha")
    need(isinstance(stage_sha, str) and SHA.fullmatch(stage_sha) and
         (pr.get("base") or {}).get("sha") == base_sha and
         g.get_merge_parents(merged_sha) == [base_sha, stage_sha],
         "PR stage/merge ancestry incorrect")
    need(re.search(r"\b(?:Refs|Closes) #" + owner + r"\b", str(pr.get("body") or "")),
         "PR not linked to responsible Issue")
    stage = commit(g, stage_sha)
    need(stage["parents"][0]["sha"] == source_sha and
         stage["tree"]["sha"] != candidate["tree"]["sha"],
         "stage not new candidate-descendant release tree")
    comments = g.list_issue_comments(issue_id)
    need(isinstance(comments, list) and len(comments) < 100,
         "Issue comments truncated")
    canonical = [c for c in comments if isinstance(c, dict) and
                 ROLLING_ID_MARKER.format(issue=issue_id) in str(c.get("body") or "")]
    need(len(canonical) == 1 and type(canonical[0].get("id")) is int,
         "canonical Rolling Comment not unique")
    content = canonical[0]["body"]
    audit.canonical(content)
    bootstrap = [line for line in content.splitlines()
                 if line.startswith("**Bootstrap creation ISO timestamp:** ")]
    need(len(bootstrap) == 1 and
         bootstrap[0].endswith("Z" + chr(96)) and
         bootstrap[0].count(chr(96)) == 2,
         "frozen original BOOTSTRAP clock missing")
    ids = {"work": find_run(g, work_sha, "work"),
           "candidate": find_run(g, source_sha, "candidate"),
           "publisher": publisher_run_id,
           "downloads": find_run(g, stage_sha, "downloads"),
           "rhc102": find_run(g, merged_sha, "rhc102")}
    need(len(set(ids.values())) == 5, "required hosted workflows not distinct")
    return dict(mode="release", issue=issue_id, comment_id=canonical[0]["id"],
                pr=pr_num, work_sha=work_sha, base_sha=base_sha,
                source_sha=source_sha, stage_sha=stage_sha,
                merged_sha=merged_sha, version=version, run_ids=ids)


class Gateway(audit.GitHubGateway):
    """Only existing GITHUB_TOKEN/gh transport; no publisher dispatch."""
    def get_git_commit(self, sha):
        return self.api("GET", "git/commits/" + sha)
    def create_fast_audit_comment(self, number, body):
        """Exactly one Fast-Path four-run audit, never a general POST gateway.

        The caller has already authenticated all four real workflow jobs,
        source ancestry, immutable tag and merged PR. Revalidate the bound
        public main/Issue/source/manifest and absence of any existing record
        immediately before the one permitted remote POST. No API write replay.
        """
        from rhc190_fast_closure import RECORD
        need(type(number) is int and number > 0 and
             isinstance(body, str) and body.startswith(RECORD) and
             len(body) < 2048, "invalid requested Fast audit comment")
        try:
            proof = json.loads(body[len(RECORD):])
        except (TypeError, ValueError) as exc:
            raise ValueError("RHC158_CLOSURE_BLOCKED: invalid Fast audit JSON") from exc
        keys = {"issue", "version", "mainSha", "sourceSha", "pr",
                "runIds", "validation"}
        need(isinstance(proof, dict) and set(proof) == keys and
             proof.get("issue") == number and
             type(proof.get("issue")) is int and
             type(proof.get("pr")) is int and proof["pr"] > 0 and
             isinstance(proof.get("version"), str) and
             VERS.fullmatch(proof["version"]) and
             isinstance(proof.get("mainSha"), str) and
             SHA.fullmatch(proof["mainSha"]) and
             isinstance(proof.get("sourceSha"), str) and
             SHA.fullmatch(proof["sourceSha"]) and
             proof.get("validation") ==
             "ACTUAL_CANDIDATE_3_PUBLISHER_4_DOWNLOADS_1_RHC102_3" and
             isinstance(proof.get("runIds"), dict) and
             set(proof["runIds"]) ==
             {"candidate", "publisher", "downloads", "rhc102"} and
             all(type(n) is int and n > 0 for n in proof["runIds"].values()) and
             len(set(proof["runIds"].values())) == 4 and
             body == RECORD + json.dumps(proof, sort_keys=True),
             "Fast audit body/issue/run roles not exact and immutable")
        issue = self.get_issue(number)
        latest = self.get_latest()
        need(isinstance(issue, dict) and issue.get("number") == number and
             issue.get("state") == "open" and
             str(issue.get("title", "")).startswith(f"[RHC-{number}] ") and
             self.get_main_sha() == proof["mainSha"] and
             isinstance(latest, dict) and
             latest.get("version") == proof["version"] and
             latest.get("sourceSha") == proof["sourceSha"],
             "Fast audit remote public Issue/main/source drift")
        prior = self.list_issue_comments(number)
        need(isinstance(prior, list) and len(prior) < 100 and
             not any(isinstance(c, dict) and
                     str(c.get("body", "")).startswith(RECORD) for c in prior),
             "Fast audit duplicate or ambiguous previous comment")
        # This exact argv is the ONLY permitted remote POST. The generic
        # inherited GitHubGateway.api continues to prohibit all POST calls.
        path = f"repos/{self.repo}/issues/{number}/comments"
        call = subprocess.run(["gh", "api", "-X", "POST", path,
                               "--input", "-"],
                              input=json.dumps({"body": body}),
                              text=True, capture_output=True, timeout=45)
        need(call.returncode == 0,
             "Fast audit POST outcome unverified; GET reconciliation required")
        try:
            response = json.loads(call.stdout)
        except (TypeError, ValueError) as exc:
            raise ValueError("RHC158_CLOSURE_BLOCKED: Fast audit POST readback malformed") from exc
        need(isinstance(response, dict) and
             type(response.get("id")) is int and response["id"] > 0 and
             response.get("body") == body,
             "Fast audit POST response missing exact original body/id")
        return response

    def list_release_prs(self, sha):
        rows = self.api("GET", "commits/" + sha + "/pulls?per_page=100")
        need(isinstance(rows, list) and len(rows) < 100, "PR list truncated")
        return rows
    def list_issue_comments(self, issue):
        rows = self.api("GET", f"issues/{issue}/comments?per_page=100")
        need(isinstance(rows, list) and len(rows) < 100, "comments truncated")
        return rows
    def find_success_runs(self, sha, event):
        obj = self.api("GET", f"actions/runs?head_sha={sha}&per_page=100")
        need(isinstance(obj, dict) and type(obj.get("total_count")) is int and
             obj["total_count"] < 100 and
             isinstance(obj.get("workflow_runs"), list), "run search truncated")
        return [x for x in obj["workflow_runs"] if x.get("event") == event]


def closure_seconds(publisher_utc, closed_utc):
    """Measured actual GitHub Publisher updated_at to Issue closed_at, not chat UI."""
    try:
        p = datetime.fromisoformat(publisher_utc.replace("Z", "+00:00"))
        c = datetime.fromisoformat(closed_utc.replace("Z", "+00:00"))
        need(p.tzinfo is not None and c.tzinfo is not None,
             "missing timezone")
        seconds = (c - p).total_seconds()
        need(seconds >= 0, "nonmonotonic hosted close clock")
        return seconds
    except (ValueError, TypeError, AttributeError):
        return None


def already_completed(g, proof):
    """Idempotent duplicate events: no write, but still all real gates verified."""
    events = audit.verify_acceptance(g, proof)
    issue = g.get_issue(proof["issue"])
    need(issue.get("state") == "closed" and
         issue.get("state_reason") == "completed" and
         isinstance(issue.get("closed_at"), str),
         "Issue not authoritatively completed")
    comment = g.get_comment(proof["comment_id"])
    body = comment.get("body", "")
    audit.canonical(body)
    if "**Agent-State:** WAITING_FOR_GITHUB" in body:
        # Remote close may already have succeeded even when RHC139's final
        # journal PATCH failed. The Issue must really be CLOSED/completed and
        # all five hosted safety gates must be independently verified first.
        return audit.complete_closed_comment(g, proof, events)
    need("**Agent-State:** COMPLETED" in body,
         "Issue closed before canonical completion")
    records = re.findall(r"(?m)^- RHC139_ISSUE_CLOSED (\{[^\r\n]+\})$", body)
    need(len(records) == 1, "missing or ambiguous RHC-139 closure evidence")
    record = json.loads(records[0])
    need(record == {"issue": proof["issue"],
                    "closed_at": issue["closed_at"],
                    "merge_sha": proof["merged_sha"], "status": "completed"},
         "Issue closure evidence/merge identity mismatch")
    events = re.findall(r"(?m)^- RHC139_EVENT (\{[^\r\n]+\})$", body)
    expected = {"work", "candidate", "publisher", "downloads", "rhc102"}
    parsed = [json.loads(row) for row in events]
    need(len(parsed) == 5 and
         {row.get("key", "").split("-")[0] for row in parsed} == expected and
         {row.get("run_id") for row in parsed} == set(proof["run_ids"].values()),
         "already-completed audit lacks five real gate events")
    return {"status": "ALREADY_COMPLETED", "closed_at": issue["closed_at"]}



def wait_for_publisher(g, publisher_id, expected_source_sha, *,
                       timeout_seconds=120, poll_seconds=3,
                       monotonic=time.monotonic, sleep=time.sleep):
    """Boundedly wait for the SAME authenticated Publisher to finish SUCCESS.

    The dispatch occurs after genuine RHC102 success but before the Publisher
    itself can report completed. Waiting never authorizes closure: the full
    existing RHC139 five-run/four-job provenance still executes afterwards.
    No polling of unrelated workflow runs or cross-version fallback.
    """
    need(type(publisher_id) is int and publisher_id > 0,
         "invalid exact Publisher run id")
    need(isinstance(expected_source_sha, str) and SHA.fullmatch(expected_source_sha),
         "required explicit Candidate SHA absent")
    need(0 < timeout_seconds <= 180 and 0 < poll_seconds <= 10,
         "unsafe Publisher wait bounds")
    limit = monotonic() + timeout_seconds
    frozen = None
    while True:
        current = g.get_run(publisher_id)
        need(isinstance(current, dict) and current.get("id") == publisher_id and
             current.get("head_sha") == expected_source_sha and
             current.get("event") == "workflow_dispatch" and
             current.get("name") == "RHC Reusable Interim Unsigned Release" and
             (current.get("actor") or {}).get("login") == "github-actions[bot]" and
             isinstance(current.get("head_branch"), str) and
             re.fullmatch(r"candidate/v[0-9]+(?:\.[0-9]+){3}",
                          current["head_branch"]) and
             type(current.get("run_attempt")) is int and
             current["run_attempt"] > 0,
             "untrusted Publisher identity, event or source")
        identity = (current["id"], current["head_sha"], current["event"],
                    current["name"], current["head_branch"],
                    current["run_attempt"], current["actor"]["login"])
        if frozen is None:
            frozen = identity
        need(identity == frozen, "Publisher identity changed during wait")
        state = current.get("status")
        if state == "completed":
            need(current.get("conclusion") == "success",
                 "Publisher terminal state is not success")
            return current
        need(state in ("queued", "in_progress", "waiting", "pending", "requested") and
             current.get("conclusion") is None,
             "Publisher has unexpected nonterminal state")
        remaining = limit - monotonic()
        need(remaining > 0, "authenticated Publisher completion timed out")
        sleep(min(remaining, poll_seconds))



def resilient_finalize(g, publisher_id, proof, *, apply=False, max_attempts=3):
    """Retry ONLY a proven prewrite optimistic conflict, never unknown writes.

    Refetch the entire immutable release/Issue/run proof after a conflict, not
    just the mutable comment. No retry after first remote PATCH is attempted.
    """
    need(type(max_attempts) is int and 1 <= max_attempts <= 3,
         "unbounded optimistic comment retries")
    for attempt in range(max_attempts):
        try:
            return audit.finalize(g, proof, now=datetime.now(timezone.utc),
                                  apply=apply)
        except ValueError as exc:
            reason = str(exc)
            prewrite = reason in (
                "RHC139_AUDIT_BLOCKED: concurrent Rolling Comment revision changed",
                "RHC139_AUDIT_BLOCKED: comment changed before patch",
            )
            if not prewrite or attempt == max_attempts - 1:
                raise
            fresh = collect_release_proof(g, publisher_id, allow_completed=True)
            need(fresh == proof, "release identity drift during comment revalidation")
            need(g.get_issue(proof["issue"]).get("state") == "open",
                 "Issue changed during comment revalidation")
    raise ValueError("RHC158_CLOSURE_BLOCKED: bounded retry exhausted")


def blocked_diagnostic(exc):
    """Only approved stable predicates, never raw API errors/comments/tokens."""
    reason = str(exc)
    if reason.startswith((
        "RHC139_AUDIT_BLOCKED: concurrent Rolling Comment revision changed",
        "RHC139_AUDIT_BLOCKED: comment changed before patch",
    )):
        code = "ROLLING_PREWRITE_CONFLICT"
    elif reason.startswith("RHC139_AUDIT_BLOCKED:") and (
            "readback" in reason.lower() or "after Issue close" in reason):
        code = "POSTWRITE_READBACK_UNVERIFIED"
    elif "Publisher" in reason and "timed out" in reason:
        code = "PUBLISHER_WAIT_TIMEOUT"
    elif "required real hosted jobs" in reason or "hosted workflow" in reason:
        code = "HOSTED_GATE_NOT_VERIFIED"
    elif "already" in reason.lower() and "closed" in reason.lower():
        code = "ISSUE_CLOSURE_STATE_UNVERIFIED"
    elif isinstance(exc, (OSError, RuntimeError, KeyError, TypeError)):
        code = "GITHUB_OR_RUNTIME_READBACK_UNVERIFIED"
    else:
        code = "ELIGIBILITY_OR_AUDIT_BLOCKED"
    return {"result": "BLOCKED_NOT_VERIFIED", "code": code,
            "exception": type(exc).__name__,
            "safeDiagnostic": True}



def close_release(g, publisher_id, apply=False, *,
                  expected_source_sha=None, wait=False):
    if wait:
        wait_for_publisher(g, publisher_id, expected_source_sha)
    # RHC-190 branchless Patch/Hotfix has no Work ref or rolling Work comment.
    # Delegate to a separately fail-closed four-run verifier, never forge Work evidence.
    # Gateway.get_git_commit exists in the actual authenticated operator.
    # Test gateways without this optional method retain the legacy proof path;
    # they cannot enter the fast branch without explicit candidate evidence.
    if hasattr(g, "get_git_commit"):
        publisher = g.get_run(publisher_id)
        candidate = g.get_git_commit(publisher.get("head_sha", ""))
        if re.findall(r"(?m)^Development-Path: fast$", candidate.get("message", "")):
            from rhc190_fast_closure import close_fast
            return close_fast(g, publisher_id, expected_source_sha, apply=apply)
    proof = collect_release_proof(g, publisher_id, allow_completed=True)
    if expected_source_sha is not None:
        need(isinstance(expected_source_sha, str) and
             SHA.fullmatch(expected_source_sha) and
             proof["source_sha"] == expected_source_sha,
             "explicit dispatch source does not match authenticated Publisher")
    if g.get_issue(proof["issue"]).get("state") == "closed":
        result = already_completed(g, proof)
    else:
        # RHC-139 is authoritative for exact hosted job roles and readback,
        # two-stage fail-closed comment update and Issue close. Never bypass it.
        result = resilient_finalize(g, publisher_id, proof, apply=apply)
    elapsed = None
    if result["status"] in ("COMPLETED", "COMPLETED_RECOVERED", "ALREADY_COMPLETED"):
        elapsed = closure_seconds(g.get_run(publisher_id).get("updated_at"),
                                  result.get("closed_at"))
    return {"status": result["status"], "issue": proof["issue"],
            "publisher": publisher_id, "pr": proof["pr"],
            "closed_at": result.get("closed_at"), "source_sha": proof["source_sha"],
            "publisher_to_issue_close_seconds": elapsed,
            "closure_kpi": "NOT_VERIFIED" if elapsed is None else
                           ("MET" if elapsed <= 60 else "ABOVE_TARGET")}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repository", required=True)
    ap.add_argument("--publisher-run-id", type=int, required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--expected-source-sha", default=None)
    ap.add_argument("--wait-for-publisher", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = close_release(Gateway(args.repository), args.publisher_run_id,
                               apply=args.apply,
                               expected_source_sha=args.expected_source_sha,
                               wait=args.wait_for_publisher)
        print("RHC158_CLOSURE=" + json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as exc:
        print("RHC158_CLOSURE_BLOCKED_NOT_VERIFIED=" +
              json.dumps(blocked_diagnostic(exc), sort_keys=True),
              file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
