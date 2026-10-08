"""RHC-5: pure, adversarial, nonpublishing release-state rehearsal tests."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rhc_release_dry_run as dry

A, B, C = ("a" * 40, "b" * 40, "c" * 40)
H1, H2 = ("1" * 64, "2" * 64)
VERSION = "3.0.9"  # Hypothetical fixture only; application stays v3.0.8.


def asset(kind, digest):
    return {"name": "RazerHealthCenter-" + kind + "-v" + VERSION + ".zip",
            "sha256": digest, "size": 123456 if kind == "Source" else 345678}


def fixture():
    assets = [asset("Source", H1), asset("Portable", H2)]
    return {
        "candidate": {
            "mainSha": B, "parentSha": B, "sha": A, "currentMainSha": B,
            "version": VERSION, "previousVersion": "3.0.8",
            "issue": 5, "profile": "version-only",
            "ref": "candidate/v" + VERSION,
            "changedPaths": ["model.go", "CHANGELOG.md"],
            "statuses": [
                {"context": x, "sha": A, "state": "success"}
                for x in ("rhc/preflight/linux", "rhc/preflight/windows",
                          "rhc/preflight/candidate")
            ],
            "tagExists": False, "releaseExists": False
        },
        "build": {
            "candidateSha": A,
            "independent": True,
            "runs": [
                {"runner": "linux-a", "sha": A, "go": "1.23.2",
                 "build": "success", "goTests": True, "safety": True},
                {"runner": "linux-b", "sha": A, "go": "1.23.2",
                 "build": "success", "goTests": True, "safety": True}
            ],
            "windows": {"sha": A, "host": "windows-2025",
                        "psVersion": "5.1", "parser": True, "goTests": True,
                        "goVet": True, "repairSafety": True}
        },
        "artifacts": {
            "candidateSha": A,
            "build1": assets, "build2": copy.deepcopy(assets),
            "source": {"files": ["LICENSE", "model.go", "go.mod", "build.sh"],
                       "forbiddenFound": False},
            "portable": {"files": 8, "directories": 12,
                         "checksumVerified": True, "licensePresent": True}
        },
        "merge": {"head": A, "base": B, "currentMainSha": B, "approved": True,
                  "checksPassed": True, "protectedDiff": True, "count": 1,
                  "resultSha": C, "resultVersion": VERSION,
                  "postMergeMainSha": C, "postMergeTagExists": False},
        "draft": {"id": "simulated-draft-1", "tag": "v" + VERSION,
                  "tagTargetSha": C, "sourceSha": C, "isDraft": True,
                  "releaseNotes": True, "complete": True,
                  "assets": copy.deepcopy(assets)},
        "approval": {"kind": "unsigned", "version": VERSION, "mergedSha": C,
                     "assets": copy.deepcopy(assets), "approver": "owner",
                     "decidedAt": "SIMULATED-NOT-REAL",
                     "unsignedDisclosure": True, "smartScreenDisclosure": True,
                     "rollbackVerified": True, "immutabilityVerified": True,
                     "previousReleaseAvailable": True},
        "published": {"id": "simulated-draft-1", "tag": "v" + VERSION,
                      "tagTargetSha": C, "assets": copy.deepcopy(assets),
                      "immutable": True, "isPublished": True,
                      "postVerify": True, "latestVersion": VERSION,
                      "previousReleaseAvailable": True, "raceDetected": False}
    }


def policy():
    return {"productionEnabled": False, "distribution": "github-release",
            "signingDecision": "unknown", "rollbackVerified": False}


class DryRun(unittest.TestCase):
    def test_complete_trace_and_no_activation(self):
        result = dry.simulate(fixture(), policy())
        self.assertEqual(result["trace"], list(dry.STATES))
        self.assertEqual(result["result"], "SIMULATED_ONLY")
        self.assertFalse(result["githubMutations"])
        self.assertFalse(result["productionEnabled"])

    def test_every_stage_individually_stoppable(self):
        for stage in dry.STATES:
            with self.subTest(stage=stage):
                result = dry.simulate(fixture(), policy(), stop_after=stage)
                self.assertEqual(result["trace"][-1], stage)
                self.assertFalse(result["githubMutations"])

    def test_resume_idempotent_exact_fingerprint(self):
        good = fixture()
        first = dry.simulate(good, policy(), stop_after="main-merged")
        resumed = dry.simulate(good, policy(), resume=first["checkpoint"])
        self.assertEqual(resumed["trace"], list(dry.STATES))
        self.assertFalse(resumed["githubMutations"])
        again = dry.simulate(good, policy(), resume=resumed["checkpoint"])
        self.assertEqual(again["checkpoint"], resumed["checkpoint"])
        changed = fixture()
        changed["merge"]["postMergeMainSha"] = A
        self.assertRaises(ValueError, dry.simulate, changed, policy(),
                          resume=first["checkpoint"])

    def test_baseline_release_policy_must_remain_disabled(self):
        for k, v in [("productionEnabled", True),
                     ("distribution", "repository-pointer"),
                     ("signingDecision", "unsigned-approved"),
                     ("rollbackVerified", True)]:
            with self.subTest(field=k):
                p = policy()
                p[k] = v
                self.assertRaises(ValueError, dry.simulate, fixture(), p)

    def test_candidate_rejects_stale_identity_and_statuses(self):
        mutations = [
            ("candidate", "mainSha", A),
            ("candidate", "parentSha", A),
            ("candidate", "currentMainSha", A),
            ("candidate", "sha", "short"),
            ("candidate", "version", "3.0.8"),
            ("candidate", "ref", "candidate/v3.0.8"),
            ("candidate", "issue", 0),
            ("candidate", "profile", "bad"),
            ("candidate", "changedPaths", ["model.go"]),
            ("candidate", "tagExists", True),
            ("candidate", "releaseExists", True)
        ]
        for section, key, value in mutations:
            with self.subTest(key=key):
                s = fixture()
                s[section][key] = value
                self.assertRaises(ValueError, dry.simulate, s, policy())
        for status in ("pending", "failure", "skipped", None):
            with self.subTest(status=status):
                s = fixture()
                s["candidate"]["statuses"][1]["state"] = status
                self.assertRaises(ValueError, dry.simulate, s, policy())
        for statuses in ([], [fixture()["candidate"]["statuses"][0]]):
            s = fixture()
            s["candidate"]["statuses"] = statuses
            self.assertRaises(ValueError, dry.simulate, s, policy())
        for new_sha in (B, None):
            s = fixture()
            s["candidate"]["statuses"][1]["sha"] = new_sha
            self.assertRaises(ValueError, dry.simulate, s, policy())
        s = fixture()
        s["candidate"]["statuses"].append(s["candidate"]["statuses"][0])
        self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_independent_build_windows_gates(self):
        bad = [
            ("build", "candidateSha", B), ("build", "independent", False),
        ]
        for section, key, value in bad:
            s = fixture()
            s[section][key] = value
            self.assertRaises(ValueError, dry.simulate, s, policy())
        for key, value in [("sha", B), ("go", "1.22.0"), ("build", "failure"),
                           ("goTests", False), ("safety", False)]:
            s = fixture()
            s["build"]["runs"][1][key] = value
            self.assertRaises(ValueError, dry.simulate, s, policy())
        for key, value in [("sha", B), ("host", "linux"), ("psVersion", "7.4"),
                           ("parser", False), ("goTests", False),
                           ("goVet", False), ("repairSafety", False)]:
            s = fixture()
            s["build"]["windows"][key] = value
            self.assertRaises(ValueError, dry.simulate, s, policy())
        s = fixture()
        s["build"]["runs"][1]["runner"] = "linux-a"
        self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_artifact_integrity_and_package_safety(self):
        changes = [
            ("artifacts", "candidateSha", B),
            ("artifacts", "build2", [asset("Source", H1)]),
            ("artifacts", "build1", [asset("Source", H1), asset("Source", H2)]),
        ]
        for sec, key, value in changes:
            s = fixture()
            s[sec][key] = value
            self.assertRaises(ValueError, dry.simulate, s, policy())
        for key, val in [("sha256", "deadbeef"), ("size", 0),
                         ("name", "evil.zip")]:
            s = fixture()
            s["artifacts"]["build2"][1][key] = val
            self.assertRaises(ValueError, dry.simulate, s, policy())
        for name in ("RazerOldSource.zip", "runtime.exe", "BUILD-FULL.log",
                     "forensics/private.json"):
            s = fixture()
            s["artifacts"]["source"]["files"].append(name)
            self.assertRaises(ValueError, dry.simulate, s, policy())
        for field, value in [("files", 7), ("directories", 11),
                             ("checksumVerified", False),
                             ("licensePresent", False)]:
            s = fixture()
            s["artifacts"]["portable"][field] = value
            self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_single_merge_and_current_main(self):
        for key, val in [("head", B), ("base", A), ("currentMainSha", A),
                         ("approved", False), ("checksPassed", False),
                         ("protectedDiff", False), ("count", 2),
                         ("resultSha", "short"), ("resultVersion", "3.0.8"),
                         ("postMergeMainSha", B), ("postMergeTagExists", True)]:
            with self.subTest(field=key):
                s = fixture()
                s["merge"][key] = val
                self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_draft_cannot_precede_merge_or_be_incomplete(self):
        for key, val in [("id", ""), ("tag", "v3.0.8"),
                         ("tagTargetSha", A), ("sourceSha", A),
                         ("isDraft", False), ("releaseNotes", False),
                         ("complete", False), ("assets", [asset("Source", H1)])]:
            with self.subTest(field=key):
                s = fixture()
                s["draft"][key] = val
                self.assertRaises(ValueError, dry.simulate, s, policy())
        s = fixture()
        s["draft"]["assets"].append(asset("Source", H1))
        self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_unsigned_approval_requires_exact_artifact_specific_consent(self):
        for key, val in [("kind", "generic"), ("version", "3.0.8"),
                         ("mergedSha", A), ("assets", [asset("Source", H1)]),
                         ("approver", ""), ("decidedAt", ""),
                         ("unsignedDisclosure", False), ("smartScreenDisclosure", False),
                         ("rollbackVerified", False), ("immutabilityVerified", False),
                         ("previousReleaseAvailable", False)]:
            with self.subTest(field=key):
                s = fixture()
                s["approval"][key] = val
                self.assertRaises(ValueError, dry.simulate, s, policy())
        s = fixture()
        s["approval"]["assets"][0]["sha256"] = "f" * 64
        self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_postverify_and_immutable_recovery_fail_closed(self):
        for key, val in [("id", "other"), ("tag", "v3.0.8"),
                         ("tagTargetSha", A), ("assets", []),
                         ("immutable", False), ("isPublished", False),
                         ("postVerify", False), ("latestVersion", "3.0.8"),
                         ("previousReleaseAvailable", False),
                         ("raceDetected", True)]:
            with self.subTest(field=key):
                s = fixture()
                s["published"][key] = val
                self.assertRaises(ValueError, dry.simulate, s, policy())

    def test_runner_timeout_and_conflicting_checkpoint(self):
        s = fixture()
        s["fault"] = {"stage": "draft-ready", "kind": "timeout"}
        self.assertRaises(ValueError, dry.simulate, s, policy())
        for bad in ({"stage": "draft-ready", "fingerprint": "bad"},
                    {"stage": "bogus", "fingerprint": "f" * 64}):
            self.assertRaises(ValueError, dry.simulate, fixture(), policy(), resume=bad)


if __name__ == "__main__":
    unittest.main()
