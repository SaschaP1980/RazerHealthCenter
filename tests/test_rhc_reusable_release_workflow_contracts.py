"""RHC-43: a reusable interim release is a real staged GitHub transaction."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/rhc-reusable-interim-release.yml"


class ReusablePublisherContract(unittest.TestCase):
    def test_new_workflow_is_version_independent_and_noncertified(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        for needle in (
            "name: RHC Reusable Interim Unsigned Release",
            "branches: [main]", "workflow_dispatch:", "model.go",
            "rhc_reusable_interim.py", "rhc_downloads.py",
            "needs: [linux, windows]", "windows-2025",
            "Get-AuthenticodeSignature", "NotSigned",
            "previousLatestVersion", "previousHistoryIntact",
            "stage_release(", "release/v", "gh pr create",
            "rhc-infrastructure-ci.yml", "rhc-downloads-verify.yml",
            "contents: write", "pull-requests: write",
            "RHC_REUSABLE_RELEASE_STAGE"):
            with self.subTest(needle=needle):
                self.assertIn(needle, s)
        for forbidden in (
            "version_from_model('.')=='3.0.8.1'",
            "test ! -e downloads/latest.json",
            "previousReleases=0", "productionEnabled=true",
            "rollbackVerified=true", "EXPLICIT_OWNER_RHC22"):
            self.assertNotIn(forbidden, s)

    def test_postmerge_tag_and_remote_verification_present(self):
        p = ROOT / ".github/workflows/rhc-reusable-interim-postmerge.yml"
        s = p.read_text(encoding="utf-8")
        for needle in (
            "pull_request:", "types: [closed]", "merged == true",
            "startsWith(github.event.pull_request.head.ref, 'release/v')",
            "github.event.pull_request.base.ref == 'main'",
            "git rev-list --parents", "rhc_downloads.py",
            "git/ref/tags/", "git/refs", "sha256",
            "Get-AuthenticodeSignature", "RHC_REUSABLE_POSTMERGE_SUCCESS",
            "contents: write", "RHC_REAL_SOURCE_SHA"):
            self.assertIn(needle, s)
        self.assertNotIn("3.0.8.1", s)
        self.assertNotIn("productionEnabled=true", s)

    def test_readme_warns_about_each_unsigned_interim_build(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import rhc_downloads as downloads
        base = {"version": "3.0.8.1", "file": "a.zip", "size": 8,
                "sha256": "a" * 64, "sourceSha": "b" * 40}
        new = dict(base, version="3.0.8.2", file="b.zip")
        html = downloads.render_readme([new, base])
        self.assertIn("v3.0.8.2 interim-release disclosure", html)
        self.assertIn("v3.0.8.1 interim-release disclosure", html)
        self.assertGreaterEqual(html.count("PUBLISHER NOT VERIFIED"), 2)
        self.assertIn("SmartScreen", html)


if __name__ == "__main__":
    unittest.main()
