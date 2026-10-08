"""RHC-20 mocked GitHub release-PR transaction: ordered API writes and crash safety."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rhc_release_live as live

A="a"*40
B="b"*40
C="c"*40
D="d"*40

class FakeGitHub:
    def __init__(self):
        self.branch=None
        self.main=A
        self.writes=[]
        self.fail_dispatch=False
    def __call__(self,method,path,payload=None,allow404=False):
        if method=="GET":
            if path=="/branches/main":
                return {"commit":{"sha":self.main}}
            if path=="/git/ref/heads/release/v3.0.8.1":
                return {"object":{"sha":self.branch}} if self.branch else None
            if path=="/git/commits/"+A:
                return {"tree":{"sha":B}}
            raise AssertionError("unknown simulated GH GET "+path)
        self.writes.append((method,path,payload))
        if method=="POST" and path=="/git/blobs":
            return {"sha":B}
        if method=="POST" and path=="/git/trees":
            self.tree=payload
            return {"sha":C}
        if method=="POST" and path=="/git/commits":
            self.commit=payload
            return {"sha":D}
        if method=="POST" and path=="/git/refs":
            assert self.branch is None, "duplicate release branch must not overwrite"
            self.branch=D
            return {}
        if method=="POST" and path=="/pulls":
            return {"number":47}
        if method=="POST" and path=="/actions/workflows/rhc-release-preflight.yml/dispatches":
            if self.fail_dispatch:
                raise ValueError("uncertain workflow dispatch")
            return {}
        raise AssertionError("unexpected GH write "+method+" "+path)


class GitHubReleaseTransaction(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tmp=pathlib.Path(temp.name)
        self.root=self.tmp/"source"
        self.root.mkdir()
        self.two=self.tmp/"a"
        self.two.write_bytes(b"MZ")
        self.args=type("Args",(),dict(root=self.root,candidate_sha=B,
                          main_sha=A,version="3.0.8.1",
                          owner_comment_id=123,exe_a=str(self.two),
                          exe_b=str(self.two),published_utc="2026-10-08T00:00:00Z"))()
        self.gh=FakeGitHub()

    def shadow(self,*args):
        t=pathlib.Path(args[5])/"downloads"
        t.mkdir(parents=True)
        for file in ("RazerHealthCenter-Portable-v3.0.8.1.zip",
                     "releases.json","latest.json","README.md"):
            (t/file).write_bytes(file.encode())
        return ({"sha256":"d"*64},t)

    def stage(self):
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":"EXPLICIT_OWNER_RHC22"}),\
             patch.object(live,"validate_prewrite",return_value={"signingDecision":"unsigned-approved"}),\
             patch.object(live,"record_approval",return_value={
                "id":123,"url":"https://github.com/SaschaP1980/RazerHealthCenter/issues/22"}),\
             patch.object(live,"dry_shadow_release",side_effect=self.shadow),\
             patch.object(live,"gh",side_effect=self.gh):
            return live.stage(self.args)

    def test_single_release_branch_pr_dispatch_after_four_blobs(self):
        result=self.stage()
        self.assertEqual(result["result"],"STAGED_PUBLIC_BRANCH_NOT_YET_MERGED")
        self.assertEqual(self.gh.branch,D)
        paths=[path for method,path,payload in self.gh.writes]
        self.assertEqual(paths,[
            "/git/blobs","/git/blobs","/git/blobs","/git/blobs",
            "/git/trees","/git/commits","/git/refs","/pulls",
            "/actions/workflows/rhc-release-preflight.yml/dispatches"])
        self.assertEqual(self.gh.commit["parents"],[A])
        self.assertEqual(len(self.gh.tree["tree"]),4)
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual(len(self.gh.writes),9)

    def test_preexisting_branch_blocks_before_any_write(self):
        self.gh.branch=D
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual(self.gh.writes,[])

    def test_uncertain_dispatch_is_attention_not_replayed(self):
        self.gh.fail_dispatch=True
        with self.assertRaisesRegex(ValueError,"uncertain"):
            self.stage()
        self.assertEqual(self.gh.branch,D)
        before=len(self.gh.writes)
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual(len(self.gh.writes),before)

if __name__=="__main__":
    unittest.main()
