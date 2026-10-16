"""RHC-206 RED: real Gateway transport must create only proven Fast audit comments."""
from pathlib import Path
from unittest.mock import Mock, patch
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rhc158_release_closure as closure
import rhc190_fast_closure as fast
from test_rhc190_fast_closure_contracts import FastClosureTests
from test_rhc_158_release_closure_contracts import SOURCE, MAIN

REPO = "SaschaP1980/RazerHealthCenter"


def fixture():
    return FastClosureTests().fixture()


def expected_body(issue=158):
    value = {
        "issue":issue, "version":"3.0.8.16",
        "mainSha":MAIN, "sourceSha":SOURCE,"pr":199,
        "runIds":{"candidate":702,"publisher":512,"downloads":703,"rhc102":704},
        "validation":"ACTUAL_CANDIDATE_3_PUBLISHER_4_DOWNLOADS_1_RHC102_3"}
    return fast.RECORD + json.dumps(value,sort_keys=True)


def attached(f):
    """Actual production Gateway's narrow operation, not fake API verb acceptance."""
    gateway = closure.Gateway(REPO)
    gateway.get_issue = lambda number: f.get_issue(number)
    gateway.get_main_sha = lambda: f.get_main_sha()
    gateway.get_latest = lambda: f.get_latest()
    gateway.list_issue_comments = lambda number: f.list_issue_comments(number)
    f.create_fast_audit_comment = gateway.create_fast_audit_comment
    def update_issue(number, state):
        if number != 158 or state != "closed":
            raise AssertionError("unapproved Issue transition")
        f.issue.update(state="closed",state_reason="completed",
                       closed_at="2026-10-16T03:00:00Z")
    f.update_issue = update_issue
    return gateway


class ExactFastGatewayTests(unittest.TestCase):
    def test_real_gateway_post_succeeds_only_after_all_four_real_gates(self):
        f = fixture()
        attached(f)
        calls=[]
        def runner(argv, **kwargs):
            calls.append((argv,kwargs))
            record = json.loads(kwargs["input"])
            f.comments.append({"id":992,"body":record["body"]})
            return Mock(returncode=0,stdout=json.dumps(f.comments[-1]),stderr="")
        with patch("rhc158_release_closure.subprocess.run", side_effect=runner):
            result = fast.close_fast(f,512,SOURCE,apply=True)
            repeat = fast.close_fast(f,512,SOURCE,apply=True)
        self.assertEqual(result["status"],"COMPLETED")
        self.assertEqual(repeat["status"],"ALREADY_COMPLETED")
        self.assertEqual(len(calls),1)
        argv, kw = calls[0]
        self.assertEqual(argv,["gh","api","-X","POST",
                              "repos/"+REPO+"/issues/158/comments","--input","-"])
        self.assertEqual(kw["input"],json.dumps({"body":expected_body()}))
        self.assertTrue(kw["capture_output"])
        self.assertEqual(kw["timeout"],45)
        self.assertEqual(sum(c["body"].startswith(fast.RECORD) for c in f.comments),1)

    def test_cross_issue_forged_payload_and_bad_schema_never_reach_transport(self):
        f = fixture()
        g = attached(f)
        good = json.loads(expected_body()[len(fast.RECORD):])
        variants = [
            (159,expected_body()),
            (158,expected_body(159)),
            (158,"RHC139_EVENT=forged"),
            (158,fast.RECORD+"not-json"),
            (158,fast.RECORD+json.dumps(dict(good,pr=0),sort_keys=True)),
            (158,fast.RECORD+json.dumps(dict(good,mainSha="f"*40),sort_keys=True)),
            (158,fast.RECORD+json.dumps(dict(good,sourceSha="f"*40),sort_keys=True)),
            (158,fast.RECORD+json.dumps(dict(good,secret="evil"),sort_keys=True)),
            (158,fast.RECORD+json.dumps(dict(good,runIds={"publisher":512}),sort_keys=True)),
            (158,fast.RECORD+json.dumps(good,indent=1)),
        ]
        with patch("rhc158_release_closure.subprocess.run") as run:
            for number,message in variants:
                with self.subTest(issue=number,message=message[:80]),self.assertRaises(ValueError):
                    g.create_fast_audit_comment(number,message)
            self.assertEqual(run.call_count,0)
            with self.assertRaises(ValueError):
                g.api("POST","issues/158/comments",{"body":expected_body()})

    def test_uncertain_remote_write_reconciles_by_get_and_never_reposts(self):
        f=fixture()
        attached(f)
        seen=[]
        def saved_then_transport_fails(argv,**kwargs):
            seen.append(argv)
            f.comments.append({"id":993,"body":json.loads(kwargs["input"])["body"]})
            return Mock(returncode=1,stdout="",stderr="private token=NEVER_ECHO")
        with patch("rhc158_release_closure.subprocess.run",
                   side_effect=saved_then_transport_fails):
            outcome=fast.close_fast(f,512,SOURCE,apply=True)
            repeat=fast.close_fast(f,512,SOURCE,apply=True)
        self.assertEqual(outcome["status"],"COMPLETED")
        self.assertEqual(repeat["status"],"ALREADY_COMPLETED")
        self.assertEqual(len(seen),1)

    def test_uncertain_remote_failure_without_saved_audit_fails_closed(self):
        f=fixture()
        attached(f)
        with patch("rhc158_release_closure.subprocess.run",
                   return_value=Mock(returncode=1,stdout="",stderr="sensitive")) as run:
            with self.assertRaises(ValueError):
                fast.close_fast(f,512,SOURCE,apply=True)
            self.assertEqual(run.call_count,1)
        self.assertEqual(f.issue["state"],"open")

    def test_stale_main_failed_hosted_jobs_and_duplicate_record_never_post(self):
        for cause in ("stale_main","zero_windows_jobs","source_tag","old_duplicate"):
            f=fixture()
            g=attached(f)
            if cause=="stale_main": f.pr["base"]["sha"]="f"*40
            if cause=="zero_windows_jobs": f.jobs[702]=0
            if cause=="source_tag": f.tag_sha="9"*40
            if cause=="old_duplicate":
                f.comments += [{"id":995,"body":expected_body()},
                               {"id":996,"body":expected_body()}]
            with self.subTest(cause=cause),patch(
                    "rhc158_release_closure.subprocess.run") as run:
                with self.assertRaises(ValueError):
                    fast.close_fast(f,512,SOURCE,apply=True)
                self.assertEqual(run.call_count,0)
                self.assertEqual(f.issue["state"],"open")

    def test_work_audit_gateway_keeps_get_patch_only(self):
        import rhc139_rolling_audit as audit
        g=audit.GitHubGateway(REPO)
        with patch("rhc139_rolling_audit.subprocess.run") as p:
            with self.assertRaises(ValueError):
                g.api("POST","issues/158/comments",{"body":expected_body()})
            p.assert_not_called()


if __name__=="__main__":
    unittest.main()
