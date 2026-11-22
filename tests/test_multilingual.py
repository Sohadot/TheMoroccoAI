"""Multilingual rendering engine, publication gates, SEO and right-to-left support (TMA-DEC-007, Sprint 19B-2).

Every localized page here is SYNTHETIC: a test-only page and mechanically generated placeholder "translations"
built in a temporary copy of i18n/. They are not translations, are never committed, and their review records
are fabricated fixtures that exist only to exercise the gates. No real localized page exists or is published.
Run: python3 -m unittest discover -s tests
"""
import datetime
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import check_site  # noqa: E402
import i18n  # noqa: E402
import registry  # noqa: E402
from test_layout import BROWSER  # noqa: E402
from i18n_fixtures import approval, approved_label, approved_unit, register_reviewers  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TODAY = datetime.date(2026, 11, 22)
PATH = "/registry/"  # the synthetic page reuses a real English path so hreflang and routes are realistic
SYNTHETIC_EN = [
    {"id": "test.title", "kind": "prose", "text": "Synthetic registry page"},
    {"id": "test.description", "kind": "prose", "text": "A synthetic page used only to test the multilingual renderer and its gates."},
    {"id": "test.cites", "kind": "prose", "text": "This page cites {evidence} and the source {source} for testing."},
    {"id": "test.qualifier", "kind": "qualifier", "text": "Not verified as delivered."},
    {"id": "test.count", "kind": "prose", "text": "Recorded across {count} evidence records & notes"},
]
WORD = {"ar": "نص", "fr": "texte"}
SOURCE = "https://example.org/source"


def synthetic(text, lang):
    """A placeholder 'translation': keeps placeholders, identifiers, URLs and digits, replaces the words."""
    keep = re.compile(r"\{[a-z_][a-z0-9_]*\}|MAI-[A-Z0-9]+(?:-[A-Z0-9]+)*|https?://\S+|\d+|&")
    parts, last = [], 0
    for m in keep.finditer(text):
        if text[last:m.start()].strip():
            parts.append(WORD[lang])
        parts.append(m.group(0))
        last = m.end()
    if text[last:].strip() or not parts:
        parts.append(WORD[lang])
    return " ".join(parts) + f" ({lang})"


def synthetic_page(model):
    """A page whose every text comes from the catalogs, as a localizable page must."""
    ev = build.iso('<a href="/registry/evidence/#MAI-EV-0001">MAI-EV-0001</a>')
    src = build.iso(f'<a href="{SOURCE}">{SOURCE}</a>')
    term = build._ctx().tr.term("classification:VERIFIED FACT", "VERIFIED FACT")
    body = (f'<h1>{build.msg("test.title")}</h1>\n<p>{build.msg_html("test.cites", evidence=ev, source=src)}</p>\n'
            f'<p class="qualifier">{build.msg("test.qualifier")}</p>\n<p>{build.msg("test.count", count=63)}</p>\n'
            f'<p>{build.human_date("2026-10-20")}</p>\n{build.badge("VERIFIED FACT")} <span>{escape_term(term)}</span>\n'
            f'<p>{build.link("/methodology/", build.msg("footer.link.methodology"))}</p>')
    return build.page(model, path=PATH, title=build.msg("test.title"), description=build.msg("test.description"), body=body)


def escape_term(term):
    return build.escape(term)


SPEC = build.PageSpec(PATH, synthetic_page)


class SyntheticSite(unittest.TestCase):
    """A temporary i18n/ with ar and fr 'published' and synthetic approved units for every message the page uses."""
    states = {"ar": "published", "fr": "published"}

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(REPO / "i18n", self.root / "i18n")
        shutil.copytree(REPO / "data", self.root / "data")  # sources for fingerprints; never modified
        register_reviewers(self.root)  # SYNTHETIC reviewers, temporary directory only
        en = self.read("en/messages.json")
        en["messages"] += SYNTHETIC_EN
        self.write("en/messages.json", en)
        langs = self.read("languages.json")
        for x in langs["languages"]:
            x["state"] = self.states.get(x["code"], x["state"])
        self.write("languages.json", langs)
        self.english = {m["id"]: m["text"] for m in en["messages"]}
        for lang in ("ar", "fr"):
            self.write(f"{lang}/messages.json", {"language": lang, "units": [self.unit(mid, lang) for mid in self.english]})
        glossary = self.read("glossary.json")
        glossary["terms"] = [{"id": "classification:VERIFIED FACT", "translations": {
            "ar": approved_label("classification:VERIFIED FACT", "واقعة متحقق منها (اختبار)", ["رسمي"]),
            "fr": approved_label("classification:VERIFIED FACT", "fait vérifié (essai)", ["officiel"], lang="fr")}}]
        self.write("glossary.json", glossary)
        evidence, ontology = registry.load_all()
        self.model = build.Model(evidence, ontology)

    def unit(self, mid, lang, source=None, **over):
        return approved_unit(mid, "interface", synthetic(self.english[mid], lang), source or self.english[mid], lang=lang, **over)

    def read(self, rel):
        return json.loads((self.root / "i18n" / rel).read_text(encoding="utf-8"))

    def write(self, rel, data):
        (self.root / "i18n" / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def replace_unit(self, lang, mid, **over):
        cat = self.read(f"{lang}/messages.json")
        cat["units"] = [self.unit(u["id"], lang, **over) if u["id"] == mid else u for u in cat["units"]]
        self.write(f"{lang}/messages.json", cat)

    def drop_unit(self, lang, mid):
        cat = self.read(f"{lang}/messages.json")
        cat["units"] = [u for u in cat["units"] if u["id"] != mid]
        self.write(f"{lang}/messages.json", cat)

    def localize(self):
        return build.localize(self.model, [SPEC], root=self.root, today=TODAY)

    def english_with(self, clusters):
        with build.rendering(build.RenderContext("en", self.root, clusters=clusters, today=TODAY)):
            return synthetic_page(self.model)

    def gate(self, lang, html):
        """Publication gates for a (possibly tampered) localized page against the synthetic English page."""
        en_ctx = build.RenderContext("en", self.root, today=TODAY)
        with build.rendering(en_ctx):
            english = synthetic_page(self.model)
        tr = i18n.Translator(lang, self.root, today=TODAY)
        with build.rendering(build.RenderContext(lang, self.root, clusters={PATH: ["en", lang]}, translator=tr)):
            synthetic_page(self.model)
        return build.localized_page_errors(lang, PATH, html, english, tr.used, en_ctx.tr.used, build.load_languages(self.root), tr)

    def rendered(self, lang="ar"):
        files, clusters, report = self.localize()
        self.assertEqual(report, [])
        return files[build.output_path(lang, PATH)]


class RepositoryRendersNothingLocalized(unittest.TestCase):
    def test_no_page_is_registered_and_no_localized_output_exists(self):
        self.assertEqual(build.LOCALIZABLE_PAGES, ())
        evidence, ontology = registry.load_all()
        files, report = build.build_outputs(build.Model(evidence, ontology))
        self.assertEqual(report, [])
        self.assertFalse([p for p in files if p.split("/")[0] in build.RESERVED_LANGUAGE_DIRS])
        self.assertFalse([p for p, c in files.items() if "hreflang" in c or "lang-switch" in c or "translation-notice" in c])
        self.assertEqual(build.cluster_errors(files, build.load_languages()), [])
        self.assertEqual(build.withdrawn_files(REPO, files), [])

    def test_check_mode_flags_a_withdrawn_translation_left_in_the_tree(self):
        stray = REPO / "ar" / "withdrawn-test" / "index.html"
        stray.parent.mkdir(parents=True)
        try:
            stray.write_text("<!DOCTYPE html><title>old</title>", encoding="utf-8")
            self.assertEqual(build.main(["--check"]), 1)
            self.assertEqual(build.withdrawn_files(REPO, {}), ["ar/withdrawn-test/index.html"])
        finally:
            shutil.rmtree(REPO / "ar")


class Rendering(SyntheticSite):
    def test_lang_dir_canonical_and_route(self):
        files, clusters, _ = self.localize()
        self.assertEqual(clusters, {PATH: ["en", "ar", "fr"]})
        ar, fr = files["ar/registry/index.html"], files["fr/registry/index.html"]
        self.assertIn('<html lang="ar" dir="rtl">', ar)
        self.assertIn('<html lang="fr" dir="ltr">', fr)
        self.assertIn('<link rel="canonical" href="https://themoroccoai.com/ar/registry/">', ar)
        self.assertIn('<link rel="canonical" href="https://themoroccoai.com/fr/registry/">', fr)
        self.assertEqual(sorted(files), ["ar/registry/index.html", "fr/registry/index.html"])

    def test_output_is_deterministic(self):
        self.assertEqual(self.localize()[0], self.localize()[0])

    def test_localized_strings_placeholders_and_escaping(self):
        ar = self.rendered("ar")
        self.assertIn(build.escape(synthetic(self.english["test.title"], "ar"), quote=False), ar)
        self.assertIn("63", ar)
        self.assertIn("&amp;", ar)          # '&' in catalog text is escaped
        self.assertIn('<bdi dir="ltr"><a href="/registry/evidence/#MAI-EV-0001">MAI-EV-0001</a></bdi>', ar)  # HTML value kept
        self.assertNotIn(self.english["test.title"], ar)

    def test_canonical_identifiers_urls_and_classification_are_preserved(self):
        ar = self.rendered("ar")
        for token in ("MAI-EV-0001", SOURCE, 'class="badge badge-verified-fact"', "VERIFIED FACT"):
            self.assertIn(token, ar)

    def test_localized_page_carries_disclosures_and_translation_notice(self):
        ar = self.rendered("ar")
        for mid in ("footer.owner_note", "footer.disclaimer", "shell.translation_notice.english"):
            self.assertIn(build.escape(synthetic(self.english[mid], "ar"), quote=False), ar)
        self.assertIn('class="translation-notice"', ar)
        self.assertIn('<a href="/registry/" hreflang="en">', ar)

    def test_links_to_untranslated_pages_go_to_english_and_say_so(self):
        ar = self.rendered("ar")
        self.assertIn('<a href="/methodology/" hreflang="en">', ar)
        self.assertIn('class="lang-note"', ar)
        self.assertIn('href="/ar/registry/"', ar)  # the nav link to a translated page stays in Arabic

    def test_dates_use_the_language_month_names_with_the_same_digits(self):
        ar = self.rendered("ar")
        self.assertIn(synthetic("20", "ar").split()[0], ar)
        self.assertNotIn("October", ar)


class SeoAndSwitcher(SyntheticSite):
    def test_reciprocal_hreflang_with_x_default_to_english(self):
        files, clusters, _ = self.localize()
        english = self.english_with(clusters)
        site = dict(files, **{"registry/index.html": english})
        for html in site.values():
            for lang, href in (("en", "/registry/"), ("ar", "/ar/registry/"), ("fr", "/fr/registry/"), ("x-default", "/registry/")):
                self.assertIn(f'<link rel="alternate" hreflang="{lang}" href="https://themoroccoai.com{href}">', html)
        self.assertEqual(build.cluster_errors(site, build.load_languages(self.root)), [])
        self.assertIn('<meta property="og:locale" content="ar_MA">', files["ar/registry/index.html"])
        self.assertIn('<meta property="og:locale:alternate" content="en_GB">', files["ar/registry/index.html"])

    def test_switcher_lists_only_generated_equivalents_and_marks_the_current_language(self):
        self.drop_unit("fr", "test.qualifier")
        files, clusters, _ = self.localize()
        self.assertEqual(clusters, {PATH: ["en", "ar"]})
        ar = files["ar/registry/index.html"]
        switch = re.search(r'<ul class="lang-switch"[^>]*>(.*?)</ul>', ar).group(1)
        self.assertIn('<a href="/registry/" lang="en" dir="ltr" hreflang="en">English</a>', switch)
        self.assertIn('<a href="/ar/registry/" lang="ar" dir="rtl" hreflang="ar" aria-current="true">العربية</a>', switch)
        self.assertNotIn("/fr/", switch)
        self.assertNotIn("/fr/", self.english_with(clusters))

    def test_switcher_is_plain_keyboard_reachable_links(self):
        ar = self.rendered("ar")
        switch = re.search(r'<ul class="lang-switch"[^>]*>(.*?)</ul>', ar).group(1)
        self.assertEqual(len(re.findall(r"<a href=", switch)), 3)
        self.assertNotIn("tabindex", switch)
        self.assertNotIn("<script", ar)
        self.assertIn('aria-label="', re.search(r'<ul class="lang-switch"[^>]*>', ar).group(0))

    def test_no_switcher_or_alternates_without_a_translation(self):
        html = self.english_with({})
        self.assertNotIn("lang-switch", html)
        self.assertNotIn("hreflang", html)

    def test_sitemap_lists_generated_localized_pages_only(self):
        files, clusters, _ = self.localize()
        sm = build.sitemap(self.model, ["/ar/registry/", "/fr/registry/"])
        self.assertIn("<loc>https://themoroccoai.com/ar/registry/</loc>", sm)
        self.assertNotIn("/zgh/", sm)

    def test_json_ld_language_and_translation_of(self):
        evidence, ontology = registry.load_all()
        with build.rendering(build.RenderContext("ar", self.root, clusters={PATH: ["en", "ar"]}, today=TODAY)):
            html = build.page(self.model, path=PATH, title="t", description="d", body="",
                              jsonld={"@context": "https://schema.org", "@type": "Dataset", "url": build.SITE + PATH})
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(ld["inLanguage"], "ar")
        self.assertEqual(ld["url"], "https://themoroccoai.com/ar/registry/")
        self.assertEqual(ld["translationOfWork"], {"@id": "https://themoroccoai.com/registry/"})


class Eligibility(SyntheticSite):
    def assertNotGenerated(self, lang, fragment):
        files, clusters, report = self.localize()
        self.assertNotIn(build.output_path(lang, PATH), files)
        self.assertNotIn(lang, clusters.get(PATH, []))
        self.assertTrue(any(fragment in r for r in report), report)
        other = [f for f in files if not f.startswith(lang + "/")]
        for html in files.values():
            self.assertNotIn(f'hreflang="{lang}"', html)
            self.assertNotIn(f"/{lang}/registry/", html)
        return other

    def test_missing_translation(self):
        self.drop_unit("ar", "test.qualifier")
        self.assertEqual(self.assertNotGenerated("ar", "no approved, current translation"), ["fr/registry/index.html"])

    def test_unapproved_translation(self):
        self.replace_unit("ar", "test.title", status="DRAFT")
        self.assertNotGenerated("ar", "test.title")

    def test_stale_translation(self):
        self.replace_unit("ar", "footer.disclaimer", source="an older English text")  # approved before English changed
        self.assertNotGenerated("ar", "footer.disclaimer")

    def test_missing_review_record(self):
        self.replace_unit("ar", "test.cites", approval=None)
        self.assertNotGenerated("ar", "test.cites")

    def test_reviewer_not_independent_of_drafter(self):
        self.replace_unit("ar", "test.cites", draft={"method": "human", "by": "synthetic-reviewer-01"})
        self.assertNotGenerated("ar", "test.cites")

    def test_missing_required_terminology(self):
        g = self.read("glossary.json")
        del g["terms"][0]["translations"]["ar"]
        self.write("glossary.json", g)
        self.assertNotGenerated("ar", "glossary term 'classification:VERIFIED FACT'")

    def test_unpublished_language_has_no_route(self):
        langs = self.read("languages.json")
        for x in langs["languages"]:
            if x["code"] == "ar":
                x["state"] = "in-preparation"
        self.write("languages.json", langs)
        files, clusters, report = self.localize()
        self.assertEqual(sorted(files), ["fr/registry/index.html"])
        self.assertNotIn("ar", clusters[PATH])

    def test_withdrawal_removes_previously_published_output(self):
        (self.root / "ar" / "registry").mkdir(parents=True)
        (self.root / "ar" / "registry" / "index.html").write_text("published earlier", encoding="utf-8")
        self.drop_unit("ar", "test.title")
        files, _, _ = self.localize()
        self.assertEqual(build.withdrawn_files(self.root, files), ["ar/registry/index.html"])

    def test_missing_disclosure_fails_the_gate(self):
        ar = self.rendered("ar")
        note = build.escape(synthetic(self.english["footer.owner_note"], "ar"), quote=False)
        self.assertTrue(any("footer.owner_note" in e for e in self.gate("ar", ar.replace(note, ""))))
        self.assertTrue(any("translation notice" in e for e in self.gate("ar", ar.replace('class="translation-notice"', 'class="x"'))))
        self.assertEqual(self.gate("ar", ar), [])


class SeoGates(SyntheticSite):
    def site(self):
        files, clusters, _ = self.localize()
        return dict(files, **{"registry/index.html": self.english_with(clusters)})

    def test_incorrect_canonical(self):
        ar = self.rendered("ar").replace("https://themoroccoai.com/ar/registry/\">\n<meta property=\"og:type\"",
                                         "https://themoroccoai.com/registry/\">\n<meta property=\"og:type\"")
        self.assertTrue(any("canonical" in e for e in self.gate("ar", ar)))

    def test_missing_reciprocal_hreflang(self):
        site = self.site()
        site["fr/registry/index.html"] = site["fr/registry/index.html"].replace(
            '<link rel="alternate" hreflang="ar" href="https://themoroccoai.com/ar/registry/">\n', "")
        self.assertTrue(any("not reciprocal" in e for e in build.cluster_errors(site, build.load_languages(self.root))))

    def test_incorrect_x_default(self):
        site = self.site()
        site["ar/registry/index.html"] = site["ar/registry/index.html"].replace(
            'hreflang="x-default" href="https://themoroccoai.com/registry/"', 'hreflang="x-default" href="https://themoroccoai.com/ar/registry/"')
        self.assertTrue(any("x-default" in e for e in build.cluster_errors(site, build.load_languages(self.root))))

    def test_reference_to_unpublished_route(self):
        site = self.site()
        site["ar/registry/index.html"] = site["ar/registry/index.html"].replace(
            "<meta name=\"twitter:card\"", '<link rel="alternate" hreflang="zgh" href="https://themoroccoai.com/zgh/registry/">\n<meta name="twitter:card"')
        errors = build.cluster_errors(site, build.load_languages(self.root))
        self.assertTrue(any("not generated" in e for e in errors))
        self.assertTrue(any("unpublished languages ['zgh']" in e for e in errors))

    def test_missing_localized_metadata(self):
        ar = re.sub(r"<title>.*?</title>", "<title></title>", self.rendered("ar"))
        self.assertTrue(any("title or meta description" in e for e in self.gate("ar", ar)))


class RightToLeftAndLanguageAttributes(SyntheticSite):
    def test_missing_rtl_direction(self):
        ar = self.rendered("ar").replace('<html lang="ar" dir="rtl">', '<html lang="ar" dir="ltr">')
        self.assertTrue(any('dir="rtl"' in e for e in self.gate("ar", ar)))

    def test_incorrect_language_attribute(self):
        ar = self.rendered("ar").replace('<html lang="ar" dir="rtl">', '<html lang="en" dir="rtl">')
        self.assertTrue(any('lang="ar"' in e for e in self.gate("ar", ar)))

    def test_unisolated_identifiers_in_rtl_text(self):
        ar = self.rendered("ar").replace('<bdi dir="ltr">', "<span>").replace("</bdi>", "</span>")
        self.assertTrue(any("not isolated" in e for e in self.gate("ar", ar)))

    def test_french_needs_no_isolation(self):
        self.assertNotIn("<bdi", self.rendered("fr"))
        self.assertEqual(self.gate("fr", self.rendered("fr")), [])

    def test_arabic_css_never_letter_spaces_or_italicizes_and_uses_the_bundled_font(self):
        css = (REPO / "assets" / "registry.css").read_text(encoding="utf-8")
        rule = re.search(r'html\[lang="ar"\] body \* \{([^}]*)\}', css).group(1)
        self.assertIn("letter-spacing: 0 !important", rule)
        self.assertIn("font-style: normal !important", rule)
        self.assertTrue(rule.strip().startswith("font-family: 'Noto Kufi Arabic'"))
        self.assertIn("font-family: 'Noto Kufi Arabic'", (REPO / "assets" / "fonts" / "fonts.css").read_text(encoding="utf-8"))
        self.assertNotRegex(css, r"(margin|padding|border)-(left|right)|[^-]left:|[^-]right:|text-align: *(left|right)")


class ResearchIntegrityGates(SyntheticSite):
    def assertGate(self, tampered, fragment):
        errors = self.gate("ar", tampered)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_altered_evidence_id(self):
        self.assertGate(self.rendered().replace(">MAI-EV-0001<", ">MAI-EV-0002<"), "identifiers differ")

    def test_altered_source_url(self):
        self.assertGate(self.rendered().replace(f'href="{SOURCE}"', 'href="https://example.org/other"'), "source URLs differ")

    def test_altered_date(self):
        self.assertGate(self.rendered().replace(">20 ", ">21 ", 1), "numbers or dates differ")

    def test_altered_number(self):
        self.assertGate(self.rendered().replace(" 63 ", " 64 ", 1), "numbers or dates differ")

    def test_altered_classification(self):
        self.assertGate(self.rendered().replace("badge-verified-fact", "badge-official-target"), "classification codes differ")

    def test_missing_uncertainty_qualifier(self):
        en_ctx = build.RenderContext("en", self.root, today=TODAY)
        with build.rendering(en_ctx):
            english = synthetic_page(self.model)
        tr = i18n.Translator("ar", self.root, today=TODAY)
        with build.rendering(build.RenderContext("ar", self.root, clusters={PATH: ["en", "ar"]}, translator=tr)):
            html = synthetic_page(self.model)
        used = [m for m in tr.used if m != "test.qualifier"]
        errors = build.localized_page_errors("ar", PATH, html, english, used, en_ctx.tr.used, build.load_languages(self.root), tr)
        self.assertTrue(any("test.qualifier" in e for e in errors), errors)

    def test_english_text_left_in_a_localized_page(self):
        self.assertGate(self.rendered().replace("</main>", f"<p>{self.english['test.description']}</p></main>"), "left untranslated")


class SiteGatesForPublishedLanguages(SyntheticSite):
    """check_site on a temporary site with ar and fr published: language attributes, sitemap and links."""

    def make_site(self):
        files, clusters, _ = self.localize()
        site = self.root
        for p, html in files.items():
            (site / p).parent.mkdir(parents=True, exist_ok=True)
            (site / p).write_text(html, encoding="utf-8")
        (site / "registry").mkdir(exist_ok=True)
        (site / "registry" / "index.html").write_text(self.english_with(clusters), encoding="utf-8")
        stub = '<!DOCTYPE html><html lang="en"><title>x</title><body><h2 id="ownership-h">x</h2><p id="MAI-EV-0001">x</p></body></html>'
        for target in ("methodology", "data", "evaluation", "acquisition", "registry/questions", "registry/matrix",
                       "registry/gaps", "registry/evidence"):
            (site / target).mkdir(parents=True, exist_ok=True)
            (site / target / "index.html").write_text(stub, encoding="utf-8")
        (site / "index.html").write_text(stub, encoding="utf-8")
        shutil.copytree(REPO / "assets", site / "assets")
        shutil.copy(REPO / "favicon.svg", site / "favicon.svg")
        (site / "robots.txt").write_text("Sitemap: https://themoroccoai.com/sitemap.xml\n")
        self._root = check_site.ROOT
        check_site.ROOT = site
        locs = [check_site.url_path(f) for f in check_site.site_pages()]
        (site / "sitemap.xml").write_text("<urlset>" + "".join(f"<url><loc>https://themoroccoai.com{l}</loc></url>" for l in locs) + "</urlset>")
        self.addCleanup(setattr, check_site, "ROOT", self._root)
        return site

    def language_errors(self):
        return [e for e in check_site.check(network=False) if "hreflang" in e or "lang/dir" in e
                or "sitemap" in e or "broken internal link" in e or "not published" in e]

    def test_published_site_passes(self):
        self.make_site()
        self.assertEqual(self.language_errors(), [])

    def test_wrong_language_attribute_under_a_language_route(self):
        site = self.make_site()
        f = site / "ar" / "registry" / "index.html"
        f.write_text(f.read_text(encoding="utf-8").replace('lang="ar" dir="rtl"', 'lang="en" dir="ltr"', 1), encoding="utf-8")
        self.assertTrue(any("lang/dir" in e for e in self.language_errors()))

    def test_localized_page_missing_from_sitemap(self):
        site = self.make_site()
        (site / "sitemap.xml").write_text((site / "sitemap.xml").read_text().replace("<url><loc>https://themoroccoai.com/fr/registry/</loc></url>", ""))
        self.assertTrue(any("fr/registry/index.html is not listed" in e for e in self.language_errors()))

    def test_broken_internal_language_link(self):
        site = self.make_site()
        f = site / "ar" / "registry" / "index.html"
        f.write_text(f.read_text(encoding="utf-8").replace("</main>", '<a href="/ar/methodology/">x</a></main>'), encoding="utf-8")
        self.assertTrue(any("broken internal link /ar/methodology/" in e for e in self.language_errors()))

    def test_non_reciprocal_hreflang_on_the_site(self):
        site = self.make_site()
        f = site / "fr" / "registry" / "index.html"
        f.write_text(f.read_text(encoding="utf-8").replace('<link rel="alternate" hreflang="ar" href="https://themoroccoai.com/ar/registry/">\n', ""), encoding="utf-8")
        self.assertTrue(any("not reciprocal" in e for e in self.language_errors()))


PROBE = """<script>
addEventListener('load', () => setTimeout(() => {
  const scrolls = e => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      if (/(auto|scroll)/.test(getComputedStyle(p).overflowX)) return true; } return false; };
  const W = document.documentElement.clientWidth, out = [];
  for (const e of document.body.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width && (r.right > W + 0.5 || r.left < -0.5) && !scrolls(e) && !e.classList.contains('skip-link'))
      out.push(e.tagName.toLowerCase() + (e.className ? '.' + e.className : ''));
  }
  const links = [...document.querySelectorAll('.lang-switch a')];
  const focus = links.map(a => { a.focus(); const s = getComputedStyle(a);
      return {focused: document.activeElement === a, outline: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0, tab: a.tabIndex}; });
  const p = document.querySelector('h1');
  const ar = document.fonts.check('16px "Noto Kufi Arabic"', 'ع');
  const pre = document.createElement('pre'); pre.id = 'probe';
  pre.textContent = JSON.stringify({width: W, overflow: out.slice(0, 5), count: out.length, focus,
      font: getComputedStyle(p).fontFamily, letterSpacing: getComputedStyle(document.querySelector('.footer-note')).letterSpacing,
      fontStyle: getComputedStyle(document.querySelector('.footer-note')).fontStyle, arabicFontAvailable: ar,
      dir: getComputedStyle(document.body).direction});
  parent.document.body.appendChild(pre);
}, 500));
</script>"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(BROWSER, "no Chromium or Chrome binary found")
class RenderedRightToLeft(SyntheticSite):
    """The synthetic Arabic page in headless Chromium: no overflow on either edge at narrow widths, a keyboard-
    focusable switcher with a visible focus ring, the bundled Arabic font, no letter-spacing or italics."""

    def probe(self, width, lang="ar", tamper=None):
        files, _, _ = self.localize()
        site = self.root / "site"
        shutil.copytree(REPO / "assets", site / "assets", dirs_exist_ok=True)
        html = files[build.output_path(lang, PATH)]
        if tamper:
            html = tamper(html)
        (site / lang / "registry").mkdir(parents=True, exist_ok=True)
        (site / lang / "registry" / "index.html").write_text(html.replace("</body>", PROBE + "</body>"), encoding="utf-8")
        host = site / f"host-{width}.html"
        host.write_text(f'<!DOCTYPE html><html><body style="margin:0"><iframe src="/{lang}/registry/" '
                        f'style="border:0;width:{width}px;height:900px"></iframe></body></html>', encoding="utf-8")
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(site)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            out = subprocess.run([BROWSER, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                                  "--window-size=800,1000", "--virtual-time-budget=5000", "--dump-dom",
                                  f"http://127.0.0.1:{server.server_address[1]}/{host.name}"], capture_output=True, text=True, timeout=90)
        finally:
            server.shutdown()
            server.server_close()
        m = re.search(r'<pre id="probe">(.*?)</pre>', out.stdout, re.S)
        if not m:
            raise AssertionError(f"no probe result: {out.stderr[-400:]}")
        return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))

    def test_arabic_page_at_narrow_and_wide_widths(self):
        for width in (320, 390, 1280):
            with self.subTest(width=width):
                r = self.probe(width)
                self.assertEqual(r["width"], width)
                self.assertEqual(r["dir"], "rtl")
                self.assertEqual(r["count"], 0, f"overflow at {width}px: {r['overflow']}")
                self.assertEqual(len(r["focus"]), 3)
                self.assertTrue(all(f["focused"] and f["outline"] and f["tab"] == 0 for f in r["focus"]), r["focus"])
                self.assertTrue(r["font"].startswith('"Noto Kufi Arabic"'), r["font"])
                self.assertTrue(r["arabicFontAvailable"])
                self.assertEqual(r["letterSpacing"], "normal")
                self.assertEqual(r["fontStyle"], "normal")

    def test_the_probe_detects_rtl_overflow(self):
        r = self.probe(320, tamper=lambda h: h.replace("</main>", '<div style="width:900px;margin-inline-start:-600px">x</div></main>'))
        self.assertGreater(r["count"], 0)

    def test_the_probe_detects_an_unfocusable_switcher(self):
        r = self.probe(390, tamper=lambda h: re.sub(r'(<ul class="lang-switch"[^>]*>.*?)</ul>',
                                                    lambda m: m.group(0).replace("<a href=", '<a tabindex="-1" href='), h, flags=re.S))
        self.assertFalse(all(f["tab"] == 0 for f in r["focus"]))


if __name__ == "__main__":
    unittest.main()
