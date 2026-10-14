"""RHC-174: verify fail-closed RHC-170 authenticated runner boundaries.

Tests inspect the actual workflow used by GitHub Actions, without network,
YAML libraries, secrets, local gh, modifying the product, or a release.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/rhc170-authenticated-cli.yml"
DRIVER = ROOT / "tools/rhc170_atomic_work_pipeline.py"


class AuthenticatedRHC170RunnerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.yaml = WORKFLOW.read_text(encoding="utf-8")
        cls.script = DRIVER.read_text(encoding="utf-8")
        cls.probe = cls.yaml.split("  authenticated-cli-probe:", 1)[1].split(
            "  authenticated-work-execute:", 1
        )[0]
        cls.execute = cls.yaml.split("  authenticated-work-execute:", 1)[1]

    def test_only_opt_in_execute_and_bounded_one_time_probe_push(self):
        self.assertIn("workflow_dispatch:", self.yaml)
        self.assertIn("      - 'work/RHC-174'", self.yaml)
        self.assertIn("    paths:", self.yaml)
        self.assertNotIn("schedule:", self.yaml)
        self.assertIn("inputs.mode == 'execute'", self.execute)
        self.assertIn("inputs.allow_apply_push == true", self.execute)
        self.assertIn("github.event_name == 'workflow_dispatch'", self.execute)
        self.assertIn("github.event_name == 'push' || inputs.mode == 'probe'", self.probe)

    def test_probe_uses_gh_read_only_and_never_work_push(self):
        self.assertIn("GH_TOKEN: ${{ github.token }}", self.probe)
        self.assertIn("gh api -X GET", self.probe)
        self.assertIn("tools/rhc170_atomic_work_pipeline.py --help", self.probe)
        self.assertNotIn("--apply", self.probe)
        self.assertNotIn("git push", self.probe)
        self.assertIn("persist-credentials: false", self.probe)

    def test_separately_minted_app_token_is_only_execute_writer(self):
        self.assertIn("actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510", self.execute)
        self.assertIn("RHC170_APP_PRIVATE_KEY", self.execute)
        self.assertIn("RHC170_APP_ID", self.execute)
        self.assertIn("permission-contents: write", self.execute)
        self.assertIn("permission-issues: read", self.execute)
        self.assertIn("permission-actions: read", self.execute)
        self.assertIn("GH_TOKEN: ${{ steps.app.outputs.token }}", self.execute)
        self.assertNotIn("GH_TOKEN: ${{ github.token }}", self.execute)
        self.assertIn("persist-credentials: true", self.execute)

    def test_exact_sha_lease_and_verified_cli_push(self):
        self.assertIn("test \"$(git rev-parse HEAD)\" = \"$PIN\"", self.execute)
        self.assertIn('test "$(git rev-parse "origin/work/RHC-${NUMBER}")" = "$PIN"', self.execute)
        self.assertIn("git status --porcelain", self.execute)
        self.assertIn("tools/rhc170_atomic_work_pipeline.py", self.execute)
        self.assertIn("--apply --push --owner-authorized-new-version", self.execute)
        self.assertIn("WORK_PUSH_VERIFIED", self.execute)
        self.assertIn("prepush_exact_ref_lease_verified", self.execute)
        self.assertIn("WORK_CI=CREATED_NOT_GREEN", self.execute)
        self.assertIn("--observe-ci-for-sha", self.execute)
        self.assertIn("--push-observed-utc", self.execute)
        self.assertIn("refs/heads/work/RHC-", self.execute)

    def test_driver_keeps_critical_safety_guards(self):
        for literal in (
            "owner_authorized_new_version",
            "_version_authorized",
            "_same_authority",
            "push_with_lease",
            "--force-with-lease",
            "verify_ci_created",
            'row.get("event") != "push"',
            "WORK_CI_CREATED_NOT_GREEN",
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, self.script)

    def test_no_release_dispatch_or_suppressed_push_green_fallback(self):
        self.assertNotIn("rhc-interim-release", self.execute)
        self.assertNotIn("gh workflow run", self.execute)
        self.assertNotIn("gh release create", self.execute)
        self.assertNotIn("repository_dispatch", self.execute)
        self.assertNotIn("RHC170_REAL_PUSH_WORK_CI=PASS", self.execute)

    def test_pinned_actions_and_read_permissions(self):
        self.assertRegex(self.yaml, r"(?m)^permissions:\n  contents: read\n  issues: read\n  actions: read$")
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", self.yaml)
        self.assertIn("environment: rhc170-benchmark", self.execute)
        self.assertIn("timeout-minutes: 20", self.execute)

    def test_not_a_product_version_change(self):
        self.assertTrue(WORKFLOW.exists())
        self.assertNotIn("model.go", self.probe)
        self.assertNotIn("CHANGELOG.md", self.probe)
        self.assertNotIn("downloads/", self.execute)
        self.assertNotIn("source tag", self.execute.lower())


if __name__ == "__main__":
    unittest.main()
