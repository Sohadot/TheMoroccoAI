"""Sprint 08 Tier 2: targets, allocations, ministry-reported outputs and independent findings for the two strategies,
each kept in its own kind and never read as progress."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import registry  # noqa: E402
from test_precision import visible  # noqa: E402

TARGETS = {"MAI-EV-0050": 2026, "MAI-EV-0051": 2030, "MAI-EV-0052": 2026, "MAI-EV-0053": 2030, "MAI-EV-0058": 2030}
SPEND = re.compile(r"(?i)\b(?:was|were|has been|have been|had been)\s+(?:spent|disbursed|executed|paid)\b")


class StrategyMeasurement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.gaps = {g["id"]: g for g in json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))["gaps"]}

    def texts(self):
        out = [r[k] for r in self.evidence["records"] for k in ("claim", "verification_note")]
        out += [e.get(k, "") for e in self.ontology["entities"] for k in ("summary", "status", "note")]
        out += [x["text"] for g in self.gaps.values() for x in g["established"]] + [g["unestablished"] for g in self.gaps.values()]
        return out

    def test_each_figure_keeps_its_kind(self):
        for rid, year in TARGETS.items():
            self.assertEqual((self.records[rid]["classification"], self.records[rid]["target_year"]), ("OFFICIAL TARGET", year), rid)
        self.assertEqual(self.records["MAI-EV-0054"]["classification"], "VERIFIED FACT")
        self.assertEqual(self.records["MAI-EV-0057"]["classification"], "VERIFIED FACT")
        for rid in ("MAI-EV-0055", "MAI-EV-0056"):
            r = self.records[rid]
            self.assertEqual(r["classification"], "UNVERIFIED CLAIM", rid)
            self.assertIn("ministry-reported output", r["title"], rid)
            self.assertIn("A ministry-reported output", r["verification_note"], rid)
        for rid in [*TARGETS, "MAI-EV-0054", "MAI-EV-0055", "MAI-EV-0056", "MAI-EV-0057"]:
            self.assertNotIn("status_evidence", self.records[rid], rid)

    def test_an_allocation_is_never_presented_as_spending(self):
        note = self.records["MAI-EV-0054"]["verification_note"]
        self.assertIn("it is not expenditure", note)
        self.assertIn("loi de règlement", note)
        self.assertIn("payment appropriations", self.records["MAI-EV-0054"]["claim"])
        for t in self.texts():
            for sentence in re.split(r"(?<=[.;])\s+", t):
                if SPEND.search(sentence):
                    self.assertRegex(sentence, r"(?i)\b(?:not|no|nor|without)\b", sentence)
        gap = next(x["text"] for x in self.gaps["GAP-06"]["established"] if "1,500,000,000" in x["text"])
        self.assertIn("not expenditure", gap)
        self.assertIn("any amount actually spent", self.gaps["GAP-06"]["unestablished"])

    def test_indicators_with_different_definitions_stay_apart(self):
        self.assertIn("not a count of total digital jobs", self.records["MAI-EV-0055"]["verification_note"])
        self.assertIn("not graduates and not certified talents", self.records["MAI-EV-0056"]["verification_note"])
        self.assertIn("a different measure from the 200,000 talents trained and certified", self.records["MAI-EV-0058"]["verification_note"])
        self.assertIn("covers offshoring only", next(x["text"] for x in self.gaps["GAP-06"]["established"] if "270,000" in x["text"]))
        outputs = next(x["text"] for x in self.gaps["GAP-06"]["established"] if "148,500" in x["text"])
        self.assertIn("offshoring jobs are not total digital jobs", outputs)
        self.assertIn("enrolments are neither graduates nor certified talents", outputs)
        for t in self.texts():
            self.assertNotRegex(t, r"(?i)148,500[^.]*\b(?:direct|digital) jobs\b(?![^.]*\bnot\b)", t)

    def test_conflicting_targets_are_recorded_side_by_side(self):
        g = next(x for x in self.gaps["GAP-06"]["established"] if "190,000" in x["text"])
        for figure in ("75th", "85th", "101", "190,000", "270,000", "240,000"):
            self.assertIn(figure, g["text"])
        self.assertIn("does not reconcile", g["text"])
        self.assertEqual(set(g["evidence"]), {"MAI-EV-0049", "MAI-EV-0050", "MAI-EV-0051", "MAI-EV-0052", "MAI-EV-0053"})
        for rid in ("MAI-EV-0050", "MAI-EV-0051", "MAI-EV-0052", "MAI-EV-0053"):
            self.assertIn("predates the launch of Digital Morocco 2030", self.records[rid]["verification_note"], rid)

    def test_finance_law_rank_is_the_overall_egdi_not_the_online_services_index(self):
        for rid in ("MAI-EV-0050", "MAI-EV-0052"):
            note = self.records[rid]["verification_note"]
            self.assertIn("overall EGDI", note, rid)
            self.assertIn("not the Online Services Index", note, rid)
        for t in self.texts():
            for sentence in re.findall(r"[^.]*113th[^.]*\.", t):
                if re.search(r"(?i)\bverified\b", sentence):
                    self.assertRegex(sentence, r"(?i)\bnot\b", sentence)

    def test_the_audit_finding_is_a_pre_strategy_baseline(self):
        r = self.records["MAI-EV-0057"]
        self.assertIn("end of 2023", r["claim"])
        self.assertIn("pre-strategy baseline, not a measure of progress", r["verification_note"])
        self.assertIn("independent of the ministry", r["verification_note"])
        self.assertIn("does not set out its method", r["verification_note"])
        g = next(x["text"] for x in self.gaps["GAP-06"]["established"] if "605" in x["text"])
        self.assertIn("before the strategy's launch, not progress under it", g)

    def test_both_strategy_gaps_stay_open_and_q9_shows_no_measured_progress(self):
        self.assertEqual((self.gaps["GAP-02"]["state"], self.gaps["GAP-06"]["state"]), ("open", "open"))
        self.assertIn("MAI-EV-0058", self.gaps["GAP-02"]["assessed_records"])
        self.assertLessEqual({"MAI-EV-0050", "MAI-EV-0054", "MAI-EV-0055", "MAI-EV-0056", "MAI-EV-0057"}, set(self.gaps["GAP-06"]["assessed_records"]))
        q9 = visible("registry/questions/index.html")
        q9 = q9[q9.index("Q9 What does the registry establish"):]
        q9 = q9[:q9.index("Q5 ")]
        rows = [r for r in self.evidence["records"] if r["classification"] == "OFFICIAL TARGET"
                and any(e in ("digital-morocco-2030", "morocco-ai-2030") for e in r["related_entities"])]
        self.assertEqual(q9.count("No qualifying evidence is currently recorded in this registry."), len(rows))
        self.assertIn("finance-law performance documents, some of which predate the strategy", q9)
        self.assertIn("the conflict is recorded in the strategy's gap, not resolved", q9)

    def test_nothing_else_moved(self):
        self.assertEqual((len(self.ontology["entities"]), len(self.ontology["relationships"])), (65, 78))
        for e in self.ontology["entities"]:
            if e["id"].startswith("jazari"):
                self.assertEqual(e.get("lifecycle"), "announced" if e["type"] == "project" else None, e["id"])

    def test_the_v070_consumer_still_verifies_this_version(self):
        old = subprocess.run(["git", "show", "0d0fa8f51eb86076999ecee08a129ffdf68809e6:examples/registry_consumer.py"],
                             cwd=REPO, capture_output=True, text=True)
        if old.returncode:
            self.skipTest("repository history not available")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "consumer_v070.py"
            path.write_text(old.stdout, encoding="utf-8")
            p = subprocess.run([sys.executable, "-I", str(path), "--source", str(REPO), "verify"], capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(f"registry {self.evidence['version']}", p.stdout)


if __name__ == "__main__":
    unittest.main()
