"""Tests for generated output and the site quality gates.  Run: python3 -m unittest discover -s tests"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import check_site  # noqa: E402
import registry  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


class PublishedSite(unittest.TestCase):
    def test_generated_files_are_up_to_date(self):
        self.assertEqual(build.main(["--check"]), 0, "run: python3 tools/build.py")

    def test_site_passes_all_offline_gates(self):
        self.assertEqual(check_site.check(network=False), [])

    def test_every_entity_has_a_page_in_the_sitemap(self):
        sitemap = (REPO / "sitemap.xml").read_text()
        for page in (REPO / "registry").glob("*/index.html"):
            self.assertIn(f"/registry/{page.parent.name}/", sitemap)

    def test_questions_page_reports_every_project_with_its_lifecycle(self):
        _, ontology = registry.load_all()
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        for e in ontology["entities"]:
            if e["type"] in ("project", "model", "dataset"):
                self.assertIn(f'href="/registry/{e["id"]}/"', html, e["id"])
        # An announced project must never appear in the operational row form.
        for e in ontology["entities"]:
            if e["type"] == "project" and e["lifecycle"] != "operational":
                self.assertNotIn(f'>{e["name"]}</a></td><td>Operational<', html, e["id"])

    def test_questions_page_does_not_overstate_sector_deployments(self):
        _, ontology = registry.load_all()
        ents = {e["id"]: e for e in ontology["entities"]}
        verified = [r for r in ontology["relationships"] if r["predicate"] == "targets"
                    and r["classification"] == "VERIFIED FACT"
                    and ents[r["subject"]].get("lifecycle") in ("operational", "pilot")]
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        if not verified:
            self.assertIn("No sector yet has a verified operational or pilot AI deployment", html)

    def test_homepage_acquisition_path(self):
        html = (REPO / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="acquire"', html)
        self.assertIn(f"mailto:{check_site.CONTACT}", html)
        self.assertIn(check_site.DISCLAIMER, html)
        self.assertNotIn("fonts.googleapis.com", html)


GOOD_PAGE = """<!DOCTYPE html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test page</title>
<meta name="description" content="A test page used to exercise the site quality gates in isolation.">
<link rel="canonical" href="https://themoroccoai.com/">
<meta property="og:url" content="https://themoroccoai.com/">
</head><body><main><h1>Title</h1>
<section id="acquire"><a href="mailto:agent@sohadot.com">Contact</a></section>
<p>Not affiliated with the Government of Morocco</p>
</main></body></html>"""


class GatesCatchRegressions(unittest.TestCase):
    """Run the checker on a throwaway site so each regression is tested in isolation."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "robots.txt").write_text("Sitemap: https://themoroccoai.com/sitemap.xml\n")
        (self.tmp / "sitemap.xml").write_text("<urlset><url><loc>https://themoroccoai.com/</loc></url></urlset>")
        self.addCleanup(shutil.rmtree, self.tmp)
        self._root = check_site.ROOT
        check_site.ROOT = self.tmp
        self.addCleanup(setattr, check_site, "ROOT", self._root)

    def run_with(self, page):
        (self.tmp / "index.html").write_text(page, encoding="utf-8")
        return check_site.check(network=False)

    def assertCaught(self, page, fragment):
        errs = self.run_with(page)
        self.assertTrue(any(fragment in e for e in errs), f"expected '{fragment}' in {errs}")

    def test_baseline_fixture_is_clean(self):
        self.assertEqual(self.run_with(GOOD_PAGE), [])

    def test_third_party_font_stylesheet(self):
        page = GOOD_PAGE.replace("</head>", '<link href="https://fonts.googleapis.com/css2?family=X" rel="stylesheet"></head>')
        self.assertCaught(page, "loads third-party resource")

    def test_third_party_script(self):
        page = GOOD_PAGE.replace("</head>", '<script src="https://cdn.example.com/x.js"></script></head>')
        self.assertCaught(page, "loads third-party resource script")

    def test_placeholder_link(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", '<h1>Title</h1><a href="#">AR</a>'), "placeholder link")

    def test_broken_internal_link(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", '<h1>Title</h1><a href="/registry/nope/">x</a>'),
                          "broken internal link")

    def test_missing_anchor(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", '<h1>Title</h1><a href="#nowhere">x</a>'),
                          "missing anchor")

    def test_canonical_mismatch(self):
        self.assertCaught(GOOD_PAGE.replace('href="https://themoroccoai.com/"', 'href="https://example.com/"'),
                          "canonical")

    def test_missing_description(self):
        self.assertCaught(GOOD_PAGE.replace('<meta name="description"', '<meta name="x"'), "meta description")

    def test_two_h1(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", "<h1>A</h1><h1>B</h1>"), "exactly one <h1>")

    def test_heading_skip(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", "<h1>A</h1><h3>B</h3>"), "heading level skips")

    def test_image_without_alt(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", '<h1>A</h1><img src="data:,">'), "without alt")

    def test_missing_independence_disclaimer(self):
        self.assertCaught(GOOD_PAGE.replace("Not affiliated with the Government of Morocco", "Hello"),
                          "independence disclaimer")

    def test_official_status_wording(self):
        page = GOOD_PAGE.replace("<h1>Title</h1>", "<h1>The sovereign reference infrastructure</h1>")
        self.assertCaught(page, "self-description")

    def test_confidential_pricing(self):
        self.assertCaught(GOOD_PAGE.replace("<h1>Title</h1>", "<h1>A</h1><p>Minimum price is private</p>"),
                          "pricing terms")

    def test_missing_acquisition_contact(self):
        self.assertCaught(GOOD_PAGE.replace('<a href="mailto:agent@sohadot.com">Contact</a>', ""),
                          "no mailto link to the acquisition contact")

    def test_stray_contact_address(self):
        self.assertCaught(GOOD_PAGE.replace("</main>", '<a href="mailto:someone@example.com">x</a></main>'),
                          "unexpected mailto address")

    def test_page_missing_from_sitemap(self):
        (self.tmp / "other.html").write_text(GOOD_PAGE.replace("https://themoroccoai.com/", "https://themoroccoai.com/other.html"))
        self.assertCaught(GOOD_PAGE, "other.html is not listed")

    def test_committed_credential(self):
        (self.tmp / "notes.txt").write_text("token ghp_" + "a" * 36)
        self.assertCaught(GOOD_PAGE, "committed credential")


if __name__ == "__main__":
    unittest.main()
