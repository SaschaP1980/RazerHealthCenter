"""RHC-110: adversarial pure controller, trusted dispatch and 3-job contracts."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_postrelease_recheck as r

S = {key: key * 40 for key in "abcdef"}
ZIP = "9" * 64
VERSION = "3.0.8.9"
REPO = "SaschaP1980/RazerHealthCenter"
EXPECTED_JOBS = (
    "Independently GET HTTPS public ZIP and exact release graph",
    "Independently reverify released EXE and native PS5.1 Razer safety",
    "Conclude only after independent HTTPS AND native Windows success",
)

def jobs(names, result="success"):
    return [{"name": n, "status": "completed", "conclusion": result} for n in names]

def valid_snapshot():
    latest = dict(version=VERSION, sourceSha=S["c"], tag="v" + VERSION,
                  file="RazerHealthCenter-Portable-v" + VERSION + ".zip",
                  sha256=ZIP, size=8619985)
    return {
        "repository": REPO, "liveMainSha": S["e"], "checkoutSha": S["e"],
        "event": "workflow_run",
        "triggerRun": dict(name="RHC Verified Merged-Branch Cleanup",
                           event="pull_request", head_sha=S["f"],
                           head_branch="work/RHC-110", status="completed",
                           conclusion="success", jobs=jobs(["Delete only the verified and unchanged merged PR head"])),
        "release": dict(verified=True, mainSha=S["e"], mergeSha=S["d"],
                        sourceSha=S["c"], version=VERSION,
                        tagSha=S["c"], archiveSha256=ZIP,
                        archiveSize=8619985, latest=latest,
                        historyHead=copy.deepcopy(latest),
                        sinceReleasePaths=["tests/test_rhc102_wiring_contracts.py",
                          "tools/rhc_postrelease_recheck.py",
                          "tests/test_rhc110_postrelease_recheck_contracts.py",
                          ".github/workflows/rhc-postrelease-recheck.yml"]),
        "releasePr": dict(number=107, merged=True, state="closed",
                          baseRef="main", headRef="release/v" + VERSION,
                          mergeSha=S["d"], stagedSha=S["b"]),
        "correctionPr": dict(number=110, merged=True, state="closed",
                body="Refs #110", headSha=S["f"], baseSha=S["a"],
                mergeSha=S["e"], baseRef="main", headRef="work/RHC-110",
                headRepo=REPO, issue=110, issueExists=True,
                mergeParents=[S["a"], S["f"]], treeMatchesHead=True,
                files=["tools/rhc_postrelease_recheck.py",
                       "tests/test_rhc110_postrelease_recheck_contracts.py",
                       ".github/workflows/rhc-postrelease-recheck.yml"],
                reviews=[dict(state="COMMENTED", commit_id=S["f"],
                              login="SaschaP1980")]),
        "qualification": dict(id=100, name="RHC Infrastructure Qualification (nonpublishing)",
                              event="push", head_sha=S["f"], head_branch="work/RHC-110",
                              status="completed", conclusion="success",
                              jobs=jobs(["rhc/infra/linux", "rhc/infra/windows",
                                         "rhc/infra/artifact-node24"])),
        "priorPostrelease": dict(id=200, event="workflow_dispatch",
                head_sha=S["d"], status="completed", conclusion="failure",
                display_title="RHC POSTRELEASE v" + VERSION + " main:" + S["d"],
                jobs=[dict(name=EXPECTED_JOBS[0], status="completed", conclusion="failure"),
                      dict(name=EXPECTED_JOBS[1], status="completed", conclusion="success"),
                      dict(name=EXPECTED_JOBS[2], status="completed", conclusion="failure")]),
        "existingCurrentRuns": [], "publisherActive": False,
    }

class ControllerContracts(unittest.TestCase):
    def test_read_only_eligible_historical_corrected_release(self):
        obj = r.validate_plan(valid_snapshot())
        self.assertEqual(obj["status"], "ELIGIBLE")
        self.assertEqual(obj["expected_main_sha"], S["e"])
        self.assertEqual(obj["expected_source_sha"], S["c"])
        self.assertEqual(obj["version"], VERSION)
        self.assertEqual(obj["expected_release_pr"], "107")
        self.assertEqual(obj["original_failed_run"], 200)
        self.assertEqual(obj["corrective_pr"], 110)

    def test_scheduled_fallback_needs_same_real_evidence(self):
        x = valid_snapshot()
        x["event"] = "schedule"
        self.assertEqual(r.validate_plan(x)["status"], "ELIGIBLE")
        x["triggerRun"]["conclusion"] = "failure"
        with self.assertRaises(ValueError):
            r.validate_plan(x)

    def test_hostile_incomplete_or_stale_proof_fails_closed(self):
        mutations = [
            lambda x: x.update(liveMainSha=S["a"]),
            lambda x: x.update(checkoutSha=S["a"]),
            lambda x: x["release"].update(verified=False),
            lambda x: x["release"].update(sourceSha=S["a"]),
            lambda x: x["release"].update(tagSha=S["a"]),
            lambda x: x["release"].update(archiveSha256="0" * 64),
            lambda x: x["release"].update(archiveSize=123),
            lambda x: x["release"]["historyHead"].update(version="3.0.8.8"),
            lambda x: x["release"]["latest"].update(version="3.0.8.8"),
            lambda x: x["release"].update(sinceReleasePaths=["model.go"]),
            lambda x: x["release"].update(sinceReleasePaths=["downloads/latest.json"]),
            lambda x: x["release"].update(sinceReleasePaths=["config/rhc-release-policy.json"]),
            lambda x: x["releasePr"].update(merged=False),
            lambda x: x["releasePr"].update(mergeSha=S["a"]),
            lambda x: x["releasePr"].update(headRef="release/evil"),
            lambda x: x["correctionPr"].update(merged=False),
            lambda x: x["correctionPr"].update(body="no linked issue"),
            lambda x: x["correctionPr"].update(issueExists=False),
            lambda x: x["correctionPr"].update(mergeSha=S["a"]),
            lambda x: x["correctionPr"].update(headRepo="other/repo"),
            lambda x: x["correctionPr"].update(files=["model.go"]),
            lambda x: x["correctionPr"].update(files=["downloads/latest.json"]),
            lambda x: x["correctionPr"].update(files=[".github/workflows/rhc-reusable-interim-release.yml"]),
            lambda x: x["correctionPr"].update(files=["docs/RELEASE_PROCESS.md"]),
            lambda x: x["correctionPr"].update(treeMatchesHead=False),
            lambda x: x["correctionPr"].update(mergeParents=[S["a"], S["b"]]),
            lambda x: x["correctionPr"].update(reviews=[]),
            lambda x: x["correctionPr"]["reviews"][0].update(commit_id=S["a"]),
            lambda x: x["correctionPr"]["reviews"][0].update(state="DISMISSED"),
            lambda x: x["qualification"].update(head_sha=S["a"]),
            lambda x: x["qualification"].update(conclusion="failure"),
            lambda x: x["qualification"].update(event="pull_request"),
            lambda x: x["qualification"].update(jobs=[]),
            lambda x: x["qualification"]["jobs"][1].update(conclusion="skipped"),
            lambda x: x["qualification"]["jobs"][1].update(status="queued"),
            lambda x: x["priorPostrelease"].update(conclusion="success"),
            lambda x: x["priorPostrelease"].update(status="in_progress"),
            lambda x: x["priorPostrelease"].update(head_sha=S["a"]),
            lambda x: x["priorPostrelease"].update(jobs=[]),
            lambda x: x["priorPostrelease"].update(event="pull_request"),
            lambda x: x.update(publisherActive=True),
            lambda x: x.update(existingCurrentRuns=[{"id":999, "status":"completed", "conclusion":"failure"}]),
            lambda x: x["triggerRun"].update(conclusion="skipped"),
            lambda x: x["triggerRun"].update(head_sha=S["a"]),
            lambda x: x["triggerRun"].update(jobs=[]),
            lambda x: x.update(repository="other/repo"),
        ]
        for i, alter in enumerate(mutations):
            obj = valid_snapshot()
            alter(obj)
            with self.subTest(index=i), self.assertRaises(ValueError):
                r.validate_plan(obj)

    def test_verify_three_actual_completed_independent_jobs(self):
        data = jobs(EXPECTED_JOBS)
        self.assertTrue(r.verify_postrelease_jobs(data))
        for bad in [
            [], data[:2], data + [data[0]],
            [data[0], data[0], data[2]],
            [dict(data[0], conclusion="failure"), *data[1:]],
            [data[0], dict(data[1], status="queued"), data[2]],
            [data[0], data[1], dict(data[2], conclusion="skipped")],
        ]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                r.verify_postrelease_jobs(bad)

    def test_workflow_has_trusted_nonpublishing_and_autonomous_triggers(self):
        s = (ROOT / ".github/workflows/rhc-postrelease-recheck.yml").read_text()
        self.assertIn("workflow_run:", s)
        self.assertIn("RHC Verified Merged-Branch Cleanup", s)
        self.assertIn("schedule:", s)
        self.assertIn("workflow_dispatch:", s)
        self.assertIn("actions: write", s)
        self.assertIn("contents: read", s)
        self.assertNotIn("contents: write", s)
        self.assertNotIn("pull-requests: write", s)
        self.assertIn("cancel-in-progress: false", s)
        self.assertIn("rhc_postrelease_recheck.py", s)
        self.assertNotIn("rhc-reusable-interim-release.yml --ref", s)
        self.assertNotIn("RHC_PUBLICATION=PASS", s)

if __name__ == "__main__":
    unittest.main()
