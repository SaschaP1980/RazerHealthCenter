"""RHC-212: reject false end-to-end KPI evidence; simulate exact GitHub proof."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import rhc190_e2e_timeline as t

REPO=t.REPO
SHA="a"*40
MAIN="b"*40
def at(seconds):
    return f"2026-10-16T04:{seconds//60:02d}:{seconds%60:02d}Z"
def run(id_,sha,event,start,end,name="audited CI"):
    return dict(id=id_,head_sha=sha,event=event,status="completed",
                conclusion="success",run_attempt=1,name=name,
                created_at=at(start),updated_at=at(end))
def jobs(run_,count,base):
    return dict(total_count=count,jobs=[
        dict(id=base+i,run_id=run_["id"],name=f"hosted-job-{i}",
             status="completed",conclusion="success",
             completed_at=at(int(run_["updated_at"][14:16])*60+
                             int(run_["updated_at"][17:19])-count+i))
        for i in range(count)])
def fixture():
    cand=run(10,SHA,"push",15,35)
    pub=run(11,SHA,"workflow_dispatch",40,75)
    ver=run(12,MAIN,"workflow_dispatch",80,105,
            "RHC Independent Postrelease Verification")
    cand["path"]=".github/workflows/rhc-candidate-preflight.yml"
    pub["path"]=".github/workflows/rhc-reusable-interim-release.yml"
    ver["path"]=".github/workflows/rhc-postrelease-verification.yml"
    return dict(repository=REPO,issue_number=212,candidate_sha=SHA,main_sha=MAIN,
        issue=dict(number=212,title="[RHC-212] example",state="closed",
                   created_at=at(0),closed_at=at(120)),
        candidate=cand,publisher=pub,rhc102=ver,
        candidate_jobs=jobs(cand,3,100),publisher_jobs=jobs(pub,4,200),
        rhc102_jobs=jobs(ver,3,300),
        pr=dict(number=23,merged=True,state="closed",merged_at=at(76),
                merge_commit_sha=MAIN,base=dict(ref="main")))
def client():
    return dict(schema=t.CLIENT,issue=212,candidate_sha=SHA,
        first_tool_utc=at(1),ref_write_start_utc=at(7),ref_write_ack_utc=at(9),
        ref_write_duration_ms=2000,
        capture_method="CLIENT_INSTRUMENTED_TOOL_ENTRY_AND_REF_WRITE_BRACKET")
class Contracts(unittest.TestCase):
    def test_full_real_github_evidence_does_not_fake_first_tool_or_ref_creation(self):
        r=t.build_report(fixture())
        self.assertEqual(r["public_verification"],"PASS_3_REAL_HOSTED_JOBS_GITHUB_SERVER")
        self.assertEqual(r["server_metrics"]["issue_to_ci_seconds"],15)
        self.assertEqual(r["server_metrics"]["issue_to_pr_merge_seconds"],76)
        self.assertIsNone(r["client_observation"]["first_tool_to_ci_seconds"])
        self.assertIsNone(r["actual_ref_created_utc"])
        self.assertIsNone(r["p95_seconds"])
        self.assertEqual(r["original_first_tool_to_ci_kpi"],"NOT_VERIFIED")
        self.assertEqual(r["server_metrics"]["issue_to_close_seconds"],120)

    def test_client_observer_is_not_git_server_attested_and_bracket_is_bounded(self):
        doc=fixture();doc["client_observation"]=client()
        r=t.build_report(doc)
        c=r["client_observation"]
        self.assertEqual(c["first_tool_to_ci_seconds"],14)
        self.assertEqual(c["ref_to_ci_lower_seconds"],6)
        self.assertEqual(c["ref_to_ci_upper_seconds"],8)
        self.assertEqual(c["kpi_first_tool_120s"],"NOT_VERIFIED_CLOCK_DOMAIN")
        self.assertIn("NOT_VERIFIED",c["kpi_ref_to_ci_45s"])
        self.assertEqual(r["original_first_tool_to_ci_kpi"],"CLIENT_ONLY_CLOCK_SYNC_NOT_VERIFIED")

    def test_missing_bad_client_time_never_falls_back_to_issue_creation(self):
        for bad in [dict(client(),candidate_sha=MAIN),
                    dict(client(),ref_write_ack_utc=at(5)),
                    dict(client(),first_tool_utc=None),
                    dict(client(),ref_write_duration_ms=-1),
                    dict(client(),ref_write_duration_ms=30000),
                    dict(client(),capture_method="GITHUB_AUTHORITATIVE"),
                    dict(client(),GH_TOKEN="fake")]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                doc=fixture();doc["client_observation"]=bad;t.build_report(doc)

    def test_every_mandatory_job_gate_real_and_exact_sha(self):
        for part in ("candidate","publisher","rhc102"):
            for mutation in ({"conclusion":"failure"},{"status":"queued"},{"head_sha":MAIN if part!="rhc102" else SHA}):
                with self.subTest(part=part,mutation=mutation),self.assertRaises(ValueError):
                    doc=fixture();doc[part].update(mutation);t.build_report(doc)
            with self.subTest(part=part,mutation="wrong job total"),self.assertRaises(ValueError):
                doc=fixture();doc[part+"_jobs"]["total_count"]=0;t.build_report(doc)
            with self.subTest(part=part,mutation="job skipped"),self.assertRaises(ValueError):
                doc=fixture();doc[part+"_jobs"]["jobs"][0]["conclusion"]="skipped";t.build_report(doc)
            with self.subTest(part=part,mutation="job stale"),self.assertRaises(ValueError):
                doc=fixture();doc[part+"_jobs"]["jobs"][0]["run_attempt"]=2;t.build_report(doc)

    def test_reject_wrong_pr_merge_and_nonmonotone_timestamp(self):
        for key,value in (("merge_commit_sha",SHA),("merged",False),
                          ("state","open"),("merged_at",None)):
            with self.subTest(field=key),self.assertRaises(ValueError):
                doc=fixture();doc["pr"][key]=value;t.build_report(doc)
        with self.assertRaises(ValueError):
            doc=fixture();doc["rhc102"]["updated_at"]=at(70);t.build_report(doc)
        with self.assertRaises(ValueError):
            doc=fixture();doc["issue"]["closed_at"]=at(5);t.build_report(doc)

    def test_historical_unclosed_release_remains_unclosed(self):
        doc=fixture();doc["issue"]["closed_at"]=None;doc["issue"]["state"]="open"
        r=t.build_report(doc)
        self.assertIsNone(r["server_metrics"]["issue_to_close_seconds"])
        self.assertIsNone(r["server_times"]["issue_closed_utc"])

    def test_no_mutating_transport_or_foreign_paths(self):
        route="issues/212"
        with patch.dict(os.environ,{"GH_TOKEN":"dummy"}):
            with patch.object(t.subprocess,"run") as call:
                call.return_value=Mock(returncode=0,stdout='{"number":212}')
                self.assertEqual(t._get(REPO,route)["number"],212)
                self.assertEqual(call.call_args.args[0][:4],["gh","api","--method","GET"])
                with self.assertRaises(ValueError):
                    t._get(REPO,"git/refs/heads/main")
                self.assertEqual(call.call_count,1)

    def test_offline_cli_generates_audited_file_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            inp=Path(td)/"fixture.json";out=Path(td)/"report.json"
            inp.write_text(json.dumps(fixture()))
            self.assertEqual(t.main(["--fixture",str(inp),"--out",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["issue"],212)
            self.assertEqual(t.main(["--fixture",str(inp),"--out",str(out)]),1)

    def test_no_nonpublishing_product_modification(self):
        contents=(Path(__file__).resolve().parents[1]/"tools/rhc190_e2e_timeline.py").read_text()
        self.assertIn('["gh","api","--method","GET"',contents)
        self.assertNotIn("git push",contents)
        self.assertNotIn("gh workflow run",contents)
        self.assertNotIn("contents: write",contents)

if __name__=="__main__":
    unittest.main()
