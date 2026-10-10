"""RHC-115: issue initialization and title-readback safety contracts."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from rhc_issue_init import (InitializationBlocked, initialize_issue,
                            recover_issue, verify_issue)

VALID_BODY = 'Development path: dev-path: fast — narrowly scoped example update'
LABELS = ['enhancement', 'priority: high', 'dev-path: fast']


class Gateway:
    def __init__(self):
        self.issues = {}
        self.number = 115
        self.creates = 0
        self.updates = 0
        self.numberless = False
        self.create_raises = False
        self.update_raises = False
        self.stale_get = False
        self.duplicate_lookup = False
        self.bad_response_number = False
        self.fail_update = False

    def create(self, title, body, labels):
        self.creates += 1
        self.issues[self.number] = dict(number=self.number, title=title,
                                        body=body, state="open",
                                        labels=[{'name': x} for x in labels])
        if self.create_raises:
            raise TimeoutError("uncertain creation result")
        return {"number": self.number + 1 if self.bad_response_number
                else None if self.numberless else self.number}

    def get(self, number):
        value = self.issues.get(number)
        if value is None:
            return None
        if self.stale_get:
            return dict(value, title="stale")
        return dict(value)

    def search(self, provisional_title, body):
        found = [dict(v) for v in self.issues.values()
                 if v["title"] == provisional_title and v["body"] == body]
        return found + found if self.duplicate_lookup else found

    def update(self, number, title):
        self.updates += 1
        if self.fail_update:
            raise PermissionError("rename failed")
        self.issues[number]["title"] = title
        if self.update_raises:
            raise TimeoutError("response lost")


class TitleContracts(unittest.TestCase):
    def test_valid_exact_match(self):
        self.assertEqual(verify_issue(dict(number=115, title="[RHC-115] Descriptive",
                                           body="Scope", state="open"), 115, body="Scope")["number"], 115)

    def test_provisional_and_malformed_titles_fail(self):
        for title in ("Initializing RHC Issue: Something [init-123]",
                      "RHC: Missing", "[RHC] Missing", "[RHC-OTHER_NUMBER] Wrong",
                      "[RHC-0] Zero", "[RHC-114] Other", "[RHC-115]",
                      "[RHC-115]   ", "[RHC-0115] Leading zero"):
            with self.subTest(title=title), self.assertRaises(InitializationBlocked):
                verify_issue(dict(number=115, title=title, body="Scope",
                                  state="open"), 115, body="Scope")

    def test_scope_number_open_and_pr_mismatch_fail(self):
        correct = dict(number=115, title="[RHC-115] Subject", body="Scope", state="open")
        for patch in ({"number": 114}, {"body": "wrong"}, {"state": "closed"},
                      {"pull_request": {}}, {"title": "[RHC-999] Other"}):
            with self.subTest(patch=patch), self.assertRaises(InitializationBlocked):
                verify_issue(dict(correct, **patch), 115, body="Scope")

    def test_create_and_independent_readback(self):
        g = Gateway()
        result = initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")
        self.assertEqual(result["number"], 115)
        self.assertEqual(g.creates, 1)
        self.assertEqual(g.updates, 1)
        self.assertEqual(g.issues[115]["title"], "[RHC-115] Example")

    def test_missing_number_reconciles_without_duplicate(self):
        g = Gateway()
        g.numberless = True
        self.assertEqual(initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")["number"], 115)
        self.assertEqual(g.creates, 1)

    def test_uncertain_create_reconciles_without_second_create(self):
        g = Gateway()
        g.create_raises = True
        self.assertEqual(initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")["number"], 115)
        self.assertEqual(g.creates, 1)

    def test_ambiguous_duplicate_or_wrong_create_number_fails_closed(self):
        for flag in ("duplicate_lookup", "bad_response_number"):
            g = Gateway()
            setattr(g, flag, True)
            with self.subTest(flag=flag), self.assertRaises(InitializationBlocked):
                initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")
            self.assertEqual(g.creates, 1)
            self.assertEqual(g.updates, 0)

    def test_failed_unknown_and_stale_rename(self):
        for flag in ("fail_update", "stale_get"):
            g = Gateway()
            setattr(g, flag, True)
            with self.subTest(flag=flag), self.assertRaises(InitializationBlocked):
                initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")
            self.assertEqual(g.creates, 1)
        g = Gateway()
        g.update_raises = True
        self.assertEqual(initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")["number"], 115)
        self.assertEqual(g.updates, 1)

    def test_recover_existing_correct_does_not_write(self):
        g = Gateway()
        g.issues[115] = dict(number=115, title="[RHC-115] Example",
                             body=VALID_BODY, state="open", labels=[{"name": x} for x in LABELS])
        self.assertEqual(recover_issue(g, 115, "Example", VALID_BODY)["number"], 115)
        self.assertEqual(g.updates, 0)
        self.assertEqual(g.creates, 0)

    def test_recover_exact_provisional_and_reject_foreign(self):
        g = Gateway()
        g.issues[115] = dict(number=115, title="Initializing RHC Issue: Example [init-aabbccddeeff]",
                             body=VALID_BODY, state="open", labels=[{"name": x} for x in LABELS])
        self.assertEqual(recover_issue(g, 115, "Example", VALID_BODY, nonce="aabbccddeeff")["number"], 115)
        self.assertEqual(g.updates, 1)
        with self.assertRaises(InitializationBlocked):
            recover_issue(g, 115, "Different", "Scope", nonce="aabbccddeeff")

    def test_missing_response_and_search_must_not_guess(self):
        g = Gateway()
        g.create = lambda *_: None
        with self.assertRaises(InitializationBlocked):
            initialize_issue(g, "Example", VALID_BODY, LABELS, nonce="aabbccddeeff")

    def test_verify_is_independent_from_create_response(self):
        g = Gateway()
        g.issues[115] = dict(number=115, title="[RHC-115] Example", body="Scope", state="open")
        self.assertEqual(verify_issue(g.get(115), 115, body="Scope")["number"], 115)
        self.assertRaises(InitializationBlocked, verify_issue, None, 115, body="Scope")


if __name__ == "__main__":
    unittest.main()
