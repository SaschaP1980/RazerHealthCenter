"""RHC-20: native GitHub merge-commit shape, not a fast-forward release fiction.

All inputs are synthetic read-only snapshots. No tag, PR merge or release write.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rhc_release_transaction import verify_postpublish
from test_rhc_release_transaction_contracts import release_case, A, B, C, D, VERSION

MERGED = "f" * 40


def real_merge_snapshot():
    case = release_case()
    case["pr"] = dict(case["pr"], state="closed", merged=True)
    case.update(
        prMerged=True,
        mergedMainSha=MERGED,
        mergeParentShas=[A, C],
        tagTargetSha=B,
        publicVersion=VERSION,
        latestSha256=D,
        publishedFileSha256=D,
        immutableHistoryVerified=True,
        releaseBranchState="deleted-after-verified-merge",
    )
    return case


class NativeMergePostverify(unittest.TestCase):
    def test_two_parent_merge_commit_and_closed_pr_are_accepted(self):
        case = real_merge_snapshot()
        self.assertNotEqual(case["mergedMainSha"], case["releaseSha"])
        self.assertEqual(verify_postpublish(case)["result"], "VERIFIED")

    def test_fast_forward_and_mismatched_merge_parentage_are_rejected(self):
        correct = real_merge_snapshot()
        tampered = (
            {"mergedMainSha": C},
            {"mergedMainSha": "not-a-sha"},
            {"mergeParentShas": [C, A]},
            {"mergeParentShas": [A, B]},
            {"mergeParentShas": [A, C, B]},
            {"mergeParentShas": []},
            {"pr": dict(correct["pr"], state="open", merged=False)},
        )
        for change in tampered:
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_postpublish(dict(correct, **change))


if __name__ == "__main__":
    unittest.main()
