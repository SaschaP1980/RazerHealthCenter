"""RHC-202 RED: genuine GET-only hosted Phase D operator, three-sample audit."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from rhc190_phase_d_operator import measure, require_identity, safe_api_route
from rhc190_phase_d_aggregate import aggregate_samples, require_hosted_jobs
import hashlib
import base64
import copy

BASE="a"*40
WORK="b"*40
ISSUE=202
REPO="SaschaP1980/RazerHealthCenter"
VERSION="3.0.8.24"
HEADINGS=("Chat origin","Work-Path authorization and scope","Benchmark configuration",
"Validation plan and coverage","Measurement ledger","Development Completion attempts",
"Candidate Entry","Candidate attempts","Release","Final Release Verification",
"Performance result","Evidence audit","Plan-conformance assessment")

def file_content(value):
    return {"encoding":"base64","content":base64.b64encode(value.encode()).decode(),"sha":"c"*40}

def db():
    return {
       f"repos/{REPO}/branches/main":{"commit":{"sha":BASE}},
       f"repos/{REPO}/issues/{ISSUE}":{"number":ISSUE,"title":"[RHC-202] GitHub CI Phase D",
          "state":"open","body":"Development path: dev-path: work-branch",
          "labels":[{"name":x} for x in ("enhancement","priority: high","dev-path: work-branch","dev-ops")]},
       f"repos/{REPO}/issues/{ISSUE}/comments?per_page=100":[{"id":123,
           "body":"**Issue:** [RHC-202](https://github.com/SaschaP1980/RazerHealthCenter/issues/202)\n"+
           "\n".join("### "+h+"\n" for h in HEADINGS)}],
       f"repos/{REPO}/branches/work/RHC-{ISSUE}":{"commit":{"sha":WORK}},
       f"repos/{REPO}/contents/model.go?ref={BASE}":file_content(
           'const (\n appVersion = "3.0.8.24"\n referenceVersion = "3.0.8.24"\n)\n'),
       f"repos/{REPO}/contents/CHANGELOG.md?ref={BASE}":file_content(
           "# Changelog\n\n## 3.0.8.24 — 2026-10-15\n"),
       f"repos/{REPO}/contents/downloads/latest.json?ref={BASE}":file_content(
           '{"version":"3.0.8.24","sourceSha":"'+("d"*40)+'","sha256":"'+("e"*64)+'","size":8619988}'),
       f"repos/{REPO}/actions/runs?head_sha={WORK}&per_page=100":{
           "total_count":1,"workflow_runs":[{"id":991,"name":"RHC Infrastructure Qualification (nonpublishing)",
                  "head_sha":WORK,"event":"push","status":"queued","created_at":"2026-10-15T16:00:01Z"}]},
    }

class FakeGet:
    def __init__(self,values):
        self.values=values;self.paths=[]
    def __call__(self,path):
        self.paths.append(path)
        return copy.deepcopy(self.values[path])

class OperatorContracts(unittest.TestCase):
    def test_three_exact_hosted_read_only_authority_samples(self):
        for sample in (1,2,3):
            f=FakeGet(db())
            result=measure(f,repository=REPO,issue=ISSUE,main_sha=BASE,
                work_sha=WORK,sample=sample,run_id=777,run_attempt=1,
                clock=lambda:100.0,utc=lambda:"2026-10-15T16:00:00Z")
            self.assertEqual(result["sample"],sample)
            self.assertEqual(result["version"],VERSION)
            self.assertEqual(result["classification"],"REAL_API_PREFLIGHT_ONLY")
            self.assertEqual(result["actual_work_ci"],"CREATED_NOT_GREEN")
            self.assertEqual(result["total_ms"],0)
            self.assertEqual(len(f.paths),8)
            self.assertTrue(all(x.startswith("repos/"+REPO+"/") for x in f.paths))

    def test_main_work_issue_and_rolling_tampering_rejected(self):
        for name,mutate in (
            ("main",lambda v:v[f"repos/{REPO}/branches/main"]["commit"].update(sha="f"*40)),
            ("work",lambda v:v[f"repos/{REPO}/branches/work/RHC-{ISSUE}"]["commit"].update(sha="f"*40)),
            ("issue",lambda v:v[f"repos/{REPO}/issues/{ISSUE}"].update(state="closed")),
            ("labels",lambda v:v[f"repos/{REPO}/issues/{ISSUE}"].update(labels=[])),
            ("rolling",lambda v:v[f"repos/{REPO}/issues/{ISSUE}/comments?per_page=100"][0].update(body="fake")),
        ):
            with self.subTest(name=name),self.assertRaises(ValueError):
                val=db();mutate(val)
                measure(FakeGet(val),repository=REPO,issue=ISSUE,main_sha=BASE,work_sha=WORK,
                        sample=1,run_id=777,run_attempt=1)

    def test_no_product_version_override_or_fake_job_green(self):
        for path,value in (("model.go",'appVersion="3.0.8.9"\nreferenceVersion="3.0.8.9"'),
                           ("CHANGELOG.md","# Changelog\n\n## 3.0.8.9"),
                           ("downloads/latest.json",'{"version":"3.0.8.9"}')):
            with self.subTest(path=path),self.assertRaises(ValueError):
                val=db();val[f"repos/{REPO}/contents/{path}?ref={BASE}"]=file_content(value)
                measure(FakeGet(val),repository=REPO,issue=ISSUE,main_sha=BASE,work_sha=WORK,
                        sample=1,run_id=777,run_attempt=1)

    def test_untrusted_route_and_hosted_job_identity_block(self):
        for path in ("https://evil.com","repos/other/repo/issues/2",
                     "repos/"+REPO+"/git/refs/heads/main","repos/"+REPO+"/issues/202/comments"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                safe_api_route(path,REPO)
        jobs=[dict(id=i,name=f"readonly-preflight-{i}",status="completed",
                   conclusion="success") for i in (1,2,3)]
        self.assertTrue(require_hosted_jobs({"total_count":4,"jobs":jobs+
               [dict(id=4,name="aggregate-independent-preflight",status="in_progress",conclusion=None)]}))
        for bad in ([],jobs[:2],jobs+[jobs[0]],
                    [dict(jobs[0],conclusion="skipped"),*jobs[1:]]):
            with self.assertRaises(ValueError):
                require_hosted_jobs({"total_count":len(bad),"jobs":bad})

    def test_aggregate_three_real_different_samples_and_no_p95_claim(self):
        rows=[dict(schema="RHC190_PHASE_D_PREFLIGHT_V1",sample=i,repository=REPO,
                   main_sha=BASE,work_sha=WORK,issue=ISSUE,version=VERSION,
                   run_id=777,run_attempt=1,total_ms=i*10,
                   classification="REAL_API_PREFLIGHT_ONLY",
                   actual_work_ci="CREATED_NOT_GREEN") for i in (1,2,3)]
        result=aggregate_samples(rows,repository=REPO,main_sha=BASE,work_sha=WORK,issue=ISSUE,
                                 run_id=777,run_attempt=1)
        self.assertEqual(result["median_ms"],20)
        self.assertEqual(result["max_ms"],30)
        self.assertIsNone(result["end_to_end_ms"])
        self.assertIsNone(result["p95_ms"])
        for bad in (rows[:2],[rows[0],rows[0],rows[2]],[dict(rows[0],work_sha="c"*40),*rows[1:]],
                    [dict(rows[0],classification="FULL_RELEASE_VERIFIED"),*rows[1:]]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                aggregate_samples(bad,repository=REPO,main_sha=BASE,work_sha=WORK,issue=ISSUE,
                                  run_id=777,run_attempt=1)

    def test_real_gh_transport_uses_allowlisted_get_only(self):
        from rhc190_phase_d_operator import github_get
        from unittest.mock import Mock
        import os
        valid="repos/"+REPO+"/branches/main"
        with patch.dict(os.environ,{"GH_TOKEN":"test-only"},clear=True), \
             patch("rhc190_phase_d_operator.subprocess.run") as runner:
            runner.return_value=Mock(returncode=0,stdout='{"ok":true}')
            self.assertEqual(github_get(valid,REPO),{"ok":True})
            self.assertEqual(runner.call_args.args[0],
                             ["gh","api","--method","GET",valid])
            self.assertEqual(runner.call_args.kwargs["timeout"],20)
            with self.assertRaises(ValueError):
                github_get("repos/"+REPO+"/git/refs/heads/main",REPO)
            self.assertEqual(runner.call_count,1)

    def test_workflow_permissions_three_jobs_no_product_publication(self):
        yaml=(ROOT/".github/workflows/rhc190-phase-d-operator.yml").read_text()
        self.assertIn("workflow_dispatch:",yaml)
        self.assertIn("work/RHC-202",yaml)
        self.assertIn("sample: [1, 2, 3]",yaml)
        self.assertIn("contents: read",yaml)
        self.assertIn("issues: read",yaml)
        self.assertIn("actions: read",yaml)
        self.assertNotIn("contents: write",yaml)
        self.assertNotIn("actions: write",yaml)
        self.assertNotIn("pull_request_target",yaml)
        self.assertNotIn("git push",yaml)
        self.assertIn("rhc190_phase_d_operator.py",yaml)
        self.assertIn("rhc190_phase_d_aggregate.py",yaml)

if __name__=="__main__":
    unittest.main()
