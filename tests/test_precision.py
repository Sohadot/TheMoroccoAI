"""Sprint 06: evidence basis of signatures, Q8 scope, and progress gaps for every strategy with a target."""
import contextlib
import copy
import html
import importlib.util
import io
import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import build  # noqa: E402
import registry  # noqa: E402
from test_consumer import PublishedCopy  # noqa: E402

_spec = importlib.util.spec_from_file_location("registry_consumer", REPO / "examples" / "registry_consumer.py")
consumer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(consumer)


def visible(path):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", (REPO / path).read_text(encoding="utf-8"))))


class SignedRelationships(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.model = build.Model(cls.evidence, cls.ontology)
        cls.rows = build.matrix_rows(cls.model)

    def test_every_signature_states_its_evidence_basis(self):
        signed = [r for r in self.rows if r["documented_as"] == "Signed"]
        self.assertEqual(len(signed), 16)
        for r in signed:
            types = {e["evidence_type"] for e in r["evidence"]}
            self.assertNotIn("signed_instrument", types, r["id"])
            self.assertIn(build.SIGNED_TEXT_NOT_RECORDED, r["qualifications"], r["id"])

    def test_announcement_only_and_official_report_signatures_are_distinguished(self):
        signed = [r for r in self.rows if r["documented_as"] == "Signed"]
        ann = [r for r in signed if r["documentation_basis"] == "announcement-or-description"]
        other = [r for r in signed if r["documentation_basis"] == "includes-non-announcement-record"]
        self.assertEqual((len(ann), len(other)), (10, 6))
        for r in ann:
            self.assertIn(build.GAP05_CAVEAT, r["qualifications"])
        for r in other:
            self.assertNotIn(build.GAP05_CAVEAT, r["qualifications"])
            self.assertTrue(any(e["evidence_type"] == "official_report" for e in r["evidence"]), r["id"])

    def test_a_signed_text_would_lift_the_caveat(self):
        ev = copy.deepcopy(self.evidence)
        rec = next(r for r in ev["records"] if r["evidence_id"] == "MAI-EV-0009")
        rec["evidence_type"] = "signed_instrument"
        rows = build.matrix_rows(build.Model(ev, self.ontology))
        x0 = [r for r in rows if r["object"]["id"] == "jazari-industrie-x0" and r["documented_as"] == "Signed"]
        self.assertEqual(len(x0), 7)
        for r in x0:
            self.assertNotIn(build.SIGNED_TEXT_NOT_RECORDED, r["qualifications"])
            self.assertEqual(r["documentation_basis"], "includes-non-announcement-record")

    def test_classifications_and_stages_are_unchanged(self):
        # Sprint 06 corrects presentation only: the signatures stay VERIFIED FACT on the same records.
        for r in self.ontology["relationships"]:
            if r["predicate"] == "signatory_of" and r["object"] in ("jazari-industrie-x0", "jazari-root", "deepecho-public-health-evaluation"):
                self.assertEqual(r["classification"], "VERIFIED FACT")
        self.assertTrue(all(e["lifecycle"] == "announced" for e in self.ontology["entities"]
                            if e["id"] in ("jazari-industrie-x0", "jazari-root", "deepecho-public-health-evaluation")))

    def test_no_published_text_implies_the_instrument_is_recorded(self):
        for path in ("registry/matrix/index.html", "registry/gaps/index.html", "data/index.html", "registry/questions/index.html"):
            text = visible(path)
            self.assertNotIn("includes-formal-record", text, path)
            self.assertNotRegex(text, r"(?i)the instrument behind them is not recorded", path)
        for path in ("registry/matrix/matrix.json", "registry/gaps/gaps.json"):
            data = json.loads((REPO / path).read_text(encoding="utf-8"))
            if "rows" in data:
                self.assertEqual({r["documentation_basis"] for r in data["rows"]},
                                 {"announcement-or-description", "includes-non-announcement-record", "declaration-or-event"})
        self.assertIn('For none of the 16 "Signed" rows is the signed text recorded', visible("registry/matrix/index.html"))
        gap05 = next(g for g in json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))["gaps"] if g["id"] == "GAP-05")
        self.assertIn("not the signed text", gap05["unestablished"])


class Q8Scope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = build.Model(*registry.load_all())
        page = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        cls.section = page[page.index('id="q8-h"'):page.index('id="q9-h"')]
        cls.text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", cls.section)))

    def test_heading_does_not_overstate(self):
        heading = self.text[:self.text.index("?") + 1]
        self.assertNotIn("documented AI", heading)
        self.assertIn("projects recorded in this registry", heading)

    def test_scope_is_every_project_kind_and_is_disclosed(self):
        rows = [r for r in build.matrix_rows(self.model) if r["object"]["type"] == "project" and r["subject"]["type"] in ("institution", "company")]
        projects = {r["object"]["id"] for r in rows}
        # No project kind is filtered out: every project an organisation is connected to is counted.
        every = {r["object"] for r in self.model.relationships if self.model.entities[r["object"]]["type"] == "project"
                 and self.model.entities[r["subject"]]["type"] in ("institution", "company")
                 and r["predicate"] in self.model.predicates}
        self.assertEqual(projects, every)
        kinds, stages = {}, {}
        for p in projects:
            e = self.model.entities[p]
            kinds[e["project_kind"]] = kinds.get(e["project_kind"], 0) + 1
            stages[e["lifecycle"]] = stages.get(e["lifecycle"], 0) + 1
        for k, v in kinds.items():
            self.assertIn(f"{v} {build.KIND_COUNT_LABELS[k][v != 1]}", self.text)
        for k, v in stages.items():
            self.assertIn(f"{v} {build.LIFECYCLE_LABELS[k].lower()}", self.text)
        self.assertIn("not itself an AI system", self.text)
        self.assertIn("None of the 16 signatures is documented by its signed text", self.text)


class TargetsAndProgress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.gaps = registry.load(REPO / "data" / "gaps.json")

    def test_every_strategy_with_a_target_has_a_progress_gap(self):
        self.assertEqual(registry.validate_gaps(self.gaps, self.evidence, self.ontology), [])
        gaps = copy.deepcopy(self.gaps)
        gaps["gaps"] = [g for g in gaps["gaps"] if g["id"] != "GAP-06"]
        self.assertIn("gaps.json: digital-morocco-2030 has an official target (MAI-EV-0002) but no gap covers its progress",
                      registry.validate_gaps(gaps, self.evidence, self.ontology))

    def test_gap_06_separates_targets_spending_and_progress(self):
        g = next(g for g in self.gaps["gaps"] if g["id"] == "GAP-06")
        self.assertEqual(g["state"], "open")
        self.assertEqual(g["checks"], [])
        self.assertEqual(sorted(g["assessed_records"]), ["MAI-EV-0001", "MAI-EV-0002", "MAI-EV-0003", "MAI-EV-0018"])
        spending = next(x for x in g["established"] if x["evidence"] == ["MAI-EV-0003"])
        self.assertIn("has not checked these figures", spending["text"])
        self.assertIn("spending is an input, not a measure of the targets", spending["text"])
        rec = next(r for r in self.evidence["records"] if r["evidence_id"] == "MAI-EV-0003")
        self.assertEqual(rec["classification"], "UNVERIFIED CLAIM")
        self.assertNotRegex(g["unestablished"] + g["question"], r"(?i)\b(no progress|has not progressed|failed|achieved)\b")

    def test_q9_reports_no_target_as_not_assessed_or_achieved(self):
        page = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        q9 = page[page.index('id="q9-h"'):page.index('id="q5-h"')]
        self.assertNotIn("Not yet assessed", q9)
        self.assertIn("#gap-06", q9)
        self.assertNotRegex(re.sub(r"<[^>]+>", " ", q9), r"(?i)\b(achieved|has reached|accomplished)\b")

    def test_gap_06_is_reassessed_when_its_data_moves(self):
        ev = copy.deepcopy(self.evidence)
        next(r for r in ev["records"] if r["evidence_id"] == "MAI-EV-0003")["claim"] += " Edited."
        self.assertTrue(any(e.startswith("GAP-06: data this gap rests on has changed") for e in registry.validate_gaps(self.gaps, ev, self.ontology)))
        ev = copy.deepcopy(self.evidence)
        new = copy.deepcopy(next(r for r in ev["records"] if r["evidence_id"] == "MAI-EV-0001"))
        new["evidence_id"] = "MAI-EV-0099"
        ev["records"].append(new)
        self.assertTrue(any(e.startswith("GAP-06: new evidence MAI-EV-0099") for e in registry.validate_gaps(self.gaps, ev, self.ontology)))


class ConsumerCompatibility(unittest.TestCase):
    def run_consumer(self, root, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = consumer.main(["--source", str(root), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_consumer_verifies_the_new_version(self):
        code, out, err = self.run_consumer(REPO, "verify")
        self.assertEqual(code, 0, err)
        self.assertIn("registry 0.5.0", out)
        self.assertIn("6 gaps", out)

    def test_consumer_takes_basis_names_from_the_data(self):
        # Renaming a basis value consistently in matrix.json and gaps.json must not break the consumer.
        copy_ = PublishedCopy()
        try:
            def rename(d):
                d["derivation"]["documentation_basis"]["assignment"]["otherwise"] = "renamed-basis"
                for r in d["rows"]:
                    if r["documentation_basis"] == "includes-non-announcement-record":
                        r["documentation_basis"] = "renamed-basis"
            copy_.edit("/registry/matrix/matrix.json", rename)
            code, out, err = copy_.verify()
            self.assertEqual(code, 0, err)
        finally:
            copy_.cleanup()

    def test_the_v041_name_is_rejected_clearly(self):
        copy_ = PublishedCopy()
        try:
            def old(d):
                next(r for r in d["rows"] if r["documentation_basis"] == "includes-non-announcement-record")["documentation_basis"] = "includes-formal-record"
            copy_.edit("/registry/matrix/matrix.json", old)
            code, out, err = copy_.verify()
            self.assertEqual(code, 1)
            self.assertIn("has documentation_basis 'includes-formal-record'", err)
        finally:
            copy_.cleanup()

    def test_signed_text_is_reserved_in_the_vocabulary(self):
        manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("signed_instrument", manifest["vocabularies"]["evidence_type"])
        self.assertFalse(any(r["evidence_type"] == "signed_instrument" for r in registry.load_all()[0]["records"]))


if __name__ == "__main__":
    unittest.main()
