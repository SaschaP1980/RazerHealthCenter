"""RHC-20: independent fail-closed, resumable Candidate + Release transaction contracts."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from rhc_release_transaction import (
    assess_candidate_recovery, validate_release_approval,
    plan_release_transaction, verify_postpublish, validate_main_rules,
)

A, B, C = "a" * 40, "b" * 40, "c" * 40
D, E = "d" * 64, "e" * 64
VERSION = "3.0.8.1"
CANDIDATE_CONTEXTS = ("rhc/preflight/linux", "rhc/preflight/windows", "rhc/preflight/candidate")
RELEASE_CONTEXTS = ("rhc/release/source", "rhc/release/portable", "rhc/release/verification")


def statuses(names, state="success"):
    return [{"context": n, "state": state, "creator": {"login": "github-actions[bot]"}}
            for n in names]


def release_case():
    return {
        "mainSha": A, "candidateSha": B, "releaseSha": C,
        "mainVersion": "3.0.8.0", "version": VERSION,
        "candidateBranch": "candidate/v" + VERSION,
        "releaseBranch": "release/v" + VERSION,
        "sourceParentSha": A, "releaseParentSha": A,
        "sourceTag": "v" + VERSION, "tagExists": False,
        "latestVersion": None, "historyCount": 0,
        "candidateStatuses": statuses(CANDIDATE_CONTEXTS),
        "releaseStatuses": statuses(RELEASE_CONTEXTS),
        "package": {"name": "RazerHealthCenter-Portable-v" + VERSION + ".zip",
                    "size": 777, "sha256": D, "files": 7,
                    "independentBuildsIdentical": True, "checksumsVerified": True},
        "policy": {"productionEnabled": True, "distribution": "repo-downloads",
                   "signingDecision": "unsigned-approved", "rollbackVerified": True},
        "approval": {"version": VERSION, "sourceSha": B, "archiveSha256": D,
                     "physicalRazerAcceptance": True, "nativeRestoreTestPassed": True,
                     "firstReleaseRecoveryVerified": True,
                     "ownerExplicitApproval": True, "smartScreenDisclosureAcknowledged": True,
                     "approvalId": "OWNER-RELEASE-2026-10-08-VERSION-BOUND"},
        "pr": {"state": "open", "baseSha": A, "headSha": C,
               "approvedByGate": True, "changedFiles": [
                   "model.go", "CHANGELOG.md",
                   "downloads/RazerHealthCenter-Portable-v3.0.8.1.zip",
                   "downloads/releases.json", "downloads/latest.json",
                   "downloads/README.md"]},
    }


class CandidateRecovery(unittest.TestCase):
    def test_missing_branch_is_safe_to_create_only_for_live_exact_main(self):
        c = dict(mainSha=A, expectedMainSha=A, workSha=B, expectedWorkSha=B,
                 candidateSha=None, candidateParentSha=None,
                 candidateVersion=VERSION, statuses=[], runState="not-started")
        self.assertEqual(assess_candidate_recovery(c)["state"], "READY_FOR_SINGLE_CREATE")
        for field, value in (("mainSha", C), ("workSha", C)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                assess_candidate_recovery(dict(c, **{field: value}))

    def test_lost_dispatch_crash_and_repeated_run_are_read_only(self):
        c = dict(mainSha=A, expectedMainSha=A, workSha=B, expectedWorkSha=B,
                 candidateSha=C, candidateParentSha=A,
                 candidateVersion=VERSION, candidateWorkSha=B,
                 statuses=[], runState="unknown")
        self.assertEqual(assess_candidate_recovery(c)["state"], "ATTENTION_READ_ONLY")
        self.assertFalse(assess_candidate_recovery(c)["mayWrite"])
        c["runState"] = "success"
        c["statuses"] = statuses(CANDIDATE_CONTEXTS)
        self.assertEqual(assess_candidate_recovery(c)["state"], "QUALIFIED_NO_WRITE")
        for key, bad in (("candidateParentSha", B), ("candidateWorkSha", A),
                         ("mainSha", B), ("runState", "cancelled")):
            with self.subTest(key=key):
                changed = dict(c, **{key: bad})
                if key == "runState":
                    self.assertEqual(assess_candidate_recovery(changed)["state"], "ATTENTION_READ_ONLY")
                else:
                    with self.assertRaises(ValueError):
                        assess_candidate_recovery(changed)

    def test_stale_lost_hosted_status_never_qualifies(self):
        c = dict(mainSha=A, expectedMainSha=A, workSha=B, expectedWorkSha=B,
                 candidateSha=C, candidateParentSha=A, candidateWorkSha=B,
                 candidateVersion=VERSION, runState="success", statuses=statuses(CANDIDATE_CONTEXTS))
        for changed in (statuses(CANDIDATE_CONTEXTS[:2]),
                        statuses(CANDIDATE_CONTEXTS, "pending"),
                        [{"context": x, "state": "success", "creator": {"login": "untrusted"}}
                         for x in CANDIDATE_CONTEXTS]):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                assess_candidate_recovery(dict(c, statuses=changed))


class ReleaseTransaction(unittest.TestCase):
    def test_approved_transaction_plan_and_postverification(self):
        c = release_case()
        self.assertEqual(validate_release_approval(c)["result"], "ELIGIBLE_NOT_PUBLISHED")
        plan = plan_release_transaction(c)
        self.assertEqual(plan["releaseBranch"], "release/v3.0.8.1")
        self.assertEqual(plan["changedFiles"], sorted(c["pr"]["changedFiles"]))
        self.assertEqual(plan["state"], "STAGED_UNPUBLISHED")
        # A GitHub merge commit has a distinct SHA and two ordered parents.
        after = dict(c, pr=dict(c["pr"], state="closed", merged=True),
                     mergedMainSha="f" * 40, mergeParentShas=[A, C],
                     tagTargetSha=B, publicVersion=VERSION,
                     latestSha256=D, publishedFileSha256=D, immutableHistoryVerified=True,
                     releaseBranchState="deleted-after-verified-merge", prMerged=True)
        self.assertEqual(verify_postpublish(after)["result"], "VERIFIED")
        for key,bad in (("tagTargetSha", A), ("latestSha256", E),
                        ("publishedFileSha256", E), ("releaseBranchState", "still-live"),
                        ("immutableHistoryVerified", False)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                verify_postpublish(dict(after,**{key:bad}))

    def test_rejects_real_disabled_policy_and_missing_native_owner_evidence(self):
        c = release_case()
        for key,bad in (("productionEnabled",False),("signingDecision","unknown"),
                        ("rollbackVerified",False),("distribution","github-releases")):
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_release_approval(dict(c,policy=dict(c["policy"],**{key:bad})))
        for key,bad in (("sourceSha", A),("archiveSha256",E),
                        ("physicalRazerAcceptance", False),
                        ("nativeRestoreTestPassed",False),
                        ("ownerExplicitApproval",False),
                        ("smartScreenDisclosureAcknowledged",False),
                        ("firstReleaseRecoveryVerified",False)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_release_approval(dict(c,approval=dict(c["approval"],**{key:bad})))

    def test_fail_closed_on_stale_sha_missing_bot_provenance_duplicate_or_conflict(self):
        c = release_case()
        for k,bad in (("sourceParentSha",B), ("releaseParentSha",B),
                      ("tagExists",True),("candidateSha","invalid"),("historyCount",1),
                      ("latestVersion",VERSION),("releaseBranch","release/v3.0.8.2")):
            with self.subTest(k=k),self.assertRaises(ValueError):
                validate_release_approval(dict(c,**{k:bad}))
        for key in ("candidateStatuses","releaseStatuses"):
            for changed in ([], statuses(CANDIDATE_CONTEXTS[:1]),
                            [{"context":x,"state":"success","creator":{"login":"malicious"}}
                             for x in (CANDIDATE_CONTEXTS if key=="candidateStatuses"
                                       else RELEASE_CONTEXTS)]):
                with self.subTest(key=key,changed=changed),self.assertRaises(ValueError):
                    validate_release_approval(dict(c,**{key:changed}))
        for delta in (dict(state="closed"),dict(baseSha=B),dict(headSha=A),
                      dict(approvedByGate=False),dict(changedFiles=["downloads/latest.json"])):
            with self.subTest(delta=delta),self.assertRaises(ValueError):
                plan_release_transaction(dict(c,pr=dict(c["pr"],**delta)))

    def test_immutable_existing_history_requires_increment_and_previous(self):
        c = release_case()
        c["historyCount"] = 1
        c["latestVersion"] = "3.0.8.0"
        c["approval"]["previousZipSha256"] = E
        c["approval"]["previousZipRetrievable"] = True
        self.assertEqual(validate_release_approval(c)["result"],"ELIGIBLE_NOT_PUBLISHED")
        c["approval"]["previousZipRetrievable"]=False
        with self.assertRaises(ValueError):
            validate_release_approval(c)

    def test_signed_version_specific_path_cannot_fake_owner_approval(self):
        c = release_case()
        c["policy"]["signingDecision"]="signed-verified"
        with self.assertRaises(ValueError):
            validate_release_approval(c)
        c["approval"].update(authenticodeVerified=True, signerIdentity="Trusted Publisher")
        self.assertEqual(validate_release_approval(c)["result"],"ELIGIBLE_NOT_PUBLISHED")


class MainProtection(unittest.TestCase):
    def test_actual_ruleset_must_be_required_checks_and_pr_or_explicit_blocker(self):
        want = ["rhc/infra/linux", "rhc/infra/windows"]
        rules = [{"type": "pull_request"},
                 {"type": "required_status_checks", "parameters": {
                     "required_status_checks":[{"context": x} for x in want]}}]
        self.assertTrue(validate_main_rules(rules, want)["effective"])
        result = validate_main_rules([{"type":"deletion"}, {"type":"non_fast_forward"}], want)
        self.assertEqual(result["state"], "ADMIN_CONFIGURATION_REQUIRED")
        self.assertFalse(result["effective"])
        self.assertFalse(result["mayClaimProtected"])


if __name__ == "__main__":
    unittest.main()
