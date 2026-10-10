"""RHC-132: RED tests for atomic version-only Work preflight."""
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import rhc132_work_preflight as hotfix

BASE = "a" * 40
MODEL = 'package main\nconst (\n appVersion = "3.0.8.12"\n referenceVersion = "3.0.8.12"\n)\n'
CHANGELOG = "# Changelog\n\n## 3.0.8.12 — previous\n\n- Initial.\n"
HEADINGS = ("Chat origin", "Work-Path authorization and scope",
            "Benchmark configuration", "Validation plan and coverage",
            "Measurement ledger", "Development Completion attempts",
            "Candidate Entry", "Candidate attempts", "Release",
            "Final Release Verification", "Performance result",
            "Evidence audit", "Plan-conformance assessment")


def issue():
    return {"number": 132,
            "title": "[RHC-132] Preflight GitHub CI Work-Branch Hotfix with One Atomic Commit",
            "body": "Development path: dev-path: work-branch — strict GitHub CI version-only work",
            "state": "open", "labels": [
                {"name": n} for n in
                ("enhancement", "priority: high", "dev-ops", "dev-path: work-branch")]}


def comment():
    return {"id": 3001, "created_at": "2026-10-10T21:00:01Z",
            "body": "\n".join("### " + h for h in HEADINGS) +
            "\n**Original ISO timestamp:** 2026-10-10T21:00:00.123Z" +
            "\n**Last heartbeat:** 2026-10-10 at 21:00:00 UTC" +
            "\n**Local reference (Europe/Berlin):** 10.10.2026, 23:00:00 CEST" +
            "\n**Issue:** [RHC-132](https://github.com/SaschaP1980/RazerHealthCenter/issues/132)" +
            "\n**Work branch / exact head:** work/RHC-132 / " + BASE +
            "\n**Bootstrap readback:** saved comment #3001 read back before branch"}


def data(**kwargs):
    obj = dict(saved_issue=issue(), comment=comment(), number=132,
               base_main_sha=BASE, readback_main_sha=BASE, work_head_sha=BASE,
               branch_created_at="2026-10-10T21:01:00Z",
               model=MODEL, changelog=CHANGELOG, day=date(2026, 10, 11))
    obj.update(kwargs)
    return obj


class Contract(unittest.TestCase):
    def test_valid_plan_changes_exactly_two_literals_and_changelog(self):
        x = hotfix.plan(**data())
        self.assertEqual(x["to_version"], "3.0.8.13")
        self.assertEqual(x["model"].count('"3.0.8.13"'), 2)
        self.assertEqual(x["allowed_paths"], ["CHANGELOG.md", "model.go"])
        self.assertIn("Development-Completion: requested", x["commit_message"])

    def test_issue_taxonomy_fail_closed(self):
        base=issue()
        for k,v in [("title","[RHC-132] Version Only"),
                    ("state","closed"),
                    ("labels",[{"name":"enhancement"},{"name":"priority: high"},
                               {"name":"dev-path: work-branch"}]),
                    ("body","Development path: PATH_DECISION_PENDING — unknown")]:
            with self.subTest(k=k), self.assertRaises(ValueError):
                hotfix.plan(**data(saved_issue=dict(base,**{k:v})))

    def test_bootstrap_readback_and_13_sections_required(self):
        old=comment()
        for new in (old["body"].replace("### Evidence audit",""),
                    old["body"]+"\n### Chat origin",
                    old["body"].replace("read back before branch","NOT VERIFIED"),
                    old["body"].replace("RHC-132","RHC-999")):
            with self.subTest(len=len(new)), self.assertRaises(ValueError):
                hotfix.plan(**data(comment=dict(old,body=new)))

    def test_comment_time_precedes_branch_and_all_clocks_match(self):
        old=comment()
        for p in ({"branch_created_at":"2026-10-10T20:59:00Z"},
                  {"comment":dict(old,body=old["body"].replace("21:00:00 UTC","21:00:01 UTC"))},
                  {"comment":dict(old,body=old["body"].replace("23:00:00 CEST","21:00:00 CEST"))}):
            with self.subTest(p=p), self.assertRaises(ValueError):
                hotfix.plan(**data(**p))

    def test_wrong_main_sha_branch_or_version_rejected(self):
        for p in ({"readback_main_sha":"b"*40},
                  {"work_head_sha":"b"*40},
                  {"model":MODEL.replace('referenceVersion = "3.0.8.12"',
                                         'referenceVersion = "3.0.8.11"')},
                  {"changelog":"# Changelog\n\n## 3.0.8.11 — old\n"}):
            with self.subTest(p=list(p)), self.assertRaises(ValueError):
                hotfix.plan(**data(**p))

    def test_no_mutation_during_preflight_plan(self):
        m, ch=MODEL,CHANGELOG
        res=hotfix.plan(**data())
        self.assertEqual(MODEL,m)
        self.assertEqual(CHANGELOG,ch)
        self.assertEqual(res["operation"],"PLAN_ONLY")

    def test_git_commit_exactly_one_commit_with_only_two_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            subprocess.run(["git","init","-q",str(root)],check=True)
            for k,v in (("user.name","RHC Test"),("user.email","test@example.invalid")):
                subprocess.run(["git","-C",str(root),"config",k,v],check=True)
            (root/"model.go").write_text(MODEL, encoding="utf-8")
            (root/"CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            subprocess.run(["git","-C",str(root),"add","."],check=True)
            subprocess.run(["git","-C",str(root),"commit","-qm","baseline"],check=True)
            subprocess.run(["git","-C",str(root),"checkout","-qb","work/RHC-132"],check=True)
            old=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
            info=hotfix.plan(**data(base_main_sha=old,readback_main_sha=old,work_head_sha=old))
            new=hotfix.atomic_local_commit(root,info)
            parents=subprocess.check_output(["git","-C",str(root),"rev-list","--parents","-n","1","HEAD"],text=True).strip().split()
            paths=subprocess.check_output(["git","-C",str(root),"diff-tree","--no-commit-id","--name-only","-r","HEAD"],text=True).splitlines()
            self.assertEqual(parents,[new,old])
            self.assertEqual(sorted(paths),["CHANGELOG.md","model.go"])
            self.assertEqual(subprocess.check_output(["git","-C",str(root),"rev-list","--count","HEAD"],text=True).strip(),"2")

    def test_git_commit_blocks_dirty_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            subprocess.run(["git","init","-q",str(root)],check=True)
            for k,v in (("user.name","RHC Test"),("user.email","test@example.invalid")):
                subprocess.run(["git","-C",str(root),"config",k,v],check=True)
            (root/"model.go").write_text(MODEL, encoding="utf-8")
            (root/"CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            subprocess.run(["git","-C",str(root),"add","."],check=True)
            subprocess.run(["git","-C",str(root),"commit","-qm","baseline"],check=True)
            subprocess.run(["git","-C",str(root),"checkout","-qb","work/RHC-132"],check=True)
            old=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
            (root/"unexpected.file").write_text("should block")
            with self.assertRaises(ValueError):
                hotfix.atomic_local_commit(root,hotfix.plan(**data(
                    base_main_sha=old,readback_main_sha=old,work_head_sha=old)))


if __name__=="__main__":
    unittest.main()
