"""Nonpublishing and adversarial migration contract tests (stdlib unittest)."""
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import rhc_release_contracts as r


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'src'
        self.root.mkdir()
        (self.root / 'tools').mkdir()
        (self.root / 'model.go').write_text('const (\n appVersion = "3.0.8"\n referenceVersion = "3.0.8"\n)\n')
        for name in ('go.mod', 'build.sh', 'tools/rhc_release_contracts.py'):
            p = self.root / name
            p.write_bytes(b'canonical source\n')
        for name in r.PORTABLE_ASSETS.values():
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'asset ' + name.encode())
        self.paths = ['go.mod', 'build.sh', 'model.go', 'tools/rhc_release_contracts.py']
        self.paths += [f'tools/fixture_{n}.py' for n in range(18)]
        for path in self.paths[4:]:
            (self.root / path).write_text('pass\n')
        self.exe = Path(self.tmp.name) / 'RazerHealthCenter.exe'
        self.exe.write_bytes(b'MZ' + b'\0'*30)
        self.out = Path(self.tmp.name) / 'out'
        self.out.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_version_agreement_and_increasing(self):
        self.assertEqual(r.version_from_model(self.root), '3.0.8')
        self.assertTrue(r.assert_future_version('3.0.9', '3.0.8'))
        for wrong in ('3.0.8', '3.0.7', '03.0.9', '3.0.9-beta', '4.0'):
            with self.assertRaises(ValueError):
                r.assert_future_version(wrong, '3.0.8')
        (self.root/'model.go').write_text('appVersion = "3.0.8"\nreferenceVersion = "3.0.7"')
        with self.assertRaises(ValueError):
            r.version_from_model(self.root)

    def test_source_reproducibility_and_exclusion(self):
        files = self.paths + ['archive.zip', 'forensics/secret.txt', 'BUILD-FULL.log', 'foo.exe']
        a, b = self.out/'one.zip', self.out/'two.zip'
        x = r.source_zip(self.root, a, source_paths=files)
        y = r.source_zip(self.root, b, source_paths=files)
        self.assertEqual(x['sha256'], y['sha256'])
        self.assertEqual(x['fileCount'], len(self.paths))
        with zipfile.ZipFile(a) as z:
            self.assertEqual(set(z.namelist()), set(self.paths))
            self.assertEqual(z.read('go.mod'), b'canonical source\n')

    def test_source_rejects_missing_and_duplicate(self):
        with self.assertRaises(ValueError):
            r.source_zip(self.root, self.out/'missing.zip', source_paths=self.paths[:-1] + ['tools/nope.py'])
        with self.assertRaises(ValueError):
            r.source_zip(self.root, self.out/'double.zip', source_paths=self.paths + [self.paths[0]])
        with self.assertRaises(ValueError):
            r.source_zip(self.root, self.root/'output.zip', source_paths=self.paths)

    def test_portable_reproducibility_and_integrity(self):
        a, b = self.out/'p1.zip', self.out/'p2.zip'
        x = r.portable_zip(self.root, self.exe, a)
        y = r.portable_zip(self.root, self.exe, b)
        self.assertEqual(x['sha256'], y['sha256'])
        self.assertEqual(x['fileCount'], 7)
        self.assertEqual(x['directoryCount'], 12)
        with zipfile.ZipFile(a) as z:
            self.assertIsNone(z.testzip())
            for line in z.read('SHA256SUMS.txt').decode().splitlines():
                h, name = line.split('  ', 1)
                self.assertEqual(h, r.sha(z.read(name)))

    def test_portable_rejects_missing_asset_and_invalid_exe(self):
        (self.root/'packaging/README.txt').unlink()
        with self.assertRaises(ValueError):
            r.portable_zip(self.root, self.exe, self.out/'p.zip')
        (self.root/'packaging/README.txt').write_text('restored')
        self.exe.write_bytes(b'not a PE')
        with self.assertRaises(ValueError):
            r.portable_zip(self.root, self.exe, self.out/'bad.zip')

    def test_sensitive_paths_denied(self):
        for path in ['forensics/patient.json', 'BUILD-FULL.log', 'OriginalSource.zip',
                     'temp.exe', '.git/config', 'dist/main.go', '../escape.go',
                     'C:/users/private.txt', 'tools/../../danger.py']:
            self.assertFalse(r.permitted_source(path), path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
