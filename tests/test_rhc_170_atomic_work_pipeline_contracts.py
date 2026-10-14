"""RHC-170: adversarial contract tests for parallel, guarded atomic Work pipeline."""
import datetime as dt
import pathlib
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
import test_rhc_132_work_preflight_contracts as fixture
import rhc170_atomic_work_pipeline as pipeline

BASE = "a" * 40
NEXT = "b" * 40
COMMENT_ID = 3001
BRANCH_AT = "2026-10-10T21:01:00Z"


class FakeGateway:
    def __init__(self):
        self.issue = fixture.issue()
        self.comment = fixture.comment()
        self.main_sha = BASE
        self.work_sha = BASE
        self.calls = []
        self.lock = threading.Lock()
        self.main_reads = 0
        self.comment_reads = 0
        self.drift_main_at = 0
        self.corrupt_comment_at = 0
        self.fail = None
        self.runs = []

    def log(self, name):
        with self.lock:
            self.calls.append(name)
            if self.fail == name:
                raise ConnectionError("simulated unavailable API")

    def get_issue(self, number):
        self.log("issue")
        return dict(self.issue)

    def get_comment(self, comment_id):
        self.log("comment")
        with self.lock:
            self.comment_reads += 1
            count = self.comment_reads
        result = dict(self.comment)
        if count >= self.corrupt_comment_at > 0:
            result["body"] = result["body"].replace("### Evidence audit", "### altered")
        return result

    def get_main(self):
        self.log("main")
        with self.lock:
            self.main_reads += 1
            count = self.main_reads
        if count >= self.drift_main_at > 0:
            return "c" * 40
        return self.main_sha

    def get_work(self, number):
        self.log("work")
        return self.work_sha

    def list_work_runs(self, sha):
        self.log("ci_runs")
        return list(self.runs)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "model.go").write_text(fixture.MODEL, encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(fixture.CHANGELOG, encoding="utf-8")
        self.gh = FakeGateway()

    def invoke(self, **overrides):
        options = dict(gateway=self.gh, root=self.root, number=132,
                       comment_id=COMMENT_ID, pinned_main_sha=BASE,
                       branch_created_at=BRANCH_AT,
                       day=dt.date(2026, 10, 11),
                       apply=False, push=False,
                       owner_authorized_new_version=False)
        options.update(overrides)
        return pipeline.run(**options)

    def test_plan_default_never_commits_or_pushes(self):
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit") as commit, \
             mock.patch.object(pipeline, "push_with_lease") as push:
            result = self.invoke()
        self.assertEqual(result["status"], "PLAN_ONLY")
        self.assertEqual(result["to_version"], "3.0.8.13")
        self.assertEqual(result["allowed_paths"], ["CHANGELOG.md", "model.go"])
        self.assertEqual(result["mutations"], 0)
        self.assertTrue(result["timings"])
        commit.assert_not_called()
        push.assert_not_called()
        self.assertEqual(sorted(self.gh.calls), ["comment", "issue", "main", "work"])

    def test_plan_with_stale_main_or_work_ref_blocks(self):
        for selector in ("main_sha", "work_sha"):
            with self.subTest(selector=selector):
                f = FakeGateway()
                setattr(f, selector, "c" * 40)
                self.gh = f
                with self.assertRaises(ValueError):
                    self.invoke()
        self.assertNotIn("push", self.gh.calls)

    def test_malformed_identity_and_rolling_comment_block(self):
        for choice in ("state", "title", "comment", "clock", "labels"):
            with self.subTest(choice=choice):
                f = FakeGateway()
                if choice == "state":
                    f.issue["state"] = "closed"
                elif choice == "title":
                    f.issue["title"] = "[RHC-999] wrong"
                elif choice == "labels":
                    f.issue["labels"] = []
                elif choice == "comment":
                    f.comment["body"] = f.comment["body"].replace("### Evidence audit", "")
                elif choice == "clock":
                    f.comment["updated_at"] = "2026-10-11T22:00:00Z"
                self.gh = f
                with self.assertRaises(ValueError):
                    self.invoke()

    def test_mismatched_model_versions_and_changelog_block(self):
        for file, text in (("model.go", fixture.MODEL.replace(
                'referenceVersion = "3.0.8.12"', 'referenceVersion = "3.0.8.13"')),
                           ("CHANGELOG.md", "# Changelog\n\n## 3.0.8.10 — old\n")):
            with self.subTest(file=file):
                (self.root / file).write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.invoke()
                (self.root / file).write_text(
                    fixture.MODEL if file == "model.go" else fixture.CHANGELOG,
                    encoding="utf-8")

    def test_network_get_error_is_fail_closed_not_a_write(self):
        self.gh.fail = "issue"
        with self.assertRaises(ConnectionError):
            self.invoke()
        self.assertNotIn("push", self.gh.calls)

    def test_apply_requires_separate_new_version_authorization(self):
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit") as commit:
            with self.assertRaises(ValueError):
                self.invoke(apply=True)
            with self.assertRaises(ValueError):
                self.invoke(push=True)
            commit.assert_not_called()

    def test_apply_rechecks_sources_and_authoritative_live_state(self):
        events = []
        def make_commit(root, approved):
            events.append("commit")
            self.assertEqual(approved["base_main_sha"], BASE)
            self.assertEqual(approved["allowed_paths"], ["CHANGELOG.md", "model.go"])
            self.assertEqual(approved["bootstrap_comment_id"], COMMENT_ID)
            return NEXT
        def push(_root, branch, expected, next_sha):
            events.append("push")
            self.assertEqual((branch, expected, next_sha),
                             ("work/RHC-132", BASE, NEXT))
            self.gh.work_sha = NEXT
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit",
                               side_effect=make_commit):
            result = self.invoke(apply=True, push=True,
                                 owner_authorized_new_version=True,
                                 push_func=push)
        self.assertEqual(result["status"], "WORK_PUSH_VERIFIED")
        self.assertEqual(result["work_sha"], NEXT)
        self.assertEqual(events, ["commit", "push"])
        self.assertGreaterEqual(self.gh.calls.count("main"), 3)
        self.assertGreaterEqual(self.gh.calls.count("comment"), 2)
        self.assertEqual(result["mutations"], 2)

    def test_main_change_before_commit_blocks_without_mutation(self):
        self.gh.drift_main_at = 2
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit") as commit:
            with self.assertRaises(ValueError):
                self.invoke(apply=True, owner_authorized_new_version=True)
            commit.assert_not_called()

    def test_comment_update_during_preflight_blocks_without_mutation(self):
        self.gh.corrupt_comment_at = 2
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit") as commit:
            with self.assertRaises(ValueError):
                self.invoke(apply=True, owner_authorized_new_version=True)
            commit.assert_not_called()

    def test_main_change_after_local_commit_blocks_push(self):
        self.gh.drift_main_at = 3
        def deny(*_args):
            raise AssertionError("push must never be invoked")
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit",
                               return_value=NEXT):
            with self.assertRaises(ValueError):
                self.invoke(apply=True, push=True,
                            owner_authorized_new_version=True,
                            push_func=deny)

    def test_missing_remote_ack_reconciles_success_without_retry(self):
        count = []
        def once(_root, _branch, _base, _new):
            count.append(1)
            self.gh.work_sha = NEXT
            raise TimeoutError("response lost, push may have succeeded")
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit",
                               return_value=NEXT):
            result = self.invoke(apply=True, push=True,
                                 owner_authorized_new_version=True,
                                 push_func=once)
        self.assertEqual(result["status"], "WORK_PUSH_VERIFIED")
        self.assertTrue(result["push_response_uncertain"])
        self.assertEqual(len(count), 1)

    def test_missing_remote_ack_without_matching_head_blocks(self):
        count = []
        def once(_root, _branch, _base, _new):
            count.append(1)
            raise TimeoutError("could have failed")
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit",
                               return_value=NEXT):
            with self.assertRaises(ValueError):
                self.invoke(apply=True, push=True,
                            owner_authorized_new_version=True,
                            push_func=once)
        self.assertEqual(len(count), 1)
        self.assertEqual(self.gh.work_sha, BASE)

    def test_foreign_work_head_after_push_blocks(self):
        def misroute(_root, _branch, _base, _new):
            self.gh.work_sha = "d" * 40
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit",
                               return_value=NEXT):
            with self.assertRaises(ValueError):
                self.invoke(apply=True, push=True,
                            owner_authorized_new_version=True,
                            push_func=misroute)

    def test_ci_proof_exact_source_event_and_single_run(self):
        self.gh.runs = [dict(id=1, event="push", head_sha=NEXT,
                             name="RHC Infrastructure Qualification (nonpublishing)",
                             created_at="2026-10-11T21:01:00Z", status="in_progress",
                             conclusion=None),
                        dict(id=2, event="push", head_sha=NEXT,
                             name="RHC Development Completion (exact SHA gate)",
                             created_at="2026-10-11T21:01:00Z", status="queued",
                             conclusion=None)]
        evidence = pipeline.verify_ci_created(self.gh, NEXT,
                                               "2026-10-11T21:00:58Z")
        self.assertEqual(evidence["status"], "WORK_CI_CREATED_NOT_GREEN")
        self.assertEqual(evidence["runs"], [1, 2])
        self.assertNotIn("PASS", evidence["status"])

    def test_ci_proof_rejects_old_duplicate_foreign_or_fake_green(self):
        good = dict(id=1, event="push", head_sha=NEXT,
                    name="RHC Infrastructure Qualification (nonpublishing)",
                    created_at="2026-10-11T21:01:00Z", status="queued",
                    conclusion=None)
        for entries in ([good, dict(good)], [dict(good, head_sha=BASE)],
                        [dict(good, event="workflow_dispatch")],
                        [dict(good, created_at="2026-10-11T20:00:00Z")],
                        [dict(good, conclusion="success", status="queued")]):
            with self.subTest(entries=entries):
                self.gh.runs = entries
                with self.assertRaises(ValueError):
                    pipeline.verify_ci_created(self.gh, NEXT,
                                               "2026-10-11T21:00:58Z")

    def test_no_owner_authorization_cannot_mutate_even_with_ci_source(self):
        with mock.patch.object(pipeline.hotfix, "atomic_local_commit") as commit:
            for op in (dict(apply=True, push=True), dict(apply=True, push=False),
                       dict(apply=False, push=True)):
                with self.subTest(op=op), self.assertRaises(ValueError):
                    self.invoke(**op)
            commit.assert_not_called()

if __name__ == "__main__":
    unittest.main()
