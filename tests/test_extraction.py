"""Sprint 19B-3: /registry/ and /methodology/ presentation text extracted into i18n/en/messages.json.

What these tests establish:
- the English pages are byte-identical to the committed output (and every other generated file is unchanged:
  test_site.PublishedSite.test_generated_files_are_up_to_date);
- every piece of visible text on both pages comes from the catalogs or canonical data, except the deferred
  canonical changelog records on /methodology/ (pseudo-localization below);
- the engine knows the complete set of units each page needs, and the real /registry/ page renders through
  the multilingual engine and its gates;
- the gates reject the defects listed in the sprint brief.

Localized renderings here are SYNTHETIC: placeholder text generated in temporary directories, with fabricated
pseudonymous review records that exist only to exercise the gates. They are not translations, are never
committed, and nothing is published (LOCALIZABLE_PAGES stays empty).
Run: python3 -m unittest discover -s tests
"""
import datetime
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
import check_site  # noqa: E402
import i18n  # noqa: E402
import registry  # noqa: E402
from test_multilingual import synthetic  # noqa: E402
from i18n_fixtures import approved_label, approved_unit, register_reviewers  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TODAY = datetime.date(2026, 11, 22)
REGISTRY, METHODOLOGY = build.EXTRACTED_PAGES
CHANGELOG = registry.load(REPO / "data" / "changelog.json")


def model():
    evidence, ontology = registry.load_all()
    return build.Model(evidence, ontology)


class EnglishParity(unittest.TestCase):
    def test_extracted_pages_are_byte_identical_to_the_committed_output(self):
        m = model()
        self.assertEqual(REGISTRY.render(m), (REPO / "registry" / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(METHODOLOGY.render(m), (REPO / "methodology" / "index.html").read_text(encoding="utf-8"))

    def test_label_maps_are_derived_from_the_catalog_with_the_same_values_and_order(self):
        en = i18n.english_messages()
        self.assertEqual(list(build.TYPE_LABELS), list(build.ENTITY_TYPE_ORDER))
        self.assertEqual(build.TYPE_LABELS["legal_instrument"], "Legal instruments")
        self.assertEqual(build.SOURCE_TYPE_LABELS["organization_website"], "Organisation's own website")
        for k in build.ENTITY_TYPE_ORDER:
            self.assertEqual(build.TYPE_SINGULAR[k], en[f"vocab.entity_type.{k}.singular"])
        self.assertEqual(set(build.SOURCE_TYPE_LABELS), set(registry.SOURCE_TYPES))

    def test_conditional_empty_domain_branch_keeps_its_wording(self):
        # Not rendered with the current data, so byte parity cannot cover it: check the exact English output.
        evidence, ontology = registry.load_all()
        for e in ontology["entities"]:
            if e.get("domain") == "funding-partnerships":
                e.pop("domain")
        html = REGISTRY.render(build.Model(evidence, ontology))
        cell = html[html.index('id="domain-funding-partnerships"'):]
        cell = cell[:cell.index("</div>")]
        self.assertIn('<p class="coverage-count">0 entities</p>', cell)
        self.assertIn('<p class="coverage-gap">No record has been verified for this domain yet. It stays empty rather than '
                      'holding unsourced entries.</p>', cell)

    def test_a_changed_english_message_changes_the_output_and_is_detected(self):
        # The guard against unintended English change is the byte comparison above (and build.py --check in CI):
        # editing one catalog text must produce different output.
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        shutil.copytree(REPO / "i18n", root / "i18n")
        shutil.copytree(REPO / "data", root / "data")
        cat = json.loads((root / "i18n" / "en" / "messages.json").read_text(encoding="utf-8"))
        for m in cat["messages"]:
            if m["id"] == "page.registry.legend.note":
                m["text"] = m["text"].replace("never shown as an outcome", "rarely shown as an outcome")
        (root / "i18n" / "en" / "messages.json").write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")
        with build.rendering(build.RenderContext("en", root)):
            changed = REGISTRY.render(model())
        self.assertNotEqual(changed, (REPO / "registry" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("rarely shown as an outcome", changed)


class PseudoTranslator(i18n.Translator):
    """Replaces every ASCII letter of every catalog and canonical text (placeholders kept). Any ASCII word left
    on the page was therefore not read from the catalogs or canonical data: it is hard-coded."""

    def __init__(self):
        super().__init__("en")
        self.lang = "fr"
        self.texts = {k: self.pseudo(v) for k, v in self.english.items()}

    @staticmethod
    def pseudo(text):
        parts = re.split(r"(\{[a-z_][a-z0-9_]*\})", text)
        return "".join(p if re.fullmatch(r"\{[a-z_][a-z0-9_]*\}", p) else re.sub(r"[A-Za-z]", "ẋ", p) for p in parts)

    def content(self, unit_id, english):
        self.used.append(unit_id)
        return self.pseudo(english)

    def term(self, term_id, english):
        self.terms_used.append(term_id)
        return self.pseudo(english)


# Visible tokens that are not translatable: identifiers, file paths and code, the contact address, the brand,
# canonical classification codes, commit references and the native names of languages.
NON_TRANSLATABLE = re.compile(r"MAI-[A-Z0-9-]+|/[\w./#-]+|[\w.]+@[\w.]+|TheMoroccoAI(?:\.com)?|evidence\.json|ontology\.json|"
                              r"VERIFIED FACT|OFFICIAL TARGET|ANNOUNCED PLAN|UNVERIFIED CLAIM|INDEPENDENT ANALYSIS|\b[0-9a-f]{7}\b")


def residual_words(html):
    facts = build._facts(html)
    text = NON_TRANSLATABLE.sub(" ", facts.visible)
    return set(re.findall(r"[A-Za-z]{2,}", text)), facts


class CompleteExtraction(unittest.TestCase):
    def render_pseudo(self, spec):
        tr = PseudoTranslator()
        with build.rendering(build.RenderContext("fr", translator=tr)):
            return spec.render(model())

    def test_registry_page_has_no_hard_coded_english(self):
        html = self.render_pseudo(REGISTRY)
        words, facts = residual_words(html)
        self.assertEqual(words, set())
        self.assertNotRegex(facts.title + (facts.description or ""), r"[A-Za-z]{2,}")
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        for value in (ld["name"], ld["description"], ld["spatialCoverage"]["name"]):
            self.assertNotRegex(value, r"[A-Za-z]{2,}")

    def test_methodology_has_no_hard_coded_english(self):
        # Since Sprint 19B-4 the changelog records render through their stable identities, so nothing is deferred.
        words, facts = residual_words(self.render_pseudo(METHODOLOGY))
        self.assertEqual(words, set())
        self.assertNotRegex(facts.title + (facts.description or ""), r"[A-Za-z]{2,}")

    def test_the_completeness_check_detects_hard_coded_english(self):
        html = self.render_pseudo(REGISTRY).replace("</main>", "<p>Hard coded sentence</p></main>")
        self.assertEqual(residual_words(html)[0], {"Hard", "coded", "sentence"})


class RequirementsContract(unittest.TestCase):
    def test_requirements_are_complete_deterministic_and_resolvable(self):
        m = model()
        en = i18n.english_messages()
        sources = i18n.Sources()
        for spec in build.EXTRACTED_PAGES:
            req = build.page_requirements(m, spec)
            self.assertEqual(req, build.page_requirements(m, spec))
            self.assertEqual([x for x in req["messages"] if x not in en], [])
            self.assertEqual([x for x in req["content"] if sources.content(x)[0] is None], [], spec.path)
            tr = PseudoTranslator()
            with build.rendering(build.RenderContext("fr", translator=tr)):
                spec.render(m)
            # A localized rendering uses exactly the page's requirements plus localization-only shell messages.
            self.assertEqual(sorted(set(tr.used) - build.LOCALIZATION_ONLY_MESSAGES), sorted(set(req["messages"]) | set(req["content"])), spec.path)
        reg = build.page_requirements(m, REGISTRY)
        self.assertEqual(len([c for c in reg["content"] if c.endswith(":name")]), len(m.entities))
        self.assertIn("classification:VERIFIED FACT:definition", reg["content"])
        self.assertIn("domain:government-policy:label", reg["content"])
        self.assertIn("page.registry.legend.note", reg["messages"])
        self.assertEqual(reg["terms"], sorted(f"entity_type:{k}" for k in build.ENTITY_TYPE_ORDER))

    def test_canonical_text_is_resolved_from_data_never_copied_into_the_catalog(self):
        en = json.dumps(i18n.english_messages(), ensure_ascii=False)
        m = model()
        for e in m.entities.values():
            if e.get("status") and len(e["status"]) > 40:
                self.assertNotIn(e["status"], en)
        for definition in m.evidence["classifications"].values():
            self.assertNotIn(definition, en)
        for label in m.domains.values():
            self.assertNotIn(label, en)
        sources = i18n.Sources()
        self.assertEqual(sources.content("classification:VERIFIED FACT:definition")[0], m.evidence["classifications"]["VERIFIED FACT"])
        self.assertEqual(sources.content("domain:government-policy:label")[0], m.domains["government-policy"])
        self.assertEqual(sources.content("classification:NOT A CODE:definition"), (None, "orphan"))
        self.assertEqual(sources.content("domain:government-policy:definition"), (None, "malformed"))

    def test_nothing_is_registered_for_localization(self):
        self.assertEqual(build.LOCALIZABLE_PAGES, ())
        files, report = build.build_outputs(model())
        self.assertFalse([p for p in files if p.split("/")[0] in build.RESERVED_LANGUAGE_DIRS])


class ExtractedRegistryFixture(unittest.TestCase):
    """A temporary i18n/ with ar and fr published and synthetic approved units for every unit /registry/ needs."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(REPO / "i18n", self.root / "i18n")
        shutil.copytree(REPO / "data", self.root / "data")  # read-only sources for fingerprints
        register_reviewers(self.root)  # SYNTHETIC reviewers, temporary directory only
        langs = self.read("languages.json")
        for x in langs["languages"]:
            if x["code"] in ("ar", "fr"):
                x["state"] = "published"
        self.write("languages.json", langs)
        self.model = model()
        self.req = build.page_requirements(self.model, REGISTRY, self.root)
        self.sources = i18n.Sources(self.root)
        self.messages = sorted(set(self.req["messages"]) | build.LOCALIZATION_ONLY_MESSAGES)
        for lang in ("ar", "fr"):
            self.write(f"{lang}/messages.json", {"language": lang, "units": [self.unit(mid, lang) for mid in self.messages]})
            self.write(f"{lang}/content.json", {"language": lang, "units": [self.unit(cid, lang) for cid in self.req["content"]]})
        g = self.read("glossary.json")
        g["terms"] = [{"id": t, "translations": {lang: approved_label(t, synthetic(t.split(":")[1], lang)) for lang in ("ar", "fr")}}
                      for t in self.req["terms"]]
        self.write("glossary.json", g)

    def source(self, uid):
        return self.sources.message(uid) if ":" not in uid else self.sources.content(uid)[0]

    @staticmethod
    def tag(uid):
        """A distinct, digit-free marker per unit, so a test can remove exactly one unit's text."""
        return "".join(chr(ord("a") + int(c, 16) % 26) for c in i18n.fingerprint(uid)[:8])

    def text(self, uid, lang):
        return synthetic(self.source(uid), lang) + " " + self.tag(uid)

    def unit(self, uid, lang, source=None, **over):
        kind = "interface" if ":" not in uid else "prose"
        if uid.endswith(":name"):
            kind = "name"
            over.setdefault("name_basis", "transliteration")
        text = over.pop("text", None) or self.text(uid, lang)
        return approved_unit(uid, kind, text, source or self.source(uid), **over)

    def read(self, rel):
        return json.loads((self.root / "i18n" / rel).read_text(encoding="utf-8"))

    def write(self, rel, data):
        (self.root / "i18n" / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def edit_unit(self, lang, uid, **over):
        kind = "content" if ":" in uid else "messages"
        cat = self.read(f"{lang}/{kind}.json")
        cat["units"] = [self.unit(u["id"], lang, **over) if u["id"] == uid else u for u in cat["units"]]
        self.write(f"{lang}/{kind}.json", cat)

    def localize(self):
        return build.localize(self.model, [REGISTRY], root=self.root, today=TODAY)

    def generated(self, lang="ar"):
        files, clusters, report = self.localize()
        self.assertEqual(report, [], report[:3])
        return files[f"{lang}/registry/index.html"]

    def gate(self, lang, html):
        en_ctx = build.RenderContext("en", self.root, today=TODAY)
        with build.rendering(en_ctx):
            english = REGISTRY.render(self.model)
        tr = i18n.Translator(lang, self.root, today=TODAY)
        with build.rendering(build.RenderContext(lang, self.root, clusters={"/registry/": ["en", lang]}, translator=tr)):
            REGISTRY.render(self.model)
        return build.localized_page_errors(lang, "/registry/", html, english, tr.used, en_ctx.tr.used,
                                           build.load_languages(self.root), tr)

    def assertGate(self, lang, html, fragment):
        errors = self.gate(lang, html)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def assertNotGenerated(self, fragment, lang="ar"):
        files, clusters, report = self.localize()
        self.assertNotIn(f"{lang}/registry/index.html", files)
        self.assertNotIn(lang, clusters.get("/registry/", []))
        self.assertTrue(any(fragment in r for r in report), report[:5])


class RealPageThroughTheEngine(ExtractedRegistryFixture):
    def test_registry_renders_in_both_languages_and_passes_every_gate(self):
        files, clusters, report = self.localize()
        self.assertEqual(report, [])
        self.assertEqual(clusters, {"/registry/": ["en", "ar", "fr"]})
        ar, fr = files["ar/registry/index.html"], files["fr/registry/index.html"]
        self.assertIn('<html lang="ar" dir="rtl">', ar)
        self.assertEqual(self.gate("ar", ar), [])
        self.assertEqual(self.gate("fr", fr), [])
        # Canonical identifiers survive inside canonical prose and are isolated in right-to-left text.
        self.assertIn('<bdi dir="ltr">MAI-EV-0048</bdi>', ar)
        self.assertEqual(len(re.findall(r'href="/registry/[a-z0-9-]+/"', ar)), len(re.findall(r'href="/registry/[a-z0-9-]+/"', REGISTRY.render(self.model))))

    def test_validator_accepts_the_synthetic_catalogs(self):
        errors, report = i18n.validate(self.root, today=TODAY)
        self.assertEqual(errors, [])
        self.assertEqual(report, {"stale": [], "orphaned": []})


class NegativeRegressions(ExtractedRegistryFixture):
    # 1
    def test_missing_translation_key(self):
        cat = self.read("ar/messages.json")
        cat["units"] = [u for u in cat["units"] if u["id"] != "page.registry.coverage.h2"]
        self.write("ar/messages.json", cat)
        self.assertNotGenerated("page.registry.coverage.h2")
        self.assertIn("fr/registry/index.html", self.localize()[0])

    # 2
    def test_duplicate_translation_key(self):
        cat = self.read("fr/messages.json")
        cat["units"].append(cat["units"][0])
        self.write("fr/messages.json", cat)
        errors, _ = i18n.validate(self.root, today=TODAY)
        self.assertTrue(any("duplicate translation id" in e for e in errors))

    # 3 — and only the changed unit is invalidated
    def test_changed_source_fingerprint_invalidates_only_that_unit(self):
        en = self.read("en/messages.json")
        for m in en["messages"]:
            if m["id"] == "page.registry.legend.note":
                m["text"] += " (revised)"
        self.write("en/messages.json", en)
        errors, report = i18n.validate(self.root, today=TODAY)
        self.assertEqual(errors, [])
        self.assertEqual(report["stale"], ["ar:page.registry.legend.note", "fr:page.registry.legend.note"])
        renderable = i18n.renderable_units("ar", self.root, today=TODAY)
        self.assertNotIn("page.registry.legend.note", renderable)
        self.assertIn("page.registry.legend.h2", renderable)
        self.assertNotGenerated("page.registry.legend.note")

    # 4, 5
    def test_missing_and_unexpected_placeholders(self):
        for text in ("{code} نص", "{code} نص {version} {extra}"):
            self.edit_unit("ar", "page.registry.label", text=text)
            errors, _ = i18n.validate(self.root, today=TODAY)
            self.assertTrue(any("page.registry.label" in e and "placeholders" in e for e in errors), errors)
            self.assertNotGenerated("page.registry.label")

    # 6
    def test_altered_canonical_identifier(self):
        self.assertGate("ar", self.generated("ar").replace("MAI-EV-0048", "MAI-EV-0049", 1), "identifiers differ")
        self.edit_unit("ar", "ontology:jazari-root:status", text=self.text("ontology:jazari-root:status", "ar").replace("MAI-EV-0048", "MAI-EV-0047"))
        errors, _ = i18n.validate(self.root, today=TODAY)
        self.assertTrue(any("identifiers or URLs differ" in e for e in errors), errors)

    # 7
    def test_altered_source_url(self):
        html = self.generated("fr").replace("</main>", '<a href="https://example.org/not-a-source">x</a></main>')
        self.assertGate("fr", html, "source URLs differ")

    # 8
    def test_missing_uncertainty_qualifier(self):
        fr = self.generated("fr")
        note = build.escape(self.text("page.registry.legend.note", "fr"), quote=False)
        self.assertIn(note, fr)
        self.assertGate("fr", fr.replace(note, ""), "qualifier page.registry.legend.note is not present")

    # 9
    def test_missing_required_disclosure(self):
        fr = self.generated("fr")
        notice = self.text("page.registry.notice", "fr").split("{independent}")[1].strip()
        self.assertGate("fr", fr.replace(build.escape(notice, quote=False), ""), "disclosure page.registry.notice is not present")
        owner = build.escape(self.text("footer.owner_note", "fr"), quote=False)
        self.assertGate("fr", fr.replace(owner, ""), "footer.owner_note")

    # 10
    def test_broken_anchor(self):
        fr = self.generated("fr")
        self.assertGate("fr", fr.replace('id="coverage-h"', 'id="coverage"'), "element ids")
        self.assertGate("fr", fr.replace('href="/fr/registry/questions/"', 'href="/fr/registry/questions/#missing"').replace(
            'href="/registry/questions/"', 'href="/registry/questions/#missing"'), "internal links or anchors differ")

    # 11
    def test_changed_heading_hierarchy(self):
        fr = self.generated("fr")
        self.assertGate("fr", fr.replace('<h2 id="coverage-h">', '<h3 id="coverage-h">', 1), "heading hierarchy")

    # 12
    def test_unauthorized_localized_publication(self):
        self.assertNotIn("/registry/", [s.path for s in build.LOCALIZABLE_PAGES])
        self.assertEqual(build.localize(model(), None, root=self.root, today=TODAY)[0], {})  # nothing registered
        for lang in ("ar", "fr"):
            self.write(f"{lang}/messages.json", {"language": lang, "units": []})
        files, clusters, report = self.localize()
        self.assertEqual(files, {})
        self.assertEqual(clusters, {})
        langs = self.read("languages.json")
        for x in langs["languages"]:
            if x["code"] == "ar":
                x["state"] = "in-preparation"
        self.write("languages.json", langs)
        self.assertNotIn("ar", build.publishable_languages(build.load_languages(self.root)))

    # 13
    def test_stale_translation_is_not_eligible(self):
        self.edit_unit("ar", "domain:government-policy:label", source="an older label")  # approved before the label changed
        self.assertNotIn("domain:government-policy:label", i18n.renderable_units("ar", self.root, today=TODAY))
        self.assertNotGenerated("domain:government-policy:label")

    # 14
    def test_invalid_structured_rich_text_token(self):
        for text, fragment in (("{independent نص", "malformed rich-text token"), ("نص}", "malformed rich-text token"),
                               ("<strong>نص</strong> {independent}", "markup is not allowed"), ("{Independent} نص", "malformed rich-text token")):
            self.edit_unit("ar", "page.registry.notice", text=text)
            errors, _ = i18n.validate(self.root, today=TODAY)
            self.assertTrue(any(fragment in e for e in errors), (text, errors))
            self.assertNotGenerated("page.registry.notice")

    # 15 — see EnglishParity.test_a_changed_english_message_changes_the_output_and_is_detected

    def test_missing_glossary_term_blocks_the_page(self):
        g = self.read("glossary.json")
        g["terms"] = [t for t in g["terms"] if t["id"] != "entity_type:institution"]
        self.write("glossary.json", g)
        self.assertNotGenerated("glossary term 'entity_type:institution'")

    def test_term_link_must_name_canonical_vocabulary(self):
        en = self.read("en/messages.json")
        en["messages"][[m["id"] for m in en["messages"]].index("vocab.entity_type.institution.plural")]["term"] = "entity_type:nonexistent"
        self.write("en/messages.json", en)
        errors, _ = i18n.validate(self.root, today=TODAY)
        self.assertTrue(any("term link" in e for e in errors), errors)


class InventoryDocument(unittest.TestCase):
    def test_inventory_lists_every_unit_the_extracted_pages_need(self):
        doc = (REPO / "docs" / "MULTILINGUAL_CONTENT_INVENTORY.md").read_text(encoding="utf-8")
        m = model()
        for spec in build.EXTRACTED_PAGES:
            req = build.page_requirements(m, spec)
            for mid in req["messages"]:
                self.assertIn(f"`{mid}`", doc, mid)


if __name__ == "__main__":
    unittest.main()
