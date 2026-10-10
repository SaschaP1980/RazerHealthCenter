#!/usr/bin/env python3
"""RHC-115: fail-closed, two-phase GitHub Issue initialization.

The create operation is deliberately never retried after an ambiguous result.
Only clients that call this entry point/verify_issue are covered; GitHub's web
UI and unrelated API clients cannot be globally intercepted by repository code.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import secrets
import subprocess
import sys

TITLE = re.compile(r"^\[RHC-([1-9][0-9]*)\] ([^\s].*\S|[^\s])$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NONCE = re.compile(r"^[0-9a-f]{12,32}$")


class InitializationBlocked(ValueError):
    """INITIALIZATION_BLOCKED / NEEDS_CORRECTION, never proceed to writes."""


def require(condition, reason):
    if not condition:
        raise InitializationBlocked("INITIALIZATION_BLOCKED / NEEDS_CORRECTION: " + reason)


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_title(number, subject):
    require(type(number) is int and number > 0, "missing authoritative issue number")
    require(isinstance(subject, str) and subject == subject.strip()
            and "\n" not in subject and "\r" not in subject
            and bool(subject) and not subject.startswith("[RHC"),
            "missing or ambiguous descriptive subject")
    return "[RHC-{}] {}".format(number, subject)


def provisional_title(subject, nonce):
    canonical_title(1, subject)  # validates the subject without guessing a real issue ID
    require(isinstance(nonce, str) and NONCE.fullmatch(nonce),
            "missing or unsafe creation nonce")
    return "Initializing RHC Issue: {} [init-{}]".format(subject, nonce)


def verify_issue(issue, number, *, body=None, subject=None, require_open=True):
    """Validate an independent raw GET, not the creation/update response."""
    require(type(number) is int and number > 0, "invalid expected numeric issue number")
    require(isinstance(issue, dict) and not ("pull_request" in issue),
            "missing issue or pull request supplied instead of Issue")
    require(type(issue.get("number")) is int and issue["number"] == number,
            "GitHub issue identity mismatch")
    title = issue.get("title")
    m = TITLE.fullmatch(title) if isinstance(title, str) else None
    require(m is not None and int(m.group(1)) == number,
            "incorrect, provisional, numberless or mismatched [RHC-N] issue title")
    require(isinstance(issue.get("body"), str) and bool(issue["body"].strip()),
            "missing saved Issue scope/body")
    if body is not None:
        require(issue["body"] == body, "saved Issue body differs from intended scope")
    if subject is not None:
        require(title == canonical_title(number, subject), "saved descriptive subject mismatch")
    require(issue.get("state") in (("open",) if require_open else ("open", "closed")),
            "invalid Issue state")
    return issue


def _candidate_number(gateway, provisional, body, created):
    # A matching response number helps, but a separate GET remains mandatory.
    response_number = created.get("number") if isinstance(created, dict) else None
    candidates = gateway.search(provisional, body)
    require(isinstance(candidates, list) and len(candidates) == 1,
            "missing or ambiguous unique provisional GitHub Issue lookup")
    candidate = candidates[0]
    require(isinstance(candidate, dict), "invalid Issue lookup record")
    number = candidate.get("number")
    require(type(number) is int and number > 0 and "pull_request" not in candidate,
            "lookup did not identify one numbered Issue")
    if response_number is not None:
        require(type(response_number) is int and response_number == number,
                "creation response number differs from authoritative lookup")
    return number


def recover_issue(gateway, number, subject, body, *, nonce=None, log=None):
    """Repair ONLY an identified matching provisional Issue; never create again."""
    expected = canonical_title(number, subject)
    saved = gateway.get(number)
    require(isinstance(saved, dict) and saved.get("number") == number
            and "pull_request" not in saved and saved.get("state") == "open"
            and saved.get("body") == body and bool(body.strip()),
            "identified Issue missing/changed or body/state mismatch")
    if saved.get("title") == expected:
        return verify_issue(gateway.get(number), number, body=body, subject=subject)
    require(nonce is not None and saved.get("title") == provisional_title(subject, nonce),
            "refusing to rename a foreign, stale or non-provisional Issue")
    try:
        gateway.update(number, expected)
        if log:
            log("rename_response_received", number, expected)
    except Exception as exc:
        if log:
            log("rename_response_unknown", number, str(exc))
        # Do not retry writes. Independent GET determines if the prior write worked.
    confirmed = gateway.get(number)
    return verify_issue(confirmed, number, body=body, subject=subject)


def initialize_issue(gateway, subject, body, labels, *, nonce=None, log=None):
    """One create, unique-search reconciliation, one guarded rename, final GET."""
    require(isinstance(body, str) and bool(body.strip()), "nonempty Issue scope required")
    nonce = nonce if nonce is not None else secrets.token_hex(8)
    temporary = provisional_title(subject, nonce)
    require(isinstance(labels, (tuple, list)), "Issue labels invalid")
    created = None
    try:
        created = gateway.create(temporary, body, list(labels))
        if log:
            log("create_response_received", None, temporary)
    except Exception as exc:
        if log:
            log("create_response_unknown", None, str(exc))
        # A timeout may mean creation succeeded: NEVER call create() again.
    number = _candidate_number(gateway, temporary, body, created)
    # Independent exact Issue readback before any title edit.
    initial = gateway.get(number)
    require(isinstance(initial, dict) and initial.get("number") == number
            and initial.get("title") == temporary and initial.get("body") == body
            and initial.get("state") == "open" and "pull_request" not in initial,
            "provisional Issue stale, duplicated, missing or modified before rename")
    if log:
        log("authoritative_provisional_readback", number, temporary)
    confirmed = recover_issue(gateway, number, subject, body, nonce=nonce, log=log)
    if log:
        log("canonical_exact_issue_get_verified", number, confirmed["title"])
    return confirmed


class GithubGateway:
    """Single-use GitHub CLI transport with no implicit write retries."""

    def __init__(self, repository):
        require(isinstance(repository, str) and REPOSITORY.fullmatch(repository),
                "invalid repository selector")
        self.repository = repository
        self.url = "repos/" + repository

    def _api(self, method, path, payload=None):
        command = ["gh", "api", "-X", method, self.url + path]
        if payload is not None:
            command += ["--input", "-"]
        result = subprocess.run(
            command, input=json.dumps(payload) if payload is not None else None,
            text=True, capture_output=True, timeout=40, check=False)
        require(result.returncode == 0,
                "GitHub {} {} failed: {}".format(method, path, result.stderr.strip()[:400]))
        try:
            return json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise InitializationBlocked("INITIALIZATION_BLOCKED / NEEDS_CORRECTION: "
                                        "GitHub response is not JSON") from exc

    def create(self, title, body, labels):
        return self._api("POST", "/issues", dict(title=title, body=body, labels=labels))

    def update(self, number, title):
        return self._api("PATCH", "/issues/{}".format(number), dict(title=title))

    def get(self, number):
        return self._api("GET", "/issues/{}".format(number))

    def all_issues(self, *, state="all"):
        require(state in ("open", "closed", "all"), "invalid issue audit state")
        for page in range(1, 21):
            rows = self._api("GET", "/issues?state={}&per_page=100&page={}".format(state, page))
            require(isinstance(rows, list), "GitHub Issue enumeration invalid")
            for item in rows:
                yield item
            if len(rows) < 100:
                return
        raise InitializationBlocked("INITIALIZATION_BLOCKED / NEEDS_CORRECTION: "
                                    "Issue audit pagination exceeded safe bound")

    def search(self, title, body):
        return [row for row in self.all_issues(state="open")
                if "pull_request" not in row
                and row.get("title") == title and row.get("body") == body]


def audit(gateway):
    """Read-only audit: never rewrite unrelated or historic Issue titles."""
    bad = []
    checked = 0
    for row in gateway.all_issues(state="all"):
        if "pull_request" in row:
            continue
        checked += 1
        try:
            verify_issue(row, row.get("number"), require_open=False)
        except InitializationBlocked as exc:
            bad.append(dict(number=row.get("number"), title=row.get("title"), error=str(exc)))
    return dict(result="PASS" if not bad else "NEEDS_CORRECTION",
                checked=checked, malformed=bad)


def _event(name, number, value):
    print("RHC115_INIT_AUDIT=" + json.dumps(dict(
        utc=utc_now(), event=name, number=number, evidence=value), sort_keys=True),
        flush=True)


def cli(argv=None):
    parser = argparse.ArgumentParser(description="RHC-115 verified GitHub Issue initialization")
    parser.add_argument("command", choices=("init", "recover", "verify", "audit"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue", type=int)
    parser.add_argument("--subject")
    parser.add_argument("--body-file")
    parser.add_argument("--body-sha256")
    parser.add_argument("--nonce")
    parser.add_argument("--label", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        gateway = GithubGateway(args.repository)
        body = None
        if args.body_file:
            with open(args.body_file, "r", encoding="utf-8") as handle:
                body = handle.read()
        if args.command == "init":
            require(body is not None and args.subject is not None,
                    "init requires --subject and --body-file")
            types = ("bug", "enhancement")
            priorities = ("priority: critical", "priority: high",
                          "priority: medium", "priority: low")
            require(sum(x in types for x in args.label) == 1
                    and sum(x in priorities for x in args.label) == 1,
                    "Issue creation requires exactly one type and priority label (RHC-116)")
            result = initialize_issue(gateway, args.subject, body, args.label,
                                      nonce=args.nonce, log=_event)
        elif args.command == "recover":
            require(args.issue is not None and args.subject is not None
                    and body is not None, "recovery requires issue, subject and saved body")
            result = recover_issue(gateway, args.issue, args.subject, body,
                                   nonce=args.nonce, log=_event)
        elif args.command == "verify":
            require(args.issue is not None, "verify requires numeric --issue")
            result = verify_issue(gateway.get(args.issue), args.issue,
                                  body=body, subject=args.subject)
            if args.body_sha256:
                require(hashlib.sha256(result["body"].encode()).hexdigest() ==
                        args.body_sha256, "saved body digest mismatch")
        else:
            report = audit(gateway)
            print("RHC115_ISSUE_TITLE_AUDIT=" + json.dumps(report, sort_keys=True))
            return 0 if report["result"] == "PASS" else 2
        print("RHC115_INITIALIZATION_VERIFIED=" + json.dumps(dict(
            result="PASS", repository=args.repository, number=result["number"],
            title=result["title"],
            url="https://github.com/{}/issues/{}".format(args.repository, result["number"]),
            bodySha256=hashlib.sha256(result["body"].encode()).hexdigest(),
            readbackUtc=utc_now()), sort_keys=True))
        return 0
    except (InitializationBlocked, OSError, subprocess.TimeoutExpired) as exc:
        print("RHC115_INITIALIZATION_BLOCKED=" + json.dumps(dict(
            result="INITIALIZATION_BLOCKED / NEEDS_CORRECTION",
            message=str(exc), utc=utc_now()), sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(cli())
