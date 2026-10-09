"""RHC-43: reusable interim unsigned qualification, not public deployment."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_reusable_interim as gate

OLD = "a" * 40
NEW = "b" * 40
ZIP = "c" * 64
EXE = "d" * 64


def snapshot():
    return {
        "mode": "interim-unsigned", "issue": 43, "ownerProcessAuthorized": True,
        "version": "3.0.8.2", "referenceVersion": "3.0.8.2",
        "changelogVersion": "3.0.8.2", "previousLatestVersion": "3.0.8.1",
        "releaseProfile": "version-only",
        "sourceSha": NEW, "mainSha": NEW,
        "archiveFile": "RazerHealthCenter-Portable-v3.0.8.2.zip",
        "archiveFiles": 7, "archiveSha256": ZIP, "archiveSize": 8621244,
        "exeSha256": EXE, "archiveReproducible": True,
        "twoIndependentPeBuilds": True, "twoIndependentZipBuilds": True,
        "linux": "SUCCESS", "nativeWindows": "SUCCESS",
        "exeSignature": "NotSigned",
        "policy": {"productionEnabled": False, "rollbackVerified": False,
                   "signingDecision": "unknown", "distribution": "repo-downloads"},
        "phaseB": {"hardware": "DEFERRED", "rollback": "DEFERRED",
                   "publisherTrust": "NOT_VERIFIED", "rulesetAdmin": "DEFERRED"},
        "previousReleaseCount": 1, "previousHistoryIntact": True,
        "existingTag": False, "existingArchive": False
    }


class ReusableInterimQualification(unittest.TestCase):
    def test_next_hotfix_accepted_without_claiming_a_published_release(self):
        result = gate.qualify(snapshot())
        self.assertEqual(result["version"], "3.0.8.2")
        self.assertEqual(result["previousLatestVersion"], "3.0.8.1")
        self.assertEqual(result["classification"], "INTERIM_UNSIGNED_UNCERTIFIED_RELEASE")
        self.assertEqual(result["status"], "ELIGIBLE_NOT_PUBLISHED")
        self.assertFalse(result["phaseBVerified"])
        self.assertIn("SmartScreen", result["disclosure"])
        self.assertEqual(result["releaseChangedPaths"], [
            "downloads/README.md",
            "downloads/RazerHealthCenter-Portable-v3.0.8.2.zip",
            "downloads/latest.json", "downloads/releases.json"])

    def test_next_patch_hotfix_must_be_exact_and_not_reused(self):
        for key, bad in (
            ("version", "3.0.8.1"), ("version", "3.0.8.3"),
            ("version", "3.0.8"), ("version", "3.0.9.0"),
            ("referenceVersion", "3.0.8.1"),
            ("changelogVersion", "3.0.8.1"),
            ("previousLatestVersion", "3.0.8.2"),
            ("previousLatestVersion", "invalid"),
            ("archiveFile", "RazerHealthCenter-Portable-v3.0.8.1.zip")):
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                gate.qualify(dict(snapshot(), **{key: bad}))

    def test_source_approval_and_history_are_real(self):
        for key, bad in (
            ("ownerProcessAuthorized", False), ("mode", "production"),
            ("issue", 0), ("sourceSha", OLD), ("mainSha", "bad"),
            ("archiveSha256", "bad"), ("exeSha256", "bad"),
            ("archiveFiles", 8), ("archiveSize", 0),
            ("archiveReproducible", False), ("twoIndependentPeBuilds", False),
            ("twoIndependentZipBuilds", False),
            ("linux", "SKIPPED"), ("nativeWindows", "PENDING"),
            ("exeSignature", "Unknown"), ("existingTag", True),
            ("existingArchive", True), ("previousHistoryIntact", False),
            ("previousReleaseCount", 0)):
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                gate.qualify(dict(snapshot(), **{key: bad}))

    def test_no_forged_external_acceptance_or_prod_policy_change(self):
        for key, bad in (
            ("hardware", "PASS"), ("rollback", "VERIFIED"),
            ("publisherTrust", "SIGNED"), ("rulesetAdmin", "EFFECTIVE")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                data = snapshot()
                data["phaseB"][key] = bad
                gate.qualify(data)
        for key, bad in (
            ("productionEnabled", True), ("rollbackVerified", True),
            ("signingDecision", "unsigned-approved"),
            ("distribution", "github-release")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                data = snapshot()
                data["policy"][key] = bad
                gate.qualify(data)

    def test_real_cli_consumer_and_rejected_snapshot(self):
        script = ROOT / "tools" / "rhc_reusable_interim.py"
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "evidence.json"
            target.write_text(json.dumps(snapshot()), encoding="utf-8")
            passed = subprocess.run(
                [sys.executable, str(script), "--snapshot", str(target)],
                capture_output=True, text=True)
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertIn("ELIGIBLE_NOT_PUBLISHED", passed.stdout)
            invalid = snapshot()
            invalid["previousHistoryIntact"] = False
            target.write_text(json.dumps(invalid), encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(script), "--snapshot", str(target)],
                capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("BLOCKED", failed.stderr)


if __name__ == "__main__":
    unittest.main()
