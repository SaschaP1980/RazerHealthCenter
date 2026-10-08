"""RHC-12 LBS-style repository-downloads archive and manifest regressions."""
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_downloads as d


class Downloads(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.src = self.base / "src"
        self.src.mkdir()
        self.downloads = self.src / "downloads"
        self.downloads.mkdir()
        self.exe = self.base / "RazerHealthCenter.exe"
        self.exe.write_bytes(b"MZ" + b"\0" * 100)
        for name in d.release.PORTABLE_ASSETS.values():
            path = self.src / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("asset:" + name).encode("utf-8"))
        self.empty()

    def empty(self):
        (self.downloads / "README.md").write_text(d.render_readme([]), encoding="utf-8")
        (self.downloads / "releases.json").write_text(
            json.dumps({"schemaVersion": 1, "releases": []}) + "\n")

    def release(self, version="3.0.9", sha="a" * 40, utc="2026-10-08T11:00:00Z"):
        name = d.filename(version)
        outer = self.base / name
        d.make_lean_zip(self.src, self.exe, outer)
        return d.stage_release(self.downloads, outer, version, utc, sha)

    def test_empty_archive_contract(self):
        self.assertEqual(d.verify(self.downloads), [])
        self.assertFalse((self.downloads / "latest.json").exists())

    def test_lbs_archive_file_names(self):
        self.assertEqual(d.filename("3.0.9"), "RazerHealthCenter-Portable-v3.0.9.zip")
        self.assertRaises(ValueError, d.filename, "3.0.9-beta")
        self.assertRaises(ValueError, d.filename, "03.0.9")

    def test_one_version_has_lean_portable_and_index(self):
        row = self.release()
        self.assertEqual(len(d.verify(self.downloads)), 1)
        self.assertEqual(row["packageFiles"], sorted(d.EXPECTED_FILES))
        self.assertEqual(json.loads((self.downloads / "latest.json").read_text()), row)
        with zipfile.ZipFile(self.downloads / row["file"]) as z:
            self.assertEqual(set(z.namelist()), d.EXPECTED_FILES)
            self.assertEqual(sum(n.endswith(".zip") for n in z.namelist()), 0)

    def test_repeated_build_bit_identical(self):
        a, b = self.base / "a.zip", self.base / "b.zip"
        d.make_lean_zip(self.src, self.exe, a)
        d.make_lean_zip(self.src, self.exe, b)
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_two_versions_newest_first_previous_unchanged(self):
        old = self.release()
        before = (self.downloads / old["file"]).read_bytes()
        new = self.release("3.0.10", "b" * 40, "2026-10-09T13:00:00Z")
        self.assertEqual([x["version"] for x in d.verify(self.downloads)],
                         ["3.0.10", "3.0.9"])
        self.assertEqual((self.downloads / old["file"]).read_bytes(), before)
        self.assertEqual(json.loads((self.downloads / "latest.json").read_text()), new)

    def test_cannot_overwrite_same_version(self):
        self.release()
        with self.assertRaises(ValueError):
            self.release()

    def test_cannot_rollback_latest_version(self):
        self.release("3.0.10")
        with self.assertRaisesRegex(ValueError, "must increase"):
            self.release("3.0.9")

    def test_zip_tamper_detected(self):
        row = self.release()
        f = self.downloads / row["file"]
        f.write_bytes(f.read_bytes() + b"mutated")
        with self.assertRaisesRegex(ValueError, "hash or size"):
            d.verify(self.downloads)

    def test_catalog_pointer_tamper_detected(self):
        self.release()
        path = self.downloads / "latest.json"
        x = json.loads(path.read_text())
        x["version"] = "3.0.10"
        path.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError, "pointer mismatch"):
            d.verify(self.downloads)

    def test_extra_unindexed_zip_is_blocked(self):
        (self.downloads / "random.zip").write_bytes(b"ZIP")
        with self.assertRaisesRegex(ValueError, "unindexed"):
            d.verify(self.downloads)

    def test_no_latest_when_empty(self):
        (self.downloads / "latest.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "must not exist"):
            d.verify(self.downloads)

    def test_legacy_duplicate_source_zip_inside_portable_blocked(self):
        archive = self.base / d.filename("3.0.9")
        d.make_lean_zip(self.src, self.exe, archive)
        with zipfile.ZipFile(archive, "a") as z:
            z.writestr("RazerHealthCenter-Source-v3.0.9.zip", b"bad")
        with self.assertRaisesRegex(ValueError, "allowlist"):
            d.make_record(archive, "3.0.9", "2026-10-08T11:00:00Z", "a" * 40)

    def test_no_unexpected_empty_directories(self):
        archive = self.base / d.filename("3.0.9")
        d.make_lean_zip(self.src, self.exe, archive)
        with zipfile.ZipFile(archive, "a") as z:
            z.writestr("Runtime/", b"")
        with self.assertRaises(ValueError):
            d.portable_zip_check(archive)

    def test_wrong_sha_or_timestamp_blocks_publication_record(self):
        archive = self.base / d.filename("3.0.9")
        d.make_lean_zip(self.src, self.exe, archive)
        with self.assertRaisesRegex(ValueError, "source SHA"):
            d.make_record(archive, "3.0.9", "2026-10-08T11:00:00Z", "BAD")
        with self.assertRaisesRegex(ValueError, "publishedUtc|timestamp"):
            d.make_record(archive, "3.0.9", "2026-10-08T11:00:00+02:00", "a" * 40)

    def test_readme_drift_detected(self):
        self.release()
        f = self.downloads / "README.md"
        f.write_text(f.read_text(encoding="utf-8") + "fake version\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "README history drift"):
            d.verify(self.downloads)

    def test_unsafe_pe_and_missing_asset_rejected(self):
        self.exe.write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError, "Windows PE"):
            d.make_lean_zip(self.src, self.exe, self.base / "bad.zip")
        self.exe.write_bytes(b"MZ")
        (self.src / "locales" / "de-DE.json").unlink()
        with self.assertRaisesRegex(ValueError, "asset"):
            d.make_lean_zip(self.src, self.exe, self.base / "noasset.zip")

    def test_wrong_catalog_schema(self):
        (self.downloads / "releases.json").write_text(
            json.dumps({"schemaVersion": 2, "releases": []}))
        with self.assertRaisesRegex(ValueError, "schema"):
            d.verify(self.downloads)


if __name__ == "__main__":
    unittest.main()
