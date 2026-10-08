"""RHC-20 regression gates. Introduced RED against pre-fix infrastructure."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class FutureVersionWorkContracts(unittest.TestCase):
    def test_generic_work_branch_push_qualifies(self):
        workflow = read(".github/workflows/rhc-infrastructure-ci.yml")
        self.assertIn("- 'work/RHC-*'", workflow)
        self.assertNotIn("- 'work/RHC-3'", workflow)
        self.assertNotIn("- 'work/RHC-5'", workflow)

    def test_infrastructure_never_pins_current_app_version(self):
        workflow = read(".github/workflows/rhc-infrastructure-ci.yml")
        self.assertNotIn("--base-version 3.0.8.0", workflow)
        self.assertNotIn('test "$VERSION" = "3.0.8.0"', workflow)
        self.assertNotIn("version 3.0.8.0, not historical", workflow)

    def test_completion_uses_stable_job_contract(self):
        workflow = read(".github/workflows/rhc-development-completion.yml")
        self.assertNotIn('startswith(\\\"Linux original Go build', workflow)
        self.assertIn("rhc/infra/linux", workflow)
        self.assertIn("rhc/infra/windows", workflow)

    def test_dry_run_source_version_is_not_fixed(self):
        workflow = read(".github/workflows/rhc-release-dry-run.yml")
        self.assertNotIn('3\\.0\\.8\\.0', workflow)
        self.assertIn("version_from_model", workflow)

    def test_appengine_semantics_may_check_next_app_version(self):
        check = read("tools/validate_v308_background_runtime_semantics.py")
        self.assertNotIn('appVersion                   = "3.0.8.0"', check)
        self.assertIn("version_from_model", check)
        self.assertIn("healthy requires persistent background contract", check)
        self.assertIn("read-only contract retained", check)

    def test_catalog_maintains_separate_validated_version_domain(self):
        check = read("tools/validate_i18n.py")
        self.assertNotIn("catalog version must be 3.0.8.0", check)
        self.assertIn("version_from_model", check)
        self.assertIn("catalogVersion", check)
        self.assertIn("catalog version", check)

    def test_candidate_preflight_accepts_dispatch_explicitly(self):
        wf = read(".github/workflows/rhc-candidate-preflight.yml")
        self.assertIn("workflow_dispatch:", wf)

    def test_candidate_preflight_emits_real_sha_bound_linux_and_windows_statuses(self):
        wf = read(".github/workflows/rhc-candidate-preflight.yml")
        for context in ("rhc/preflight/linux", "rhc/preflight/windows", "rhc/preflight/candidate"):
            with self.subTest(context=context):
                self.assertIn(context, wf)
        self.assertIn("needs: [linux, windows]", wf)
        self.assertIn("statuses: write", wf)
        self.assertIn("exit 1", wf)  # existing production promotion must stay blocked

    def test_candidate_publication_workflow_is_gated_and_nonpublishing(self):
        wf = read(".github/workflows/rhc-candidate-from-work.yml")
        self.assertIn("workflow_run:", wf)
        self.assertIn("RHC Development Completion (exact SHA gate)", wf)
        self.assertIn("head_repository.full_name == github.repository", wf)
        self.assertIn("persist-credentials: false", wf)
        self.assertNotIn("create-release", wf)
        self.assertNotIn("productionEnabled: true", wf)
        self.assertIn("head_commit.message", wf)
        self.assertIn("Release-Profile: version-only", wf)
        self.assertIn("Development-Completion: requested", wf)

    def test_candidate_builds_two_independent_exes_and_compares_package_bytes(self):
        wf = read(".github/workflows/rhc-candidate-preflight.yml")
        self.assertIn("build-one/RazerHealthCenter.exe", wf)
        self.assertIn("build-two/RazerHealthCenter.exe", wf)
        self.assertIn("RHC_CANDIDATE_INDEPENDENT_PE_AND_PACKAGE_REPRODUCIBILITY=PASS", wf)
        self.assertIn('for name in "RazerHealthCenter-Source-v', wf)
        self.assertIn("cmp -s", wf)


if __name__ == "__main__":
    unittest.main()
