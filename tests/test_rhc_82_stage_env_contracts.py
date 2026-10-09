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
        self.assertIn("rhc94_atomic_release.py validate-candidate", stage)
        self.assertIn("RHC_ISSUE_NUMBER=", stage)
        self.assertIn('snapshot=dict(linux,mode=\'interim-unsigned\',issue=int(os.environ[\'RHC_ISSUE_NUMBER\'])', stage)
        # A write to GITHUB_ENV only affects the next step; the Python heredoc
        # in *this* step must inherit the independently verified issue ID.
        before_python = stage.split("python3 - <<'PY'", 1)[0]
        self.assertRegex(before_python, r"(?m)^\s*export RHC_ISSUE_NUMBER(?:\s+SOURCE_PR_NUMBER\s+WORK_HEAD)?\s*$")

    def test_only_reviewed_issue_is_allowed(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("rhc94_atomic_release.py validate-candidate", s)
        self.assertIn("rhc94_atomic_release.py validate-stage", s)
        self.assertIn("rhc94_atomic_release.py validate-candidate", s)
        self.assertIn("assert policy_full['productionEnabled'] is False", s)
        self.assertIn("assert policy_full['rollbackVerified'] is False", s)
        self.assertIn("assert policy_full['signingDecision']=='unknown'", s)



class FrozenSourceRecoveryContract(unittest.TestCase):
    def setUp(self):
        self.recovery = (ROOT / ".github/workflows/rhc82-v3085-recovery.yml").read_text(encoding="utf-8")
        self.postmerge = (ROOT / ".github/workflows/rhc-reusable-interim-postmerge.yml").read_text(encoding="utf-8")

    def test_exact_failed_run_and_original_source_pinned_no_version_change(self):
        for needle in (
            "182197e845bfd252988f27f417c4cd0f12092667",
            "37947690011",
            "ae681e4ec9ce3f337d437ae31d41494e59ff88dcddbd5f6fb94b617e94fb9aa1",
            "985be795784d87fe964491e66c605d16b6626a702588d5535adaa19c7d230f37",
            "git merge-base --is-ancestor", "git diff --quiet",
            "rhc_workflow_reliability.py resolve-source",
            "git show", "workHead", "ORIGINAL_ZIP_SHA", "ORIGINAL_EXE_SHA",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.recovery)
        self.assertNotIn("productionEnabled=true", self.recovery)
        self.assertNotIn("model.go > ", self.recovery)

    def test_independent_linux_and_native_windows_proofs_are_required_before_stage(self):
        for needle in (
            "verify_linux:", "verify_windows:", "needs: [verify_linux, verify_windows]",
            "runs-on: windows-2025", "Get-AuthenticodeSignature",
            "validate_repair_safety.py", "Native PS5.1 required",
            "linux['archiveSha256']==win['archiveSha256']",
            "gate.qualify(snap)", "sourceSha",
            "assert previous[0]['version']=='3.0.8.4'",
            "assert history==[latest,*previous]",
            "test -z \"$(git ls-remote origin",
            "path: ${{ runner.temp }}/rhc-reusable-stage",
            "actions: read", "contents: write",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.recovery)

    def test_only_four_paths_and_separate_exact_stage_ci_before_publication(self):
        for needle in (
            "git diff --cached --name-only", "diff -u", "gh pr create",
            "source PR #79; sourceSha $SOURCE_SHA", "RHC-Issue: 78",
            "gh workflow run rhc-infrastructure-ci.yml",
            "gh workflow run rhc-downloads-verify.yml",
            "rhc_workflow_reliability.py verify-hosted",
            "r.verify_release_metadata(78,79,",
            "test \"$RESULT\" = success", "test \"$(jq -r '.merged'",
            "rhc_remote_binary_verify.py", "git push --force-with-lease",
            "RHC82_FROZEN_SOURCE_PUBLIC_RELEASE=PASS",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.recovery)
        self.assertLess(self.recovery.index("check_gate rhc-downloads-verify.yml"),
                        self.recovery.index("pulls/$RHC82_RELEASE_PR/merge"))

    def test_postmerge_verifies_historical_source_ancestor_and_infra_only_delta(self):
        for needle in (
            "git merge-base --is-ancestor \"$SOURCE\" \"$FIRST\"",
            "git diff --quiet \"$SOURCE\" \"$FIRST\" -- model.go CHANGELOG.md config/rhc-release-policy.json",
            "rhc82-v3085-recovery.yml",
            "rhc_workflow_reliability.py resolve-source",
            "test \"$(jq -r '.issueNumber'", " = 78",
            'echo "RHC_REAL_SOURCE_SHA=$SOURCE"',
            "source=latest['sourceSha']",
            "test \"$(gh api \"repos/$GITHUB_REPOSITORY/git/ref/tags/v$VERSION\" --jq '.object.sha')\" = \"$SOURCE\"",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.postmerge)

    def test_recovery_is_one_time_main_only_and_does_not_relax_production(self):
        for needle in (
            "branches: [main]",
            "paths: ['.github/workflows/rhc82-v3085-recovery.yml']",
            "github.ref == 'refs/heads/main'",
            "cancel-in-progress: false",
            "test \"$(gh api \"repos/$GITHUB_REPOSITORY/branches/main\" --jq '.commit.sha')\" = \"$GITHUB_SHA\"",
            "policy['productionEnabled'] is False",
            "policy['rollbackVerified'] is False",
            "policy['signingDecision']=='unknown'",
            "exeSignature=win['exeSignature']",
            "existingTag=False,existingArchive=False",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.recovery)


if __name__ == "__main__":
    unittest.main()
