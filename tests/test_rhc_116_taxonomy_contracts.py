"""RHC-116 negative contracts: Issue taxonomy, disposition, live GET, safe recovery."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from rhc_issue_init import (InitializationBlocked, initialize_issue,
                            verify_initialized_issue, issue_taxonomy,
                            audit, repair_issue_labels)

PATH_FAST = "Development path: dev-path: fast — bounded documentation update"
PATH_WORK = "Development path: dev-path: work-branch — cross-entrypoint infrastructure"
PATH_NA = "Development path: Not applicable — external legal clearance only"
PATH_PENDING = "Development path: PATH_DECISION_PENDING — owner must choose scope"


def row(labels=None, body=PATH_WORK, title="[RHC-116] GitHub workflow labels"):
    return dict(number=116, title=title, state="open", body=body,
                labels=[{"name": x} for x in (labels if labels is not None
                        else ["enhancement", "priority: high", "dev-ops", "dev-path: work-branch"])])


class Fake:
    def __init__(self):
        self.rows = {}
        self.next = 116
        self.writes = []
        self.fail_create = False
        self.no_number = False
        self.fail_rename = False
        self.stale = False

    def create(self, title, body, labels):
        self.writes.append(("create", title, list(labels)))
        self.rows[self.next] = dict(number=self.next, title=title, body=body,
                                    labels=[{"name": x} for x in labels], state="open")
        if self.fail_create:
            raise TimeoutError("create response lost")
        return {} if self.no_number else {"number": self.next}

    def search(self, title, body):
        return [dict(v) for v in self.rows.values()
                if v["title"] == title and v["body"] == body]

    def get(self, number):
        r=self.rows.get(number)
        return dict(r, title="outdated") if r and self.stale else dict(r) if r else None

    def update(self, number, title):
        self.writes.append(("rename", number, title))
        if self.fail_rename:
            raise TimeoutError("rename response lost")
        self.rows[number]["title"] = title

    def add_labels(self, number, labels):
        self.writes.append(("add_labels", number, list(labels)))
        self.rows[number]["labels"] += [{"name": n} for n in labels]

    def all_issues(self, *, state="all"):
        return iter(self.rows.values())


class Taxonomy(unittest.TestCase):
    def test_valid_fast_and_work_paths_with_reason(self):
        fast=row(["enhancement","priority: low","dev-path: fast"], PATH_FAST,
                 "[RHC-116] Update copyright wording")
        self.assertEqual(verify_initialized_issue(fast,116,for_development=True)["number"],116)
        self.assertEqual(verify_initialized_issue(row(),116,for_development=True)["number"],116)

    def test_type_priority_absent_duplicate_unknown_fail(self):
        base=["enhancement","priority: high","dev-ops","dev-path: work-branch"]
        for labels in (base[1:],base+["bug"],base[:1]+base[2:],
                       base+["priority: critical"],base+["priority: strange"],
                       base+["enhancement"]):
            with self.subTest(labels=labels),self.assertRaises(InitializationBlocked):
                verify_initialized_issue(row(labels),116,for_development=True)

    def test_path_missing_conflicting_pending_fail_for_development(self):
        base=["enhancement","priority: high","dev-ops"]
        for labels,body in ((base,PATH_WORK),(base+["dev-path: fast","dev-path: work-branch"],PATH_WORK),
                            (base,PATH_PENDING),(base+["dev-path: fast"],PATH_PENDING),
                            (base+["dev-path: fast"],PATH_NA)):
            with self.subTest(labels=labels,body=body),self.assertRaises(InitializationBlocked):
                verify_initialized_issue(row(labels,body),116,for_development=True)

    def test_pending_allowed_only_as_tracking_not_as_development(self):
        r=row(["enhancement","priority: high","dev-ops"],PATH_PENDING)
        self.assertEqual(verify_initialized_issue(r,116)["number"],116)
        with self.assertRaises(InitializationBlocked):
            verify_initialized_issue(r,116,for_development=True)

    def test_non_executable_reason_is_allowed_without_path(self):
        r=row(["enhancement","priority: high"],PATH_NA,
              "[RHC-116] External legal review")
        self.assertEqual(verify_initialized_issue(r,116)["number"],116)
        with self.assertRaises(InitializationBlocked):
            verify_initialized_issue(r,116,for_development=True)

    def test_non_executable_with_dev_path_or_false_reason_is_rejected(self):
        for body in ("Development path: Not applicable — do coding work",
                     "Development path: Not applicable — TBD",
                     "Development path: Not applicable — external", PATH_NA):
            r=row(["enhancement","priority: high","dev-path: fast"],body,
                  "[RHC-116] Implement GitHub workflow")
            with self.assertRaises(InitializationBlocked):
                verify_initialized_issue(r,116)

    def test_devops_work_area_missing_and_false_for_unrelated(self):
        r=row(["enhancement","priority: high","dev-path: work-branch"],PATH_WORK)
        with self.assertRaises(InitializationBlocked):
            verify_initialized_issue(r,116)
        r=row(["enhancement","priority: high","dev-ops","dev-path: fast"],
              PATH_FAST,"[RHC-116] Correct a public product description")
        with self.assertRaises(InitializationBlocked):
            verify_initialized_issue(r,116)

    def test_correct_title_wrong_labels_and_correct_labels_wrong_title(self):
        with self.assertRaises(InitializationBlocked):
            verify_initialized_issue(row(["enhancement"]),116)
        with self.assertRaises(InitializationBlocked):
            verify_initialized_issue(row(title="[RHC-117] GitHub workflow labels"),116)

    def test_single_create_sets_all_labels_and_reads_back_both(self):
        g=Fake()
        labels=["enhancement","priority: high","dev-ops","dev-path: work-branch"]
        result=initialize_issue(g,"GitHub workflow labels",PATH_WORK,labels,
                                nonce="aabbccddeeff")
        self.assertEqual(result["number"],116)
        self.assertEqual(g.writes[0],("create","Initializing RHC Issue: GitHub workflow labels [init-aabbccddeeff]",labels))
        self.assertEqual([w[0] for w in g.writes],["create","rename"])
        self.assertEqual(result["title"],"[RHC-116] GitHub workflow labels")

    def test_ambiguous_response_recovered_without_second_create(self):
        for attr in ("fail_create","no_number"):
            g=Fake()
            setattr(g,attr,True)
            result=initialize_issue(g,"GitHub workflow labels",PATH_WORK,
                     ["enhancement","priority: high","dev-ops","dev-path: work-branch"],nonce="aabbccddeeff")
            self.assertEqual(result["number"],116)
            self.assertEqual(len([w for w in g.writes if w[0]=="create"]),1)

    def test_rename_stale_get_never_passes(self):
        g=Fake()
        g.stale=True
        with self.assertRaises(InitializationBlocked):
            initialize_issue(g,"GitHub workflow labels",PATH_WORK,
                     ["enhancement","priority: high","dev-ops","dev-path: work-branch"],nonce="aabbccddeeff")
        self.assertEqual(len([w for w in g.writes if w[0]=="create"]),1)

    def test_no_labels_created_when_invalid_input(self):
        for labels in ([],["enhancement","priority: high"],["bug","enhancement","priority: high"],
                       ["enhancement","priority: high","dev-path: fast","dev-path: work-branch"]):
            g=Fake()
            with self.subTest(labels=labels),self.assertRaises(InitializationBlocked):
                initialize_issue(g,"GitHub workflow labels",PATH_WORK,labels,nonce="aabbccddeeff")
            self.assertFalse(g.writes)

    def test_additive_backfill_without_removal_and_readback(self):
        g=Fake()
        r=row(["enhancement","dev-ops","dev-path: work-branch"])
        g.rows[116]=r
        repaired=repair_issue_labels(g,116,["priority: high"])
        self.assertEqual(issue_taxonomy(repaired,for_development=True)["priority"],"priority: high")
        self.assertEqual([w[0] for w in g.writes],["add_labels"])
        self.assertIn("dev-ops",[n["name"] for n in g.rows[116]["labels"]])

    def test_audit_excludes_pull_requests_and_reports_missing_labels(self):
        g=Fake()
        g.rows[116]=row()
        g.rows[117]=dict(number=117,title="[RHC-117] Other",body=PATH_PENDING,
                         state="open",labels=[],pull_request={"url":"pr"})
        g.rows[118]=dict(row(["enhancement"],title="[RHC-118] GitHub workflow labels"), number=118)
        output=audit(g)
        self.assertEqual(output["checked"],2)
        self.assertEqual(len(output["malformed"]),1)
        self.assertEqual(output["malformed"][0]["number"],118)
        self.assertTrue(all(w[0] not in ("create","rename","add_labels") for w in g.writes))


if __name__ == "__main__":
    unittest.main()
