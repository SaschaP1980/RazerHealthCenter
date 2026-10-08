#!/usr/bin/env python3
"""RHC-20 strict Candidate/release control-plane contracts. No network or writes.

All positive inputs are evidence snapshots, NOT publication authorization.
Only a separate trusted live orchestrator may derive these from remote GitHub,
native hardware attestation, rollback evidence and artifact hashes.
"""
import re
from rhc_orchestration_contracts import publication_policy, safe_ref
from rhc_release_contracts import SEMVER, assert_future_version, require

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
BOT = "github-actions[bot]"
CANDIDATE = ("rhc/preflight/linux", "rhc/preflight/windows", "rhc/preflight/candidate")
RELEASE = ("rhc/release/source", "rhc/release/portable", "rhc/release/verification")


def hash40(value):
    return isinstance(value, str) and SHA40.fullmatch(value) is not None


def hash64(value):
    return isinstance(value, str) and SHA64.fullmatch(value) is not None


def trusted_contexts(rows, required):
    require(isinstance(rows, list), "statuses absent/untrusted")
    latest = {}
    for record in rows:
        require(isinstance(record, dict), "invalid status record")
        name = record.get("context")
        if name in required and name not in latest:
            latest[name] = record
    require(set(latest) == set(required), "required hosted status missing")
    for name in required:
        s = latest[name]
        require(s.get("state") == "success"
                and s.get("creator", {}).get("login") == BOT,
                "pending/failed/untrusted status: " + name)
    return True


def assess_candidate_recovery(state):
    """A pure read-back classification: uncertain GitHub mutations NEVER retried."""
    s = state
    require(isinstance(s, dict), "candidate recovery snapshot missing")
    for x in ("mainSha", "expectedMainSha", "workSha", "expectedWorkSha"):
        require(hash40(s.get(x)), "missing candidate source SHA: " + x)
    require(s["mainSha"] == s["expectedMainSha"]
            and s["workSha"] == s["expectedWorkSha"], "concurrent main/Work advance")
    version = s.get("candidateVersion")
    require(isinstance(version, str) and SEMVER.fullmatch(version),
            "invalid four-part Candidate version")
    candidate = s.get("candidateSha")
    if candidate is None:
        require(s.get("candidateParentSha") is None
                and not s.get("statuses"), "orphaned Candidate checkpoints")
        require(s.get("runState") == "not-started", "ambiguous absent Candidate")
        return {"state": "READY_FOR_SINGLE_CREATE", "mayWrite": True,
                "reason": "ref confirmed absent before a single compare-and-create"}
    require(hash40(candidate), "malformed existing Candidate ref")
    require(s.get("candidateParentSha") == s["mainSha"]
            and s.get("candidateWorkSha") == s["workSha"],
            "existing Candidate origin mismatch: manual recovery required")
    if s.get("runState") != "success":
        return {"state": "ATTENTION_READ_ONLY", "mayWrite": False,
                "reason": "cancelled, pending, timed-out or unknown dispatch; inspect GitHub"}
    trusted_contexts(s.get("statuses"), CANDIDATE)
    return {"state": "QUALIFIED_NO_WRITE", "mayWrite": False,
            "reason": "exact Candidate already exists; no blind re-create"}


def validate_release_approval(snapshot):
    """Strong logical eligibility; evidence must come from real trusted sources."""
    s = snapshot
    require(isinstance(s, dict), "release evidence unavailable")
    p = s.get("policy")
    publication_policy(p)
    version, previous = s.get("version"), s.get("mainVersion")
    require(isinstance(version, str) and SEMVER.fullmatch(version),
            "invalid release version")
    require(isinstance(previous, str) and SEMVER.fullmatch(previous),
            "invalid main version")
    assert_future_version(version, previous)
    for k in ("mainSha", "candidateSha", "releaseSha",
              "sourceParentSha", "releaseParentSha"):
        require(hash40(s.get(k)), "missing exact source/parent: " + k)
    require(len({s["mainSha"], s["candidateSha"], s["releaseSha"]}) == 3,
            "source identities collide")
    require(s["sourceParentSha"] == s["mainSha"]
            and s["releaseParentSha"] == s["mainSha"], "stale base or ancestry")
    require(s.get("candidateBranch") == "candidate/v" + version
            and s.get("releaseBranch") == "release/v" + version
            and s.get("sourceTag") == "v" + version
            and s.get("tagExists") is False, "unsafe versioned release refs/tag")
    require(safe_ref(s["candidateBranch"], "candidate") == version
            and safe_ref(s["releaseBranch"], "release") == version,
            "invalid release reference")
    trusted_contexts(s.get("candidateStatuses"), CANDIDATE)
    trusted_contexts(s.get("releaseStatuses"), RELEASE)
    archive = s.get("package", {})
    require(archive.get("name") == "RazerHealthCenter-Portable-v" + version + ".zip"
            and hash64(archive.get("sha256"))
            and isinstance(archive.get("size"), int)
            and not isinstance(archive.get("size"), bool)
            and archive["size"] > 0
            and archive.get("files") == 7
            and archive.get("independentBuildsIdentical") is True
            and archive.get("checksumsVerified") is True,
            "missing true current seven-file reproducible artifact")
    approval = s.get("approval", {})
    require(approval.get("version") == version
            and approval.get("sourceSha") == s["candidateSha"]
            and approval.get("archiveSha256") == archive["sha256"],
            "explicit trust approval does not match exact candidate ZIP")
    require(approval.get("physicalRazerAcceptance") is True
            and approval.get("nativeRestoreTestPassed") is True,
            "native hardware/rollback evidence missing")
    prior, count = s.get("latestVersion"), s.get("historyCount")
    require(isinstance(count, int) and not isinstance(count, bool)
            and count >= 0, "published history untrusted")
    if prior is None:
        require(count == 0 and approval.get("firstReleaseRecoveryVerified") is True,
                "no verified first-release recovery")
    else:
        require(isinstance(prior, str) and SEMVER.fullmatch(prior)
                and tuple(map(int, version.split("."))) >
                    tuple(map(int, prior.split(".")))
                and count > 0
                and hash64(approval.get("previousZipSha256"))
                and approval.get("previousZipRetrievable") is True,
                "previous immutable ZIP/rollback unverified")
    if p["signingDecision"] == "signed-verified":
        require(approval.get("authenticodeVerified") is True
                and isinstance(approval.get("signerIdentity"), str)
                and len(approval["signerIdentity"].strip()) >= 3,
                "signed publisher chain not independently validated")
    else:
        require(approval.get("ownerExplicitApproval") is True
                and approval.get("smartScreenDisclosureAcknowledged") is True
                and isinstance(approval.get("approvalId"), str)
                and approval["approvalId"].strip(), "missing concrete unsigned Owner consent")
    return {"result": "ELIGIBLE_NOT_PUBLISHED", "version": version,
            "sourceSha": s["candidateSha"], "releaseSha": s["releaseSha"],
            "archiveSha256": archive["sha256"]}


def plan_release_transaction(snapshot):
    """Only a stage plan; no GitHub or archive writes from this function."""
    proof = validate_release_approval(snapshot)
    pr = snapshot.get("pr", {})
    expected = sorted(("downloads/README.md", "downloads/releases.json",
                       "downloads/latest.json",
                       "downloads/RazerHealthCenter-Portable-v" + proof["version"] + ".zip"))
    require(pr.get("state") == "open"
            and pr.get("baseSha") == snapshot["mainSha"]
            and pr.get("headSha") == snapshot["releaseSha"]
            and pr.get("approvedByGate") is True
            and isinstance(pr.get("changedFiles"), list)
            and sorted(pr["changedFiles"]) == expected,
            "release PR parent/status/scope mismatch")
    return {"state": "STAGED_UNPUBLISHED", "version": proof["version"],
            "releaseBranch": snapshot["releaseBranch"], "sourceSha": proof["sourceSha"],
            "releaseSha": proof["releaseSha"], "archiveSha256": proof["archiveSha256"],
            "changedFiles": expected}


def verify_postpublish(snapshot):
    """Only a read-back verdict; must be run after authorized live PR merge."""
    plan = plan_release_transaction(snapshot)
    require(snapshot.get("prMerged") is True
            and snapshot.get("mergedMainSha") == plan["releaseSha"]
            and snapshot.get("tagTargetSha") == plan["sourceSha"]
            and snapshot.get("publicVersion") == plan["version"]
            and snapshot.get("latestSha256") == plan["archiveSha256"]
            and snapshot.get("publishedFileSha256") == plan["archiveSha256"]
            and snapshot.get("immutableHistoryVerified") is True
            and snapshot.get("releaseBranchState") == "deleted-after-verified-merge",
            "postpublish SHA/tag/ZIP/history/branch verification incomplete")
    return {"result": "VERIFIED", "version": plan["version"],
            "releaseSha": plan["releaseSha"], "sha256": plan["archiveSha256"]}


def validate_main_rules(rules, required):
    """Current GitHub ruleset inspection, never infer an effective rule from wishes."""
    require(isinstance(rules, list) and isinstance(required, list),
            "main protection state unavailable")
    rtypes = {x.get("type") for x in rules if isinstance(x, dict)}
    status_rules = [x for x in rules if isinstance(x, dict)
                    and x.get("type") == "required_status_checks"]
    contexts = set()
    for rule in status_rules:
        for row in rule.get("parameters", {}).get("required_status_checks", []):
            if isinstance(row, dict) and isinstance(row.get("context"), str):
                contexts.add(row["context"])
    effect = "pull_request" in rtypes and set(required).issubset(contexts)
    return {"state": "EFFECTIVE" if effect else "ADMIN_CONFIGURATION_REQUIRED",
            "effective": effect, "mayClaimProtected": effect,
            "missingContexts": sorted(set(required) - contexts),
            "missingPRRule": "pull_request" not in rtypes}
