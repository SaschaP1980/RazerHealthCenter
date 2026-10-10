"""RHC-114: supplementary zero-job runs never qualify as trusted hosted gates."""
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from rhc114_ci_noise import (EvidenceBlocked, classify_supplementary,
                             verify_trusted_dispatch, evaluate_release_pr,
                             read_only_github_audit)

SHA = "47d421612470a94e2baeb0b13b2c5c1c854c34ef"
OTHER = "b" * 40
WF_DOWNLOADS = 378374563
WF_PREACTIVATION = 378644602
WF_INFRA = 378158256
BOT = {"login": "github-actions[bot]"}
PR = dict(number=113, base={"ref": "main"}, head={"sha": SHA, "ref": "release/v3.0.8.10"},
          user=BOT, merged=True, state="closed")
WFS = [(38043054293, WF_DOWNLOADS, "RHC Repository Downloads Integrity (nonpublishing)"),
       (38043054299, WF_PREACTIVATION, "RHC-12 Release Preactivation Evidence Check (read-only)"),
       (38043054302, WF_INFRA, "RHC Infrastructure Qualification (nonpublishing)")]


def run(id, workflow, *, sha=SHA, event="pull_request", status="completed",
        conclusion="failure", actor=BOT, name="optional"):
    return dict(id=id, workflow_id=workflow, name=name, head_sha=sha,
                head_branch="release/v3.0.8.10", event=event, status=status,
                conclusion=conclusion, actor=actor,
                created_at="2026-10-10T09:54:40Z", updated_at="2026-10-10T09:54:57Z")


def trusted(jobs=None, **changes):
    x = run(38043049852, WF_DOWNLOADS, event="workflow_dispatch",
            conclusion="success", name="RHC Repository Downloads Integrity (nonpublishing)")
    x.update(changes)
    return x, jobs if jobs is not None else [dict(id=999, run_id=38043049852,
           name="Validate ZIP manifest and unmodified release history",
           status="completed", conclusion="success")]


class NoiseContracts(unittest.TestCase):
    def test_three_historical_records_preserved_not_green(self):
        runs = [run(id, workflow, name=name) for id,workflow,name in WFS]
        events = classify_supplementary(PR, SHA, runs, {r["id"]: [] for r in runs})
        self.assertEqual(len(events), 3)
        self.assertTrue(all(e["classification"] == "SUPPLEMENTARY_ZERO_JOB_FAILURE" for e in events))
        self.assertEqual([e["runId"] for e in events], [x[0] for x in WFS])
        self.assertTrue(all(e["conclusion"] == "failure" and e["actualJobs"] == 0 for e in events))

    def test_trusted_one_real_hosted_dispatch_is_pass(self):
        r, jobs = trusted()
        result = verify_trusted_dispatch(r, jobs, SHA, WF_DOWNLOADS)
        self.assertEqual(result["classification"], "TRUSTED_HOSTED_PASS")
        self.assertEqual(result["runId"], r["id"])
        self.assertEqual(result["actualJobs"], 1)

    def test_nonpassing_mandatory_jobs_always_block(self):
        for change in ({"status": "completed", "conclusion": "failure"},
                       {"status": "completed", "conclusion": "skipped"},
                       {"status": "in_progress", "conclusion": None}):
            r, jobs = trusted(jobs=[dict(id=2,run_id=38043049852,name="Required",
                                         **change)])
            with self.subTest(change=change), self.assertRaises(EvidenceBlocked):
                verify_trusted_dispatch(r, jobs, SHA, WF_DOWNLOADS)

    def test_zero_job_action_required_skipped_cancelled_are_never_pass(self):
        for conclusion in ("failure", "action_required", "skipped", "cancelled", None):
            r, _ = trusted(conclusion=conclusion)
            with self.subTest(conclusion=conclusion), self.assertRaises(EvidenceBlocked):
                verify_trusted_dispatch(r, [], SHA, WF_DOWNLOADS)

    def test_wrong_event_workflow_actor_or_sha_blocks_trusted(self):
        for change in ({"event": "pull_request"}, {"head_sha": OTHER},
                       {"workflow_id": WF_INFRA}, {"actor": {"login": "untrusted"}},
                       {"status": "queued"}, {"conclusion": "failure"}):
            r, jobs = trusted(**change)
            with self.subTest(change=change), self.assertRaises(EvidenceBlocked):
                verify_trusted_dispatch(r, jobs, SHA, WF_DOWNLOADS)

    def test_missing_check_job_evidence_is_never_synthetic_pass(self):
        r,_ = trusted()
        for jobs in (None, [], [{}]):
            with self.subTest(jobs=jobs), self.assertRaises(EvidenceBlocked):
                verify_trusted_dispatch(r, jobs, SHA, WF_DOWNLOADS)

    def test_supplementary_real_failed_job_is_not_renamed_optional_zero_job(self):
        r = run(38043054293, WF_DOWNLOADS)
        events = classify_supplementary(PR, SHA, [r], {r["id"]: [
            dict(run_id=r["id"],name="Test", status="completed",conclusion="failure")]})
        self.assertEqual(events[0]["classification"], "ACTUAL_HOSTED_JOB_FAIL")
        self.assertEqual(events[0]["actualJobs"], 1)

    def test_failed_workflow_with_all_successful_jobs_is_not_relabelled_success(self):
        r = run(38043054293, WF_DOWNLOADS, conclusion="failure")
        result = classify_supplementary(PR,SHA,[r],{r["id"]:[
            dict(id=5,run_id=r["id"],name="actual job",
                 status="completed",conclusion="success")]})
        self.assertNotEqual(result[0]["classification"],
                            "SUPPLEMENTARY_HOSTED_SUCCESS_NOT_TRUSTED_DISPATCH")
        self.assertEqual(result[0]["conclusion"],"failure")

    def test_human_pr_failed_zero_job_is_not_labeled_bot_noise(self):
        pr = dict(PR, user={"login":"contributor"})
        r = run(38043054293, WF_DOWNLOADS, actor={"login":"contributor"})
        events = classify_supplementary(pr,SHA,[r],{r["id"]:[]})
        self.assertEqual(events[0]["classification"],"ZERO_JOB_FAILURE_UNEXPLAINED")

    def test_unrelated_workflow_runs_are_not_certified(self):
        r = run(123, 987654321)
        events = classify_supplementary(PR,SHA,[r],{123:[]})
        self.assertEqual(events[0]["classification"],"UNRELATED_RUN_NOT_QUALIFICATION")

    def test_stale_sha_and_run_id_mismatch_fail_closed(self):
        for corrupt in (run(12, WF_DOWNLOADS, sha=OTHER), run(12, WF_DOWNLOADS, status="queued")):
            with self.subTest(corrupt=corrupt),self.assertRaises(EvidenceBlocked):
                classify_supplementary(PR,SHA,[corrupt],{12:[]})
        r,jobs = trusted(jobs=[dict(id=1,run_id=25,name="Test",
                                    status="completed",conclusion="success")])
        with self.assertRaises(EvidenceBlocked):
            verify_trusted_dispatch(r,jobs,SHA,WF_DOWNLOADS)

    def test_report_separates_optional_noise_from_true_gate(self):
        extra=[run(id, wf, name=name) for id,wf,name in WFS]
        r,jobs=trusted()
        report=evaluate_release_pr(PR,SHA,extra,{x["id"]:[] for x in extra},r,jobs,WF_DOWNLOADS)
        self.assertEqual(report["trustedGate"]["classification"], "TRUSTED_HOSTED_PASS")
        self.assertEqual(report["supplementary"]["zeroJobFailureCount"],3)
        self.assertNotEqual(report["result"],"ALL_GREEN")
        self.assertEqual(report["sourceSha"],SHA)

    def test_report_never_qualifies_failed_required_job(self):
        r,jobs=trusted(jobs=[dict(id=1,run_id=38043049852,name="Test",
                                   status="completed",conclusion="failure")])
        with self.assertRaises(EvidenceBlocked):
            evaluate_release_pr(PR,SHA,[],{},r,jobs,WF_DOWNLOADS)

    def test_real_supplementary_hosted_failure_remains_visible_even_if_dispatch_passed(self):
        r, jobs = trusted()
        extra = run(38043054293, WF_DOWNLOADS)
        report = evaluate_release_pr(PR,SHA,[extra],{extra["id"]:[
            dict(id=20,run_id=extra["id"],name="genuine test",
                 status="completed",conclusion="failure")]},r,jobs,WF_DOWNLOADS)
        self.assertEqual(report["result"],
                         "TRUSTED_GATE_PASS_WITH_OTHER_HOSTED_FAILURES_REQUIRING_REVIEW")
        self.assertEqual(report["supplementary"]["actualHostedFailures"],1)
        self.assertEqual(report["trustedGate"]["classification"],"TRUSTED_HOSTED_PASS")

    def test_timing_reports_real_relative_events_without_claiming_speedup(self):
        r,jobs=trusted(updated_at="2026-10-10T09:54:46Z")
        extra=run(38043054293,WF_DOWNLOADS)
        pr=dict(PR,merged_at="2026-10-10T09:54:56Z")
        report=evaluate_release_pr(pr,SHA,[extra],{extra["id"]:[]},r,jobs,WF_DOWNLOADS)
        timing=report["releaseCriticalPath"]
        self.assertEqual(timing["trustedCompletedSecondsBeforeMerge"],10)
        self.assertEqual(timing["supplementaryCompletions"][0]
                         ["completedSecondsAfterMerge"],1)
        self.assertEqual(timing["performanceGain"],"NOT VERIFIED — cannot infer causality or improvement")

    def test_optional_action_required_and_cancelled_are_never_pass(self):
        rr=[run(501,WF_DOWNLOADS,conclusion="action_required"),
            run(502,WF_PREACTIVATION,conclusion="cancelled")]
        events=classify_supplementary(PR,SHA,rr,{501:[],502:[]})
        self.assertEqual([z["classification"] for z in events],
                        ["ZERO_JOB_NO_TEST_ACTION_REQUIRED","ZERO_JOB_NO_TEST_CANCELLED"])
        self.assertFalse(any(z["countsAsTrustedGate"] for z in events))

    def test_read_only_protocol_fetches_exact_pr_runs_jobs_and_no_writes(self):
        r,jobs=trusted()
        zero=run(*WFS[0][:2],name=WFS[0][2])
        responses={
            "/pulls/113":PR,
            "/actions/runs?head_sha="+SHA+"&event=pull_request&per_page=100&page=1":
                {"workflow_runs":[zero],"total_count":1},
            "/actions/runs/38043054293/jobs?per_page=100&page=1":{"jobs":[],"total_count":0},
            "/actions/runs/38043049852":r,
            "/actions/runs/38043049852/jobs?per_page=100&page=1":{"jobs":jobs,"total_count":1}
        }
        calls=[]
        def get(path):
            calls.append(path)
            return responses[path]
        report=read_only_github_audit(get,113,SHA,38043049852,WF_DOWNLOADS)
        self.assertEqual(report["supplementary"]["zeroJobFailureCount"],1)
        self.assertEqual(len(calls),5)
        self.assertTrue(all("POST" not in x and "PATCH" not in x for x in calls))

    def test_missing_or_ambiguous_api_pagination_blocks(self):
        r,jobs=trusted()
        def wrong(path):
            if path=="/pulls/113":return PR
            if "actions/runs?head_sha=" in path:return {"workflow_runs":[],"total_count":101}
            return {"jobs":[],"total_count":0}
        with self.assertRaises(EvidenceBlocked):
            read_only_github_audit(wrong,113,SHA,38043049852,WF_DOWNLOADS)


if __name__ == "__main__":
    unittest.main()
