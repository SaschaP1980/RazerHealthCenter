"""RHC-115 executable entrypoint/readback wiring contracts (nonpublishing)."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rhc_issue_init import InitializationBlocked, verify_issue


class Wiring(unittest.TestCase):
    def file(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_work_infrastructure_requires_actual_issue_get(self):
        workflow = self.file(".github/workflows/rhc-infrastructure-ci.yml")
        self.assertIn("RHC-115 canonical Issue readback for Work push", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn('python3 tools/rhc_issue_init.py verify --repository "$GITHUB_REPOSITORY" --issue "$NUMBER" --for-development', workflow)
        self.assertIn("github.event_name == 'push'", workflow)

    def test_development_completion_blocks_before_trusted_status(self):
        workflow = self.file(".github/workflows/rhc-development-completion.yml")
        self.assertIn("RHC-Issue: ([1-9][0-9]*)", workflow)
        self.assertIn('python3 tools/rhc_issue_init.py verify --repository "$GITHUB_REPOSITORY" --issue "$ISSUE" --for-development', workflow)
        self.assertLess(workflow.index("python3 tools/rhc_issue_init.py verify"),
                        workflow.index('CURRENT_MAIN="$(gh api'))

    def test_candidate_transfer_checks_live_issue_before_write(self):
        code = self.file("tools/rhc_candidate_from_work.py")
        self.assertIn('verify_initialized_issue(gh("GET", "/issues/" + plan["issue"]),', code)
        self.assertLess(code.index('verify_initialized_issue(gh("GET", "/issues/"'),
                        code.index('new = gh("POST", "/git/commits"'))

    def test_publisher_checks_actual_issue_before_staging(self):
        code = self.file("tools/rhc94_atomic_release.py")
        self.assertIn('responsible_issue = verify_initialized_issue(gh("issues/" + str(n)), n,', code)
        self.assertIn('workhead = gh("git/ref/heads/" + wb)', code)
        self.assertIn('proof = qualify_candidate(source, base, cand, work, responsible_issue,', code)

    def test_historical_source_reads_are_nonmutating_and_title_checked(self):
        code = self.file("tools/rhc_workflow_reliability.py")
        self.assertIn("verify_issue(issue, n, require_open=False)", code)

    def test_real_scope_body_required_even_if_title_valid(self):
        issue = dict(number=115, title="[RHC-115] Relevant", body="", state="open")
        with self.assertRaises(InitializationBlocked):
            verify_issue(issue, 115)

    def test_init_tool_claims_no_global_webui_interception(self):
        code = self.file("tools/rhc_issue_init.py")
        self.assertIn("cannot be globally intercepted", code)
        self.assertIn("never retried after an ambiguous result", code)
        self.assertNotIn("model.go", self.file("tools/rhc_issue_init.py"))


if __name__ == "__main__":
    unittest.main()
