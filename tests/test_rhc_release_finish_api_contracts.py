"""RHC-20 independent remote merge readback: real SHA/tag/history/ZIP bytes, mocks only."""
import base64
import hashlib
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rhc_release_finish as release

A="a"*40
B="b"*40
C="c"*40
D="d"*40
E="e"*40
F="f"*40
VERSION="3.0.8.1"
ZIP=b"immutable-seven-file-zip-content"
H=hashlib.sha256(ZIP).hexdigest()
PKG="downloads/RazerHealthCenter-Portable-v3.0.8.1.zip"
IDX="downloads/releases.json"
PTR="downloads/latest.json"
README="downloads/README.md"


class Remote:
    def __init__(self):
        self.tag=False
        self.merged=False
        self.branch=True
        self.calls=[]
        self.badTag=False
        self.badBytes=False
        self.badSource=False
        self.badHistory=False

    def gh(self,method,path,payload=None,allow404=False):
        self.calls.append((method,path))
        if method=="POST" and path=="/git/refs":
            assert payload=={"ref":"refs/tags/v"+VERSION,"sha":C}
            assert not self.tag
            self.tag=True
            return {}
        if method=="PUT" and path=="/pulls/47/merge":
            assert self.tag and payload["sha"]==B
            self.merged=True
            return {"merged":True,"sha":D}
        if method=="DELETE" and path=="/git/refs/heads/release/v"+VERSION:
            self.branch=False
            return {}
        if method=="GET" and path=="/branches/main":
            return {"commit":{"sha":D if self.merged else A}}
        if method=="GET" and path=="/git/ref/tags/v"+VERSION:
            return None if not self.tag else {"object":{"sha":A if self.badTag else C}}
        if method=="GET" and path=="/git/commits/"+D:
            return {"parents":[{"sha":A},{"sha":B}],"tree":{"sha":F}}
        if method=="GET" and path=="/git/commits/"+A:
            return {"parents":[],"tree":{"sha":E}}
        if method=="GET" and path=="/git/commits/"+C:
            return {"parents":[{"sha":A}],"tree":{"sha":"7"*40}}
        if method=="GET" and path=="/git/trees/"+E+"?recursive=1":
            return {"truncated":False,"tree":[
                {"path":IDX,"sha":"9"*40,"type":"blob"},
                {"path":README,"sha":"8"*40,"type":"blob"}]}
        if method=="GET" and path=="/git/trees/"+"7"*40+"?recursive=1":
            return {"truncated":False,"tree":[
                {"path":"model.go","sha":"5"*40,"type":"blob"},
                {"path":"CHANGELOG.md","sha":"6"*40,"type":"blob"}]}
        if method=="GET" and path=="/git/trees/"+F+"?recursive=1":
            return {"truncated":False,"tree":[
                {"path":"model.go","sha":("0"*40 if self.badSource else "5"*40),"type":"blob"},
                {"path":"CHANGELOG.md","sha":"6"*40,"type":"blob"},
                {"path":PKG,"sha":"1"*40,"type":"blob"},
                {"path":IDX,"sha":"2"*40,"type":"blob"},
                {"path":PTR,"sha":"3"*40,"type":"blob"},
                {"path":README,"sha":"4"*40,"type":"blob"}]}
        if method=="GET" and path.startswith("/git/blobs/"):
            record={"version":VERSION,"sourceSha":C,"sha256":H,
                    "size":len(ZIP)}
            newer=[record]
            if self.badHistory:
                newer.append(dict(record,version="3.0.8.0"))
            values={"1":b"wrong" if self.badBytes else ZIP,
                    "2":json.dumps({"schemaVersion":1,"releases":newer}).encode(),
                    "3":json.dumps(record).encode(),
                    "4":b"Readme",
                    "9":json.dumps({"schemaVersion":1,"releases":[]}).encode()}
            return {"encoding":"base64","content":base64.b64encode(
                values[path[-40]]).decode()}
        raise AssertionError("unknown GH remote operation: "+method+" "+path)


class GitHubPostverify(unittest.TestCase):
    def test_true_merge_parent_tag_and_full_blob_digest(self):
        api=Remote()
        api.tag=True;api.merged=True
        with patch.object(release,"gh",side_effect=api.gh):
            result=release.verify_merged_release(
                main_before=A,release_sha=B,candidate_sha=C,
                version=VERSION,zip_sha=H)
        self.assertEqual(result["result"],"MERGE_AND_BYTES_VERIFIED")
        for change in ("badTag","badBytes","badSource","badHistory"):
            api=Remote();api.tag=True;api.merged=True
            setattr(api,change,True)
            with self.subTest(change=change),patch.object(release,"gh",
                            side_effect=api.gh),self.assertRaises(ValueError):
                release.verify_merged_release(
                    main_before=A,release_sha=B,candidate_sha=C,
                    version=VERSION,zip_sha=H)

    def test_live_merge_and_cleanup_only_after_external_gate(self):
        api=Remote()
        evidence={"mainSha":A,"candidateSha":C,"version":VERSION,
                  "sha256":H,"pr":47}
        ref="release/v"+VERSION
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":"EXPLICIT_OWNER_RHC22",
                                    "GH_TOKEN":"MOCK-TOKEN"}),\
             patch.object(release,"check_live_staged_release",return_value=evidence),\
             patch.object(release,"ready_release_pr",return_value={"ready":True}),\
             patch.object(release,"branch",side_effect=
                lambda name: {"object":{"sha":B}} if api.branch else None),\
             patch.object(release,"gh",side_effect=api.gh):
            verdict=release.finish(ROOT,ref,B)
        self.assertEqual(verdict["result"],"PUBLISHED_VERIFIED")
        self.assertTrue(verdict["releaseBranchRemoved"])
        writes=[(method,path) for method,path in api.calls if method!="GET"]
        self.assertEqual(writes,[("POST","/git/refs"),("PUT","/pulls/47/merge"),
                                 ("DELETE","/git/refs/heads/"+ref)])

    def test_draft_pr_must_be_marked_ready_before_tag_or_merge(self):
        # The stage controller creates a Draft. GitHub rejects merging a Draft.
        # Finalize must perform a separately gated, verified ready transition
        # BEFORE creating the immutable tag, not after a failed merge request.
        api=Remote()
        evidence={"mainSha":A,"candidateSha":C,"version":VERSION,
                  "sha256":H,"pr":47}
        ref="release/v"+VERSION
        observed=[]
        def ready(pr_number, branch_name, head, main):
            self.assertEqual((pr_number,branch_name,head,main),(47,ref,B,A))
            self.assertFalse(api.tag)
            self.assertFalse(api.merged)
            observed.append("ready")
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":"EXPLICIT_OWNER_RHC22",
                                    "GH_TOKEN":"MOCK-TOKEN"}),\
             patch.object(release,"check_live_staged_release",return_value=evidence),\
             patch.object(release,"ready_release_pr",create=True,side_effect=ready),\
             patch.object(release,"branch",side_effect=
                lambda name: {"object":{"sha":B}} if api.branch else None),\
             patch.object(release,"gh",side_effect=api.gh):
            outcome=release.finish(ROOT,ref,B)
        self.assertEqual(outcome["result"],"PUBLISHED_VERIFIED")
        self.assertEqual(observed,["ready"])

    def test_failed_ready_transition_must_never_create_tag(self):
        api=Remote()
        evidence={"mainSha":A,"candidateSha":C,"version":VERSION,
                  "sha256":H,"pr":47}
        ref="release/v"+VERSION
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":"EXPLICIT_OWNER_RHC22",
                                    "GH_TOKEN":"MOCK-TOKEN"}),\
             patch.object(release,"check_live_staged_release",return_value=evidence),\
             patch.object(release,"ready_release_pr",create=True,
                          side_effect=ValueError("Draft PR readiness unverified")),\
             patch.object(release,"branch",side_effect=
                lambda name: {"object":{"sha":B}} if api.branch else None),\
             patch.object(release,"gh",side_effect=api.gh):
            with self.assertRaisesRegex(ValueError,"readiness unverified"):
                release.finish(ROOT,ref,B)
        self.assertFalse(api.tag)
        self.assertFalse(api.merged)

    def test_real_ready_transition_checks_exact_pr_and_confirms_readback(self):
        import types
        ref="release/v"+VERSION
        result={"state":"open","merged":False,"draft":True,
                "head":{"sha":B,"ref":ref},"base":{"sha":A}}
        calls=[]
        def query(method,path,payload=None,allow404=False):
            calls.append((method,path))
            if path=="/pulls/47":
                return dict(result)
            if path=="/branches/main":
                return {"commit":{"sha":A}}
            raise AssertionError("unexpected read "+path)
        def ready_run(args,**kwargs):
            self.assertEqual(args[:3],["gh","pr","ready"])
            result["draft"]=False
            return types.SimpleNamespace(returncode=0,stderr="")
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":"EXPLICIT_OWNER_RHC22",
                                    "GH_TOKEN":"MOCK-TOKEN"}),\
             patch.object(release,"gh",side_effect=query),\
             patch.object(release,"branch",return_value={"object":{"sha":B}}),\
             patch.object(release.subprocess,"run",side_effect=ready_run) as runner:
            self.assertTrue(release.ready_release_pr(47,ref,B,A)["ready"])
            self.assertEqual(runner.call_count,1)
        self.assertEqual([x for x in calls if x[1]=="/pulls/47"],
                         [("GET","/pulls/47"),("GET","/pulls/47")])
        # Missing a real Draft->Ready confirmation must block before any tag.
        result["draft"]=True
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":"EXPLICIT_OWNER_RHC22",
                                    "GH_TOKEN":"MOCK-TOKEN"}),\
             patch.object(release,"gh",side_effect=query),\
             patch.object(release,"branch",return_value={"object":{"sha":B}}),\
             patch.object(release.subprocess,"run",
                          return_value=types.SimpleNamespace(returncode=0,stderr="")):
            with self.assertRaisesRegex(ValueError,"readiness unverified"):
                release.ready_release_pr(47,ref,B,A)

    def test_uncertain_owner_gate_does_not_start_any_remote_write(self):
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":""}),\
             patch.object(release,"gh",side_effect=AssertionError("GH called")):
            with self.assertRaises(ValueError):
                release.finish(ROOT,"release/v"+VERSION,B)


if __name__=="__main__":
    unittest.main()
