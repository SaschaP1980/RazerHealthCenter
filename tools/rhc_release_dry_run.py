#!/usr/bin/env python3
"""RHC-5 immutable, pure simulated Release lifecycle. Never calls GitHub or mutates state.

All 'future' versions, SHAs, drafts, merges and publishes are fixture data only.
This code has no network, file-write, subprocess or GitHub API capabilities.
"""
import hashlib
import json
import re

from rhc_orchestration_contracts import (
    REQUIRED_CANDIDATE_CONTEXTS, validate_candidate, publication_policy
)
from rhc_release_contracts import require

STATES = (
    "candidate-qualified", "release-built", "artifacts-verified",
    "merge-ready", "main-merged", "draft-ready", "publish-ready",
    "published-verified"
)
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _sha(s):
    return isinstance(s, str) and bool(_HEX40.fullmatch(s))


def _digest(s):
    return isinstance(s, str) and bool(_HEX64.fullmatch(s))


def _yes(o, name):
    require(isinstance(o, dict) and o.get(name) is True, name + " not verified")


def _same(value, expected, label):
    require(value == expected, label + " differs from pinned evidence")


def _get(s, key):
    value = s.get(key)
    require(isinstance(value, dict), "missing " + key + " fixture")
    return value


def _artifacts(rows, version):
    require(isinstance(rows, list) and len(rows) == 2,
            "exactly source and portable assets required")
    expected = {
        "RazerHealthCenter-Source-v" + version + ".zip",
        "RazerHealthCenter-Portable-v" + version + ".zip"
    }
    result = {}
    for a in rows:
        require(isinstance(a, dict), "invalid asset")
        name, h, size = a.get("name"), a.get("sha256"), a.get("size")
        require(isinstance(name, str) and name in expected and name not in result,
                "wrong/duplicate asset")
        require(_digest(h) and type(size) is int and size > 0,
                "invalid asset sha256 or size")
        result[name] = (h, size)
    require(set(result) == expected, "incomplete assets")
    return result


def _candidate(s):
    c = _get(s, "candidate")
    for key in ("mainSha", "parentSha", "sha", "currentMainSha"):
        require(_sha(c.get(key)), "missing exact candidate SHA: " + key)
    _same(c.get("parentSha"), c["mainSha"], "candidate parent")
    _same(c.get("currentMainSha"), c["mainSha"], "current main")
    version = c.get("version")
    require(type(c.get("issue")) is int and c["issue"] > 0, "missing issue")
    require(c.get("ref") == "candidate/v" + str(version), "candidate ref/version mismatch")
    validate_candidate(previous=c.get("previousVersion"), version=version,
                       changed_paths=c.get("changedPaths"),
                       release_profile=c.get("profile"),
                       current_main_parent=True)
    require(c.get("tagExists") is False and c.get("releaseExists") is False,
            "version/tag/release collision")
    statuses = c.get("statuses")
    require(isinstance(statuses, list) and
            len(statuses) == len(REQUIRED_CANDIDATE_CONTEXTS),
            "missing/duplicate hosted statuses")
    seen = set()
    for row in statuses:
        require(isinstance(row, dict), "invalid status row")
        name = row.get("context")
        require(name in REQUIRED_CANDIDATE_CONTEXTS and name not in seen,
                "missing/duplicate status context")
        seen.add(name)
        _same(row.get("sha"), c["sha"], "hosted status SHA")
        require(row.get("state") == "success", "hosted status not success")
    require(seen == set(REQUIRED_CANDIDATE_CONTEXTS), "missing hosted status")
    return c


def _build(s, c):
    b = _get(s, "build")
    _same(b.get("candidateSha"), c["sha"], "build source")
    _yes(b, "independent")
    runs = b.get("runs")
    require(isinstance(runs, list) and len(runs) == 2, "two independent Go builds required")
    runners = set()
    for run in runs:
        require(isinstance(run, dict), "missing Linux build")
        name = run.get("runner")
        require(isinstance(name, str) and name.startswith("linux") and
                name not in runners, "independent Linux runner identities required")
        runners.add(name)
        _same(run.get("sha"), c["sha"], "Linux build SHA")
        require(run.get("go") == "1.23.2" and run.get("build") == "success",
                "original Go build failed")
        _yes(run, "goTests")
        _yes(run, "safety")
    w = b.get("windows")
    require(isinstance(w, dict), "Windows job missing")
    _same(w.get("sha"), c["sha"], "Windows build SHA")
    require(w.get("host") == "windows-2025" and w.get("psVersion") == "5.1",
            "real hosted Windows PowerShell 5.1 required")
    for key in ("parser", "goTests", "goVet", "repairSafety"):
        _yes(w, key)


def _packages(s, c):
    a = _get(s, "artifacts")
    _same(a.get("candidateSha"), c["sha"], "artifact build")
    first = _artifacts(a.get("build1"), c["version"])
    require(_artifacts(a.get("build2"), c["version"]) == first,
            "independent package digest/size mismatch")
    src = a.get("source")
    require(isinstance(src, dict) and isinstance(src.get("files"), list),
            "source manifest missing")
    files = src["files"]
    require(len(files) == len(set(files)) and
            {"LICENSE", "model.go", "go.mod", "build.sh"} <= set(files),
            "source manifest incomplete/duplicate")
    require(src.get("forbiddenFound") is False, "forbidden source payload")
    for name in files:
        require(isinstance(name, str) and name and "\\" not in name and
                not name.startswith("/") and
                ".." not in name.split("/") and
                not name.lower().endswith((".zip", ".exe", ".log")) and
                not name.startswith(("forensics/", "dist/", ".git/")),
                "unsafe source ZIP entry")
    portable = a.get("portable")
    require(isinstance(portable, dict) and type(portable.get("files")) is int
            and portable["files"] == 8 and
            type(portable.get("directories")) is int and
            portable["directories"] == 12,
            "future GPL portable package topology mismatch")
    _yes(portable, "checksumVerified")
    _yes(portable, "licensePresent")
    return first


def _merge(s, c, *, post=False):
    m = _get(s, "merge")
    _same(m.get("head"), c["sha"], "source PR head")
    _same(m.get("base"), c["mainSha"], "source PR base")
    _same(m.get("currentMainSha"), c["mainSha"], "premerge live main")
    for key in ("approved", "checksPassed", "protectedDiff"):
        _yes(m, key)
    require(type(m.get("count")) is int and m["count"] == 1,
            "single reviewed source merge required")
    require(_sha(m.get("resultSha")) and m["resultSha"] != c["mainSha"],
            "final merged source SHA missing")
    if post:
        _same(m.get("postMergeMainSha"), m["resultSha"], "postmerge main SHA")
        _same(m.get("resultVersion"), c["version"], "merged source version")
        require(m.get("postMergeTagExists") is False,
                "tag may only be created after final merge checks")
    return m


def _draft(s, c, m, assets):
    d = _get(s, "draft")
    require(isinstance(d.get("id"), str) and bool(d["id"]),
            "simulated draft identity absent")
    _same(d.get("tag"), "v" + c["version"], "Draft version/tag")
    _same(d.get("tagTargetSha"), m["resultSha"], "tag target after merge")
    _same(d.get("sourceSha"), m["resultSha"], "Draft source")
    for key in ("isDraft", "releaseNotes", "complete"):
        _yes(d, key)
    require(_artifacts(d.get("assets"), c["version"]) == assets,
            "draft incomplete or wrong artifact bytes")
    return d


def _approval(s, c, m, assets):
    a = _get(s, "approval")
    require(a.get("kind") in ("unsigned", "signed"), "signing path missing")
    _same(a.get("version"), c["version"], "per-release approval version")
    _same(a.get("mergedSha"), m["resultSha"], "approved final source")
    require(_artifacts(a.get("assets"), c["version"]) == assets,
            "approval must bind exact asset SHA and size")
    require(isinstance(a.get("approver"), str) and bool(a["approver"])
            and isinstance(a.get("decidedAt"), str) and bool(a["decidedAt"]),
            "explicit approval provenance missing")
    if a["kind"] == "unsigned":
        _yes(a, "unsignedDisclosure")
        _yes(a, "smartScreenDisclosure")
    for key in ("rollbackVerified", "immutabilityVerified", "previousReleaseAvailable"):
        _yes(a, key)


def _post(s, c, m, d, assets):
    p = _get(s, "published")
    _same(p.get("id"), d["id"], "postpublication identity")
    _same(p.get("tag"), d["tag"], "published version/tag")
    _same(p.get("tagTargetSha"), m["resultSha"], "published tag source SHA")
    require(_artifacts(p.get("assets"), c["version"]) == assets,
            "published assets differ from verified Draft")
    for key in ("immutable", "isPublished", "postVerify", "previousReleaseAvailable"):
        _yes(p, key)
    _same(p.get("latestVersion"), c["version"], "published latest release")
    require(p.get("raceDetected") is False, "concurrent publish / recovery race")


def simulate(snapshot, policy, *, stop_after=None, resume=None):
    """Pure validation of an *imaginary* lifecycle. No GitHub access or writes."""
    require(isinstance(snapshot, dict), "immutable fixture required")
    require(isinstance(policy, dict) and policy.get("productionEnabled") is False
            and policy.get("distribution") == "github-release"
            and policy.get("signingDecision") == "unknown"
            and policy.get("rollbackVerified") is False,
            "production policy must remain fail-closed")
    # The real publication policy must reject this exact unchanged policy.
    try:
        publication_policy(policy)
    except ValueError as exc:
        require("disabled" in str(exc), "publication policy guard changed")
    else:
        raise ValueError("UNSAFE: real publication policy accepted the dry-run")
    require(stop_after is None or stop_after in STATES, "unknown simulation stop")
    fingerprint = hashlib.sha256(json.dumps(snapshot, sort_keys=True,
                              separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if resume is not None:
        require(isinstance(resume, dict) and resume.get("stage") in STATES
                and resume.get("fingerprint") == fingerprint,
                "stale/ambiguous restart or concurrent snapshot")
    trace = []
    c = m = d = assets = None
    for stage in STATES:
        fault = snapshot.get("fault")
        if isinstance(fault, dict) and fault.get("stage") == stage:
            raise ValueError("uncertain external state; query authoritative read-only snapshot")
        if stage == "candidate-qualified":
            c = _candidate(snapshot)
        elif stage == "release-built":
            _build(snapshot, c)
        elif stage == "artifacts-verified":
            assets = _packages(snapshot, c)
        elif stage == "merge-ready":
            m = _merge(snapshot, c)
        elif stage == "main-merged":
            m = _merge(snapshot, c, post=True)
        elif stage == "draft-ready":
            d = _draft(snapshot, c, m, assets)
        elif stage == "publish-ready":
            _approval(snapshot, c, m, assets)
        else:
            _post(snapshot, c, m, d, assets)
        trace.append(stage)
        if stop_after == stage:
            break
    return {"result": "SIMULATED_ONLY", "trace": trace, "githubMutations": False,
            "productionEnabled": False,
            "checkpoint": {"stage": trace[-1], "fingerprint": fingerprint}}


def assess_recovery(snapshot, policy, checkpoint, observed):
    """Read-only supervised recovery classification from a fresh authoritative snapshot.

    Never attempts a GitHub retry. A merge is source activation, not public binary
    activation. Postpublication inconsistency requires a new authorised version.
    """
    require(isinstance(checkpoint, dict) and checkpoint.get("stage") in STATES,
            "missing durable checkpoint")
    simulate(snapshot, policy, stop_after=checkpoint["stage"], resume=checkpoint)
    require(isinstance(observed, dict), "unknown GitHub state: manual inspection required")
    c = _get(snapshot, "candidate")
    m = _get(snapshot, "merge")
    stage_index = STATES.index(checkpoint["stage"])
    merged = stage_index >= STATES.index("main-merged")
    expected_main = m["resultSha"] if merged else c["mainSha"]
    _same(observed.get("mainSha"), expected_main, "recovery main/head")
    state = observed.get("releaseState")
    require(state in ("absent", "draft", "published"), "unresolved timeout/API state")
    if not merged:
        require(state == "absent", "release must not predate the source merge")
        return {"status": "PREMERGE_REVALIDATION", "public": False,
                "action": "requalify-current-main-no-write"}
    if state == "absent":
        return {"status": "BLOCKED_UNPUBLISHED", "public": False,
                "action": "supervised-idempotent-revalidation"}
    _same(observed.get("tagTargetSha"), m["resultSha"], "recovery tag target")
    _same(observed.get("draftId"), _get(snapshot, "draft")["id"],
          "recovery release identity")
    expected = _artifacts(_get(snapshot, "artifacts")["build1"], c["version"])
    if state == "draft":
        try:
            complete = _artifacts(observed.get("assets"), c["version"]) == expected
        except (TypeError, ValueError):
            complete = False
        return {"status": "UNPUBLISHED_DRAFT_VERIFIED" if complete else "BLOCKED_UNPUBLISHED",
                "public": False, "action": "supervised-idempotent-revalidation"}
    # Once published, never rewrite an immutable tag, Draft, or asset.
    require(observed.get("immutable") is True,
            "unexpected mutable published release: critical manual review")
    try:
        good = (observed.get("postVerify") is True and
                _artifacts(observed.get("assets"), c["version"]) == expected and
                observed.get("previousReleaseAvailable") is True and
                observed.get("latestVersion") == c["version"])
    except (TypeError, ValueError):
        good = False
    return {"status": "PUBLISHED_VERIFIED" if good else "CRITICAL_POSTPUBLISH_ATTENTION",
            "public": True, "action": "no-in-place-mutation"}
