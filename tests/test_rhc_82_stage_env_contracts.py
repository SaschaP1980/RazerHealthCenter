"""RHC-82: real staged publisher bug - GITHUB_ENV does not update current shell."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/rhc-reusable-interim-release.yml"


class SameStepEnvRegression(unittest.TestCase):
    def test_stage_exports_verified_source_issue_to_current_python_process(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        stage = s.split("\n  stage:", 1)[1].split("\n  finalize:", 1)[0]
        self.assertIn("resolve-source", stage)
        self.assertIn("RHC_ISSUE_NUMBER=\"$(jq -er '.issueNumber' <<< \"$SOURCE_EVIDENCE\")\"", stage)
        self.assertIn('snapshot=dict(linux,mode=\'interim-unsigned\',issue=int(os.environ[\'RHC_ISSUE_NUMBER\'])', stage)
        # A write to GITHUB_ENV only affects the next step; the Python heredoc
        # in *this* step must inherit the independently verified issue ID.
        before_python = stage.split("python3 - <<'PY'", 1)[0]
        self.assertRegex(before_python, r"(?m)^\s*export RHC_ISSUE_NUMBER(?:\s+SOURCE_PR_NUMBER\s+WORK_HEAD)?\s*$")

    def test_only_reviewed_issue_is_allowed(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("jq -er '.issueNumber'", s)
        self.assertIn("jq -er '.sourcePR'", s)
        self.assertIn("rhc_workflow_reliability.py resolve-source", s)
        self.assertIn("assert policy_full['productionEnabled'] is False", s)
        self.assertIn("assert policy_full['rollbackVerified'] is False", s)
        self.assertIn("assert policy_full['signingDecision']=='unknown'", s)


if __name__ == "__main__":
    unittest.main()
