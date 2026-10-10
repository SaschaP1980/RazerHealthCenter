#!/usr/bin/env python3
"""RHC-114 read-only report: do not misread GitHub zero-job events as hosted proof.

This does not disable PR triggers, alter GitHub's actual conclusions, make
publication decisions, retry writes or infer GITHUB_TOKEN causality.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys

SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BOT = "github-actions[bot]"
# Historical and current supplementary PR workflow identity. These are
# workflow IDs from GitHub's actual RHC-105 incident, not required check IDs.
SUPPLEMENTARY = frozenset((378374563, 378644602, 378158256))


class EvidenceBlocked(ValueError):
    """Evidence is insufficient for a trusted exact-SHA hosted gate."""


def require(ok, message):
    if not ok:
        raise EvidenceBlocked("RHC114_EVIDENCE_BLOCKED: " + message)


def verified_pr(pr, sha):
    require(isinstance(sha, str) and SHA.fullmatch(sha),
            "missing exact release-stage SHA")
    require(isinstance(pr, dict) and type(pr.get("number")) is int and pr["number"] > 0,
            "missing numbered release PR")
    head, base = pr.get("head"), pr.get("base")
    require(isinstance(head, dict) and head.get("sha") == sha
            and isinstance(head.get("ref"), str)
            and head["ref"].startswith("release/v")
            and isinstance(base, dict) and base.get("ref") == "main",
            "release PR head/base does not match expected immutable stage")
    return pr


def _job_list(jobs, run_id):
    require(isinstance(jobs, list), "hosted job evidence unavailable")
    for job in jobs:
        require(isinstance(job, dict) and
                (job.get("run_id") is None or job["run_id"] == run_id),
                "hosted job belongs to an unrelated run")
    return jobs


def classify_supplementary(pr, sha, runs, jobs_by_run):
    """Keep each true run conclusion; never synthesize a passing check."""
    verified_pr(pr, sha)
    require(isinstance(runs, list) and isinstance(jobs_by_run, dict),
            "supplementary run/job enumeration unavailable")
    classified = []
    seen = set()
    for run in runs:
        require(isinstance(run, dict) and type(run.get("id")) is int
                and run["id"] > 0 and run["id"] not in seen, "invalid/duplicate run ID")
        rid = run["id"]
        seen.add(rid)
        require(run.get("head_sha") == sha, "supplementary run points to a stale SHA")
        require(run.get("status") == "completed",
                "supplementary run not terminal; classification deferred")
        require(rid in jobs_by_run, "missing actual GitHub jobs enumeration")
        jobs = _job_list(jobs_by_run[rid], rid)
        conclusion = run.get("conclusion")
        actor = (run.get("actor") or {}).get("login")
        is_supplementary = (run.get("workflow_id") in SUPPLEMENTARY
                            and run.get("event") == "pull_request")
        is_bot = (pr.get("user") or {}).get("login") == BOT and actor == BOT
        if not is_supplementary:
            classification = "UNRELATED_RUN_NOT_QUALIFICATION"
        elif jobs and any(j.get("conclusion") == "failure" for j in jobs):
            classification = "ACTUAL_HOSTED_JOB_FAIL"
        elif jobs and conclusion == "success" and all(
                j.get("status") == "completed" and j.get("conclusion") == "success"
                for j in jobs):
            classification = "SUPPLEMENTARY_HOSTED_SUCCESS_NOT_TRUSTED_DISPATCH"
        elif jobs:
            classification = "HOSTED_JOBS_NOT_SUCCESSFUL"
        elif conclusion == "failure" and is_bot:
            classification = "SUPPLEMENTARY_ZERO_JOB_FAILURE"
        elif conclusion == "failure":
            classification = "ZERO_JOB_FAILURE_UNEXPLAINED"
        else:
            classification = "ZERO_JOB_NO_TEST_" + str(conclusion or "unknown").upper()
        classified.append(dict(runId=rid, workflowId=run.get("workflow_id"),
                               workflow=run.get("name"), event=run.get("event"),
                               actor=actor, headSha=sha, status=run["status"],
                               conclusion=conclusion, actualJobs=len(jobs),
                               createdAt=run.get("created_at"),
                               updatedAt=run.get("updated_at"),
                               classification=classification,
                               countsAsTrustedGate=False,
                               rootCause="NOT VERIFIED — zero jobs alone cannot prove GitHub token/event restriction"))
    return classified


def verify_trusted_dispatch(run, jobs, sha, workflow_id):
    """Exactly bound real dispatch + hosted jobs, independent of PR event noise."""
    require(isinstance(sha, str) and SHA.fullmatch(sha), "invalid exact SHA")
    require(type(workflow_id) is int and workflow_id > 0, "invalid expected workflow ID")
    require(isinstance(run, dict) and type(run.get("id")) is int
            and run["id"] > 0 and run.get("workflow_id") == workflow_id
            and run.get("head_sha") == sha
            and run.get("event") == "workflow_dispatch"
            and (run.get("actor") or {}).get("login") == BOT
            and run.get("status") == "completed"
            and run.get("conclusion") == "success",
            "no authenticated exact-stage completed-success workflow_dispatch")
    rows = _job_list(jobs, run["id"])
    require(len(rows) >= 1, "trusted dispatch completed with zero real hosted jobs")
    require(all(type(j.get("id")) is int and j["id"] > 0
                and isinstance(j.get("name"), str) and bool(j["name"].strip())
                and j.get("status") == "completed"
                and j.get("conclusion") == "success" for j in rows),
            "required hosted job failed, skipped, cancelled or incomplete")
    return dict(classification="TRUSTED_HOSTED_PASS", runId=run["id"],
                workflowId=workflow_id, headSha=sha,
                event="workflow_dispatch", conclusion="success",
                actualJobs=len(rows), jobIds=[j["id"] for j in rows],
                countsAsTrustedGate=True)



def _utc_seconds(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        stamp = dt.datetime.fromisoformat(value[:-1] + "+00:00")
        return stamp.timestamp()
    except ValueError:
        return None


def _timing(pr, supplementary, trusted):
    """Measurements only when GitHub exposes authoritative event timestamps."""
    merged = _utc_seconds(pr.get("merged_at"))
    finished = _utc_seconds(trusted.get("updated_at"))
    if merged is None or finished is None:
        return dict(mergedAt=pr.get("merged_at"),
                    trustedCompletedAt=trusted.get("updated_at"),
                    evidence="unknown — no verified critical-path timestamp pair",
                    performanceGain="NOT VERIFIED")
    rows = []
    for r in supplementary:
        elapsed = _utc_seconds(r.get("updatedAt"))
        rows.append(dict(runId=r["runId"],
                         completedSecondsAfterMerge=(round(elapsed - merged, 3)
                            if elapsed is not None else None)))
    return dict(mergedAt=pr["merged_at"], trustedCompletedAt=trusted["updated_at"],
                trustedCompletedSecondsBeforeMerge=round(merged - finished, 3),
                supplementaryCompletions=rows,
                performanceGain="NOT VERIFIED — cannot infer causality or improvement")


def evaluate_release_pr(pr, sha, extra_runs, jobs_by_run, trusted_run,
                        trusted_jobs, trusted_workflow_id):
    verified_pr(pr, sha)
    extra = classify_supplementary(pr, sha, extra_runs, jobs_by_run)
    gate = verify_trusted_dispatch(trusted_run, trusted_jobs, sha, trusted_workflow_id)
    noise = sum(x["classification"] == "SUPPLEMENTARY_ZERO_JOB_FAILURE" for x in extra)
    genuine = sum(x["classification"] == "ACTUAL_HOSTED_JOB_FAIL" for x in extra)
    return dict(result=("TRUSTED_GATE_PASS_WITH_OTHER_HOSTED_FAILURES_REQUIRING_REVIEW"
                        if genuine else "TRUSTED_GATE_PASS_WITH_SEPARATE_SUPPLEMENTARY_EVIDENCE"),
                repositoryReleasePR=pr["number"], sourceSha=sha,
                trustedGate=gate, supplementary=dict(
                    totalRuns=len(extra), zeroJobFailureCount=noise,
                    actualHostedFailures=genuine, records=extra),
                releaseCriticalPath=_timing(pr, extra, trusted_run),
                interpretation=(
                    "The trusted exact-SHA dispatch has real successful jobs. "
                    "Supplementary pull_request outcomes retain original failure/skip state; "
                    "zero jobs do not mean tests passed or failed. Causality and performance "
                    "improvement are NOT VERIFIED by this report."
                ))


def _one_page(get, path, key):
    data = get(path + "&per_page=100&page=1" if "?" in path else path + "?per_page=100&page=1")
    require(isinstance(data, dict) and isinstance(data.get(key), list)
            and type(data.get("total_count")) is int
            and data["total_count"] == len(data[key]) and data["total_count"] < 100,
            "API job/run evidence missing, inconsistent or exceeds single-page bound")
    return data[key]


def read_only_github_audit(get, pr_number, sha, trusted_run_id, trusted_workflow_id):
    """GET only; complete bounded response required, no publication mutations."""
    require(type(pr_number) is int and pr_number > 0, "invalid PR number")
    require(type(trusted_run_id) is int and trusted_run_id > 0, "invalid trusted run ID")
    pr = get("/pulls/{}".format(pr_number))
    require(isinstance(pr, dict) and pr.get("number") == pr_number,
            "PR readback identity mismatch")
    verified_pr(pr, sha)
    runs = _one_page(get, "/actions/runs?head_sha={}&event=pull_request".format(sha),
                     "workflow_runs")
    extras = [r for r in runs if r.get("workflow_id") in SUPPLEMENTARY]
    jobs_by_run = {r["id"]: _one_page(
        get, "/actions/runs/{}/jobs".format(r["id"]), "jobs") for r in extras}
    trusted = get("/actions/runs/{}".format(trusted_run_id))
    trusted_jobs = _one_page(
        get, "/actions/runs/{}/jobs".format(trusted_run_id), "jobs")
    return evaluate_release_pr(pr, sha, extras, jobs_by_run, trusted,
                               trusted_jobs, trusted_workflow_id)


def main(argv=None):
    p = argparse.ArgumentParser(description="RHC-114 read-only release PR CI evidence audit")
    p.add_argument("--repository", required=True)
    p.add_argument("--pr", type=int, required=True)
    p.add_argument("--stage-sha", required=True)
    p.add_argument("--trusted-run-id", type=int, required=True)
    p.add_argument("--trusted-workflow-id", type=int, required=True)
    args = p.parse_args(argv)
    try:
        require(REPO.fullmatch(args.repository) is not None, "invalid repository selector")
        def get(path):
            command = ["gh", "api", "-X", "GET",
                       "repos/" + args.repository + path]
            done = subprocess.run(command, text=True, capture_output=True,
                                  check=False, timeout=40)
            require(done.returncode == 0,
                    "GitHub API GET failed: " + done.stderr.strip()[:200])
            try:
                return json.loads(done.stdout)
            except (ValueError, TypeError) as exc:
                raise EvidenceBlocked("GitHub API did not return JSON") from exc
        report = read_only_github_audit(get, args.pr, args.stage_sha,
                                        args.trusted_run_id, args.trusted_workflow_id)
        print("RHC114_CI_EVIDENCE=" + json.dumps(report, sort_keys=True))
        return 0
    except (EvidenceBlocked, OSError, subprocess.TimeoutExpired) as exc:
        print("RHC114_CI_EVIDENCE_BLOCKED=" + json.dumps(
            {"result": "BLOCKED", "detail": str(exc)}, sort_keys=True),
            file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
