"""RHC-34 automatic interim postmerge exact-source/QA gate contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class InterimPostmergeContract(unittest.TestCase):
    def test_tagging_requires_actual_merged_release_pr_and_readback(self):
        s=(ROOT/".github/workflows/rhc-interim-postmerge-v3081.yml").read_text(encoding="utf-8")
        for needle in (
            "pull_request:", "types: [closed]", "merged == true",
            "head.ref == 'release/v3.0.8.1'", "base.ref == 'main'",
            "contents: write", "RHC34_POSTMERGE_RELEASE_SUCCESS",
            "75b9209a90a192dba5f22665720a048195dc6881",
            "c7a7ac150d236e85710454c61c806a6f3f4fb400d5309487ecbb88746f28c4c8",
            "rhc_downloads.py", "tests -p 'test_rhc_downloads_contracts.py'",
            "RHC34_PRETAG_RELEASE_PROVENANCE=PASS",
            "git diff --name-only \"$SOURCE_SHA\" \"$FIRST\"",
            "gh api \"repos/$GITHUB_REPOSITORY/branches/main\"",
            "source=$SOURCE_SHA main=$MERGED_SHA",
            "git/ref/tags/v3.0.8.1", "git/refs/heads/release/v3.0.8.1",
        ):
            self.assertIn(needle,s)
        for forbidden in (
            "rollbackVerified=true", "productionEnabled=true",
            "signingDecision: unsigned-approved", "gh release create",
            "EXPLICIT_OWNER_RHC22",
        ):
            self.assertNotIn(forbidden,s)


    def test_tag_recovery_requires_audited_merges_without_owner_phase_b(self):
        script=(ROOT/".github/workflows/rhc-interim-postmerge-v3081.yml").read_text(encoding="utf-8")
        for needle in (
            "push:", "RHC34_TAG_RECOVERY_SUCCESS",
            "d2509511ee913689e2d514dc72202d969ca60247",
            "90fe14f47c826e89a26b9a7a1dde97eac7e02fac",
            "gh api -X POST",
            "RHC34_RECOVERY_PRETAG=PASS",
            "work/RHC-34-fixture",
            "sourceSha", "source=$SOURCE_SHA",
        ):
            self.assertIn(needle,script)
        self.assertIn("github.event_name == 'push'",script)
        self.assertIn("RHC34_RECOVERY_PRETAG=PASS",script)
        self.assertIn("git merge-base --is-ancestor",script)
        self.assertIn("grep -q '404'",script)
        self.assertIn("gh api -X DELETE",script)
        self.assertIn("RHC34_RECOVERY_TAG=PASS",script)
        self.assertIn("RHC34_POSTMERGE_RELEASE_SUCCESS",script)
        self.assertNotIn("EXPLICIT_OWNER_RHC22",script)

    def test_null_safe_postdelete_cleanup_handles_already_removed_ref(self):
        workflow=(ROOT/".github/workflows/rhc-interim-postmerge-v3081.yml").read_text(encoding="utf-8")
        self.assertIn("--jq '.object.sha // empty'",workflow)
        self.assertGreaterEqual(workflow.count("--jq '.object.sha // empty'"), 4)
        self.assertIn("RHC34_TAG_RECOVERY_SUCCESS",workflow)
        self.assertIn("delete_safe release/v3.0.8.1",workflow)
        self.assertIn("work/RHC-34-fixture",workflow)
        self.assertIn("work/RHC-34-tagfix",workflow)
        self.assertIn("work/RHC-34-cleanup",workflow)
        self.assertIn("git merge-base --is-ancestor",workflow)

if __name__=="__main__":
    unittest.main()
