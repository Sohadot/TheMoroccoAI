"""Tests for the evidence registry and ontology validator.  Run: python3 -m unittest discover -s tests"""
import copy
import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import registry  # noqa: E402

TODAY = datetime.date(2026, 10, 18)


class RepositoryData(unittest.TestCase):
    def test_published_registry_and_ontology_are_valid(self):
        evidence, ontology = registry.load_all()
        self.assertEqual(registry.validate(evidence, ontology), [])

    def test_registry_is_not_empty_and_covers_a_full_chain(self):
        evidence, ontology = registry.load_all()
        types = {e["type"] for e in ontology["entities"]}
        for t in ("institution", "initiative", "project", "technology", "sector"):
            self.assertIn(t, types)
        self.assertGreaterEqual(len(evidence["records"]), 10)

    def test_every_classification_label_is_defined_publicly(self):
        evidence, _ = registry.load_all()
        self.assertEqual(set(evidence["classifications"]), set(registry.CLASSIFICATIONS))

    def test_targets_are_never_classified_as_facts(self):
        evidence, _ = registry.load_all()
        for r in evidence["records"]:
            if r["classification"] == "VERIFIED FACT":
                self.assertIsNone(registry.FORWARD_LOOKING.search(r["claim"]), r["evidence_id"])


class ValidatorRejects(unittest.TestCase):
    """Each case breaks one rule in a copy of the real data and expects the matching error."""

    def setUp(self):
        self.evidence, self.ontology = registry.load_all()

    def errors(self):
        return registry.validate(self.evidence, self.ontology, today=TODAY)

    def assertError(self, fragment):
        errs = self.errors()
        self.assertTrue(any(fragment in e for e in errs), f"expected '{fragment}' in {errs}")

    def record(self, rid="MAI-EV-0001"):
        return next(r for r in self.evidence["records"] if r["evidence_id"] == rid)

    def entity(self, eid):
        return next(e for e in self.ontology["entities"] if e["id"] == eid)

    def test_duplicate_evidence_id(self):
        self.evidence["records"].append(copy.deepcopy(self.record()))
        self.assertError("duplicate evidence_id")

    def test_malformed_evidence_id(self):
        self.record()["evidence_id"] = "EV-1"
        self.assertError("must match MAI-EV-NNNN")

    def test_missing_field(self):
        del self.record()["retrieval_date"]
        self.assertError("missing field 'retrieval_date'")

    def test_http_source_url(self):
        self.record()["source_url"] = "http://www.maroc.ma/en/news/x"
        self.assertError("source_url must use https")

    def test_source_url_with_whitespace(self):
        self.record()["source_url"] = "https://www.maroc.ma/en/news x"
        self.assertError("source_url contains whitespace")

    def test_self_citation(self):
        self.record()["source_url"] = "https://themoroccoai.com/registry/"
        self.assertError("must point to the original source")

    def test_future_retrieval_date(self):
        self.record()["retrieval_date"] = "2026-12-01"
        self.assertError("retrieval_date is in the future")

    def test_publication_after_retrieval(self):
        self.record()["publication_date"] = "2026-10-19"
        self.record()["retrieval_date"] = "2026-10-18"
        self.assertError("publication_date is after retrieval_date")

    def test_unknown_classification(self):
        self.record()["classification"] = "PROBABLY TRUE"
        self.assertError("unknown classification")

    def test_target_presented_as_fact(self):
        r = self.record("MAI-EV-0011")
        r["classification"] = "VERIFIED FACT"
        self.assertError("forward-looking wording")

    def test_target_presented_as_achieved(self):
        self.record("MAI-EV-0011")["claim"] = "Morocco has reached 50,000 AI jobs."
        self.assertError("presents an outcome as achieved")

    def test_target_without_year(self):
        del self.record("MAI-EV-0011")["target_year"]
        self.assertError("needs an integer target_year")

    def test_unverified_claim_needs_note(self):
        self.record("MAI-EV-0003")["verification_note"] = ""
        self.assertError("UNVERIFIED CLAIM needs a verification_note")

    def test_record_without_excerpt(self):
        self.record()["source_excerpts"] = []
        self.assertError("needs at least one non-empty source excerpt")

    def test_record_references_missing_entity(self):
        self.record()["related_entities"].append("ministry-of-nowhere")
        self.assertError("'ministry-of-nowhere' does not exist")

    def test_entity_cites_missing_evidence(self):
        self.entity("um6p")["evidence"].append("MAI-EV-9999")
        self.assertError("cites missing evidence MAI-EV-9999")

    def test_entity_and_record_must_reference_each_other(self):
        self.entity("um6p")["evidence"].append("MAI-EV-0001")
        self.assertError("does not list it in related_entities")

    def test_duplicate_entity_id(self):
        self.ontology["entities"].append(copy.deepcopy(self.entity("um6p")))
        self.assertError("duplicate entity id")

    def test_documented_entity_without_evidence(self):
        self.ontology["entities"].append({"id": "acme-ai", "type": "institution", "name": "Acme AI",
                                          "summary": "x", "domain": "companies-deployments", "evidence": []})
        self.assertError("acme-ai: has no supporting evidence")

    def test_relationship_to_missing_entity(self):
        self.ontology["relationships"].append({"subject": "um6p", "predicate": "signatory_of", "object": "ghost",
                                               "evidence": ["MAI-EV-0007"], "classification": "VERIFIED FACT"})
        self.assertError("references a missing entity")

    def test_relationship_type_mismatch(self):
        self.ontology["relationships"].append({"subject": "robotics", "predicate": "launched", "object": "um6p",
                                               "evidence": ["MAI-EV-0009"], "classification": "VERIFIED FACT"})
        self.assertError("predicate does not accept technology → institution")

    def test_relationship_classified_beyond_its_evidence(self):
        rel = next(r for r in self.ontology["relationships"] if r["object"] == "sovereign-ai-marketplace")
        rel["classification"] = "VERIFIED FACT"
        self.assertError("no cited record supports that class")

    def test_analysis_needs_note_and_two_records(self):
        rel = next(r for r in self.ontology["relationships"] if r["classification"] == "INDEPENDENT ANALYSIS")
        rel["note"] = ""
        self.assertError("INDEPENDENT ANALYSIS needs a note")

    def test_relationship_evidence_must_document_an_end(self):
        rel = next(r for r in self.ontology["relationships"] if r["subject"] == "cndp")
        rel["evidence"] = ["MAI-EV-0001"]
        self.assertError("documents neither end")


if __name__ == "__main__":
    unittest.main()
