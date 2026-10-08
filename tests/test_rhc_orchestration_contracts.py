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
        good=gate.validate_candidate(previous='3.0.8',version='3.0.9',
            changed_paths=['model.go','CHANGELOG.md'],release_profile='version-only',current_main_parent=True)
        self.assertEqual(good['result'],'PASS')
        for fields in [
            {'version':'3.0.8'}, {'version':'3.0.7'},
            {'changed_paths':['model.go','CHANGELOG.md','repair.go']},
            {'changed_paths':['model.go','README.md']},
            {'release_profile':'unapproved'}, {'current_main_parent':False},
            {'changed_paths':['model.go','CHANGELOG.md','private.pfx']},
        ]:
            inputs=dict(previous='3.0.8',version='3.0.9',changed_paths=['model.go','CHANGELOG.md'],
                        release_profile='version-only',current_main_parent=True)
            inputs.update(fields)
            with self.assertRaises(ValueError):gate.validate_candidate(**inputs)

    def test_refs(self):
        self.assertEqual(gate.safe_ref('candidate/v3.0.9','candidate'),'3.0.9')
        for ref in ('release/v3.0.9','candidate/v3.0.9-beta','candidate/v3.0.9/escape','candidate/v03.0.9'):
            with self.assertRaises(ValueError):gate.safe_ref(ref,'candidate')

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
        data=dict(public_version='3.0.8',staged_version='3.0.9',expected_previous='3.0.8',
                  candidate_sha=S,release_sha=T,
                  candidate_statuses=status_for(gate.REQUIRED_CANDIDATE_CONTEXTS),
                  release_statuses=status_for(gate.REQUIRED_RELEASE_CONTEXTS),policy=policy)
        with self.assertRaisesRegex(ValueError,'disabled'):gate.validate_preactivation(**data)
        approved=dict(policy,productionEnabled=True,distribution='github-release',
                      signingDecision='unsigned-approved',rollbackVerified=True)
        self.assertEqual(gate.validate_preactivation(**dict(data,policy=approved))['result'],'PASS')
        for change in [{'public_version':'3.0.9'},{'staged_version':'3.0.8'},{'candidate_sha':'bad'},
                       {'release_statuses':status_for(gate.REQUIRED_RELEASE_CONTEXTS[:-1])}]:
            with self.assertRaises(ValueError):gate.validate_preactivation(**dict(data,policy=approved,**change))

if __name__=='__main__':unittest.main(verbosity=2)
