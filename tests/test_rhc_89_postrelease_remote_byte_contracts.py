"""RHC-89: fail-closed, self-triggering independent public ZIP readback.

GitHub GITHUB_TOKEN-generated release PR merges suppress downstream push events.
The *upstream publisher workflow_run completion* is a separate GitHub event,
and must be able to launch the same immutable read-only public HTTPS validator.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / ".github/workflows/rhc-downloads-verify.yml"
PUBLISHER = ROOT / ".github/workflows/rhc-reusable-interim-release.yml"

class AutoPostreleaseReadback(unittest.TestCase):
    def setUp(self):
        self.script = DOWNLOADS.read_text(encoding="utf-8")

    def test_independent_successful_publisher_completion_triggers_readback(self):
        s = self.script
        self.assertIn("workflow_run:", s)
        self.assertRegex(s, r"workflow_run:\s*\n\s+workflows:\s*\[RHC Reusable Interim Unsigned Release\]")
        self.assertRegex(s, r"workflow_run:[\s\S]*?types:\s*\[completed\]")
        self.assertIn("github.event.workflow_run.conclusion == 'success'", s)
        self.assertIn("github.event.workflow_run.event == 'workflow_dispatch'", s)
        self.assertIn("startsWith(github.event.workflow_run.head_branch, 'candidate/v')", s)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", s)

    def test_original_readonly_paths_and_exact_current_public_main_are_preserved(self):
        s = self.script
        for key in ("push:", "pull_request:", "workflow_dispatch:",
                    "branches: [main]", "contents: read", "cancel-in-progress: false",
                    'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
                    'python3 -B tools/rhc_remote_binary_verify.py "${args[@]}"',
                    "RHC_PUBLIC_BINARY_READBACK_SCOPE=READ_ONLY",
                    "RHC_DOWNLOADS_NONPUBLISHING_POLICY=PASS",
                    "RHC_DOWNLOADS_HISTORY=PASS"):
            with self.subTest(key=key):
                self.assertIn(key,s)
        self.assertNotIn("contents: write",s)
        self.assertNotIn("pull-requests: write",s)

    def test_workflow_run_binds_original_publisher_source_to_current_catalog(self):
        # Trust a completed publisher only when it was this repository's original
        # push to main and the actual public latest.sourceSha agrees exactly.
        s=self.script
        self.assertIn("github.event_name == 'workflow_run'",s)
        self.assertIn("GITHUB_EVENT: ${{ github.event_name }}",s)
        self.assertIn("PUBLISHER_SOURCE_SHA: ${{ github.event.workflow_run.head_sha || '' }}",s)
        self.assertIn("latest['sourceSha']==os.environ['PUBLISHER_SOURCE_SHA']",s)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',s)
        self.assertIn('test "$(gh api',s) if 'gh api' in s else self.assertIn(
            'test "$GITHUB_REF" = \'refs/heads/main\'',s)

    def test_remote_get_requires_true_public_sha_size_and_internal_hashes(self):
        s=self.script
        script=(ROOT/"tools/rhc_remote_binary_verify.py").read_text(encoding="utf-8")
        self.assertIn("github.event_name != 'pull_request'",s)
        self.assertIn("github.ref == 'refs/heads/main'",s)
        self.assertIn("--commit-sha \"$GITHUB_SHA\"",s)
        remote_step=s.split('name: Independently GET immutable published ZIP bytes via HTTPS',1)[1]
        # Both before and after the network fetch must bind to the *live*
        # current main ref. A stale source event cannot look freshly verified.
        self.assertGreaterEqual(remote_step.count('git ls-remote origin refs/heads/main'),1)
        self.assertLess(remote_step.index('python3 -B tools/rhc_remote_binary_verify.py'),
                        remote_step.index('test "$(git ls-remote origin refs/heads/main'))
        self.assertIn("urllib.request.urlopen(req, timeout=45)",script)
        self.assertIn('transport": "HTTPS_GITHUB_RAW_EXACT_COMMIT"',script)
        self.assertIn("downloads.portable_zip_check(path)",script)
        self.assertIn("if total != record[\"size\"] or hasher.hexdigest() != record[\"sha256\"]:",script)

if __name__=="__main__":
    unittest.main()
