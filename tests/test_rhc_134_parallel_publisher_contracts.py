"""RHC-134: Publisher parallel prechecks without weakening native artifact attestation."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / ".github/workflows/rhc-reusable-interim-release.yml"
SMOKE = ROOT / ".github/workflows/rhc134-parallel-smoke.yml"
HELPER = ROOT / "tools/rhc134_artifact_wait.py"

class ParallelPublisher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = PUBLISHER.read_text(encoding="utf-8")
        cls.windows = cls.script.split("\n  windows:\n", 1)[1].split("\n  stage:\n", 1)[0]

    def test_single_native_windows_runner_starts_parallel_to_linux(self):
        self.assertNotRegex(self.windows, r"(?m)^    needs: linux$")
        self.assertEqual(self.script.count("\n  windows:\n"), 1)
        self.assertIn("runs-on: windows-2025", self.windows)
        self.assertIn("needs: [linux, windows]", self.script)
        self.assertIn("RHC_REUSABLE_LINUX_DOUBLE_BUILD=PASS", self.script)
        self.assertIn("if-no-files-found: error", self.script)

    def test_full_ps51_safety_precedes_bounded_wait_and_real_zip_attestation(self):
        win = self.windows
        for required in ("go test ./...", "go vet ./...", "validate_repair_safety.py",
                         "validate_v307_ps51_appengine_diagnostic.py",
                         "validate_v306_appengine_recovery.py",
                         "rhc134_artifact_wait.py", "actions/download-artifact@",
                         "Expand-Archive", "Get-AuthenticodeSignature",
                         "Get-FileHash", "NotSigned", "RHC_REUSABLE_WINDOWS=PASS"):
            self.assertIn(required, win)
        a = win.index("go test ./...")
        b = win.index("rhc134_artifact_wait.py")
        c = win.index("actions/download-artifact@")
        d = win.index("Get-AuthenticodeSignature")
        self.assertLess(a,b)
        self.assertLess(b,c)
        self.assertLess(c,d)
        self.assertIn("RHC134_WINDOWS_PRECHECK=PASS", win)
        self.assertIn("RHC134_WINDOWS_ARTIFACT_ATTESTATION=PASS", win)
        self.assertIn("needs: [linux, windows]", self.script)

    def test_helper_is_bounded_and_sha_artifact_identity_locked(self):
        s = HELPER.read_text(encoding="utf-8")
        for x in ("GITHUB_RUN_ID", "GITHUB_SHA", "GITHUB_REPOSITORY",
                  "RHC_REUSABLE-INTERNAL-STAGE-", "artifact", "expired",
                  "size_in_bytes", "max_attempts", "GH_TOKEN"):
            self.assertIn(x,s)
        self.assertNotIn("gh workflow run",s)
        self.assertNotIn("gh api -X POST",s)

    def test_nonpublishing_integration_smoke_does_not_write_release(self):
        s = SMOKE.read_text(encoding="utf-8")
        for x in ("work/RHC-134", "runs-on: ubuntu-24.04",
                  "runs-on: windows-2025", "rhc134_artifact_wait.py",
                  "Get-AuthenticodeSignature", "NotSigned",
                  "RHC134_SMOKE_WINDOWS=PASS", "RHC134_SMOKE_LINUX=PASS"):
            self.assertIn(x,s)
        for danger in ("pull_request_target:", "contents: write",
                       "pull-requests: write", "gh pr create",
                       "gh workflow run", "git push", "stage_release("):
            self.assertNotIn(danger,s)
        self.assertRegex(s,r"(?ms)^  windows:.*^  linux:" if False else r"(?m)^  windows:")
        self.assertIn("if-no-files-found: error",s)

class ArtifactGateAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        import rhc134_artifact_wait as helper
        cls.gate = helper
        cls.sha = "a" * 40
        cls.name = "RHC_REUSABLE-INTERNAL-STAGE-" + cls.sha

    def good(self):
        return {"total_count": 1, "artifacts": [
            {"name": self.name, "id": 42, "expired": False,
             "size_in_bytes": 600, "archive_download_url":
             "https://api.github.com/repos/owner/repo/actions/artifacts/42/zip"}]}

    def test_exact_same_name_positive_and_other_name_never_qualifies(self):
        self.assertEqual(self.gate.select_artifact(self.good(), self.name), 42)
        self.assertIsNone(self.gate.select_artifact(self.good(), self.name[:-1] + "b"))

    def test_missing_tampered_duplicate_or_unauthorized_metadata_blocks(self):
        cases = []
        for key, bad in (("id", 0), ("expired", True), ("expired", None),
                         ("size_in_bytes", 0),
                         ("archive_download_url", "http://example.org/a"),
                         ("archive_download_url", None)):
            x = self.good()
            x["artifacts"][0][key] = bad
            cases.append(x)
        same = self.good()
        same["artifacts"].append(dict(same["artifacts"][0]))
        same["total_count"] = 2
        cases.append(same)
        truncated = self.good()
        truncated["total_count"] = 101
        cases.append(truncated)
        inconsistent = self.good()
        inconsistent["total_count"] = 2
        cases.append(inconsistent)
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.gate.select_artifact(bad, self.name)

    def test_bounded_wait_never_accepts_wrong_ref_or_unavailable_linux(self):
        good=self.good()
        empty={"total_count": 0, "artifacts": []}
        calls=[]
        def fetch(repo, run):
            calls.append((repo,run))
            return empty if len(calls) < 3 else good
        self.assertEqual(self.gate.wait_for_artifact(
            repository="owner/repo", run_id="123", sha=self.sha,
            prefix="RHC_REUSABLE-INTERNAL-STAGE-", max_attempts=3,
            interval=0.1, fetcher=fetch, sleeper=lambda _:None),42)
        self.assertEqual(len(calls),3)
        with self.assertRaises(TimeoutError):
            self.gate.wait_for_artifact(
                repository="owner/repo",run_id="123",sha=self.sha,
                prefix="RHC_REUSABLE-INTERNAL-STAGE-",max_attempts=2,
                interval=0.1,fetcher=lambda repo,run:empty,sleeper=lambda _:None)
        for wrong in (dict(sha="not-a-sha"), dict(prefix="untrusted-"),
                      dict(run_id="0"),dict(max_attempts=0),dict(max_attempts=500)):
            params=dict(repository="owner/repo",run_id="123",sha=self.sha,
                        prefix="RHC_REUSABLE-INTERNAL-STAGE-",max_attempts=2,
                        interval=0.1,fetcher=lambda repo,run:good,sleeper=lambda _:None)
            params.update(wrong)
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                self.gate.wait_for_artifact(**params)


if __name__ == "__main__":
    unittest.main()
