"""RHC-162 RED-first contract for nonpublishing guarded Publisher -> closure dispatch.

Security rules: token-safe explicit workflow_dispatch after 3-job RHC102 PASS;
the closure must wait for the actual Publisher terminal success and reject all
untrusted IDs, stale SHAs, failed or unfinished publisher runs without writes.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc158_release_closure as rc

SOURCE = "a" * 40


class Clock:
    def __init__(self):
        self.seconds = 0.0

    def monotonic(self):
        return self.seconds

    def sleep(self, duration):
        self.seconds += duration


def publisher(status="completed", conclusion="success", **overrides):
    result = {
        "id": 901, "name": "RHC Reusable Interim Unsigned Release",
        "head_sha": SOURCE, "head_branch": "candidate/v3.0.8.17",
        "actor": {"login": "github-actions[bot]"},
        "event": "workflow_dispatch", "run_attempt": 1,
        "status": status, "conclusion": conclusion,
    }
    result.update(overrides)
    return result


class Gateway:
    def __init__(self, *states):
        self.states = list(states)
        self.seen = 0

    def get_run(self, run_id):
        self.seen += 1
        return self.states[min(self.seen - 1, len(self.states) - 1)]


class DispatchContract(unittest.TestCase):
    def test_publisher_dispatches_only_after_full_postrelease_success(self):
        text = (ROOT / ".github/workflows/rhc-reusable-interim-release.yml").read_text()
        verified = text.index("RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS")
        succeeded = text.index("RHC_REUSABLE_INTERIM_RELEASE_SUCCESS=PASS")
        dispatched = text.index("gh workflow run rhc158-release-closure.yml --ref main")
        self.assertLess(verified, succeeded)
        self.assertLess(succeeded, dispatched)
        self.assertIn('-f publisher_run_id="$GITHUB_RUN_ID"', text[dispatched:])
        self.assertIn('-f expected_source_sha="$SOURCE_SHA"', text[dispatched:])
        self.assertEqual(text.count("gh workflow run rhc158-release-closure.yml"), 1)
        self.assertIn("actions: write", text)

    def test_closure_dispatch_inputs_are_restricted_and_workflow_run_retained(self):
        text = (ROOT / ".github/workflows/rhc158-release-closure.yml").read_text()
        self.assertIn("workflow_run:", text)
        self.assertIn("types: [completed]", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("publisher_run_id:", text)
        self.assertIn("expected_source_sha:", text)
        self.assertIn("github.actor == 'github-actions[bot]'", text)
        self.assertIn("--wait-for-publisher", text)
        self.assertIn("--expected-source-sha", text)
        self.assertIn("issues: write", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("gh pr merge", text)
        self.assertNotIn("productionEnabled=true", text)

    def test_bounded_poll_requires_actual_publisher_terminal_success(self):
        clock = Clock()
        gateway = Gateway(publisher("in_progress", None),
                          publisher("queued", None),
                          publisher("completed", "success"))
        verified = rc.wait_for_publisher(
            gateway, 901, SOURCE, timeout_seconds=30, poll_seconds=3,
            monotonic=clock.monotonic, sleep=clock.sleep)
        self.assertEqual(verified["conclusion"], "success")
        self.assertEqual(gateway.seen, 3)
        self.assertEqual(clock.seconds, 6)

    def test_untrusted_terminal_or_mismatched_run_never_qualifies(self):
        corrupt = [
            publisher("completed", "failure"),
            publisher("completed", "cancelled"),
            publisher("completed", "skipped"),
            publisher("completed", "success", id=902),
            publisher("completed", "success", head_sha="f" * 40),
            publisher("completed", "success", event="pull_request"),
            publisher("completed", "success", head_branch="work/RHC-162"),
            publisher("completed", "success", name="Fake Workflow"),
            publisher("completed", "success", run_attempt=0),
            publisher("completed", "success", actor={"login": "untrusted"}),
        ]
        for item in corrupt:
            with self.subTest(item=item):
                clock = Clock()
                with self.assertRaises(ValueError):
                    rc.wait_for_publisher(
                        Gateway(item), 901, SOURCE, timeout_seconds=12,
                        poll_seconds=3, monotonic=clock.monotonic, sleep=clock.sleep)

    def test_running_forever_times_out_without_acceptance(self):
        clock = Clock()
        gateway = Gateway(publisher("in_progress", None))
        with self.assertRaises(ValueError):
            rc.wait_for_publisher(gateway, 901, SOURCE,
                timeout_seconds=9, poll_seconds=3,
                monotonic=clock.monotonic, sleep=clock.sleep)
        self.assertLessEqual(clock.seconds, 12)

    def test_wait_has_to_precede_any_closure_audit_or_write(self):
        fake = Gateway(publisher("completed", "success"))
        with patch.object(rc, "wait_for_publisher", return_value=publisher()) as wait, \
             patch.object(rc, "collect_release_proof", side_effect=ValueError("STOP")) as collect:
            with self.assertRaises(ValueError):
                rc.close_release(fake, 901, apply=True,
                    expected_source_sha=SOURCE, wait=True)
        wait.assert_called_once()
        collect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
