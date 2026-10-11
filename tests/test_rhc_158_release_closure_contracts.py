"""RHC-158 RED-first: release close integration cannot trust workflow success alone."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc158_release_closure as rc

BASE = "a" * 40
WORK = "b" * 40
SOURCE = "c" * 40
STAGE = "d" * 40
MAIN = "e" * 40


class Fake:
    def __init__(self):
        self.publisher = 512
        self.issue_id = 158
        self.issue = {"number": 158, "state": "open", "title": "[RHC-158] GitHub CI guarded closure"}
        self.run = {"id": 512, "name": "RHC Reusable Interim Unsigned Release",
                    "status": "completed", "conclusion": "success",
                    "event": "workflow_dispatch", "head_sha": SOURCE,
                    "head_branch": "candidate/v3.0.8.16",
                    "actor": {"login": "github-actions[bot]"}, "run_attempt": 1}
        self.latest = {"version": "3.0.8.16", "sourceSha": SOURCE,
                       "sha256": "f" * 64, "size": 888}
        self.git = {
            SOURCE: {"sha": SOURCE, "tree": {"sha": "1" * 40},
                     "parents": [{"sha": BASE}],
                     "message": ("candidate v3.0.8.16\n"
                                 "Work-SHA: " + WORK + "\n"
                                 "Main-SHA: " + BASE + "\n"
                                 "RHC-Issue: 158\n")},
            WORK: {"sha": WORK, "tree": {"sha": "1" * 40},
                   "parents": [{"sha": BASE}],
                   "message": "work\nRHC-Issue: 158\n"},
            STAGE: {"sha": STAGE, "tree": {"sha": "2" * 40},
                    "parents": [{"sha": SOURCE}],
                    "message": "release stage"},
        }
        self.pr = {"number": 199, "state": "closed", "merged": True,
                   "base": {"sha": BASE}, "head": {"sha": STAGE},
                   "merge_commit_sha": MAIN, "body": "Refs #158"}
        self.comments = [{"id": 220, "body": rc.ROLLING_ID_MARKER.format(issue=158)
                          + "\n" + "\n".join("### " + h + "\npass"
                          for h in rc.audit.HEADINGS)}]
        self.runs = {
            "work": {"id": 701, "head_sha": WORK, "event": "push"},
            "candidate": {"id": 702, "head_sha": SOURCE, "event": "workflow_dispatch"},
            "publisher": self.run,
            "downloads": {"id": 703, "head_sha": STAGE, "event": "workflow_dispatch"},
            "rhc102": {"id": 704, "head_sha": MAIN, "event": "workflow_dispatch"},
        }
        self.jobs = {701: 3, 702: 3, 512: 4, 703: 1, 704: 3}
        self.tag_sha = SOURCE

    def get_run(self, rid):
        if rid == 512: return dict(self.run)
        names = {"work": "RHC Infrastructure Qualification (nonpublishing)",
                 "candidate": "RHC Candidate Preflight (nonpublishing)",
                 "downloads": "RHC Repository Downloads Integrity (nonpublishing)",
                 "rhc102": "RHC POSTRELEASE v3.0.8.16 main:" + MAIN,
                 "double": "RHC Candidate Preflight (nonpublishing)"}
        matches = [(key, value) for key, value in self.runs.items()
                   if value["id"] == rid]
        if len(matches) != 1: raise ValueError("ambiguous real run")
        key, run = matches[0]
        return dict(run, name=names[key], status="completed",
                    conclusion="success", actor={"login":"github-actions[bot]"},
                    run_attempt=1)
    def get_jobs(self, rid): return [{"id": rid * 10 + x, "conclusion": "success",
                                      "status": "completed"} for x in range(self.jobs[rid])]
    def get_latest(self): return dict(self.latest)
    def get_main_sha(self): return MAIN
    def get_merge_parents(self, sha): return [BASE, STAGE]
    def get_tag(self, name): return self.tag_sha
    def get_pr(self, n): return dict(self.pr)
    def get_issue(self, n): return dict(self.issue)
    def list_release_prs(self, merged): return [dict(self.pr)]
    def list_issue_comments(self, n): return list(self.comments)
    def get_git_commit(self, sha): return dict(self.git[sha])
    def find_success_runs(self, sha, event):
        return [self.get_run(run["id"]) for key, run in self.runs.items()
                if run["head_sha"] == sha and run["event"] == event]


class ClosureIntegration(unittest.TestCase):
    def test_exact_verified_identity_and_run_ids_from_real_graph(self):
        f = Fake()
        p = rc.collect_release_proof(f, 512)
        self.assertEqual(p["issue"], 158)
        self.assertEqual(p["comment_id"], 220)
        self.assertEqual(p["work_sha"], WORK)
        self.assertEqual(p["source_sha"], SOURCE)
        self.assertEqual(p["stage_sha"], STAGE)
        self.assertEqual(p["merged_sha"], MAIN)
        self.assertEqual(p["run_ids"],
                         {"work":701,"candidate":702,"publisher":512,
                          "downloads":703,"rhc102":704})

    def test_untrusted_publisher_never_identifies_issue(self):
        for field, value in [
            ("conclusion", "failure"), ("status", "in_progress"),
            ("event", "pull_request"), ("head_sha", "f" * 40),
            ("head_branch", "work/RHC-158"),
            ("actor", {"login": "attacker"})]:
            with self.subTest(field=field):
                f = Fake()
                f.run[field] = value
                with self.assertRaises(ValueError):
                    rc.collect_release_proof(f, 512)

    def test_wrong_provenance_never_returns_proof(self):
        for mismatch in ["source_tree", "main_ancestor", "work_issue",
                         "tag", "stage_parent", "pr_ref", "issue_closed"]:
            with self.subTest(mismatch=mismatch):
                f = Fake()
                if mismatch == "source_tree": f.git[WORK]["tree"]["sha"] = "0" * 40
                if mismatch == "main_ancestor": f.git[SOURCE]["parents"][0]["sha"] = "f" * 40
                if mismatch == "work_issue": f.git[WORK]["message"] = "RHC-Issue: 9"
                if mismatch == "tag": f.tag_sha = "f" * 40
                if mismatch == "stage_parent": f.git[STAGE]["parents"][0]["sha"] = "f" * 40
                if mismatch == "pr_ref": f.pr["body"] = "Refs #999"
                if mismatch == "issue_closed": f.issue["state"] = "closed"
                with self.assertRaises(ValueError):
                    rc.collect_release_proof(f, 512)

    def test_missing_or_duplicate_hosted_jobs_or_run_identity_block(self):
        for corruption in ["missing", "duplicate", "zero_jobs", "wrong_sha"]:
            with self.subTest(corruption=corruption):
                f = Fake()
                if corruption == "missing": del f.runs["rhc102"]
                if corruption == "duplicate": f.runs["double"] = dict(f.runs["candidate"])
                if corruption == "zero_jobs": f.jobs[703] = 0
                if corruption == "wrong_sha": f.runs["downloads"]["head_sha"] = "9" * 40
                with self.assertRaises(ValueError):
                    rc.collect_release_proof(f, 512)

    def test_missing_or_noncanonical_rolling_blocks(self):
        for corruption in ["missing", "duplicate", "wrong_issue"]:
            with self.subTest(corruption=corruption):
                f=Fake()
                if corruption=="missing": f.comments=[]
                if corruption=="duplicate": f.comments=f.comments*2
                if corruption=="wrong_issue": f.comments[0]["body"]="## Wrong issue"
                with self.assertRaises(ValueError):
                    rc.collect_release_proof(f,512)

    def test_live_collection_detail_have_distinct_optional_fields(self):
        f = Fake()
        rows = f.find_success_runs(WORK, "push")
        row = dict(rows[0], optional_collection_field="not in details")
        self.assertEqual(rc.trusted_run(f, row, WORK,
            "RHC Infrastructure Qualification (nonpublishing)", "push", 3), 701)
        bad = dict(row, head_sha="0" * 40)
        with self.assertRaises(ValueError):
            rc.trusted_run(f, bad, WORK,
                "RHC Infrastructure Qualification (nonpublishing)", "push", 3)

    def test_operator_delegates_to_original_rhc139_audit(self):
        from unittest.mock import patch
        f=Fake()
        with patch.object(rc.audit, "finalize",
                          return_value={"status":"READY_PLAN_ONLY"}) as final:
            result=rc.close_release(f,512,apply=False)
        self.assertEqual(result["status"], "READY_PLAN_ONLY")
        self.assertFalse(final.call_args.kwargs["apply"])
        self.assertEqual(final.call_args.args[1]["run_ids"]["rhc102"], 704)

    def test_wiring_no_untrusted_pr_or_auto_product_release(self):
        s=(ROOT/".github/workflows/rhc158-release-closure.yml").read_text()
        self.assertIn("workflow_run:",s)
        self.assertIn("types: [completed]",s)
        self.assertIn("RHC Reusable Interim Unsigned Release",s)
        self.assertIn("issues: write",s)
        self.assertIn("pull-requests: read",s)
        self.assertIn("--publisher-run-id",s)
        self.assertIn("--apply",s)
        self.assertIn("rhc158_release_closure.py",s)
        self.assertNotIn("pull_request_target:",s)
        self.assertNotIn("productionEnabled=true",s)
        self.assertNotIn("gh pr merge",s)
        self.assertNotIn("workflow_dispatch:",s)
        self.assertNotIn("contents: write",s)

if __name__ == "__main__":
    unittest.main()
