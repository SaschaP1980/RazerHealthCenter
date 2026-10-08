"""RHC-20 live boundaries: owner approval, reproducibility and no synthetic release."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rhc_downloads as d
import rhc_release_live as live
import rhc_release_finish as finish

SHA="a"*40
ZIP="d"*64
LINE=("RHC-RELEASE-APPROVAL version=3.0.8.1 sourceSha="+SHA+
      " archiveSha256="+ZIP+" signing=unsigned-approved")
BODY=LINE+"\nNATIVE-RAZER-ACCEPTANCE=VERIFIED\nNATIVE-ROLLBACK=VERIFIED\nFIRST-RELEASE-RECOVERY=VERIFIED\nUNSIGNED-SMARTSCREEN-RISK=EXPLICITLY-ACCEPTED"


class Approval(unittest.TestCase):
    def test_only_live_owner_comment_bound_to_exact_archive(self):
        base=dict(user={"login":"SaschaP1980"},
                  issue_url="https://api.github.com/repos/SaschaP1980/RazerHealthCenter/issues/22",
                  body=BODY,html_url="https://github.com/SaschaP1980/RazerHealthCenter/issues/22")
        with patch.object(live,"gh",return_value=base):
            self.assertEqual(live.record_approval(123,"3.0.8.1",SHA,ZIP,
                            {"signingDecision":"unsigned-approved"})["id"],123)
        for change in (dict(user={"login":"github-actions[bot]"}),
                       dict(issue_url=base["issue_url"].replace("/22","/20")),
                       dict(body=BODY.replace(ZIP,"e"*64)),
                       dict(body=BODY.replace("NATIVE-ROLLBACK=VERIFIED","")),
                       dict(body=BODY.replace("UNSIGNED-SMARTSCREEN-RISK=EXPLICITLY-ACCEPTED","")),
                       dict(body=BODY+"\n"+LINE)):
            with self.subTest(change=change),patch.object(live,"gh",
                            return_value=dict(base,**change)):
                with self.assertRaises(ValueError):
                    live.record_approval(123,"3.0.8.1",SHA,ZIP,
                                         {"signingDecision":"unsigned-approved"})

    def test_no_deployment_permission_without_explicit_owner_run(self):
        args=SimpleNamespace(root=ROOT,exe_a="a",exe_b="b",candidate_sha=SHA,
                             main_sha=SHA,version="3.0.8.1",owner_comment_id=123,
                             published_utc="2026-10-08T00:00:00Z")
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":""}),\
             patch.object(live,"gh",side_effect=AssertionError("GH wrote")):
            with self.assertRaises(ValueError):
                live.stage(args)
        with patch.dict(os.environ,{"RHC_REAL_PUBLICATION_APPROVED":""}),\
             patch.object(finish,"gh",side_effect=AssertionError("GH wrote")):
            with self.assertRaises(ValueError):
                finish.finish(ROOT,"release/v3.0.8.1",SHA)

    def test_current_main_ruleset_is_not_effective(self):
        def fake(method,path,payload=None,allow404=False):
            if path=="/rulesets": return [{"id":24701145,"enforcement":"active"}]
            return {"conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},
                    "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}
        with patch.object(live,"gh",side_effect=fake):
            with self.assertRaises(ValueError):
                live.required_main_rules()

    def test_main_required_checks_do_not_deadlock_nonrelease_prs(self):
        import rhc_main_rules as admin
        self.assertEqual(tuple(admin.CONTEXTS),
                         ("rhc/infra/linux","rhc/infra/windows"))
        self.assertEqual(live.MAIN_CONTEXTS,
                         ["rhc/infra/linux","rhc/infra/windows"])
        # Release-only contexts are independently checked by the finalizer.
        self.assertIn("trusted_contexts", (ROOT/"tools/rhc_release_finish.py").read_text())
        self.assertIn("RELEASE", (ROOT/"tools/rhc_release_finish.py").read_text())

    def test_real_release_stage_and_finalize_are_owner_manual_dispatch_only(self):
        for workflow in ("rhc-release-stage.yml","rhc-release-finalize.yml"):
            with self.subTest(workflow=workflow):
                text=(ROOT/".github/workflows"/workflow).read_text()
                self.assertIn("workflow_dispatch:",text)
                self.assertIn("github.actor == 'SaschaP1980'",text)
                self.assertIn("EXPLICIT_OWNER_RHC22",text)
                self.assertNotIn("push:",text)
                self.assertNotIn("schedule:",text)
        stage=(ROOT/".github/workflows/rhc-release-stage.yml").read_text()
        self.assertIn("tools/rhc_release_live.py stage",stage)
        self.assertIn("rhc-release-preflight.yml", (ROOT/"tools/rhc_release_live.py").read_text())
        final=(ROOT/".github/workflows/rhc-release-finalize.yml").read_text()
        self.assertIn("tools/rhc_release_finish.py",final)
        self.assertIn("release_sha",final)

    def test_new_workflow_has_readonly_preflight_and_exact_sha_contexts(self):
        wf=(ROOT/".github/workflows/rhc-release-preflight.yml").read_text()
        for token in ("workflow_dispatch:","statuses: write",
                      "rhc/release/source","rhc/release/portable",
                      "rhc/release/verification","tools/rhc_release_verify.py",
                      "Get-AuthenticodeSignature","ref: ${{ github.sha }}"):
            self.assertIn(token.replace("${{","$"+"{{"),wf)
        self.assertNotIn("gh release create",wf)


class Shadow(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.tmp=pathlib.Path(t.name)
        self.root=self.tmp/"source"
        self.root.mkdir()
        (self.root/"model.go").write_text(
            'const (\nappVersion = "3.0.8.1"\nreferenceVersion = "3.0.8.1"\n)\n')
        for rel in d.release.PORTABLE_ASSETS.values():
            p=self.root/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(rel.encode())
        self.catalog=self.root/"downloads"
        self.catalog.mkdir()
        (self.catalog/"releases.json").write_text(
            json.dumps({"schemaVersion":1,"releases":[]})+"\n")
        (self.catalog/"README.md").write_text(d.render_readme([]),
                                              encoding="utf-8")
        (self.tmp/"a").mkdir()
        (self.tmp/"b").mkdir()
        self.a=self.tmp/"a"/"RazerHealthCenter.exe"
        self.b=self.tmp/"b"/"RazerHealthCenter.exe"
        self.a.write_bytes(b"MZ"+b"x"*80)
        self.b.write_bytes(self.a.read_bytes())
        self.stage=self.tmp/"stage"

    def test_staged_zip_catalog_is_unpublished_and_replay_fails(self):
        initial={p.name:p.read_bytes() for p in self.catalog.iterdir()}
        record,stage=live.dry_shadow_release(self.root,SHA,"3.0.8.1",
                                             self.a,self.b,self.stage,
                                             "2026-10-08T00:00:00Z")
        self.assertEqual(len(record["packageFiles"]),7)
        self.assertEqual(d.verify(stage)[0],record)
        self.assertEqual(initial,{p.name:p.read_bytes() for p in self.catalog.iterdir()})
        with self.assertRaises(ValueError):
            live.dry_shadow_release(self.root,SHA,"3.0.8.1",self.a,self.b,
                                    self.stage,"2026-10-08T00:00:00Z")

    def test_different_independent_binaries_cannot_publish(self):
        self.b.write_bytes(b"MZnot-equal")
        with self.assertRaisesRegex(ValueError,"reproducible"):
            live.dry_shadow_release(self.root,SHA,"3.0.8.1",self.a,self.b,
                                    self.stage,"2026-10-08T00:00:00Z")
        self.assertFalse((self.catalog/"latest.json").exists())


if __name__=="__main__":
    unittest.main()
