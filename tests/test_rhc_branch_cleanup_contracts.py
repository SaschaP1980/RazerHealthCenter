"""RHC-10 branch cleanup contract tests; all external commands are mocked."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "tools" / "rhc_branch_cleanup.py"
spec = importlib.util.spec_from_file_location("rhc_branch_cleanup", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

REPO = "SaschaP1980/RazerHealthCenter"
HEAD, MERGE, MAIN = "a" * 40, "b" * 40, "c" * 40


class Cleanup(unittest.TestCase):
    def setUp(self):
        self.branch = "work/RHC-5"
        self.pr = {
            "number": 9, "state": "closed", "merged": True,
            "merged_at": "2026-10-08T09:22:16Z", "merge_commit_sha": MERGE,
            "base": {"ref": "main", "repo": {"full_name": REPO}},
            "head": {"ref": self.branch, "sha": HEAD,
                     "repo": {"full_name": REPO}},
        }
        self.refs = {self.branch: HEAD}
        self.commands = []

    def get(self, path):
        if path == "repos/" + REPO + "/pulls/9":
            return self.pr
        if path == "repos/" + REPO + "/branches/main":
            return {"commit": {"sha": MAIN}}
        for old in [HEAD, MERGE]:
            if path == "repos/" + REPO + "/compare/" + old + "..." + MAIN:
                return {"status": "ahead", "behind_by": 0,
                        "merge_base_commit": {"sha": old}}
        raise AssertionError("unexpected mock request: " + path)

    def git(self, args):
        self.commands.append(args)
        if args[:3] == ["git", "ls-remote", "--heads"]:
            branch = args[4].removeprefix("refs/heads/")
            if branch not in self.refs:
                return ""
            return self.refs[branch] + "\trefs/heads/" + branch + "\n"
        if args[:2] == ["git", "push"]:
            self.assertEqual(args, ["git", "push",
                             "--force-with-lease=refs/heads/" + self.branch + ":" + HEAD,
                             "origin", ":refs/heads/" + self.branch])
            if self.refs[self.branch] != HEAD:
                raise m.Blocked("remote lease rejection")
            del self.refs[self.branch]
            return ""
        raise AssertionError("unexpected git request: " + repr(args))

    def run(self, execute=True):
        return m.cleanup(9, REPO, execute=execute, get=self.get, run=self.git)

    def test_merged_head_deleted_under_atomic_lease(self):
        self.assertEqual(self.run()["status"], "deleted")
        self.assertNotIn(self.branch, self.refs)

    def test_dry_run_keeps_branch(self):
        self.assertEqual(self.run(execute=False)["status"], "would-delete")
        self.assertIn(self.branch, self.refs)
        self.assertFalse(any(x[1] == "push" for x in self.commands))

    def test_missing_branch_is_idempotent(self):
        self.refs.clear()
        self.assertEqual(self.run()["status"], "already-absent")

    def test_open_or_unmerged_pr_blocks(self):
        self.pr["merged"] = False
        with self.assertRaises(m.Blocked):
            self.run()
        self.assertFalse(self.commands)

    def test_wrong_repo_blocks(self):
        self.pr["head"]["repo"]["full_name"] = "someone/fork"
        with self.assertRaises(m.Blocked):
            self.run()

    def test_wrong_base_blocks(self):
        self.pr["base"]["ref"] = "dev"
        with self.assertRaises(m.Blocked):
            self.run()

    def test_branch_advanced_blocks(self):
        self.refs[self.branch] = "d" * 40
        with self.assertRaisesRegex(m.Blocked, "advanced"):
            self.run()
        self.assertFalse(any(x[1] == "push" for x in self.commands))

    def test_nonancestor_head_blocks(self):
        orig = self.get
        def reject(path):
            if path.endswith("compare/" + HEAD + "..." + MAIN):
                return {"status": "diverged", "behind_by": 1,
                        "merge_base_commit": {"sha": "d" * 40}}
            return orig(path)
        with self.assertRaisesRegex(m.Blocked, "head not contained"):
            m.cleanup(9, REPO, execute=True, get=reject, run=self.git)

    def test_nonancestor_merge_commit_blocks(self):
        orig = self.get
        def reject(path):
            if path.endswith("compare/" + MERGE + "..." + MAIN):
                return {"status": "diverged", "behind_by": 1,
                        "merge_base_commit": {"sha": "d" * 40}}
            return orig(path)
        with self.assertRaisesRegex(m.Blocked, "merged commit"):
            m.cleanup(9, REPO, execute=True, get=reject, run=self.git)

    def test_pr_number_mismatch_blocks(self):
        self.pr["number"] = 2
        with self.assertRaisesRegex(m.Blocked, "wrong PR"):
            self.run()

    def test_unsafe_branch_names_are_blocked(self):
        for unsafe in ["main", "release/v3.0.9", "candidate/v3.0.9",
                       "work/RHC-10/../../main", "work/other",
                       "import/RHC-1-v3.0.8;echo BAD"]:
            self.assertFalse(m.BRANCH.fullmatch(unsafe), unsafe)

    def test_known_branch_forms_are_allowed(self):
        for safe in ["work/RHC-10", "work/RHC-5",
                     "import/RHC-1-v3.0.8", "license/RHC-6-gpl3"]:
            self.assertTrue(m.BRANCH.fullmatch(safe), safe)

    def test_stale_branch_after_push_fails_postverification(self):
        orig = self.git
        def no_op(args):
            if args[:2] == ["git", "push"]:
                self.commands.append(args)
                return ""  # unexpected success with ref still live
            return orig(args)
        with self.assertRaisesRegex(m.Blocked, "still exists"):
            m.cleanup(9, REPO, execute=True, get=self.get, run=no_op)

    def test_failed_sha_lease_preserves_updated_branch(self):
        orig = self.git
        def concurrent_advance(args):
            if args[:2] == ["git", "push"]:
                self.refs[self.branch] = "d" * 40
                raise m.Blocked("remote lease rejection")
            return orig(args)
        with self.assertRaisesRegex(m.Blocked, "lease rejection"):
            m.cleanup(9, REPO, execute=True, get=self.get, run=concurrent_advance)
        self.assertEqual(self.refs[self.branch], "d" * 40)


if __name__ == "__main__":
    unittest.main()
