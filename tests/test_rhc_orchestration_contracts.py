"""Adversarial candidate/promotion and release-preactivation state contracts."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import rhc_orchestration_contracts as gate

S = 'a'*40
T = 'b'*40

def status_for(names, state='success'):
    return {'statuses':[{'context':n,'state':state} for n in names]}

class Gates(unittest.TestCase):
    def test_candidate_scopes(self):
        good=gate.validate_candidate(previous='3.0.8.0',version='3.0.8.1',
            changed_paths=['model.go','CHANGELOG.md'],release_profile='version-only',current_main_parent=True)
        self.assertEqual(good['result'],'PASS')
        for fields in [
            {'version':'3.0.8.0'}, {'version':'3.0.7'},
            {'changed_paths':['model.go','CHANGELOG.md','repair.go']},
            {'changed_paths':['model.go','README.md']},
            {'release_profile':'unapproved'}, {'current_main_parent':False},
            {'changed_paths':['model.go','CHANGELOG.md','private.pfx']},
        ]:
            inputs=dict(previous='3.0.8.0',version='3.0.8.1',changed_paths=['model.go','CHANGELOG.md'],
                        release_profile='version-only',current_main_parent=True)
            inputs.update(fields)
            with self.assertRaises(ValueError):gate.validate_candidate(**inputs)

    def test_refs(self):
        self.assertEqual(gate.safe_ref('candidate/v3.0.8.1','candidate'),'3.0.8.1')
        for ref in ('release/v3.0.8.1','candidate/v3.0.8.1-beta','candidate/v3.0.8.1/escape','candidate/v03.0.8.1'):
            with self.assertRaises(ValueError):gate.safe_ref(ref,'candidate')

    def test_candidate_hotfix_profile(self):
        accepted = gate.validate_candidate(previous="3.0.8.0", version="3.0.8.1",
            changed_paths=["model.go", "CHANGELOG.md", "repair.go"],
            release_profile="hotfix", current_main_parent=True)
        self.assertEqual(accepted["profile"], "hotfix")
        for invalid in ("3.0.9.0", "3.0.8.0", "3.0.8.3", "3.0.7.9"):
            with self.assertRaises(ValueError):
                gate.validate_candidate(previous="3.0.8.0", version=invalid,
                    changed_paths=["model.go", "CHANGELOG.md", "repair.go"],
                    release_profile="hotfix", current_main_parent=True)

    def test_three_part_refs_rejected_and_four_part_refs_supported(self):
        for ref in ("candidate/v3.0.8", "release/v3.0.8",
                    "candidate/v3.0.8.1.0", "candidate/v3.0.8.01"):
            with self.assertRaises(ValueError):
                gate.safe_ref(ref, ref.split("/")[0])
        self.assertEqual(gate.safe_ref("release/v3.0.8.1", "release"), "3.0.8.1")

    def test_latest_statuses_fail_closed(self):
        good=status_for(gate.REQUIRED_CANDIDATE_CONTEXTS)
        self.assertEqual(gate.exact_statuses(good,gate.REQUIRED_CANDIDATE_CONTEXTS)['rhc/preflight/linux'],'success')
        for data in [status_for(gate.REQUIRED_CANDIDATE_CONTEXTS[:-1]),
                     status_for(gate.REQUIRED_CANDIDATE_CONTEXTS,'pending'),
                     status_for(gate.REQUIRED_CANDIDATE_CONTEXTS,'failure'),
                     {'statuses': []}]:
            with self.assertRaises(ValueError):gate.exact_statuses(data,gate.REQUIRED_CANDIDATE_CONTEXTS)

    def test_work_completion_freshness(self):
        good={'result':'PASS','workSha':S,'baseMainSha':T,'linux':'success','windows':'success'}
        self.assertTrue(gate.validate_work_completion(good,work_sha=S,base_main_sha=T))
        for change in [{'workSha':T},{'baseMainSha':S},{'linux':'failure'},{'result':'BLOCKED'}]:
            bad=dict(good,**change)
            with self.assertRaises(ValueError):gate.validate_work_completion(bad,work_sha=S,base_main_sha=T)

    def test_preactivation_policy_disabled(self):
        policy={'productionEnabled':False,'distribution':'unknown','signingDecision':'unknown','rollbackVerified':False}
        data=dict(public_version='3.0.8.0',staged_version='3.0.8.1',expected_previous='3.0.8.0',
                  candidate_sha=S,release_sha=T,
                  candidate_statuses=status_for(gate.REQUIRED_CANDIDATE_CONTEXTS),
                  release_statuses=status_for(gate.REQUIRED_RELEASE_CONTEXTS),policy=policy)
        with self.assertRaisesRegex(ValueError,'disabled'):gate.validate_preactivation(**data)
        approved=dict(policy,productionEnabled=True,distribution='repo-downloads',
                      signingDecision='unsigned-approved',rollbackVerified=True)
        self.assertEqual(gate.validate_preactivation(**dict(data,policy=approved))['result'],'PASS')
        with self.assertRaisesRegex(ValueError,'repo-downloads'):
            gate.publication_policy(dict(approved,distribution='github-release'))
        for change in [{'public_version':'3.0.8.1'},{'staged_version':'3.0.8.0'},{'candidate_sha':'bad'},
                       {'release_statuses':status_for(gate.REQUIRED_RELEASE_CONTEXTS[:-1])}]:
            with self.assertRaises(ValueError):gate.validate_preactivation(**dict(data,policy=approved,**change))

if __name__=='__main__':unittest.main(verbosity=2)
