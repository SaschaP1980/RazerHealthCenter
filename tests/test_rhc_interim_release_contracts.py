"""RHC-34: temporary 3.0.8.1 interim release is neither fake Phase B nor QA."""
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rhc_interim_release as interim

SHA="a"*40
NEW="b"*40
ZIP="c"*64


def evidence():
    return {
        "version":"3.0.8.1", "sourceSha":SHA, "mainSha":SHA,
        "changelogVersion":"3.0.8.1", "archiveSha256":ZIP,
        "archiveFile":"RazerHealthCenter-Portable-v3.0.8.1.zip",
        "archiveFiles":7, "archiveReproducible":True,
        "nativeWindows": "SUCCESS", "linux":"SUCCESS",
        "exeSignature":"NotSigned",
        "policy":{"productionEnabled":False,"rollbackVerified":False,
                  "signingDecision":"unknown","distribution":"repo-downloads"},
        "phaseB":{"hardware":"DEFERRED","rollback":"DEFERRED",
                  "publisherTrust":"NOT_VERIFIED","rulesetAdmin":"DEFERRED"},
        "existingTag":False, "existingArchive":False,
        "previousReleases":0
    }


class InterimReleaseContracts(unittest.TestCase):
    def test_explicit_interim_v3081_release_with_deferred_phase_b(self):
        o=interim.qualify(evidence())
        self.assertEqual(o["version"],"3.0.8.1")
        self.assertEqual(o["classification"],"INTERIM_UNSIGNED_UNCERTIFIED_RELEASE")
        self.assertEqual(o["sourceSha"],SHA)
        self.assertFalse(o["phaseBVerified"])
        self.assertEqual(o["releaseChangedPaths"],[
            "downloads/README.md",
            "downloads/RazerHealthCenter-Portable-v3.0.8.1.zip",
            "downloads/latest.json", "downloads/releases.json"
        ])
        self.assertIn("SmartScreen",o["disclosure"])

    def test_version_must_be_already_on_main_and_exact(self):
        for key,val in (("version","3.0.8.0"),("changelogVersion","3.0.8.0"),
                        ("sourceSha",NEW),("mainSha","bad"),("version","3.0.8.2")):
            with self.subTest(key=key),self.assertRaises(ValueError):
                interim.qualify(dict(evidence(),**{key:val}))

    def test_old_owner_release_policy_not_spoofed(self):
        for field,val in (("productionEnabled",True),("signingDecision","unsigned-approved"),
                          ("rollbackVerified",True),("distribution","github-releases")):
            with self.subTest(field=field),self.assertRaises(ValueError):
                x=evidence()
                x["policy"][field]=val
                interim.qualify(x)

    def test_phase_b_claims_are_never_manufactured(self):
        for key,val in (("hardware","VERIFIED"),("rollback","VERIFIED"),
                        ("publisherTrust","APPROVED"),("rulesetAdmin","EFFECTIVE")):
            with self.subTest(key=key),self.assertRaises(ValueError):
                x=evidence()
                x["phaseB"][key]=val
                interim.qualify(x)

    def test_actual_builds_and_unsigned_status_must_pass(self):
        for key,val in (("archiveSha256","bad"),("archiveFile","RazerHealthCenter-Portable-v3.0.8.1-TEST-UNSIGNED.zip"),
                        ("archiveFiles",8),("archiveReproducible",False),
                        ("nativeWindows","SKIPPED"),("linux","FAILURE"),
                        ("exeSignature","Unknown"),("existingTag",True),
                        ("existingArchive",True),("previousReleases",1)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                interim.qualify(dict(evidence(),**{key:val}))

    def test_workflow_scoped_and_requires_real_windows_before_staging(self):
        script=(ROOT/".github/workflows/rhc-interim-release-v3081.yml").read_text()
        for token in ("ubuntu-24.04","windows-2025","Get-AuthenticodeSignature",
                      "rhc_interim_release.py","rhc_downloads.py",
                      "needs: [linux, windows]", "3.0.8.1",
                      "INTERIM_UNSIGNED_UNCERTIFIED_RELEASE",
                      "pull-requests: write", "contents: write"):
            self.assertIn(token,script)
        self.assertIn("workflow_dispatch:",script)
        self.assertNotIn("pull_request:",script)
        self.assertNotIn("  push:",script)
        self.assertIn("if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'",script)
        for token in ("RHC_REAL_PUBLICATION_APPROVED: EXPLICIT_OWNER_RHC22",
                      "productionEnabled=true","rollbackVerified=true",
                      "signingDecision: unsigned-approved","gh release create"):
            self.assertNotIn(token,script)

    def test_old_prod_release_controller_keeps_fail_closed_policy(self):
        source=(ROOT/"tools/rhc_release_live.py").read_text()
        self.assertIn('policy.get("rollbackVerified") is True',source)
        self.assertIn('policy.get("productionEnabled") is True',source)


if __name__=="__main__":
    unittest.main()
