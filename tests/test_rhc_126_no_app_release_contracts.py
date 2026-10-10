"""RHC-126: retain proven release gates without a dedicated GitHub App.

Tests intentionally assert the desired no-App contract, and must RED against
the merged RHC-124 design before any publisher fix is applied.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / ".github/workflows/rhc-reusable-interim-release.yml"
HOWTO = ROOT / "docs/GITHUB_HOWTO.md"
DOWNLOADS = ROOT / ".github/workflows/rhc-downloads-verify.yml"
INFRA = ROOT / ".github/workflows/rhc-infrastructure-ci.yml"
PREACT = ROOT / ".github/workflows/rhc-release-preactivation.yml"
POST = ROOT / ".github/workflows/rhc-postrelease-verification.yml"


class RHC126ReleaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = PUBLISHER.read_text(encoding="utf-8")

    def test_no_dedicated_app_token_or_credential_dependency(self):
        for forbidden in (
            "actions/create-github-app-token", "app-token", "release_app_actor",
            "RELEASE_APP_ACTOR", "RHC_RELEASE_APP_CLIENT_ID",
            "RHC_RELEASE_APP_PRIVATE_KEY",
            "steps.app-token.outputs.token", "rhc124-pr-identity",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.w)

    def test_existing_scoped_github_token_creates_one_combined_pr(self):
        self.assertIn("GH_TOKEN: ${{ github.token }}", self.w)
        self.assertEqual(self.w.count("gh pr create --repo"), 1)
        self.assertIn('gh pr create --repo "$GITHUB_REPOSITORY" --base main --head release/v$VERSION', self.w)
        self.assertIn('test "$ACTUAL" = 1', self.w)
        self.assertIn("github-actions[bot]", self.w)
        self.assertNotIn("GH_TOKEN: ${{ steps.app-token.outputs.token }}", self.w)
        # Preserve a single qualified exact-head source+four-downloads merge.
        self.assertIn("rhc94_atomic_release.py validate-stage", self.w)
        self.assertIn("downloads/RazerHealthCenter-Portable-v$VERSION.zip", self.w)
        self.assertIn("-f sha=\"$STAGED_SHA\" -f merge_method=merge", self.w)

    def test_supplemental_release_pr_gate_is_not_required(self):
        self.assertNotIn("rhc124_pr_ci.py", self.w)
        self.assertNotIn("RHC124_HOSTED_PR_THREE_WORKFLOW_GATE", self.w)
        self.assertNotIn("PR_CI_VERIFIED", self.w)
        self.assertNotIn("tools/rhc124_pr_ci.py", self.w)

    def test_trusted_exact_stage_downloads_gate_still_mandatory(self):
        self.assertIn('gh workflow run rhc-downloads-verify.yml --ref "release/v$VERSION"', self.w)
        self.assertIn('.event==\\"workflow_dispatch\\"', self.w)
        self.assertIn('test "$CONC" = success', self.w)
        self.assertIn("rhc_workflow_reliability.py verify-hosted", self.w)
        self.assertIn('test -n "$VAL" && test "$STATUS" = completed && test "$CONC" = success', self.w)
        self.assertIn('test "$(git rev-parse "$STAGED^")" = "$SOURCE"', self.w)
        self.assertIn('test -z "$(git ls-remote origin refs/tags/v$VERSION)"', self.w)

    def test_real_two_os_build_and_postrelease_remain_mandatory(self):
        self.assertIn("needs: [linux, windows]", self.w)
        self.assertIn("RHC_REUSABLE_LINUX_DOUBLE_BUILD=PASS", self.w)
        self.assertIn("PowerShell 5.1", self.w)
        self.assertIn("Get-AuthenticodeSignature", self.w)
        self.assertIn("expected_main_sha=", self.w)
        self.assertIn("rhc-postrelease-verification.yml --ref main", self.w)
        self.assertIn("RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS", self.w)
        self.assertIn("assert len(rows)==3", self.w)
        self.assertIn("RHC_REUSABLE_INTERIM_RELEASE_SUCCESS=PASS", self.w)

    def test_human_pull_request_ci_remains_configured(self):
        for path in (INFRA, DOWNLOADS, PREACT):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertRegex(text, r"(?m)^  pull_request:")
                self.assertRegex(text, r"(?m)^    branches:")
        self.assertIn("windows-2025", INFRA.read_text(encoding="utf-8"))

    def test_no_unsafe_pr_target_or_bypass(self):
        self.assertNotIn("pull_request_target:", self.w)
        self.assertIn("rhc_downloads.py", DOWNLOADS.read_text(encoding="utf-8"))
        self.assertIn("RHC102_INDEPENDENT_HTTPS=PASS", POST.read_text(encoding="utf-8"))
        self.assertIn("RHC102_INDEPENDENT_WINDOWS=PASS", POST.read_text(encoding="utf-8"))
        self.assertIn("RHC102_INDEPENDENT_POSTRELEASE=PASS", POST.read_text(encoding="utf-8"))

    def test_operator_docs_do_not_require_extra_app(self):
        howto = HOWTO.read_text(encoding="utf-8")
        self.assertNotIn("### RHC-124 dedicated App identity for automated interim release PRs", howto)
        self.assertIn("RHC-126", howto)
        self.assertIn("workflow_dispatch", howto)


    def test_authoritative_release_docs_keep_required_gates(self):
        contract = (ROOT / "docs/REUSABLE_INTERIM_RELEASE_CONTRACT.md").read_text(encoding="utf-8")
        process = (ROOT / "docs/RELEASE_PROCESS.md").read_text(encoding="utf-8")
        for doc in (contract, process):
            with self.subTest(path="release docs"):
                self.assertIn("RHC-126", doc)
                self.assertIn("GITHUB_TOKEN", doc)
                self.assertIn("workflow_dispatch", doc)
                self.assertIn("native Windows", doc)
                self.assertIn("RHC-102", doc)
        self.assertIn("RHC-114", process)
        self.assertIn("rhc_workflow_reliability.py", contract)

    def test_bot_actor_and_frozen_pr_sha_are_checked(self):
        self.assertIn('.user.login == "github-actions[bot]"', self.w)
        self.assertIn('.head.sha == $stage', self.w)
        self.assertIn('.base.sha == $base', self.w)
        self.assertIn('.draft == false', self.w)
        self.assertIn('test "$ACTUAL" = 1', self.w)
        self.assertIn('test "$(git rev-parse "$STAGED^")" = "$SOURCE"', self.w)


    def test_rhc124_forensic_suite_retained_but_never_a_publisher_dependency(self):
        # Historical extra-suite evidence remains useful for diagnostics,
        # but no GitHub App or those five jobs are a release prerequisite.
        helper = ROOT / "tools/rhc124_pr_ci.py"
        self.assertTrue(helper.is_file())
        text = helper.read_text(encoding="utf-8")
        self.assertIn("verify_check_suites", text)
        self.assertNotIn("rhc124_pr_ci.py", self.w)
        contract = (ROOT / "docs/REUSABLE_INTERIM_RELEASE_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("archival read-only forensic helper", contract)
        self.assertIn("rhc_workflow_reliability.py verify-hosted", contract)


if __name__ == "__main__":
    unittest.main()
