"""RHC-139: RED contracts for exact-evidence rolling audit and closure."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rhc139_rolling_audit as audit

BASE, HEAD, MERGE, STAGE, SOURCE = ("a"*40, "b"*40, "c"*40, "d"*40, "e"*40)
HEADINGS = ("Chat origin", "Work-Path authorization and scope",
            "Benchmark configuration", "Validation plan and coverage",
            "Measurement ledger", "Development Completion attempts",
            "Candidate Entry", "Candidate attempts", "Release",
            "Final Release Verification", "Performance result",
            "Evidence audit", "Plan-conformance assessment")
NOW = datetime(2026,10,11,0,30,0,tzinfo=timezone.utc)


def canonical():
    header = ("## RHC-139 — Rolling Build & Release State\n"
              "**Last heartbeat:** 2026-10-10 at 22:00:00 UTC\n"
              "**Local reference (Europe/Berlin):** 11.10.2026, 00:00:00 CEST\n"
              "**Original ISO timestamp:** 2026-10-10T22:00:00.000Z\n"
              "**Agent-State:** ACTIVE\n"
              "**Issue:** [RHC-139](https://github.com/SaschaP1980/RazerHealthCenter/issues/139)\n"
              "**Current phase:** Work CI\n"
              "**Next action:** Collect real evidence\n")
    return header + "\n".join("### "+h+"\n- Existing verified data\n" for h in HEADINGS)


def job(jid,name,conclusion="success"):
    return {"id":jid,"name":name,"status":"completed","conclusion":conclusion}


class Fake:
    def __init__(self):
        self.comment={"id":3101,"body":canonical(),
                      "updated_at":"2026-10-10T23:50:00Z"}
        self.issue={"number":139,"state":"open","state_reason":None}
        self.calls=[]
        self.mutate=False
        self.heads={"main":MERGE,"work/RHC-139":None}
        self.pr={"number":155,"state":"closed","merged":True,
                 "head":{"sha":HEAD,"ref":"work/RHC-139"},
                 "base":{"sha":BASE},"merge_commit_sha":MERGE}
        self.parents=[BASE,HEAD]
        self.runs={
            101:{"id":101,"name":"RHC Infrastructure Qualification","status":"completed",
                 "conclusion":"success","head_sha":HEAD,"event":"push"},
            102:{"id":102,"name":"RHC Infrastructure Qualification","status":"completed",
                 "conclusion":"success","head_sha":HEAD,"event":"pull_request"},
            103:{"id":103,"name":"RHC v3.0.8 Source Intake","status":"completed",
                 "conclusion":"success","head_sha":HEAD,"event":"pull_request"},
            104:{"id":104,"name":"RHC Verified Merged-Branch Cleanup","status":"completed",
                 "conclusion":"success","head_sha":MERGE,"event":"workflow_run"},
        }
        self.jobs={
            101:[job(1,"rhc/infra/linux"),job(2,"rhc/infra/windows"),
                 job(3,"rhc/infra/artifact-node24")],
            102:[job(4,"rhc/infra/linux"),job(5,"rhc/infra/windows"),
                 job(6,"rhc/infra/artifact-node24")],
            103:[job(7,"Linux build"),job(8,"Hosted Windows native")],
            104:[job(9,"cleanup-merged")],
        }

    def get_issue(self,n): return dict(self.issue)
    def get_comment(self,n):
        if self.mutate:
            self.mutate=False
            return dict(self.comment,body=self.comment["body"]+"\nOTHER WRITER",
                        updated_at="2026-10-10T23:51:00Z")
        return dict(self.comment)
    def get_run(self,n):return dict(self.runs[n])
    def get_jobs(self,n):return [dict(v) for v in self.jobs[n]]
    def get_pr(self,n):return dict(self.pr)
    def get_main_sha(self):return self.heads["main"]
    def get_merge_parents(self,sha):return list(self.parents)
    def get_work_branch(self,branch):return self.heads.get(branch)
    def update_comment(self,n,body):
        self.calls.append("update_comment")
        self.comment["body"]=body
        self.comment["updated_at"]="2026-10-11T00:30:01Z"
    def update_issue(self,n,state):
        self.calls.append("update_issue:"+state)
        self.issue["state"]=state
        if state=="closed":
            self.issue["state_reason"]="completed"
            self.issue["closed_at"]="2026-10-11T00:30:03Z"


def proof():
    return {"mode":"nonpublishing","issue":139,"comment_id":3101,
            "pr":155,"work_sha":HEAD,"base_sha":BASE,
            "merged_sha":MERGE,"run_ids":
            {"work":101,"pr_infra":102,"pr_source":103,"cleanup":104}}


class AuditContract(unittest.TestCase):
    def test_exact_work_ci_required_and_one_safe_close(self):
        gateway=Fake()
        result=audit.finalize(gateway,proof(),now=NOW,apply=True)
        self.assertEqual(result["status"],"COMPLETED")
        self.assertEqual(gateway.issue["state"],"closed")
        self.assertIn("RHC139_EVENT",gateway.comment["body"])
        self.assertEqual(len([x for x in gateway.comment["body"].splitlines()
                              if x.startswith("### ")]),13)
        self.assertEqual(gateway.calls.count("update_issue:closed"),1)

    def test_dry_run_never_changes_issue_or_comment(self):
        gateway=Fake()
        result=audit.finalize(gateway,proof(),now=NOW,apply=False)
        self.assertEqual(result["status"],"READY_PLAN_ONLY")
        self.assertEqual(gateway.calls,[])

    def test_repeated_event_is_idempotent_and_conflict_is_blocked(self):
        original=canonical()
        entry={"key":"work-101","issue":139,"sha":HEAD,
               "status":"success","run_id":101,"job_count":3}
        first=audit.render_event(original,entry,NOW)
        second=audit.render_event(first,entry,NOW)
        self.assertEqual(first.count("RHC139_EVENT"),second.count("RHC139_EVENT"))
        with self.assertRaises(ValueError):
            audit.render_event(first,dict(entry,job_count=0),NOW)

    def test_missing_or_duplicate_13_headings_block(self):
        for body in [canonical().replace("### Evidence audit",""),
                     canonical()+"\n### Chat origin"]:
            with self.assertRaises(ValueError):
                audit.render_event(body,{"key":"a","issue":139,
                    "sha":HEAD,"status":"success","run_id":101,"job_count":3},NOW)

    def test_actual_one_instant_utc_and_berlin_heartbeat(self):
        x=audit.render_event(canonical(),{"key":"work-101","issue":139,
            "sha":HEAD,"status":"success","run_id":101,"job_count":3},NOW)
        self.assertIn("2026-10-11 at 00:30:00 UTC",x)
        self.assertIn("11.10.2026, 02:30:00 CEST",x)
        self.assertIn("2026-10-11T00:30:00.000Z",x)

    def test_wrong_sha_or_wrong_pr_ancestry_blocks_without_writes(self):
        for change in ("wrong_head","parents","main"):
            gateway=Fake()
            if change=="wrong_head": gateway.runs[101]["head_sha"]=BASE
            if change=="parents": gateway.parents=[BASE,SOURCE]
            if change=="main": gateway.heads["main"]=SOURCE
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit.finalize(gateway,proof(),now=NOW,apply=True)
            self.assertEqual(gateway.calls,[])

    def test_skipped_failed_or_zero_job_mandatory_ci_blocks(self):
        for problem in ("zero","skipped","failed"):
            gateway=Fake()
            if problem=="zero":gateway.jobs[102]=[]
            elif problem=="skipped":gateway.jobs[101][1]["conclusion"]="skipped"
            else:gateway.runs[103]["conclusion"]="failure"
            with self.subTest(problem=problem), self.assertRaises(ValueError):
                audit.finalize(gateway,proof(),now=NOW,apply=True)
            self.assertEqual(gateway.calls,[])

    def test_auto_closed_issue_requires_explicit_owner_repair(self):
        gateway=Fake()
        gateway.issue["state"]="closed"
        with self.assertRaises(ValueError):
            audit.finalize(gateway,proof(),now=NOW,apply=True)
        self.assertEqual(gateway.calls,[])

    def test_stale_comment_second_readback_blocks_any_write(self):
        gateway=Fake()
        gateway.mutate=True
        with self.assertRaises(ValueError):
            audit.finalize(gateway,proof(),now=NOW,apply=True)
        self.assertEqual(gateway.calls,[])

    def test_inconsistent_written_comment_blocks_close(self):
        gateway=Fake()
        def unreliable_update(n,body):
            gateway.calls.append("update_comment")
        gateway.update_comment=unreliable_update
        with self.assertRaises(ValueError):
            audit.finalize(gateway,proof(),now=NOW,apply=True)
        self.assertNotIn("update_issue:closed",gateway.calls)

    def test_release_without_true_downloads_and_rhc102_never_passes(self):
        gateway=Fake()
        p=proof()
        p.update(mode="release",version="3.0.8.13",
                 stage_sha=STAGE,source_sha=SOURCE)
        with self.assertRaises(ValueError):
            audit.finalize(gateway,p,now=NOW,apply=True)
        self.assertEqual(gateway.calls,[])

    def test_unknown_time_or_untrusted_record_cannot_be_audit_pass(self):
        with self.assertRaises(ValueError):
            audit.render_event(canonical(),{"key":"unsafe","issue":139,
                "sha":HEAD,"status":"success","run_id":0,"job_count":0},NOW)


    def test_incremental_event_saves_once_with_real_run_sha_and_job_readback(self):
        gateway=Fake()
        ev={"key":"work-101","issue":139,"sha":HEAD,
            "status":"success","run_id":101,"job_count":3}
        first=audit.record_verified_event(gateway,3101,ev,now=NOW,apply=True)
        self.assertEqual(first["status"],"RECORDED")
        self.assertEqual(gateway.calls,["update_comment"])
        second=audit.record_verified_event(gateway,3101,ev,now=NOW,apply=True)
        self.assertEqual(second["status"],"ALREADY_RECORDED")
        self.assertEqual(gateway.calls,["update_comment"])
        with self.assertRaises(ValueError):
            audit.record_verified_event(gateway,3101,
                                        dict(ev,job_count=1),now=NOW,apply=True)

    def test_incremental_bad_or_zero_job_never_writes_comment(self):
        gateway=Fake()
        ev={"key":"work-101","issue":139,"sha":HEAD,
            "status":"success","run_id":101,"job_count":3}
        gateway.runs[101]["head_sha"]=SOURCE
        with self.assertRaises(ValueError):
            audit.record_verified_event(gateway,3101,ev,now=NOW,apply=True)
        self.assertEqual(gateway.calls,[])

    def test_release_mode_needs_all_real_stage_and_postrelease_jobs(self):
        gateway=Fake()
        gateway.pr["head"]["sha"]=STAGE
        gateway.parents=[BASE,STAGE]
        gateway.runs.update({
            105:{"id":105,"name":"RHC Candidate Preflight","event":"workflow_dispatch",
                 "status":"completed","conclusion":"success","head_sha":SOURCE},
            106:{"id":106,"name":"RHC Interim Release","event":"workflow_dispatch",
                 "status":"completed","conclusion":"success","head_sha":SOURCE},
            107:{"id":107,"name":"RHC Downloads Integrity","event":"workflow_dispatch",
                 "status":"completed","conclusion":"success","head_sha":STAGE},
            108:{"id":108,"name":"RHC Independent Postrelease","event":"workflow_dispatch",
                 "status":"completed","conclusion":"success","head_sha":MERGE},
        })
        gateway.jobs.update({
            105:[job(20,"candidate linux"),job(21,"candidate windows"),
                 job(22,"candidate aggregate")],
            106:[job(23,"publish linux"),job(24,"publish windows"),
                 job(25,"stage"),job(26,"finalizer")],
            107:[job(27,"downloads hash check")],
            108:[job(28,"https linux"),job(29,"native windows"),
                 job(30,"aggregate")],
        })
        gateway.get_latest=lambda:{"version":"3.0.8.13","sourceSha":SOURCE,
                                  "sha256":"f"*40,"size":100}
        gateway.get_tag=lambda tag:SOURCE if tag=="v3.0.8.13" else None
        p=proof()
        p.update(mode="release",stage_sha=STAGE,source_sha=SOURCE,
                 version="3.0.8.13",
                 run_ids={"work":101,"candidate":105,"publisher":106,
                          "downloads":107,"rhc102":108})
        x=audit.finalize(gateway,p,now=NOW,apply=True)
        self.assertEqual(x["status"],"COMPLETED")
        self.assertEqual(x["run_count"],5)
        self.assertEqual(gateway.issue["state"],"closed")
        gateway2=Fake()
        gateway2.pr["head"]["sha"]=STAGE
        gateway2.parents=[BASE,STAGE]
        gateway2.runs.update(gateway.runs)
        gateway2.jobs.update(gateway.jobs)
        gateway2.get_latest=gateway.get_latest
        gateway2.get_tag=gateway.get_tag
        gateway2.jobs[107]=[]
        with self.assertRaises(ValueError):
            audit.finalize(gateway2,p,now=NOW,apply=True)
        self.assertEqual(gateway2.calls,[])


if __name__=="__main__":
    unittest.main()
