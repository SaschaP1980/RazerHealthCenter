"""RHC-102: fail-closed immutable release graph, with adversarial mutation."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import rhc102_postrelease_provenance as r

A, B, C, D, E, T = ("a"*40,"b"*40,"c"*40,"d"*40,"e"*40,"f"*40)
VERSION="3.0.8.8"
def fixture():
    catalog={"version":VERSION,"sourceSha":C,"tag":"v"+VERSION}
    graph=dict(main=E,releaseMerge=D,previousMain=A,staged=B,source=C,
               mergeParents=[A,B],stagedParents=[C],sourceParents=[A],
               mergeTree=T,stagedTree=T,tagSha=C,previousVersion="3.0.8.7",
               releasePaths=["model.go","CHANGELOG.md","downloads/README.md",
                   "downloads/latest.json","downloads/releases.json",
                   "downloads/RazerHealthCenter-Portable-v"+VERSION+".zip"],
               laterSourceOrDownloadsDiff=[],oldZipDiff=[])
    return graph,catalog
class RHC102ReadOnlyGraph(unittest.TestCase):
    def test_complete_immutable_combined_graph(self):
        graph,catalog=fixture()
        a=r.verify_commit_shape(graph,catalog,VERSION)
        self.assertEqual(a["result"],"PASS")
        self.assertEqual(a["combinedPaths"],6)
    def test_fail_closed_adversarial_sources_and_history(self):
        modifications=[
            lambda g,c:g.update(main="INVALID"),
            lambda g,c:g.update(source="INVALID"),
            lambda g,c:g.update(source=B),
            lambda g,c:g.update(mergeParents=[A,C]),
            lambda g,c:g.update(mergeParents=[A,B,C]),
            lambda g,c:g.update(stagedParents=[A]),
            lambda g,c:g.update(stagedParents=[C,A]),
            lambda g,c:g.update(sourceParents=[B]),
            lambda g,c:g.update(sourceParents=[A,A]),
            lambda g,c:g.update(mergeTree=A),
            lambda g,c:g.update(tagSha=A),
            lambda g,c:g.update(previousVersion=VERSION),
            lambda g,c:g["releasePaths"].append("downloads/evil.zip"),
            lambda g,c:g["releasePaths"].remove("model.go"),
            lambda g,c:g["releasePaths"].remove("downloads/latest.json"),
            lambda g,c:g["releasePaths"].append("model.go"),
            lambda g,c:g.update(laterSourceOrDownloadsDiff=["model.go"]),
            lambda g,c:g.update(oldZipDiff=["downloads/RazerHealthCenter-Portable-v3.0.8.7.zip"]),
            lambda g,c:c.update(sourceSha=A),
            lambda g,c:c.update(tag="v3.0.8.7"),
            lambda g,c:c.update(version="3.0.8.7"),
        ]
        for mutate in modifications:
            g,c=fixture()
            mutate(g,c)
            with self.subTest(mutator=str(mutate)),self.assertRaises(ValueError):
                r.verify_commit_shape(g,c,VERSION)
    def test_product_version_mismatch(self):
        g,c=fixture()
        with self.assertRaises(ValueError):
            r.verify_commit_shape(g,c,"3.0.8.7")
    def test_published_safety_fields_unchanged(self):
        import json
        p=json.loads((pathlib.Path(__file__).resolve().parents[1]/
                      "config/rhc-release-policy.json").read_text())
        for key,value in r.POLICY.items():
            self.assertEqual(p[key],value)
if __name__=="__main__":
    unittest.main()
