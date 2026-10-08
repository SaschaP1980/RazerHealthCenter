#!/usr/bin/env python3
"""RHC-12 immutable repo-downloads preactivation PLAN, with ZERO GitHub writes.

This is evidence validation, not a publisher, signer, approval grant or physical
hardware verifier. Production is blocked until the external evidence exists.
"""
import re
from rhc_release_contracts import require, assert_future_version, SEMVER
from rhc_orchestration_contracts import exact_statuses, publication_policy
from rhc_orchestration_contracts import REQUIRED_CANDIDATE_CONTEXTS, REQUIRED_RELEASE_CONTEXTS

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")

def evaluate(snapshot):
    s = snapshot
    require(isinstance(s, dict), "release snapshot missing")
    policy = s.get("policy")
    publication_policy(policy)
    v = s.get("version")
    prior = s.get("mainVersion")
    require(isinstance(v, str) and bool(SEMVER.fullmatch(v)), "bad release version")
    require(isinstance(prior, str) and bool(SEMVER.fullmatch(prior)), "bad main version")
    assert_future_version(v, prior)
    main, candidate, release = (s.get(x) for x in
                                 ("observedMainSha", "candidateSha", "releaseSha"))
    require(all(isinstance(x, str) and HEX40.fullmatch(x) for x in
                (main, candidate, release)), "missing exact source SHA")
    require(s.get("expectedMainSha") == main, "main advanced since release staging")
    require(candidate != release and release != main and candidate != main,
            "source/release identity collision")
    require(s.get("candidateBranch") == "candidate/v" + v
            and s.get("releaseBranch") == "release/v" + v, "wrong versioned refs")
    require(s.get("releaseBranchAvailable") is True, "release branch conflict")
    require(s.get("releaseSourceSha") == candidate, "release source provenance mismatch")
    exact_statuses(s.get("candidateStatuses"), REQUIRED_CANDIDATE_CONTEXTS)
    exact_statuses(s.get("releaseStatuses"), REQUIRED_RELEASE_CONTEXTS)
    archive = s.get("archive", {})
    digest = archive.get("sha256")
    require(isinstance(digest,str) and HEX64.fullmatch(digest)
            and isinstance(archive.get("size"),int) and archive["size"] > 0,
            "release archive hash/size missing")
    require(archive.get("name") == "RazerHealthCenter-Portable-v" + v + ".zip",
            "noncanonical archive filename")
    require(archive.get("leanSevenFiles") is True and
            archive.get("noNestedZip") is True and
            archive.get("manifestVerified") is True and
            archive.get("independentBuildsIdentical") is True,
            "seven-file reproducibility/integrity unproven")
    require(s.get("sourceTagSha") == candidate and
            s.get("tagExists") is False, "source tag not uniquely anchored")
    require(s.get("readOnlyCandidate") is True
            and s.get("physicalRazerAcceptance") is True, "native product evidence missing")
    previous = s.get("publicVersion")
    rollback = s.get("rollbackEvidence", {})
    # In the first official release, require an independently identified
    # recoverable baseline: do not fabricate a public predecessor.
    if previous is None:
        require(s.get("releasedCount") == 0 and s.get("latestExists") is False,
                "phantom latest/index before first release")
        require(rollback.get("firstReleaseRecoveryVerified") is True,
                "first public release recovery plan unverified")
    else:
        require(bool(SEMVER.fullmatch(previous)) and
                tuple(map(int,previous.split("."))) < tuple(map(int,v.split("."))),
                "invalid public predecessor")
        require(s.get("latestVersion") == previous and s.get("releasedCount",0) > 0,
                "public history or latest pointer drift")
        require(rollback.get("previousVersion") == previous and
                isinstance(rollback.get("previousZipSha"),str)
                and bool(HEX64.fullmatch(rollback["previousZipSha"]))
                and rollback.get("previousZipRetrievable") is True,
                "previous immutable ZIP rollback unverified")
    require(rollback.get("nativeRestoreTestPassed") is True,
            "rollback tested recovery missing")
    trust = s.get("windowsTrust", {})
    require(trust.get("version") == v and trust.get("sourceSha") == candidate
            and trust.get("archiveSha256") == digest, "trust not artifact bound")
    if policy["signingDecision"] == "signed-verified":
        require(trust.get("authenticodeVerified") is True and
                isinstance(trust.get("signerIdentity"),str) and
                len(trust["signerIdentity"]) >= 3,
                "signer identity/proof missing")
    else:
        require(policy["signingDecision"] == "unsigned-approved" and
                trust.get("ownerExplicitApproval") is True and
                trust.get("smartScreenDisclosureAcknowledged") is True and
                isinstance(trust.get("approvalId"),str) and
                bool(trust["approvalId"].strip()),
                "unsigned owner/SmartScreen approval missing")
    require(s.get("releasePrNotMerged") is True
            and s.get("immutableHistoryVerified") is True,
            "release history/PR transaction not ready")
    return {"result":"PREACTIVATION_ELIGIBLE_NOT_PUBLISHED",
            "version":v,"sourceSha":candidate,"releaseSha":release,
            "artifact":archive["name"],"sha256":digest,
            "nextAction":"single reviewed release PR merge, then independent postpublish verification"}
