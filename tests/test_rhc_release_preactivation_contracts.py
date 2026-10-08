"""RHC-20 RHC-12 release preactivation: adversarial *pure* tests only."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from rhc12_release_plan import evaluate

A="a"*40
B="b"*40
C="c"*40
D="d"*64
E="e"*64
contextsC=("rhc/preflight/linux","rhc/preflight/windows","rhc/preflight/candidate")
contextsR=("rhc/release/source","rhc/release/portable","rhc/release/verification")
def statuses(contexts):
    return {"statuses":[{"context":c,"state":"success"} for c in contexts]}
def case():
    return {
       "policy":{"productionEnabled":True,"distribution":"repo-downloads",
          "signingDecision":"unsigned-approved","rollbackVerified":True},
       "version":"3.0.8.1","mainVersion":"3.0.8.0",
       "observedMainSha":A,"expectedMainSha":A,"candidateSha":B,"releaseSha":C,
       "candidateBranch":"candidate/v3.0.8.1","releaseBranch":"release/v3.0.8.1",
       "releaseBranchAvailable":True,"releaseSourceSha":B,
       "candidateStatuses":statuses(contextsC),"releaseStatuses":statuses(contextsR),
       "archive":{"name":"RazerHealthCenter-Portable-v3.0.8.1.zip","sha256":D,
             "size":777,"leanSevenFiles":True,"noNestedZip":True,
             "manifestVerified":True,"independentBuildsIdentical":True},
       "sourceTagSha":B,"tagExists":False,"readOnlyCandidate":True,
       "physicalRazerAcceptance":True,
       "publicVersion":None,"releasedCount":0,"latestExists":False,
       "rollbackEvidence":{"firstReleaseRecoveryVerified":True,
              "nativeRestoreTestPassed":True},
       "windowsTrust":{"version":"3.0.8.1","sourceSha":B,"archiveSha256":D,
              "ownerExplicitApproval":True,"smartScreenDisclosureAcknowledged":True,
              "approvalId":"EXPLICIT-FIXTURE-ONLY"},
       "releasePrNotMerged":True,"immutableHistoryVerified":True}
class RHC12Gate(unittest.TestCase):
    def test_only_pure_preactivation_eligible(self):
        self.assertEqual(evaluate(case())["result"],"PREACTIVATION_ELIGIBLE_NOT_PUBLISHED")

    def test_real_current_policy_blocks(self):
        s=case()
        for change in [dict(productionEnabled=False),dict(signingDecision="unknown"),
                       dict(rollbackVerified=False)]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                evaluate(dict(s,policy=dict(s["policy"],**change)))

    def test_missing_hosted_statuses_and_source(self):
        s=case()
        for change in [dict(candidateStatuses=statuses(contextsC[:2])),
                       dict(releaseStatuses=statuses(contextsR[:2])),
                       dict(candidateStatuses={"statuses":[{"context":x,"state":"pending"} for x in contextsC]}),
                       dict(sourceTagSha=A),dict(releaseSourceSha=A),
                       dict(expectedMainSha=B),dict(candidateBranch="candidate/v3.0.8")]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                evaluate(dict(s,**change))

    def test_artifact_tampering_and_unsafe_package(self):
        s=case()
        for patch in [dict(sha256="bad"),dict(size=0),dict(leanSevenFiles=False),
                      dict(noNestedZip=False),dict(independentBuildsIdentical=False),
                      dict(name="RazerHealthCenter-Source-v3.0.8.1.zip")]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                evaluate(dict(s,archive=dict(s["archive"],**patch)))

    def test_no_fabricated_rollback_or_hardware(self):
        s=case()
        for change in [dict(physicalRazerAcceptance=False),
                       dict(rollbackEvidence={"nativeRestoreTestPassed":True}),
                       dict(rollbackEvidence={"firstReleaseRecoveryVerified":True}),
                       dict(releasePrNotMerged=False),dict(immutableHistoryVerified=False),
                       dict(latestExists=True)]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                evaluate(dict(s,**change))

    def test_immutable_prior_release(self):
        s=case()
        s.update(publicVersion="3.0.8.0",releasedCount=1,latestVersion="3.0.8.0",
                 rollbackEvidence={"previousVersion":"3.0.8.0","previousZipSha":E,
                  "previousZipRetrievable":True,"nativeRestoreTestPassed":True})
        self.assertEqual(evaluate(s)["version"],"3.0.8.1")
        s["rollbackEvidence"]["previousZipRetrievable"]=False
        with self.assertRaises(ValueError):evaluate(s)

    def test_signed_verified_path_only_with_proof(self):
        s=case()
        s["policy"]["signingDecision"]="signed-verified"
        with self.assertRaises(ValueError):evaluate(s)
        s["windowsTrust"].update(authenticodeVerified=True,signerIdentity="Verified publisher fixture")
        self.assertEqual(evaluate(s)["result"],"PREACTIVATION_ELIGIBLE_NOT_PUBLISHED")

    def test_unsigned_must_have_exact_consent(self):
        s=case()
        for delta in [dict(sourceSha=A),dict(archiveSha256=E),
                      dict(ownerExplicitApproval=False),
                      dict(smartScreenDisclosureAcknowledged=False),dict(approvalId="")]:
            with self.subTest(delta=delta),self.assertRaises(ValueError):
                evaluate(dict(s,windowsTrust=dict(s["windowsTrust"],**delta)))

if __name__=="__main__":
    unittest.main()
