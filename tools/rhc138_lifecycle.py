#!/usr/bin/env python3
"""RHC-138: read-only, nonauthoritative owner-to-close release timing.

Timings are OBSERVED spans. This utility never guesses chat timestamps,
GitHub runner idle time, release acceptance, or a causal DAG critical path.
It uses only allowlisted event names/fields. GitHub reads are optional and GET
only; no workflow dispatch, publish, or issue mutation is possible.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

VERSION = 1
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
KNOWN = frozenset({
    "owner_authorized", "issue_created", "bootstrap_comment_saved",
    "bootstrap_comment_readback", "work_branch_created",
    "first_work_commit", "first_work_ci_created", "work_attempt_failed",
    "work_retry_succeeded", "development_completion_green",
    "candidate_started", "candidate_green", "publisher_started",
    "required_downloads_gate", "combined_pr_created", "combined_pr_merged",
    "publisher_green", "public_https_green", "native_windows_green",
    "rhc102_aggregate_green", "rolling_comment_final_readback",
    "issue_closed", "issue_reopened", "final_user_notification",
    "supplemental_pr_zero_job", "work_ci_completed",
})
TRUSTED = frozenset({
    "github", "github_issue", "github_timeline", "github_actions",
    "github_pull_request", "attested_user_message", "attested_outgoing_message",
})
OWNER_TRUST = {"owner_authorized": "attested_user_message",
               "final_user_notification": "attested_outgoing_message"}
SPANS = {
    "owner_request_to_final_message": ("owner_authorized", "final_user_notification"),
    "owner_request_to_issue": ("owner_authorized", "issue_created"),
    "issue_to_first_work_ci": ("issue_created", "first_work_ci_created"),
    "work_ci_to_development_completion": ("first_work_ci_created", "development_completion_green"),
    "candidate_window": ("candidate_started", "candidate_green"),
    "publisher_window": ("publisher_started", "publisher_green"),
    "publisher_to_issue_close": ("publisher_green", "issue_closed"),
    "issue_to_issue_close": ("issue_created", "issue_closed"),
    "publisher_to_final_message": ("publisher_green", "final_user_notification"),
    "public_verification_to_issue_close": ("rhc102_aggregate_green", "issue_closed"),
}


def parse_time(value):
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp absent or not an ISO8601 string")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError("clock missing timezone")
    return d.astimezone(timezone.utc)


def _diff(a, b):
    if a is None or b is None:
        return None
    diff = (parse_time(b) - parse_time(a)).total_seconds()
    if diff < 0:
        raise ValueError("negative observed chronological interval")
    return round(diff, 3)


def _allowed(e, issue, sha):
    if not isinstance(e, dict) or e.get("event") not in KNOWN:
        return False
    if e.get("issue") != issue:
        return False
    src = e.get("source")
    if src not in TRUSTED:
        return False
    if e["event"] in OWNER_TRUST and src != OWNER_TRUST[e["event"]]:
        return False
    if sha is not None and e.get("event") not in (
            "issue_created", "issue_closed", "issue_reopened",
            "owner_authorized", "final_user_notification"):
        if e.get("sha") != sha:
            return False
    if e.get("sha") is not None and not SHA.fullmatch(str(e.get("sha"))):
        return False
    if not isinstance(e.get("evidence_id"), str) or not e["evidence_id"]:
        return False
    if e.get("status") not in ("success", "failure", "pending", "skipped",
                               "cancelled", "not_verified"):
        return False
    parse_time(e.get("at"))
    return True


def build_report(events, *, issue, expected_sha=None):
    if type(issue) is not int or issue < 1:
        raise ValueError("issue number invalid")
    if expected_sha is not None and not SHA.fullmatch(expected_sha):
        raise ValueError("invalid frozen SHA")
    if not isinstance(events, list) or len(events) > 500:
        raise ValueError("too many events or invalid event container")
    valid, excluded, seen, untrusted = [], [], {}, []
    for i, raw in enumerate(events):
        if not isinstance(raw, dict):
            raise ValueError("malformed event")
        if raw.get("source") not in TRUSTED or (
                raw.get("event") in OWNER_TRUST and
                raw.get("source") != OWNER_TRUST[raw.get("event")]):
            untrusted.append({"position": i, "event": raw.get("event")})
            continue
        if not _allowed(raw, issue, expected_sha):
            excluded.append({"position": i, "reason": "ISSUE_SHA_OR_SCHEMA_MISMATCH"})
            continue
        identity = (raw["event"], raw["source"], raw["evidence_id"])
        stamp = parse_time(raw["at"]).isoformat().replace("+00:00", "Z")
        if identity in seen:
            if seen[identity] != (stamp, raw.get("status")):
                raise ValueError("conflicting immutable event identity")
            continue
        seen[identity] = (stamp, raw.get("status"))
        item = {
            "event": raw["event"], "at": stamp, "source": raw["source"],
            "evidence_id": raw["evidence_id"], "issue": issue,
            "sha": raw.get("sha") if raw.get("sha") and SHA.fullmatch(raw["sha"]) else None,
            "status": raw["status"], "attempt": raw.get("attempt")
            if type(raw.get("attempt")) is int else None,
            "job_count": raw.get("job_count")
            if type(raw.get("job_count")) is int and raw["job_count"] >= 0 else None,
        }
        valid.append(item)
    valid.sort(key=lambda v: (v["at"], v["event"]))
    grouped = {}
    for item in valid:
        grouped.setdefault(item["event"], []).append(item)
    def selected(name):
        candidates = grouped.get(name, [])
        if name == "issue_closed":
            return candidates[-1] if candidates else None
        return candidates[0] if candidates else None
    intervals = {}
    for name, (a, b) in SPANS.items():
        start, end = selected(a), selected(b)
        # Never count a failed workflow as a successful phase boundary.
        if start and start["status"] != "success":
            start = None
        if end and end["status"] != "success":
            end = None
        intervals[name] = _diff(start["at"], end["at"]) if start and end else None
    observations = []
    started, finished = selected("candidate_started"), selected("candidate_green")
    pub = selected("publisher_started")
    if started and pub and finished and (parse_time(started["at"])
                                          <= parse_time(pub["at"])
                                          < parse_time(finished["at"])):
        observations.append("candidate_publisher_overlap")
    if any(x["event"] == "required_downloads_gate" and
           (x["job_count"] is None or x["job_count"] < 1)
           for x in valid):
        observations.append("REQUIRED_JOB_COUNT_UNVERIFIED")
    closes = grouped.get("issue_closed", [])
    reopen = grouped.get("issue_reopened", [])
    premature = sum(1 for item in closes if
                    any(parse_time(x["at"]) > parse_time(item["at"])
                        for x in reopen))
    retries = [x for x in valid if x["event"] == "work_attempt_failed"
               or x["status"] == "failure"]
    return {
        "schema_version": VERSION, "scope": "READ_ONLY_NONAUTHORITATIVE",
        "issue": issue, "expected_sha": expected_sha,
        "events": valid, "excluded_events": excluded,
        "untrusted_events": untrusted, "retries": retries,
        "interval_seconds": intervals, "observations": observations,
        "measurement": {
            "unique_event_count": len(valid),
            "owner_span_verification": "VERIFIED"
            if intervals["owner_request_to_final_message"] is not None
            else "NOT_VERIFIED",
            "retry_failure_count": sum(x["status"] == "failure" for x in retries),
            "premature_close_count": premature,
            "supplemental_zero_job_failures": sum(
                x["event"] == "supplemental_pr_zero_job"
                and x["status"] == "failure" and x["job_count"] == 0
                for x in valid),
            "administrative_causal_time_seconds": None,
            "exact_causal_critical_path_seconds": None,
        },
        "limitations": [
            "Observed GitHub event timestamps and intervals do not prove operator effort.",
            "Chat authorization and outgoing message require individually attested time sources.",
            "Release/Candidate phases may overlap; observed intervals cannot be added as independent work.",
            "Job queue, causal DAG and GitHub polling delay need separately linked step/run evidence.",
            "This report does not grant or prove publication, signing, RHC102 or safety-gate PASS.",
        ],
    }


def to_tsv(report):
    rows = ["event\tat_utc\tstatus\tsource\tevidence_id\tattempt"]
    for x in report["events"]:
        row = [x["event"], x["at"], x["status"], x["source"],
               x["evidence_id"], str(x["attempt"]) if x["attempt"] else "NOT_VERIFIED"]
        rows.append("\t".join(row))
    return "\n".join(rows) + "\n"


def _api(repository, path):
    # Strict read-only GET with no print of tokens/API output.
    if not REPO.fullmatch(repository):
        raise ValueError("invalid repository")
    if not re.fullmatch(r"[A-Za-z0-9/?=&_.-]+", path):
        raise ValueError("invalid GitHub API subpath")
    ret = subprocess.run(["gh", "api", "-X", "GET",
                          f"repos/{repository}/{path}"],
                         capture_output=True, text=True, timeout=45)
    if ret.returncode != 0:
        raise ValueError("GitHub GET evidence unavailable")
    return json.loads(ret.stdout)


def collect_issue(repository, issue_number, run_map=None):
    """Read real Issue, PR-independent timeline, and explicitly named runs.

    run_map: e.g. {'first_work_ci_created': 3807..., 'publisher_green': ...}.
    Never infer release success from run status alone; still reports events
    as observed status only. No final chat times can be read via gh.
    """
    i = _api(repository, f"issues/{issue_number}")
    if i.get("number") != issue_number:
        raise ValueError("Issue identity mismatch")
    a = []
    def add(name, stamp, evidence, *, status="success", sha=None):
        if stamp:
            a.append({"event": name, "at": stamp, "issue": issue_number,
                      "sha": sha, "source": "github", "evidence_id": evidence,
                      "status": status})
    add("issue_created", i.get("created_at"), f"issue:{issue_number}")
    page = 1
    while page <= 10:
        history = _api(repository, f"issues/{issue_number}/events?per_page=100&page={page}")
        if not isinstance(history, list):
            raise ValueError("invalid GitHub Issue event page")
        for x in history:
            if x.get("event") in ("closed", "reopened"):
                add("issue_closed" if x["event"] == "closed" else "issue_reopened",
                    x.get("created_at"), f"issue_event:{x.get('id')}")
        if len(history) < 100:
            break
        page += 1
    if run_map:
        for name, run_id in run_map.items():
            if name not in KNOWN or type(run_id) is not int or run_id < 1:
                raise ValueError("invalid run mapping")
            run = _api(repository, f"actions/runs/{run_id}")
            if run.get("id") != run_id:
                raise ValueError("Run identity mismatch")
            # Observed 'updated_at' is a bound, not true completion instant.
            stamp = run.get("created_at") if name.endswith("_started") or name.endswith("_created") else run.get("updated_at")
            status = "success" if run.get("status") == "completed" and run.get("conclusion") == "success" else (
                "failure" if run.get("conclusion") == "failure" else "not_verified")
            add(name, stamp, f"actions_run:{run_id}", status=status,
                sha=run.get("head_sha"))
    return a


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixture", type=Path)
    ap.add_argument("--repository")
    ap.add_argument("--issue", type=int)
    ap.add_argument("--run-map", type=Path,
                    help="optional JSON mapping event names to genuine GitHub run IDs")
    ap.add_argument("--expected-sha")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    if bool(args.fixture) == bool(args.repository):
        ap.error("provide exactly one of --fixture or --repository")
    try:
        if args.fixture:
            data = json.loads(args.fixture.read_text(encoding="utf-8"))
            events = data["events"]
            issue = args.issue or data["issue"]
        else:
            if not args.issue:
                raise ValueError("issue required for GitHub")
            mapping = json.loads(args.run_map.read_text(encoding="utf-8")) if args.run_map else {}
            issue = args.issue
            events = collect_issue(args.repository, issue, mapping)
        report = build_report(events, issue=issue, expected_sha=args.expected_sha)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "rhc138-lifecycle.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (args.out_dir / "rhc138-lifecycle.tsv").write_text(to_tsv(report), encoding="utf-8")
        fmt = lambda v: str(v) if v is not None else "NOT_VERIFIED"
        lines = ["RHC138_E2E_NONAUTHORITATIVE",
                 f"issue={issue} events={report['measurement']['unique_event_count']}",
                 f"issue_to_close_s={fmt(report['interval_seconds']['issue_to_issue_close'])}",
                 f"owner_request_to_final_message_s={fmt(report['interval_seconds']['owner_request_to_final_message'])}",
                 f"publisher_to_issue_close_s={fmt(report['interval_seconds']['publisher_to_issue_close'])}",
                 "exact_causal_critical_path_s=NOT_VERIFIED",
                 "No release-gate authorization follows from timing output."]
        (args.out_dir / "rhc138-summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 0
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError,
            subprocess.TimeoutExpired):
        print("RHC138_EVIDENCE_NOT_VERIFIED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
