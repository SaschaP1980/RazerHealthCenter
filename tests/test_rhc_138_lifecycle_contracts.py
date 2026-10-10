"""RHC-138: real-evidence owner-to-close timing contracts (test-first)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rhc138_lifecycle as life


BASE = "2026-10-10T18:56:57Z"
END = "2026-10-10T19:13:28Z"


def event(kind, stamp, *, issue=129, sha="a" * 40, source="github",
          entity="129", status="success", version="3.0.8.12", **extra):
    fields = dict(event=kind, at=stamp, issue=issue, sha=sha, source=source,
                  evidence_id=entity, status=status, version=version)
    fields.update(extra)
    return fields


class LifecycleContracts(unittest.TestCase):
    def test_hist_129_observed_spans_are_not_summed_when_overlapping(self):
        events = [
            event("issue_created", BASE),
            event("first_work_ci_created", "2026-10-10T18:59:12Z"),
            event("development_completion_green", "2026-10-10T19:02:36Z"),
            event("candidate_started", "2026-10-10T19:02:37Z"),
            event("publisher_started", "2026-10-10T19:04:18Z"),
            event("candidate_green", "2026-10-10T19:04:22Z"),
            event("publisher_green", "2026-10-10T19:08:12Z"),
            event("issue_closed", END),
        ]
        r = life.build_report(events, issue=129)
        d = r["interval_seconds"]
        self.assertEqual(d["issue_to_first_work_ci"], 135)
        self.assertEqual(d["work_ci_to_development_completion"], 204)
        self.assertEqual(d["publisher_to_issue_close"], 316)
        self.assertEqual(d["issue_to_issue_close"], 991)
        self.assertIsNone(d["owner_request_to_final_message"])
        self.assertEqual(r["measurement"]["exact_causal_critical_path_seconds"], None)
        self.assertIn("candidate_publisher_overlap", r["observations"])

    def test_no_user_request_timestamp_means_not_verified_not_zero(self):
        r = life.build_report([event("issue_created", BASE),
                               event("issue_closed", END, entity="129-final-close")], issue=129)
        self.assertIsNone(r["interval_seconds"]["owner_request_to_final_message"])
        self.assertEqual(r["measurement"]["owner_span_verification"], "NOT_VERIFIED")

    def test_user_request_and_final_message_require_attested_event_sources(self):
        e = [event("owner_authorized", "2026-10-10T18:55:00Z",
                   source="unverified_assistant_guess"),
             event("issue_created", BASE),
             event("issue_closed", END),
             event("final_user_notification", "2026-10-10T19:14:00Z",
                   source="unverified_assistant_guess")]
        r = life.build_report(e, issue=129)
        self.assertIsNone(r["interval_seconds"]["owner_request_to_final_message"])
        self.assertEqual(len(r["untrusted_events"]), 2)

    def test_genuine_attested_owner_boundaries_are_measurable(self):
        e = [event("owner_authorized", "2026-10-10T18:55:00Z",
                   source="attested_user_message", evidence_id="chat-message-23"),
             event("issue_created", BASE), event("issue_closed", END),
             event("final_user_notification", "2026-10-10T19:14:00Z",
                   source="attested_outgoing_message", evidence_id="message-44")]
        r = life.build_report(e, issue=129)
        self.assertEqual(r["interval_seconds"]["owner_request_to_final_message"], 1140)
        self.assertEqual(r["measurement"]["owner_span_verification"], "VERIFIED")

    def test_wrong_issue_or_sha_never_enters_measured_spans(self):
        e = [event("issue_created", BASE), event("first_work_ci_created",
              "2026-10-10T18:58:00Z", sha="b" * 40),
             event("issue_closed", END, issue=130)]
        r = life.build_report(e, issue=129, expected_sha="a" * 40)
        self.assertIsNone(r["interval_seconds"]["issue_to_first_work_ci"])
        self.assertIsNone(r["interval_seconds"]["issue_to_issue_close"])
        self.assertEqual(len(r["excluded_events"]), 2)

    def test_retry_failure_is_not_swallowed_or_rewritten_green(self):
        e = [event("issue_created", BASE),
             event("work_attempt_failed", "2026-10-10T19:00:00Z",
                   status="failure", attempt=1, entity="38077977604/1"),
             event("work_retry_succeeded", "2026-10-10T19:02:14Z",
                   attempt=2, entity="38077977604/2")]
        r = life.build_report(e, issue=129)
        self.assertEqual(r["retries"][0]["status"], "failure")
        self.assertEqual(r["measurement"]["retry_failure_count"], 1)
        self.assertEqual(r["retries"][0]["attempt"], 1)

    def test_auto_close_and_reopen_are_visible_not_misclassified(self):
        e = [event("issue_created", BASE),
             event("issue_closed", "2026-10-10T19:07:15Z", entity="129-early-close"),
             event("issue_reopened", "2026-10-10T19:08:00Z"),
             event("issue_closed", END)]
        r = life.build_report(e, issue=129)
        self.assertEqual(r["interval_seconds"]["issue_to_issue_close"], 991)
        self.assertEqual(r["measurement"]["premature_close_count"], 1)

    def test_zero_job_optional_failure_is_not_required_job_green(self):
        e = [event("supplemental_pr_zero_job", "2026-10-10T19:07:14Z",
                   status="failure", job_count=0, entity="38078506084"),
             event("required_downloads_gate", "2026-10-10T19:07:05Z",
                   status="success", job_count=0)]
        r = life.build_report(e, issue=129)
        self.assertEqual(r["measurement"]["supplemental_zero_job_failures"], 1)
        self.assertIn("REQUIRED_JOB_COUNT_UNVERIFIED", r["observations"])

    def test_negative_clock_and_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            life.parse_time("2026-10-10T19:00:00")
        with self.assertRaises(ValueError):
            life.build_report([event("issue_created", END),
                               event("issue_closed", BASE)], issue=129)

    def test_unknown_but_valid_job_gaps_are_not_called_operator_time(self):
        r = life.build_report([event("publisher_green", "2026-10-10T19:08:12Z"),
                               event("issue_closed", END)], issue=129)
        self.assertEqual(r["interval_seconds"]["publisher_to_issue_close"], 316)
        self.assertEqual(r["measurement"]["administrative_causal_time_seconds"], None)

    def test_duplicate_event_ids_are_deduplicated_and_conflicts_block(self):
        a = event("issue_created", BASE, entity="GH:issue129")
        r = life.build_report([a, dict(a)], issue=129)
        self.assertEqual(r["measurement"]["unique_event_count"], 1)
        with self.assertRaises(ValueError):
            life.build_report([a, dict(a, at=END)], issue=129)

    def test_cli_emits_json_tsv_and_human_summary_without_secret(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            input_file = base / "events.json"
            input_file.write_text(json.dumps({"events": [
                event("issue_created", BASE), event("issue_closed", END)
            ], "issue": 129}), encoding="utf-8")
            out = base / "out"
            self.assertEqual(life.main(["--fixture", str(input_file),
                                        "--out-dir", str(out)]), 0)
            obj = json.loads((out / "rhc138-lifecycle.json").read_text())
            self.assertEqual(obj["interval_seconds"]["issue_to_issue_close"], 991)
            self.assertIn("NOT_VERIFIED", (out / "rhc138-summary.txt").read_text())
            self.assertTrue((out / "rhc138-lifecycle.tsv").exists())


if __name__ == "__main__":
    unittest.main()
