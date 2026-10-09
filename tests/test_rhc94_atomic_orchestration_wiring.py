"""RHC-94: permanent executable single-PR wiring and trigger regression."""
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8")
class AtomicOrchestrationWiring(unittest.TestCase):
    def test_candidate_authorizes_publisher_after_two_os(self):
        y=read(".github/workflows/rhc-candidate-preflight.yml")
        self.assertIn("needs: [linux, windows]",y)
        self.assertIn("rhc/preflight/candidate",y)
        self.assertIn('gh workflow run rhc-reusable-interim-release.yml --ref "$GITHUB_REF_NAME"',y)
    def test_one_combined_release_pr(self):
        y=read(".github/workflows/rhc-reusable-interim-release.yml")
        self.assertNotIn("branches: [main]",y.split("jobs:")[0])
        self.assertIn("startsWith(github.ref, 'refs/heads/candidate/v')",y)
        self.assertIn("rhc94_atomic_release.py validate-candidate",y)
        self.assertIn("GH_TOKEN: ${{ github.token }}",y)
        self.assertIn("rhc94_atomic_release.py validate-stage",y)
        self.assertEqual(y.count("gh pr create"),1)
        self.assertEqual(y.count("pulls/$RELEASE_PR/merge"),1)
        self.assertIn('gh api -X DELETE "repos/$GITHUB_REPOSITORY/git/refs/heads/$WORK_REF"',y)
        self.assertIn('test "$(git ls-remote origin "refs/heads/$WORK_REF" | cut -f1)" = "$WORK_SHA"',y)
        self.assertNotIn("source PR #$SOURCE_PR_NUMBER",y)
        self.assertIn('gh workflow run rhc-downloads-verify.yml --ref "release/v$VERSION"',y)
    def test_no_bot_pr_success_fabrication(self):
        y=read(".github/workflows/rhc-downloads-verify.yml")
        self.assertIn("github.event.workflow_run.event == 'workflow_dispatch'",y)
        self.assertIn("startsWith(github.event.workflow_run.head_branch, 'candidate/v')",y)
        self.assertIn("RHC_PUBLIC_BINARY_READBACK_SCOPE=READ_ONLY",y)
    def test_no_historical_fixture_every_version_only_push(self):
        for p in (".github/workflows/rhc-release-dry-run.yml",
                  ".github/workflows/rhc-source-intake.yml",
                  ".github/workflows/rhc-phase-a-qa.yml"):
            self.assertNotIn("      - 'model.go'",read(p),p)
    def test_legacy_import_go_glob_excludes_model_go(self):
        y=read(".github/workflows/rhc-source-intake.yml")
        self.assertIn("      - '!model.go'", y)
    def test_production_policy_remains_fail_closed(self):
        import json
        p=json.loads(read("config/rhc-release-policy.json"))
        self.assertIs(p["productionEnabled"],False)
        self.assertIs(p["rollbackVerified"],False)
        self.assertEqual(p["signingDecision"],"unknown")
        self.assertEqual(p["distribution"],"repo-downloads")
if __name__=="__main__":unittest.main()
