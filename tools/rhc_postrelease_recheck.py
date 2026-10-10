#!/usr/bin/env python3
"""RHC-110: fail-closed autonomous read-only RHC-102 postrelease recheck.

The sole remote mutation permitted here is POST workflow_dispatch on the existing
independent verifier. No product release, tag, pull request or download writes.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import rhc102_postrelease_provenance as provenance

SHA = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\Z")
WORK = re.compile(r"work/RHC-([1-9][0-9]*)\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
CLEANUP = "RHC Verified Merged-Branch Cleanup"
INFRA = "RHC Infrastructure Qualification (nonpublishing)"
VERIFY = "rhc-postrelease-verification.yml"
JOB_NAMES = (
    "Independently GET HTTPS public ZIP and exact release graph",
    "Independently reverify released EXE and native PS5.1 Razer safety",
    "Conclude only after independent HTTPS AND native Windows success",
)
INFRA_JOBS = ("rhc/infra/linux", "rhc/infra/windows", "rhc/infra/artifact-node24")
ALLOWED = frozenset((
    "tools/rhc102_postrelease_provenance.py",
    "tools/rhc_remote_binary_verify.py",
    "tools/rhc_postrelease_recheck.py",
    "tests/test_rhc102_release_contracts.py",
    "tests/test_rhc102_wiring_contracts.py",
    "tests/test_rhc_remote_binary_verify_contracts.py",
    "tests/test_rhc_110_postrelease_recheck_contracts.py",
    ".github/workflows/rhc-postrelease-verification.yml",
    ".github/workflows/rhc-postrelease-recheck.yml",
    "docs/RHC_CICD_ARCHITECTURE.md",
    "docs/DEVELOPMENT_GUIDELINES.md",
    "docs/GITHUB_HOWTO.md",
    "docs/RELEASE_PROCESS.md",
    "docs/REUSABLE_INTERIM_RELEASE_CONTRACT.md",
))
ACTIVE_PATHS = frozenset(p for p in ALLOWED if p.startswith((
    "tools/", "tests/", ".github/workflows/")))
CLEANUP_JOB = "cleanup-merged"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_jobs(rows, expected, successful=True):
    require(isinstance(rows, list) and len(rows) == len(expected), "incomplete hosted jobs")
    for name in expected:
        hits = [x for x in rows if isinstance(x, dict) and x.get("name") == name]
        require(len(hits) == 1, "missing/duplicate hosted job: " + name)
        job = hits[0]
        require(job.get("status") == "completed", "unfinished hosted job: " + name)
        if successful:
            require(job.get("conclusion") == "success", "hosted job not successful: " + name)
        else:
            require(job.get("conclusion") in ("success", "failure"),
                    "prior failed run has skipped/cancelled job: " + name)
    if not successful:
        require(any(x["conclusion"] == "failure" for x in rows),
                "not an actual historical failed job")
    return True


def verify_postrelease_jobs(rows):
    return verify_jobs(rows, JOB_NAMES)


def validate_plan(x):
    """Pure reviewable security boundary; all live snapshots are read-only."""
    repo = x.get("repository", "")
    require(isinstance(repo, str) and REPOSITORY.fullmatch(repo),
            "untrusted repository identity")
    main = x.get("liveMainSha")
    require(isinstance(main, str) and SHA.fullmatch(main) and
            x.get("checkoutSha") == main, "main/ref/checkout changed")

    release = x["release"]
    latest, history = release["latest"], release["historyHead"]
    version = release["version"]
    source = release["sourceSha"]
    require(bool(VERSION.fullmatch(version)) and SHA.fullmatch(source) and
            release.get("verified") is True, "unverified public release")
    require(latest == history and latest["version"] == version and
            latest["sourceSha"] == source and latest["tag"] == "v" + version and
            latest["file"] == "RazerHealthCenter-Portable-v" + version + ".zip",
            "public catalog identity mismatch")
    require(release["tagSha"] == source and latest["sha256"] ==
            release["archiveSha256"] and latest["size"] == release["archiveSize"] and
            bool(re.fullmatch(r"[0-9a-f]{64}", latest["sha256"])) and
            isinstance(latest["size"], int) and latest["size"] > 0,
            "ZIP/tag/archive integrity changed")
    require(release["mainSha"] == main and SHA.fullmatch(release["mergeSha"]) and
            release["mergeSha"] != main, "missing postrelease corrective commit")
    changed = release["sinceReleasePaths"]
    require(isinstance(changed, list) and bool(changed) and
            len(changed) == len(set(changed)) and set(changed) <= ALLOWED and
            bool(set(changed) & ACTIVE_PATHS),
            "postrelease diff touches unapproved product/publisher/download paths")

    release_pr = x["releasePr"]
    require(release_pr.get("merged") is True and release_pr.get("state") == "closed"
            and isinstance(release_pr.get("number"), int) and release_pr["number"] > 0
            and release_pr.get("mergeSha") == release["mergeSha"]
            and SHA.fullmatch(release_pr.get("stagedSha", ""))
            and release_pr.get("baseRef") == "main"
            and release_pr.get("headRef") == "release/v" + version,
            "immutable combined release PR unverified")

    pr = x["correctionPr"]
    head = pr.get("headSha", "")
    wm = WORK.fullmatch(pr.get("headRef", ""))
    require(wm is not None and SHA.fullmatch(head), "correction not from Work branch")
    issue = int(wm.group(1))
    require(isinstance(pr.get("number"), int) and pr["number"] > 0
            and pr["number"] != release_pr["number"]
            and pr.get("issue") == issue and pr.get("issueExists") is True
            and pr.get("merged") is True and pr.get("state") == "closed"
            and pr.get("mergeSha") == main and
            SHA.fullmatch(pr.get("baseSha", ""))
            and pr["mergeParents"] == [pr["baseSha"], head] and
            pr.get("treeMatchesHead") is True and
            pr.get("headRepo") == repo and pr.get("baseRef") == "main",
            "untrusted/unmerged correction PR lineage")
    require(bool(re.search(r"(?m)\b(?:Refs|Closes|Fixes) #" + str(issue) + r"\b",
                           pr.get("body") or "")), "PR missing responsible Issue")
    files = pr.get("files")
    require(isinstance(files, list) and bool(files) and
            len(files) == len(set(files)) and set(files) <= ALLOWED and
            bool(set(files) & ACTIVE_PATHS), "PR contains an unrelated or docs-only change")
    reviews = pr.get("reviews")
    owner = repo.partition("/")[0]
    require(isinstance(reviews, list) and any(
        review.get("state") in ("COMMENTED", "APPROVED") and
        review.get("commit_id") == head and
        (review.get("login") == owner or review.get("state") == "APPROVED")
        for review in reviews if isinstance(review, dict)),
        "missing exact-head owner review/approval")

    qualifying = x["qualification"]
    require(qualifying.get("name") == INFRA and
            qualifying.get("event") == "push" and
            qualifying.get("head_sha") == head and
            qualifying.get("head_branch") == pr["headRef"] and
            qualifying.get("status") == "completed" and
            qualifying.get("conclusion") == "success" and
            isinstance(qualifying.get("id"), int) and qualifying["id"] > 0,
            "missing exact-head trusted hosted qualification")
    verify_jobs(qualifying.get("jobs"), INFRA_JOBS)

    trigger = x["triggerRun"]
    require(x.get("event") in ("workflow_run", "schedule", "workflow_dispatch"),
            "invalid trusted trigger")
    require(trigger.get("name") == CLEANUP and
            trigger.get("event") == "pull_request" and
            trigger.get("status") == "completed" and
            trigger.get("conclusion") == "success" and
            trigger.get("head_sha") == head and
            trigger.get("head_branch") == pr["headRef"],
            "cleanup provenance not exact verified correction")
    verify_jobs(trigger.get("jobs"), (CLEANUP_JOB,))

    prior = x["priorPostrelease"]
    require(prior.get("event") == "workflow_dispatch" and
            prior.get("head_sha") == release["mergeSha"] and
            prior.get("status") == "completed" and
            prior.get("conclusion") == "failure" and
            prior.get("display_title") ==
            "RHC POSTRELEASE v" + version + " main:" + release["mergeSha"] and
            isinstance(prior.get("id"), int) and prior["id"] > 0,
            "not the real original exact-release failed postrelease run")
    verify_jobs(prior.get("jobs"), JOB_NAMES, successful=False)
    require(x.get("existingCurrentRuns") == [], "already attempted on this main SHA")
    require(x.get("publisherActive") is False, "publication currently active")
    return dict(status="ELIGIBLE", expected_main_sha=main,
                expected_source_sha=source, version=version,
                expected_release_pr=str(release_pr["number"]),
                original_failed_run=prior["id"], corrective_pr=pr["number"],
                qualifying_run=qualifying["id"], correction_sha=head)


def command(args, *, input_data=None, timeout=90):
    proc = subprocess.run(args, input=input_data, text=True, capture_output=True,
                          timeout=timeout, check=False)
    require(proc.returncode == 0, "command failed: " + " ".join(args[:5]) +
            " " + (proc.stderr or "")[-240:])
    return proc.stdout


def git(*args):
    return command(["git", *args], timeout=90).strip()


def api(path, *, method="GET", data=None):
    require(os.environ.get("GH_TOKEN"), "missing GitHub token")
    cmd = ["gh", "api", "--method", method, path]
    if data is not None:
        require(method == "POST" and path.endswith("/dispatches"),
                "only RHC-102 verifier workflow dispatch mutation permitted")
        cmd += ["--input", "-"]
    content = command(cmd, input_data=json.dumps(data) if data else None)
    return json.loads(content) if content.strip() else {}


def repo_route(suffix):
    return "repos/" + os.environ["GITHUB_REPOSITORY"] + "/" + suffix


def get_jobs(run_id):
    x = api(repo_route("actions/runs/" + str(run_id) + "/jobs?per_page=100"))
    require(x.get("total_count", 0) <= 100, "hosted job pagination ambiguous")
    return [{k: row.get(k) for k in ("name", "status", "conclusion", "id")}
            for row in x["jobs"]]


def associated_pr(commit):
    rows = api(repo_route("commits/" + commit + "/pulls?per_page=100"))
    matches = [p for p in rows if p.get("merge_commit_sha") == commit
               and p.get("merged_at") and p.get("state") == "closed"]
    require(len(matches) == 1, "merged commit not associated with exactly one PR")
    # The commit association list omits the merged boolean; read the full PR.
    number = matches[0]["number"]
    complete = api(repo_route("pulls/" + str(number)))
    require(complete.get("merged") is True and
            complete.get("merge_commit_sha") == commit, "PR merge readback differs")
    return complete


def find_qualification(head, branch):
    rows = api(repo_route("actions/runs?head_sha=" + head + "&per_page=100"))
    matches = [p for p in rows["workflow_runs"]
               if p.get("name") == INFRA and p.get("event") == "push" and
               p.get("head_branch") == branch and p.get("head_sha") == head and
               p.get("status") == "completed" and p.get("conclusion") == "success"]
    require(len(matches) == 1, "hosted exact Work Linux/Windows run missing/ambiguous")
    x = matches[0]
    return dict(id=x["id"], name=x["name"], event=x["event"],
                head_sha=x["head_sha"], head_branch=x["head_branch"],
                status=x["status"], conclusion=x["conclusion"],
                jobs=get_jobs(x["id"]))


def find_cleanup(head, branch, event):
    if event.get("workflow_run"):
        matches = [event["workflow_run"]]
    else:
        rows = api(repo_route("actions/workflows/rhc-branch-cleanup.yml/runs?per_page=100"))
        matches = [x for x in rows["workflow_runs"]
                   if x.get("head_sha") == head and x.get("head_branch") == branch
                   and x.get("event") == "pull_request" and
                   x.get("status") == "completed" and x.get("conclusion") == "success"]
    require(len(matches) == 1, "missing or ambiguous verified cleanup event")
    x = matches[0]
    require(x.get("head_repository", {}).get("full_name") in
            (None, os.environ["GITHUB_REPOSITORY"]),
            "untrusted cleanup source repository")
    return dict(name=x["name"], event=x["event"], head_sha=x["head_sha"],
                head_branch=x["head_branch"], status=x["status"],
                conclusion=x["conclusion"], jobs=get_jobs(x["id"]), id=x["id"])


def workflow_runs(name):
    rows = api(repo_route("actions/workflows/" + name + "/runs?per_page=100"))
    require(len(rows.get("workflow_runs", [])) < 100,
            "run discovery exceeds safe one-page bound; manual reconciliation")
    return rows["workflow_runs"]


def discover_run(rows, sha, version):
    title = "RHC POSTRELEASE v" + version + " main:" + sha
    return [x for x in rows if x.get("head_sha") == sha and
            x.get("event") == "workflow_dispatch" and
            x.get("display_title") == title]


def collect(event, forced_pr=None):
    repo = os.environ["GITHUB_REPOSITORY"]
    require(REPOSITORY.fullmatch(repo), "invalid Actions repository")
    require(os.environ.get("GITHUB_EVENT_NAME") in
            ("workflow_run", "schedule", "workflow_dispatch"), "invalid GH event")
    checkout = git("rev-parse", "HEAD")
    main = api(repo_route("branches/main"))["commit"]["sha"]
    require(main == checkout == os.environ["GITHUB_SHA"],
            "current exact main checkout changed")

    proof = provenance.verify_live(".", expected_main=main)
    releasepr = associated_pr(proof["releaseMergeSha"])
    correction = associated_pr(main)
    number = correction["number"]
    if forced_pr is not None:
        require(number == forced_pr, "owner recovery requested noncurrent PR")
    head = correction["head"]["sha"]
    branch = correction["head"]["ref"]
    change_page = api(repo_route("pulls/" + str(number) + "/files?per_page=100"))
    require(len(change_page) < 100, "PR file scope exceeds safe bound")
    changed = [p["filename"] for p in change_page]
    review_page = api(repo_route("pulls/" + str(number) + "/reviews?per_page=100"))
    require(len(review_page) < 100, "review list too large for proof")
    wm = WORK.fullmatch(branch)
    require(wm is not None, "current PR not a Work correction")
    issue_num = int(wm.group(1))
    issue = api(repo_route("issues/" + str(issue_num)))
    issue_exists = (issue.get("number") == issue_num and
                    issue.get("pull_request") is None)
    # True exact tree check prevents conflict merge changes from smuggling edits.
    mergeparents = git("rev-list", "--parents", "-n", "1", main).split()[1:]
    tree_matches = git("rev-parse", main + "^{tree}") == git(
        "rev-parse", head + "^{tree}")
    post_paths = git("diff", "--name-only", proof["releaseMergeSha"], main,
                     "--").splitlines()
    latest = json.loads(Path("downloads/latest.json").read_text(encoding="utf-8"))
    history = json.loads(Path("downloads/releases.json").read_text(encoding="utf-8"))
    archive = Path("downloads") / latest["file"]
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    require(archive_sha == latest["sha256"], "actual local published ZIP changed")
    tag_remote = git("ls-remote", "origin", "refs/tags/v" + latest["version"])
    tag_sha = tag_remote.split()[0] if tag_remote else ""
    event_name = os.environ["GITHUB_EVENT_NAME"]
    cleanup = find_cleanup(head, branch, event)
    qual = find_qualification(head, branch)
    prior_and_current = workflow_runs(VERIFY)
    current = discover_run(prior_and_current, main, latest["version"])
    prior = discover_run(prior_and_current, proof["releaseMergeSha"], latest["version"])
    prior = [x for x in prior if x.get("status") == "completed"
             and x.get("conclusion") == "failure"]
    require(len(prior) == 1, "original failed exact-release verifier missing")
    failed = prior[0]
    prior_data = {k: failed.get(k) for k in ("id", "event", "head_sha", "status",
                                          "conclusion", "display_title")}
    prior_data["jobs"] = get_jobs(failed["id"])
    publish_runs = workflow_runs("rhc-reusable-interim-release.yml")
    publisher_active = any(x.get("status") != "completed" for x in publish_runs)
    snapshot = dict(repository=repo, liveMainSha=main, checkoutSha=checkout,
        event=event_name, triggerRun=cleanup,
        release=dict(verified=proof["result"] == "PASS", mainSha=main,
                     mergeSha=proof["releaseMergeSha"], sourceSha=proof["sourceSha"],
                     version=proof["version"], tagSha=tag_sha,
                     archiveSha256=archive_sha, archiveSize=archive.stat().st_size,
                     latest=latest, historyHead=history["releases"][0],
                     sinceReleasePaths=post_paths),
        releasePr=dict(number=releasepr["number"], merged=releasepr["merged"],
                       state=releasepr["state"], baseRef=releasepr["base"]["ref"],
                       headRef=releasepr["head"]["ref"],
                       mergeSha=releasepr["merge_commit_sha"],
                       stagedSha=releasepr["head"]["sha"]),
        correctionPr=dict(number=number, merged=correction["merged"],
            state=correction["state"], body=correction.get("body"),
            headSha=head, baseSha=correction["base"]["sha"],
            mergeSha=correction["merge_commit_sha"],
            baseRef=correction["base"]["ref"], headRef=branch,
            headRepo=correction["head"]["repo"]["full_name"],
            issue=issue_num, issueExists=issue_exists,
            mergeParents=mergeparents, treeMatchesHead=tree_matches,
            files=changed, reviews=[dict(state=x.get("state"),
                             commit_id=x.get("commit_id"),
                             login=(x.get("user") or {}).get("login"))
                         for x in review_page]),
        qualification=qual, priorPostrelease=prior_data,
        existingCurrentRuns=current, publisherActive=publisher_active)
    return snapshot


def dispatch_and_watch(plan):
    repo = os.environ["GITHUB_REPOSITORY"]
    main = plan["expected_main_sha"]
    version = plan["version"]
    # Recheck all exact ref/immutable identities immediately before the only POST.
    require(api(repo_route("branches/main"))["commit"]["sha"] == main
            and git("rev-parse", "HEAD") == main, "public main drift pre-dispatch")
    latest = json.loads(Path("downloads/latest.json").read_text())
    require(latest["sourceSha"] == plan["expected_source_sha"] and
            latest["version"] == version and
            git("ls-remote", "origin", "refs/tags/v" + version).split()[0] ==
            plan["expected_source_sha"], "source tag or public catalog changed")
    require(not discover_run(workflow_runs(VERIFY), main, version),
            "exact-main verifier already submitted")
    stamp = dt.datetime.now(dt.timezone.utc)
    payload = dict(ref="main", inputs=dict(
        expected_main_sha=main, expected_source_sha=plan["expected_source_sha"],
        version=version, expected_release_pr=plan["expected_release_pr"]))
    api(repo_route("actions/workflows/" + VERIFY + "/dispatches"),
        method="POST", data=payload)
    print("RHC110_RECHECK_DISPATCHED=" + json.dumps(
        dict(plan, dispatchedUtc=stamp.isoformat().replace("+00:00", "Z")),
        sort_keys=True), flush=True)
    target = None
    for attempt in range(90):
        runs = discover_run(workflow_runs(VERIFY), main, version)
        fresh = [x for x in runs if x.get("created_at", "") >=
                 (stamp - dt.timedelta(seconds=10)).isoformat().replace("+00:00", "Z")
                 and x.get("actor", {}).get("login") == "github-actions[bot]"]
        require(len(fresh) <= 1, "ambiguous post-dispatch verifier identity")
        if fresh:
            target = fresh[0]
            if target["status"] == "completed":
                checked = api(repo_route("actions/runs/" + str(target["id"])))
                rows = get_jobs(target["id"])
                verify_postrelease_jobs(rows)
                require(checked.get("conclusion") == "success" and
                        checked.get("head_sha") == main and
                        checked.get("event") == "workflow_dispatch" and
                        api(repo_route("branches/main"))["commit"]["sha"] == main,
                        "independent postrelease outcome is not exact-main SUCCESS")
                print("RHC110_RECHECK_VERIFIED=" + json.dumps(
                    dict(runId=target["id"], status="PASS_CORRECTIVE_AUDIT_ONLY",
                         mainSha=main, version=version, jobs=rows,
                         originalFailedRun=plan["original_failed_run"]),
                    sort_keys=True), flush=True)
                return
        if attempt != 89:
            time.sleep(10)
    raise ValueError("postrelease dispatch unconfirmed/timeout; never retry blindly")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-json", required=True)
    parser.add_argument("--corrective-pr", type=int, default=None)
    args = parser.parse_args()
    require(Path(args.event_json).is_file(), "missing authentic event payload")
    event = json.loads(Path(args.event_json).read_text())
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_run":
        upstream = event.get("workflow_run") or {}
        if (upstream.get("name") != CLEANUP or
                upstream.get("status") != "completed" or
                upstream.get("conclusion") != "success" or
                upstream.get("event") != "pull_request"):
            print("RHC110_RECHECK=NO_ELIGIBLE_TRUSTED_UPSTREAM")
            return
    try:
        snapshot = collect(event, forced_pr=args.corrective_pr)
        plan = validate_plan(snapshot)
    except ValueError as exc:
        # A scheduled sweep over unrelated / already-checked main must not
        # submit a new run, yet never synthesize PASS or hide incident details.
        if os.environ.get("GITHUB_EVENT_NAME") in ("schedule", "workflow_run") and (
                "not a Work correction" in str(exc) or
                "already attempted" in str(exc) or
                "not associated" in str(exc)):
            print("RHC110_RECHECK=NO_DISPATCH reason=" + str(exc))
            return
        raise
    print("RHC110_RECHECK_ELIGIBILITY=" + json.dumps(plan, sort_keys=True), flush=True)
    dispatch_and_watch(plan)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print("RHC110_RECHECK=BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(1)
