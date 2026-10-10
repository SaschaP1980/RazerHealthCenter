"""RHC-116 transport-level nonpublishing end-to-end simulator.

Exercises the real gh-api transport, one POST, list lookup, guarded PATCH,
independent raw numbered GET and second CLI development gate; no live Issue.
"""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from rhc_issue_init import cli

BODY = "Development path: dev-path: work-branch — verified GitHub Issue initialization workflow"
LABELS = ("enhancement", "priority: high", "dev-ops", "dev-path: work-branch")


class Response:
    def __init__(self, payload):
        self.returncode = 0
        self.stdout = json.dumps(payload)
        self.stderr = ""


class LiveProtocol:
    def __init__(self, *, drop_priority=False):
        self.issue = None
        self.calls = []
        self.drop_priority = drop_priority

    def run(self, command, input=None, text=None, capture_output=None, timeout=None, check=None):
        assert command[:3] == ["gh", "api", "-X"]
        method, path = command[3], command[4]
        data = json.loads(input) if input else None
        self.calls.append((method, path, data))
        prefix = "repos/SaschaP1980/RazerHealthCenter"
        if (method, path) == ("POST", prefix + "/issues"):
            assert self.issue is None
            names = [n for n in data["labels"] if not (self.drop_priority and n == "priority: high")]
            self.issue = dict(number=116, title=data["title"], body=data["body"],
                              state="open", labels=[{"name": n} for n in names])
            return Response({"number": 116})
        if (method, path) == ("GET", prefix + "/issues?state=open&per_page=100&page=1"):
            return Response([self.issue] if self.issue else [])
        if (method, path) == ("GET", prefix + "/issues/116"):
            return Response(self.issue)
        if (method, path) == ("PATCH", prefix + "/issues/116"):
            assert self.issue is not None
            self.issue["title"] = data["title"]
            return Response(self.issue)
        raise AssertionError("Unexpected GitHub API interaction: " + str((method, path)))


class FullTransport(unittest.TestCase):
    def run_command(self, server, argv):
        result = io.StringIO()
        with patch("rhc_issue_init.subprocess.run", side_effect=server.run), contextlib.redirect_stdout(result):
            rc = cli(argv)
        return rc, result.getvalue()

    def test_full_two_phase_e2e_create_labels_rename_raw_get_and_development(self):
        server = LiveProtocol()
        with tempfile.TemporaryDirectory() as tmp:
            file = pathlib.Path(tmp) / "body.md"
            file.write_text(BODY, encoding="utf-8")
            args = ["init", "--repository", "SaschaP1980/RazerHealthCenter",
                    "--subject", "GitHub Issue initialization workflow", "--body-file", str(file),
                    "--nonce", "aabbccddeeff"]
            for label in LABELS:
                args.extend(["--label", label])
            rc, output = self.run_command(server, args)
        self.assertEqual(rc, 0, output)
        self.assertIn("RHC115_INITIALIZATION_VERIFIED=", output)
        self.assertEqual(server.issue["title"], "[RHC-116] GitHub Issue initialization workflow")
        self.assertEqual([call[0] for call in server.calls], ["POST", "GET", "GET", "PATCH", "GET"])
        self.assertEqual(server.calls[0][2]["labels"], list(LABELS))
        rc, output = self.run_command(server, ["verify", "--repository",
                   "SaschaP1980/RazerHealthCenter", "--issue", "116", "--for-development"])
        self.assertEqual(rc, 0, output)
        self.assertEqual(server.calls[-1][0], "GET")

    def test_dropped_create_time_priority_blocks_before_rename(self):
        server = LiveProtocol(drop_priority=True)
        with tempfile.TemporaryDirectory() as tmp:
            file = pathlib.Path(tmp) / "body.md"
            file.write_text(BODY, encoding="utf-8")
            args = ["init", "--repository", "SaschaP1980/RazerHealthCenter",
                    "--subject", "GitHub Issue initialization workflow", "--body-file", str(file),
                    "--nonce", "aabbccddeeff"]
            for label in LABELS:
                args.extend(["--label", label])
            rc, _ = self.run_command(server, args)
        self.assertEqual(rc, 2)
        self.assertEqual([c[0] for c in server.calls], ["POST", "GET", "GET"])
        self.assertEqual(server.issue["title"], "Initializing RHC Issue: GitHub Issue initialization workflow [init-aabbccddeeff]")

    def test_pending_label_state_may_exist_but_never_start_development(self):
        server = LiveProtocol()
        server.issue = dict(number=116,title="[RHC-116] GitHub Issue initialization workflow",
            body="Development path: PATH_DECISION_PENDING — awaiting owner decision on implementation scope",
            labels=[{"name": n} for n in ["enhancement","priority: high","dev-ops"]],
            state="open")
        rc, output = self.run_command(server, ["verify", "--repository",
                       "SaschaP1980/RazerHealthCenter", "--issue", "116", "--for-development"])
        self.assertEqual(rc, 2)
        self.assertEqual([c[0] for c in server.calls], ["GET"])


if __name__ == "__main__":
    unittest.main()
