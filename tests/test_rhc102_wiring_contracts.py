"""RHC-102: permanent future publisher/independent safety gate wiring."""
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding="utf-8")
class RHC102HostedWiring(unittest.TestCase):
    def test_dedicated_independent_workflow_has_two_actual_hosted_os(self):
        s=read(".github/workflows/rhc-postrelease-verification.yml")
        self.assertIn("workflow_dispatch:",s)
        self.assertIn("pull_request:",s)
        self.assertIn("types: [closed]",s)
        self.assertIn("head.ref == 'work/RHC-102'",s)
        self.assertIn("runs-on: ubuntu-24.04",s)
        self.assertIn("runs-on: windows-2025",s)
        self.assertIn("Get-AuthenticodeSignature",s)
        self.assertIn("NotSigned",s)
        self.assertIn("validate_repair_safety.py",s)
        self.assertIn("tools/rhc102_postrelease_provenance.py",s)
        self.assertIn("tools/rhc_remote_binary_verify.py",s)
        self.assertIn("rhc102_postrelease_provenance.py",s)
        self.assertIn("test_rhc_remote_binary_verify_contracts.py",s)
        self.assertIn("github.event.pull_request.merged == true",s)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository",s)
        self.assertIn("RHC102_INDEPENDENT_HTTPS=PASS",s)
        self.assertIn("RHC102_INDEPENDENT_WINDOWS=PASS",s)
        self.assertIn("RHC102_INDEPENDENT_POSTRELEASE=PASS",s)
        self.assertIn("needs: [linux, windows]",s)
        self.assertIn("test \"$LINUX_RESULT\" = success",s)
        self.assertIn("test \"$WINDOWS_RESULT\" = success",s)
        self.assertNotIn("productionEnabled: true",s)
    def test_publisher_cannot_proclaim_green_before_real_https(self):
        s=read(".github/workflows/rhc-reusable-interim-release.yml")
        stage=s.split("\n  finalize:\n",1)[1]
        self.assertIn("actions: write",stage)
        self.assertIn("gh workflow run rhc-postrelease-verification.yml --ref main",stage)
        self.assertIn('-f expected_main_sha="$MERGED_MAIN_SHA"',stage)
        self.assertIn('-f expected_source_sha="$SOURCE_SHA"',stage)
        self.assertIn('-f version="$VERSION"',stage)
        self.assertIn('-f expected_release_pr="$RELEASE_PR"',stage)
        self.assertIn("RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS",stage)
        self.assertIn('test "$LINUX_RESULT" = success',
                      read(".github/workflows/rhc-postrelease-verification.yml"))
        self.assertIn("RHC_PUBLICATION=PASS_POSTRELEASE_PENDING",stage)
        self.assertLess(stage.index("RHC_PUBLICATION=PASS_POSTRELEASE_PENDING"),
                        stage.index("RHC94_SINGLE_ATOMIC_PR_RELEASE_SUCCESS=PASS"))
        self.assertIn("test \"$(gh api \"repos/$GITHUB_REPOSITORY/branches/main\"",stage)
        self.assertNotIn("productionEnabled=true",stage)
        self.assertNotIn("rollbackVerified=true",stage)
    def test_negative_data_policy_no_false_success_on_null_job_runs(self):
        s=read(".github/workflows/rhc-reusable-interim-release.yml")
        self.assertIn("assert len(rows)==3",s)
        self.assertIn("jobs[0]['conclusion']=='success'",s)
        self.assertIn("jobs[0]['status']=='completed'",s)
        self.assertIn("github-actions[bot]",s)
        self.assertIn("RUNNER_TEMP/postjobs.json",s)
        self.assertIn('test "$(jq -r \'.conclusion\'',s)
    def test_current_published_data_unchanged_by_infrastructure(self):
        import json
        root=ROOT
        l=json.loads((root/"downloads/latest.json").read_text())
        self.assertEqual(l["version"],"3.0.8.8")
        self.assertEqual(l["sourceSha"],"83d894a8c556ab83286c7a0569032fd2ab4728b9")
        self.assertEqual(l["sha256"],"67d4289f26b7f6b3ca1078a936aa840e9a58529e375156b9bcb5f3213eded4e1")
if __name__=="__main__":
    unittest.main()
