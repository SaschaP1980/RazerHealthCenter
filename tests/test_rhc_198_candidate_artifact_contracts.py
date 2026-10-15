"""RHC-198 RED -> GREEN: guarded Candidate PE provenance reuse, no unsafe skips."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rhc190_candidate_artifact import ArtifactBlocked, emit_evidence, verify_evidence

SHA = "a" * 40
TREE = "b" * 40
VERSION = "3.0.8.25"
REPO = "SaschaP1980/RazerHealthCenter"
JOBS = (
    "Linux Candidate exact-main and deterministic Go artifacts",
    "Windows native PowerShell 5.1 and Go Candidate safety",
    "Exact-SHA Candidate qualification (nonpublishing)",
)


class CandidateArtifactContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "source" / "RazerHealthCenter.exe"
        self.src.parent.mkdir()
        self.src.write_bytes(b"MZ" + b"CANONICAL-REAL-PE-DUMMY-FOR-UNIT-TEST")
        self.bundle = self.root / "bundle"
        self.meta = emit_evidence(
            self.src, self.bundle, source_sha=SHA, tree_sha=TREE,
            version=VERSION, repository=REPO, run_id=12345, run_attempt=1,
        )
        self.pe = self.bundle / "RazerHealthCenter.exe"
        self.run = dict(id=12345, name="RHC Candidate Preflight (nonpublishing)",
                        path=".github/workflows/rhc-candidate-preflight.yml",
                        event="workflow_dispatch", status="completed",
                        conclusion="success", head_sha=SHA,
                        head_branch="candidate/v" + VERSION,
                        run_attempt=1, head_repository=dict(full_name=REPO))
        self.jobs = dict(total_count=3, jobs=[
            dict(id=n, name=name, status="completed", conclusion="success")
            for n, name in enumerate(JOBS, start=1)])

    def check(self, meta=None, run=None, jobs=None, pe=None, **expected):
        return verify_evidence(
            self.meta if meta is None else meta,
            self.run if run is None else run,
            self.jobs if jobs is None else jobs,
            self.pe if pe is None else pe,
            source_sha=expected.get("source_sha", SHA),
            tree_sha=expected.get("tree_sha", TREE),
            version=expected.get("version", VERSION),
            repository=expected.get("repository", REPO),
        )

    def test_real_binary_bytes_and_candidate_run_success(self):
        self.assertEqual(self.check()["sourceSha"], SHA)
        self.assertEqual(hashlib.sha256(self.pe.read_bytes()).hexdigest(),
                         self.meta["exeSha256"])
        self.assertEqual(self.meta["runId"], 12345)
        self.assertEqual(self.meta["runAttempt"], 1)

    def test_producer_never_overwrites_existing_immutable_evidence(self):
        with self.assertRaises(ArtifactBlocked):
            emit_evidence(
                self.src, self.bundle, source_sha=SHA, tree_sha=TREE,
                version=VERSION, repository=REPO, run_id=12345, run_attempt=1,
            )
    def test_bad_meta_provenance_fails_closed(self):
        for key, corrupt in (
            ("sourceSha", "f" * 40), ("treeSha", "f" * 40),
            ("version", "3.0.8.24"), ("repository", "evil/fork"),
            ("runId", 9), ("runAttempt", 2), ("doublePeVerified", False),
            ("zipReproducible", False), ("schema", "wrong"),
            ("exeSha256", "0" * 64), ("exeSize", 0),
        ):
            with self.subTest(key=key), self.assertRaises(ArtifactBlocked):
                data = dict(self.meta, **{key: corrupt})
                self.check(meta=data)

    def test_tampered_binary_and_invalid_executable_fails(self):
        self.pe.write_bytes(self.pe.read_bytes() + b"x")
        with self.assertRaises(ArtifactBlocked):
            self.check()
        self.pe.write_bytes(b"not PE")
        with self.assertRaises(ArtifactBlocked):
            self.check()

    def test_wrong_run_identity_status_or_attempt_fails(self):
        for change in (
            dict(id=222), dict(name="ordinary workflow"),
            dict(path=".github/workflows/untrusted.yml"),
            dict(event="pull_request"), dict(status="queued"),
            dict(status="completed", conclusion="failure"),
            dict(conclusion="skipped"), dict(head_sha="f" * 40),
            dict(head_branch="candidate/v3.0.8.24"),
            dict(run_attempt=2), dict(head_repository=dict(full_name="fork/untrusted")),
        ):
            with self.subTest(change=change), self.assertRaises(ArtifactBlocked):
                self.check(run=dict(self.run, **change))

    def test_no_zero_job_fake_green_or_missing_os_proof(self):
        for invalid in (
            dict(total_count=0,jobs=[]),
            dict(total_count=2,jobs=self.jobs["jobs"][:2]),
            dict(total_count=3,jobs=self.jobs["jobs"][:2]),
            dict(total_count=4,jobs=self.jobs["jobs"] * 2),
        ):
            with self.subTest(invalid=invalid["total_count"]), self.assertRaises(ArtifactBlocked):
                self.check(jobs=invalid)
        for i in range(3):
            for bad in ("failure", "skipped", None):
                new = copy.deepcopy(self.jobs)
                new["jobs"][i]["conclusion"] = bad
                with self.subTest(i=i,bad=bad), self.assertRaises(ArtifactBlocked):
                    self.check(jobs=new)

    def test_duplicate_hosted_job_or_wrong_name_denied(self):
        new = copy.deepcopy(self.jobs)
        new["jobs"][2]["name"] = new["jobs"][0]["name"]
        with self.assertRaises(ArtifactBlocked):
            self.check(jobs=new)

    def test_read_only_exact_source_and_bad_sha_rejected(self):
        for kwargs in (dict(source_sha="e"*40),dict(tree_sha="d"*40),
                       dict(version="3.0.8.26"),dict(repository="bad/repo")):
            with self.subTest(kwargs=kwargs), self.assertRaises(ArtifactBlocked):
                self.check(**kwargs)

    def test_candidate_and_publisher_workflow_wiring(self):
        candidate = (ROOT / ".github/workflows/rhc-candidate-preflight.yml").read_text()
        publisher = (ROOT / ".github/workflows/rhc-reusable-interim-release.yml").read_text()
        self.assertIn("rhc190_candidate_artifact.py emit", candidate)
        self.assertIn("RHC190-CANDIDATE-PE-", candidate)
        self.assertIn("rhc190_candidate_artifact.py verify", publisher)
        self.assertIn("gh run download", publisher)
        self.assertIn("actions: read", publisher)
        self.assertNotIn('bash build.sh "$RUNNER_TEMP/build1"', publisher)
        self.assertNotIn('bash build.sh "$RUNNER_TEMP/build2"', publisher)
        self.assertIn("go test ./...", candidate)
        self.assertIn("go test ./...", publisher)
        self.assertIn("rhc-reusable-stage", publisher)
        self.assertIn("rhc-postrelease-verification.yml", publisher)


if __name__ == "__main__":
    unittest.main()
