"""Semantic-risk checks (tools/semantic.py) and their place in publication eligibility (Sprint 19B-5).

The checks are word lists and patterns: errors are deterministic mismatches and block a unit; warnings are
review aids the human approval must acknowledge. These tests pin both behaviours and check that a correct
translation raises nothing. Translations below are written for the tests; none is an approved translation.
Run: python3 -m unittest discover -s tests
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n  # noqa: E402
import semantic  # noqa: E402
from i18n_fixtures import approval, approved_label  # noqa: E402
from test_i18n import TODAY, Fixture  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def codes(source, text, lang, **kw):
    return {(f.code, f.severity) for f in semantic.findings(source, text, lang, **kw)}


class Errors(unittest.TestCase):
    def test_faithful_translations_raise_nothing(self):
        cases = [
            ("Public availability is not evidence of use.", "التوفر العلني ليس دليلا على الاستخدام.", "ar"),
            ("Public availability is not evidence of use.", "La disponibilité publique n'est pas une preuve d'utilisation.", "fr"),
            ("Release by the ministry, dated 8 September 2026.", "Communiqué du ministère, daté du 8 septembre 2026.", "fr"),
            ("Release by the ministry, dated 8 September 2026.", "بلاغ صادر عن الوزارة بتاريخ 8 شتنبر 2026.", "ar"),
            ("The roadmap plans 50,000 jobs by 2030.", "تهدف خارطة الطريق إلى 50,000 منصب شغل بحلول 2030.", "ar"),
            ("MAD 100 billion in added value", "100 milliards de MAD de valeur ajoutée", "fr"),
        ]
        for source, text, lang in cases:
            self.assertEqual(codes(source, text, lang), set(), text)

    def test_changed_date(self):
        self.assertIn(("DATE_MONTH", "error"), codes("dated 8 September 2026.", "daté du 8 octobre 2026.", "fr"))
        self.assertIn(("DATE_MONTH", "error"), codes("October", "نونبر", "ar"))
        self.assertEqual(codes("October", "أكتوبر", "ar"), set())
        # 'May' as a modal verb at the start of a sentence is not a month; an evidence id is not the month 'mai'.
        self.assertNotIn(("DATE_MONTH", "error"), codes("May apply. See MAI-EV-0001.", "Peut s'appliquer. Voir MAI-EV-0001.", "fr"))

    def test_altered_number_and_scale(self):
        self.assertIn(("NUMBER_MISSING", "error"), codes("50,000 jobs", "5,000 emplois", "fr"))
        self.assertIn(("SCALE_WORD", "error"), codes("MAD 100 billion", "100 millions de MAD", "fr"))
        self.assertIn(("SCALE_WORD", "error"), codes("MAD 100 billion", "100 مليون درهم", "ar"))

    def test_changed_evidence_classification_code(self):
        self.assertIn(("CLASSIFICATION_CODE", "error"), codes("Labelled VERIFIED FACT.", "Marqué FAIT VÉRIFIÉ.", "fr"))

    def test_incorrect_institutional_terminology(self):
        terms = {"independent evidence registry": "registre indépendant de preuves"}
        found = codes("TheMoroccoAI is an independent evidence registry.", "TheMoroccoAI est un registre officiel.", "fr",
                      terms=terms, required=("independent evidence registry",))
        self.assertIn(("TERM_MISSING", "error"), found)
        self.assertIn(("TERM_NOT_USED", "warning"), codes("an independent evidence registry", "un registre officiel", "fr", terms=terms))
        self.assertIn(("ACRONYM_MISSING", "warning"), codes("Mohammed VI Polytechnic University (UM6P)", "جامعة محمد السادس", "ar"))


class Warnings(unittest.TestCase):
    def test_negation_mismatch(self):
        self.assertIn(("NEGATION_LOST", "warning"), codes("Public availability is not evidence of use.", "التوفر العلني دليل على الاستخدام.", "ar"))
        self.assertIn(("NEGATION_ADDED", "warning"), codes("The project is operational.", "Le projet n'est pas opérationnel.", "fr"))

    def test_removed_uncertainty_qualifier(self):
        self.assertIn(("HEDGE_LOST", "warning"), codes("The figure may be revised.", "Le chiffre est révisé.", "fr"))

    def test_prediction_presented_as_completed(self):
        self.assertIn(("PLAN_LOST", "warning"), codes("The roadmap plans 50,000 jobs by 2030.", "أحدثت خارطة الطريق 50,000 منصب شغل سنة 2030.", "ar"))

    def test_attribution_removed(self):
        self.assertIn(("ATTRIBUTION_LOST", "warning"), codes("The ministry states that 20 sites opened.", "20 sites ont ouvert.", "fr"))

    def test_correlation_presented_as_causation(self):
        self.assertIn(("CAUSATION_ADDED", "warning"), codes("Use grew after the launch.", "L'usage a augmenté en raison du lancement.", "fr"))

    def test_comparison_and_legal_terminology(self):
        self.assertIn(("COMPARISON_LOST", "warning"), codes("more than 20 projects", "20 projets", "fr"))
        self.assertIn(("LEGAL_LOST", "warning"), codes("Law 09-08 governs personal data.", "09-08 encadre les informations.", "fr"))

    def test_untranslated_and_length(self):
        self.assertIn(("UNTRANSLATED", "warning"), codes("This page is a translation.", "This page is a translation.", "fr"))
        long = "Each answer below is generated from the registry data when the site is built, and links to its records."
        self.assertIn(("LENGTH_RATIO", "warning"), codes(long, "Réponses.", "fr"))


class Eligibility(Fixture):
    UID = "footer.as_of"  # "as of {date}"

    def unit(self, text, ack=None, **over):
        a = approval(self.en[self.UID], text, self.UID, "ar")
        if ack is not None:
            a["acknowledged_warnings"] = ack
        return self.message_unit(text=text, approval=a, **over)

    def renderable(self):
        return i18n.renderable_texts("ar", self.root, self.evidence, self.ontology, self.gaps, today=TODAY)

    def test_semantic_error_fails_validation_and_rendering(self):
        self.with_units([self.message_unit(uid="date.month.10", text="نونبر", source=self.en["date.month.10"],
                                           approval=approval(self.en["date.month.10"], "نونبر", "date.month.10", "ar"))])
        self.assertRejected("semantic DATE_MONTH")
        self.assertNotIn("date.month.10", self.renderable())

    def test_unacknowledged_warning_is_reported_and_withheld(self):
        uid = "shell.in_english"  # "(in English)"
        text = "بالإنجليزية"
        self.assertEqual(semantic.warning_codes(semantic.findings(self.en[uid], text, "ar")), [])
        uid, text = "footer.disclaimer", "تابع لحكومة المغرب"  # negation dropped: "Not affiliated ..."
        a = approval(self.en[uid], text, uid, "ar", acknowledged_warnings=[])
        self.with_units([self.message_unit(uid=uid, text=text, source=self.en[uid], kind="disclosure", approval=a)])
        errors, report = self.validate()
        self.assertEqual(errors, [])
        self.assertEqual(report["unacknowledged"], [f"ar:{uid}"])
        self.assertNotIn(uid, self.renderable())
        # Acknowledging the warning records the reviewer's decision; the unit becomes renderable. Whether the
        # meaning is right remains the reviewer's responsibility: the check only made the risk visible.
        a["acknowledged_warnings"] = ["LENGTH_RATIO", "NEGATION_LOST"]
        self.with_units([self.message_unit(uid=uid, text=text, source=self.en[uid], kind="disclosure", approval=a)])
        self.assertIn(uid, self.renderable())

    def test_acknowledgement_must_be_a_list_of_codes(self):
        self.with_units([self.unit("بتاريخ {date}", ack="NEGATION_LOST")])
        self.assertRejected("acknowledged_warnings must list")


class Concepts(Fixture):
    def glossary(self, concepts, terms=()):
        g = self.read("glossary.json")
        g["concepts"], g["terms"] = concepts, list(terms)
        self.write("glossary.json", g)

    def test_committed_concepts_occur_in_the_english_catalog(self):
        g = json.loads((REPO / "i18n" / "glossary.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(g["concepts"]), 10)
        self.assertEqual(i18n.validate_concepts(g, " ".join(i18n.english_messages().values())), [])
        self.assertEqual(g["terms"], [])  # no label is approved

    def test_concept_must_occur_in_the_catalog_and_be_well_formed(self):
        self.glossary([{"id": "estimated-value", "en": "estimated value", "added": "2026-11-22"}])
        self.assertRejected("does not occur in the English catalog")
        self.glossary([{"id": "AI Ecosystem", "en": "AI ecosystem", "added": "2026-11-22"}])
        self.assertRejected("lower-case slug")
        self.glossary([{"id": "ai-ecosystem", "en": "AI ecosystem"}] * 2)
        self.assertRejected("duplicate concept id")

    def test_concept_term_is_approved_against_its_english_form(self):
        concept = {"id": "ai-ecosystem", "en": "AI ecosystem", "added": "2026-11-22"}
        label = approved_label("concept:ai-ecosystem", "منظومة الذكاء الاصطناعي", approval=approval(
            "AI ecosystem", "منظومة الذكاء الاصطناعي", "concept:ai-ecosystem", "ar"))
        self.glossary([concept], [{"id": "concept:ai-ecosystem", "translations": {"ar": label}}])
        self.assertEqual(self.validate()[0], [])
        self.assertEqual(i18n.term_forms("ar", self.root, TODAY), {"AI ecosystem": "منظومة الذكاء الاصطناعي"})
        self.glossary([concept], [{"id": "concept:unknown", "translations": {}}])
        self.assertRejected("does not name canonical vocabulary")


if __name__ == "__main__":
    unittest.main()
