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
        # RHC-76: Candidate qualification succeeds independently of the
        # separately blocked signed-production controller.
        self.assertNotIn("  promotion:", wf)
        self.assertIn("RHC_STANDARD_PRODUCTION=BLOCKED_BY_POLICY", wf)
        self.assertIn("no production promotion", wf)
        production=read(".github/workflows/rhc-release-preactivation.yml")
        self.assertIn("RHC12_REAL_PRODUCTION_POLICY=BLOCKED", production)

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

    def test_all_retained_runtime_validators_use_current_four_part_app_version(self):
        # These 15 validators were originally pinned to the historical 3.0.8.0.
        # Never change catalog-domain historical fixture versions or weaken
        # the other read-only/repair/PowerShell/Setup safety assertions.
        paths = (
            "tools/validate_setup_inventory.py",
            "tools/validate_version_check.py",
            "tools/validate_guided_calibration.py",
            "tools/validate_historical_details_v240.py",
            "tools/validate_v302_historical_session_archive.py",
            "tools/validate_v303_archive_header_polish.py",
            "tools/validate_v304_archive_surface_tint.py",
            "tools/validate_v300_diagnostic_repair_platform.py",
            "tools/validate_v301_manifest_authority.py",
            "tools/validate_v305_false_green_guard.py",
            "tools/validate_v306_appengine_recovery.py",
            "tools/validate_v307_ps51_appengine_diagnostic.py",
            "tools/validate_healthcheck_selection_v237.py",
            "tools/validate_gate_finalization_v238.py",
            "tools/validate_ui_recovery.py",
        )
        for path in paths:
            with self.subTest(path=path):
                code = read(path)
                self.assertIn("from rhc_release_contracts import version_from_model", code)
                self.assertIn("version_from_model(root)", code)
                self.assertNotIn('appVersion                   = "3.0.8.0"', code)
                self.assertNotIn('referenceVersion             = "3.0.8.0"', code)

    def test_current_rhc12_preactivation_workflow_is_strictly_readonly(self):
        wf = read(".github/workflows/rhc-release-preactivation.yml")
        self.assertIn("RHC12_REAL_PRODUCTION_POLICY=BLOCKED", wf)
        self.assertIn("permissions:", wf)
        self.assertIn("  contents: read", wf)
        self.assertIn("persist-credentials: false", wf)
        self.assertIn("tools/rhc_downloads.py --downloads downloads", wf)
        self.assertIn("rhc12_release_plan import evaluate", wf)
        self.assertNotIn("contents: write", wf)
        self.assertNotIn("actions: write", wf)
        self.assertNotIn("productionEnabled: true", wf)


if __name__ == "__main__":
    unittest.main()
