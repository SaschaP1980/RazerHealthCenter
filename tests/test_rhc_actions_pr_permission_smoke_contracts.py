"""RHC-43: prove GITHUB_TOKEN createPullRequest, not merely saved settings."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / ".github/workflows/rhc-actions-pr-permission-smoke.yml"


class ActionsPrPermissionSmokeContract(unittest.TestCase):
    def test_smoke_is_nonpublishing_scoped_and_uses_only_workflow_token(self):
        s = SMOKE.read_text(encoding="utf-8")
        for fragment in (
            "name: RHC Actions GITHUB_TOKEN PR-Creation Smoke",
            "workflow_dispatch:", "work/RHC-43",
            "rhc-actions-pr-permission-smoke.yml",
            "contents: write", "pull-requests: write",
            "GH_TOKEN:", "github.token",
            "gh pr create", "--draft",
            "github-actions[bot]", "GITHUB_RUN_ID",
            "refs/heads/rhc43-pr-smoke-",
            "--force-with-lease=", "state=closed",
            "RHC43_PR_PERMISSION=PASS",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, s)
        for dangerous in ("model.go", "downloads/latest.json", "git tag -f",
                          "gh pr merge", "gh pr review", "signingDecision: verified"):
            self.assertNotIn(dangerous, s)

    def test_smoke_cleanup_is_nonoptional_and_reports_failures(self):
        s = SMOKE.read_text(encoding="utf-8")
        self.assertIn("trap cleanup EXIT", s)
        self.assertIn("PUSHED_SHA", s)
        self.assertIn("PR_NUM", s)
        self.assertIn("git ls-remote", s)
        self.assertIn("if [ \"$ACTUAL\" = \"$PUSHED_SHA\" ]", s)
        self.assertIn("test \"$REMOTE\" = ''", s)


if __name__ == "__main__":
    unittest.main()
