"""RHC-20 owner-only main Ruleset setup contract; purely mocked, never administers GitHub."""
import copy
import io
import os
import pathlib
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_main_rules as admin

BASE = {"id":24701145, "name":"RHC - Protect main", "target":"branch",
        "enforcement":"active",
        "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
        "bypass_actors":[], "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}


class MainRulesOwnerAdmin(unittest.TestCase):
    def setUp(self):
        self.rule = copy.deepcopy(BASE)
        self.writes = []
        def gh(method,path,payload=None):
            self.assertEqual(path,"/rulesets/24701145")
            if method=="GET":
                return copy.deepcopy(self.rule)
            self.assertEqual(method,"PUT")
            self.writes.append(copy.deepcopy(payload))
            self.rule = dict(self.rule, **copy.deepcopy(payload))
            return copy.deepcopy(self.rule)
        self.fake = gh

    def call_cli(self, apply=False, authorized=False):
        args=["rhc_main_rules.py"]+(["--apply"] if apply else [])
        environment={"RHC_OWNER_RULESET_ADMIN":
                     "EXPLICIT_RULESET_ONLY" if authorized else ""}
        with patch.object(admin,"gh",side_effect=self.fake),\
             patch.object(sys,"argv",args),\
             patch.dict(os.environ,environment),redirect_stdout(io.StringIO()):
            return admin.main()

    def test_no_apply_and_no_owner_admin_token_never_write(self):
        with self.assertRaisesRegex(ValueError,"BLOCKED_ADMIN"):
            self.call_cli(apply=False,authorized=True)
        self.assertEqual(self.writes,[])
        with self.assertRaisesRegex(ValueError,"Owner did not explicitly authorize"):
            self.call_cli(apply=True,authorized=False)
        self.assertEqual(self.writes,[])

    def test_explicit_single_apply_preserves_legacy_rules_and_requires_two_infra_checks(self):
        self.call_cli(apply=True,authorized=True)
        self.assertEqual(len(self.writes),1)
        rule=self.rule
        self.assertEqual(rule["enforcement"],"active")
        self.assertEqual(rule["conditions"],BASE["conditions"])
        self.assertEqual(rule["bypass_actors"],[])
        self.assertEqual({x["type"] for x in rule["rules"]},
                         {"deletion","non_fast_forward","pull_request","required_status_checks"})
        prs=next(x for x in rule["rules"] if x["type"]=="pull_request")
        self.assertEqual(prs["parameters"]["required_approving_review_count"],0)
        checks=next(x for x in rule["rules"] if x["type"]=="required_status_checks")
        names={x["context"] for x in checks["parameters"]["required_status_checks"]}
        self.assertEqual(names,{"rhc/infra/linux","rhc/infra/windows"})
        self.assertNotIn("rhc/release/source",names)
        self.call_cli(apply=True,authorized=True)
        self.assertEqual(len(self.writes),1,"second successful run must be no-op")

    def test_admin_api_drift_must_not_claim_green(self):
        original=self.fake
        def drop_required_after_put(method,path,payload=None):
            response=original(method,path,payload)
            if method=="PUT":
                self.rule=copy.deepcopy(BASE)
            return response
        self.fake=drop_required_after_put
        with self.assertRaisesRegex(ValueError,"NOT effective"):
            self.call_cli(apply=True,authorized=True)


if __name__ == "__main__":
    unittest.main()
