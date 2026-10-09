"""RHC-98: fail-closed immutable retry of failed RHC-96 Candidate; one atomic PR."""
import copy
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_candidate_from_work as c

A, B, C, D = ("a"*40,"b"*40,"c"*40,"d"*40)
RUN_ID = "37979416751"
def run():
    return dict(id=int(RUN_ID), head_sha=D, event="workflow_dispatch",
                status="completed", conclusion="failure",
                name="RHC Reusable Interim Unsigned Release")
def job(prefix, verdict):
    return dict(name=prefix+" — actual",status="completed",conclusion=verdict)
def jobs():
    return [
        job("Exact-candidate double Linux PE/ZIP","success"),
        job("Actual native Windows PS5.1","success"),
        job("Stage single immutable ZIP/catalog","failure"),
        job("Independently verify exact release PR","skipped"),
    ]
def fixture():
    return dict(workBranch="work/RHC-99",mainSha=A,workSha=B,treeSha=C,
        compareStatus="ahead",behindBy=0,aheadBy=1,
        files=[dict(filename="model.go",status="modified"),
               dict(filename="CHANGELOG.md",status="modified")],
        mainVersion="3.0.8.7",workVersion="3.0.8.8",candidateExists=True,
        policy=dict(productionEnabled=False,distribution="repo-downloads",
                    signingDecision="unknown",rollbackVerified=False),
        statuses=[dict(context="development-completion/gate",state="success",
                       description="PASS main="+A,creator={"login":"github-actions[bot]"})],
        message="chore: retry\n\nRHC-Issue: 99\nRelease-Profile: version-only\n"
                "Development-Completion: requested\nRecovery-Original-Candidate: "+D+
                "\nRecovery-Original-Run: "+RUN_ID+"\nRecovery-Attempt: 1",
        retry=dict(allowed=True,originalSha=D,runId=RUN_ID,run=run(),jobs=jobs(),
                   version="3.0.8.8",originalVersion="3.0.8.8",
                   publicPreviousVersion="3.0.8.7",originalRefUnchanged=True,
                   retryRefExists=False,tagExists=False,archiveExists=False,
                   releaseRefExists=False))
class ImmutableRetry(unittest.TestCase):
    def test_new_ref_and_history_unmodified(self):
        p=c.validate_plan(fixture())
        self.assertEqual(p["branch"],"candidate/v3.0.8.8-retry1")
        self.assertEqual(p["retryOriginalSha"],D)
        self.assertEqual(p["retryRunId"],RUN_ID)
    def test_original_must_be_real_hosted_partial_failure(self):
        self.assertTrue(c.validate_failed_publisher(dict(run=run(),jobs=jobs()),D,RUN_ID))
        variants=[
            lambda e:e["run"].update(head_sha=B),
            lambda e:e["run"].update(conclusion="success"),
            lambda e:e["run"].update(conclusion="cancelled"),
            lambda e:e["run"].update(event="pull_request"),
            lambda e:e["run"].update(name="other workflow"),
            lambda e:e.update(jobs=[]),
            lambda e:e["jobs"][0].update(conclusion="skipped"),
            lambda e:e["jobs"][1].update(conclusion="failure"),
            lambda e:e["jobs"][2].update(conclusion="success"),
            lambda e:e["jobs"][3].update(conclusion="success"),
            lambda e:e["jobs"][3].update(status="queued")
        ]
        for mutation in variants:
            ev=dict(run=run(),jobs=jobs())
            mutation(ev)
            with self.subTest(change=str(mutation)),self.assertRaises(ValueError):
                c.validate_failed_publisher(ev,D,RUN_ID)
    def test_no_unsupported_retry_or_provenance_drift(self):
        changes=[
            lambda f:f.update(candidateExists=False),
            lambda f:f.update(retry=None),
            lambda f:f["retry"].update(originalRefUnchanged=False),
            lambda f:f["retry"].update(retryRefExists=True),
            lambda f:f["retry"].update(releaseRefExists=True),
            lambda f:f["retry"].update(archiveExists=True),
            lambda f:f["retry"].update(tagExists=True),
            lambda f:f["retry"].update(publicPreviousVersion="3.0.8.8"),
            lambda f:f["retry"].update(originalVersion="3.0.8.7"),
            lambda f:f.update(mainSha=D),
            lambda f:f.update(workSha="WRONG"),
            lambda f:f["statuses"][0].update(state="pending"),
            lambda f:f.update(message=f["message"].replace("Recovery-Attempt: 1","Recovery-Attempt: 2")),
            lambda f:f.update(message=f["message"]+"\nRecovery-Attempt: 1"),
            lambda f:f.update(message=f["message"].replace("Recovery-Original-Run: "+RUN_ID,
                                                   "Recovery-Original-Run: 37900000000"))
        ]
        for mutation in changes:
            f=fixture()
            mutation(f)
            with self.subTest(mutation=str(mutation)),self.assertRaises(ValueError):
                c.validate_plan(f)
    def test_unmarked_existing_candidate_remains_blocked(self):
        f=fixture();f["message"]="RHC-Issue: 99\nRelease-Profile: version-only\nDevelopment-Completion: requested"
        with self.assertRaises(ValueError):c.validate_plan(f)
    def test_new_candidate_and_publisher_require_exact_immutable_markers(self):
        entry=(ROOT/"tools/rhc_candidate_entry.py").read_text()
        publisher=(ROOT/"tools/rhc94_atomic_release.py").read_text()
        for marker in ("Recovery-Attempt","Recovery-Original-Candidate","Recovery-Original-Run"):
            self.assertIn(marker,entry)
        for check in ("-retry1","original frozen Candidate ref changed",
                      "validate_failed_publisher","retryAttempt"):
            self.assertIn(check,publisher)
    def test_postmerge_verifies_two_source_and_four_download_paths(self):
        post=(ROOT/".github/workflows/rhc-reusable-interim-postmerge.yml").read_text()
        for check in ('test "$SOURCE" = "$(git rev-parse "$STAGED_SHA^")"',
                      'test "$FIRST" = "$(git rev-parse "$SOURCE^")"',
                      'downloads/README.md',
                      "model.go",
                      "CHANGELOG.md",
                      'test "$(git rev-parse "$STAGED_SHA^{tree}")" = "$(git rev-parse "$MERGED_SHA^{tree}")"'):
            self.assertIn(check,post)
        self.assertNotIn('git merge-base --is-ancestor "$SOURCE" "$RELEASE_MAIN"',post)
    def test_prod_flag_invariant(self):
        import json
        policy=json.loads((ROOT/"config/rhc-release-policy.json").read_text())
        self.assertIs(policy["productionEnabled"],False)
        self.assertIs(policy["rollbackVerified"],False)
        self.assertEqual(policy["signingDecision"],"unknown")
if __name__=="__main__":unittest.main()
