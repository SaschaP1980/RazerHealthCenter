#!/usr/bin/env python3
"""RHC-132: fail-closed version-only Issue/Work preflight and atomic commit.

Plans by default. Optional --apply makes one LOCAL Git commit containing
exactly model.go + CHANGELOG.md; --push also requires a verified current
main and exact remote Work-ref lease. It NEVER publishes a release.
"""
import argparse
import calendar
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from rhc_issue_init import verify_initialized_issue

SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
CONSTANT = re.compile(r"(?m)^(?!\s*//)(\s*(?:appVersion|referenceVersion)\s*=\s*\")(\d+(?:\.\d+){3})(\"[^\n]*)$")
HEADINGS = (
    "Chat origin", "Work-Path authorization and scope", "Benchmark configuration",
    "Validation plan and coverage", "Measurement ledger",
    "Development Completion attempts", "Candidate Entry",
    "Candidate attempts", "Release", "Final Release Verification",
    "Performance result", "Evidence audit", "Plan-conformance assessment",
)
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def clock(text):
    if not isinstance(text, str):
        raise ValueError("missing UTC timestamp")
    try:
        instant = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid UTC timestamp") from exc
    if instant.utcoffset() is None:
        raise ValueError("naive UTC clock")
    return instant.astimezone(timezone.utc)


def berlin(utc):
    """CET/CEST with Europe/Berlin's EU rules, including on native Windows."""
    def last_sunday(year, month):
        last = calendar.monthrange(year, month)[1]
        day = date(year, month, last)
        return day - timedelta(days=(day.weekday() + 1) % 7)
    year = utc.year
    start = datetime.combine(last_sunday(year, 3), datetime.min.time(),
                             timezone.utc).replace(hour=1)
    end = datetime.combine(last_sunday(year, 10), datetime.min.time(),
                           timezone.utc).replace(hour=1)
    summer = start <= utc < end
    local = utc + timedelta(hours=2 if summer else 1)
    return local.strftime("%d.%m.%Y, %H:%M:%S ") + ("CEST" if summer else "CET")


def verify_bootstrap(comment, issue_number, branch_created):
    if not isinstance(comment, dict) or type(comment.get("id")) is not int:
        raise ValueError("missing saved GitHub comment")
    body = comment.get("body")
    if not isinstance(body, str):
        raise ValueError("missing canonical comment body")
    headings = re.findall(r"(?m)^### (.+)$", body)
    if headings != list(HEADINGS):
        raise ValueError("canonical 13-heading readback missing/duplicate")
    iso = re.search(r"(?m)^\*\*Original ISO timestamp:\*\* `?([^\s`]+)`?$", body)
    utc = re.search(r"(?m)^\*\*Last heartbeat:\*\* (.+)$", body)
    local = re.search(r"(?m)^\*\*Local reference \(Europe/Berlin\):\*\* (.+)$", body)
    if not iso or not utc or not local:
        raise ValueError("missing consistent 3-clock heartbeat")
    instant = clock(iso.group(1))
    if utc.group(1) != instant.strftime("%Y-%m-%d at %H:%M:%S UTC"):
        raise ValueError("UTC heartbeat differs from one ISO instant")
    if local.group(1) != berlin(instant):
        raise ValueError("Berlin heartbeat differs from ISO instant")
    # The current rolling heartbeat is refreshed on every substantive edit.
    # Its GitHub clock counterpart is updated_at, not immutable created_at.
    # The original BOOTSTRAP ISO is separately persisted and compared to
    # GitHub's independent creation timestamp even after later edits.
    creation_proofs = re.findall(
        r"(?m)^[*][*]Bootstrap creation ISO timestamp:[*][*] [`]?([0-9T:.-]+Z)[`]?$",
        body)
    if len(creation_proofs) != 1:
        raise ValueError("exactly one frozen BOOTSTRAP creation clock required")
    bootstrap = clock(creation_proofs[0])
    created = clock(comment.get("created_at"))
    updated = clock(comment.get("updated_at"))
    if abs((created - bootstrap).total_seconds()) > 30:
        raise ValueError("BOOTSTRAP creation proof differs from GitHub created_at")
    if updated < created:
        raise ValueError("GitHub comment updated_at precedes creation")
    if abs((updated - instant).total_seconds()) > 30:
        raise ValueError("current rolling heartbeat differs from GitHub updated_at")
    if instant < bootstrap - timedelta(seconds=30):
        raise ValueError("rolling heartbeat predates original BOOTSTRAP")
    if created >= clock(branch_created):
        raise ValueError("BOOTSTRAP comment created after Work branch")
    if f"issues/{issue_number}" not in body or (
            f"work/RHC-{issue_number}" not in body):
        raise ValueError("comment bound to wrong Issue/Work identity")
    if not re.search(r"(?mi)^\*\*Bootstrap readback:\*\*.*read back", body):
        raise ValueError("BOOTSTRAP did not record independent readback")
    if "NOT VERIFIED" in re.search(
            r"(?mi)^\*\*Bootstrap readback:\*\*.*$", body).group(0):
        raise ValueError("BOOTSTRAP readback still unverified")
    return True


def _updated_version(model):
    found = CONSTANT.findall(model)
    if len(found) != 2:
        raise ValueError("two and only two version constants required")
    names = [re.search(r"(appVersion|referenceVersion)", row[0]).group(1)
             for row in found]
    if sorted(names) != ["appVersion", "referenceVersion"]:
        raise ValueError("version constant identities invalid")
    old = found[0][1]
    if not VERSION.fullmatch(old) or found[1][1] != old:
        raise ValueError("appVersion/referenceVersion differ")
    components = [int(x) for x in old.split(".")]
    components[-1] += 1
    new = ".".join(map(str, components))
    rewritten = CONSTANT.sub(lambda m: m.group(1) + new + m.group(3), model)
    if rewritten.count('"' + new + '"') < 2:
        raise ValueError("version rewrite failed")
    return old, new, rewritten


def plan(*, saved_issue, comment, number, base_main_sha, readback_main_sha,
         work_head_sha, branch_created_at, model, changelog, day):
    if type(number) is not int or number < 1:
        raise ValueError("number invalid")
    verify_initialized_issue(saved_issue, number, for_development=True)
    if any(not isinstance(x, str) or not SHA.fullmatch(x) for x in
           (base_main_sha, readback_main_sha, work_head_sha)):
        raise ValueError("missing exact immutable Git SHA")
    if readback_main_sha != base_main_sha or work_head_sha != base_main_sha:
        raise ValueError("main or initial Work-head lease stale")
    verify_bootstrap(comment, number, branch_created_at)
    if not isinstance(model, str) or not isinstance(changelog, str):
        raise ValueError("source file unavailable")
    if not isinstance(day, date):
        raise ValueError("date invalid")
    old, new, changed_model = _updated_version(model)
    if not changelog.startswith("# Changelog\n\n## " + old + " "):
        raise ValueError("existing latest changelog version differs")
    new_section = ("## " + new + " — " + day.isoformat() + "\n\n"
                   "- Version-only HOTFIX: appVersion and referenceVersion "
                   "advanced from " + old + " to " + new + ". No runtime "
                   "or Razer repair/privilege/security-gate changes.\n\n")
    changed_changelog = changelog.replace("# Changelog\n\n",
                                            "# Changelog\n\n" + new_section, 1)
    if changed_changelog.count("## " + new + " ") != 1:
        raise ValueError("ambiguous new changelog section")
    message = (f"chore(RHC-{number}): advance version-only HOTFIX to v{new}\n\n"
               f"RHC-Issue: {number}\n"
               "Release-Profile: version-only\n"
               "Development-Completion: requested")
    return {"operation": "PLAN_ONLY", "number": number,
            "branch": f"work/RHC-{number}", "base_main_sha": base_main_sha,
            "from_version": old, "to_version": new,
            "allowed_paths": ["CHANGELOG.md", "model.go"],
            "original_model": model, "original_changelog": changelog,
            "model": changed_model, "changelog": changed_changelog,
            "commit_message": message, "bootstrap_comment_id": comment["id"]}


def _git(root, *arguments):
    result = subprocess.run(["git", "-C", str(root), *arguments],
                            capture_output=True, text=True, timeout=45)
    if result.returncode != 0:
        raise ValueError("local Git preflight/commit blocked")
    return result.stdout.strip()


def atomic_local_commit(root, approved_plan):
    """Only authorized independent plan can write both paths as one commit."""
    root = Path(root).resolve()
    if approved_plan.get("operation") != "PLAN_ONLY":
        raise ValueError("missing immutable validated plan")
    if _git(root, "branch", "--show-current") != approved_plan["branch"]:
        raise ValueError("wrong Work branch")
    if _git(root, "rev-parse", "HEAD") != approved_plan["base_main_sha"]:
        raise ValueError("Work HEAD no longer at frozen parent")
    if _git(root, "status", "--porcelain"):
        raise ValueError("local worktree not completely clean")
    originals = {p: (root / p).read_text(encoding="utf-8")
                 for p in approved_plan["allowed_paths"]}
    if originals != {"CHANGELOG.md": approved_plan["original_changelog"],
                     "model.go": approved_plan["original_model"]}:
        raise ValueError("local source differs from preflight snapshot")
    completed = False
    try:
        (root / "model.go").write_text(approved_plan["model"], encoding="utf-8")
        (root / "CHANGELOG.md").write_text(approved_plan["changelog"], encoding="utf-8")
        _git(root, "add", "--", "model.go", "CHANGELOG.md")
        staged = _git(root, "diff", "--cached", "--name-only").splitlines()
        if staged != approved_plan["allowed_paths"]:
            raise ValueError("non-authorized staged path")
        _git(root, "diff", "--cached", "--check")
        _git(root, "commit", "-m", approved_plan["commit_message"])
        completed = True
        new_sha = _git(root, "rev-parse", "HEAD")
        parents = _git(root, "rev-list", "--parents", "-n", "1", "HEAD").split()
        changed = _git(root, "diff-tree", "--no-commit-id", "--name-only",
                       "-r", "HEAD").splitlines()
        if parents != [new_sha, approved_plan["base_main_sha"]] or (
                changed != approved_plan["allowed_paths"]):
            raise ValueError("committed ancestry/file set changed")
        return new_sha
    finally:
        if not completed:
            for name, original in originals.items():
                (root / name).write_text(original, encoding="utf-8")
            _git(root, "reset", "-q", "HEAD", "--", *approved_plan["allowed_paths"])


def _api(repository, endpoint):
    if not REPO.fullmatch(repository) or not re.fullmatch(
            r"[A-Za-z0-9/?=&_.-]+", endpoint):
        raise ValueError("invalid GitHub API identity")
    r = subprocess.run(["gh", "api", "-X", "GET",
                        f"repos/{repository}/{endpoint}"],
                       capture_output=True, text=True, timeout=45)
    if r.returncode:
        raise ValueError("read-only GitHub GET failed")
    return json.loads(r.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repository", required=True)
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--comment-id", type=int, required=True)
    ap.add_argument("--base-main-sha", required=True)
    ap.add_argument("--branch-created-at", required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--day", help="UTC date YYYY-MM-DD; default today UTC")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args(argv)
    if args.push and not args.apply:
        ap.error("--push requires --apply")
    try:
        if not SHA.fullmatch(args.base_main_sha):
            raise ValueError("invalid pinned main SHA")
        root = args.root.resolve()
        saved_issue = _api(args.repository, f"issues/{args.issue}")
        comment = _api(args.repository, f"issues/comments/{args.comment_id}")
        work = _api(args.repository, f"git/ref/heads/work/RHC-{args.issue}")
        main_sha = _api(args.repository, "git/ref/heads/main")["object"]["sha"]
        work_sha = work["object"]["sha"]
        info = plan(saved_issue=saved_issue, comment=comment, number=args.issue,
                    base_main_sha=args.base_main_sha, readback_main_sha=main_sha,
                    work_head_sha=work_sha,
                    branch_created_at=args.branch_created_at,
                    model=(root / "model.go").read_text(encoding="utf-8"),
                    changelog=(root / "CHANGELOG.md").read_text(encoding="utf-8"),
                    day=date.fromisoformat(args.day) if args.day
                    else datetime.now(timezone.utc).date())
        if not args.apply:
            print("RHC132_PREFLIGHT=PASS PLAN_ONLY " +
                  json.dumps({k: info[k] for k in
                              ("branch", "from_version", "to_version",
                               "allowed_paths", "bootstrap_comment_id")}))
            return 0
        new_sha = atomic_local_commit(root, info)
        if args.push:
            # Original main and remote Work ref must STILL match preflight.
            if _api(args.repository, "git/ref/heads/main")["object"]["sha"] != (
                    args.base_main_sha):
                raise ValueError("main moved after local commit; push blocked")
            if _api(args.repository, f"git/ref/heads/work/RHC-{args.issue}")[
                    "object"]["sha"] != args.base_main_sha:
                raise ValueError("remote Work ref moved; push blocked")
            _git(root, "push", "origin",
                 f"HEAD:refs/heads/work/RHC-{args.issue}")
            if _api(args.repository, f"git/ref/heads/work/RHC-{args.issue}")[
                    "object"]["sha"] != new_sha:
                raise ValueError("remote push readback inconsistent")
        print("RHC132_ATOMIC_WORK_COMMIT=PASS " +
              json.dumps({"sha": new_sha, "pushed": args.push,
                          "paths": info["allowed_paths"]}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
        print("RHC132_PREFLIGHT_BLOCKED — no unsafe retry or release", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
