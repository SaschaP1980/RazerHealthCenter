"""RHC-196: deterministic PR-trigger/noise and ordinary PR coverage contracts.

This is a deliberately small standard-library-only test of the authored event
filters, not a substitute for real hosted Actions / GitHub approval behavior.
"""
from fnmatch import fnmatchcase
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "infra": ".github/workflows/rhc-infrastructure-ci.yml",
    "downloads": ".github/workflows/rhc-downloads-verify.yml",
    "preactivation": ".github/workflows/rhc-release-preactivation.yml",
}
RELEASE_PR_CHANGED_PATHS = (
    "model.go", "CHANGELOG.md", "downloads/README.md",
    "downloads/latest.json", "downloads/releases.json",
    "downloads/RazerHealthCenter-Portable-v3.0.8.24.zip",
)


def event_block(yaml_text, event):
    lines = yaml_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line == "on:":
            start = i
            break
    if start is None:
        raise AssertionError("Missing on: event block")
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line and not line.startswith((" ", "#")):
            break
        if line == f"  {event}:":
            section = []
            for other in lines[i + 1:]:
                if other and not other.startswith(("   ", "#")):
                    break
                section.append(other)
            return "\n".join(section)
    return None


def path_filters(workflow, event):
    body = event_block(workflow, event)
    if body is None:
        return ()
    match = re.search(r"(?m)^    paths:\s*$", body)
    if match is None:
        return ()
    patterns = []
    for row in body[match.end():].splitlines():
        if row.strip() and not row.startswith(("      ", "        ", "#")):
            break
        m = re.fullmatch(r"\s+-\s+['\"]([^'\"]+)['\"]\s*(?:#.*)?", row)
        if m:
            patterns.append(m.group(1))
    return tuple(patterns)


def would_match(patterns, changed_files):
    for changed in changed_files:
        accepted = False
        for pattern in patterns:
            negate = pattern.startswith("!")
            if fnmatchcase(changed, pattern[1:] if negate else pattern):
                accepted = not negate
        if accepted:
            return True
    return False


class PhaseAPrTriggers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {
            key: (ROOT / path).read_text(encoding="utf-8")
            for key, path in WORKFLOWS.items()
        }

    def test_no_ancillary_pull_request_workflow_matches_immutable_release_pr(self):
        for key, data in self.text.items():
            with self.subTest(workflow=key):
                self.assertIsNotNone(event_block(data, "pull_request"))
                self.assertFalse(
                    would_match(path_filters(data, "pull_request"),
                                RELEASE_PR_CHANGED_PATHS),
                    f"{key} still schedules a bot-created release PR (0-job approval noise)",
                )

    def test_normal_source_and_security_prs_remain_tested(self):
        positive_paths = {
            "infra": (
                "tools/rhc_workflow_reliability.py",
                "tests/test_rhc_workflow_reliability_contracts.py",
                ".github/workflows/rhc-infrastructure-ci.yml",
            ),
            "downloads": (
                "tools/rhc_downloads.py",
                "tests/test_rhc_downloads_contracts.py",
                "config/rhc-release-policy.json",
            ),
            "preactivation": (
                "tools/rhc12_release_plan.py",
                "tests/test_rhc_release_preactivation_contracts.py",
                "config/rhc-release-policy.json",
            ),
        }
        for key, files in positive_paths.items():
            with self.subTest(workflow=key):
                patterns = path_filters(self.text[key], "pull_request")
                for changed in files:
                    self.assertTrue(would_match(patterns, (changed,)),
                                    f"{key} loses ordinary PR coverage: {changed}")

    def test_work_branch_and_manual_dispatch_not_displaced(self):
        for key, data in self.text.items():
            with self.subTest(workflow=key):
                self.assertIsNotNone(event_block(data, "workflow_dispatch"))
                self.assertIsNotNone(event_block(data, "push"))
                self.assertIn("work/RHC-*", event_block(data, "push"))
        self.assertIn("model.go", path_filters(self.text["infra"], "push"))
        self.assertIn("downloads/**", path_filters(self.text["downloads"], "push"))
        self.assertIn("downloads/**", path_filters(self.text["preactivation"], "push"))
        self.assertIn("main", event_block(self.text["downloads"], "push"))

    def test_exact_stage_and_native_safety_gates_stay_in_source(self):
        paths = [
            ".github/workflows/rhc-candidate-preflight.yml",
            ".github/workflows/rhc-reusable-interim-release.yml",
            ".github/workflows/rhc-postrelease-verification.yml",
        ]
        for path in paths:
            with self.subTest(workflow=path):
                self.assertTrue((ROOT / path).exists())
        self.assertIn("windows-2025",
                      (ROOT / paths[0]).read_text(encoding="utf-8"))
        self.assertIn("windows-2025",
                      (ROOT / paths[2]).read_text(encoding="utf-8"))
        self.assertIn("workflow_dispatch", self.text["downloads"])
        for key, data in self.text.items():
            with self.subTest(workflow=key):
                self.assertNotIn("pull_request_target:", data)

    def test_restricted_publication_paths_do_not_silently_qualify_any_pr(self):
        # This demonstrates a coverage boundary, NOT full external-fork
        # equivalence. Publication-only paths require separate trusted RHC-94
        # Candidate/Publisher/staged Downloads and RHC-102 evidence.
        for key, sensitive in (
            ("infra", "model.go"),
            ("downloads", "downloads/latest.json"),
            ("preactivation", "downloads/releases.json"),
        ):
            with self.subTest(workflow=key):
                self.assertFalse(would_match(
                    path_filters(self.text[key], "pull_request"), (sensitive,)))
        self.assertIsNotNone(event_block(self.text["downloads"], "workflow_dispatch"))


if __name__ == "__main__":
    unittest.main()
