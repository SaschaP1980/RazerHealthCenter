#!/usr/bin/env python3
"""RHC-76 read-only, exact-SHA GitHub workflow reliability contracts.

No publishing, tag creation, device interaction, policy mutation or GitHub writes.
The owner-authorized interim publisher uses this only to reject inconsistent
source/Issue/PR identity and missing real hosted checks before publication.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

SHA = re.compile(r"[0-9a-f]{40}\Z")
TITLE = re.compile(r"^\[RHC-([1-9][0-9]*)\]")
TRAILER = re.compile(r"(?m)^RHC-Issue: ([1-9][0-9]*)\s*$")
REF = re.compile(r"(?m)\b(?:Refs|Closes) #([1-9][0-9]*)\b")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def issue_numbers(message):
    require(isinstance(message, str), "missing commit message")
    found = TRAILER.findall(message)
    require(len(found) == 1, "exactly one RHC-Issue commit trailer required")
    return int(found[0])


def body_issue_number(body):
    require(isinstance(body, str), "source or release PR body missing")
    refs = REF.findall(body)
    require(len(refs) == 1, "exactly one explicit Refs/Closes #N required")
    return int(refs[0])


def resolve_source_provenance(source_sha, pull_requests, work_commit, issue):
    """One authoritative merged source PR; head trailer, Issue and body agree."""
    require(isinstance(source_sha, str) and SHA.fullmatch(source_sha),
            "invalid source SHA")
    require(isinstance(pull_requests, list) and len(pull_requests) == 1,
            "exactly one source PR associated with exact source merge required")
    p = pull_requests[0]
    require(isinstance(p, dict), "invalid source PR")
    number = p.get("number")
    require(type(number) is int and number > 0, "invalid source PR number")
    require(p.get("merged_at") and p.get("merge_commit_sha") == source_sha,
            "source PR must be merged into exact source SHA")
    require((p.get("base") or {}).get("ref") == "main", "source PR base not main")
    head = (p.get("head") or {}).get("sha")
    require(isinstance(head, str) and SHA.fullmatch(head), "invalid source Work head")
    require(isinstance(work_commit, dict) and work_commit.get("sha") == head,
            "source Work commit must match merged PR exact head")
    message = (work_commit.get("commit") or {}).get("message")
    issue_number = issue_numbers(message)
    require(isinstance(message, str)
            and re.findall(r"(?m)^Release-Profile: ([^\r\n]+)$", message)
            == ["version-only"], "version-only source contract missing or ambiguous")
    require(body_issue_number(p.get("body")) == issue_number,
            "source PR must explicitly link its responsible Issue")
    title = TITLE.match(p.get("title") or "")
    require(title and int(title[1]) == issue_number,
            "source PR title must carry correct responsible Issue")
    require(isinstance(issue, dict) and issue.get("number") == issue_number
            and issue.get("state") == "open" and not issue.get("pull_request"),
            "responsible live GitHub Issue missing, not open or mismatched")
    return {"issueNumber": issue_number, "sourcePR": number, "workHead": head}


def verify_release_metadata(issue_number, source_pr, work_head, source_sha,
                            commit_message, pr_title, pr_body):
    """Validate immutable staged commit and *actual* final release PR metadata."""
    require(type(issue_number) is int and issue_number > 0, "invalid responsible Issue")
    require(type(source_pr) is int and source_pr > 0, "invalid source PR")
    require(isinstance(work_head, str) and SHA.fullmatch(work_head),
            "invalid source Work identity")
    require(isinstance(source_sha, str) and SHA.fullmatch(source_sha),
            "invalid source SHA")
    require(issue_numbers(commit_message) == issue_number,
            "stage commit Issue trailer differs from qualified source")
    title = TITLE.match(pr_title or "")
    require(title and int(title[1]) == issue_number,
            "release PR title has wrong Issue")
    require(body_issue_number(pr_body) == issue_number, "release PR body wrong Issue")
    require(re.search(r"\bsource PR #([1-9][0-9]*)\b", pr_body or "")
            and int(re.search(r"\bsource PR #([1-9][0-9]*)\b", pr_body)[1]) == source_pr,
            "release PR not linked to exact source PR")
    require(re.search(r"\bsourceSha ([0-9a-f]{40})\b", pr_body or "")
            and re.search(r"\bsourceSha ([0-9a-f]{40})\b", pr_body)[1] == source_sha,
            "release PR does not reference exact frozen source SHA")
    return True


def verify_hosted_jobs(run, jobs, expected_sha, required_names):
    """A zero-job, action_required or stale event is *never* a PASS."""
    require(isinstance(expected_sha, str) and SHA.fullmatch(expected_sha),
            "invalid staged SHA")
    require(isinstance(run, dict) and run.get("head_sha") == expected_sha
            and run.get("event") == "workflow_dispatch"
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
            and type(run.get("id")) is int and run["id"] > 0,
            "trusted exact-stage workflow_dispatch completed SUCCESS required")
    require(isinstance(required_names, list) and required_names
            and len(required_names) == len(set(required_names)),
            "invalid expected hosted job names")
    require(isinstance(jobs, list) and len(jobs) >= len(required_names),
            "no actual hosted CI jobs or missing required jobs")
    names = [j.get("name") for j in jobs if isinstance(j, dict)]
    require(len(names) == len(jobs), "invalid job entry")
    for name in required_names:
        require(names.count(name) == 1, "missing or duplicate hosted required job: " + name)
    require(all(j.get("conclusion") == "success" and j.get("status") == "completed"
                for j in jobs),
            "hosted jobs include failed/cancelled/skipped/incomplete outcome")
    return run["id"]


def normalize_job_steps(job):
    """Absence is empty *evidence*, not evidence of successful steps."""
    if job is None:
        return []
    require(isinstance(job, dict), "invalid hosted job")
    steps = job.get("steps")
    if steps is None:
        return []
    require(isinstance(steps, list) and all(isinstance(s, dict) for s in steps),
            "invalid hosted job step array")
    return steps


def retry_read_only(callback, *, attempts=3, sleeper=time.sleep):
    """Bounded retries for explicitly read-only requests and retryable transport."""
    require(type(attempts) is int and 1 <= attempts <= 5,
            "invalid bounded read-only retry count")
    for attempt in range(attempts):
        try:
            return callback()
        except (ConnectionError, TimeoutError, OSError):
            if attempt == attempts - 1:
                raise
            sleeper(min(2 ** attempt, 4))
    raise AssertionError("unreachable")


def gh_read(path):
    """Only GitHub REST GET; never HTTP methods changing repository state."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo),
            "missing or unsafe GitHub repository")
    require(path.startswith("repos/" + repo + "/"), "unexpected cross-repository API read")

    def fetch():
        p = subprocess.run(["gh", "api", path], text=True, capture_output=True,
                           check=False, timeout=35)
        if p.returncode:
            diagnostic = (p.stderr or "")[:600]
            if re.search(r"(?:HTTP\s+(?:429|5\d\d)|rate limit|timeout|timed out|"
                         r"RemoteProtocolError|EOF|connection reset|error connecting)",
                         diagnostic, re.I):
                raise ConnectionError("transient GitHub read failed: " + diagnostic)
            raise ValueError("GitHub read denied/failed: " + diagnostic)
        try:
            return json.loads(p.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid GitHub API JSON (not PASS)") from exc
    return retry_read_only(fetch)


def git_message(commit_sha):
    require(SHA.fullmatch(commit_sha), "invalid commit SHA")
    p = subprocess.run(["git", "log", "-1", "--format=%B", commit_sha],
                       text=True, capture_output=True, check=True)
    return p.stdout


def live_source(source_sha, work_sha):
    require(isinstance(work_sha, str) and SHA.fullmatch(work_sha), "invalid Work SHA")
    prs = gh_read("repos/" + os.environ["GITHUB_REPOSITORY"] + "/commits/" + source_sha + "/pulls")
    commit = gh_read("repos/" + os.environ["GITHUB_REPOSITORY"] + "/commits/" + work_sha)
    require(commit.get("sha") == work_sha, "source Work readback wrong SHA")
    n = issue_numbers((commit.get("commit") or {}).get("message"))
    issue = gh_read("repos/" + os.environ["GITHUB_REPOSITORY"] + "/issues/" + str(n))
    return resolve_source_provenance(source_sha, prs, commit, issue)


def main():
    ap = argparse.ArgumentParser(description="RHC-76 nonmutating GitHub provenance and hosted CI checks")
    cmds = ap.add_subparsers(dest="command", required=True)
    source = cmds.add_parser("resolve-source")
    source.add_argument("--source-sha", required=True)
    source.add_argument("--work-sha", required=True)
    stage = cmds.add_parser("verify-stage")
    stage.add_argument("--source-sha", required=True)
    stage.add_argument("--work-sha", required=True)
    stage.add_argument("--stage-sha", required=True)
    stage.add_argument("--pr", type=int, required=True)
    hosted = cmds.add_parser("verify-hosted")
    hosted.add_argument("--sha", required=True)
    hosted.add_argument("--run-json", required=True)
    hosted.add_argument("--jobs-json", required=True)
    hosted.add_argument("--workflow", required=True,
                        choices=["rhc-infrastructure-ci.yml", "rhc-downloads-verify.yml"])
    args = ap.parse_args()
    if args.command == "resolve-source":
        print(json.dumps(live_source(args.source_sha, args.work_sha), sort_keys=True))
    elif args.command == "verify-stage":
        source = live_source(args.source_sha, args.work_sha)
        pr = gh_read("repos/" + os.environ["GITHUB_REPOSITORY"] + "/pulls/" + str(args.pr))
        require(pr.get("number") == args.pr and pr.get("state") == "open"
                and pr.get("merged_at") is None and pr.get("draft") is False
                and (pr.get("head") or {}).get("sha") == args.stage_sha
                and (pr.get("base") or {}).get("sha") == args.source_sha,
                "release PR exact parent/head/status mismatch")
        verify_release_metadata(source["issueNumber"], source["sourcePR"],
                                source["workHead"], args.source_sha,
                                git_message(args.stage_sha), pr.get("title"), pr.get("body"))
        print("RHC76_RELEASE_METADATA=PASS sourcePR=" + str(source["sourcePR"])
              + " issue=" + str(source["issueNumber"]) + " stage=" + args.stage_sha)
    elif args.command == "verify-hosted":
        with open(args.run_json, encoding="utf-8") as f:
            run = json.load(f)
        with open(args.jobs_json, encoding="utf-8") as f:
            jobs = json.load(f).get("jobs")
        expected = (["rhc/infra/linux", "rhc/infra/windows"]
                    if args.workflow == "rhc-infrastructure-ci.yml"
                    else ["Validate ZIP manifest and unmodified release history"])
        rid = verify_hosted_jobs(run, jobs, args.sha, expected)
        print("RHC76_HOSTED_EXACT_SHA=PASS run=" + str(rid) + " workflow=" + args.workflow)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.SubprocessError, OSError, KeyError) as exc:
        print("RHC76_WORKFLOW_EVIDENCE=BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(1)
