"""RHC-43: new-repository manual GitHub Actions PR permission onboarding."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/GITHUB_HOWTO.md"
TEMPLATE = ROOT / "docs/templates/PROJECT_MIGRATION_TEMPLATE.md"
DEVELOPMENT = ROOT / "docs/DEVELOPMENT_GUIDELINES.md"
RELEASE = ROOT / "docs/RELEASE_PROCESS.md"


class ManualActionsOnboardingContract(unittest.TestCase):
    def test_operator_guide_contains_complete_manual_project_initialization(self):
        guide = GUIDE.read_text(encoding="utf-8")
        for required in (
            "Manual first-time setup for new repositories",
            "Settings > Actions > General",
            "Workflow permissions",
            "Read and write permissions",
            "Allow GitHub Actions to create and approve pull requests",
            "Save",
            "repository administrator",
            "GITHUB_TOKEN",
            "not proof of effective permission",
        ):
            with self.subTest(required=required):
                self.assertIn(required, guide)

    def test_reusable_migration_template_has_manual_setup_checklist(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        for required in (
            "Manual one-time GitHub Actions repository setup",
            "- [ ]",
            "Settings > Actions > General",
            "Workflow permissions",
            "Read and write permissions",
            "Allow GitHub Actions to create and approve pull requests",
            "Save",
            "only for repositories requiring GitHub Actions to create PRs",
        ):
            with self.subTest(required=required):
                self.assertIn(required, template)

    def test_release_and_development_guides_link_to_mandatory_setup(self):
        for path in (DEVELOPMENT, RELEASE):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertIn("GITHUB_HOWTO.md", source)
                self.assertIn("manual repository setup", source)
                self.assertIn("GitHub Actions PR-creation permission", source)
                self.assertIn("nonpublishing", source)

    def test_documented_setup_does_not_equate_saved_settings_with_effective_permission(self):
        guide = GUIDE.read_text(encoding="utf-8")
        for required in (
            "repository administrator",
            "Settings > Actions > General",
            "Workflow permissions",
            "Read and write permissions",
            "Allow GitHub Actions to create and approve pull requests",
            "Save",
            "not proof of effective permission",
            "GITHUB_TOKEN",
            "nonpublishing",
            "Do not enable broad write permissions for repositories that do not need them",
        ):
            with self.subTest(required=required):
                self.assertIn(required, guide)
        self.assertIn("Independently verify", guide)
        self.assertIn("verified refs", guide)
        self.assertNotIn("Owner-confirmed Save on 2026-10-09", guide)


if __name__ == "__main__":
    unittest.main()
