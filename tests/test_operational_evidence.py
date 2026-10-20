"""Sprint 08: the online-services ranking, JAZARI governance events and the per-institute operational-evidence gap."""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import build  # noqa: E402
import registry  # noqa: E402
from test_consumer import PublishedCopy  # noqa: E402
from test_precision import visible  # noqa: E402

INSTITUTES = ["jazari-root", "jazari-edutech", "jazari-industrie-x0", "jazari-smart-city", "jazari-institute-nador"]


def load_gaps():
    return json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))


class OnlineServicesRanking(unittest.TestCase):
    """The strategy's 113th place is an Online Services Index position it states; the UN gives OSI values without a
    rank, and overall EGDI ranks are a different measure."""

    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.gaps = {g["id"]: g for g in load_gaps()["gaps"]}

    def current_texts(self):
        texts = [r[k] for r in self.evidence["records"] for k in ("claim", "verification_note", "title")]
        texts += [e.get(k, "") for e in self.ontology["entities"] for k in ("summary", "status", "note")]
        texts += [r.get("note", "") for r in self.ontology["relationships"]]
        texts += [json.dumps(g, ensure_ascii=False) for g in self.gaps.values()]
        return texts

    def test_the_strategy_defines_its_ranking_as_the_online_services_index(self):
        r = self.records["MAI-EV-0049"]
        self.assertEqual((r["classification"], r["evidence_type"], r["source_type"]), ("OFFICIAL TARGET", "official_report", "government_publication"))
        self.assertTrue(any("Online Services Index" in x and "composant de l" in x for x in r["source_excerpts"]))
        self.assertTrue(any(x.startswith("113e rang mondial") for x in r["source_excerpts"]))
        self.assertIn("image-only", r["verification_note"])
        self.assertIn("has not verified it", r["verification_note"])

    def test_no_text_compares_the_osi_place_with_overall_egdi_ranks(self):
        for t in self.current_texts():
            self.assertNotRegex(t, r"(?i)no (?:United Nations )?edition(?: of the United Nations index)? (?:ranks|shows) Morocco(?: at)? 113", t)
            self.assertNotRegex(t, r"113th to 50th place (?:worldwide )?in the e-government development index", t)

    def test_the_113th_place_is_never_presented_as_verified(self):
        for t in self.current_texts():
            for m in re.finditer(r"[^.]*113th[^.]*\.", t):
                s = m.group(0)
                if re.search(r"(?i)\bverified\b", s):
                    self.assertRegex(s, r"(?i)not (?:been )?verified|has not verified", s)

    def test_un_osi_values_are_recorded_without_a_rank(self):
        r = self.records["MAI-EV-0046"]
        self.assertIn("Morocco (Value) 0.56184 0.47210", " ".join(r["source_excerpts"]))
        self.assertIn("without a rank on that index", r["claim"])
        self.assertNotIn("113", r["claim"] + " ".join(r["source_excerpts"]))

    def test_gap_06_keeps_the_three_measures_apart(self):
        g = self.gaps["GAP-06"]
        self.assertEqual(g["state"], "open")
        self.assertIn("MAI-EV-0049", g["assessed_records"])
        target = next(s for s in g["established"] if "113th to 50th" in s["text"])
        self.assertEqual(set(target["evidence"]), {"MAI-EV-0002", "MAI-EV-0049"})
        self.assertIn("Online Services Index", target["text"])
        un = next(s for s in g["established"] if "0.47210" in s["text"])
        self.assertIn("MAI-EV-0046", un["evidence"])
        self.assertIn("not its rank", un["text"])
        self.assertIn("101st in 2022 and 90th in 2024", un["text"])
        self.assertIn("has not been verified", un["text"])

    def test_digital_morocco_summary_names_the_index_the_strategy_uses(self):
        e = next(e for e in self.ontology["entities"] if e["id"] == "digital-morocco-2030")
        self.assertIn("Online Services Index", e["summary"])
        self.assertIn("not verified by the registry", e["summary"])
        self.assertIn("Online Services Index", visible("registry/digital-morocco-2030/index.html"))

    def test_the_earlier_correction_is_annotated_not_rewritten(self):
        log = json.loads((REPO / "data" / "changelog.json").read_text(encoding="utf-8"))["entries"]
        v060 = next(e for e in log if e["version"] == "0.6.0")
        old = next(x for x in v060["corrections"] if "113th" in x)
        self.assertIn("no United Nations edition ranks Morocco 113th", old)
        self.assertIn("Corrected in v0.7.0", old)
        v070 = next(e for e in log if e["version"] == "0.7.0")
        self.assertTrue(any("Online Services Index" in x for x in v070["corrections"]))


class GovernanceEventIsNotOperation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.entities = {e["id"]: e for e in cls.ontology["entities"]}

    def test_the_general_assemblies_are_recorded_without_a_stage_change(self):
        r = self.records["MAI-EV-0048"]
        self.assertEqual(r["classification"], "VERIFIED FACT")
        self.assertNotIn("status_evidence", r)
        self.assertIn("not evidence that any institute operates", r["verification_note"])
        for eid in INSTITUTES[:4]:
            e = self.entities[eid]
            self.assertEqual(e["lifecycle"], "announced", eid)
            self.assertNotIn("MAI-EV-0048", e["lifecycle_evidence"], eid)
            self.assertIn("MAI-EV-0048", e["evidence"], eid)
            self.assertIn("general assembly was held on 8 September 2026", e["status"], eid)
            self.assertIn("Operation is not documented", e["status"], eid)
        self.assertNotIn("jazari-institute-nador", r["related_entities"])
        self.assertEqual(self.entities["jazari-institute-nador"]["lifecycle"], "announced")

    def test_the_release_cannot_carry_an_operating_stage(self):
        ev, on = copy.deepcopy(self.evidence), copy.deepcopy(self.ontology)
        root = next(e for e in on["entities"] if e["id"] == "jazari-root")
        root["lifecycle"], root["lifecycle_evidence"] = "operational", ["MAI-EV-0048"]
        self.assertTrue(any("lifecycle 'operational'" in e for e in registry.validate(ev, on)))

    def test_stale_and_overbroad_notes_are_corrected(self):
        self.assertIn("later read and is recorded as MAI-EV-0047", self.records["MAI-EV-0008"]["verification_note"])
        self.assertNotIn("was not located", self.records["MAI-EV-0008"]["verification_note"])
        note = self.records["MAI-EV-0047"]["verification_note"]
        self.assertIn("This issue (Bulletin Officiel 7534) contains no act concerning the Al Jazari institute in Nador", note)
        self.assertIn("does not show that no such act exists", note)
        self.assertNotIn("No act concerns the Al Jazari institute in Nador.", note)


class PerInstituteGap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.gaps = load_gaps()

    def gap07(self, gaps=None):
        return next(g for g in (gaps or self.gaps)["gaps"] if g["id"] == "GAP-07")

    def errors(self, mutate, ontology=None):
        gaps, ontology = copy.deepcopy(self.gaps), copy.deepcopy(ontology or self.ontology)
        mutate(self.gap07(gaps), ontology)
        entities = {e["id"]: e for e in ontology["entities"]}
        records = {r["evidence_id"]: r for r in self.evidence["records"]}
        return registry._check_entity_assessments(self.gap07(gaps), gaps["entity_assessment"], records, entities)

    def assessment(self, g, eid):
        return next(a for a in g["entity_assessments"] if a["entity"] == eid)

    def test_scope_dimensions_and_state(self):
        g = self.gap07()
        self.assertEqual(g["entities"], INSTITUTES)
        self.assertEqual(g["state"], "open")
        self.assertEqual(tuple(self.gaps["entity_assessment"]["dimension_order"]), registry.ENTITY_ASSESSMENT_DIMENSIONS)
        self.assertEqual(set(build.DIMENSION_LABELS), set(registry.ENTITY_ASSESSMENT_DIMENSIONS))
        for a in g["entity_assessments"]:
            self.assertEqual(a["state"], "open", a["entity"])
        for eid in INSTITUTES[:4]:
            d = self.assessment(g, eid)["dimensions"]
            self.assertEqual((d["legal_approval"], d["governance_event"]), (["MAI-EV-0047"], ["MAI-EV-0048"]))
            self.assertFalse(any(d[k] for k in ("staffing", "premises", "operational_activity", "outputs", "documented_non_operation")))
        nador = self.assessment(g, "jazari-institute-nador")
        self.assertFalse(any(nador["dimensions"].values()))
        self.assertIn("which does not show that none exists", nador["note"])
        self.assertEqual(self.errors(lambda g, o: None), [])

    def test_legal_approval_and_a_general_assembly_never_resolve_an_institute(self):
        def resolve(g, o):
            a = self.assessment(g, "jazari-root")
            a["state"], a["resolved_by"] = "resolved", ["MAI-EV-0047", "MAI-EV-0048"]
        self.assertTrue(any("meet no resolution path" in e for e in self.errors(resolve)))

    def test_aspirational_or_unrelated_records_cannot_document_a_dimension(self):
        def plan(g, o):
            self.assessment(g, "jazari-root")["dimensions"]["operational_activity"] = ["MAI-EV-0010"]  # an announced plan
        self.assertTrue(any("only a VERIFIED FACT documents a dimension" in e for e in self.errors(plan)))

        def unrelated(g, o):
            self.assessment(g, "jazari-institute-nador")["dimensions"]["governance_event"] = ["MAI-EV-0048"]  # not about Nador
        self.assertTrue(any("which does not concern jazari-institute-nador" in e for e in self.errors(unrelated)))

    def test_one_institute_can_resolve_while_the_others_stay_open(self):
        on = copy.deepcopy(self.ontology)
        next(e for e in on["entities"] if e["id"] == "jazari-root")["lifecycle"] = "operational"

        def operating(g, o):
            a = self.assessment(g, "jazari-root")
            a["dimensions"].update(staffing=["MAI-EV-0048"], operational_activity=["MAI-EV-0048"], outputs=["MAI-EV-0048"])
            a["state"], a["resolved_by"] = "resolved", ["MAI-EV-0048"]
        self.assertEqual(self.errors(operating, on), [])

        def gap_resolved_too(g, o):
            operating(g, o)
            g["state"] = "resolved"
        self.assertTrue(any("is resolved while an entity it assesses is still open" in e for e in self.errors(gap_resolved_too, on)))

        def left_open(g, o):
            operating(g, o)
            self.assessment(g, "jazari-root")["state"] = "open"
        self.assertTrue(any("now meet the operating resolution path" in e for e in self.errors(left_open, on)))

    def test_documented_non_operation_needs_a_discontinued_stage(self):
        on = copy.deepcopy(self.ontology)

        def ceased(g, o):
            a = self.assessment(g, "jazari-smart-city")
            a["dimensions"]["documented_non_operation"] = ["MAI-EV-0047"]
            a["state"], a["resolved_by"] = "resolved", ["MAI-EV-0047"]
        self.assertTrue(any("meet no resolution path" in e for e in self.errors(ceased, on)))
        next(e for e in on["entities"] if e["id"] == "jazari-smart-city")["lifecycle"] = "discontinued"
        self.assertEqual(self.errors(ceased, on), [])

    def test_assessments_must_match_the_gaps_entities(self):
        def dropped(g, o):
            g["entity_assessments"].pop()
        self.assertTrue(any("exactly the gap's entities" in e for e in self.errors(dropped)))

        def missing_dimension(g, o):
            del self.assessment(g, "jazari-root")["dimensions"]["premises"]
        self.assertTrue(any("dimensions must be exactly" in e for e in self.errors(missing_dimension)))

    def test_published_page_and_json_show_every_institute(self):
        page = visible("registry/gaps/index.html")
        section = page[page.index("GAP-07"):]
        self.assertIn("Assessment by institute", section)
        self.assertEqual(section.count("Not documented"), 4 * 5 + 7)
        published = json.loads((REPO / "registry" / "gaps" / "gaps.json").read_text(encoding="utf-8"))
        self.assertEqual(next(g for g in published["gaps"] if g["id"] == "GAP-07")["entity_assessments"], self.gap07()["entity_assessments"])
        self.assertEqual(published["entity_assessment"], self.gaps["entity_assessment"])
        self.assertIn("entity_assessments", published["derivation"])


class ConsumerChecksTheAssessments(unittest.TestCase):
    def run_copy(self, change):
        copy_ = PublishedCopy()
        try:
            for path in ("/data/gaps.json", "/registry/gaps/gaps.json"):
                copy_.edit(path, change)
            return copy_.verify()
        finally:
            copy_.cleanup()

    def test_a_resolution_without_operation_is_rejected(self):
        def resolve(d):
            a = next(a for a in next(g for g in d["gaps"] if g["id"] == "GAP-07")["entity_assessments"] if a["entity"] == "jazari-root")
            a["state"], a["resolved_by"] = "resolved", ["MAI-EV-0047"]
        code, out, err = self.run_copy(resolve)
        self.assertEqual(code, 1)
        self.assertIn("GAP-07: jazari-root is resolved but does not meet a resolution path", err)

    def test_the_previous_consumer_still_verifies_this_version(self):
        old = subprocess.run(["git", "show", "48eac8a880e045459efff9e4cab29783cbbd23b7:examples/registry_consumer.py"],
                             cwd=REPO, capture_output=True, text=True)
        if old.returncode:
            self.skipTest("repository history not available")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "consumer_v060.py"
            path.write_text(old.stdout, encoding="utf-8")
            p = subprocess.run([sys.executable, "-I", str(path), "--source", str(REPO), "verify"], capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(f"registry {registry.load_all()[0]['version']}", p.stdout)


class RootSignatoriesDeferred(unittest.TestCase):
    def test_only_the_documented_root_signature_is_recorded(self):
        _, on = registry.load_all()
        signers = sorted(r["subject"] for r in on["relationships"] if (r["predicate"], r["object"]) == ("signatory_of", "jazari-root"))
        self.assertEqual(signers, ["cgem"])
        log = json.loads((REPO / "data" / "changelog.json").read_text(encoding="utf-8"))["entries"]
        v070 = next(e for e in log if e["version"] == "0.7.0")
        self.assertTrue(any("not added" in x and "represented by the undersigned" in x for x in v070["changes"]))


if __name__ == "__main__":
    unittest.main()
