"""Sprint 04: institutional matrix, evidence gap register and questions Q8–Q9.  Run: python3 -m unittest discover -s tests"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import registry  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def load_gaps():
    return registry.load(REPO / "data" / "gaps.json")


class MatrixIntegrity(unittest.TestCase):
    def setUp(self):
        self.evidence, self.ontology = registry.load_all()
        self.model = build.Model(self.evidence, self.ontology)
        self.rows = build.matrix_rows(self.model)
        self.canon = {(r["subject"], r["predicate"], r["object"]): r for r in registry.matrix_relationships(self.ontology)}

    def test_rows_are_exactly_the_canonical_relationships(self):
        ids = [r["id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)), "duplicate matrix rows")
        self.assertEqual(set(ids), {"|".join(k) for k in self.canon})
        self.assertEqual(ids, sorted(ids, key=lambda i: tuple(i.split("|"))), "rows must be in a stable order")

    def test_every_row_cites_exactly_its_relationships_records(self):
        for r in self.rows:
            rel = self.canon[tuple(r["id"].split("|"))]
            self.assertEqual([e["id"] for e in r["evidence"]], rel["evidence"], r["id"])
            self.assertEqual(r["classification"], rel["classification"], r["id"])
            for e in r["evidence"]:
                self.assertEqual(e["source_url"], self.model.records[e["id"]]["source_url"])

    def test_documented_as_never_exceeds_the_classification(self):
        for r in self.rows:
            if r["classification"] != "VERIFIED FACT":
                self.assertNotIn(r["documented_as"], ("Signed", "Operated", "Developed", "Documented"), r["id"])
            if r["classification"] == "ANNOUNCED PLAN":
                self.assertEqual(r["documented_as"], "Announced or planned", r["id"])
                self.assertIn("Not verified as delivered.", r["qualifications"], r["id"])

    def test_status_is_the_entitys_own_and_unknown_stays_unknown(self):
        for r in self.rows:
            obj = self.model.entities[r["object"]["id"]]
            self.assertEqual(r["object"]["lifecycle"], obj.get("lifecycle"))
            if obj.get("lifecycle") is None:
                self.assertIsNone(r["object"]["stage"], r["id"])
            else:
                self.assertEqual(r["object"]["stage"], build.stage_label(self.model, obj))

    def test_signed_but_undelivered_is_qualified(self):
        for r in self.rows:
            if r["documented_as"] == "Signed" and r["object"]["lifecycle"] == "announced":
                self.assertTrue(any("delivery is not documented" in q for q in r["qualifications"]), r["id"])

    def test_html_and_json_agree(self):
        data = json.loads((REPO / "registry" / "matrix" / "matrix.json").read_text(encoding="utf-8"))
        self.assertEqual(data["rows"], self.rows)
        self.assertEqual(data["registry_version"], self.evidence["version"])
        html = (REPO / "registry" / "matrix" / "index.html").read_text(encoding="utf-8")
        table = html[html.index("<table"):html.index("</table>")]
        self.assertEqual(table.count("<tr><td>"), len(self.rows))
        for r in self.rows:
            for e in r["evidence"]:
                self.assertIn(f'href="/registry/evidence/#{e["id"]}"', table)
        self.assertIn("It is not a complete map of Morocco's AI ecosystem", html)

    def test_unsupported_relationship_cannot_reach_the_matrix(self):
        # A relationship citing a record that does not document either end is rejected before rendering.
        o = copy.deepcopy(self.ontology)
        o["relationships"].append({"subject": "cgem", "predicate": "signatory_of", "object": "nexus-ai-factory",
                                   "evidence": ["MAI-EV-0009"], "classification": "VERIFIED FACT"})
        errors = registry.validate(self.evidence, o)
        self.assertTrue(any("documents neither end" in e for e in errors), errors)


class GapIntegrity(unittest.TestCase):
    def setUp(self):
        self.evidence, self.ontology = registry.load_all()
        self.gaps = load_gaps()

    def errors(self, gaps=None, evidence=None, ontology=None):
        return registry.validate_gaps(gaps or self.gaps, evidence or self.evidence, ontology or self.ontology)

    def gap(self, gid, gaps=None):
        return next(g for g in (gaps or self.gaps)["gaps"] if g["id"] == gid)

    def test_published_gaps_are_valid(self):
        self.assertEqual(self.errors(), [])

    def test_missing_evidence_is_never_stated_as_nonexistence(self):
        self.assertEqual(self.gaps["open_wording"], "No qualifying evidence is currently recorded in this registry.")
        g = copy.deepcopy(self.gaps)
        self.gap("GAP-01", g)["unestablished"] = "No evidence exists that anyone uses it."
        self.assertTrue(any("states absence in the world" in e for e in self.errors(g)))
        html = (REPO / "registry" / "gaps" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("No evidence exists", html)
        self.assertEqual(html.count(self.gaps["open_wording"]), sum(1 for x in self.gaps["gaps"] if x["state"] == "open"))

    def test_new_evidence_forces_reassessment(self):
        e = copy.deepcopy(self.evidence)
        rec = copy.deepcopy(next(r for r in e["records"] if r["evidence_id"] == "MAI-EV-0038"))
        rec["evidence_id"] = "MAI-EV-0999"
        e["records"].append(rec)
        self.assertTrue(any("GAP-01: new evidence MAI-EV-0999" in x for x in self.errors(evidence=e)))

    def test_resolving_without_evidence_is_rejected(self):
        g = copy.deepcopy(self.gaps)
        self.gap("GAP-03", g)["state"] = "resolved"
        errs = self.errors(g)
        self.assertTrue(any("must cite the existing records that resolve it" in x for x in errs), errs)

    def test_resolved_gap_cannot_keep_open_wording(self):
        g = copy.deepcopy(self.gaps)
        x = self.gap("GAP-03", g)
        x.update(state="resolved", resolved_by=["MAI-EV-0041"], unestablished="Scale. " + g["open_wording"])
        self.assertTrue(any("still displays the open wording" in e for e in self.errors(g)))

    def test_use_evidence_makes_gap_01_stale(self):
        e = copy.deepcopy(self.evidence)
        next(r for r in e["records"] if r["evidence_id"] == "MAI-EV-0034")["status_basis"] = "operator-report-of-use"
        self.assertTrue(any("GAP-01: is open but the data has changed" in x for x in self.errors(evidence=e)))

    def test_delivery_evidence_makes_gap_04_stale(self):
        o = copy.deepcopy(self.ontology)
        next(x for x in o["entities"] if x["id"] == "green-data-centres-agreement")["lifecycle"] = "operational"
        self.assertTrue(any("GAP-04: is open but the data has changed" in x for x in self.errors(ontology=o)))

    def test_established_statements_cite_records_about_the_gap(self):
        g = copy.deepcopy(self.gaps)
        self.gap("GAP-03", g)["established"].append({"text": "Unrelated.", "evidence": ["MAI-EV-0009"]})
        self.assertTrue(any("does not concern the gap's entities" in x for x in self.errors(g)))

    def test_dates_and_states_are_consistent(self):
        for x in self.gaps["gaps"]:
            self.assertIn(x["state"], registry.GAP_STATES)
            self.assertLessEqual(x["assessed"], self.evidence["as_of"])
        g = copy.deepcopy(self.gaps)
        self.gap("GAP-02", g)["assessed"] = "2030-01-01"
        self.assertTrue(any("assessed must be a valid date" in x for x in self.errors(g)))

    def test_gap_05_lists_exactly_the_computed_relationships(self):
        data = json.loads((REPO / "registry" / "gaps" / "gaps.json").read_text(encoding="utf-8"))
        g5 = next(x for x in data["gaps"] if x["id"] == "GAP-05")
        computed = ["|".join(k) for k in sorted((r["subject"], r["predicate"], r["object"]) for r in registry.announcement_only(self.ontology, self.evidence))]
        self.assertEqual([r["id"] for r in g5["relationships"]], computed)
        records = {r["evidence_id"]: r for r in self.evidence["records"]}
        for r in g5["relationships"]:
            self.assertTrue(all(records[x]["evidence_type"] in registry.ANNOUNCEMENT_TYPES for x in r["evidence"]), r["id"])

    def test_html_and_json_agree(self):
        data = json.loads((REPO / "registry" / "gaps" / "gaps.json").read_text(encoding="utf-8"))
        html = (REPO / "registry" / "gaps" / "index.html").read_text(encoding="utf-8")
        self.assertEqual([x["id"] for x in data["gaps"]], [x["id"] for x in self.gaps["gaps"]])
        for x in data["gaps"]:
            self.assertIn(f'id="{x["id"].lower()}"', html)
            self.assertEqual(x["open_wording"] is not None, x["state"] == "open")
            for item in x["established"]:
                for e in item["evidence"]:
                    self.assertIn(f'href="/registry/evidence/#{e}"', html)


class SemanticAudit(unittest.TestCase):
    """Sprint 04 pre-merge semantic audit: each contested claim, the inference it may support, and a guard against more."""

    def setUp(self):
        self.evidence, self.ontology = registry.load_all()
        self.records = {r["evidence_id"]: r for r in self.evidence["records"]}
        self.gaps = load_gaps()
        self.G = {g["id"]: g for g in self.gaps["gaps"]}

    def test_mai_ev_0041_supports_execution_not_scale_or_independence(self):
        r = self.records["MAI-EV-0041"]
        # Allowed: specific fine-tuning runs were executed on Toubkal, as its operator's authors report.
        self.assertTrue(any("performed on the Toubkal supercomputer by Belkasmi et al." in x for x in r["source_excerpts"]))
        self.assertIn("Belkasmi et al.", r["claim"])
        # Not allowed: scale, continuity, independent confirmation, or a stage change.
        for limit in ("not independent", "not the scale, share or continuity of AI use"):
            self.assertIn(limit, r["verification_note"])
        self.assertNotRegex(r["claim"], r"\b(widely|routinely|regularly|production use|thousands)\b")
        self.assertNotIn("status_evidence", r)

    def test_gap_03_does_not_deny_ai_use(self):
        g = self.G["GAP-03"]
        self.assertIn("This is not a finding that Toubkal is not used for AI", g["unestablished"])
        self.assertIn("MAI-EV-0041", [x for item in g["established"] for x in item["evidence"]])
        html = (REPO / "registry" / "gaps" / "index.html").read_text(encoding="utf-8")
        art = html[html.index('id="gap-03"'):html.index('id="gap-04"')]
        self.assertIn("its operator&#x27;s own authors report specific fine-tuning runs", art)

    def test_gap_05_measures_only_formal_acts_and_says_so(self):
        listed = registry.announcement_only(self.ontology, self.evidence)
        self.assertTrue(all(r["predicate"] in registry.FORMAL_ACT_PREDICATES for r in listed))
        for declared in ("presented", "launched", "organized", "includes", "implemented_through"):
            self.assertNotIn(declared, registry.FORMAL_ACT_PREDICATES)
        self.assertIn("not whether it is true", self.G["GAP-05"]["unestablished"])
        n, m = len(listed), len(registry.formal_act_relationships(self.ontology))
        matrix = (REPO / "registry" / "matrix" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"Of the {m} relationships that assert a formal act", matrix)
        self.assertIn(f"{n} rest only on announcements", matrix)
        self.assertIn("not whether they are true", matrix)

    def test_declarations_are_not_marked_as_weakly_documented(self):
        model = build.Model(self.evidence, self.ontology)
        for r in build.matrix_rows(model):
            if r["relationship"] not in registry.FORMAL_ACT_PREDICATES:
                self.assertEqual(r["documentation_basis"], "declaration-or-event", r["id"])
                self.assertFalse(any("GAP-05" in q for q in r["qualifications"]), r["id"])

    def _stale(self, mutate):
        e, o = copy.deepcopy(self.evidence), copy.deepcopy(self.ontology)
        mutate(e, o)
        return [x for x in registry.validate_gaps(self.gaps, e, o) if "has changed since it was assessed" in x]

    def test_editing_an_assessed_record_forces_reassessment(self):
        def reclassify(e, o):
            next(r for r in e["records"] if r["evidence_id"] == "MAI-EV-0041")["classification"] = "UNVERIFIED CLAIM"
        self.assertTrue(any(x.startswith("GAP-03") for x in self._stale(reclassify)))

    def test_superseding_a_cited_record_forces_reassessment(self):
        def supersede(e, o):
            next(r for r in e["records"] if r["evidence_id"] == "MAI-EV-0038")["superseded_by"] = ["MAI-EV-0034"]
        self.assertTrue(any(x.startswith("GAP-01") for x in self._stale(supersede)))

    def test_new_relationship_without_new_record_forces_reassessment(self):
        def relate(e, o):
            o["relationships"].append({"subject": "um6p", "predicate": "operates", "object": "toubkal-supercomputer",
                                       "evidence": ["MAI-EV-0041"], "classification": "VERIFIED FACT"})
        self.assertTrue(any(x.startswith("GAP-03") for x in self._stale(relate)))

    def test_changed_attribute_or_stage_forces_reassessment(self):
        def attr(e, o):
            next(x for x in o["entities"] if x["id"] == "idarati-ai")["attributes"].append({"name": "Users", "value": "1 million", "evidence": "MAI-EV-0034"})
        self.assertTrue(any(x.startswith("GAP-01") for x in self._stale(attr)))

    def test_mai_ev_0040_limits_absence_to_the_article(self):
        r = self.records["MAI-EV-0040"]
        self.assertIn("it gives no quantified progress", r["verification_note"])
        g = copy.deepcopy(self.gaps)
        next(x for x in g["gaps"] if x["id"] == "GAP-02")["unestablished"] = "No progress has been made."
        self.assertTrue(any("states absence in the world" in x for x in registry.validate_gaps(g, self.evidence, self.ontology)))


class QuestionsAndEvidence(unittest.TestCase):
    def setUp(self):
        self.evidence, self.ontology = registry.load_all()
        self.html = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")

    def section(self, qid, nxt):
        return self.html[self.html.index(f'id="{qid}"'):self.html.index(f'id="{nxt}"')]

    def test_q1_to_q7_are_preserved(self):
        for q in ("q1-h", "q2-h", "q3-h", "q4-h", "q5-h", "q6-h", "q7-h", "q8-h", "q9-h"):
            self.assertIn(f'id="{q}"', self.html)

    def test_q8_counts_match_the_matrix(self):
        model = build.Model(self.evidence, self.ontology)
        rows = [r for r in build.matrix_rows(model) if r["object"]["type"] == "project" and r["subject"]["type"] in ("institution", "company")]
        q8 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.section("q8-h", "q9-h")))
        self.assertIn(f"through {len(rows)} relationships", q8)
        self.assertIn("A signature or an announcement is not delivery", q8)

    def test_q9_never_shows_a_target_as_achieved(self):
        q9 = self.section("q9-h", "q5-h")
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", q9))
        self.assertIn("Targets are never shown as outcomes", text)
        self.assertNotRegex(text, r"\b(achieved|reached|met)\b")
        row = q9[q9.index('href="/registry/morocco-ai-2030/"'):]
        row = row[:row.index("</tr>")]
        self.assertIn("No qualifying evidence is currently recorded in this registry.", row)
        self.assertIn('href="/registry/gaps/#gap-02"', row)

    def test_new_records_cannot_set_a_stage(self):
        records = {r["evidence_id"]: r for r in self.evidence["records"]}
        for rid in ("MAI-EV-0040", "MAI-EV-0041"):
            self.assertNotIn("status_evidence", records[rid])
        toubkal = next(e for e in self.ontology["entities"] if e["id"] == "toubkal-supercomputer")
        self.assertEqual((toubkal["lifecycle"], toubkal["lifecycle_evidence"]), ("operational", ["MAI-EV-0020"]))

    def test_operator_workload_report_is_not_presented_as_independent(self):
        rec = next(r for r in self.evidence["records"] if r["evidence_id"] == "MAI-EV-0041")
        self.assertIn("not independent", rec["verification_note"])
        page = (REPO / "registry" / "toubkal-supercomputer" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Reported AI workloads (operator-affiliated authors)", page)

    def test_new_pages_are_discoverable(self):
        for f in (REPO / "registry" / "index.html", REPO / "registry" / "questions" / "index.html", REPO / "index.html"):
            html = f.read_text(encoding="utf-8")
            self.assertIn('href="/registry/matrix/"', html, f)
            self.assertIn('href="/registry/gaps/"', html, f)


if __name__ == "__main__":
    unittest.main()
