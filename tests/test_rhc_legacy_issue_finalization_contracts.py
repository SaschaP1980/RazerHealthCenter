"""RHC-1/3/34 closure: current migration gate truth and SHA-bound historical cleanup."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/MIGRATION_STATUS.md"
CLEAN = ROOT / ".github/workflows/rhc34-historical-ref-cleanup.yml"
EXPECTED = {
    "work/RHC-34-fixture": "36b7112d140a591bc74cd67e54e48f51142c84a1",
    "work/RHC-34-tagfix": "fd9dd2750069929b5e049d51736c870613d7b037",
    "work/RHC-34-cleanup": "0da3af767fdd3ef79b851bad5ae96a10d3f681f4",
    "work/RHC-34-cleanup-final": "55e0a19a43236429a78ef60e4311cc29091be83b",
}

class HistoricalIssueFinalizationContract(unittest.TestCase):
    def test_migration_locator_is_live_and_version_neutral(self):
        locator = LEDGER.read_text(encoding="utf-8")
        for required in (
            "Migration Evidence Locator",
            "GitHub Issues",
            "Rolling Comments",
            "merged PRs",
            "model.go",
            "downloads/latest.json",
            "downloads/releases.json",
            "sourceSha",
            "M0–M6",
            "DEFERRED",
            "INITIAL_PROMPT.md",
            "GIT_PROVENANCE_CONTRACT.md",
        ):
            with self.subTest(required=required):
                self.assertIn(required, locator)
        # Historical per-release/CI facts belong in the original Issues, not in
        # the reusable live-status locator. Do not retain frozen status assertions.
        import re
        self.assertIsNone(re.search(r"\bv\d+\.\d+\.\d+", locator))
        self.assertIsNone(re.search(r"\b[0-9a-f]{40}\b", locator))
        self.assertNotIn("RHC-1: COMPLETED", locator)
        self.assertNotIn("## Final migration disposition — 2026-10-09", locator)

    def test_cleanup_only_exact_four_historical_ancestor_refs(self):
        s = CLEAN.read_text(encoding="utf-8")
        self.assertIn("name: RHC-34 Verified Historical Branch Cleanup", s)
        self.assertIn("workflow_dispatch:", s)
        self.assertIn("branches: [main]", s)
        self.assertIn("rhc34-historical-ref-cleanup.yml", s)
        self.assertIn("contents: write", s)
        self.assertIn("persist-credentials: true", s)
        self.assertIn("git merge-base --is-ancestor", s)
        self.assertIn("--force-with-lease=refs/heads/$BRANCH:$EXPECTED", s)
        self.assertIn("RHC34_LEGACY_CLEANUP=PASS", s)
        for branch, sha in EXPECTED.items():
            with self.subTest(branch=branch):
                self.assertIn(branch, s)
                self.assertIn(sha, s)
        self.assertNotIn("work/RHC-3:", s)  # Do not conflate RHC-3 with RHC-34 prefix
        self.assertNotIn("candidate/v3.0.8.1", s)
        self.assertNotIn("downloads/latest.json", s)
        self.assertNotIn("model.go", s)

    def test_cleanup_requires_main_ref_and_independent_ref_absence(self):
        s = CLEAN.read_text(encoding="utf-8")
        self.assertIn("github.ref == 'refs/heads/main'", s)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', s)
        self.assertIn("gh api", s)
        self.assertIn('test -z "$(git ls-remote origin "refs/heads/$BRANCH"', s)

if __name__ == "__main__":
    unittest.main()
