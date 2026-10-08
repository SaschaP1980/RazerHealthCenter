"""Nonpublishing Candidate API orchestration: fully mocked network contract."""
import base64
import contextlib
import io
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import rhc_candidate_from_work as candidate

A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40
BASE = 'const (\n appVersion = "3.0.8.0"\n referenceVersion = "3.0.8.0"\n secret = 0\n)\n'
TARGET = BASE.replace('appVersion = "3.0.8.0"', 'appVersion = "3.0.8.1"').replace(
    'referenceVersion = "3.0.8.0"', 'referenceVersion = "3.0.8.1"')


def encoded(text):
    return {"encoding": "base64", "content": base64.b64encode(text.encode()).decode()}


class Server:
    def __init__(self):
        self.main_reads = 0
        self.candidate_created = False
        self.writes = []
        self.status_ok = True
        self.main_moved = False
        self.model_tampered = False
        self.fail_dispatch = False

    def api(self, method, path, payload=None, optional404=False):
        if method == "POST":
            self.writes.append((path, payload))
            if path == "/git/commits":
                assert payload["tree"] == C and payload["parents"] == [A]
                return {"sha": D}
            if path == "/git/refs":
                assert not self.candidate_created
                assert payload == {"ref": "refs/heads/candidate/v3.0.8.1", "sha": D}
                self.candidate_created = True
                return {}
            if path == "/actions/workflows/rhc-candidate-preflight.yml/dispatches":
                assert payload == {"ref": "candidate/v3.0.8.1"}
                if self.fail_dispatch:
                    raise ValueError("simulated dispatch failure")
                return {}
            raise AssertionError("unapproved GitHub POST: " + path)
        assert method == "GET"
        if path == "/branches/main":
            self.main_reads += 1
            return {"commit": {"sha": B if self.main_moved and self.main_reads > 1 else A}}
        if path == "/git/ref/heads/work/RHC-18":
            return {"object": {"sha": B}}
        if path == "/git/commits/" + B:
            return {"tree": {"sha": C},
                    "message": "Prepare hotfix\nRHC-Issue: 18\nRelease-Profile: version-only\nDevelopment-Completion: requested"}
        if path == "/compare/" + A + "..." + B:
            return {"status": "ahead", "ahead_by": 1, "behind_by": 0,
                    "files": [{"filename": "model.go", "status": "modified"},
                              {"filename": "CHANGELOG.md", "status": "added"}]}
        if path == "/commits/" + B + "/status":
            return {"statuses": [{"context": "development-completion/gate",
                "state": "success" if self.status_ok else "pending",
                "description": "PASS main=" + A,
                "creator": {"login": "github-actions[bot]"}}]}
        if path == "/contents/model.go?ref=" + A:
            return encoded(BASE)
        if path == "/contents/model.go?ref=" + B:
            return encoded(TARGET + ("\nmalicious=true\n" if self.model_tampered else ""))
        if path == "/git/ref/heads/candidate/v3.0.8.1":
            return {"object": {"sha": D}} if self.candidate_created else None
        if path == "/contents/config/rhc-release-policy.json?ref=" + A:
            return encoded(json.dumps({"productionEnabled": False,
                "distribution": "repo-downloads", "signingDecision": "unknown",
                "rollbackVerified": False}))
        if path == "/git/ref/heads/candidate/v3.0.8.1" and self.candidate_created:
            return {"object": {"sha": D}}
        if path == "/git/commits/" + D:
            return {"tree": {"sha": C}, "parents": [{"sha": A}]}
        raise AssertionError("unexpected GitHub GET: " + path)


class CandidateApiSimulation(unittest.TestCase):
    def execute(self, server):
        output = io.StringIO()
        with patch.object(candidate, "gh", side_effect=server.api), patch.dict(
                os.environ, {"WORK_BRANCH": "work/RHC-18", "WORK_SHA": B,
                             "GH_TOKEN": "ONLY-FIXTURE"}, clear=False
                ), contextlib.redirect_stdout(output):
            candidate.main()
        return output.getvalue()

    def test_success_creates_only_candidate_and_dispatches_pure_preflight(self):
        server = Server()
        output = self.execute(server)
        self.assertIn("CANDIDATE_STAGED_PREFLIGHT_DISPATCHED", output)
        self.assertEqual([path for path, _ in server.writes], [
            "/git/commits", "/git/refs",
            "/actions/workflows/rhc-candidate-preflight.yml/dispatches"])
        self.assertTrue(server.candidate_created)

    def test_missing_real_completion_or_tampered_model_never_writes(self):
        for scenario in ("status_ok", "model_tampered"):
            server = Server()
            setattr(server, scenario, False if scenario == "status_ok" else True)
            with self.subTest(scenario=scenario), self.assertRaises(ValueError):
                self.execute(server)
            self.assertEqual(server.writes, [])

    def test_main_advance_fails_before_mutation(self):
        server = Server()
        server.main_moved = True
        with self.assertRaises(ValueError):
            self.execute(server)
        self.assertEqual(server.writes, [])

    def test_preexisting_candidate_never_overwritten(self):
        server = Server()
        server.candidate_created = True
        with self.assertRaises(ValueError):
            self.execute(server)
        self.assertEqual(server.writes, [])

    def test_partial_dispatch_failure_is_not_reported_success_or_retried(self):
        server = Server()
        server.fail_dispatch = True
        with self.assertRaises(ValueError):
            self.execute(server)
        self.assertTrue(server.candidate_created)
        before = len(server.writes)
        with self.assertRaises(ValueError):
            self.execute(server)
        self.assertEqual(len(server.writes), before)


if __name__ == "__main__":
    unittest.main()
