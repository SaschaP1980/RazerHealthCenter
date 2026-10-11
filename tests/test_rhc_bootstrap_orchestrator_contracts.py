"""RHC-166 RED-first, then GREEN: saved Issue -> 13-section Work BOOTSTRAP.

No product release; mocks exercise the exact external sequence and safety.
"""
import datetime as dt
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_bootstrap_orchestrator as boot

BASE = "a" * 40
SUBJECT = "GitHub CI Work initialization acceleration"
BODY = ("Development path: dev-path: work-branch — "
        "implement guarded GitHub CI developer bootstrap")
LABELS = ["enhancement", "priority: high", "dev-path: work-branch", "dev-ops"]
TEMPLATE = (ROOT / "docs/templates/WORK_PATH_ROLLING_COMMENT.md").read_text()
CLOCK = dt.datetime(2026, 10, 11, 16, 45, 0, 123000, tzinfo=dt.timezone.utc)
MARKER = "RHC900CHAT1234ABCDEF89"


class Fake:
    def __init__(self):
        self.main = BASE
        self.issue = None
        self.comments = []
        self.branches = {}
        self.event = []
        self.fail_comment_create = False
        self.fail_comment_update = False
        self.fail_branch = False
        self.move_main_on_branch = False
        self.duplicate_comments = False
        self.corrupt_comment = False
        self.corrupt_issue = False

    def get_main(self):
        self.event.append("get_main")
        return self.main

    # RHC115 two-phase issue gateway:
    def create(self, title, body, labels):
        self.event.append("create_issue")
        self.issue = dict(number=900, title=title, body=body, state="open",
                          labels=[{"name": x} for x in labels],
                          created_at="2026-10-11T16:45:02Z")
        return dict(number=900)

    def search(self, title, body):
        self.event.append("search_issue")
        return [self.get(900)] if self.issue and self.issue["title"] == title and self.issue["body"] == body else []

    def update(self, number, title):
        self.event.append("rename_issue")
        self.issue["title"] = title

    def get(self, number):
        self.event.append("get_issue")
        if not self.issue or self.issue["number"] != number:
            raise ValueError("issue missing")
        result = dict(self.issue)
        if self.corrupt_issue:
            result["labels"] = [{"name": "enhancement"}]
        return result

    def list_comments(self, number):
        self.event.append("list_comments")
        return list(self.comments) * (2 if self.duplicate_comments else 1)

    def create_comment(self, number, body):
        self.event.append("create_comment")
        item = dict(id=5001, body=body,
                    created_at="2026-10-11T16:45:03Z",
                    updated_at="2026-10-11T16:45:03Z")
        self.comments.append(item)
        if self.fail_comment_create:
            raise TimeoutError("saved, network response lost")
        return item

    def get_comment(self, comment_id):
        self.event.append("get_comment")
        item = next((x for x in self.comments if x["id"] == comment_id), None)
        if item is None: raise ValueError("missing saved comment")
        result = dict(item)
        if self.corrupt_comment:
            result["body"] = result["body"].replace("### Evidence audit", "### WRONG")
        return result

    def update_comment(self, comment_id, body):
        self.event.append("update_comment")
        item = next(x for x in self.comments if x["id"] == comment_id)
        item["body"] = body
        item["updated_at"] = "2026-10-11T16:45:04Z"
        if self.fail_comment_update:
            raise TimeoutError("PATCH may have succeeded")

    def get_branch(self, name):
        self.event.append("get_branch")
        return self.branches.get(name)

    def create_branch(self, name, sha):
        self.event.append("create_branch")
        if self.move_main_on_branch:
            self.main = "b" * 40
        if self.fail_branch:
            raise TimeoutError("no response")
        if name in self.branches:
            raise ValueError("duplicate branch")
        self.branches[name] = sha
        return {"sha": sha, "ref": name, "created_at": "2026-10-11T16:45:06Z"}


def execute(g, **kw):
    return boot.run(g, repository="SaschaP1980/RazerHealthCenter",
                    subject=SUBJECT, issue_body=BODY, labels=LABELS,
                    template=TEMPLATE, pinned_main=BASE, marker=MARKER,
                    instant=CLOCK, clock=lambda: CLOCK + dt.timedelta(seconds=4), **kw)


class GuardedBootstrap(unittest.TestCase):
    def test_plan_is_read_only_and_requires_valid_inputs(self):
        f = Fake()
        result = execute(f, apply=False)
        self.assertEqual(result["status"], "PLAN_ONLY")
        self.assertFalse(f.event.count("create_issue"))
        self.assertFalse(f.event.count("create_comment"))
        self.assertFalse(f.event.count("create_branch"))

    def test_green_happy_path_uses_real_rhc115_and_complete_template(self):
        f = Fake()
        r = execute(f, apply=True)
        self.assertEqual(r["status"], "BOOTSTRAP_VERIFIED")
        self.assertEqual(r["issue"], 900)
        self.assertEqual(r["comment_id"], 5001)
        self.assertEqual(r["work_sha"], BASE)
        self.assertEqual(f.branches["work/RHC-900"], BASE)
        body = f.get_comment(5001)["body"]
        self.assertEqual(boot.extract_headings(body), boot.HEADINGS)
        self.assertIn("RHC900CHAT1234ABCDEF89", body)
        self.assertIn("**Bootstrap creation ISO timestamp:** " + chr(96) + "2026-10-11T16:45:00.123Z" + chr(96), body)
        self.assertIn("**Current phase:** WORK_CREATED", body)
        self.assertEqual(f.event.count("create_comment"), 1)
        self.assertEqual(f.event.count("create_branch"), 1)
        self.assertLess(f.event.index("create_comment"), f.event.index("create_branch"))
        self.assertGreaterEqual(f.event.count("get_comment"), 3)
        self.assertFalse(any("release" in action or "push" in action for action in f.event))

    def test_existing_issue_never_created_again(self):
        f = Fake()
        f.create("[RHC-900] " + SUBJECT, BODY, LABELS)
        f.event.clear()
        r = execute(f, apply=True, issue_number=900)
        self.assertEqual(r["status"], "BOOTSTRAP_VERIFIED")
        self.assertNotIn("create_issue", f.event)

    def test_ambiguous_comment_create_reconciles_with_get_once(self):
        f = Fake()
        f.fail_comment_create = True
        r = execute(f, apply=True)
        self.assertEqual(r["comment_id"], 5001)
        self.assertEqual(f.event.count("create_comment"), 1)

    def test_ambiguous_comment_update_readback_can_recover(self):
        f = Fake()
        f.fail_comment_update = True
        self.assertEqual(execute(f, apply=True)["status"], "BOOTSTRAP_VERIFIED")
        self.assertEqual(f.event.count("create_branch"), 1)

    def test_invalid_clock_and_missing_template_block_before_mutation(self):
        for kw in (
                {"instant": dt.datetime(2026, 10, 11, 16, 45)},
                {"template": TEMPLATE.replace("### Evidence audit", "### BROKEN")},
                {"marker": "unverified"},
                {"pinned_main": "bad"},
                {"labels": ["enhancement"]}):
            with self.subTest(kw=list(kw)):
                f = Fake()
                kwargs = dict(repository="SaschaP1980/RazerHealthCenter",
                              subject=SUBJECT, issue_body=BODY, labels=LABELS,
                              template=TEMPLATE, pinned_main=BASE,
                              marker=MARKER, instant=CLOCK, apply=True)
                kwargs.update(kw)
                with self.assertRaises(ValueError):
                    boot.run(f, **kwargs)
                self.assertNotIn("create_issue", f.event)
                self.assertNotIn("create_branch", f.event)

    def test_saved_noncanonical_comment_blocks_branch(self):
        f = Fake()
        f.corrupt_comment = True
        with self.assertRaises(ValueError):
            execute(f, apply=True)
        self.assertNotIn("create_branch", f.event)

    def test_foreign_existing_issue_blocks_new_comment(self):
        f = Fake()
        f.create("[RHC-900] " + SUBJECT, BODY, LABELS)
        f.corrupt_issue = True
        with self.assertRaises(ValueError):
            execute(f, apply=True, issue_number=900)
        self.assertNotIn("create_comment", f.event)

    def test_ambiguous_duplicate_comment_blocks(self):
        f = Fake()
        f.duplicate_comments = True
        with self.assertRaises(ValueError):
            execute(f, apply=True)
        self.assertNotIn("create_branch", f.event)

    def test_moved_main_blocks_branch(self):
        f = Fake()
        f.move_main_on_branch = True
        with self.assertRaises(ValueError):
            execute(f, apply=True)
        # Gateway pretends it raced during write; never falsely accept.
        self.assertNotIn("WORK_CREATED", str(f.comments[-1]["body"]))

    def test_stale_main_blocks_before_creating_issue(self):
        f = Fake()
        f.main = "b" * 40
        with self.assertRaises(ValueError):
            execute(f, apply=True)
        self.assertNotIn("create_issue", f.event)

    def test_existing_foreign_comment_never_overwritten(self):
        f = Fake()
        f.create("[RHC-900] " + SUBJECT, BODY, LABELS)
        f.comments = [dict(id=99, body="foreign comment",
                           created_at="2026-10-11T16:40:00Z",
                           updated_at="2026-10-11T16:40:00Z")]
        with self.assertRaises(ValueError):
            execute(f, apply=True, issue_number=900)
        self.assertNotIn("update_comment", f.event)
        self.assertNotIn("create_branch", f.event)

    def test_version_only_planning_reuses_rhc132_not_a_second_validator(self):
        f = Fake()
        result = execute(f, apply=True)
        model = 'package main\nconst (\n appVersion = "3.0.8.17"\n referenceVersion = "3.0.8.17"\n)\n'
        changelog = '# Changelog\n\n## 3.0.8.17 — previous\n\n- Initial.\n'
        info = boot.version_only_plan(
            saved_issue=f.get(900), saved_comment=f.get_comment(result["comment_id"]),
            number=900, main_sha=BASE, work_sha=BASE,
            branch_created_at=result["branch_created_at"],
            model=model, changelog=changelog, day=dt.date(2026, 10, 11))
        self.assertEqual(info["to_version"], "3.0.8.18")
        self.assertEqual(info["allowed_paths"], ["CHANGELOG.md", "model.go"])

if __name__ == "__main__":
    unittest.main()
