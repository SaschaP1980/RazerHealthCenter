"""Synthetic PE fixtures prove the real-byte rehearsal is isolated/fail closed."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
import rhc_downloads as d
from rhc_release_rehearsal import rehearse, inventory


class ReleaseRehearsal(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.tmp=pathlib.Path(self.t.name)
        self.root=self.tmp/"source"
        self.root.mkdir()
        (self.root/"config").mkdir()
        self.policy=self.root/"config"/"rhc-release-policy.json"
        self.cfg={"productionEnabled":False,"signingDecision":"unknown",
                  "rollbackVerified":False,"distribution":"repo-downloads"}
        self.policy.write_text(json.dumps(self.cfg))
        (self.root/"model.go").write_text(
            'const (\nappVersion = "3.0.8.0"\nreferenceVersion = "3.0.8.0"\n)\n')
        for name in d.release.PORTABLE_ASSETS.values():
            path=self.root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(name.encode())
        self.downloads=self.root/"downloads"
        self.downloads.mkdir()
        (self.downloads/"releases.json").write_text(
            json.dumps({"schemaVersion":1,"releases":[]})+"\n")
        (self.downloads/"README.md").write_text(d.render_readme([]), encoding="utf-8")
        for name in ("one","two"):
            (self.tmp/name).mkdir()
            (self.tmp/name/"RazerHealthCenter.exe").write_bytes(b"MZ"+b"x"*300)
        self.a=self.tmp/"one"/"RazerHealthCenter.exe"
        self.b=self.tmp/"two"/"RazerHealthCenter.exe"
        self.stage=self.tmp/"stage"

    def runit(self, **kw):
        args={"root":self.root,"exe1":self.a,"exe2":self.b,
              "stage":self.stage,"source_sha":"a"*40}
        args.update(kw)
        return rehearse(**args)

    def test_real_byte_shadows_retain_public_downloads(self):
        old=inventory(self.downloads)
        result=self.runit()
        self.assertEqual(result["result"],"PASS_NONPUBLISHING_ONLY")
        self.assertEqual(result["files"],7)
        self.assertEqual(result["negativeCases"],3)
        self.assertEqual(inventory(self.downloads),old)
        self.assertFalse((self.downloads/"latest.json").exists())
        self.assertEqual(len(d.verify(self.stage/"downloads")),1)
        with self.assertRaisesRegex(ValueError,"already exists"):
            self.runit()

    def test_blocked_prod_policy_is_mandatory(self):
        for key,bad in (("productionEnabled",True),
                        ("signingDecision","unsigned-approved"),
                        ("rollbackVerified",True),
                        ("distribution","github-releases")):
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.policy.write_text(json.dumps(dict(self.cfg,**{key:bad})))
                self.runit()
            self.policy.write_text(json.dumps(self.cfg))
            self.assertFalse(self.stage.exists())

    def test_wrong_sha_and_mismatching_build_rejected(self):
        with self.assertRaisesRegex(ValueError,"source commit SHA"):
            self.runit(source_sha="bad")
        self.b.write_bytes(b"MZwrong")
        with self.assertRaisesRegex(ValueError,"PE build bytes"):
            self.runit()
        self.assertFalse(self.stage.exists())

    def test_source_stage_and_existing_stage_rejected(self):
        with self.assertRaisesRegex(ValueError,"outside source"):
            self.runit(stage=self.root/"temp")
        self.stage.mkdir()
        with self.assertRaisesRegex(ValueError,"already exists"):
            self.runit()

    def test_existing_latest_pointer_is_not_hidden(self):
        (self.downloads/"latest.json").write_text("{}")
        with self.assertRaises(ValueError):
            self.runit()
        self.assertFalse(self.stage.exists())


if __name__=="__main__":
    unittest.main()
