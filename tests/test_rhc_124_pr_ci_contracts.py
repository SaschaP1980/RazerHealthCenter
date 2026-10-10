"""RHC-124: real PR hosted-check gate and least-privilege App wiring."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rhc124_pr_ci import (EvidenceBlocked, EvidencePending, verify_pr_ci)  # noqa: E402

SHA = "a" * 40
ACTOR = "rhc-release-pr-bot[bot]"
PR = {
    "number": 456, "title": "RHC release candidate", "state": "open",
    "draft": False, "created_at": "2026-10-10T18:00:00Z",
    "user": {"login": ACTOR},
    "head": {"sha": SHA, "ref": "release/v3.0.8.12"},
    "base": {"ref": "main"},
}
NAMES = {
    378158256: ("rhc/infra/linux", "rhc/infra/windows", "rhc/infra/artifact-node24"),
    378374563: ("Validate ZIP manifest and unmodified release history",),
    378644602: ("Verify immutable downloads and current release policy rejection",),
}


def fixture():
    runs, jobs = [], {}
    for index, (workflow, names) in enumerate(NAMES.items()):
        run_id = 900 + index
        runs.append({
            "id": run_id, "workflow_id": workflow,
            "head_sha": SHA, "head_branch": PR["head"]["ref"],
            "event": "pull_request", "actor": {"login": ACTOR},
            "display_title": PR["title"],
            "created_at": "2026-10-10T18:00:01Z", "run_attempt": 1,
            "status": "completed", "conclusion": "success",
        })
        jobs[run_id] = [
            {"id": run_id * 10 + k, "run_id": run_id, "name": name,
             "status": "completed", "conclusion": "success"}
            for k, name in enumerate(names)
        ]
    return dict(PR), runs, jobs


class RHC124PrGateTests(unittest.TestCase):
    def test_exact_genuine_jobs_pass(self):
        pr, runs, jobs = fixture()
        report = verify_pr_ci(pr, runs, jobs, SHA, ACTOR)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["jobs"], 5)
        self.assertEqual(report["workflows"], 3)

    def test_bot_identity_or_forged_pr_rejected(self):
        for bad in ["github-actions[bot]", "someone-else[bot]", "rhc-release-pr-bot"]:
            with self.subTest(bad=bad):
                pr, runs, jobs = fixture()
                pr["user"]["login"] = bad
                with self.assertRaises(EvidenceBlocked):
                    verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_stale_sha_wrong_branch_base_pr_number_rejected(self):
        for key, value in [("sha", "b"*40), ("ref", "work/RHC-124")]:
            pr, runs, jobs = fixture()
            pr["head"][key] = value
            with self.assertRaises(EvidenceBlocked):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)
        pr, runs, jobs = fixture()
        pr["base"]["ref"] = "other"
        with self.assertRaises(EvidenceBlocked):
            verify_pr_ci(pr, runs, jobs, SHA, ACTOR)
        pr, runs, jobs = fixture()
        pr["number"] = 0
        with self.assertRaises(EvidenceBlocked):
            verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_wrong_event_actor_workflow_branch_or_sha_rejected(self):
        for prop, value in [("event", "workflow_dispatch"),
                            ("actor", {"login": "github-actions[bot]"}),
                            ("head_sha", "b"*40), ("head_branch", "other"),
                            ("display_title", "unrelated")]:
            pr, runs, jobs = fixture()
            runs[0][prop] = value
            with self.subTest(prop=prop), self.assertRaises(EvidenceBlocked):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_real_failure_skipped_cancelled_action_required_block(self):
        for conclusion in ["failure", "skipped", "cancelled", "action_required"]:
            pr, runs, jobs = fixture()
            runs[0]["conclusion"] = conclusion
            with self.subTest(conclusion=conclusion), self.assertRaises(EvidenceBlocked):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_failed_windows_job_even_successful_workflow_blocks(self):
        pr, runs, jobs = fixture()
        jobs[900][1]["conclusion"] = "failure"
        with self.assertRaises(EvidenceBlocked):
            verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_missing_or_zero_jobs_never_green(self):
        for key in (900, 901, 902):
            pr, runs, jobs = fixture()
            jobs[key] = []
            with self.subTest(workflow=key), self.assertRaises(EvidenceBlocked):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_job_run_binding_extra_skipped_job_duplicate_names_block(self):
        for change in ["foreign", "skipped", "duplicate"]:
            pr, runs, jobs = fixture()
            if change == "foreign":
                jobs[900][0]["run_id"] = 321
            elif change == "skipped":
                jobs[900].append({"id": 98765, "run_id": 900,
                                  "name": "extra", "status": "completed",
                                  "conclusion": "skipped"})
            else:
                jobs[900].append(dict(jobs[900][0], id=99999))
            with self.subTest(change=change), self.assertRaises(EvidenceBlocked):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_missing_or_incomplete_pr_workflow_is_pending_not_pass(self):
        for scenario in ["no_run", "queued", "in_progress"]:
            pr, runs, jobs = fixture()
            if scenario == "no_run":
                runs.pop()
            else:
                runs[0]["status"] = scenario
                runs[0]["conclusion"] = None
            with self.subTest(scenario=scenario), self.assertRaises(EvidencePending):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_missing_job_api_and_unrelated_run_block(self):
        pr, runs, jobs = fixture()
        del jobs[900]
        with self.assertRaises(EvidenceBlocked):
            verify_pr_ci(pr, runs, jobs, SHA, ACTOR)
        pr, runs, jobs = fixture()
        runs.append(dict(runs[0], id=999, workflow_id=378158256))
        jobs[999] = list(jobs[900])
        with self.assertRaises(EvidenceBlocked):
            verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_missing_timestamp_or_pre_pr_creation_rejected(self):
        for bad in [None, "2026-10-10T17:59:59Z"]:
            pr, runs, jobs = fixture()
            runs[1]["created_at"] = bad
            with self.subTest(time=bad), self.assertRaises(EvidenceBlocked):
                verify_pr_ci(pr, runs, jobs, SHA, ACTOR)

    def test_hosted_trusted_dispatch_still_separately_required(self):
        y = (ROOT / ".github/workflows/rhc-reusable-interim-release.yml").read_text()
        self.assertIn("rhc_workflow_reliability.py verify-hosted", y)
        self.assertIn('gh workflow run rhc-downloads-verify.yml --ref "release/v$VERSION"', y)
        self.assertIn("RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS", y)

    def test_wiring_scopes_app_only_to_pr_creation(self):
        y = (ROOT / ".github/workflows/rhc-reusable-interim-release.yml").read_text()
        self.assertIn("actions/create-github-app-token@", y)
        self.assertIn("permission-pull-requests: write", y)
        self.assertIn("permission-contents: read", y)
        self.assertIn("RHC_RELEASE_APP_ID", y)
        self.assertIn("RHC_RELEASE_APP_PRIVATE_KEY", y)
        self.assertIn("needs.stage.outputs.release_app_actor", y)
        self.assertIn("rhc124_pr_ci.py", y)
        self.assertIn("GH_TOKEN: ${{ steps.app-token.outputs.token }}", y)
        self.assertEqual(y.count("gh pr create"), 1)
        self.assertIn("GH_TOKEN: ${{ github.token }}", y)
        self.assertNotIn("pull_request_target:", y)


if __name__ == "__main__":
    unittest.main()
