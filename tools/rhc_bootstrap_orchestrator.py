#!/usr/bin/env python3
"""RHC-166: single safe Issue -> canonical Rolling -> Work branch transaction.

Read-only by default. --apply never commits, pushes, dispatches or publishes;
a separately approved new version uses RHC-132's existing atomic Work commit.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

import rhc_issue_init as issue_init
import rhc132_work_preflight as rhc132

HEADINGS = rhc132.HEADINGS
SHA = re.compile(r"^[0-9a-f]{40}$")
MARKER = re.compile(r"^RHC[1-9][0-9]*CHAT[A-F0-9]{12}$")
SCHEMA = re.compile(r"~~~markdown\n([\s\S]+?)\n~~~")


def require(condition, reason):
    if not condition:
        raise ValueError("RHC166_BOOTSTRAP_BLOCKED: " + reason)


def utc(value):
    require(isinstance(value, datetime) and value.tzinfo is not None and
            value.utcoffset() is not None, "verified aware timestamp required")
    return value.astimezone(timezone.utc)


def iso(value):
    return utc(value).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def extract_headings(body):
    return tuple(re.findall(r"(?m)^### (.+)$", str(body)))


def scaffold(text):
    require(isinstance(text, str), "missing canonical template")
    match = SCHEMA.search(text)
    require(match is not None, "full template Markdown fence missing")
    body = match.group(1)
    require(extract_headings(body) == HEADINGS and
            "**Bootstrap creation ISO timestamp:**" in body and
            "| Rolling Comment BOOTSTRAP created/read back |" in body,
            "mandatory 13 headings or ledger missing")
    return body


def replace_line(body, prefix, value):
    lines = body.split("\n")
    indexes = [idx for idx, line in enumerate(lines) if line.startswith(prefix)]
    require(len(indexes) == 1, "missing/duplicate original field " + prefix)
    lines[indexes[0]] = prefix + " " + str(value)
    return "\n".join(lines)


def replace_row(body, event, when, evidence):
    lines = body.split("\n")
    prefix = "| " + event + " |"
    found = [idx for idx, line in enumerate(lines) if line.startswith(prefix)]
    require(len(found) == 1, "missing/duplicate original ledger event")
    lines[found[0]] = prefix + " " + when + " | " + evidence + " |"
    return "\n".join(lines)


def set_heartbeat(body, value):
    stamp = utc(value)
    body = replace_line(body, "**Last heartbeat:**",
                        stamp.strftime("%Y-%m-%d at %H:%M:%S UTC"))
    body = replace_line(body, "**Local reference (Europe/Berlin):**",
                        rhc132.berlin(stamp))
    return replace_line(body, "**Original ISO timestamp:**",
                        chr(96) + iso(stamp) + chr(96))


def create_bootstrap(template, number, main, marker, instant):
    require(type(number) is int and number > 0 and
            isinstance(main, str) and SHA.fullmatch(main) and
            isinstance(marker, str) and MARKER.fullmatch(marker) and
            marker.startswith("RHC{}CHAT".format(number)),
            "Issue/main/visible marker identity mismatch")
    body = scaffold(template).replace("<GitHub Issue number>", str(number))
    body = body.replace("<number>", str(number))
    body = set_heartbeat(body, instant)
    frozen = chr(96) + iso(instant) + chr(96)
    fields = {
        "**Bootstrap creation ISO timestamp:**": frozen,
        "**Agent-State:**": "ACTIVE",
        "**Issue:**": "[RHC-{0}](https://github.com/SaschaP1980/RazerHealthCenter/issues/{0})".format(number),
        "**Base main:**": chr(96) + main + chr(96),
        "**Work branch / exact head:**": "work/RHC-{} / NOT CREATED in BOOTSTRAP".format(number),
        "**Last checkpoint:**": main + " prebranch main",
        "**Bootstrap readback:**": "NOT VERIFIED — STOP before branch",
        "**Version:**": "unknown — no product version authorized",
        "**Current phase:**": "BOOTSTRAP",
        "**Next action:**": "independently GET Issue and complete same comment before Work ref",
        "- Execution platform:": "ChatGPT or authenticated operator",
        "- Originating Work-Chat-ID:": marker,
        "- Marker posted as a visible message in that chat:": "yes — operator attested, chat proof checked separately",
        "- Additional execution chats:": "none",
        "- Search confirmation:": "explicit current owner Work authorization required",
        "- Development-path decision:": "GitHub saved Issue independently validates dev-path: work-branch",
        "- Work-Branch-Reason:": "combine RHC115 Issue, full rolling and RHC132 guarded Work preflight",
        "- Allowed diff:": "saved Issue defines permitted source paths",
        "- Forbidden changes:": "no Razer repair/UAC, workflow bypass, version or new release by bootstrap",
        "- Protected/deletion intent:": "none during bootstrap",
        "- Real Razer hardware E2E:": "NOT APPLICABLE — nonpublishing bootstrap",
        "- Work-Path Development Completion:": "NOT APPLICABLE — no new product release",
        "- Candidate-Entry:": "NOT APPLICABLE — nonpublishing",
        "- Release run/status:": "NOT APPLICABLE — no release",
        "- Issue completion eligibility:": "NO until future real CI/PR/merge",
        "**PASS | PASS WITH CORRECTION | FAIL | NOT READY**": "NOT READY",
    }
    for key, value in fields.items():
        body = replace_line(body, key, value)
    # Preserve every label and table from the canonical template. Values
    # without live evidence remain explicit placeholders, never synthetic PASS.
    body = replace_row(body, "Issue created", "unknown — independent readback pending",
                       "Issue #{} real GitHub created_at required".format(number))
    body = replace_row(body, "Rolling Comment BOOTSTRAP created/read back",
                       "NOT VERIFIED", "STOP until real GitHub readback")
    require(extract_headings(body) == HEADINGS, "full scaffold changed")
    return body


def checked_comment(g, ident, expected):
    row = g.get_comment(ident)
    require(isinstance(row, dict) and row.get("id") == ident and
            row.get("body") == expected and extract_headings(expected) == HEADINGS,
            "saved comment ID/content/13 headings differ")
    return row


def edit_exact(g, comment_id, revised):
    # Ambiguous mutation? Never retry: GET alone establishes the result.
    try:
        g.update_comment(comment_id, revised)
    except Exception:
        pass
    return checked_comment(g, comment_id, revised)


def version_only_plan(*, saved_issue, saved_comment, number, main_sha, work_sha,
                      branch_created_at, model, changelog, day):
    """Delegate ALL version-specific authority to RHC132 (no cloned checks)."""
    return rhc132.plan(saved_issue=saved_issue, comment=saved_comment,
                       number=number, base_main_sha=main_sha,
                       readback_main_sha=main_sha, work_head_sha=work_sha,
                       branch_created_at=branch_created_at,
                       model=model, changelog=changelog, day=day)


def run(g, *, repository, subject, issue_body, labels, template, pinned_main,
        marker, instant, apply=False, issue_number=None, clock=None):
    require(repository == "SaschaP1980/RazerHealthCenter" and
            isinstance(pinned_main, str) and SHA.fullmatch(pinned_main) and
            isinstance(marker, str) and MARKER.fullmatch(marker),
            "untrusted repo/main/visible marker")
    utc(instant)
    scaffold(template)
    issue_init.validate_create_request(subject, issue_body, labels)
    require(g.get_main() == pinned_main, "pinned main already stale")
    if issue_number is not None:
        require(type(issue_number) is int and issue_number > 0 and
                marker.startswith("RHC{}CHAT".format(issue_number)),
                "existing Issue number/marker inconsistent")
        issue_init.verify_initialized_issue(g.get(issue_number), issue_number,
                                            body=issue_body, subject=subject,
                                            for_development=True)
    if not apply:
        return {"status": "PLAN_ONLY", "main_sha": pinned_main,
                "issue": issue_number, "writes": 0, "headings": len(HEADINGS)}
    if issue_number is None:
        verified = issue_init.initialize_issue(g, subject, issue_body, labels)
        issue_number = verified["number"]
        require(marker.startswith("RHC{}CHAT".format(issue_number)),
                "new number differs from visible user/chat marker")
    verified = issue_init.verify_initialized_issue(
        g.get(issue_number), issue_number, body=issue_body, subject=subject,
        for_development=True)
    branch = "work/RHC-{}".format(issue_number)
    require(g.get_main() == pinned_main and g.get_branch(branch) is None,
            "main changed or Work branch occupied")
    require(g.list_comments(issue_number) == [],
            "existing comments need explicit operator recovery; no blind overwrite")
    original = create_bootstrap(template, issue_number, pinned_main, marker, instant)
    try:
        g.create_comment(issue_number, original)
    except Exception:
        pass
    rows = g.list_comments(issue_number)
    require(isinstance(rows, list) and len(rows) == 1 and
            isinstance(rows[0], dict) and rows[0].get("body") == original and
            type(rows[0].get("id")) is int,
            "missing, foreign or duplicate BOOTSTRAP after possible POST")
    saved = checked_comment(g, rows[0]["id"], original)
    created_at = rhc132.clock(saved["created_at"])
    require(abs((created_at - utc(instant)).total_seconds()) <= 30,
            "frozen BOOTSTRAP clock differs from GitHub created_at")
    fresh = clock() if clock else datetime.now(timezone.utc)
    prebranch = set_heartbeat(original, fresh)
    prebranch = replace_line(prebranch, "**Bootstrap readback:**",
                             "saved comment #{} independently read back before branch".format(saved["id"]))
    prebranch = replace_line(prebranch, "**Next action:**",
                             "verify persisted updated comment and main, create unique Work branch")
    prebranch = replace_row(prebranch, "Rolling Comment BOOTSTRAP created/read back",
                            saved["created_at"],
                            "comment #{} exact full readback".format(saved["id"]))
    saved = edit_exact(g, saved["id"], prebranch)
    require(g.get_main() == pinned_main and g.get_branch(branch) is None,
            "base drift/duplicate branch after readback")
    try:
        created_branch = g.create_branch(branch, pinned_main)
    except Exception:
        created_branch = None
    head = g.get_branch(branch)
    require(head == pinned_main and g.get_main() == pinned_main,
            "ambiguous branch response, wrong SHA or moved main")
    # Git refs do not carry GitHub created_at. A time read *after* the
    # create response is a local observation, explicitly distinct from REST.
    branch_at = created_branch.get("created_at") if isinstance(created_branch, dict) else None
    if branch_at is None:
        branch_at = iso(datetime.now(timezone.utc))
    require(rhc132.clock(branch_at) > created_at,
            "comment must exist BEFORE branch; no chronological proof")
    refreshed = clock() if clock else datetime.now(timezone.utc)
    final = set_heartbeat(prebranch, refreshed)
    final = replace_line(final, "**Work branch / exact head:**",
                         "{} / {} independently re-read".format(branch, head))
    final = replace_line(final, "**Last checkpoint:**", head + " Work initial HEAD")
    final = replace_line(final, "**Current phase:**", "WORK_CREATED")
    final = replace_line(final, "**Next action:**",
                         "invoke RHC132 guarded version-only preflight only when separately owner-authorized")
    final = replace_row(final, "Work branch created", branch_at,
                        "{} SHA {} independently read back".format(branch, head))
    saved = edit_exact(g, saved["id"], final)
    rhc132.verify_bootstrap(saved, issue_number, branch_at)
    require(g.get_main() == pinned_main and g.get_branch(branch) == pinned_main,
            "final issue/ref readback changed")
    return {"status": "BOOTSTRAP_VERIFIED", "issue": issue_number,
            "comment_id": saved["id"], "branch": branch, "work_sha": head,
            "branch_created_at": branch_at, "main_sha": pinned_main,
            "headings": len(HEADINGS), "new_version": "NOT AUTHORIZED"}


class Gateway(issue_init.GithubGateway):
    """Authenticated gh CLI REST (no additional PAT, app, retries or scopes)."""

    def get_main(self):
        return self._api("GET", "/git/ref/heads/main")["object"]["sha"]

    def get_branch(self, branch):
        require(re.fullmatch(r"work/RHC-[1-9][0-9]*", str(branch)),
                "unexpected branch selector")
        try:
            return self._api("GET", "/git/ref/heads/" + branch)["object"]["sha"]
        except issue_init.InitializationBlocked as exc:
            require("404" in str(exc) or "Not Found" in str(exc),
                    "GitHub branch read API failed (not 404)")
            return None

    def create_branch(self, branch, sha):
        require(SHA.fullmatch(str(sha)) and
                re.fullmatch(r"work/RHC-[1-9][0-9]*", str(branch)),
                "unsafe branch create")
        return self._api("POST", "/git/refs",
                         {"ref": "refs/heads/" + branch, "sha": sha})

    def list_comments(self, number):
        result = []
        for page in range(1, 11):
            chunk = self._api("GET",
                              "/issues/{}/comments?per_page=100&page={}".format(number, page))
            require(isinstance(chunk, list), "invalid GitHub comments response")
            result.extend(chunk)
            if len(chunk) < 100:
                return result
        raise ValueError("RHC166_BOOTSTRAP_BLOCKED: pagination overflow")

    def create_comment(self, number, body):
        return self._api("POST", "/issues/{}/comments".format(number), {"body": body})

    def get_comment(self, ident):
        return self._api("GET", "/issues/comments/{}".format(ident))

    def update_comment(self, ident, body):
        return self._api("PATCH", "/issues/comments/{}".format(ident), {"body": body})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--template-file", type=Path,
                        default=Path("docs/templates/WORK_PATH_ROLLING_COMMENT.md"))
    parser.add_argument("--pinned-main-sha", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--existing-issue", type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run(Gateway(args.repository), repository=args.repository,
                     subject=args.subject,
                     issue_body=args.body_file.read_text(encoding="utf-8"),
                     labels=args.label,
                     template=args.template_file.read_text(encoding="utf-8"),
                     pinned_main=args.pinned_main_sha, marker=args.marker,
                     instant=datetime.now(timezone.utc),
                     apply=args.apply, issue_number=args.existing_issue)
        print("RHC166_BOOTSTRAP=" + json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, RuntimeError, OSError):
        print("RHC166_BOOTSTRAP_BLOCKED_NOT_VERIFIED — no blind mutation retries",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
