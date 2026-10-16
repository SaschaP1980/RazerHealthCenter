"""RHC-190: no forged Work evidence during branchless Issue closure."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import rhc190_fast_closure as fast
from test_rhc_158_release_closure_contracts import Fake, BASE, SOURCE, MAIN

class FastClosureTests(unittest.TestCase):
    def fixture(self):
        f=Fake()
        f.git[SOURCE]["message"]=(
            "candidate v3.0.8.16\nMain-SHA: "+BASE+
            "\nRHC-Issue: 158\nDevelopment-Path: fast\n")
        f.issue["labels"]=[
            {"name":"enhancement"},{"name":"priority: high"},
            {"name":"dev-ops"},{"name":"dev-path: fast"}]
        f.issue["body"]=("Development path: dev-path: fast — "
                         "Issue-authorized narrow branchless product release")
        f.pr["body"]="Refs #158; sourceSha "+SOURCE+"; Development-Path fast"
        self.assertEqual(f.latest["sourceSha"],SOURCE)
        return f
    def test_read_only_exact_four_run_qualified(self):
        f=self.fixture()
        p=fast.close_fast(f,512,SOURCE,apply=False)
        self.assertEqual(p["status"],"READY_PLAN_ONLY")
        self.assertEqual(p["pr"],199)
    def test_wrong_label_source_and_job_block(self):
        for which in ("path","tag","candidate_jobs","download_jobs",
                      "source","pr","main","duplicate"):
            f=self.fixture()
            if which=="path": f.issue["labels"][-1]={"name":"dev-path: work-branch"}
            if which=="tag": f.tag_sha="0"*40
            if which=="candidate_jobs": f.jobs[702]=0
            if which=="download_jobs": f.jobs[703]=0
            if which=="source": f.git[SOURCE]["message"]+="Work-SHA: "+"b"*40+"\n"
            if which=="pr": f.pr["body"]="Refs #999"
            if which=="main": f.pr["base"]["sha"]="f"*40
            if which=="duplicate":
                original_find = f.find_success_runs
                def duplicated_runs(sha,event):
                    rows = original_find(sha,event)
                    if sha == SOURCE and event == "workflow_dispatch":
                        rows = rows + [dict(f.get_run(702), id=711)]
                    return rows
                f.find_success_runs = duplicated_runs
            with self.subTest(which=which),self.assertRaises(ValueError):
                fast.close_fast(f,512,SOURCE,apply=False)
    def test_comment_and_close_only_with_full_hosted_proof(self):
        f=self.fixture()
        ops=[]
        def api(method,path,payload=None):
            ops.append((method,path,payload))
            if method=="POST":
                f.comments.append({"id":999,"body":payload["body"]})
            return {}
        def update_issue(number,state):
            self.assertEqual(number,158)
            self.assertEqual(state,"closed")
            f.issue.update(state="closed",state_reason="completed",
                           closed_at="2026-10-15T08:30:00Z")
        f.create_fast_audit_comment=lambda number,body: api(
            "POST",f"issues/{number}/comments",{"body":body})
        f.update_issue=update_issue
        p=fast.close_fast(f,512,SOURCE,apply=True)
        self.assertEqual(p["status"],"COMPLETED")
        self.assertEqual(len(ops),1)
        self.assertEqual(fast.close_fast(f,512,SOURCE,apply=True)["status"],
                         "ALREADY_COMPLETED")
if __name__=="__main__": unittest.main()
