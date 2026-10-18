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

    def test_redirect_to_another_host_needs_review_even_if_quotes_match(self):
        e = check_sources.check_record(RECORD, lambda url: (200, PAGE, "text/html", None, "https://parked.example.net/a"))
        self.assertEqual(e["final_url"], "https://parked.example.net/a")
        self.assertTrue(e["result"].startswith("manual review: redirected to another host"))
        same = check_sources.check_record(RECORD, lambda url: (200, PAGE, "text/html", None, "https://www.example.org/a"))
        self.assertEqual(same["result"], "all excerpts matched")

    def test_http_error_is_distinct_from_network_failure(self):
        e = check_sources.check_record(RECORD, fetcher(status=404, body=b"Not found"))
        self.assertEqual(e["fetch"], "http-error")
        self.assertIn("record kept unchanged", e["result"])

    def test_declared_charset_is_honoured(self):
        rec = dict(RECORD, source_excerpts=["Ministère de la Santé"])
        body = "<p>Ministère de la Santé</p>".encode("latin-1")
        e = check_sources.check_record(rec, fetcher(body=body, ctype="text/html; charset=ISO-8859-1"))
        self.assertEqual(e["excerpts"], ["visible"])

    def test_single_page_app_strings_are_read_from_same_host_scripts_only(self):
        rec = dict(RECORD, source_url="https://app.example.org/", source_excerpts=["Assistant automatisé"])
        shell = b'<html><head><script src="/assets/app.js"></script><script src="https://cdn.example.com/x.js"></script></head></html>'
        seen = []

        def fake(url):
            seen.append(url)
            return {"https://app.example.org/": (200, shell, "text/html", None),
                    "https://app.example.org/assets/app.js": (200, "t=`Assistant automatisé`".encode(), "text/javascript", None)}.get(
                        url, (200, b"Assistant automatis\xc3\xa9", "text/javascript", None))
        e = check_sources.check_record(rec, fake)
        self.assertEqual(e["excerpts"], ["page-script"])
        self.assertNotIn("https://cdn.example.com/x.js", seen)

    def test_each_url_is_fetched_once_per_run(self):
        calls = []
        records = [dict(RECORD, evidence_id="MAI-EV-9001"), dict(RECORD, evidence_id="MAI-EV-9002")]
        check_sources.run(records, lambda url: calls.append(url) or (200, PAGE, "text/html", None), sleep=lambda s: None)
        self.assertEqual(calls, ["https://example.org/a"])

    def test_requests_to_one_host_are_spaced(self):
        waits = []
        records = [dict(RECORD, evidence_id="MAI-EV-9001"), dict(RECORD, evidence_id="MAI-EV-9002", source_url="https://example.org/b")]
        check_sources.run(records, fetcher(), sleep=waits.append)
        self.assertEqual(len(waits), 1)
        self.assertGreater(waits[0], 0)

    def test_report_is_never_written_into_registry_data(self):
        root = registry.ROOT
        for target in (root / "data" / "evidence.json", root / "tools" / "x.json", root / "report.txt"):
            with self.subTest(target=str(target)):
                with self.assertRaises(SystemExit):
                    check_sources._safe_out(str(target))

    def test_matching_quote_of_a_superseded_claim_is_flagged(self):
        # DeepEcho regression: the website disclaimer still matches its source, but the FDA record contradicts it.
        evidence, _ = registry.load_all()
        rec = next(r for r in evidence["records"] if r["evidence_id"] == "MAI-EV-0029")
        page = ("<p>" + " ".join(rec["source_excerpts"]) + "</p>").encode()
        e = check_sources.check_record(rec, fetcher(body=page))
        self.assertEqual(e["result"], "all excerpts matched")
        self.assertEqual(e["claim_check"], "manual")
        self.assertEqual(e["superseded_by"], ["MAI-EV-0032", "MAI-EV-0039"])

    def test_site_build_does_not_import_the_checker(self):
        build_src = (Path(__file__).resolve().parent.parent / "tools" / "build.py").read_text()
        self.assertNotIn("check_sources", build_src)


if __name__ == "__main__":
    unittest.main()
