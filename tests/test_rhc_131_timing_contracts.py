"""RHC-131 test-first: evidence-only hosted CI timing and phase reports."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rhc131_timing as timing


def run(identifier, start, finish, *, sha="a" * 40, status="completed",
        conclusion="success", event="workflow_dispatch", actor="github-actions[bot]",
        attempt=1, name="RHC Infrastructure Qualification"):
    return {
        "id": identifier, "name": name, "event": event,
        "head_sha": sha, "status": status, "conclusion": conclusion,
        "run_attempt": attempt, "actor": {"login": actor},
        "created_at": start, "run_started_at": start, "updated_at": finish,
    }


def job(identifier, start, end, *, result="success", steps=None, attempt=1):
    return {
        "id": identifier, "name": "rhc/linux", "status": "completed",
        "conclusion": result, "run_attempt": attempt,
        "started_at": start, "completed_at": end,
        "runner_name": "GitHub Actions", "labels": ["ubuntu-24.04"],
        "steps": steps or [],
    }


class TimingContractTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40

    def test_overlap_is_not_double_counted_in_critical_wall_time(self):
        a = run(1, "2026-10-10T10:00:00Z", "2026-10-10T10:00:45Z")
        jobs = {"1": {"total_count": 2, "jobs": [
            job(10, "2026-10-10T10:00:05Z", "2026-10-10T10:00:35Z"),
            job(11, "2026-10-10T10:00:15Z", "2026-10-10T10:00:45Z"),
        ]}}
        r = timing.build_report([a], jobs, expected_sha=self.sha)
        self.assertEqual(r["schema_version"], 1)
        self.assertEqual(r["measurement"]["observed_wall_seconds"], 45)
        self.assertEqual(r["measurement"]["sum_job_seconds"], 60)
        self.assertEqual(r["measurement"]["job_active_union_seconds"], 40)
        self.assertEqual(r["measurement"]["job_overlap_seconds"], 20)
        self.assertEqual(r["measurement"]["nonbusy_span_seconds"], 5)

    def test_missing_job_start_is_null_not_zero_or_pass(self):
        a = run(2, "2026-10-10T10:00:00Z", "2026-10-10T10:01:00Z")
        j = job(20, None, "2026-10-10T10:00:45Z")
        r = timing.build_report([a], {"2": {"total_count": 1, "jobs": [j]}}, expected_sha=self.sha)
        self.assertIsNone(r["runs"][0]["jobs"][0]["execution_seconds"])
        self.assertIsNone(r["runs"][0]["jobs"][0]["queue_seconds"])
        self.assertEqual(r["runs"][0]["jobs"][0]["time_verification"], "NOT_VERIFIED")

    def test_zero_job_bot_pr_failure_is_reported_without_synthetic_success(self):
        runs = [run(n, "2026-10-10T10:00:00Z", "2026-10-10T10:00:15Z",
                    event="pull_request", conclusion="failure") for n in (3, 4, 5)]
        r = timing.build_report(runs, {str(n): {"total_count": 0, "jobs": []} for n in (3, 4, 5)}, expected_sha=self.sha)
        self.assertEqual(r["zero_job_supplementary_failures"], 3)
        self.assertEqual([x["classification"] for x in r["runs"]],
                         ["SUPPLEMENTARY_ZERO_JOB_FAILURE"] * 3)
        self.assertTrue(all(x["conclusion"] == "failure" for x in r["runs"]))
        self.assertIsNone(r["measurement"]["sum_job_seconds"])

    def test_missing_hosted_job_on_mandatory_dispatch_is_not_noise(self):
        r = timing.build_report([run(6, "2026-10-10T10:00:00Z", "2026-10-10T10:00:15Z",
                                     conclusion="failure")],
                                {"6": {"total_count": 0, "jobs": []}}, expected_sha=self.sha)
        self.assertEqual(r["zero_job_supplementary_failures"], 0)
        self.assertEqual(r["runs"][0]["classification"], "NO_HOSTED_JOB_NOT_VERIFIED")

    def test_wrong_sha_does_not_enter_expected_sha_statistics(self):
        a = run(7, "2026-10-10T10:00:00Z", "2026-10-10T10:00:40Z", sha="b" * 40)
        r = timing.build_report([a], {"7": {"total_count": 0, "jobs": []}}, expected_sha=self.sha)
        self.assertEqual(r["runs"][0]["classification"], "SHA_MISMATCH")
        self.assertEqual(r["measurement"]["included_run_count"], 0)
        self.assertIsNone(r["measurement"]["observed_wall_seconds"])

    def test_retry_penalty_is_separate_from_successful_attempt(self):
        a = run(8, "2026-10-10T10:00:00Z", "2026-10-10T10:00:30Z", conclusion="success", attempt=2)
        jobs = {"8": {"total_count": 2, "jobs": [
            job(80, "2026-10-10T10:00:03Z", "2026-10-10T10:00:10Z", result="failure", attempt=1),
            job(81, "2026-10-10T10:00:15Z", "2026-10-10T10:00:30Z", attempt=2),
        ]}}
        r = timing.build_report([a], jobs, expected_sha=self.sha)
        self.assertEqual(r["measurement"]["retry_job_seconds"], 7)
        self.assertEqual(r["measurement"]["successful_attempt_job_seconds"], 15)
        self.assertEqual(r["measurement"]["sum_job_seconds"], 22)

    def test_steps_include_queue_and_validation_build_package_breakdown(self):
        a = run(9, "2026-10-10T10:00:00Z", "2026-10-10T10:00:40Z")
        steps = [
            {"name": "Set up job", "started_at": "2026-10-10T10:00:05Z", "completed_at": "2026-10-10T10:00:10Z"},
            {"name": "Compile and validate original Go Windows GUI", "started_at": "2026-10-10T10:00:10Z", "completed_at": "2026-10-10T10:00:27Z"},
            {"name": "Deterministically package source/portable twice", "started_at": "2026-10-10T10:00:27Z", "completed_at": "2026-10-10T10:00:38Z"},
        ]
        r = timing.build_report([a], {"9": {"total_count": 1, "jobs": [job(90, "2026-10-10T10:00:05Z", "2026-10-10T10:00:40Z", steps=steps)]}}, expected_sha=self.sha)
        j = r["runs"][0]["jobs"][0]
        self.assertEqual(j["queue_seconds"], 5)
        self.assertEqual(j["step_categories"]["runner_setup"], 5)
        self.assertEqual(j["step_categories"]["mixed_build_validation"], 17)
        self.assertEqual(j["step_categories"]["packaging"], 11)

    def test_malformed_clock_is_not_silently_zero(self):
        with self.assertRaises(ValueError):
            timing.parse_timestamp("2026-10-10 not-a-time")
        self.assertIsNone(timing.parse_timestamp(None))
        self.assertEqual(timing.seconds_between("2026-10-10T10:00:01Z", "2026-10-10T10:00:00Z"), None)

    def test_phase_marker_parser_rejects_secrets_and_matches_pairs(self):
        raw = "\n".join([
            "RHC131_PHASE start=2026-10-10T10:00:00.000Z label=go_build",
            "RHC131_PHASE end=2026-10-10T10:00:04.250Z label=go_build",
            "RHC131_PHASE start=2026-10-10T10:00:05.000Z label=validation",
            "RHC131_PHASE end=2026-10-10T10:00:06.000Z label=validation",
        ])
        x = timing.parse_phase_markers(raw)
        self.assertEqual(x["go_build"], 4.25)
        self.assertEqual(x["validation"], 1)
        with self.assertRaises(ValueError):
            timing.parse_phase_markers("RHC131_PHASE start=2026-10-10T10:00:00Z label=GH_TOKEN")

    def test_reports_have_no_tokens_raw_actors_or_urls(self):
        a = run(10, "2026-10-10T10:00:00Z", "2026-10-10T10:00:15Z", actor="private-user")
        r = timing.build_report([a], {"10": {"total_count": 0, "jobs": []}}, expected_sha=self.sha)
        b = json.dumps(r)
        self.assertNotIn("private-user", b)
        self.assertNotIn("token", b.lower())
        self.assertIn("event", r["runs"][0])

    def test_unknown_run_completion_is_not_synthesized_from_updated_at(self):
        a = run(11, "2026-10-10T10:00:00Z", "2026-10-10T10:00:15Z", status="in_progress", conclusion=None)
        r = timing.build_report([a], {"11": {"total_count": 0, "jobs": []}}, expected_sha=self.sha)
        self.assertIsNone(r["measurement"]["observed_wall_seconds"])
        self.assertEqual(r["runs"][0]["completion_verification"], "NOT_VERIFIED")

    def test_tsv_has_status_and_no_fabricated_durations(self):
        a = run(12, "2026-10-10T10:00:00Z", "2026-10-10T10:00:15Z", conclusion="failure", event="pull_request")
        r = timing.build_report([a], {"12": {"total_count": 0, "jobs": []}}, expected_sha=self.sha)
        t = timing.to_tsv(r)
        self.assertIn("SUPPLEMENTARY_ZERO_JOB_FAILURE", t)
        self.assertIn("NOT_VERIFIED", t)


    def test_manual_audit_workflow_remains_opt_in_read_only(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/rhc131-performance-audit.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertIn("  actions: read", workflow)
        self.assertIn("  contents: read", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("\n  pull_request:", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("gh workflow run", workflow)
        self.assertIn("python3 -B tools/rhc131_timing.py", workflow)
        self.assertIn("rhc131-readonly-timing-", workflow)

    def test_existing_build_script_guards_remain_with_nonfatal_timing_markers(self):
        build = (Path(__file__).resolve().parents[1] / "build.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", build)
        self.assertEqual(build.count("rhc131_phase start "), 9)
        self.assertEqual(build.count("rhc131_phase end "), 9)
        for must in (
            "go test .", "go run ./tools/i18n_guard .", "go vet ./...",
            "go build -trimpath", "tools/patch_rsrc.py", "tools/validate_pe.py",
            "tools/validate_ui_recovery.py", "tools/validate_repair_safety.py",
            'sha256sum "$OUT/RazerHealthCenter.exe"',
        ):
            with self.subTest(guard=must):
                self.assertIn(must, build)

    def test_cli_offline_fixture_writes_schema_json_tsv_and_summary(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            fixture = folder / "fixture.json"
            fixture.write_text(json.dumps({
                "runs": [run(20, "2026-10-10T10:00:00Z", "2026-10-10T10:00:30Z")],
                "jobs_by_run": {"20": {"total_count": 1, "jobs": [
                    job(200, "2026-10-10T10:00:05Z", "2026-10-10T10:00:25Z")
                ]}},
            }), encoding="utf-8")
            output = folder / "output"
            self.assertEqual(timing.main([
                "--fixture", str(fixture), "--out-dir", str(output),
                "--issue", "131", "--version", "3.0.8.12",
                "--expected-sha", self.sha,
            ]), 0)
            doc = json.loads((output / "rhc131-timing.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["issue"], 131)
            self.assertEqual(doc["measurement"]["observed_wall_seconds"], 30)
            self.assertEqual(doc["measurement"]["sum_job_seconds"], 20)
            self.assertIn("run_id", (output / "rhc131-timing.tsv").read_text(encoding="utf-8"))
            self.assertIn("NONAUTHORITATIVE", (output / "rhc131-summary.txt").read_text(encoding="utf-8"))


    def test_gh_attempt_list_reuses_job_id_without_double_counting(self):
        from unittest.mock import patch
        first = job(501, "2026-10-10T10:00:05Z", "2026-10-10T10:00:10Z",
                    result="failure", attempt=1)
        stable = job(502, "2026-10-10T10:00:05Z", "2026-10-10T10:00:20Z",
                     attempt=1)
        retry = job(503, "2026-10-10T10:00:25Z", "2026-10-10T10:00:45Z",
                    attempt=2)
        evidence = {
            "actions/runs/60": run(60, "2026-10-10T10:00:00Z",
                                   "2026-10-10T10:00:48Z", attempt=2),
            "actions/runs/60/attempts/1/jobs?per_page=100&page=1":
                {"jobs": [first, stable]},
            "actions/runs/60/attempts/2/jobs?per_page=100&page=1":
                {"jobs": [{**stable, "run_attempt": 2}, retry]},
        }
        with patch.object(timing, "_api", side_effect=lambda _r, path: evidence[path]):
            sample = timing.collect("SaschaP1980/RazerHealthCenter", ["60"])
        unique = sample["jobs_by_run"]["60"]["jobs"]
        self.assertEqual(sample["jobs_by_run"]["60"]["total_count"], 3)
        self.assertEqual(sorted(x["id"] for x in unique), [501, 502, 503])
        self.assertEqual(next(x for x in unique if x["id"] == 502)["run_attempt"], 1)
        r = timing.build_report(sample["runs"], sample["jobs_by_run"], expected_sha=self.sha)
        self.assertEqual(r["measurement"]["sum_job_seconds"], 40)
        self.assertEqual(r["measurement"]["retry_job_seconds"], 5)


    def test_final_success_preserved_with_failed_previous_attempt(self):
        item = run(61, "2026-10-10T10:00:00Z",
                   "2026-10-10T10:00:48Z", attempt=2, conclusion="success")
        evidence = {"61": {"total_count": 2, "jobs": [
            job(610, "2026-10-10T10:00:05Z", "2026-10-10T10:00:10Z",
                result="failure", attempt=1),
            job(611, "2026-10-10T10:00:25Z", "2026-10-10T10:00:45Z",
                result="success", attempt=2),
        ]}}
        report = timing.build_report([item], evidence, expected_sha=self.sha)
        self.assertEqual(report["runs"][0]["conclusion"], "success")
        self.assertEqual(report["runs"][0]["classification"], "COMPLETED_WITH_HOSTED_SUCCESS")
        self.assertEqual(report["measurement"]["retry_job_seconds"], 5)
        self.assertEqual(report["measurement"]["successful_attempt_job_seconds"], 20)
        self.assertEqual(report["runs"][0]["jobs"][0]["conclusion"], "failure")


    def test_gh_attempt_listing_can_duplicate_unchanged_job_under_new_id(self):
        # Observed risk: a rerun-failed-jobs endpoint includes the earlier
        # successful Windows step window under a later attempt listing.
        from unittest.mock import patch
        one = job(701, "2026-10-10T10:00:05Z", "2026-10-10T10:00:25Z",
                  result="success", attempt=1)
        one["name"] = "rhc/infra/windows"
        reused = {**one, "id": 702, "run_attempt": 2}
        two = job(703, "2026-10-10T10:00:30Z", "2026-10-10T10:00:45Z",
                  result="success", attempt=2)
        two["name"] = "rhc/infra/linux"
        evidence = {
            "actions/runs/70": run(70, "2026-10-10T10:00:00Z",
                                   "2026-10-10T10:00:50Z", attempt=2),
            "actions/runs/70/attempts/1/jobs?per_page=100&page=1":
                {"jobs": [one]},
            "actions/runs/70/attempts/2/jobs?per_page=100&page=1":
                {"jobs": [reused, two]},
        }
        with patch.object(timing, "_api", side_effect=lambda _repo, path: evidence[path]):
            sample = timing.collect("SaschaP1980/RazerHealthCenter", ["70"])
        self.assertEqual(sample["jobs_by_run"]["70"]["total_count"], 2)
        self.assertEqual(sample["jobs_by_run"]["70"]["reused_attempt_job_listings"], 1)
        report = timing.build_report(sample["runs"], sample["jobs_by_run"],
                                     expected_sha=self.sha)
        self.assertEqual(report["measurement"]["sum_job_seconds"], 35)
        self.assertEqual(report["runs"][0]["reused_attempt_job_listings"], 1)


if __name__ == "__main__":
    unittest.main()
