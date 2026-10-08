"""Integration characterization of the no-publish atomic Candidate Entry CLI."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_TOOLS = Path(__file__).resolve().parents[1] / 'tools'


def cmd(*args, cwd=None, check=True):
    result=subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f'{args}: {result.stdout} {result.stderr}')
    return result


class AtomicGitCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.remote=self.root/'origin.git'
        self.checkout=self.root/'repo'
        cmd('git','init','-q','--bare',str(self.remote))
        cmd('git','init','-q','-b','main',str(self.checkout))
        cmd('git','config','user.name','RHC CI Test',cwd=self.checkout)
        cmd('git','config','user.email','test@invalid.example',cwd=self.checkout)
        cmd('git','config','core.autocrlf','false',cwd=self.checkout)
        (self.checkout/'tools').mkdir()
        for tool in ('rhc_candidate_entry.py','rhc_orchestration_contracts.py','rhc_release_contracts.py'):
            shutil.copy2(SOURCE_TOOLS/tool,self.checkout/'tools'/tool)
        self.model=self.checkout/'model.go'
        self.model.write_text('const (\n appVersion = "3.0.8"\n referenceVersion = "3.0.8"\n)\n')
        (self.checkout/'go.mod').write_text('module testing\ngo 1.23.2\n')
        cmd('git','add','-A',cwd=self.checkout)
        cmd('git','commit','-qm','baseline RHC v3.0.8',cwd=self.checkout)
        cmd('git','remote','add','origin',str(self.remote),cwd=self.checkout)
        cmd('git','push','-q','-u','origin','main',cwd=self.checkout)
        cmd('git','fetch','-q','origin','main',cwd=self.checkout)
        cmd('git','switch','-qc','candidate/v3.0.9',cwd=self.checkout)
        self.model.write_text('const (\n appVersion = "3.0.9"\n referenceVersion = "3.0.9"\n)\n')
        (self.checkout/'CHANGELOG.md').write_text('## 3.0.9 — version only\n')
        cmd('git','add','-A',cwd=self.checkout)
        cmd('git','commit','-qm','release: RHC v3.0.9\n\nRelease-Profile: version-only\nRHC-Issue: 3',cwd=self.checkout)

    def tearDown(self):
        self.temp.cleanup()

    def check_cli(self, ref='candidate/v3.0.9'):
        return cmd(sys.executable,'-B','tools/rhc_candidate_entry.py','--root','.','--candidate-ref',ref,
                   cwd=self.checkout,check=False)

    def test_exact_atomic_version_only_accepted(self):
        res=self.check_cli()
        self.assertEqual(res.returncode,0,res.stderr)
        self.assertIn('RHC_CANDIDATE_ENTRY_SUMMARY=',res.stdout)
        self.assertIn('"baseMainSha"',res.stdout)

    def test_mismatched_ref_fail_closed(self):
        res=self.check_cli('candidate/v3.0.10')
        self.assertNotEqual(res.returncode,0)
        self.assertIn('version',res.stderr)

    def test_dirty_checkout_fail_closed(self):
        (self.checkout/'dirty.txt').write_text('untracked changes\n')
        res=self.check_cli()
        self.assertNotEqual(res.returncode,0)
        self.assertIn('checkout',res.stderr)

    def test_stale_main_parent_fail_closed(self):
        cmd('git','switch','-q','main',cwd=self.checkout)
        (self.checkout/'README.md').write_text('changed main\n')
        cmd('git','add','-A',cwd=self.checkout)
        cmd('git','commit','-qm','main advanced',cwd=self.checkout)
        cmd('git','push','-q','origin','main',cwd=self.checkout)
        cmd('git','fetch','-q','origin','main',cwd=self.checkout)
        cmd('git','switch','-q','candidate/v3.0.9',cwd=self.checkout)
        res=self.check_cli()
        self.assertNotEqual(res.returncode,0)
        self.assertIn('current main',res.stderr)


if __name__=='__main__':unittest.main(verbosity=2)
