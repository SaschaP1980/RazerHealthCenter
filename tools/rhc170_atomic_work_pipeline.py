#!/usr/bin/env python3
"""RHC-170: one bounded, parallel-read, fail-closed RHC132 Work-commit driver.

Default PLAN_ONLY is read-only. --apply makes one local atomic version-only
commit; --push additionally moves exactly work/RHC-N with a Git lease.
No product release, workflow dispatch, Issue mutation or fake CI-green proof.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

import rhc132_work_preflight as hotfix

SHA = re.compile(r"^[0-9a-f]{40}$")
TARGET = re.compile(r"(?m)^Owner-approved version-only target: (\d+\.\d+\.\d+\.\d+)$")
INFRA = "RHC Infrastructure Qualification (nonpublishing)"
DEVELOPMENT = "RHC Development Completion (exact SHA gate)"


def require(condition, reason):
    if not condition:
        raise ValueError("RHC170_WORK_BLOCKED: " + reason)


def observed():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z")


def _timed(name, action):
    start = observed()
    before = time.monotonic()
    result = action()
    return name, result, dict(event=name, observed_start_utc=start,
                              observed_end_utc=observed(),
                              elapsed_ms=round((time.monotonic() - before) * 1000, 3),
                              time_authority="CLIENT_OBSERVED_NOT_GITHUB_SERVER")


def parallel_snapshot(gateway, root, number, comment_id, *, with_sources=True):
    """Parallel GET/read; one immutable pinned-SHA PLAN validates all inputs.

    Requests are independently observable, NOT an atomic remote GitHub snapshot.
    A second independent authority read is required before any mutation.
    """
    jobs = {
        "issue": lambda: gateway.get_issue(number),
        "comment": lambda: gateway.get_comment(comment_id),
        "main": gateway.get_main,
        "work": lambda: gateway.get_work(number),
    }
    if with_sources:
        jobs["model"] = lambda: (root / "model.go").read_text(encoding="utf-8")
        jobs["changelog"] = lambda: (root / "CHANGELOG.md").read_text(encoding="utf-8")
    result, events = {}, []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {pool.submit(_timed, name, fn): name for name, fn in jobs.items()}
        for f in as_completed(futures):
            name, value, event = f.result()
            result[name] = value
            events.append(event)
    return result, sorted(events, key=lambda x: x["event"])


def _same_authority(earlier, current, expected_main):
    # These exact snapshots are protected against concurrent Issue/comment
    # editing. GitHub GET requests are not a transactional snapshot.
    for key in ("issue", "comment"):
        require(current[key] == earlier[key],
                "Issue or Rolling Comment changed between readbacks: " + key)
    require(current["main"] == expected_main and
            current["work"] == expected_main,
            "fresh main or Work-ref SHA differs from immutable lease")


def _version_authorized(issue, target):
    body = issue.get("body")
    require(isinstance(body, str),
            "owner-approved target cannot be verified from saved Issue")
    matches = TARGET.findall(body)
    require(matches == [target],
            "exact owner-approved new version must be recorded ONCE in the "
            "canonical Issue body, in addition to explicit CLI authorization")


def _check_command(p):
    require(p.returncode == 0,
            "Git push blocked; no retry (independent GET reconciliation required)")
    return p.stdout


def push_with_lease(root, branch, expected_sha, new_sha):
    """One and only one local Git push with an exact expected remote SHA.

    force-with-lease protects against races. New commit ancestry is already
    independently certified by RHC132 atomic_local_commit; this operation
    is a fast-forward from exactly the approved former ref, NOT generic force.
    """
    require(re.fullmatch(r"work/RHC-[1-9][0-9]*", branch) and
            SHA.fullmatch(expected_sha) and SHA.fullmatch(new_sha) and
            expected_sha != new_sha, "unsafe branch/commit push parameters")
    args = ["git", "-C", str(Path(root).resolve()), "push", "--porcelain",
            "--force-with-lease=refs/heads/{}:{}".format(branch, expected_sha),
            "origin", "HEAD:refs/heads/" + branch]
    result = subprocess.run(args, text=True, capture_output=True,
                            timeout=60, check=False)
    return _check_command(result)


def _ledger(evidence, name, **data):
    evidence.append(dict(event=name, observed_utc=observed(),
                         time_authority="CLIENT_OBSERVED_NOT_GITHUB_SERVER",
                         **data))


def run(*, gateway, root, number, comment_id, pinned_main_sha,
        branch_created_at, day, apply=False, push=False,
        owner_authorized_new_version=False, commit_func=None, push_func=None):
    """One orchestrated RHC132-backed commit; no direct release/Issue writes.

    All four live authorities and both source files are fetched in parallel;
    a second full authority batch checks drift before any mutation. The
    existing RHC132 atomic_local_commit enforces git HEAD/clean tree/diff.
    """
    require(type(number) is int and number > 0 and
            type(comment_id) is int and comment_id > 0 and
            isinstance(pinned_main_sha, str) and SHA.fullmatch(pinned_main_sha),
            "invalid Issue/comment/main identity")
    require(isinstance(day, date) and isinstance(branch_created_at, str),
            "missing date or true branch creation observation")
    require(not push or apply, "--push requires --apply")
    require(not apply or owner_authorized_new_version,
            "mutations require separate owner authorization, not mere Issue planning")
    root = Path(root).resolve()
    events = []
    _ledger(events, "initial_observed_start")
    snapshot, parallel_events = parallel_snapshot(gateway, root, number, comment_id)
    events.extend(parallel_events)
    _ledger(events, "parallel_snapshot_finished")
    info = hotfix.plan(
        saved_issue=snapshot["issue"], comment=snapshot["comment"],
        number=number, base_main_sha=pinned_main_sha,
        readback_main_sha=snapshot["main"], work_head_sha=snapshot["work"],
        branch_created_at=branch_created_at,
        model=snapshot["model"], changelog=snapshot["changelog"], day=day)
    require(info["allowed_paths"] == ["CHANGELOG.md", "model.go"] and
            info["branch"] == "work/RHC-{}".format(number),
            "RHC132 unexpected source paths or branch")
    _ledger(events, "rhc132_full_plan_verified",
            from_version=info["from_version"], to_version=info["to_version"],
            original_main_sha=pinned_main_sha)
    if not apply:
        return dict(status="PLAN_ONLY", issue=number, main_sha=pinned_main_sha,
                    from_version=info["from_version"],
                    to_version=info["to_version"],
                    allowed_paths=info["allowed_paths"], mutations=0,
                    timings=events,
                    actual_work_ci_created_at="NOT_OBSERVED")
    _version_authorized(snapshot["issue"], info["to_version"])
    checked, seen = parallel_snapshot(gateway, root, number, comment_id,
                                      with_sources=False)
    events.extend(seen)
    _same_authority(snapshot, checked, pinned_main_sha)
    _ledger(events, "precommit_authority_recheck_verified")
    commit = commit_func or hotfix.atomic_local_commit
    # The existing RHC132 locally validates clean checkout, exact parent,
    # exactly two staged paths, and checks the final commit's ancestry/diff.
    new_sha = commit(root, info)
    require(isinstance(new_sha, str) and SHA.fullmatch(new_sha) and
            new_sha != pinned_main_sha, "atomic commit did not return new SHA")
    _ledger(events, "local_atomic_commit_verified", new_sha=new_sha)
    if not push:
        return dict(status="LOCAL_COMMIT_VERIFIED", issue=number,
                    main_sha=pinned_main_sha, work_sha=new_sha,
                    to_version=info["to_version"], mutations=1,
                    timings=events, actual_work_ci_created_at="NOT_OBSERVED")
    latest, seen = parallel_snapshot(gateway, root, number, comment_id,
                                     with_sources=False)
    events.extend(seen)
    _same_authority(snapshot, latest, pinned_main_sha)
    _ledger(events, "prepush_exact_ref_lease_verified")
    push_one = push_func or push_with_lease
    uncertain = False
    try:
        push_one(root, info["branch"], pinned_main_sha, new_sha)
    except Exception:
        uncertain = True
        # NEVER retry an uncertain push. Independently GET the remote head.
        _ledger(events, "push_response_uncertain_reconcile_only")
    remote, seen = parallel_snapshot(gateway, root, number, comment_id,
                                     with_sources=False)
    events.extend(seen)
    require(remote["main"] == pinned_main_sha and
            remote["work"] == new_sha,
            "push did not yield the exact intended remote head; no retry")
    for key in ("issue", "comment"):
        require(remote[key] == snapshot[key],
                "authority altered during push: " + key)
    _ledger(events, "remote_work_sha_independently_verified",
            work_sha=new_sha, response_uncertain=uncertain)
    return dict(status="WORK_PUSH_VERIFIED", issue=number,
                main_sha=pinned_main_sha, work_sha=new_sha,
                to_version=info["to_version"], allowed_paths=info["allowed_paths"],
                mutations=2, push_response_uncertain=uncertain,
                timings=events, actual_work_ci_created_at="NOT_OBSERVED")


def verify_ci_created(gateway, exact_work_sha, push_observed_utc):
    """Read-only evidence. Never convert creation into a CI success/green."""
    require(isinstance(exact_work_sha, str) and SHA.fullmatch(exact_work_sha),
            "invalid expected CI head")
    start = hotfix.clock(push_observed_utc)
    rows = gateway.list_work_runs(exact_work_sha)
    require(isinstance(rows, list) and len(rows) <= 100,
            "missing/ambiguous bounded GH Actions evidence")
    wanted = (INFRA, DEVELOPMENT)
    selected = {}
    for row in rows:
        require(isinstance(row, dict), "malformed Actions run entry")
        if row.get("name") not in wanted:
            continue  # unrelated RHC5 push run; never count as a Work gate
        require(type(row.get("id")) is int and
                row.get("head_sha") == exact_work_sha and
                row.get("event") == "push",
                "foreign, duplicate, or unverifiable Actions run")
        require(row.get("name") in wanted, "unexpected job in exact-work evidence")
        require(row.get("name") not in selected,
                "duplicated Work-CI run for same exact head")
        created = hotfix.clock(row.get("created_at"))
        require(created >= start - timedelta(seconds=5),
                "old workflow cannot attest this new push")
        status, conclusion = row.get("status"), row.get("conclusion")
        require(status in ("queued", "in_progress", "completed") and
                (status == "completed" or conclusion is None) and
                (status != "completed" or conclusion in
                 ("success", "failure", "cancelled", "skipped", "timed_out")),
                "inconsistent workflow status and conclusion")
        selected[row["name"]] = row
    require(set(selected) == set(wanted),
            "both independent Work-CI creation events required")
    return dict(status="WORK_CI_CREATED_NOT_GREEN",
                source_sha=exact_work_sha,
                runs=[selected[name]["id"] for name in wanted],
                github_created_at={name: selected[name]["created_at"]
                                   for name in wanted},
                checked_at_utc=observed(),
                green_verified=False)


class GithubReader:
    """Existing read-only gh CLI gateway; no own source/branch writers."""

    def __init__(self, repository):
        require(repository == "SaschaP1980/RazerHealthCenter",
                "GitHub repository not permitted")
        self.repository = repository

    def api(self, endpoint):
        return hotfix._api(self.repository, endpoint)

    def get_issue(self, number):
        return self.api("issues/{}".format(number))

    def get_comment(self, ident):
        return self.api("issues/comments/{}".format(ident))

    def get_main(self):
        return self.api("git/ref/heads/main")["object"]["sha"]

    def get_work(self, number):
        return self.api("git/ref/heads/work/RHC-{}".format(number))["object"]["sha"]

    def list_work_runs(self, sha):
        rows = self.api("actions/runs?head_sha={}&per_page=100".format(sha))
        return rows["workflow_runs"]


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--comment-id", type=int, required=True)
    parser.add_argument("--base-main-sha", required=True)
    parser.add_argument("--branch-created-at", required=True,
                        help="honest client observation; never Git refs created_at")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--day", help="UTC YYYY-MM-DD (default actual UTC today)")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--owner-authorized-new-version", action="store_true",
                        help="also requires Issue's explicit exact target line")
    parser.add_argument("--observe-ci-for-sha",
                        help="read-only exact-work CI creation evidence; not green")
    parser.add_argument("--push-observed-utc",
                        help="actual observed UTC with --observe-ci-for-sha")
    args = parser.parse_args(argv)
    try:
        gateway = GithubReader(args.repository)
        if args.observe_ci_for_sha:
            require(not args.apply and not args.push and args.push_observed_utc,
                    "CI evidence mode is read-only and needs observed push UTC")
            result = verify_ci_created(gateway, args.observe_ci_for_sha,
                                       args.push_observed_utc)
        else:
            require(not args.push_observed_utc,
                    "--push-observed-utc only with CI evidence mode")
            result = run(
                gateway=gateway, root=args.root, number=args.issue,
                comment_id=args.comment_id, pinned_main_sha=args.base_main_sha,
                branch_created_at=args.branch_created_at,
                day=date.fromisoformat(args.day) if args.day
                else datetime.now(timezone.utc).date(),
                apply=args.apply, push=args.push,
                owner_authorized_new_version=args.owner_authorized_new_version)
        print("RHC170_ATOMIC_WORK=" + json.dumps(result, sort_keys=True), flush=True)
        return 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError,
            subprocess.TimeoutExpired):
        print("RHC170_WORK_BLOCKED_NOT_VERIFIED — no unsafe retry or release",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli())
