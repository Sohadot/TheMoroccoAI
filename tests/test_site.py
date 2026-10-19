"""Tests for generated output and the site quality gates.  Run: python3 -m unittest discover -s tests"""
import datetime
import html as html_lib
import re
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
            self.assertIn("No qualifying deployment has yet been documented in this registry", html)
        # Absence in the registry must never be stated as absence in Morocco.
        self.assertIn("not the state of AI use in Morocco", html)

    def _questions_with(self, mutate):
        evidence, ontology = registry.load_all()
        mutate(ontology)
        return build.render_questions(build.Model(evidence, ontology))

    def test_operational_infrastructure_does_not_count_as_a_sector_deployment(self):
        def mutate(o):
            o["relationships"].append({"subject": "toubkal-supercomputer", "predicate": "targets", "object": "health",
                                       "evidence": ["MAI-EV-0020"], "classification": "VERIFIED FACT"})
        html = self._questions_with(mutate)
        q4 = html[html.index('id="q4-h"'):html.index("<table", html.index('id="q4-h"'))]
        self.assertNotIn('href="/registry/health/"', q4)

    def _questions_with_dates(self, date, as_of=None, ids=("MAI-EV-0034", "MAI-EV-0035", "MAI-EV-0038")):
        evidence, ontology = registry.load_all()
        if as_of:
            evidence["as_of"] = as_of
        for r in evidence["records"]:
            if r["evidence_id"] in ids:
                r["publication_date"] = date
        html = build.render_questions(build.Model(evidence, ontology))
        return html[html.index('id="q6-h"'):html.index('id="q7-h"')], html[html.index('id="q7-h"'):html.index('id="q8-h"')]

    def test_old_evidence_is_flagged_but_never_changes_the_stage(self):
        q6, q7 = self._questions_with_dates("2024-01-15")
        row = q6[q6.index('href="/registry/idarati-ai/"'):]
        row = row[:row.index("</tr>")]
        self.assertIn("Latest supporting evidence 15 January 2024 is more than 12 months old; current operation has not been reconfirmed", row)
        self.assertIn("Operational (public availability; use not documented)", row)
        self.assertNotIn("Discontinued", row)
        self.assertIn('href="/registry/idarati-ai/"', q7)
        self.assertIn("Not reconfirmed in 12 months", q7)

    def test_recent_evidence_is_not_presented_as_continued_operation(self):
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("Current:", html)
        self.assertIn("operation after that date not reconfirmed", html)

    def test_recency_boundary_is_twelve_calendar_months(self):
        cases = [("2025-10-19", None, False), ("2025-10-18", None, True),        # exactly 12 months / one day more (as_of 2026-10-19)
                 ("2025-10", None, True),                                          # month-only date counts from its 1st
                 ("2027-02-28", "2028-02-29", False), ("2027-02-27", "2028-02-29", True)]  # leap-day as_of
        for date, as_of, stale in cases:
            with self.subTest(date=date, as_of=as_of):
                q6, q7 = self._questions_with_dates(date, as_of)
                self.assertEqual("more than 12 months old" in q6, stale)
                self.assertEqual('href="/registry/idarati-ai/"' in q7, stale)

    def test_months_before_clamps_to_month_end(self):
        self.assertEqual(build._months_before(datetime.date(2028, 2, 29), 12), datetime.date(2027, 2, 28))
        self.assertEqual(build._months_before(datetime.date(2026, 3, 31), 1), datetime.date(2026, 2, 28))
        self.assertEqual(build._months_before(datetime.date(2026, 1, 15), 12), datetime.date(2025, 1, 15))

    def test_undated_observation_uses_its_retrieval_date(self):
        q6, _ = self._questions_with_dates(None)
        self.assertIn("Latest supporting evidence 18 October 2026 (observed)", q6)

    def test_discontinued_project_gets_no_recency_wording(self):
        def mutate(o):
            next(e for e in o["entities"] if e["id"] == "toubkal-supercomputer")["lifecycle"] = "discontinued"
        evidence, ontology = registry.load_all()
        mutate(ontology)
        rec = next(r for r in evidence["records"] if r["evidence_id"] == "MAI-EV-0020")
        rec["status_evidence"] = "discontinued"
        del rec["status_basis"]
        model = build.Model(evidence, ontology)
        facts = build.deployment_facts(model, model.entities["toubkal-supercomputer"])
        self.assertEqual((facts["currency"], facts["stale"]), ("", False))

    def test_deployments_show_operator_separately_from_provider(self):
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        q6 = html[html.index('id="q6-h"'):html.index('id="q7-h"')]
        row = q6[q6.index('href="/registry/idarati-ai/"'):]
        row = row[:row.index("</tr>")]
        self.assertIn('href="/registry/ministry-digital-transition/"', row)
        # An interface label not shown on the assistant establishes no provider role.
        self.assertNotIn("Berexia", row)
        self.assertIn("<td>Not documented</td>", row)
        self.assertIn("use not documented", row)

    def test_availability_is_labelled_wherever_the_stage_appears(self):
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        page = (REPO / "registry" / "idarati-ai" / "index.html").read_text(encoding="utf-8")
        rows = re.findall(r'<tr>(?:(?!</tr>).)*?href="/registry/idarati-ai/"(?:(?!</tr>).)*</tr>', html)
        self.assertGreaterEqual(len(rows), 3)
        for row in rows + [page]:
            with self.subTest(row=row[:80]):
                self.assertNotIn(">Operational<", row)
                self.assertNotIn("Idarati AI</a> (Operational)", row)
        self.assertIn("Operational (public availability; use not documented)", page)

    def test_single_deployment_is_not_presented_as_national(self):
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        self.assertIn("It is the only one currently documented in this registry, not necessarily the only one in Morocco.", html)

    def test_regulatory_caveats_are_shown_on_records(self):
        html = (REPO / "registry" / "evidence" / "index.html").read_text(encoding="utf-8")
        card = html[html.index('id="MAI-EV-0029"'):]
        self.assertIn("The quotation still matches its source, but the claim is no longer current", card[:card.index("</li>")])
        card = html[html.index('id="MAI-EV-0032"'):]
        self.assertIn("not established as the same legal entity", card[:card.index("</li>")])
        self.assertNotIn("FDA-approved", html)

    def test_questions_reflect_admitted_records(self):
        _, ontology = registry.load_all()
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        q6 = html[html.index('id="q6-h"'):html.index('id="q7-h"')]
        for e in ontology["entities"]:
            if e.get("project_kind") == "ai-application":
                self.assertIn(f'href="/registry/{e["id"]}/"', q6, e["id"])
            if e.get("project_kind") in ("compute-infrastructure", "digital-platform"):
                self.assertNotIn(f'href="/registry/{e["id"]}/"', q6, e["id"])

    def test_operational_ai_application_does_count(self):
        def mutate(o):
            next(e for e in o["entities"] if e["id"] == "deepecho-ultrasound-software")["lifecycle"] = "operational"
        html = self._questions_with(mutate)
        self.assertIn("Sectors with a documented operational or pilot AI application in this registry", html)

    def test_inferred_developer_is_not_listed_as_verified(self):
        html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        q3 = html[html.index('id="q3-h"'):html.index('id="q4-h"')]
        row = q3[q3.index('href="/registry/darijabert/"'):]
        row = row[:row.index("</tr>")]
        self.assertNotIn("/registry/aiox-labs/", row)
        self.assertIn("/registry/insea/", row)

    def test_homepage_acquisition_path(self):
        html = (REPO / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="acquire"', html)
        self.assertIn('href="/acquisition/"', html)
        self.assertIn(f"mailto:{check_site.CONTACT}", html)
        self.assertIn(check_site.DISCLAIMER, html)
        self.assertNotIn("fonts.googleapis.com", html)


def _section(html, sid):
    """The HTML of the <section id=sid> element (sections are not nested on these pages)."""
    start = html.index(f'id="{sid}"')
    return html[start:html.index("</section>", start)]


def _visible(html):
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", html)))


class ReferenceFirstPositioning(unittest.TestCase):
    """Sprint 03.5: the homepage leads with the registry; framing and acquisition are separated and labelled."""

    def setUp(self):
        self.home = (REPO / "index.html").read_text(encoding="utf-8")
        self.evidence, self.ontology = registry.load_all()

    def test_homepage_counts_come_from_the_data(self):
        expected = {"version": self.evidence["version"], "records": len(self.evidence["records"]),
                    "entities": len(self.ontology["entities"]), "relationships": len(self.ontology["relationships"]),
                    "domains": len(self.ontology["domains"]), "entity-types": len(self.ontology["entity_types"])}
        for key, value in expected.items():
            found = re.findall(rf"<!--r:{key}-->(.*?)<!--/r:{key}-->", self.home)
            self.assertTrue(found, key)
            self.assertTrue(all(v == str(value) for v in found), (key, found, value))

    def test_no_stale_hand_written_figures(self):
        text = _visible(self.home)
        self.assertNotIn("v0.1", text)
        self.assertNotIn("seven entity types", text.lower())
        self.assertNotIn("EN · AR · FR · TZM planned", text)

    def test_reading_order_is_reference_first(self):
        order = ['id="top"', 'id="coverage"', 'id="access"', 'id="examples"', 'id="method"', 'id="thesis"', 'id="acquire"']
        positions = [self.home.index(x) for x in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("on the record", _visible(self.home[self.home.index("<h1"):self.home.index("</h1>")]))

    def test_examples_link_to_their_supporting_outputs(self):
        examples = self.home[self.home.index("<!--r:examples-->"):self.home.index("<!--/r:examples-->")]
        self.assertEqual(examples.count('<article class="example"'), 3)
        expectations = {"ex-idarati": ['href="/registry/idarati-ai/"', 'href="/registry/questions/#q6-h"', 'href="/registry/evidence/#MAI-EV-0038"'],
                        "ex-2030": ['href="/registry/morocco-ai-2030/"', 'href="/registry/evidence/#MAI-EV-0011"'],
                        "ex-infra": ['href="/registry/toubkal-supercomputer/"', 'href="/registry/questions/#q5-h"']}
        for qid, links in expectations.items():
            block = examples[examples.index(f'id="{qid}"'):]
            block = block[:block.index("</article>")]
            for link in links:
                self.assertIn(link, block, (qid, link))

    def test_examples_follow_the_evidence_rules(self):
        examples = _visible(self.home[self.home.index("<!--r:examples-->"):self.home.index("<!--/r:examples-->")])
        self.assertIn("Operational (public availability; use not documented)", examples)
        self.assertIn("no usage, accuracy or outcome evidence is recorded", examples)
        self.assertIn("records no target as achieved", examples)
        self.assertIn("no record shows them built or running", examples)
        self.assertNotIn("FDA-approved", self.home)

    def test_strategic_claims_appear_only_as_labelled_framing(self):
        thesis = _section(self.home, "thesis")
        self.assertIn("Framing, not findings.", _visible(thesis))
        outside = _visible(self.home.replace(thesis, ""))
        for term in ("civilization", "civilizational", "inevitable", "scarce", "category anchor", "sovereign reference", "moat"):
            self.assertNotIn(term, outside.lower(), term)

    def test_framing_vocabulary_is_not_presented_as_the_ontology(self):
        thesis = _visible(_section(self.home, "thesis"))
        self.assertIn("They are not part of the registry’s ontology", thesis)
        self.assertNotIn('id="ontology"', self.home)

    def test_homepage_acquisition_section_is_discreet(self):
        acquire = _visible(_section(self.home, "acquire"))
        self.assertLess(len(acquire.split()), 90)
        self.assertIn('href="/acquisition/"', _section(self.home, "acquire"))
        for sales in ("acquirable", "Buyer", "Asset Class", "Category Anchor Domain"):
            self.assertNotIn(sales, _visible(self.home), sales)
        self.assertNotIn("nav-acquire", self.home)

    def test_acquisition_page_separates_assets_from_potential(self):
        page = (REPO / "acquisition" / "index.html").read_text(encoding="utf-8")
        text = _visible(page)
        self.assertIn(f'href="mailto:{check_site.CONTACT}?subject=', page)
        self.assertIn("Owner's view of potential (not established)", text)
        self.assertIn("no interest from any specific party is implied", text)
        self.assertIn("No price, traffic or revenue figures are published", text)
        self.assertIn("no institution has adopted or designated it", text)
        self.assertIn(check_site.DISCLAIMER, text)

    def test_every_page_links_to_acquisition_quietly(self):
        for f in [REPO / "registry" / "index.html", REPO / "methodology" / "index.html", REPO / "registry" / "idarati-ai" / "index.html"]:
            html = f.read_text(encoding="utf-8")
            self.assertIn('href="/acquisition/"', html, f)
            self.assertNotIn("nav-acquire", html, f)

    def test_independence_is_unmistakable_on_the_homepage(self):
        hero = _visible(_section(self.home, "top"))
        self.assertIn("Not affiliated with the Government of Morocco", hero)
        self.assertIn("not endorsed or operated by any institution it lists", hero)

    def test_methodology_explains_limits_and_corrections(self):
        text = _visible((REPO / "methodology" / "index.html").read_text(encoding="utf-8"))
        for heading in ("What the registry documents", "What it does not establish", "How evidence is admitted",
                        "Unsupported, conflicting and outdated claims", "Corrections and reuse", "Changelog"):
            self.assertIn(heading, text)
        self.assertIn("No content or data licence has been declared", text)

    def test_examples_do_not_exceed_their_evidence(self):
        examples = self.home[self.home.index("<!--r:examples-->"):self.home.index("<!--/r:examples-->")]
        text = _visible(examples)
        # Toubkal is general-purpose computing: shown with its basis, never as AI compute in use.
        self.assertNotIn("AI compute", text)
        self.assertIn("Which institutions are documented as connected to computing and data-centre infrastructure?", text)
        self.assertIn("basis: independent listing", text)
        # The only workload statement is the operator's own (MAI-EV-0041): shown with its source and limits.
        self.assertIn("Reported AI workloads (operator-affiliated authors): fine-tuning runs that produced the GemMaroc Moroccan Darija language models (Belkasmi et al.), presented as a benchmark", text)
        self.assertIn("they do not establish the scale, users or outcomes of AI use", text)
        self.assertIn('href="/registry/evidence/#MAI-EV-0041"', examples)
        self.assertIn('href="/registry/evidence/#MAI-EV-0020"', examples)
        # Morocco AI 2030: inclusion rests on a presentation, and project status is not progress toward targets.
        self.assertIn("on the basis of the ministry's presentation", text)
        self.assertIn("A project's status is not a measure of progress toward the quantified targets", text)
        self.assertIn("The source gives no progress figures towards them", text)
        self.assertIn('href="/registry/evidence/#MAI-EV-0013"', examples)

    def test_first_screen_leads_to_answered_questions(self):
        hero = _section(self.home, "top")
        self.assertIn('href="#examples"', hero)
        self.assertLess(self.home.index('id="examples"'), self.home.index('id="thesis"'))

    def test_acquisition_page_states_availability_and_contact_up_front(self):
        page = (REPO / "acquisition" / "index.html").read_text(encoding="utf-8")
        lede = page[page.index('<p class="lede">'):]
        lede = lede[:lede.index("</p>")]
        self.assertIn("available for strategic acquisition", lede)
        self.assertIn(f'href="mailto:{check_site.CONTACT}?subject=', lede)

    def test_changelog_is_marked_as_retrospective_and_separates_review_fixes(self):
        log = registry.load(REPO / "data" / "changelog.json")
        self.assertIn("it was not published alongside each release", log["note"])
        page = _visible((REPO / "methodology" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("Corrections to previously published content", page)
        self.assertIn("Found in pre-release review (never published)", page)
        allowed = {"date", "commit", "pull_request", "title", "version", "records", "entities", "relationships", "changes", "corrections", "review_fixes"}
        for c in log["entries"]:
            self.assertLessEqual(set(c), allowed, c.get("commit") or c.get("pull_request"))

    def test_changelog_matches_the_published_data(self):
        log = registry.load(REPO / "data" / "changelog.json")
        latest = next(c for c in log["entries"] if c.get("version"))
        self.assertEqual((latest["version"], latest["records"], latest["entities"], latest["relationships"]),
                         (self.evidence["version"], len(self.evidence["records"]), len(self.ontology["entities"]),
                          len(self.ontology["relationships"])))
        dates = [c["date"] for c in log["entries"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        page = (REPO / "methodology" / "index.html").read_text(encoding="utf-8")
        for c in log["entries"]:
            if c.get("commit"):
                self.assertRegex(c["commit"], r"^[0-9a-f]{40}$")
                self.assertIn(f'href="{log["repository"]}/commit/{c["commit"]}"', page)
            else:
                self.assertIsInstance(c["pull_request"], int)
                self.assertIn(f'href="{log["repository"]}/pull/{c["pull_request"]}"', page)
        self.assertEqual(latest["date"], self.evidence["as_of"])


GOOD_PAGE = """<!DOCTYPE html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test page</title>
<meta name="description" content="A test page used to exercise the site quality gates in isolation.">
<link rel="canonical" href="https://themoroccoai.com/">
<meta property="og:url" content="https://themoroccoai.com/">
</head><body><main><h1>Title</h1>
<section id="acquire"><a href="mailto:agent@sohadot.com">Contact</a> <a href="/acquisition/">Acquisition</a></section>
<p>Not affiliated with the Government of Morocco</p>
</main></body></html>"""


class GatesCatchRegressions(unittest.TestCase):
    """Run the checker on a throwaway site so each regression is tested in isolation."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "robots.txt").write_text("Sitemap: https://themoroccoai.com/sitemap.xml\n")
        (self.tmp / "sitemap.xml").write_text("<urlset><url><loc>https://themoroccoai.com/</loc></url>"
                                              "<url><loc>https://themoroccoai.com/acquisition/</loc></url></urlset>")
        (self.tmp / "acquisition").mkdir()
        (self.tmp / "acquisition" / "index.html").write_text(
            GOOD_PAGE.replace('href="https://themoroccoai.com/"', 'href="https://themoroccoai.com/acquisition/"')
                     .replace('content="https://themoroccoai.com/"', 'content="https://themoroccoai.com/acquisition/"'), encoding="utf-8")
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

    def test_missing_acquisition_page(self):
        (self.tmp / "acquisition" / "index.html").unlink()
        (self.tmp / "acquisition").rmdir()
        self.assertCaught(GOOD_PAGE, "missing dedicated acquisition page")

    def test_homepage_must_link_to_acquisition_page(self):
        self.assertCaught(GOOD_PAGE.replace(' <a href="/acquisition/">Acquisition</a>', ""), "no link to /acquisition/")

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
