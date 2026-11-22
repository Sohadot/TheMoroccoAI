"""Translation layer (TMA-DEC-007): validation rules, staleness, eligibility, and the English-only build.

Each validation rule has a negative test on a throwaway copy of i18n/. Passing these tests shows structure,
provenance and parity of placeholders, digits and identifiers; it is not evidence that a translation means
the same as the English, which only the recorded human reviews can establish.
Run: python3 -m unittest discover -s tests
"""
import copy
import datetime
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import check_site  # noqa: E402
import i18n  # noqa: E402
import registry  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TODAY = datetime.date(2026, 11, 22)
REVIEW = {"drafted_by": "translator-ar-01", "draft_method": "machine-assisted", "substantive_reviewer": "reviewer-sub-01",
          "linguistic_reviewer": "reviewer-ar-02", "approved_on": "2026-11-20", "glossary_version": "2026-11-22"}


class Fixture(unittest.TestCase):
    """A copy of i18n/ in a temporary root; canonical data is passed in, never copied or modified."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(REPO / "i18n", self.root / "i18n")
        self.evidence, self.ontology = registry.load_all()
        self.gaps = registry.load(REPO / "data" / "gaps.json")
        self.en = i18n.english_messages(REPO)

    def write(self, rel, data):
        (self.root / "i18n" / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def read(self, rel):
        return json.loads((self.root / "i18n" / rel).read_text(encoding="utf-8"))

    def message_unit(self, uid="footer.as_of", text="بتاريخ {date}", **over):
        unit = {"id": uid, "kind": "interface", "status": "approved", "text": text,
                "source_sha256": i18n.fingerprint(self.en[uid]), "review": dict(REVIEW)}
        unit.update(over)
        return unit

    def content_unit(self, uid="evidence:MAI-EV-0001:title", text="إطلاق رسمي", **over):
        source, _ = i18n.Sources(REPO).content(uid)
        unit = {"id": uid, "kind": "prose", "status": "approved", "text": text,
                "source_sha256": i18n.fingerprint(source), "review": dict(REVIEW)}
        unit.update(over)
        return unit

    def with_units(self, units, kind="messages", lang="ar"):
        self.write(f"{lang}/{kind}.json", {"language": lang, "units": units})

    def validate(self, **data):
        return i18n.validate(self.root, data.get("evidence", self.evidence), data.get("ontology", self.ontology),
                             data.get("gaps", self.gaps), today=TODAY)

    def assertRejected(self, fragment, **data):
        errors, _ = self.validate(**data)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")


class RepositoryState(unittest.TestCase):
    def test_committed_translation_layer_is_valid_and_empty(self):
        errors, report = i18n.validate(today=TODAY)
        self.assertEqual(errors, [])
        self.assertEqual(report, {"stale": [], "orphaned": []})
        for lang in ("ar", "fr"):
            for kind in ("messages", "content"):
                units = json.loads((REPO / "i18n" / lang / f"{kind}.json").read_text(encoding="utf-8"))["units"]
                self.assertEqual(units, [], "no translation is recorded before it is drafted and reviewed")

    def test_only_english_is_authoritative_and_nothing_is_published(self):
        langs = json.loads((REPO / "i18n" / "languages.json").read_text(encoding="utf-8"))["languages"]
        states = {x["code"]: x["state"] for x in langs}
        self.assertEqual(states, {"en": "authoritative", "ar": "in-preparation", "fr": "in-preparation"})
        # Renderers exist for ar and fr (Sprint 19B-2), but rendering is not publication: no language is published.
        self.assertEqual(i18n.RENDERING_LANGUAGES, frozenset({"ar", "fr"}))
        self.assertEqual(check_site.published_languages(), set())

    def test_translation_layer_is_outside_the_canonical_contract(self):
        self.assertTrue(all(not p.startswith("i18n/") for p in build.REFERENCE_INPUTS))
        self.assertTrue(all(not r[0].startswith("i18n/") for r in build.RESOURCES))
        manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("i18n/", json.dumps(manifest))


class EnglishBuildUsesTheCatalog(unittest.TestCase):
    def test_every_message_id_used_by_the_build_exists(self):
        src = (REPO / "tools" / "build.py").read_text(encoding="utf-8")
        used = set(re.findall(r'(?:msg|i18n\.t)\("([a-z0-9_.]+)"', src))
        used |= set(re.findall(r'\("/[^"]*", "(footer\.link\.[a-z]+)"\)', src))
        en = i18n.english_messages()
        self.assertTrue(used)
        self.assertEqual(sorted(used - set(en)), [])
        for month in range(1, 13):
            self.assertIn(f"date.month.{month:02d}", en)

    def test_shell_and_footer_render_the_catalog_text(self):
        evidence, ontology = registry.load_all()
        model = build.Model(evidence, ontology)
        html = build.render_methodology(model, registry.load(REPO / "data" / "changelog.json"))
        en = i18n.english_messages()
        for key in ("shell.skip_link", "shell.nav.registry", "footer.owner_note", "footer.disclaimer",
                    "footer.link.ownership", "footer.link.evaluation"):
            self.assertIn(en[key], html, key)
        self.assertIn(en["disclosure.ownership_statement"], html)
        self.assertEqual(build.OWNERSHIP_STATEMENT, en["disclosure.ownership_statement"])

    def test_dates_do_not_depend_on_strftime_or_locale(self):
        self.assertEqual(build.human_date("2026-10-20"), "20 October 2026")
        self.assertEqual(build.human_date("2026-05"), "May 2026")
        self.assertEqual(build.human_date(""), "Not stated")
        self.assertNotIn(".strftime(", (REPO / "tools" / "build.py").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            build.human_date("2026-02-30")

    def test_build_generates_no_localized_route(self):
        evidence, ontology = registry.load_all()
        files = build.outputs(build.Model(evidence, ontology))
        for code in check_site.RESERVED_LANGUAGE_ROUTES:
            self.assertFalse([p for p in files if p.startswith(code + "/")], code)
            self.assertFalse((REPO / code).exists(), code)
            self.assertNotIn(f"https://themoroccoai.com/{code}/", files["sitemap.xml"])
        self.assertFalse([p for p, c in files.items() if "hreflang" in c])

    def test_t_rejects_unknown_ids_and_placeholder_mismatch(self):
        with self.assertRaises(KeyError):
            i18n.t("no.such.message")
        with self.assertRaises(KeyError):
            i18n.t("footer.as_of")
        with self.assertRaises(KeyError):
            i18n.t("footer.as_of", date="x", extra="y")


class ValidUnits(Fixture):
    def test_approved_message_and_content_units_validate_and_render(self):
        self.with_units([self.message_unit()])
        self.with_units([self.content_unit()], kind="content")
        self.assertEqual(self.validate(), ([], {"stale": [], "orphaned": []}))
        self.assertEqual(i18n.renderable_units("ar", self.root, self.evidence, self.ontology, self.gaps),
                         {"footer.as_of", "evidence:MAI-EV-0001:title"})

    def test_a_language_that_is_not_published_has_no_eligible_page(self):
        self.with_units([self.message_unit()])
        eligible, missing = i18n.page_eligibility("ar", {"footer.as_of"}, self.root, self.evidence, self.ontology, self.gaps)
        self.assertFalse(eligible)
        self.assertEqual(missing, ["footer.as_of"])


class LanguageRegistryRules(Fixture):
    def mutate(self, change):
        data = self.read("languages.json")
        change(data["languages"])
        self.write("languages.json", data)

    def test_invalid_language_code(self):
        self.mutate(lambda ls: ls[1].update(code="Arabic"))
        self.assertRejected("invalid language code")

    def test_bcp47_must_match_code(self):
        self.mutate(lambda ls: ls[1].update(bcp47="fr"))
        self.assertRejected("does not match code")

    def test_english_must_be_authoritative(self):
        self.mutate(lambda ls: ls[0].update(state="published"))
        self.assertRejected("English must be 'authoritative'")

    def test_only_english_may_be_authoritative(self):
        self.mutate(lambda ls: ls[1].update(state="authoritative"))
        self.assertRejected("only English may be authoritative")

    def test_unknown_state(self):
        self.mutate(lambda ls: ls[1].update(state="live"))
        self.assertRejected("unknown state")

    def test_route_must_match_code(self):
        self.mutate(lambda ls: ls[1].update(route="/arabic/"))
        self.assertRejected("route must be '/ar/'")

    def test_duplicate_language(self):
        self.mutate(lambda ls: ls.append(copy.deepcopy(ls[1])))
        self.assertRejected("duplicate language codes")

    def test_cannot_publish_without_a_renderer(self):
        # Darija has no renderer: registering it as published must fail (ar and fr have renderers since 19B-2).
        self.mutate(lambda ls: ls.append({"code": "ary", "bcp47": "ary", "script": "Arab", "dir": "rtl", "native_name": "الدارجة",
                                          "state": "published", "route": "/ary/", "og_locale": "ary_MA"}))
        (self.root / "i18n" / "ary").mkdir()
        self.assertRejected("'ary' cannot be 'published'")

    def test_og_locale_must_match_the_language(self):
        self.mutate(lambda ls: ls[1].update(og_locale="fr_MA"))
        self.assertRejected("og_locale")

    def test_unregistered_language_directory(self):
        (self.root / "i18n" / "es").mkdir()
        self.assertRejected("i18n/es/: language is not registered")


class EnglishCatalogRules(Fixture):
    def mutate(self, change):
        data = self.read("en/messages.json")
        change(data["messages"])
        self.write("en/messages.json", data)

    def test_duplicate_english_id(self):
        self.mutate(lambda ms: ms.append(dict(ms[0])))
        self.assertRejected("duplicate message id")

    def test_invalid_english_id(self):
        self.mutate(lambda ms: ms[0].update(id="Skip Link"))
        self.assertRejected("invalid message id")

    def test_markup_in_english_text(self):
        self.mutate(lambda ms: ms[0].update(text="<b>Skip</b>"))
        self.assertRejected("markup is not allowed")


class UnitRules(Fixture):
    def test_unknown_status(self):
        self.with_units([self.message_unit(status="done")])
        self.assertRejected("unknown status")

    def test_unapproved_unit_cannot_be_committed(self):
        self.with_units([self.message_unit(status="draft")])
        self.assertRejected("is not publishable; drafts stay off main")

    def test_duplicate_translation_id(self):
        self.with_units([self.message_unit(), self.message_unit()])
        self.assertRejected("duplicate translation id")

    def test_missing_source_fingerprint(self):
        unit = self.message_unit()
        del unit["source_sha256"]
        self.with_units([unit])
        self.assertRejected("missing or invalid source_sha256")

    def test_malformed_content_reference(self):
        self.with_units([self.content_unit(id="evidence:MAI-EV-0001:source_url")], kind="content")
        self.assertRejected("not a translatable canonical field")

    def test_unknown_kind_and_name_basis(self):
        self.with_units([self.message_unit(kind="banner")])
        self.assertRejected("unknown kind")
        self.with_units([self.content_unit(id="ontology:um6p:name", kind="name")], kind="content")
        self.assertRejected("needs name_basis")

    def test_stale_translation_is_reported_not_rendered_and_not_an_error(self):
        self.with_units([self.message_unit(source_sha256=i18n.fingerprint("an older English text"))])
        errors, report = self.validate()
        self.assertEqual(errors, [])
        self.assertEqual(report["stale"], ["ar:footer.as_of"])
        self.assertEqual(i18n.renderable_units("ar", self.root, self.evidence, self.ontology, self.gaps), set())

    def test_changed_english_source_makes_a_content_unit_stale(self):
        self.with_units([self.content_unit()], kind="content")
        evidence = copy.deepcopy(self.evidence)
        evidence["records"][0]["title"] += " (revised)"
        errors, report = self.validate(evidence=evidence)
        self.assertEqual(errors, [])
        self.assertEqual(report["stale"], ["ar:evidence:MAI-EV-0001:title"])
        self.assertEqual(i18n.renderable_units("ar", self.root, evidence, self.ontology, self.gaps), set())

    def test_removed_record_orphans_its_translation_without_blocking_english(self):
        self.with_units([self.content_unit()], kind="content")
        evidence = copy.deepcopy(self.evidence)
        evidence["records"] = [r for r in evidence["records"] if r["evidence_id"] != "MAI-EV-0001"]
        errors, report = self.validate(evidence=evidence)
        self.assertEqual(errors, [])
        self.assertEqual(report["orphaned"], ["ar:evidence:MAI-EV-0001:title"])


class ReviewRules(Fixture):
    def review(self, **over):
        r = dict(REVIEW)
        r.update(over)
        return r

    def test_approved_unit_needs_a_review_record(self):
        unit = self.message_unit()
        del unit["review"]
        self.with_units([unit])
        self.assertRejected("approved unit has no review record")

    def test_reviewers_must_be_pseudonymous(self):
        for value in ("Jane Doe", "jane@example.com", "reviewer"):
            self.with_units([self.message_unit(review=self.review(linguistic_reviewer=value))])
            self.assertRejected("must be a pseudonymous identifier")

    def test_reviewers_must_be_independent_of_the_drafter(self):
        self.with_units([self.message_unit(review=self.review(substantive_reviewer="translator-ar-01"))])
        self.assertRejected("must be independent of the drafter")

    def test_one_reviewer_may_perform_both_reviews_if_not_the_drafter(self):
        self.with_units([self.message_unit(review=self.review(substantive_reviewer="reviewer-ar-02"))])
        self.assertEqual(self.validate()[0], [])

    def test_draft_method_is_declared(self):
        self.with_units([self.message_unit(review=self.review(draft_method="unknown"))])
        self.assertRejected("draft_method must be one of")

    def test_approval_date_is_valid_and_not_in_the_future(self):
        self.with_units([self.message_unit(review=self.review(approved_on="2027-01-01"))])
        self.assertRejected("approved_on is in the future")
        self.with_units([self.message_unit(review=self.review(approved_on="soon"))])
        self.assertRejected("approved_on must be an ISO date")

    def test_no_extra_personal_fields(self):
        self.with_units([self.message_unit(review=self.review(email="someone@example.com"))])
        self.assertRejected("unexpected review fields")


class TextRules(Fixture):
    def test_unicode_must_be_nfc(self):
        self.with_units([self.message_unit(uid="footer.link.data", text="Données")])
        self.assertRejected("not Unicode NFC")

    def test_bidirectional_controls_are_prohibited(self):
        for ch in ("‮", "⁧", "‏", "​"):
            self.with_units([self.message_unit(text=f"بتاريخ {ch}{{date}}")])
            self.assertRejected("prohibited invisible or bidirectional control characters")

    def test_zero_width_joiners_are_allowed(self):
        self.with_units([self.message_unit(text="بتاريخ‌ {date}")])
        self.assertEqual(self.validate()[0], [])

    def test_markup_is_not_allowed_in_translations(self):
        self.with_units([self.message_unit(text="<b>بتاريخ</b> {date}")])
        self.assertRejected("markup is not allowed")

    def test_placeholders_must_match_the_english_source(self):
        self.with_units([self.message_unit(text="بتاريخ {day}")])
        self.assertRejected("placeholders")
        self.with_units([self.message_unit(text="بتاريخ")])
        self.assertRejected("placeholders")

    def test_numbers_keep_western_digits_and_cannot_be_added(self):
        self.with_units([self.message_unit(text="بتاريخ {date} ٢٠٢٦")])
        self.assertRejected("Arabic-Indic digits")
        self.with_units([self.message_unit(text="بتاريخ {date} 2026")])
        self.assertRejected("do not occur in the English source")

    def test_identifiers_and_urls_cannot_change(self):
        source = "See MAI-EV-0001 at https://example.org/a"
        en = self.read("en/messages.json")
        en["messages"].append({"id": "test.identifiers", "kind": "prose", "text": source})
        self.write("en/messages.json", en)
        base = {"id": "test.identifiers", "kind": "prose", "status": "approved",
                "source_sha256": i18n.fingerprint(source), "review": dict(REVIEW)}
        for text in ("انظر MAI-EV-0002 في https://example.org/a", "انظر MAI-EV-0001", "انظر MAI-EV-0001 في https://example.org/b"):
            self.with_units([dict(base, text=text)])
            self.assertRejected("identifiers or URLs differ")
        self.with_units([dict(base, text="انظر MAI-EV-0001 في https://example.org/a")])
        self.assertEqual(self.validate()[0], [])


class GlossaryRules(Fixture):
    def term(self, **over):
        t = {"id": "classification:VERIFIED FACT", "translations": {"ar": {"label": "واقعة متحقق منها", "status": "approved",
                                                                          "forbidden": ["رسمي"]}}}
        t.update(over)
        return t

    def with_terms(self, terms):
        g = self.read("glossary.json")
        g["terms"] = terms
        self.write("glossary.json", g)

    def test_valid_term(self):
        self.with_terms([self.term()])
        self.assertEqual(self.validate()[0], [])

    def test_term_must_name_canonical_vocabulary(self):
        self.with_terms([self.term(id="classification:PROVEN")])
        self.assertRejected("does not name canonical vocabulary")
        self.with_terms([self.term(id="slogan:independent")])
        self.assertRejected("does not name canonical vocabulary")

    def test_duplicate_term(self):
        self.with_terms([self.term(), self.term()])
        self.assertRejected("duplicate term id")

    def test_unapproved_term_label(self):
        self.with_terms([self.term(translations={"ar": {"label": "واقعة", "status": "draft", "forbidden": []}})])
        self.assertRejected("is not approved")

    def test_term_for_unregistered_language(self):
        self.with_terms([self.term(translations={"es": {"label": "hecho", "status": "approved", "forbidden": []}})])
        self.assertRejected("not a registered translation language")

    def test_label_cannot_contain_its_forbidden_variant(self):
        self.with_terms([self.term(translations={"ar": {"label": "واقعة رسمية", "status": "approved", "forbidden": ["رسمي"]}})])
        self.assertRejected("contains its own forbidden variant")

    def test_units_cannot_use_a_forbidden_variant(self):
        self.with_terms([self.term()])
        self.with_units([self.message_unit(text="سجل رسمي {date}")])
        self.assertRejected("forbidden glossary variant")


GOOD_PAGE = """<!DOCTYPE html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test page</title>
<meta name="description" content="A test page used to exercise the site quality gates in isolation.">
<link rel="canonical" href="https://themoroccoai.com/">
<meta property="og:url" content="https://themoroccoai.com/">
</head><body><main><h1>Title</h1>
<section id="acquire"><a href="mailto:agent@sohadot.com">Contact</a> <a href="/acquisition/">Acquisition</a></section>
<p>Not affiliated with the Government of Morocco · Owned and operated by Sohadot</p>
<p>""" + check_site.OWNERSHIP_STATEMENT + """</p>
</main></body></html>"""


class LanguageRouteGates(unittest.TestCase):
    """check_site: no route for an unpublished language, and hreflang only to published, existing pages."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "robots.txt").write_text("Sitemap: https://themoroccoai.com/sitemap.xml\n")
        (self.tmp / "sitemap.xml").write_text("<urlset><url><loc>https://themoroccoai.com/</loc></url>"
                                              "<url><loc>https://themoroccoai.com/acquisition/</loc></url></urlset>")
        (self.tmp / "acquisition").mkdir()
        (self.tmp / "acquisition" / "index.html").write_text(
            GOOD_PAGE.replace('"https://themoroccoai.com/"', '"https://themoroccoai.com/acquisition/"'), encoding="utf-8")
        shutil.copytree(REPO / "i18n", self.tmp / "i18n")
        self._root = check_site.ROOT
        check_site.ROOT = self.tmp
        self.addCleanup(setattr, check_site, "ROOT", self._root)

    def errors(self, page=GOOD_PAGE):
        (self.tmp / "index.html").write_text(page, encoding="utf-8")
        return check_site.check(network=False)

    def test_fixture_is_clean(self):
        self.assertEqual(self.errors(), [])

    def test_route_for_unpublished_language(self):
        for code in ("ar", "fr", "zgh"):
            (self.tmp / code).mkdir()
            self.assertTrue(any(e.startswith(f"{code}/: route for a language that is not published") for e in self.errors()), code)
            shutil.rmtree(self.tmp / code)

    def test_hreflang_to_unpublished_language(self):
        page = GOOD_PAGE.replace("</head>", '<link rel="alternate" hreflang="ar" href="/ar/"></head>')
        self.assertTrue(any("points to an unpublished language" in e for e in self.errors(page)))

    def test_hreflang_to_missing_page(self):
        page = GOOD_PAGE.replace("</head>", '<link rel="alternate" hreflang="x-default" href="/nowhere/"></head>')
        self.assertTrue(any("points to a missing page" in e for e in self.errors(page)))


if __name__ == "__main__":
    unittest.main()
