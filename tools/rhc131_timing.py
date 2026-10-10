#!/usr/bin/env python3
"""RHC-131 read-only Actions timing evidence; never participates in release gates.

Input comes from real GitHub workflow-run / workflow-job / step metadata or
explicit offline fixtures. All emitted fields are allowlisted: no token, URLs,
actor login, runner host, job logs, environment, payloads, or secrets.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_RE = re.compile(r"^[1-9][0-9]{0,17}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
MARKER_RE = re.compile(
    r"^RHC131_PHASE (start|end)=([^ ]+) label=([A-Za-z0-9_]+)$")
PHASE_LABELS = frozenset({
    "validation", "go_test", "i18n_guard", "go_vet", "go_build",
    "resource_patch", "pe_validation", "ui_validation", "checksum",
})


def parse_timestamp(value):
    """Return an aware UTC datetime, None for missing; reject invalid clocks."""
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO8601 string")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp lacks UTC offset")
    return timestamp.astimezone(timezone.utc)


def seconds_between(start, end):
    a, b = parse_timestamp(start), parse_timestamp(end)
    if a is None or b is None:
        return None
    duration = (b - a).total_seconds()
    return round(duration, 3) if duration >= 0 else None


def _interval(start, end):
    a, b = parse_timestamp(start), parse_timestamp(end)
    return (a, b) if a is not None and b is not None and b >= a else None


def _union_seconds(intervals):
    if not intervals:
        return None
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        elif end > merged[-1][1]:
            merged[-1][1] = end
    return round(sum((end - start).total_seconds() for start, end in merged), 3)


def _step_category(name):
    name = (name or "").lower()
    if "upload-artifact" in name or "download-artifact" in name or "transfer" in name:
        return "artifact_transfer"
    if "set up job" in name or "setup-go" in name or "checkout" in name or "post run actions/" in name:
        return "runner_setup"
    if "independent" in name and ("https" in name or "public zip" in name):
        return "remote_https"
    if "merge" in name or "create one combined" in name or "single immutable zip/catalog pr" in name:
        return "release_pr_merge"
    if "package" in name or "zip" in name or "archive" in name:
        return "packaging"
    if "compile" in name and ("validate" in name or "test" in name):
        return "mixed_build_validation"
    if "go windows gui build" in name or "build" in name or "compile" in name:
        return "build"
    if "powershell" in name or "safety" in name or "contract" in name or "test" in name or "verify" in name:
        return "validation"
    return "other"


def _nonempty_str(value):
    return value if isinstance(value, str) and value else None


def _safe_sha(value):
    if value is None:
        return None
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ValueError("expected SHA must be 40 lowercase hex characters")
    return value


def _job_report(raw, run, attempt):
    steps = []
    categories = {}
    unknown_steps = False
    for step in raw.get("steps") or []:
        duration = seconds_between(step.get("started_at"), step.get("completed_at"))
        category = _step_category(step.get("name"))
        steps.append({
            "category": category,
            "execution_seconds": duration,
            "time_verification": "VERIFIED" if duration is not None else "NOT_VERIFIED",
            "conclusion": _nonempty_str(step.get("conclusion")),
        })
        if duration is None:
            unknown_steps = True
        else:
            categories[category] = round(categories.get(category, 0) + duration, 3)
    if unknown_steps:
        categories = None  # cannot present incomplete step sum as complete evidence
    execution = seconds_between(raw.get("started_at"), raw.get("completed_at"))
    job_attempt = raw.get("run_attempt", attempt)
    if isinstance(job_attempt, bool) or not isinstance(job_attempt, int) or job_attempt < 1:
        job_attempt = None
    # Original run.created_at is not the rerun enqueue time.
    queue = (seconds_between(run.get("created_at"), raw.get("started_at"))
             if job_attempt == 1 else None)
    os_label = "unknown"
    labels = raw.get("labels") or []
    if any("windows" in str(l).lower() for l in labels):
        os_label = "windows"
    elif any("ubuntu" in str(l).lower() or "linux" in str(l).lower() for l in labels):
        os_label = "linux"
    return {
        "id": raw.get("id") if type(raw.get("id")) is int else None,
        "name": _nonempty_str(raw.get("name")),
        "os": os_label,
        "attempt": job_attempt,
        "status": _nonempty_str(raw.get("status")),
        "conclusion": _nonempty_str(raw.get("conclusion")),
        "started_at": raw.get("started_at"),
        "completed_at": raw.get("completed_at"),
        "queue_seconds": queue,
        "execution_seconds": execution,
        "time_verification": "VERIFIED" if execution is not None else "NOT_VERIFIED",
        "step_categories": categories,
        "steps": steps,
    }


def _collect_run(raw, jobs_by_run, expected_sha):
    number = raw.get("id")
    if type(number) is not int or number <= 0:
        raise ValueError("run ID must be positive integer")
    entry = jobs_by_run.get(str(number))
    if not isinstance(entry, dict):
        entry = {}
    jobs = entry.get("jobs", [])
    if not isinstance(jobs, list):
        raise ValueError("jobs must be list")
    reported = entry.get("total_count")
    if not isinstance(reported, int) or reported < len(jobs):
        reported = None
    attempt = raw.get("run_attempt", 1)
    if type(attempt) is not int or attempt < 1:
        attempt = None
    sha = raw.get("head_sha")
    status = _nonempty_str(raw.get("status"))
    conclusion = _nonempty_str(raw.get("conclusion"))
    event = _nonempty_str(raw.get("event"))
    actor_bot = (raw.get("actor") or {}).get("login") == "github-actions[bot]"
    if expected_sha is not None and sha != expected_sha:
        classification = "SHA_MISMATCH"
    elif reported is None:
        classification = "INCOMPLETE_JOB_EVIDENCE"
    elif reported == 0 and event == "pull_request" and actor_bot and conclusion == "failure":
        classification = "SUPPLEMENTARY_ZERO_JOB_FAILURE"
    elif reported == 0:
        classification = "NO_HOSTED_JOB_NOT_VERIFIED"
    elif status != "completed" or conclusion is None:
        classification = "NOT_COMPLETED_NOT_VERIFIED"
    elif conclusion != "success":
        classification = "JOB_OR_WORKFLOW_FAILURE"
    elif any(x.get("conclusion") != "success" for x in jobs):
        classification = "JOB_OR_WORKFLOW_FAILURE"
    else:
        classification = "COMPLETED_WITH_HOSTED_SUCCESS"
    observed_until = raw.get("updated_at")
    # GitHub Actions run.updated_at is a change marker, not a true completed_at.
    complete = status == "completed" and conclusion is not None
    report_jobs = [_job_report(j, raw, attempt) for j in jobs]
    return {
        "id": number, "workflow": _nonempty_str(raw.get("name")),
        "event": event, "head_sha": sha if isinstance(sha, str) and SHA_RE.fullmatch(sha) else None,
        "actor_class": "github-actions[bot]" if actor_bot else "OTHER_OR_UNKNOWN",
        "attempt": attempt, "status": status, "conclusion": conclusion,
        "created_at": raw.get("created_at"), "run_started_at": raw.get("run_started_at"),
        "observed_updated_at": observed_until,
        "completion_verification": "OBSERVED_COMPLETED_RUN" if complete else "NOT_VERIFIED",
        "observed_run_window_seconds": seconds_between(raw.get("created_at"), observed_until)
        if complete else None,
        "reported_job_count": reported, "classification": classification,
        "jobs": report_jobs,
    }


def build_report(runs, jobs_by_run, *, expected_sha=None, issue=None, version=None,
                 work_sha=None, candidate_sha=None, stage_sha=None, public_sha=None):
    expected_sha = _safe_sha(expected_sha)
    if not isinstance(runs, list) or not isinstance(jobs_by_run, dict):
        raise ValueError("expected list of runs and per-run job mapping")
    if len(runs) > 100:
        raise ValueError("at most 100 runs")
    for sha in (work_sha, candidate_sha, stage_sha, public_sha):
        _safe_sha(sha)
    reports = [_collect_run(x, jobs_by_run, expected_sha) for x in runs]
    accepted = [r for r in reports if r["classification"] != "SHA_MISMATCH"]
    jobs = [j for r in accepted for j in r["jobs"]]
    valid_jobs = [j for j in jobs if j["execution_seconds"] is not None]
    all_job_times = bool(jobs) and len(valid_jobs) == len(jobs) and all(
        r["reported_job_count"] == len(r["jobs"]) for r in accepted)
    count = sum(len(r["jobs"]) for r in accepted)
    intervals = []
    for j in jobs:
        iv = _interval(j["started_at"], j["completed_at"])
        if iv:
            intervals.append(iv)
    job_union = _union_seconds(intervals) if all_job_times else None
    total_jobs = round(sum(j["execution_seconds"] for j in valid_jobs), 3) if all_job_times else None
    ends = [parse_timestamp(x["observed_updated_at"]) for x in accepted
            if x["completion_verification"] == "OBSERVED_COMPLETED_RUN"]
    starts = [parse_timestamp(x["created_at"]) for x in accepted]
    all_ended = bool(accepted) and len(ends) == len(accepted) and len(starts) == len(accepted) and all(starts) and all(ends)
    wall = round((max(ends) - min(starts)).total_seconds(), 3) if all_ended and max(ends) >= min(starts) else None
    if job_union is not None and wall is not None and job_union > wall + 0.001:
        job_union = None  # contradictory clocks; do not fabricate nonbusy time
    max_attempt = max((j["attempt"] for j in jobs if j["attempt"] is not None), default=1)
    retry = [j for j in valid_jobs if j["attempt"] is not None and j["attempt"] < max_attempt
             and j["conclusion"] != "success"]
    winning = [j for j in valid_jobs if j["attempt"] == max_attempt]
    critical_lb = max((j["execution_seconds"] for j in valid_jobs), default=None) if all_job_times else None
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "READ_ONLY_NON_AUTHORITATIVE_NO_RELEASE_GATE",
        "issue": issue if type(issue) is int and issue > 0 else None,
        "version": version if isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", version) else None,
        "work_sha": work_sha, "candidate_sha": candidate_sha,
        "stage_sha": stage_sha, "public_sha": public_sha, "expected_sha": expected_sha,
        "runs": reports,
        "zero_job_supplementary_failures": sum(
            r["classification"] == "SUPPLEMENTARY_ZERO_JOB_FAILURE" for r in accepted),
        "measurement": {
            "included_run_count": len(accepted), "reported_hosted_job_count": count,
            "observed_wall_seconds": wall,
            "sum_job_seconds": total_jobs,
            "job_active_union_seconds": job_union,
            "job_overlap_seconds": round(total_jobs - job_union, 3)
            if job_union is not None and total_jobs is not None else None,
            "nonbusy_span_seconds": round(wall - job_union, 3)
            if wall is not None and job_union is not None and wall >= job_union else None,
            "critical_path_lower_bound_seconds": critical_lb,
            "critical_path_exact_seconds": None,
            "retry_job_seconds": round(sum(x["execution_seconds"] for x in retry), 3)
            if retry and all_job_times else (None if not all_job_times else 0),
            "successful_attempt_job_seconds": round(sum(x["execution_seconds"] for x in winning), 3)
            if winning and all_job_times else None,
        },
        "limitations": [
            "GitHub run.updated_at is an observed last-change bound, NOT actual run completion.",
            "True causal-DAG critical path, runner wait and API poll idle time require dedicated phase/dependency evidence.",
            "Runner queue: job.started_at minus original run.created_at is unavailable on reruns.",
            "Step categories are heuristics; a mixed build+validation step cannot be decomposed by job metadata.",
            "Overlap is measured across job execution intervals, NOT a sum of sequential stage costs.",
            "All PASS/BLOCKED release decisions must use independent existing gate verifiers; this report is not a gate.",
        ],
    }


def parse_phase_markers(log):
    """Parse strict nonsecret RHC131_PHASE lines; ignore unmatched incomplete phases."""
    active = {}
    durations = {}
    for line in log.splitlines():
        if "RHC131_PHASE " not in line:
            continue
        if not line.startswith("RHC131_PHASE "):
            line = line[line.index("RHC131_PHASE "):]
        match = MARKER_RE.fullmatch(line.strip())
        if not match or match.group(3) not in PHASE_LABELS:
            raise ValueError("invalid or prohibited phase label")
        kind, stamp, label = match.groups()
        point = parse_timestamp(stamp)
        if kind == "start":
            if label in active:
                raise ValueError("overlapping same phase start")
            active[label] = point
        elif label in active:
            delta = (point - active.pop(label)).total_seconds()
            if delta < 0:
                raise ValueError("negative phase marker")
            durations[label] = round(durations.get(label, 0) + delta, 3)
    return durations


def to_tsv(report):
    header = "run_id\tevent\tsha\tattempt\tconclusion\tclassification\tjob_count\tobserved_window_s\tsum_jobs_s"
    rows = [header]
    for r in report["runs"]:
        known = [j["execution_seconds"] for j in r["jobs"]]
        counted = round(sum(known), 3) if known and all(n is not None for n in known) else None
        values = [r["id"], r["event"], r["head_sha"], r["attempt"],
                  r["conclusion"], r["classification"], r["reported_job_count"],
                  r["observed_run_window_seconds"], counted]
        rows.append("\t".join("NOT_VERIFIED" if val is None else str(val) for val in values))
    return "\n".join(rows) + "\n"


def _api(repo, path):
    # gh uses GH_TOKEN; never print credential, URL response, or raw account data.
    result = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github+json",
                             f"repos/{repo}/{path}"], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False, text=True,
                            timeout=45)
    if result.returncode != 0:
        raise RuntimeError("GitHub read-only API request failed (details withheld)")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GitHub returned invalid evidence JSON") from exc


def collect(repo, identifiers):
    if not REPOSITORY_RE.fullmatch(repo):
        raise ValueError("invalid repository")
    if not identifiers or len(identifiers) > 25:
        raise ValueError("need 1–25 run IDs")
    result = {"runs": [], "jobs_by_run": {}}
    for ident in identifiers:
        if not RUN_ID_RE.fullmatch(ident):
            raise ValueError("invalid run ID")
        run = _api(repo, f"actions/runs/{ident}")
        if run.get("id") != int(ident):
            raise ValueError("run API ID mismatch")
        # Read *all* attempts; a latest-attempt-only jobs API hides retry costs.
        attempt_count = run.get("run_attempt", 1)
        if type(attempt_count) is not int or not (1 <= attempt_count <= 20):
            raise ValueError("unsupported run attempt count")
        combined = []
        seen_ids = set()
        for attempt in range(1, attempt_count + 1):
            page = 1
            while True:
                page_data = _api(repo, f"actions/runs/{ident}/attempts/{attempt}/jobs?per_page=100&page={page}")
                items = page_data.get("jobs")
                if not isinstance(items, list):
                    raise ValueError("missing job array")
                for item in items:
                    job_id = item.get("id")
                    if type(job_id) is not int or job_id < 1:
                        raise ValueError("missing actual GitHub job ID")
                    if job_id in seen_ids:
                        # GitHub's attempt-N listing can repeat unchanged
                        # Windows jobs under a later attempt. Only the
                        # earliest occurrence provides truthful provenance.
                        continue
                    seen_ids.add(job_id)
                    item["run_attempt"] = attempt
                    combined.append(item)
                if len(items) < 100:
                    break
                page += 1
                if page > 10:
                    raise ValueError("too many job pages")
        result["runs"].append(run)
        result["jobs_by_run"][ident] = {"total_count": len(combined), "jobs": combined}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, help="read-only precollected runs/jobs JSON")
    parser.add_argument("--repository", help="OWNER/REPO to retrieve completed Actions runs")
    parser.add_argument("--run-ids", help="comma-separated numeric Actions run IDs")
    parser.add_argument("--expected-sha")
    parser.add_argument("--issue", type=int)
    parser.add_argument("--version")
    for field in ("work_sha", "candidate_sha", "stage_sha", "public_sha"):
        parser.add_argument("--" + field.replace("_", "-"))
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if bool(args.fixture) == bool(args.run_ids):
        parser.error("supply exactly one of --fixture and --run-ids")
    try:
        if args.fixture:
            evidence = json.loads(args.fixture.read_text(encoding="utf-8"))
        else:
            evidence = collect(args.repository or "", args.run_ids.split(","))
        report = build_report(evidence["runs"], evidence["jobs_by_run"],
                              expected_sha=args.expected_sha, issue=args.issue,
                              version=args.version, work_sha=args.work_sha,
                              candidate_sha=args.candidate_sha, stage_sha=args.stage_sha,
                              public_sha=args.public_sha)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "rhc131-timing.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (args.out_dir / "rhc131-timing.tsv").write_text(to_tsv(report), encoding="utf-8")
        m = report["measurement"]
        def fmt(value):
            return str(value) if value is not None else "NOT_VERIFIED"
        summary = (
            f"RHC131_TIMING_NONAUTHORITATIVE schema={SCHEMA_VERSION}\n"
            f"runs={m['included_run_count']} jobs={m['reported_hosted_job_count']} "
            f"supplemental_zero_job_failures={report['zero_job_supplementary_failures']}\n"
            f"observed_wall_s={fmt(m['observed_wall_seconds'])} "
            f"sum_job_s={fmt(m['sum_job_seconds'])} "
            f"job_union_s={fmt(m['job_active_union_seconds'])} "
            f"overlap_s={fmt(m['job_overlap_seconds'])} "
            f"nonbusy_s={fmt(m['nonbusy_span_seconds'])}\n"
            f"critical_path_exact_s=NOT_VERIFIED; "
            f"retry_failed_job_s={fmt(m['retry_job_seconds'])}\n"
            "Release PASS/FAIL is NEVER determined by this report.\n"
        )
        (args.out_dir / "rhc131-summary.txt").write_text(summary, encoding="utf-8")
        print(summary, end="")
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        # Avoid leaking raw API values/paths/secrets from exception messages.
        print("RHC131_TIMING_NOT_VERIFIED: evidence absent, inconsistent or inaccessible", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
