"""RHC-200 RED: conservative auto-recheck triage and idempotent Issue closure."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_postrelease_recheck as recheck
import rhc158_release_closure as closure
import rhc139_rolling_audit as audit
from test_rhc_158_release_closure_contracts import Fake, MAIN, SOURCE

VERSION = "3.0.8.24"
RELEASE_SHA = "a" * 40


def original_run(state="success"):
    return dict(id=1234, name="RHC POSTRELEASE v"+VERSION+" main:"+RELEASE_SHA,
                event="workflow_dispatch",
                head_sha=RELEASE_SHA, head_branch="main",
                status="completed", conclusion=state, run_attempt=1,
                display_title="RHC POSTRELEASE v"+VERSION+" main:"+RELEASE_SHA,
                actor={"login": "github-actions[bot]"})


def real_jobs(state="success"):
    return [dict(name=name, status="completed", conclusion=state if i == 0 else "success")
            for i,name in enumerate(recheck.JOB_NAMES)]


class RecheckTriage(unittest.TestCase):
    def test_authentic_original_success_is_inapplicable_only_for_auto_events(self):
        run=original_run()
        got=lambda _: real_jobs()
        self.assertTrue(recheck.original_release_passed([run], RELEASE_SHA, VERSION, got))
        self.assertEqual(recheck.classify_nonapplicable_recheck(
            [run],RELEASE_SHA,VERSION,got,"workflow_run"), "ORIGINAL_RHC102_3JOB_PASS")
        self.assertEqual(recheck.classify_nonapplicable_recheck(
            [run],RELEASE_SHA,VERSION,got,"schedule"), "ORIGINAL_RHC102_3JOB_PASS")
        self.assertIsNone(recheck.classify_nonapplicable_recheck(
            [run],RELEASE_SHA,VERSION,got,"workflow_dispatch"))

    def test_failed_real_original_is_never_n_a(self):
        run=original_run("failure")
        self.assertFalse(recheck.original_release_passed(
            [run], RELEASE_SHA, VERSION, lambda _: real_jobs("failure")))
        self.assertIsNone(recheck.classify_nonapplicable_recheck(
            [run], RELEASE_SHA,VERSION,lambda _: real_jobs("failure"),"workflow_run"))

    def test_zero_job_skipped_forged_or_untrusted_original_never_skips(self):
        cases=[
            ([original_run()],lambda _:[]),
            ([dict(original_run(),conclusion="skipped")],lambda _:real_jobs()),
            ([dict(original_run(),status="in_progress")],lambda _:real_jobs()),
            ([dict(original_run(),head_sha="e"*40)],lambda _:real_jobs()),
            ([dict(original_run(),head_branch="untrusted")],lambda _:real_jobs()),
            ([dict(original_run(),name="Other successful workflow")],lambda _:real_jobs()),
            ([dict(original_run(),actor={"login":"attacker"})],lambda _:real_jobs()),
            ([dict(original_run(),event="pull_request")],lambda _:real_jobs()),
            ([original_run(),original_run()],lambda _:real_jobs()),
        ]
        for rows,getter in cases:
            with self.subTest(rows=len(rows)):
                with self.assertRaises(ValueError):
                    recheck.classify_nonapplicable_recheck(
                        rows, RELEASE_SHA,VERSION,getter,"workflow_run")

    def test_no_original_run_must_not_silently_skip(self):
        self.assertIsNone(recheck.classify_nonapplicable_recheck(
            [],RELEASE_SHA,VERSION,lambda _:[],"workflow_run"))


class ClosureDiagnostics(unittest.TestCase):
    def test_fixed_sanitized_predicate_without_credentials_or_body(self):
        error=ValueError("RHC139_AUDIT_BLOCKED: concurrent Rolling Comment revision changed token=secret")
        info=closure.blocked_diagnostic(error)
        self.assertEqual(info["code"], "ROLLING_PREWRITE_CONFLICT")
        self.assertNotIn("secret",json.dumps(info))
        self.assertNotIn("token=",json.dumps(info))
        for exc in (OSError("HTTP 403 token=abc"),RuntimeError("private issue body"),
                    KeyError("authorization bearer secret")):
            output=json.dumps(closure.blocked_diagnostic(exc))
            self.assertNotIn("secret",output)
            self.assertNotIn("bearer",output)
            self.assertNotIn("HTTP 403",output)

    def test_only_prewrite_comment_drift_may_retry_and_full_proof_is_rechecked(self):
        g=Fake()
        initial=closure.collect_release_proof(g,512)
        with patch.object(closure,"collect_release_proof",return_value=initial) as collect, \
             patch.object(closure.audit,"finalize",
                side_effect=[ValueError("RHC139_AUDIT_BLOCKED: comment changed before patch"),
                             {"status":"READY_PLAN_ONLY"}]) as finish:
            result=closure.resilient_finalize(g,512,initial,apply=False,max_attempts=2)
        self.assertEqual(result["status"],"READY_PLAN_ONLY")
        self.assertEqual(finish.call_count,2)
        self.assertEqual(collect.call_count,1)

    def test_no_retry_for_postwrite_or_changed_provenance(self):
        g=Fake()
        initial=closure.collect_release_proof(g,512)
        with patch.object(closure.audit,"finalize",
                side_effect=ValueError("RHC139_AUDIT_BLOCKED: saved Rolling Comment readback disagrees")) as finish:
            with self.assertRaises(ValueError):
                closure.resilient_finalize(g,512,initial,apply=True,max_attempts=2)
            self.assertEqual(finish.call_count,1)
        divergent=dict(initial,merged_sha="0"*40)
        with patch.object(closure.audit,"finalize",
                side_effect=ValueError("RHC139_AUDIT_BLOCKED: concurrent Rolling Comment revision changed")), \
             patch.object(closure,"collect_release_proof",return_value=divergent):
            with self.assertRaises(ValueError):
                closure.resilient_finalize(g,512,initial,apply=True,max_attempts=2)


class ClosedJournalRecovery(unittest.TestCase):
    def fixture(self):
        g=Fake()
        proof=closure.collect_release_proof(g,512)
        event=[]
        for name,rid in proof["run_ids"].items():
            sha=({"work":proof["work_sha"],"candidate":proof["source_sha"],
                  "publisher":proof["source_sha"],"downloads":proof["stage_sha"],
                  "rhc102":proof["merged_sha"]})[name]
            event.append(dict(key=name+"-"+str(rid),issue=158,sha=sha,status="success",
                              run_id=rid,job_count=g.jobs[rid]))
        now=datetime(2026,10,15,tzinfo=timezone.utc)
        body=g.comments[0]["body"]
        for item in event:
            body=audit.render_event(body,item,now)
        body=audit._set_line(body,"Agent-State","WAITING_FOR_GITHUB")
        g.comments[0]["body"]=body
        g.comments[0]["updated_at"]="2026-10-15T11:00:00Z"
        g.issue.update(state="closed",state_reason="completed",
                       closed_at="2026-10-15T11:01:00Z")
        g.update_comment=lambda cid,new: g.comments[0].update(body=new)
        return g,proof,event

    def test_recover_already_closed_waiting_journal_with_five_proved_events(self):
        g,proof,events=self.fixture()
        result=audit.complete_closed_comment(g,proof,events)
        self.assertEqual(result["status"],"COMPLETED_RECOVERED")
        self.assertIn("**Agent-State:** COMPLETED",g.comments[0]["body"])
        self.assertIn("RHC139_ISSUE_CLOSED",g.comments[0]["body"])
        self.assertEqual(g.issue["state"],"closed")
        self.assertEqual(g.comments[0]["body"].count("RHC139_ISSUE_CLOSED"),1)

    def test_partial_journal_does_not_invent_pass(self):
        g,proof,events=self.fixture()
        g.comments[0]["body"]=g.comments[0]["body"].replace(
            '- RHC139_EVENT '+json.dumps(events[0],sort_keys=True,
                                          ensure_ascii=True,separators=(",",":")),'')
        with self.assertRaises(ValueError):
            audit.complete_closed_comment(g,proof,events)
        self.assertNotIn("RHC139_ISSUE_CLOSED",g.comments[0]["body"])

    def test_completed_state_without_exact_authenticated_close_never_recovers(self):
        for field,bad in (("state_reason","not_planned"),("closed_at",None)):
            g,proof,events=self.fixture()
            g.issue[field]=bad
            with self.subTest(field=field),self.assertRaises(ValueError):
                audit.complete_closed_comment(g,proof,events)


if __name__ == "__main__":
    unittest.main()
