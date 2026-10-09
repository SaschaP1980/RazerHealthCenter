"""RHC-76: version-neutral, fail-closed, nonpublishing DevOps regression tests."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_workflow_reliability as r

A = "a" * 40
B = "b" * 40
C = "c" * 40


def fixture():
    return dict(
        source_sha=C,
        pull_requests=[dict(number=87, title="[RHC-82] Next HOTFIX", merged_at="2026-10-09T10:00:00Z",
                            merge_commit_sha=C, base=dict(ref="main"), head=dict(sha=B),
                            body="**Refs #82** -- exact Work source, hardware deferred")],
        work_commit=dict(sha=B, commit=dict(message="source\n\nRHC-Issue: 82\nRelease-Profile: version-only\nDevelopment-Completion: requested")),
        issue=dict(number=82, state="open", pull_request=None, title="[RHC-82] Next HOTFIX"),
    )


class Provenance(unittest.TestCase):
    def test_two_distinct_live_issue_numbers_never_use_historical_default(self):
        for number in (72, 82, 131):
            x = fixture()
            x["pull_requests"][0]["title"] = f"[RHC-{number}] Next HOTFIX"
            x["pull_requests"][0]["body"] = f"**Refs #{number}** and exact source SHA"
            x["work_commit"]["commit"]["message"] = f"source\n\nRHC-Issue: {number}\nRelease-Profile: version-only\nDevelopment-Completion: requested"
            x["issue"]["number"] = number
            self.assertEqual(r.resolve_source_provenance(**x),
                             {"issueNumber": number, "sourcePR": 87, "workHead": B})

    def test_adversarial_source_mismatch_fails_closed(self):
        variants = [
            lambda x: x.update(source_sha=A),
            lambda x: x["pull_requests"][0].update(merge_commit_sha=A),
            lambda x: x["pull_requests"][0].update(merged_at=None),
            lambda x: x["pull_requests"][0].update(number=0),
            lambda x: x["pull_requests"][0].update(base=dict(ref="dev")),
            lambda x: x["pull_requests"][0].update(head=dict(sha=A)),
            lambda x: x["pull_requests"][0].update(title="[RHC-34] stale"),
            lambda x: x["pull_requests"][0].update(body="RHC-33 reference only"),
            lambda x: x["pull_requests"][0].update(body="Refs #82\nRefs #77"),
            lambda x: x["work_commit"]["commit"].update(message="source\nRHC-Issue: 34\nRelease-Profile: version-only"),
            lambda x: x["work_commit"]["commit"].update(message="source\nRHC-Issue: 82\nRHC-Issue: 82\nRelease-Profile: version-only"),
            lambda x: x["work_commit"]["commit"].update(message="source\nRHC-Issue: 82\nRelease-Profile: production"),
            lambda x: x["issue"].update(number=34),
            lambda x: x["issue"].update(state="closed"),
            lambda x: x["issue"].update(pull_request={"url": "not an issue"}),
            lambda x: x.update(pull_requests=[]),
            lambda x: x.update(pull_requests=x["pull_requests"] * 2),
        ]
        for change in variants:
            x = fixture()
            change(x)
            with self.subTest(change=str(change)), self.assertRaises(ValueError):
                r.resolve_source_provenance(**x)

    def test_staged_commit_and_pr_must_match_responsible_source(self):
        r.verify_release_metadata(
            82, 87, B, C,
            "release: stage\n\nRHC-Issue: 82",
            "[RHC-82] Interim unsigned v3.0.8.5",
            "Refs #82; source PR #87; sourceSha " + C)
        for change in [
            dict(commit_message="release\nRHC-Issue: 34"),
            dict(pr_title="[RHC-34] Wrong"),
            dict(pr_body="RHC-33 context only"),
            dict(pr_body="Refs #82; source PR #87; sourceSha " + A),
            dict(commit_message="release\nRHC-Issue: 82\nRHC-Issue: 82"),
        ]:
            kw=dict(issue_number=82,source_pr=87,work_head=B,source_sha=C,
                    commit_message="release\nRHC-Issue: 82",
                    pr_title="[RHC-82] Interim unsigned v3.0.8.5",
                    pr_body="Refs #82; source PR #87; sourceSha "+C)
            kw.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                r.verify_release_metadata(**kw)


def job(name, result="success"):
    return {"name":name, "conclusion":result, "status":"completed"}


class HostedEvidence(unittest.TestCase):
    def test_valid_exact_sha_and_complete_job_set(self):
        run=dict(head_sha=A, event="workflow_dispatch", status="completed",
                 conclusion="success", id=123)
        rows=[job("rhc/infra/linux"),job("rhc/infra/windows")]
        self.assertEqual(r.verify_hosted_jobs(run,rows,A,
                         ["rhc/infra/linux","rhc/infra/windows"]),123)

    def test_zero_job_action_required_and_stale_green_rejected(self):
        valid=dict(head_sha=A, event="workflow_dispatch", status="completed",
                   conclusion="success", id=123)
        rows=[job("rhc/infra/linux"),job("rhc/infra/windows")]
        cases=[
            (dict(valid,event="pull_request"),rows),
            (dict(valid,head_sha=B),rows),
            (dict(valid,conclusion="action_required"),[]),
            (valid,[]), (valid,rows[:1]),
            (valid,rows+[job("rhc/infra/linux")]),
            (valid,rows+[job("optional","skipped")]),
            (valid,[job("rhc/infra/linux","failure"),job("rhc/infra/windows")]),
            (dict(valid,status="in_progress",conclusion=None),rows),
        ]
        for run,steps in cases:
            with self.subTest(run=run,steps=steps),self.assertRaises(ValueError):
                r.verify_hosted_jobs(run,steps,A,["rhc/infra/linux","rhc/infra/windows"])

    def test_absent_steps_never_are_green(self):
        self.assertEqual(r.normalize_job_steps(None),[])
        self.assertEqual(r.normalize_job_steps({"steps": None}),[])
        self.assertEqual(r.normalize_job_steps({"steps":[]}),[])
        self.assertEqual(r.normalize_job_steps({"steps":[{"name":"compile","conclusion":"success"}]}),
                         [{"name":"compile","conclusion":"success"}])
        with self.assertRaises(ValueError):
            r.normalize_job_steps({"steps": "not an array"})


class ReadOnlyTransport(unittest.TestCase):
    def test_bounded_read_only_retry_transient(self):
        attempts=[]
        def fetch():
            attempts.append(1)
            if len(attempts)<3: raise ConnectionError("temporary")
            return {"ok":True}
        self.assertEqual(r.retry_read_only(fetch,attempts=3,sleeper=lambda _:None),{"ok":True})
        self.assertEqual(len(attempts),3)

    def test_persistent_failure_is_not_synthetic_pass(self):
        attempts=[]
        def fail():
            attempts.append(1)
            raise TimeoutError("still unavailable")
        with self.assertRaises(TimeoutError):
            r.retry_read_only(fail,attempts=2,sleeper=lambda _:None)
        self.assertEqual(len(attempts),2)
        with self.assertRaises(ValueError):
            r.retry_read_only(lambda:None,attempts=0,sleeper=lambda _:None)


class WorkflowContracts(unittest.TestCase):
    def test_reusable_publisher_has_no_hardcoded_owner_issue(self):
        y=(ROOT/".github/workflows/rhc-reusable-interim-release.yml").read_text()
        self.assertNotIn('RHC-Issue: 34',y)
        self.assertNotIn('--title "[RHC-34]',y)
        self.assertNotIn('commit_title="Release RHC v$VERSION (interim unsigned, RHC-33)"',y)
        self.assertIn("resolve-source",y)
        self.assertIn("verify-stage",y)
        self.assertIn("verify_release_metadata", (ROOT/"tools/rhc_workflow_reliability.py").read_text())

    def test_candidate_qualification_is_not_deliberately_failed(self):
        y=(ROOT/".github/workflows/rhc-candidate-preflight.yml").read_text()
        self.assertIn("rhc/preflight/candidate",y)
        self.assertNotIn("Promotion deliberately BLOCKED",y)
        self.assertNotIn("echo 'RHC_CANDIDATE_PROMOTION=BLOCKED",y)
        self.assertIn("no production promotion",y)
        policy=(ROOT/"config/rhc-release-policy.json").read_text()
        self.assertIn('"productionEnabled": false',policy)
        self.assertIn('"signingDecision": "unknown"',policy)
        self.assertIn('"rollbackVerified": false',policy)

    def test_rhc71_readback_is_preserved(self):
        y=(ROOT/".github/workflows/rhc-downloads-verify.yml").read_text()
        self.assertIn("tools/rhc_remote_binary_verify.py",y)


if __name__ == "__main__":
    unittest.main()
