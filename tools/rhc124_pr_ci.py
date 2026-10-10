#!/usr/bin/env python3
"""RHC-124: read-only, fail-closed PR CI gate for dedicated GitHub App release PRs.

Never creates PRs, statuses, Candidate refs or publications. Real hosted jobs
and independent check suites must match exactly; zero-job noise is NOT PASS.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys

SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
BOT = re.compile(r"[a-z0-9][a-z0-9_-]*\[bot\]\Z")
EXPECTED = {
    378158256: (
        "RHC Infrastructure Qualification (nonpublishing)",
        ("rhc/infra/linux", "rhc/infra/windows", "rhc/infra/artifact-node24"),
    ),
    378374563: (
        "RHC Repository Downloads Integrity (nonpublishing)",
        ("Validate ZIP manifest and unmodified release history",),
    ),
    378644602: (
        "RHC-12 Release Preactivation Evidence Check (read-only)",
        ("Verify immutable downloads and current release policy rejection",),
    ),
}


class EvidenceBlocked(ValueError):
    """A terminal failed, ambiguous, or untrusted release PR check."""


class EvidencePending(ValueError):
    """One or more required genuine GitHub runs have not yet completed."""


def require(condition, message):
    if not condition:
        raise EvidenceBlocked("RHC124_PR_CI_BLOCKED: " + message)


def _date(value):
    require(isinstance(value, str) and value.endswith("Z"),
            "missing/non-UTC event time")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceBlocked("invalid GitHub event time") from exc
    return parsed


def verify_pr_ci(pr, runs, jobs_by_run, sha, expected_actor):
    """Pure CI admission decision. Never green an unexecuted or failed run."""
    require(isinstance(sha, str) and SHA.fullmatch(sha), "invalid stage SHA")
    require(isinstance(expected_actor, str) and BOT.fullmatch(expected_actor)
            and expected_actor != "github-actions[bot]", "invalid App bot identity")
    require(isinstance(pr, dict) and type(pr.get("number")) is int
            and pr["number"] > 0 and pr.get("state") == "open"
            and pr.get("draft") is False and not pr.get("merged_at"),
            "exact numbered unmerged PR required")
    head, base = pr.get("head") or {}, pr.get("base") or {}
    require(head.get("sha") == sha and isinstance(head.get("ref"), str)
            and re.fullmatch(r"release/v\d+\.\d+\.\d+\.\d+(?:-retry1)?",
                             head["ref"]) is not None
            and base.get("ref") == "main",
            "release PR head SHA/ref/base not exact")
    require((pr.get("user") or {}).get("login") == expected_actor,
            "release PR creator must be the dedicated GitHub App")
    require(isinstance(pr.get("title"), str) and pr["title"]
            and isinstance(runs, list) and isinstance(jobs_by_run, dict),
            "missing PR or run/job evidence")
    created = _date(pr.get("created_at"))
    found = {}
    for run in runs:
        require(isinstance(run, dict), "invalid GitHub workflow run")
        workflow = run.get("workflow_id")
        if workflow not in EXPECTED:
            continue
        require(workflow not in found, "duplicate/ambiguous required PR workflow")
        require(type(run.get("id")) is int and run["id"] > 0
                and run.get("head_sha") == sha
                and run.get("head_branch") == head["ref"]
                and run.get("event") == "pull_request"
                and (run.get("actor") or {}).get("login") == expected_actor
                and run.get("display_title") == pr["title"]
                and run.get("name") == EXPECTED[workflow][0]
                and _date(run.get("created_at")) >= created,
                "PR run actor/event/ref/SHA/title/time/provenance mismatch")
        found[workflow] = run
    pending = []
    for workflow in EXPECTED:
        if workflow not in found:
            pending.append("missing workflow " + str(workflow))
            continue
        run = found[workflow]
        if run.get("status") != "completed":
            require(run.get("status") in ("queued", "in_progress", "requested",
                                          "waiting", "pending")
                    and run.get("conclusion") is None,
                    "invalid nonterminal run state")
            pending.append("running workflow " + str(workflow))
            continue
        require(run.get("conclusion") == "success",
                "required PR workflow non-success: " + str(workflow)
                + " " + str(run.get("conclusion")))
        rid = run["id"]
        require(rid in jobs_by_run and isinstance(jobs_by_run[rid], list),
                "actual hosted jobs unavailable for " + str(rid))
        jobs = jobs_by_run[rid]
        expected_names = EXPECTED[workflow][1]
        require(len(jobs) == len(expected_names) and
                {j.get("name") for j in jobs if isinstance(j, dict)}
                == set(expected_names),
                "required actual hosted job list missing/extra/duplicate")
        ids = set()
        for j in jobs:
            require(isinstance(j, dict) and type(j.get("id")) is int
                    and j["id"] not in ids and j.get("run_id") == rid
                    and j.get("status") == "completed"
                    and j.get("conclusion") == "success",
                    "required hosted job missing, foreign, skipped or failed")
            ids.add(j["id"])
    if pending:
        raise EvidencePending("RHC124_PR_CI_PENDING: " + ", ".join(pending))
    return dict(result="PASS", pr=pr["number"], stageSha=sha,
                actor=expected_actor, workflows=3, jobs=5,
                runIds={str(k): found[k]["id"] for k in sorted(EXPECTED)})


def verify_check_suites(pr_report, runs, jobs_by_run, suites, check_runs):
    """Second real GitHub check-suite/check-run readback, exact job IDs only."""
    require(pr_report.get("result") == "PASS"
            and isinstance(suites, list) and isinstance(check_runs, list),
            "missing check-suite evidence")
    selected = [r for r in runs if r.get("workflow_id") in EXPECTED]
    ids = set()
    for run in selected:
        sid = run.get("check_suite_id")
        require(type(sid) is int and sid > 0 and sid not in ids,
                "missing/duplicate check-suite ID")
        ids.add(sid)
        matches = [s for s in suites if s.get("id") == sid]
        require(len(matches) == 1 and
                matches[0].get("status") == "completed" and
                matches[0].get("conclusion") == "success" and
                matches[0].get("head_sha") == pr_report["stageSha"] and
                matches[0].get("latest_check_runs_count")
                == len(jobs_by_run[run["id"]]), "suite not independently SUCCESS")
        for job in jobs_by_run[run["id"]]:
            matches = [c for c in check_runs if c.get("id") == job["id"]]
            require(len(matches) == 1 and
                    (matches[0].get("check_suite") or {}).get("id") == sid
                    and matches[0].get("head_sha") == pr_report["stageSha"]
                    and matches[0].get("name") == job["name"]
                    and matches[0].get("status") == "completed"
                    and matches[0].get("conclusion") == "success",
                    "hosted job lacks matching successful actual check-run")
    return dict(pr_report, checkSuites=3, actualCheckRuns=5)


def gh_get(resource):
    result = subprocess.run(["gh", "api", "-X", "GET", resource],
                            check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def require_collection(payload, field):
    require(isinstance(payload, dict)
            and type(payload.get("total_count")) is int
            and payload["total_count"] <= 100
            and isinstance(payload.get(field), list)
            and payload["total_count"] == len(payload[field]),
            "incomplete/non-paginated GitHub " + field)
    return payload[field]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--stage-sha", required=True)
    parser.add_argument("--actor", required=True)
    args = parser.parse_args()
    try:
        require(REPO.fullmatch(args.repository) is not None and
                SHA.fullmatch(args.stage_sha) is not None and args.pr > 0,
                "invalid repository/PR/SHA request")
        prefix = "repos/" + args.repository + "/"
        pr = gh_get(prefix + "pulls/" + str(args.pr))
        runs = require_collection(gh_get(prefix + "actions/runs?head_sha="
            + args.stage_sha + "&event=pull_request&per_page=100"), "workflow_runs")
        found = [r for r in runs if r.get("workflow_id") in EXPECTED]
        jobs = {}
        for r in found:
            if r.get("status") == "completed":
                jobs[r["id"]] = require_collection(gh_get(
                    prefix + "actions/runs/" + str(r["id"]) + "/jobs?per_page=100"), "jobs")
        result = verify_pr_ci(pr, runs, jobs, args.stage_sha, args.actor)
        suites = require_collection(gh_get(prefix + "commits/"
           + args.stage_sha + "/check-suites?per_page=100"), "check_suites")
        check_runs = require_collection(gh_get(prefix + "commits/"
           + args.stage_sha + "/check-runs?per_page=100"), "check_runs")
        result = verify_check_suites(result, runs, jobs, suites, check_runs)
        print("RHC124_PR_CI=" + json.dumps(result, sort_keys=True))
    except EvidencePending as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (EvidenceBlocked, subprocess.CalledProcessError, ValueError, KeyError, TypeError) as exc:
        print("RHC124_PR_CI=BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
