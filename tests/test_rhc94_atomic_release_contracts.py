"""RHC-94: source+downloads must be one fail-closed atomic PR."""
import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import rhc94_atomic_release as r

A, B, C, D = ("a"*40, "b"*40, "c"*40, "d"*40)
def status(ctx, state="success", actor="github-actions[bot]", description=""):
    return dict(context=ctx,state=state,creator=dict(login=actor),description=description)
def fixture():
    cm="candidate\n\nWork-SHA: "+B+"\nMain-SHA: "+A+"\nRHC-Issue: 94\nRelease-Profile: version-only"
    wm="change\n\nRHC-Issue: 94\nRelease-Profile: version-only\nDevelopment-Completion: requested"
    return dict(candidate_sha=C,base_sha=A,
        candidate=dict(sha=C,parents=[dict(sha=A)],tree=D,message=cm),
        work=dict(sha=B,parents=[dict(sha=A)],tree=D,message=wm),
        issue=dict(number=94,state="open",pull_request=None),
        statuses=[status(x) for x in r.CONTEXTS],
        completion=[status("development-completion/gate",description="PASS main="+A)],
        current_main=A,work_head=B)
class CandidateContract(unittest.TestCase):
    def test_authoritative_positive(self):
        self.assertEqual(r.qualify_candidate(**fixture())["issueNumber"],94)
    def test_adversarial_blocks(self):
        for change in [
            lambda v:v.update(current_main=D),
            lambda v:v.update(work_head=A),
            lambda v:v["candidate"].update(parents=[dict(sha=D)]),
            lambda v:v["candidate"].update(tree=A),
            lambda v:v["candidate"].update(message=v["candidate"]["message"].replace("Work-SHA: "+B,"Work-SHA: "+A)),
            lambda v:v["work"].update(message=v["work"]["message"].replace("RHC-Issue: 94","RHC-Issue: 33")),
            lambda v:v["issue"].update(state="closed"),
            lambda v:v.update(statuses=[]),
            lambda v:v["statuses"][0].update(state="skipped"),
            lambda v:v["statuses"][0]["creator"].update(login="attacker"),
            lambda v:v["completion"][0].update(description="PASS main="+D),
            lambda v:v["completion"][0].update(state="failure"),
        ]:
            v=fixture();change(v)
            with self.subTest(change=change),self.assertRaises(ValueError):
                r.qualify_candidate(**v)
class StageContract(unittest.TestCase):
    def stage_fixture(self):
        q=r.qualify_candidate(**fixture())
        version="3.0.8.8"
        p=dict(state="open",draft=False,merged_at=None,headSha=D,
               baseSha=A,headRef="release/v"+version,title="[RHC-94] Interim unsigned",
               body="Refs #94; sourceSha "+C+"; Work-SHA "+B)
        s=dict(sha=D,parents=[dict(sha=C)],message="release\n\nRHC-Issue: 94")
        files=[*r.PUBLISH_PATHS,"downloads/RazerHealthCenter-Portable-v"+version+".zip"]
        return q,s,p,version,files
    def test_exact_four_downloads_and_single_pr(self):
        q,s,p,v,files=self.stage_fixture()
        self.assertEqual(r.qualify_stage(q,s,p,"release/v"+v,v,files)["result"],"PASS")
    def test_stage_negatives(self):
        for change in [
            lambda x:x[1].update(parents=[dict(sha=A)]),
            lambda x:x[2].update(baseSha=D),
            lambda x:x[2].update(headSha=A),
            lambda x:x[2].update(draft=True),
            lambda x:x[2].update(body="Refs #94; sourceSha "+A+"; Work-SHA "+B),
            lambda x:x[2].update(body="Refs #94; Refs #33; sourceSha "+C+"; Work-SHA "+B),
            lambda x:x[1].update(message="release\nRHC-Issue: 33"),
            lambda x:x[4].append("model.go"),
            lambda x:x[4].remove("downloads/latest.json"),
        ]:
            x=list(self.stage_fixture());change(x)
            with self.subTest(change=change),self.assertRaises(ValueError):
                r.qualify_stage(x[0],x[1],x[2],"release/v"+x[3],x[3],x[4])
if __name__=="__main__":
    unittest.main()
