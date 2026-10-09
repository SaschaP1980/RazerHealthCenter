"""RHC-43: historic one-off and prepublication workflows must not gate new-version PRs.

This regression retains the historical fail-closed code and asserts that new
versions use a separate, qualified release lifecycle rather than replaying
the old v3.0.8.1 workflow or the empty-catalog rehearsal.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def event_block(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^on:\n(.*?)(?=^[a-zA-Z][\w-]*:|\Z)", text)
    if not match:
        raise AssertionError("missing workflow event configuration: " + str(path))
    return match.group(1)


class HistoricReleaseIsolation(unittest.TestCase):
    def test_v3081_release_cannot_fire_on_future_source_change_or_pr(self):
        workflow = WORKFLOWS / "rhc-interim-release-v3081.yml"
        events = event_block(workflow)
        self.assertIn("workflow_dispatch:", events)
        self.assertNotRegex(events, r"(?m)^  push:")
        self.assertNotRegex(events, r"(?m)^  pull_request:")
        src = workflow.read_text(encoding="utf-8")
        self.assertIn("only exact interim version", src)
        self.assertIn("3.0.8.1", src)
        self.assertIn("needs: [linux, windows]", src)

    def test_prepublication_rehearsal_cannot_gate_ordinary_hotfix_pr(self):
        workflow = WORKFLOWS / "rhc-release-rehearsal.yml"
        events = event_block(workflow)
        self.assertIn("workflow_dispatch:", events)
        self.assertNotRegex(events, r"(?m)^  pull_request:")
        self.assertNotRegex(events, r"(?m)^  push:")
        src = workflow.read_text(encoding="utf-8")
        self.assertIn("tools/rhc_release_rehearsal.py", src)
        self.assertIn("test ! -e downloads/latest.json", src)

    def test_normal_latest_version_matrix_remains_event_driven(self):
        workflow = WORKFLOWS / "rhc-infrastructure-ci.yml"
        events = event_block(workflow)
        self.assertRegex(events, r"(?m)^  push:")
        self.assertRegex(events, r"(?m)^  pull_request:")


if __name__ == "__main__":
    unittest.main()
