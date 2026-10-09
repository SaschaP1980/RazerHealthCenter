"""RHC-71: read-only, release-version-neutral HTTP byte readback contracts."""
import io
import json
import pathlib
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rhc_downloads as releases
import rhc_remote_binary_verify as remote

SHA = "a" * 40
REPO = "SaschaP1980/RazerHealthCenter"


class Response(io.BytesIO):
    def __init__(self, data, address):
        super().__init__(data)
        self.address = address

    def geturl(self):
        return self.address

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class RemoteByteReadback(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = pathlib.Path(tmp.name)
        self.root = self.home / "repo"
        self.root.mkdir()
        self.downloads = self.root / "downloads"
        self.downloads.mkdir()
        exe = self.home / "RazerHealthCenter.exe"
        exe.write_bytes(b"MZ" + b"frozen test PE" * 15)
        self.exe = exe
        for name in releases.release.PORTABLE_ASSETS.values():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("data:" + name).encode())
        (self.downloads / "releases.json").write_text(
            json.dumps({"schemaVersion": 1, "releases": []}) + "\n")
        (self.downloads / "README.md").write_text(releases.render_readme([]))
        self.published = {}

    def publish(self, version, sha="b" * 40):
        path = self.home / releases.filename(version)
        releases.make_lean_zip(self.root, self.exe, path)
        row = releases.stage_release(self.downloads, path, version,
                                     "2026-10-09T00:00:00Z", sha)
        self.published[row["file"]] = path.read_bytes()
        return row

    def fetch(self, request, timeout=30):
        url = request.full_url
        name = url.rsplit("/", 1)[-1]
        self.assertIn("/" + SHA + "/downloads/", url)
        self.assertIn("raw.githubusercontent.com/" + REPO, url)
        return Response(self.published[name], url)

    def check(self, **kwargs):
        with patch.object(remote.urllib.request, "urlopen", side_effect=self.fetch):
            return remote.verify_remote_binary(
                self.root, REPO, SHA, **kwargs)

    def test_downloaded_latest_bytes_match_checkout_and_catalog(self):
        row = self.publish("3.0.8.1")
        before = releases.verify(self.downloads)
        result = self.check()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["version"], "3.0.8.1")
        self.assertEqual(result["filename"], row["file"])
        self.assertEqual(result["sha256"], row["sha256"])
        self.assertEqual(result["bytes"], row["size"])
        self.assertEqual(result["commitSha"], SHA)
        self.assertEqual(result["sourceSha"], row["sourceSha"])
        self.assertEqual(releases.verify(self.downloads), before)

    def test_older_published_version_is_selectable(self):
        row = self.publish("3.0.8.1")
        self.publish("3.0.8.2")
        self.assertEqual(self.check(version="3.0.8.1")["sha256"], row["sha256"])
        self.assertEqual(self.check()["version"], "3.0.8.2")

    def test_corrupt_remote_zip_rejected(self):
        row = self.publish("3.0.8.1")
        original = self.published[row["file"]]
        for damaged in (original[:-2], original + b"changed", b""):
            with self.subTest(size=len(damaged)):
                self.published[row["file"]] = damaged
                with self.assertRaises(ValueError):
                    self.check()

    def test_http_failure_is_not_success(self):
        self.publish("3.0.8.1")
        with patch.object(remote.urllib.request, "urlopen",
                          side_effect=urllib.error.URLError("blocked")):
            with self.assertRaises((ValueError, urllib.error.URLError)):
                remote.verify_remote_binary(self.root, REPO, SHA)

    def test_cross_origin_redirect_is_rejected(self):
        self.publish("3.0.8.1")
        def wrong(request, timeout=30):
            return Response(self.published[next(iter(self.published))],
                            "https://example.org/attacker.zip")
        with patch.object(remote.urllib.request, "urlopen", side_effect=wrong):
            with self.assertRaises(ValueError):
                remote.verify_remote_binary(self.root, REPO, SHA)

    def test_invalid_repository_or_commit_or_version_is_rejected(self):
        self.publish("3.0.8.1")
        for repo, sha, version in (
            ("http://localhost", SHA, None),
            (REPO, "../main", None),
            (REPO, "0" * 40, "../../private"),
            ("a/b/c", SHA, None),
        ):
            with self.subTest(repo=repo, sha=sha, version=version):
                with self.assertRaises(ValueError):
                    remote.verify_remote_binary(self.root, repo, sha, version=version)

    def test_unindexed_or_empty_latest_rejected(self):
        with self.assertRaises(ValueError):
            self.check()
        self.publish("3.0.8.1")
        with self.assertRaises(ValueError):
            self.check(version="3.0.8.9")

    def test_existing_local_zip_corruption_blocks_before_download(self):
        row = self.publish("3.0.8.1")
        path = self.downloads / row["file"]
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaises(ValueError):
            self.check()

    def test_workflow_public_readback_is_readonly_and_main_only(self):
        content = (ROOT / ".github/workflows/rhc-downloads-verify.yml"
                   ).read_text(encoding="utf-8")
        for token in ("workflow_dispatch:", "RHC_PUBLIC_BINARY_READBACK_SCOPE=READ_ONLY",
                      "tools/rhc_remote_binary_verify.py",
                      "github.ref == 'refs/heads/main'",
                      "contents: read", "rhc_remote_binary_verify_contracts.py"):
            self.assertIn(token, content)
        self.assertIn("RHC_PUBLIC_BINARY_READBACK=", (
            ROOT / "tools/rhc_remote_binary_verify.py").read_text(encoding="utf-8"))
        for forbidden in ("contents: write", "gh release create", "git push"):
            self.assertNotIn(forbidden, content)


if __name__ == "__main__":
    unittest.main()
