"""Sprint 09 Tier 2: budget execution evidence and conflicting target statements for Digital Morocco 2030.
An allocation is not expenditure, a ministry total is not spending on the strategy, a project code is not compared across
years whose labels differ, and conflicting statements are recorded side by side, never reconciled."""
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

EXECUTION = ("MAI-EV-0060", "MAI-EV-0061")
STRATEGIES = ("digital-morocco-2030", "morocco-ai-2030")
OSI = re.compile(r"(?i)online services? index|\bOSI\b")
ORDINAL = re.compile(r"\b\d+(?:st|nd|rd|th)\b")
# Every rank the registry's sources state for these indices: the strategy's 113th and 50th, the finance-law EGDI targets
# 75th and 85th, and the United Nations' published EGDI ranks 101st and 90th.
SOURCED_RANKS = {"113th", "50th", "75th", "85th", "101st", "90th"}


def sentences(text):
    return re.split(r"(?<=[.;])\s+", text)


class ExecutionEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.entities = {e["id"]: e for e in cls.ontology["entities"]}
        cls.gaps = {g["id"]: g for g in json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))["gaps"]}
        cls.changelog = json.loads((REPO / "data" / "changelog.json").read_text(encoding="utf-8"))["entries"]

    def texts(self):
        out = [x for r in self.evidence["records"] for x in (r["title"], r["claim"], r["verification_note"], *r["source_excerpts"])]
        out += [e.get(k, "") for e in self.ontology["entities"] for k in ("summary", "status", "note")]
        out += [x["text"] for g in self.gaps.values() for x in g["established"]]
        out += [g["unestablished"] for g in self.gaps.values()] + [x for g in self.gaps.values() for x in g["evidence_needed"]]
        out += [x for e in self.changelog for k in ("changes", "corrections", "review_fixes") for x in e.get(k, [])]
        return out

    def pages(self):
        return [visible(str(p.relative_to(REPO))) for p in sorted(REPO.glob("**/index.html")) if ".git" not in p.parts]

    def test_each_record_keeps_its_kind(self):
        kinds = {"MAI-EV-0059": ("VERIFIED FACT", None), "MAI-EV-0060": ("VERIFIED FACT", None), "MAI-EV-0061": ("VERIFIED FACT", None),
                 "MAI-EV-0062": ("OFFICIAL TARGET", 2030), "MAI-EV-0063": ("OFFICIAL TARGET", 2030)}
        for rid, kind in kinds.items():
            r = self.records[rid]
            self.assertEqual((r["classification"], r.get("target_year")), kind, rid)
            self.assertNotIn("status_evidence", r, rid)
        self.assertIn("payment appropriations for 2025", self.records["MAI-EV-0059"]["claim"])
        self.assertIn("it is not expenditure", self.records["MAI-EV-0059"]["verification_note"])

    def test_ministry_execution_is_never_attributed_to_a_strategy(self):
        for rid in EXECUTION:
            r = self.records[rid]
            self.assertEqual(r["related_entities"], ["ministry-digital-transition"], rid)
            self.assertIn("ministry-level total", r["title"], rid)
            self.assertIn("so it is not spending on Digital Morocco 2030, and the record is not related to the strategy", r["verification_note"], rid)
            self.assertIn(rid, self.entities["ministry-digital-transition"]["evidence"])
            for s in STRATEGIES:
                self.assertNotIn(rid, self.entities[s]["evidence"], (rid, s))
                # The strategy's page may show the allocation record's note, which points to the ministry-level totals.
                page = visible(f"registry/{s}/index.html").replace(self.records["MAI-EV-0059"]["verification_note"], "")
                self.assertNotIn(rid, page, (rid, s))
            for g in self.gaps.values():
                for x in g["established"]:
                    self.assertNotIn(rid, x["evidence"], (rid, g["id"]))
        for rel in self.ontology["relationships"]:
            self.assertFalse(set(EXECUTION) & set(rel.get("evidence") or []), rel)
        # Money is never said to have been spent on a strategy, unless the sentence denies or questions it before saying so.
        for t in self.texts() + self.pages():
            for s in sentences(t):
                m = re.search(r"(?i)\b(?:spent|disbursed|executed)\s+(?:on|for|under)\s+(?:the\s+)?(?:Maroc Digital|Digital Morocco|Morocco AI|strateg)", s)
                if m:
                    self.assertRegex(s[:m.start()], r"(?i)\b(?:not|no|nor|never|any|without|whether|showing)\b", s)
        # The executed amounts never appear beside a strategy in the same sentence, unless that sentence denies the link.
        for t in self.texts() + self.pages():
            for s in sentences(t):
                if re.search(r"1,704|1\.704|1,348\.7|1\.348,7", s) and re.search(r"(?i)strateg|Digital Morocco|Maroc Digital|Morocco AI", s):
                    self.assertRegex(s, r"(?i)\b(?:not|no)\b", s)

    def test_yearly_appropriations_are_never_added_together(self):
        self.assertIn("are not added together", self.records["MAI-EV-0059"]["verification_note"])
        st = next(x for x in self.gaps["GAP-06"]["established"] if "1,500,000,000" in x["text"])
        self.assertEqual(set(st["evidence"]), {"MAI-EV-0054", "MAI-EV-0059"})
        self.assertIn("each provide MAD 1,500,000,000", st["text"])
        self.assertIn("not expenditure, and the two are not added together", st["text"])
        for t in self.texts() + self.pages():
            self.assertNotRegex(t, r"(?i)3,000,000,000|3\.0 billion|MAD 3 billion|3 milliards", t[:200])

    def test_project_20_is_not_compared_across_years(self):
        for rid in ("MAI-EV-0059", "MAI-EV-0060"):
            self.assertIn("project 20 of programme 429 was \"Développement de l'Administration Numérique\"", self.records[rid]["verification_note"], rid)
        st = next(x for x in self.gaps["GAP-06"]["established"] if "1,500,000,000" in x["text"])
        self.assertIn("a code that designated a different line in the 2024 finance law", st["text"])
        self.assertNotIn("273,000,000", " ".join(x["text"] for g in self.gaps.values() for x in g["established"]))

    def test_execution_bases_are_not_combined(self):
        note = self.records["MAI-EV-0061"]["verification_note"]
        self.assertIn("excludes credits carried over", note)
        self.assertIn("the two are not combined", note)
        self.assertIn("provisional until the settlement law for 2025", note)
        self.assertIn("is not an independent measurement", self.records["MAI-EV-0060"]["verification_note"])
        self.assertIn("Manual visual verification was required", self.records["MAI-EV-0060"]["verification_note"])
        for t in self.texts() + self.pages():
            for s in sentences(t):
                self.assertFalse(re.search(r"1,704|1\.704", s) and re.search(r"1,348\.7|1\.348,7", s), s)

    def test_egdi_and_osi_statements_of_the_objective_stay_side_by_side(self):
        est = self.gaps["GAP-06"]["established"]
        brochure = next(x for x in est if "113th to 50th" in x["text"])
        egdi = next(x for x in est if "MAI-EV-0062" in x["evidence"])
        self.assertEqual(est.index(egdi), est.index(brochure) + 1)
        self.assertIn("overall e-government development index, not on the Online Services Index", egdi["text"])
        self.assertIn("the registry does not reconcile them", egdi["text"])
        self.assertIn("the Online Services Index, a component of the EGDI (MAI-EV-0049)", self.records["MAI-EV-0062"]["verification_note"])
        self.assertIn("Online Services Index", self.records["MAI-EV-0049"]["claim"])
        self.assertIn("the registry does not reconcile the two", self.entities["digital-morocco-2030"]["summary"])

    def test_the_offshoring_target_is_not_a_reconciliation(self):
        st = next(x for x in self.gaps["GAP-06"]["established"] if x["evidence"] == ["MAI-EV-0063"])
        self.assertIn("attributes that figure to the offshoring sector", st["text"])
        self.assertIn("the registry does not reconcile them", st["text"])
        conflict = next(x for x in self.gaps["GAP-06"]["established"] if "190,000" in x["text"])
        self.assertIn("does not reconcile", conflict["text"])
        note = self.records["MAI-EV-0063"]["verification_note"]
        self.assertIn("offshoring jobs are not total digital jobs", note)
        self.assertIn("The registry has not read the circular itself", note)
        self.assertIn("130,000 direct jobs, which differs from the more than 148,500", note)

    def test_both_enrolment_figures_are_kept(self):
        r = self.records["MAI-EV-0056"]
        self.assertIn("22,649", r["claim"])
        self.assertIn("gives 22,258 new students for 2024–2025", r["verification_note"])
        self.assertIn("the registry records both figures and does not resolve the difference", r["verification_note"])
        v090 = next(e for e in self.changelog if e["version"] == "0.9.0")
        self.assertTrue(any("22,258" in c for c in v090["corrections"]))

    def test_no_osi_rank_is_published_beyond_the_sourced_ones(self):
        self.assertIn("The registry does not compute a rank from the published values", self.records["MAI-EV-0046"]["verification_note"])
        un = next(x for x in self.gaps["GAP-06"]["established"] if "0.47210" in x["text"])
        self.assertIn("publish the index's values without a rank column", un["text"])
        self.assertIn("a rank on the Online Services Index published by the United Nations", self.gaps["GAP-06"]["unestablished"])
        docs = [p.read_text(encoding="utf-8") for p in sorted(REPO.glob("*.md"))]
        for t in self.texts() + self.pages() + docs:
            for s in sentences(t):
                if OSI.search(s):
                    self.assertLessEqual(set(ORDINAL.findall(s)), SOURCED_RANKS, s)
                self.assertNotRegex(s, r"(?i)\b(?:derived|computed|calculated)\s+(?:OSI\s+|online services? index\s+)?(?:rank|position)\s+(?:of\s+)?\d", s)
            self.assertNotRegex(t, r"\b100th\b")

    def test_counts_and_gaps(self):
        self.assertEqual(self.evidence["version"], "0.9.0")
        self.assertEqual(len(self.evidence["records"]), 63)
        self.assertEqual((len(self.ontology["entities"]), len(self.ontology["relationships"])), (65, 78))
        self.assertEqual({g["state"] for g in self.gaps.values()}, {"open"})
        self.assertLessEqual({"MAI-EV-0059", "MAI-EV-0062", "MAI-EV-0063"}, set(self.gaps["GAP-06"]["assessed_records"]))
        rows = [r for r in self.evidence["records"] if r["classification"] == "OFFICIAL TARGET" and set(STRATEGIES) & set(r["related_entities"])]
        self.assertEqual(len(rows), 10)

    def test_the_v080_consumer_still_verifies_this_version(self):
        old = subprocess.run(["git", "show", "59c4221:examples/registry_consumer.py"], cwd=REPO, capture_output=True, text=True)
        if old.returncode:
            self.skipTest("repository history not available")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "consumer_v080.py"
            path.write_text(old.stdout, encoding="utf-8")
            p = subprocess.run([sys.executable, "-I", str(path), "--source", str(REPO), "verify"], capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("registry 0.9.0", p.stdout)


if __name__ == "__main__":
    unittest.main()
