"""Tests for the source checker, using a fake fetcher (no network).  Run: python3 -m unittest discover -s tests"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import check_sources  # noqa: E402
import registry  # noqa: E402

RECORD = {"evidence_id": "MAI-EV-9001", "source_url": "https://example.org/a",
          "source_excerpts": ["The ministry signed a convention", "launched in Rabat"]}
PAGE = b"<html><body><p>The ministry  signed a convention.</p><script>var x='launched in Rabat';</script></body></html>"


def fetcher(status=200, body=PAGE, ctype="text/html", error=None):
    return lambda url: (status, body, ctype, error)


class SourceChecker(unittest.TestCase):
    def test_matches_visible_text_and_raw_source_separately(self):
        e = check_sources.check_record(RECORD, fetcher())
        self.assertEqual(e["excerpts"], ["visible", "raw-source"])
        self.assertEqual(e["result"], "all excerpts matched")

    def test_claim_support_is_never_automated(self):
        self.assertEqual(check_sources.check_record(RECORD, fetcher())["claim_check"], "manual")

    def test_http_200_alone_is_not_verification(self):
        e = check_sources.check_record(RECORD, fetcher(body=b"<html><body>Unrelated page</body></html>"))
        self.assertEqual(e["fetch"], "retrieved")
        self.assertTrue(e["result"].startswith("manual review: no excerpt found"))

    def test_partial_match_needs_review(self):
        e = check_sources.check_record(RECORD, fetcher(body=b"<p>The ministry signed a convention</p>"))
        self.assertTrue(e["result"].startswith("manual review: some excerpts missing"))

    def test_blocked_and_challenge_pages_are_not_checked(self):
        for kwargs in ({"status": 403, "body": b"Forbidden"}, {"status": 429, "body": b""},
                       {"status": 200, "body": b"<title>Just a moment...</title>"}):
            with self.subTest(**{k: str(v) for k, v in kwargs.items()}):
                e = check_sources.check_record(RECORD, fetcher(**kwargs))
                self.assertEqual(e["fetch"], "blocked")
                self.assertIn("record kept unchanged", e["result"])

    def test_network_failure_is_unreachable_not_a_deletion(self):
        evidence, _ = registry.load_all()
        before = copy.deepcopy(evidence)
        report = check_sources.run(evidence["records"][:3], fetcher(status=None, body=b"", error="timed out"), sleep=lambda s: None)
        self.assertTrue(all(e["fetch"] == "unreachable" for e in report))
        self.assertEqual(evidence, before)
        self.assertEqual(registry.load_all()[0], before)

    def test_change_against_baseline_is_reported(self):
        first = check_sources.check_record(RECORD, fetcher())
        second = check_sources.check_record(RECORD, fetcher(body=PAGE + b"<!-- edited -->"), baseline=first)
        self.assertTrue(second["changed_since_baseline"])
        same = check_sources.check_record(RECORD, fetcher(), baseline=first)
        self.assertFalse(same["changed_since_baseline"])

    def test_site_build_does_not_import_the_checker(self):
        build_src = (Path(__file__).resolve().parent.parent / "tools" / "build.py").read_text()
        self.assertNotIn("check_sources", build_src)


if __name__ == "__main__":
    unittest.main()
