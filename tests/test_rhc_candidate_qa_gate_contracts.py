"""RHC-31 candidate QA binding tests; synthetic statuses are never Owner approvals."""
import json
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_candidate_qa_gate as gate

SHA = "1b78ca928979e9507863a53ce2e4b25491544d5e"
PARENT = "a" * 40
VERSION = "3.0.8.1"
BASE_MODEL = 'const (\n\tappVersion = "3.0.8.0"\n\treferenceVersion = "3.0.8.0"\n)\n'
MODEL = BASE_MODEL.replace("3.0.8.0", VERSION)
CONTEXTS = ("rhc/preflight/linux", "rhc/preflight/windows",
            "rhc/preflight/candidate")


def eligible():
    return dict(
        candidate_sha=SHA, branch_sha=SHA, checkout_sha=SHA,
        version=VERSION, parent_shas=[PARENT],
        changed_paths=["CHANGELOG.md", "model.go"],
        model=MODEL, parent_model=BASE_MODEL,
        changelog="# Changelog\n\n## 3.0.8.1 — Version-only hotfix\n",
        statuses=[dict(context=context, state="success",
                       creator={"login": "github-actions[bot]"})
                  for context in CONTEXTS],
        policy=dict(productionEnabled=False, signingDecision="unknown",
                    rollbackVerified=False, distribution="repo-downloads"),
    )


class CandidateQABinding(unittest.TestCase):
    def test_exact_qualified_candidate_positive(self):
        result = gate.qualify(eligible())
        self.assertEqual(result["sourceSha"], SHA)
        self.assertEqual(result["version"], VERSION)
        self.assertEqual(result["classification"], "TEST_ONLY_NOT_RELEASE")
        self.assertEqual(result["phaseB"], "DISABLED")

    def test_wrong_refs_and_source_sha_do_not_fall_through(self):
        for field, bad in (("candidate_sha", "b"*40),
                           ("branch_sha", "b"*40),
                           ("checkout_sha", "b"*40),
                           ("candidate_sha", "not-sha")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                gate.qualify(dict(eligible(), **{field: bad}))

    def test_actual_fourpart_version_and_model_bytes_required(self):
        for field, value in (("version", "3.0.8.0"),
                             ("version", "3.0.8"),
                             ("model", BASE_MODEL),
                             ("parent_model", MODEL),
                             ("changelog", "# Changelog\n")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                gate.qualify(dict(eligible(), **{field: value}))

    def test_only_one_two_file_version_only_parent_commit(self):
        for field, bad in (("parent_shas", []),
                           ("parent_shas", [PARENT, "b"*40]),
                           ("changed_paths", ["model.go"]),
                           ("changed_paths", ["model.go", "CHANGELOG.md", "tools/a"])):
            with self.subTest(field=field), self.assertRaises(ValueError):
                gate.qualify(dict(eligible(), **{field: bad}))

    def test_forged_failed_or_stale_latest_status_fails_closed(self):
        for field, bad in (("state", "pending"),
                           ("state", "failure"),
                           ("creator", {"login": "SaschaP1980"}),
                           ("context", "other/context")):
            with self.subTest(field=field):
                fixture = eligible()
                fixture["statuses"][0][field] = bad
                with self.assertRaises(ValueError):
                    gate.qualify(fixture)
        fixture = eligible()
        fixture["statuses"].insert(0, dict(context=CONTEXTS[0], state="failure",
                         creator={"login": "github-actions[bot]"}))
        with self.assertRaises(ValueError):
            gate.qualify(fixture)

    def test_real_release_policy_cannot_be_loosened(self):
        for key, value in (("productionEnabled", True),
                           ("rollbackVerified", True),
                           ("signingDecision", "unsigned-approved"),
                           ("distribution", "github-releases")):
            with self.subTest(key=key):
                fixture = eligible()
                fixture["policy"][key] = value
                with self.assertRaises(ValueError):
                    gate.qualify(fixture)

    def test_workflow_pins_real_candidate_and_never_publishes(self):
        self.assertEqual(gate.CANDIDATE_REF, "candidate/v3.0.8.1")
        yml = (ROOT / ".github/workflows/rhc-candidate-qa-v3081.yml").read_text(
            encoding="utf-8")
        for expected in (SHA, "ubuntu-24.04",
                         "windows-2025", "Get-AuthenticodeSignature",
                         "rhc_candidate_qa_gate.py", "rhc_phase_a_qa.py",
                         "needs: windows", "upload-artifact", "contents: read",
                         "RHC31-TEST-UNSIGNED-NOT-RELEASE"):
            self.assertIn(expected, yml)
        for forbidden in ("contents: write", "gh release create", "git push",
                          "RHC_REAL_PUBLICATION_APPROVED",
                          "productionEnabled=true", "downloads/latest.json >"):
            self.assertNotIn(forbidden, yml)


if __name__ == "__main__":
    unittest.main()
