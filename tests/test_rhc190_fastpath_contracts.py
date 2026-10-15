"""RHC-190: branchless fast Candidate and Work provenance are disjoint."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import rhc94_atomic_release as r

A, B, C, D = ("a"*40, "b"*40, "c"*40, "d"*40)

def good(ctx, state="success", actor="github-actions[bot]"):
    return {"context":ctx,"state":state,"creator":{"login":actor}}

def fixture():
    message = ("chore(RHC-200): candidate v3.0.8.24\n\n"
               "Main-SHA: "+A+"\nDevelopment-Path: fast\n"
               "RHC-Issue: 200\nRelease-Profile: version-only")
    return dict(candidate_sha=C, base_sha=A,
                candidate={"sha":C,"parents":[{"sha":A}],"tree":D,
                           "message":message},
                issue={"number":200,"state":"open","labels":[{"name":"dev-path: fast"}]},
                statuses=[good(x) for x in r.CONTEXTS], current_main=A,
                previous_version="3.0.8.23", version="3.0.8.24",
                changed_paths=["model.go","CHANGELOG.md"])

class FastPathQualification(unittest.TestCase):
    def test_exact_fast_patch_hotfix(self):
        q=r.qualify_fast_candidate(**fixture())
        self.assertEqual(q["result"],"PASS")
        self.assertEqual(q["developmentPath"],"fast")
        self.assertIsNone(q["workSha"])
    def test_major_minor_cannot_skip_work(self):
        for previous, new in [("3.0.8.23","3.1.0.0"),
                              ("3.0.8.23","4.0.0.0")]:
            f=fixture()
            f["previous_version"], f["version"]=previous,new
            with self.subTest(new=new),self.assertRaisesRegex(ValueError,"Work-Branch"):
                r.qualify_fast_candidate(**f)
    def test_stale_wrong_issue_and_status_block(self):
        changes=[
            lambda f:f.update(current_main=B),
            lambda f:f["candidate"].update(parents=[{"sha":B}]),
            lambda f:f["candidate"].update(message=f["candidate"]["message"]+
                                            "\nWork-SHA: "+B),
            lambda f:f["candidate"].update(message=f["candidate"]["message"]+
                                            "\nDevelopment-Path: fast"),
            lambda f:f["candidate"].update(message=f["candidate"]["message"].replace(
                                            "Development-Path: fast","Development-Path: work")),
            lambda f:f["issue"].update(labels=[{"name":"dev-path: work-branch"}]),
            lambda f:f["issue"].update(state="closed"),
            lambda f:f["statuses"][0].update(state="failure"),
            lambda f:f["statuses"][1]["creator"].update(login="attacker"),
            lambda f:f.update(changed_paths=["model.go","CHANGELOG.md","evil.exe"]),
            lambda f:f.update(version="3.0.8.23"),
        ]
        for change in changes:
            f=fixture();change(f)
            with self.subTest(change=change),self.assertRaises(ValueError):
                r.qualify_fast_candidate(**f)
    def test_fast_stage_requires_exact_pr_provenance(self):
        q=r.qualify_fast_candidate(**fixture())
        v="3.0.8.24"
        p={"state":"open","draft":False,"merged_at":None,"headSha":D,
           "baseSha":A,"headRef":"release/v"+v,"title":"[RHC-200] interim",
           "body":"Refs #200; sourceSha "+C+"; Development-Path fast"}
        stage={"sha":D,"parents":[{"sha":C}],"message":"stage\nRHC-Issue: 200"}
        paths=list(r.PUBLISH_PATHS)+["downloads/RazerHealthCenter-Portable-v"+v+".zip"]
        self.assertEqual(r.qualify_stage(q,stage,p,"release/v"+v,v,paths)["result"],"PASS")
        p["body"]=p["body"].replace("Development-Path fast","Work-SHA "+B)
        with self.assertRaises(ValueError):
            r.qualify_stage(q,stage,p,"release/v"+v,v,paths)
    def test_work_provenance_still_uses_completion(self):
        from test_rhc94_atomic_release_contracts import fixture as work_fixture
        q=r.qualify_candidate(**work_fixture())
        self.assertEqual(q["developmentPath"],"work")
        self.assertEqual(q["workSha"],B)

class PublisherWiring(unittest.TestCase):
    def test_fast_and_work_branches_fail_closed(self):
        wf=(pathlib.Path(__file__).resolve().parents[1]/
            ".github/workflows/rhc-reusable-interim-release.yml").read_text()
        self.assertIn("Development-Path: fast",wf)
        self.assertIn("PROVENANCE='Development-Path fast'",wf)
        self.assertIn('if [ -n "$WORK_SHA" ]; then',wf)
        self.assertIn('test "$(git ls-remote origin "refs/heads/$WORK_REF" | cut -f1)" = "$WORK_SHA"',wf)
        self.assertIn("RHC102_HOSTED_POSTRELEASE_THREE_JOB_GATE=PASS",wf)
        self.assertIn("RHC190_CANDIDATE_REAPER=PASS",wf)

if __name__=="__main__":
    unittest.main()
