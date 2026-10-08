"""RHC-20 real Candidate checkpoint inspection: no GitHub writes on replay."""
import base64
import contextlib
import io
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rhc_candidate_from_work as candidate

A="a"*40
B="b"*40
C="c"*40
D="d"*40

class API:
    def __init__(self):
        self.present=True
        self.finished=True
        self.changedMain=False
        self.changedWork=False
        self.calls=[]
    def gh(self,method,path,payload=None,optional404=False):
        self.calls.append((method,path))
        assert method=="GET", "Recovery must never write"
        if path=="/branches/main":
            return {"commit":{"sha":D if self.changedMain else A}}
        if path=="/git/ref/heads/work/RHC-18":
            return {"object":{"sha":C if self.changedWork else B}}
        if path=="/git/commits/"+B:
            return {"message":"Work completion","tree":{"sha":C}}
        if path=="/git/ref/heads/candidate/v3.0.8.1":
            return {"object":{"sha":C}} if self.present else None
        if path=="/git/commits/"+C:
            return {"parents":[{"sha":A}],
                    "message":"Candidate\nWork-SHA: "+B+"\nMain-SHA: "+A}
        if path=="/commits/"+C+"/statuses":
            return ([{"context":name,"state":"success","creator":{"login":"github-actions[bot]"}}
                    for name in ("rhc/preflight/linux","rhc/preflight/windows",
                                 "rhc/preflight/candidate")] if self.finished else [])
        raise AssertionError("Unexpected GitHub path "+path)

class CandidateLiveAudit(unittest.TestCase):
    def execute(self,api):
        out=io.StringIO()
        with patch.object(candidate,"gh",side_effect=api.gh),\
             patch.object(candidate,"remote_model",return_value=
                'const (\nappVersion = "3.0.8.1"\nreferenceVersion = "3.0.8.1"\n)\n'),\
             patch.dict(os.environ,dict(WORK_BRANCH="work/RHC-18",WORK_SHA=B,
                EXPECTED_MAIN_SHA=A,GH_TOKEN="MOCK-READ-ONLY",
                RHC_CANDIDATE_RECOVERY="READ_ONLY")),contextlib.redirect_stdout(out):
            candidate.main()
        self.assertTrue(all(x[0]=="GET" for x in api.calls))
        return out.getvalue()

    def test_qualified_checkpoint_has_no_mutations_even_on_repeat(self):
        api=API()
        self.assertIn("QUALIFIED_NO_WRITE",self.execute(api))
        self.assertIn("QUALIFIED_NO_WRITE",self.execute(api))
        self.assertFalse(any(x[0]=="POST" for x in api.calls))

    def test_unknown_dispatch_is_attention_not_new_write(self):
        api=API();api.finished=False
        self.assertIn("ATTENTION_READ_ONLY",self.execute(api))

    def test_missing_ref_only_classifies_safe_creation(self):
        api=API();api.present=False
        self.assertIn("READY_FOR_SINGLE_CREATE",self.execute(api))

    def test_main_or_work_advance_fails_closed(self):
        for key in ("changedMain","changedWork"):
            api=API();setattr(api,key,True)
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.execute(api)

if __name__=="__main__":
    unittest.main()
