"""RHC-43: repeatable interim source tag and safe release-branch cleanup."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / ".github/workflows/rhc-reusable-interim-postmerge.yml"
RECOVERY = ROOT / ".github/workflows/rhc-reusable-interim-recovery.yml"
GENERIC = ROOT / ".github/workflows/rhc-branch-cleanup.yml"


class ReusableFinalizerContract(unittest.TestCase):
    def test_future_postmerge_handles_missing_tag_and_fails_closed_on_mismatch(self):
        script = POST.read_text(encoding="utf-8")
        self.assertIn('gh api "$TAG_ENDPOINT" > "$RUNNER_TEMP/tag-existing.json"', script)
        self.assertIn("tag-existing.err", script)
        self.assertIn('jq -er \'\x2eobject.sha | select(type=="string")\'', script)
        self.assertIn('test "$BEFORE" = "$SOURCE"', script)
        self.assertIn('test "$FOUND" = "$SOURCE"', script)
        self.assertIn('refs/tags/v$VERSION', script)
        self.assertIn("needs.linux.result == 'success'", script)
        self.assertIn("needs.windows.result == 'success'", script)

    def test_raw_tag_lookup_rejects_wrong_existing_sha_and_non404_api_failures(self):
        for path in (POST, RECOVERY):
            with self.subTest(path=path):
                script = path.read_text(encoding="utf-8")
                self.assertIn('gh api "$TAG_ENDPOINT" > "$RUNNER_TEMP/tag-existing.json"', script)
                self.assertIn("tag-existing.err", script)
                self.assertIn("Tag lookup API failure", script)
                self.assertIn("Existing immutable source tag", script)
                self.assertIn("Tag write ambiguous or denied", script)

    def test_future_postmerge_owns_exclusively_verified_release_cleanup(self):
        script = POST.read_text(encoding="utf-8")
        self.assertIn("--force-with-lease=refs/heads/release/v$VERSION:$STAGED_SHA", script)
        self.assertIn('test "$REMOTE" = "$STAGED_SHA"', script)
        self.assertIn('test -z "$(git ls-remote origin "refs/heads/release/v$VERSION")"', script)
        self.assertIn("persist-credentials: true", script)

    def test_generic_work_cleaner_explicitly_skips_release_branches(self):
        script = GENERIC.read_text(encoding="utf-8")
        self.assertIn("!startsWith(github.event.pull_request.head.ref, 'release/v')", script)
        # Generic cleaner must never accept the release branch as a work branch.
        import importlib.util
        p = ROOT / "tools/rhc_branch_cleanup.py"
        spec = importlib.util.spec_from_file_location("rhc_branch_cleanup", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertFalse(mod.BRANCH.fullmatch("release/v3.0.8.2"))

    def test_published_release_recovery_is_idempotent_and_live_verified(self):
        script = RECOVERY.read_text(encoding="utf-8")
        for required in (
            "name: RHC Reusable Interim Published Release Recovery",
            "branches: [main]",
            "rhc-reusable-interim-recovery.yml",
            "workflow_dispatch:",
            "needs: [verify_linux, verify_windows]",
            "windows-2025",
            "Get-AuthenticodeSignature",
            "NotSigned",
            "rhc_downloads.py",
            "git rev-list --first-parent",
            "sourceSha",
            "releases.json",
            "latest.json",
            "'.object.sha // empty'",
            "refs/tags/v$VERSION",
            "git push --force-with-lease=refs/heads/release/v$VERSION:$STAGED_SHA",
            "RHC_REUSABLE_RECOVERY_VERIFIED",
        ):
            with self.subTest(required=required):
                self.assertIn(required, script)
        self.assertNotIn("productionEnabled=true", script)
        self.assertNotIn("rollbackVerified=true", script)

    def test_recovery_verifies_actual_merged_pr_detail_not_missing_list_boolean(self):
        # Real recovery #37898054100: GitHub REST list /pulls omits merged.
        # The list identifies exactly one merged_at PR by hashes and repo;
        # authoritative /pulls/{number} must then prove merged=true.
        script = RECOVERY.read_text(encoding="utf-8")
        self.assertIn(".merged_at!=null", script)
        self.assertIn('PR_NUMBER="$(jq -r', script)
        self.assertIn('gh api "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"', script)
        self.assertIn(".merged==true", script)
        self.assertNotIn(".merged==true and .merge_commit_sha==$merge", script)

    def test_standing_owner_unsigned_release_acceptance_is_nonnormative_for_standard_production(self):
        docs = (ROOT / "docs/REUSABLE_INTERIM_RELEASE_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("UNTIL EXPLICITLY REVOKED", docs)
        self.assertIn("NOT A RELEASE BLOCKER", docs)
        self.assertIn("productionEnabled=false", docs)
        self.assertIn("NOT_VERIFIED", docs)


if __name__ == "__main__":
    unittest.main()
