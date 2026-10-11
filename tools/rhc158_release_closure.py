#!/usr/bin/env python3
"""RHC-158: guarded nonpublishing operator for post-Publisher Issue closure.

No release, PR, tag, branch, download or product mutation. Existing RHC-139
performs the only opt-in canonical comment PATCH and completed Issue closure.
"""
import argparse
from datetime import datetime, timezone
import json
import re
import sys
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


def collect_release_proof(g, publisher_run_id):
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
    need(issue.get("number") == issue_id and issue.get("state") == "open" and
         str(issue.get("title", "")).startswith("[RHC-" + owner + "] "),
         "canonical Issue not open")
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


def close_release(g, publisher_id, apply=False):
    proof = collect_release_proof(g, publisher_id)
    # RHC-139 is authoritative for exact hosted job roles and readback,
    # two-stage fail-closed comment update and Issue close. Never bypass it.
    result = audit.finalize(g, proof, now=datetime.now(timezone.utc), apply=apply)
    elapsed = None
    if result["status"] == "COMPLETED":
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
    args = ap.parse_args(argv)
    try:
        result = close_release(Gateway(args.repository), args.publisher_run_id,
                               apply=args.apply)
        print("RHC158_CLOSURE=" + json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError):
        print("RHC158_CLOSURE_BLOCKED_NOT_VERIFIED", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
