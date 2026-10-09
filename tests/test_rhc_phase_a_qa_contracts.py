"""RHC-29 Phase A test-only evidence: no publication or external acceptance."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_downloads as downloads
import rhc_phase_a_qa as qa

SHA = "a" * 40


class PhaseAQATests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = pathlib.Path(temporary.name)
        self.source = self.tmp / "repo"
        self.source.mkdir()
        (self.source / "model.go").write_text(
            'const (\nappVersion = "3.0.8.0"\nreferenceVersion = "3.0.8.0"\n)\n',
            encoding="utf-8")
        policy = self.source / "config/rhc-release-policy.json"
        policy.parent.mkdir()
        self.policy = {"productionEnabled": False, "signingDecision": "unknown",
                       "rollbackVerified": False, "distribution": "repo-downloads"}
        policy.write_text(json.dumps(self.policy), encoding="utf-8")
        for name in downloads.release.PORTABLE_ASSETS.values():
            p = self.source / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(name.encode("utf-8"))
        dest = self.source / "downloads"
        dest.mkdir()
        (dest / "releases.json").write_text(
            json.dumps({"schemaVersion": 1, "releases": []}) + "\n",
            encoding="utf-8")
        (dest / "README.md").write_text(downloads.render_readme([]),
                                        encoding="utf-8")
        for name in ("a", "b"):
            p = self.tmp / name
            p.mkdir()
            (p / "RazerHealthCenter.exe").write_bytes(b"MZ" + b"X" * 120)
        self.exe1 = self.tmp / "a/RazerHealthCenter.exe"
        self.exe2 = self.tmp / "b/RazerHealthCenter.exe"
        self.stage = self.tmp / "stage"

    def run_stage(self, **changes):
        args = dict(root=self.source, exe_a=self.exe1, exe_b=self.exe2,
                    stage=self.stage, source_sha=SHA)
        args.update(changes)
        with patch.object(qa, "checkout_sha", return_value=SHA):
            return qa.stage(**args)

    def verify(self):
        with patch.object(qa, "checkout_sha", return_value=SHA):
            return qa.verify(self.source, self.stage, SHA)

    def publish_fixture_release(self):
        """Create a real internally consistent prior release (not a fake latest pointer)."""
        version = "3.0.7.9"  # Earlier than the test source version 3.0.8.0.
        package = self.tmp / downloads.filename(version)
        downloads.make_lean_zip(self.source, self.exe1, package)
        record = downloads.stage_release(
            self.source / "downloads", package, version,
            "2026-10-09T00:00:00Z", "b" * 40)
        self.assertEqual(downloads.verify(self.source / "downloads")[0], record)
        self.assertEqual(
            json.loads((self.source / "downloads/latest.json").read_text()),
            record)
        return record

    def test_published_catalog_remains_immutable_during_test_only_qa(self):
        """A valid historic release must not block independent, nonpublishing QA."""
        published = self.publish_fixture_release()
        before = qa.inventory(self.source / "downloads")
        result = self.run_stage()  # RED on unfixed SHA: obsolete no-latest guard.
        self.assertEqual(result["classification"], "TEST_ONLY_NOT_RELEASE")
        self.assertEqual(result["phaseB"], qa.PHASE_B)
        self.assertEqual(self.verify(), result)
        self.assertEqual(qa.inventory(self.source / "downloads"), before)
        self.assertEqual(downloads.verify(self.source / "downloads"), [published])
        self.assertFalse((self.source / "downloads" / result["archive"]["file"]).exists())
        self.assertEqual(set(p.name for p in self.stage.iterdir()),
                         {result["archive"]["file"], "qa-evidence.json"})

    def test_published_catalog_corruption_still_blocks_qa(self):
        """A live catalog must be fully verified, never waved through."""
        record = self.publish_fixture_release()
        directory = self.source / "downloads"
        original = qa.inventory(directory)
        archive = directory / record["file"]
        latest = directory / "latest.json"
        readme = directory / "README.md"
        cases = (
            (archive, archive.read_bytes() + b"tampered prior ZIP"),
            (latest, b'{"schemaVersion":1,"version":"0.0.0.0"}'),
            (readme, b"tampered live release history"),
            (archive, None),  # Missing referenced immutable ZIP.
        )
        for path, payload in cases:
            with self.subTest(target=path.name, removed=payload is None):
                contents = path.read_bytes()
                if payload is None:
                    path.unlink()
                else:
                    path.write_bytes(payload)
                try:
                    with self.assertRaises(ValueError):
                        self.run_stage()
                    self.assertFalse(self.stage.exists())
                finally:
                    path.write_bytes(contents)
                self.assertEqual(qa.inventory(directory), original)
                self.assertEqual(downloads.verify(directory), [record])

    def test_qa_zip_is_reproducible_and_never_approved_or_published(self):
        before = qa.inventory(self.source / "downloads")
        result = self.run_stage()
        self.assertEqual(result["classification"], "TEST_ONLY_NOT_RELEASE")
        self.assertEqual(result["sourceSha"], SHA)
        self.assertEqual(result["phaseB"]["status"], "DISABLED")
        self.assertEqual(result["phaseB"]["hardwareAcceptance"], "NOT_VERIFIED")
        self.assertEqual(result["phaseB"]["rollback"], "NOT_VERIFIED")
        self.assertEqual(result["phaseB"]["ownerTrustApproval"], "NOT_AUTHORIZED")
        self.assertEqual(result["phaseB"]["productionRelease"], "BLOCKED")
        self.assertEqual(len(result["archive"]["files"]), 7)
        self.assertEqual(self.verify(), result)
        self.assertEqual(qa.inventory(self.source / "downloads"), before)
        self.assertFalse((self.source / "downloads/latest.json").exists())
        self.assertEqual(set(x.name for x in self.stage.iterdir()),
                         {result["archive"]["file"], "qa-evidence.json"})
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.run_stage()

    def test_wrong_commit_or_changed_real_policy_fails_before_stage(self):
        with patch.object(qa, "checkout_sha", return_value="b" * 40), \
             self.assertRaisesRegex(ValueError, "source SHA"):
            qa.stage(self.source, self.exe1, self.exe2, self.stage, SHA)
        self.assertFalse(self.stage.exists())
        path = self.source / "config/rhc-release-policy.json"
        for key, value in (("productionEnabled", True),
                           ("rollbackVerified", True),
                           ("signingDecision", "unsigned-approved"),
                           ("distribution", "github-releases")):
            with self.subTest(key=key):
                path.write_text(json.dumps(dict(self.policy, **{key: value})))
                with self.assertRaises(ValueError):
                    self.run_stage()
                self.assertFalse(self.stage.exists())
        path.write_text(json.dumps(self.policy))

    def test_mismatched_or_unsafe_binaries_and_source_paths(self):
        self.exe2.write_bytes(b"MZnot-the-same")
        with self.assertRaisesRegex(ValueError, "independent executable"):
            self.run_stage()
        self.assertFalse(self.stage.exists())
        self.exe2.write_bytes(self.exe1.read_bytes())
        with self.assertRaisesRegex(ValueError, "outside source"):
            self.run_stage(stage=self.source / "stage")
        with self.assertRaisesRegex(ValueError, "exact 40-hex"):
            self.run_stage(source_sha="invalid")

    def test_tampered_archive_and_manifest_cannot_be_claimed_pass(self):
        record = self.run_stage()
        path = self.stage / record["archive"]["file"]
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaises(ValueError):
            self.verify()
        path.unlink()
        with self.assertRaises(ValueError):
            self.verify()

    def test_fake_hardware_rollback_or_trust_status_is_rejected(self):
        self.run_stage()
        path = self.stage / "qa-evidence.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for key, value in (("hardwareAcceptance", "VERIFIED"),
                           ("rollback", "VERIFIED"),
                           ("ownerTrustApproval", "APPROVED"),
                           ("productionRelease", "AUTHORIZED"),
                           ("status", "ENABLED")):
            with self.subTest(key=key):
                fake = json.loads(json.dumps(original))
                fake["phaseB"][key] = value
                path.write_text(json.dumps(fake), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.verify()
        path.write_text(json.dumps(original), encoding="utf-8")
        self.assertEqual(self.verify(), original)

    def test_workflow_must_not_mutate_repository_or_claim_phase_b(self):
        workflow = (ROOT / ".github/workflows/rhc-phase-a-qa.yml").read_text(
            encoding="utf-8")
        for must in ("contents: read", "windows-2025", "ubuntu-24.04",
                     "needs: windows", "tools/rhc_phase_a_qa.py",
                     "test_rhc_phase_a_qa_contracts.py", "upload-artifact",
                     "Get-AuthenticodeSignature", "SOURCE_SHA", "github.sha"):
            self.assertIn(must, workflow)
        # Live public releases are valid input, but publishing or changing
        # any existing downloads in a TEST-ONLY QA job must be impossible.
        for must in ("rhc29-downloads-before.json",
                     'inventory("downloads") == before',
                     "git status --porcelain --untracked-files=all -- downloads",
                     "RHC29_PUBLISHED_DOWNLOADS_UNCHANGED=PASS",
                     "RHC29_FINAL_REPO_DOWNLOADS=UNCHANGED"):
            self.assertIn(must, workflow)
        for forbidden in ("contents: write", "gh release create", "git push",
                          "refs/tags", "EXPLICIT_OWNER_RHC22",
                          "productionEnabled=true",
                          'assert not pathlib.Path("downloads/latest.json").exists()',
                          "test ! -e downloads/latest.json",
                          'find downloads -maxdepth 1 -name'):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
