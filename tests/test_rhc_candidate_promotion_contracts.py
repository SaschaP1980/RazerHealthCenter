"""RHC-20 pure Work-to-Candidate promotion safety cases."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from rhc_candidate_from_work import validate_plan, model_version, enforce_version_only_model_edit

A="a"*40
B="b"*40
C="c"*40
def fixture():
    return dict(workBranch="work/RHC-18",mainSha=A,workSha=B,treeSha=C,
        compareStatus="ahead",behindBy=0,aheadBy=1,
        files=[dict(filename="model.go",status="modified"),
               dict(filename="CHANGELOG.md",status="added")],
        mainVersion="3.0.8.0",workVersion="3.0.8.1",candidateExists=False,
        policy=dict(productionEnabled=False,distribution="repo-downloads",
                    signingDecision="unknown",rollbackVerified=False),
        statuses=[dict(context="development-completion/gate",state="success",
                       description="PASS main="+A,creator={"login":"github-actions[bot]"})],
        message="RHC-Issue: 18\nRelease-Profile: version-only\nDevelopment-Completion: requested")

class CandidatePromotion(unittest.TestCase):
    def test_future_candidate_ready(self):
        self.assertEqual(validate_plan(fixture())["branch"],"candidate/v3.0.8.1")
        f=fixture();f["mainVersion"]="3.0.8.1";f["workVersion"]="3.0.8.2"
        self.assertEqual(validate_plan(f)["version"],"3.0.8.2")

    def test_version_only_model(self):
        self.assertEqual(model_version('appVersion = "3.0.8.1"\nreferenceVersion = "3.0.8.1"'),"3.0.8.1")
        for src in ['appVersion = "3.0.8"\nreferenceVersion = "3.0.8"',
                    'appVersion = "3.0.8.1"\nreferenceVersion = "3.0.8.2"']:
            with self.assertRaises(ValueError):model_version(src)

    def test_stale_identity_and_wrong_diff_fail(self):
        for diff in [dict(workSha=A),dict(mainSha="bad"),dict(treeSha="bad"),
                     dict(workBranch="work/RHC-03"),dict(compareStatus="diverged"),
                     dict(behindBy=1),dict(aheadBy=0),dict(candidateExists=True),
                     dict(files=[dict(filename="model.go",status="modified")]),
                     dict(workVersion="3.0.9.0"),dict(workVersion="3.0.8.3"),
                     dict(workVersion="3.0.8")]:
            with self.subTest(diff=diff),self.assertRaises(ValueError):
                validate_plan(dict(fixture(),**diff))

    def test_status_and_scope_guards(self):
        for change in [dict(statuses=[]),dict(statuses=[dict(context="development-completion/gate",state="pending")]),
                       dict(message="RHC-Issue: 18\nRelease-Profile: version-only"),
                       dict(message="RHC-Issue: 18\nRelease-Profile: hotfix\nDevelopment-Completion: requested"),
                       dict(files=[dict(filename="model.go",status="modified"),
                                   dict(filename="CHANGELOG.md",status="added"),
                                   dict(filename="config/rhc-release-policy.json",status="modified")])]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                validate_plan(dict(fixture(),**change))

    def test_policy_cannot_be_silently_approved(self):
        for delta in [dict(productionEnabled=True),dict(signingDecision="signed-verified"),
                      dict(rollbackVerified=True),dict(distribution="github-release")]:
            p=dict(fixture()["policy"],**delta)
            with self.assertRaises(ValueError):validate_plan(dict(fixture(),policy=p))

    def test_version_only_source_must_preserve_all_other_model_bytes(self):
        original='const (\\n appVersion = "3.0.8.0"\\n referenceVersion = "3.0.8.0"\\n diagnosticMode = true\\n)\\n'
        updated=original.replace('version = "3.0.8.0"', 'version = "3.0.8.1"')
        # use both exact field assignments, retain all other source text
        updated=original.replace('appVersion = "3.0.8.0"', 'appVersion = "3.0.8.1"').replace(
            'referenceVersion = "3.0.8.0"', 'referenceVersion = "3.0.8.1"')
        self.assertTrue(enforce_version_only_model_edit(original, updated))
        for malicious in (updated+'\\n', updated.replace("diagnosticMode = true", "diagnosticMode = false"),
                          updated.replace('referenceVersion = "3.0.8.1"', 'referenceVersion = "3.0.8.0"')):
            with self.subTest(malicious=malicious),self.assertRaises(ValueError):
                enforce_version_only_model_edit(original, malicious)

if __name__=="__main__":
    unittest.main()
