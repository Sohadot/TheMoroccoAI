"""The homepage is generated from tools/templates/homepage.tmpl and the catalogs (Sprint 19B-4).

English output is byte-identical to the committed index.html. A pseudo-locale proves that no visible, metadata or
JSON-LD text is hard-coded. A fully SYNTHETIC localization (temporary directory, synthetic reviewers and approvals,
never committed) proves that the homepage passes every localized gate and that each failure withholds it. The
homepage is not registered for localization: nothing here publishes it.
Run: python3 -m unittest discover -s tests
"""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import i18n  # noqa: E402
from test_extraction import HOMEPAGE, TODAY, ExtractedRegistryFixture, PseudoTranslator, model, residual_words  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
INDEX = (REPO / "index.html").read_text(encoding="utf-8")
# Visible literals that are not translatable: the data format name on two access cards and the language code of the
# current edition in the footer (the other codes are in the catalog text).
LITERALS = {"JSON", "EN"}


def render_en(root=None):
    with build.rendering(build.RenderContext("en", root or REPO, today=TODAY)):
        return build.render_homepage(model())


class EnglishHomepage(unittest.TestCase):
    def test_generated_homepage_is_byte_identical(self):
        self.assertEqual(render_en(), INDEX)
        self.assertEqual(HOMEPAGE.path, "/")
        self.assertNotIn(HOMEPAGE, build.LOCALIZABLE_PAGES)

    def test_markers_and_generated_blocks_are_kept(self):
        for key in ("version", "records", "entities", "relationships", "as-of", "domains", "entity-types", "landscape", "examples"):
            self.assertIn(f"<!--r:{key}-->", INDEX)
            self.assertIn(f"<!--/r:{key}-->", INDEX)

    def test_english_page_carries_no_localization_markup(self):
        for fragment in ("hreflang", "translation-notice", "lang-switch", "og:locale", "inLanguage", "{{", "}}"):
            self.assertNotIn(fragment, INDEX)

    def test_template_has_only_known_tokens_and_no_hard_coded_links(self):
        tmpl = build.HOMEPAGE_TEMPLATE.read_text(encoding="utf-8")
        kinds = {m.group(1) for m in build._TOKEN.finditer(tmpl)}
        self.assertLessEqual(kinds, {"m", "a", "j", "h", "i", "href", "b", "lang", "dir", "canonical", "seo", "ld_extra", "notice", "switcher"})
        # Internal page links go through {{href:...}} or link(); only anchors, data files and mailto stay literal.
        for href in re.findall(r'href="([^"{]+)"', tmpl):
            self.assertTrue(href.startswith(("#", "/data/", "/favicon", "/assets/", "mailto:", "https://")), href)

    def test_unknown_token_stops_the_build(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        bad = root / "homepage.tmpl"
        bad.write_text(build.HOMEPAGE_TEMPLATE.read_text(encoding="utf-8").replace("{{m:page.home.hero.meta}}", "{{x:page.home.hero.meta}}"),
                       encoding="utf-8")
        original = build.HOMEPAGE_TEMPLATE
        build.HOMEPAGE_TEMPLATE = bad
        self.addCleanup(setattr, build, "HOMEPAGE_TEMPLATE", original)
        with self.assertRaises(SystemExit):
            render_en()

    # Negative test 1: a missing English key stops the build (no silent fallback).
    def test_missing_english_key_stops_the_build(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        shutil.copytree(REPO / "i18n", root / "i18n")
        cat = json.loads((root / "i18n/en/messages.json").read_text(encoding="utf-8"))
        cat["messages"] = [m for m in cat["messages"] if m["id"] != "page.home.hero.cta.registry"]
        (root / "i18n/en/messages.json").write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(KeyError):
            render_en(root)

    # Negative test 2: an unintended English change is detected by the byte comparison (and build.py --check).
    def test_changed_english_text_is_detected(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        shutil.copytree(REPO / "i18n", root / "i18n")
        cat = json.loads((root / "i18n/en/messages.json").read_text(encoding="utf-8"))
        for m in cat["messages"]:
            if m["id"] == "page.home.hero.notice":
                m["text"] = m["text"].replace("Not affiliated", "Affiliated")
        (root / "i18n/en/messages.json").write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")
        changed = render_en(root)
        self.assertNotEqual(changed, INDEX)
        self.assertIn("Affiliated with the Government", changed)


class HomepageCompleteness(unittest.TestCase):
    def render_pseudo(self):
        with build.rendering(build.RenderContext("fr", translator=PseudoTranslator())):
            return build.render_homepage(model())

    def test_homepage_has_no_hard_coded_english(self):
        html = self.render_pseudo()
        words, facts = residual_words(html)
        self.assertEqual(words - LITERALS, set())
        self.assertNotRegex(facts.title + (facts.description or ""), r"[A-Za-z]{2,}")
        for attr in re.findall(r'(?:aria-label|content)="([^"]*)"', html):
            if attr not in ("width=device-width, initial-scale=1.0", "website", "TheMoroccoAI", "summary") and not attr.startswith("https://"):
                self.assertNotRegex(attr, r"[A-Za-z]{2,}", attr)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertNotRegex(ld["description"] + ld["hasPart"]["name"], r"[A-Za-z]{2,}")

    def test_the_completeness_check_detects_hard_coded_english(self):
        html = self.render_pseudo().replace("</main>", "<p>Hard coded sentence</p></main>")
        self.assertEqual(residual_words(html)[0] - LITERALS, {"Hard", "coded", "sentence"})

    def test_inventory_covers_shared_vocabulary_and_examples(self):
        req = build.page_requirements(model(), HOMEPAGE)
        for mid in ("page.home.hero.notice", "page.home.ex.2030.targets_qualifier", "vocab.lifecycle.operational",
                    "facts.currency.recent", "shell.skip_link", "disclosure.ownership_statement"):
            self.assertIn(mid, req["messages"])
        self.assertIn("evidence:MAI-EV-0011:claim", req["content"])
        self.assertTrue(any(c.startswith("attribute:attribute.toubkal-supercomputer.") for c in req["content"]), req["content"])
        self.assertTrue(any(c.startswith("predicate:") for c in req["content"]))
        self.assertIn("lifecycle:operational", req["terms"])


class LocalizedHomepage(ExtractedRegistryFixture):
    """SYNTHETIC: every unit the homepage needs is given a synthetic approved translation in a temporary root."""

    SPEC = HOMEPAGE

    def test_homepage_renders_in_both_languages_and_passes_every_gate(self):
        files, clusters, report = self.localize()
        self.assertEqual(report, [])
        self.assertEqual(clusters, {"/": ["en", "ar", "fr"]})
        ar, fr = files["ar/index.html"], files["fr/index.html"]
        self.assertEqual(self.gate("ar", ar), [])
        self.assertEqual(self.gate("fr", fr), [])
        self.assertIn('<html lang="ar" dir="rtl">', ar)
        self.assertIn('<link rel="canonical" href="https://themoroccoai.com/ar/">', ar)
        self.assertIn('<bdi dir="ltr">MAI-ROOT-001</bdi>', ar)
        self.assertIn('hreflang="x-default" href="https://themoroccoai.com/"', ar)
        self.assertIn('"translationOfWork": {"@id": "https://themoroccoai.com/"}', ar)
        json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', ar, re.S).group(1))
        policy = build.escape(self.text("shell.translation_policy", "ar"), quote=False)
        self.assertIn(policy, ar)
        self.assertIn('class="lang-switch"', ar)
        # Untranslated pages are linked in English and say so.
        self.assertIn('href="/registry/" hreflang="en"', ar)

    # Negative test 3: a translated page whose CTA URL differs from English fails the gate.
    def test_changed_cta_url(self):
        html = self.generated("fr").replace('href="/registry/" hreflang="en" class="btn-primary"', 'href="/registre/" hreflang="en" class="btn-primary"')
        self.assertGate("fr", html, "internal links or anchors differ")

    # Negative test 4: a missing disclosure withholds the page.
    def test_missing_disclosure(self):
        html = self.generated("ar")
        notice = build.escape(self.text("page.home.hero.notice", "ar").split("{independent}")[-1].strip(), quote=False)
        self.assertIn(notice, html)
        self.assertGate("ar", html.replace(notice, ""), "page.home.hero.notice")
        cat = self.read("fr/messages.json")
        cat["units"] = [u for u in cat["units"] if u["id"] != "page.home.hero.notice"]
        self.write("fr/messages.json", cat)
        self.assertNotGenerated("page.home.hero.notice", lang="fr")

    # Negative test 5: a changed canonical record (an entity name) makes its translation stale and withholds the page.
    def test_changed_canonical_data(self):
        ontology = json.loads((self.root / "data" / "ontology.json").read_text(encoding="utf-8"))
        for e in ontology["entities"]:
            if e["id"] == "idarati-ai":
                e["name"] = "Idarati AI assistant"
        (self.root / "data" / "ontology.json").write_text(json.dumps(ontology, ensure_ascii=False), encoding="utf-8")  # temporary copy
        self.model = build.Model(json.loads((self.root / "data" / "evidence.json").read_text(encoding="utf-8")), ontology)
        files, clusters, report = build.localize(self.model, [self.SPEC], root=self.root, today=TODAY)
        self.assertNotIn("fr/index.html", files)
        self.assertTrue(any("ontology:idarati-ai:name" in r for r in report), report[:3])

    def test_missing_translation_key(self):
        cat = self.read("ar/messages.json")
        cat["units"] = [u for u in cat["units"] if u["id"] != "page.home.ex.infra.announced"]
        self.write("ar/messages.json", cat)
        self.assertNotGenerated("page.home.ex.infra.announced", lang="ar")

    def test_changed_english_source_makes_the_translation_stale(self):
        cat = self.read("fr/messages.json")
        cat["units"] = [self.unit(u["id"], "fr", source="an older English text") if u["id"] == "page.home.coverage.intro" else u
                        for u in cat["units"]]
        self.write("fr/messages.json", cat)
        self.assertNotGenerated("page.home.coverage.intro", lang="fr")

    def test_altered_identifier_or_number(self):
        html = self.generated("fr")
        self.assertGate("fr", re.sub(r">MAI-EV-0034(?=[ <])", ">MAI-EV-0099", html, count=1), "identifiers differ")
        self.assertGate("fr", re.sub(r"<!--r:records-->\d+", "<!--r:records-->64", html, count=1), "numbers or dates differ")


if __name__ == "__main__":
    unittest.main()
