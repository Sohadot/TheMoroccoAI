"""Tests for the evidence registry and ontology validator.  Run: python3 -m unittest discover -s tests"""
import copy
import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import registry  # noqa: E402

TODAY = datetime.date(2026, 10, 19)


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

    def test_institutions_are_not_linked_beyond_what_sources_state(self):
        # Regression: the CNDP page supports a framework listing, not "administers";
        # the Nador memorandum says the higher-education ministry was "involved", not that it signed.
        _, ontology = registry.load_all()
        predicates = {(r["subject"], r["object"]): r["predicate"] for r in ontology["relationships"]}
        self.assertEqual(predicates[("cndp", "law-09-08")], "lists_in_framework")
        # Sprint 02: a source naming the signatories (MAI-EV-0019) now supports "signatory of".
        rel = next(r for r in ontology["relationships"]
                   if (r["subject"], r["object"]) == ("ministry-higher-education", "jazari-institute-nador"))
        self.assertEqual(rel["predicate"], "signatory_of")
        self.assertIn("MAI-EV-0019", rel["evidence"])

    def test_name_based_identification_is_not_a_verified_fact(self):
        # Regression: the DarijaBERT card names "AIOX Lab"; equating it with AIOX Labs is an inference.
        _, ontology = registry.load_all()
        rel = next(r for r in ontology["relationships"]
                   if (r["subject"], r["predicate"], r["object"]) == ("aiox-labs", "develops", "darijabert"))
        self.assertEqual(rel["classification"], "INDEPENDENT ANALYSIS")

    def test_compute_infrastructure_is_not_an_ai_application(self):
        _, ontology = registry.load_all()
        kinds = {e["id"]: e.get("project_kind") for e in ontology["entities"]}
        self.assertEqual(kinds["toubkal-supercomputer"], "compute-infrastructure")
        self.assertEqual(kinds["nexus-ai-factory"], "compute-infrastructure")

    def test_outdated_self_description_no_longer_sets_status(self):
        # Regression: DeepEcho's website disclaimer was contradicted by the FDA record (MAI-EV-0032).
        evidence, ontology = registry.load_all()
        rec = next(r for r in evidence["records"] if r["evidence_id"] == "MAI-EV-0029")
        self.assertNotIn("status_evidence", rec)
        sw = next(e for e in ontology["entities"] if e["id"] == "deepecho-ultrasound-software")
        self.assertEqual(sw["lifecycle"], "unresolved")

    def test_fda_link_is_a_qualified_association(self):
        # Regression: the FDA applicant (Delaware) is associated with the Morocco-based DeepEcho, not identified with it.
        evidence, ontology = registry.load_all()
        recs = {r["evidence_id"]: r for r in evidence["records"]}
        for rid in ("MAI-EV-0032", "MAI-EV-0039"):
            self.assertIn("deepecho", recs[rid]["associated_entities"])
            self.assertIsNone(recs[rid].get("status_evidence"))
        self.assertEqual(recs["MAI-EV-0029"]["superseded_by"], ["MAI-EV-0032", "MAI-EV-0039"])

    def test_provider_label_is_not_recorded_as_a_role(self):
        # Regression: "Powered by Berexia" is interface text not shown on the assistant; it establishes no role.
        _, ontology = registry.load_all()
        e = next(e for e in ontology["entities"] if e["id"] == "idarati-ai")
        self.assertFalse(any("Berexia" in a["value"] for a in e.get("attributes") or []))
        self.assertFalse(any(r["object"] == "idarati-ai" and "berexia" in r["subject"] for r in ontology["relationships"]))

    def test_digital_platform_is_not_an_ai_application(self):
        _, ontology = registry.load_all()
        e = next(e for e in ontology["entities"] if e["id"] == "sovereign-ai-marketplace")
        self.assertEqual(e["project_kind"], "digital-platform")

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

    def test_impossible_calendar_date_is_reported_not_crashed(self):
        self.record()["publication_date"] = "2026-02-30"
        self.assertError("publication_date must be a valid")

    def test_invalid_month_is_reported_not_crashed(self):
        self.record()["retrieval_date"] = "2026-13-01"
        self.assertError("retrieval_date must be a valid")

    def test_retrieval_after_registry_as_of(self):
        self.evidence["as_of"] = "2026-10-17"
        self.assertError("retrieval_date is after the registry as_of date")

    def test_unsafe_domain_key(self):
        self.ontology["domains"]['bad" onmouseover="x'] = "Bad"
        self.assertError("domain key")

    # ── Sprint 02: lifecycle, origin, attributes and source independence ──

    def test_secondary_press_cannot_be_verified_fact(self):
        self.record("MAI-EV-0030")["classification"] = "VERIFIED FACT"
        self.assertError("secondary press can support only")

    def test_operational_needs_an_independent_source(self):
        self.record("MAI-EV-0020")["source_type"] = "organization_website"
        self.assertError("an independent basis cannot rest on a self-published or press source")

    def test_operational_cannot_rest_on_an_announcement(self):
        nexus = self.entity("nexus-ai-factory")
        nexus["lifecycle"] = "operational"
        self.assertError("lifecycle 'operational' is not supported")

    def test_project_needs_a_lifecycle(self):
        del self.entity("toubkal-supercomputer")["lifecycle"]
        self.assertError("project needs a lifecycle")

    def test_released_is_only_for_models_and_datasets(self):
        self.entity("toubkal-supercomputer")["lifecycle"] = "released"
        self.assertError("project needs a lifecycle from")

    def test_lifecycle_evidence_must_belong_to_the_entity(self):
        self.entity("toubkal-supercomputer")["lifecycle_evidence"] = ["MAI-EV-0001"]
        self.assertError("lifecycle_evidence must be a subset")

    def test_lifecycle_only_on_projects_models_datasets(self):
        self.entity("um6p")["lifecycle"] = "operational"
        self.assertError("institution entities take no lifecycle")

    def test_company_needs_an_origin(self):
        del self.entity("deepecho")["origin"]
        self.assertError("company needs an origin")

    def test_origin_needs_evidence(self):
        self.entity("deepecho")["origin_evidence"] = []
        self.assertError("origin 'based-in-morocco' needs origin_evidence")

    def test_origin_only_on_companies(self):
        self.entity("um6p")["origin"] = "moroccan"
        self.assertError("only company entities take an origin")

    def test_attribute_must_cite_the_entitys_own_record(self):
        self.entity("al-atlas")["attributes"][0]["evidence"] = "MAI-EV-0001"
        self.assertError("must cite one of the entity's own records")

    # ── Sprint 02 review: delivery must be evidenced explicitly ──

    def test_signature_or_announcement_cannot_establish_delivery(self):
        # Regression: before the review, each of these passed because the cited record was a
        # VERIFIED FACT from an independent source, although it documented only a signature.
        cases = [("jazari-root", "operational", ["MAI-EV-0008"]),
                 ("jazari-institute-nador", "operational", ["MAI-EV-0019"]),
                 ("jazari-industrie-x0", "pilot", ["MAI-EV-0009"]),
                 ("deepecho-ultrasound-software", "operational", ["MAI-EV-0028"])]
        for eid, stage, basis in cases:
            with self.subTest(eid=eid):
                self.setUp()
                e = self.entity(eid)
                e["lifecycle"], e["lifecycle_evidence"] = stage, basis
                self.assertError(f"lifecycle '{stage}' needs a lifecycle_evidence record whose status_evidence is '{stage}'")

    def test_status_evidence_requires_a_verified_record(self):
        self.record("MAI-EV-0030")["status_evidence"] = "operational"
        self.assertError("status_evidence requires a VERIFIED FACT record")

    def test_operational_status_cannot_come_from_own_website(self):
        self.record("MAI-EV-0029")["status_evidence"] = "operational"
        self.assertError("'operational' needs a status_basis")

    def test_released_must_come_from_the_repository(self):
        self.record("MAI-EV-0021")["status_evidence"] = "released"
        self.assertError("'released' must be evidenced by the technical repository itself")

    def test_unknown_status_evidence(self):
        self.record("MAI-EV-0020")["status_evidence"] = "live"
        self.assertError("unknown status_evidence")

    def test_project_needs_a_known_kind(self):
        self.entity("toubkal-supercomputer")["project_kind"] = "supercomputer"
        self.assertError("project needs a project_kind")

    def test_kind_only_on_projects(self):
        self.entity("atlas-chat")["project_kind"] = "ai-application"
        self.assertError("only projects take a project_kind")

    def test_independent_origin_cannot_rest_on_self_description(self):
        e = self.entity("aiox-labs")  # origin rests on its own website ("roots in Morocco")
        e["origin"] = "based-in-morocco"
        self.assertError("needs origin_evidence from a source independent of the company")

    def test_verified_operations_cannot_rest_on_press(self):
        self.entity("nexus-core-systems")["origin"] = "foreign-moroccan-operations-verified"
        self.assertError("needs origin_evidence from a source independent of the company")

    # ── Sprint 03: deployment evidence ──

    def test_announcement_cannot_become_operational(self):
        e = self.entity("swam-fraud-scoring")
        e["lifecycle"], e["lifecycle_evidence"] = "operational", ["MAI-EV-0036"]
        self.assertError("lifecycle 'operational' is not supported by a VERIFIED FACT record")

    def test_procurement_cannot_prove_operational_use(self):
        r = self.record("MAI-EV-0034")
        r["evidence_type"] = "procurement_notice"
        self.assertError("a procurement notice cannot evidence a lifecycle status")

    def test_vendor_availability_cannot_prove_customer_deployment(self):
        r = self.record("MAI-EV-0029")
        r.update(status_evidence="operational", status_basis="public-availability-observed", source_entity="deepecho")
        e = self.entity("deepecho-ultrasound-software")
        e["lifecycle"], e["lifecycle_evidence"] = "operational", ["MAI-EV-0029"]
        del e["note"]
        self.assertError("needs a status record published by a verified operator of the project")

    def test_operator_basis_needs_the_publishing_operator(self):
        del self.record("MAI-EV-0034")["source_entity"]
        self.assertError("needs source_entity naming the operator that published it")

    def test_infrastructure_cannot_count_as_an_ai_application(self):
        self.entity("toubkal-supercomputer")["project_kind"] = "ai-application"
        self.assertError("needs a VERIFIED FACT 'operates' relationship naming its operator")

    def test_developer_is_not_an_operator(self):
        rels = self.ontology["relationships"]
        self.ontology["relationships"] = [r for r in rels if not (r["predicate"] == "operates" and r["object"] == "idarati-ai")]
        self.ontology["relationships"].append({"subject": "ministry-digital-transition", "predicate": "develops",
                                               "object": "idarati-ai", "evidence": ["MAI-EV-0034"], "classification": "VERIFIED FACT"})
        self.assertError("needs a status record published by a verified operator of the project")

    # ── Sprint 03 review: availability, identity, regulatory status, recency ──

    def test_public_interface_is_not_proof_of_adoption(self):
        self.record("MAI-EV-0038")["claim"] += " The assistant is used by 1.2 million users."
        self.assertError("an availability observation cannot assert use or continuity")

    def test_availability_observation_cannot_claim_continuity(self):
        self.record("MAI-EV-0038")["claim"] += " It has been available continuously since 2024."
        self.assertError("an availability observation cannot assert use or continuity")

    def test_provider_label_does_not_make_an_operator(self):
        # MAI-EV-0035 carries a provider label but was published by the ministry, not by the would-be operator.
        self.ontology["relationships"].append({"subject": "aiox-labs", "predicate": "operates", "object": "idarati-ai",
                                               "evidence": ["MAI-EV-0035"], "classification": "VERIFIED FACT"})
        self.assertError("a verified operator must be documented by a record the operator published")

    def test_market_clearance_is_not_use_in_morocco(self):
        self.record("MAI-EV-0032").update(status_evidence="operational", status_basis="independent-listing")
        e = self.entity("deepecho-ultrasound-software")
        e["lifecycle"], e["lifecycle_evidence"] = "operational", ["MAI-EV-0032"]
        self.ontology["relationships"].append({"subject": "ministry-health", "predicate": "operates",
                                               "object": "deepecho-ultrasound-software", "evidence": ["MAI-EV-0032"],
                                               "classification": "VERIFIED FACT"})
        self.assertError("a regulatory_record cannot evidence 'operational'")
        self.assertError("a verified operator must be documented by a record the operator published")

    def test_clearance_is_not_called_approval(self):
        self.entity("deepecho-ultrasound-software")["summary"] += " The software is FDA-approved."
        self.assertError("calls a device approved")

    def test_approval_wording_is_allowed_only_as_a_quotation(self):
        self.record("MAI-EV-0032")["claim"] += " The device was approved by the U.S. FDA."
        self.assertError("claim calls a device approved")
        self.setUp()
        self.record("MAI-EV-0032")["claim"] += ' The government calls it "approved by the FDA".'
        self.assertEqual(self.errors(), [])

    def test_similar_names_are_not_one_legal_entity(self):
        self.entity("deepecho")["origin_evidence"] = ["MAI-EV-0032", "MAI-EV-0028"]
        self.assertError("names an entity only associated with this company")

    def test_association_cannot_alone_support_a_verified_relationship(self):
        self.ontology["relationships"].append({"subject": "deepecho", "predicate": "develops", "object": "deepecho-ultrasound-software",
                                               "evidence": ["MAI-EV-0039"], "classification": "VERIFIED FACT"})
        self.ontology["relationships"] = [r for r in self.ontology["relationships"]
                                          if not (r["predicate"] == "develops" and r["object"] == "deepecho-ultrasound-software"
                                                  and r["evidence"] != ["MAI-EV-0039"])]
        self.assertError("cannot rest only on records that associate")

    def test_associated_record_attribute_must_say_so(self):
        attr = next(a for a in self.entity("deepecho-ultrasound-software")["attributes"] if a["evidence"] == "MAI-EV-0032")
        attr["name"] = "US FDA 510(k)"
        self.assertError("cites a record only associated with this entity")

    def test_matching_but_superseded_quote_cannot_set_status(self):
        self.record("MAI-EV-0029")["status_evidence"] = "in-development"
        e = self.entity("deepecho-ultrasound-software")
        e["lifecycle"], e["lifecycle_evidence"] = "in-development", ["MAI-EV-0029"]
        self.assertError("a superseded record cannot evidence a lifecycle status")

    def test_superseded_by_must_point_to_other_records(self):
        self.record("MAI-EV-0029")["superseded_by"] = ["MAI-EV-0029"]
        self.assertError("superseded_by must list other existing records")

    def test_old_evidence_is_not_discontinuation(self):
        e = self.entity("idarati-ai")
        e["lifecycle"] = "discontinued"
        for rid in ("MAI-EV-0034", "MAI-EV-0035", "MAI-EV-0038"):
            self.record(rid)["publication_date"] = "2024-01-15"
        self.assertError("lifecycle 'discontinued' needs a lifecycle_evidence record whose status_evidence is 'discontinued'")

    def test_unsupported_performance_claims_are_rejected(self):
        self.record("MAI-EV-0034")["claim"] += " It reduced processing times by 40%."
        self.assertError("asserts performance or outcomes")

    def test_status_basis_is_required_for_operational(self):
        del self.record("MAI-EV-0020")["status_basis"]
        self.assertError("'operational' needs a status_basis")

    def test_secondary_press_cannot_evidence_operation(self):
        r = self.record("MAI-EV-0020")
        r["source_type"] = "secondary_press"
        self.assertError("'operational' cannot be evidenced by secondary press")

    def test_unresolved_needs_an_explanation(self):
        del self.entity("deepecho-ultrasound-software")["note"]
        self.assertError("lifecycle 'unresolved' needs a note explaining why")

    def test_source_entity_must_resolve(self):
        self.record("MAI-EV-0035")["source_entity"] = "ministry-of-nowhere"
        self.assertError("source_entity 'ministry-of-nowhere' must be an existing entity")

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
