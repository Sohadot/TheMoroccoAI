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
        self.assertEqual(len(signed), sum(1 for r in self.ontology["relationships"]
                                          if r["predicate"] == "signatory_of" and r["classification"] == "VERIFIED FACT"))
        for r in signed:
            types = {e["evidence_type"] for e in r["evidence"]}
            self.assertNotIn("signed_instrument", types, r["id"])
            self.assertIn(build.SIGNED_TEXT_NOT_RECORDED, r["qualifications"], r["id"])

    def test_announcement_only_and_official_report_signatures_are_distinguished(self):
        signed = [r for r in self.rows if r["documented_as"] == "Signed"]
        ann = [r for r in signed if r["documentation_basis"] == "announcement-or-description"]
        other = [r for r in signed if r["documentation_basis"] == "includes-non-announcement-record"]
        self.assertEqual(len(ann) + len(other), len(signed))
        for r in ann:
            self.assertIn(build.GAP05_CAVEAT, r["qualifications"])
            self.assertTrue(all(e["evidence_type"] in registry.ANNOUNCEMENT_TYPES for e in r["evidence"]), r["id"])
        for r in other:
            self.assertNotIn(build.GAP05_CAVEAT, r["qualifications"])
            # An official report or a gazette text: a record of the signing, never the signed text.
            self.assertTrue(any(e["evidence_type"] in ("official_report", "official_gazette") for e in r["evidence"]), r["id"])
            self.assertIn(build.SIGNED_TEXT_NOT_RECORDED, r["qualifications"])

    @staticmethod
    def instrument_record(ev, signatories):
        """MAI-EV-0009 turned into a record of the convention's text, as a hypothetical."""
        rec = next(r for r in ev["records"] if r["evidence_id"] == "MAI-EV-0009")
        rec.update(evidence_type="signed_instrument", source_type="government_publication",
                   instrument={"title": "Convention pour la création de l'Institut Al-Jazari pour l'Industrie", "signed_on": "2026-03-10",
                               "signatories": signatories, "access": "full-text-read"})
        return rec

    def test_a_signed_text_lifts_the_caveat_only_for_its_signatories(self):
        ev = copy.deepcopy(self.evidence)
        self.instrument_record(ev, ["ministry-industry-commerce", "uemf"])
        rows = build.matrix_rows(build.Model(ev, self.ontology))
        x0 = {r["subject"]["id"]: r for r in rows if r["object"]["id"] == "jazari-industrie-x0" and r["documented_as"] == "Signed"}
        self.assertEqual(len(x0), 7)
        for sid, r in x0.items():
            self.assertEqual(build.SIGNED_TEXT_NOT_RECORDED in r["qualifications"], sid not in ("ministry-industry-commerce", "uemf"), sid)
            self.assertEqual(r["documentation_basis"], "includes-non-announcement-record")

    def test_signed_instrument_admission_rules(self):
        def problems(change):
            ev = copy.deepcopy(self.evidence)
            rec = self.instrument_record(ev, ["ministry-industry-commerce", "ministry-digital-transition", "ministry-economy-finance",
                                              "uemf", "usmba", "umi", "al-akhawayn-university"])
            change(rec)
            return [e for e in registry.validate_evidence(ev) + registry.validate_ontology(self.ontology, ev) if "MAI-EV-0009" in e or "signed text" in e]
        self.assertEqual(problems(lambda r: None), [])
        cases = {
            "a report of the signing": (lambda r: r.update(source_type="state_news_agency"), "must come from a party or an official publisher"),
            "the press": (lambda r: r.update(source_type="secondary_press"), "must come from a party or an official publisher"),
            "partial reading": (lambda r: r.update(verification_status="partial"), "full text read"),
            "not a fact": (lambda r: r.update(classification="ANNOUNCED PLAN"), "must be a VERIFIED FACT"),
            "no instrument": (lambda r: r.pop("instrument"), "needs an instrument field"),
            "access not declared": (lambda r: r["instrument"].update(access="summary"), "must have read the signed text itself"),
            "no date": (lambda r: r["instrument"].pop("signed_on"), "needs signed_on"),
            "one party": (lambda r: r["instrument"].update(signatories=["uemf"]), "at least two parties"),
            "signatory not related": (lambda r: r["instrument"]["signatories"].append("cgem"), "each among related_entities"),
            "relationship outside the signatories": (lambda r: r["instrument"].update(signatories=["uemf", "usmba"]), "whose signatories do not include"),
        }
        for name, (change, msg) in cases.items():
            with self.subTest(name):
                self.assertTrue(any(msg in e for e in problems(change)), problems(change))
        ev = copy.deepcopy(self.evidence)
        ev["records"][0]["instrument"] = {"title": "x"}
        self.assertTrue(any("only a signed_instrument record may carry an instrument field" in e for e in registry.validate_evidence(ev)))

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
            if path == "data/index.html":
                # The old value may appear only in the migration note.
                text = text[:text.index("09 Changes to the data contract")] + text[text.index("10 Corrections"):]
            self.assertNotIn("includes-formal-record", text, path)
            self.assertNotRegex(text, r"(?i)the instrument behind them is not recorded", path)
        for path in ("registry/matrix/matrix.json", "registry/gaps/gaps.json"):
            data = json.loads((REPO / path).read_text(encoding="utf-8"))
            if "rows" in data:
                self.assertEqual({r["documentation_basis"] for r in data["rows"]},
                                 {"announcement-or-description", "includes-non-announcement-record", "declaration-or-event"})
        n = sum(1 for r in self.rows if r["documented_as"] == "Signed")
        self.assertIn(f'For none of the {n} "Signed" rows is the signed text recorded', visible("registry/matrix/index.html"))
        gap05 = next(g for g in json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))["gaps"] if g["id"] == "GAP-05")
        self.assertIn("Neither is the signed text", gap05["unestablished"])


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
        n = sum(1 for r in rows if r["documented_as"] == "Signed")
        self.assertIn(f"None of the {n} signatures is documented by its signed text", self.text)


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
        self.assertLessEqual({"MAI-EV-0001", "MAI-EV-0002", "MAI-EV-0003", "MAI-EV-0018"}, set(g["assessed_records"]))
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


class BreakingChangeNotice(unittest.TestCase):
    def test_rename_is_documented_as_breaking_everywhere_and_without_alias(self):
        manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
        bc = manifest["breaking_changes"]
        self.assertEqual([(c["version"], c["old"], c["new"]) for c in bc],
                         [("0.5.0", "includes-formal-record", "includes-non-announcement-record")])
        for key in ("file", "field", "reason", "consumer_effect", "migration"):
            self.assertTrue(bc[0][key].strip(), key)
        self.assertIn("only the name changed", bc[0]["reason"])
        self.assertIn("exits with status 1", bc[0]["consumer_effect"])
        page = visible("data/index.html")
        note = page[page.index("09 Changes to the data contract"):page.index("10 Corrections")]
        for x in ("includes-formal-record", "includes-non-announcement-record", "not accepted as aliases", "only the name changed"):
            self.assertIn(x, note)
        log = next(e for e in json.loads((REPO / "data" / "changelog.json").read_text(encoding="utf-8"))["entries"]
                   if e["version"] == "0.5.0")
        self.assertTrue(any("includes-formal-record" in x and "No alias" in x for x in log["breaking_changes"]))
        self.assertIn("Breaking changes to the data contract", visible("methodology/index.html"))
        # No alias: no published JSON value and no consumer path accepts the old name.
        matrix = (REPO / "registry" / "matrix" / "matrix.json").read_text(encoding="utf-8")
        self.assertNotIn("includes-formal-record", matrix)
        self.assertNotIn("includes-formal-record", (REPO / "examples" / "registry_consumer.py").read_text(encoding="utf-8"))

    def test_v041_consumer_fails_closed_as_documented(self):
        import subprocess
        old = subprocess.run(["git", "show", "c6211538caa4285b446644d3cf38cd2e55ae7f7f:examples/registry_consumer.py"],
                             cwd=REPO, capture_output=True, text=True)
        if old.returncode:
            self.skipTest("repository history not available")
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "consumer_v041.py"
            path.write_text(old.stdout, encoding="utf-8")
            p = subprocess.run([sys.executable, "-I", str(path), "--source", str(REPO), "verify"], capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 1)
        self.assertIn("has documentation_basis 'includes-non-announcement-record'; the published data gives 'includes-formal-record'", p.stderr)


class JazariWording(unittest.TestCase):
    def test_no_jazari_text_implies_a_recorded_instrument_or_delivery(self):
        ev, on = registry.load_all()
        texts = [e.get(k, "") for e in on["entities"] if "jazari" in e["id"] for k in ("summary", "status", "note")]
        texts += [r.get("note", "") for r in on["relationships"] if "jazari" in r["subject"] + r["object"]]
        texts += [r["verification_note"] for r in ev["records"] if any("jazari" in x for x in r["related_entities"])]
        for t in texts:
            self.assertNotRegex(t, r"(?i)(signed|founding) instruments? (is|are) documented|documents signed instruments", t)
            self.assertNotRegex(t, r"(?i)\b(is|are|was|were) (operational|constituted|established|running)\b", t)
        for e in on["entities"]:
            if "jazari" in e["id"] and e.get("lifecycle"):
                self.assertEqual(e["lifecycle"], "announced", e["id"])
        rel = next(r for r in on["relationships"] if (r["subject"], r["predicate"]) == ("morocco-ai-2030", "implemented_through"))
        self.assertIn("implementation through the network is not documented", rel["note"])
        self.assertIn("its planned core institute", visible("registry/index.html"))


class ConsumerCompatibility(unittest.TestCase):
    def run_consumer(self, root, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = consumer.main(["--source", str(root), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_consumer_verifies_the_new_version(self):
        code, out, err = self.run_consumer(REPO, "verify")
        self.assertEqual(code, 0, err)
        self.assertIn(f"registry {registry.load_all()[0]['version']}", out)
        self.assertIn(f"{len(json.loads((REPO / 'data' / 'gaps.json').read_text(encoding='utf-8'))['gaps'])} gaps", out)

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


class EvidenceAcquisition(unittest.TestCase):
    """Sprint 07: what the gazette, the ministry releases, the preprints and the UN entry may and may not establish."""

    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.gaps = json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))

    def errors(self, mutate):
        ev, on = copy.deepcopy(self.evidence), copy.deepcopy(self.ontology)
        mutate(ev, on)
        return registry.validate(ev, on)

    def test_a_gazette_cannot_set_a_stage_or_show_use(self):
        def stage(ev, on):
            r = next(r for r in ev["records"] if r["evidence_id"] == "MAI-EV-0047")
            r.update(status_evidence="operational", status_basis="operator-reported-use", source_entity="cgem")
        errs = self.errors(stage)
        self.assertTrue(any("an official gazette cannot evidence a lifecycle status" in e for e in errs), errs)
        self.assertTrue(any("official gazette cannot evidence 'operational'" in e for e in errs), errs)

    def test_a_gazette_cannot_document_an_operator(self):
        def operates(ev, on):
            on["relationships"].append({"subject": "cgem", "predicate": "operates", "object": "jazari-root",
                                        "evidence": ["MAI-EV-0047"], "classification": "VERIFIED FACT"})
        self.assertTrue(any("a verified operator must be documented" in e for e in self.errors(operates)))

    def test_gazette_is_not_a_signed_instrument_and_stages_stay_announced(self):
        r = self.records["MAI-EV-0047"]
        self.assertEqual(r["evidence_type"], "official_gazette")
        self.assertNotIn("status_evidence", r)
        self.assertIn("not the signed text", r["verification_note"])
        for e in self.ontology["entities"]:
            if e["id"].startswith("jazari-") and e.get("lifecycle"):
                self.assertEqual(e["lifecycle"], "announced", e["id"])

    def test_gazette_moves_the_jazari_signatures_out_of_gap_05(self):
        cited = [r for r in self.ontology["relationships"] if "MAI-EV-0047" in r["evidence"]]
        self.assertEqual(len(cited), 8)
        self.assertTrue(all(r["predicate"] == "signatory_of" and r["classification"] == "VERIFIED FACT" for r in cited))
        key = lambda r: (r["subject"], r["predicate"], r["object"])
        listed = {key(r) for r in registry.announcement_only(self.ontology, self.evidence)}
        self.assertFalse(listed & {key(r) for r in cited})
        n, m = len(listed), len(registry.formal_act_relationships(self.ontology))
        self.assertIn(f"{n} of the {m} relationships that assert a formal act", visible("registry/gaps/index.html"))

    def test_nexus_signatures_rest_on_the_ministry_release_without_construction(self):
        for s in ("nexus-core-systems", "ministry-digital-transition"):
            r = next(r for r in self.ontology["relationships"]
                     if (r["subject"], r["predicate"], r["object"]) == (s, "signatory_of", "nexus-ai-factory"))
            self.assertEqual(r["classification"], "VERIFIED FACT")
            self.assertIn("MAI-EV-0044", r["evidence"])
            self.assertIn("does not reproduce the memorandum", r["note"])
            self.assertIn("has not obtained its text", r["note"])
        nexus = next(e for e in self.ontology["entities"] if e["id"] == "nexus-ai-factory")
        self.assertEqual(nexus["lifecycle"], "announced")
        for t in (nexus["summary"], nexus.get("status", ""), self.records["MAI-EV-0045"]["verification_note"]):
            self.assertNotRegex(t, r"(?i)\b(under construction|construction (has )?(started|began|begun)|is operational)\b")

    def test_no_registry_text_attributes_gemmaroc_to_belkasmi(self):
        texts = [self.records["MAI-EV-0041"]["claim"]]
        texts += [a.get("value", "") + " " + a.get("name", "") for e in self.ontology["entities"] for a in e.get("attributes", [])]
        texts += [e.get(k, "") for e in self.ontology["entities"] for k in ("summary", "status", "note")]
        for t in texts:
            if "Belkasmi" in t:
                self.assertIn("attributes to", t)
        self.assertIn("Skiredj", self.records["MAI-EV-0041"]["claim"])

    def test_preprint_does_not_place_the_runs_on_toubkal(self):
        note = self.records["MAI-EV-0042"]["verification_note"]
        self.assertIn("not peer-reviewed", note)
        self.assertRegex(note, r"neither confirms nor rules out")
        self.assertEqual(self.records["MAI-EV-0042"]["classification"], "VERIFIED FACT")
        self.assertNotIn("status_evidence", self.records["MAI-EV-0042"])

    def test_un_entry_is_a_starting_position_not_progress(self):
        r = self.records["MAI-EV-0046"]
        self.assertIn("position at the start of the strategy, not progress", r["verification_note"])
        g = next(g for g in self.gaps["gaps"] if g["id"] == "GAP-06")
        self.assertIn("MAI-EV-0046", g["assessed_records"])
        # Progress wording may appear only where a sentence negates it ("not progress under the strategy").
        for gid in ("GAP-02", "GAP-06"):
            for item in next(x for x in self.gaps["gaps"] if x["id"] == gid)["established"]:
                for sentence in re.split(r"(?<=\.)\s+", item["text"]):
                    if re.search(r"(?i)\b(progress|improved|achieved|on track)\b", sentence):
                        self.assertRegex(sentence, r"(?i)\b(not|no|without|neither|nor)\b", f"{gid}: {sentence}")

    def test_arabic_excerpts_are_marked_right_to_left(self):
        page = (REPO / "registry" / "evidence" / "index.html").read_text(encoding="utf-8")
        quotes = re.findall(r'<blockquote class="evidence-quote"[^>]*>', page)
        arabic = [q for q in quotes if 'lang="ar"' in q]
        self.assertEqual(len(arabic), sum(1 for r in self.evidence["records"] if r["source_language"] == "ar"))
        self.assertTrue(all('dir="rtl"' in q for q in arabic))
        self.assertFalse(any('dir="rtl"' in q for q in quotes if 'lang="ar"' not in q))

    def test_no_gap_closed_by_this_sprint(self):
        self.assertEqual({g["state"] for g in self.gaps["gaps"]}, {"open"})
        self.assertFalse(any(r["evidence_type"] == "signed_instrument" for r in self.evidence["records"]))


NUMBER = re.compile(r"\d[\d,\u202f\u00a0]*(?:\.\d+)?")


def numbers(text):
    return {re.sub(r"[,\u202f\u00a0]", "", m.group(0)) for m in NUMBER.finditer(text)}


def unsupported_numbers(text, records):
    """Numerals in a statement that appear in none of its cited records' claim, excerpts or dates.
    This checks provenance only: a numeral that does appear may still be misattributed or misread,
    and numbers written in words are not checked. It cannot establish that a statement is correct."""
    have = set()
    for r in records:
        have |= numbers(" ".join([r["claim"], *r["source_excerpts"]]))
        for d in (r.get("publication_date"), r.get("retrieval_date")):
            if d:
                have |= {x.lstrip("0") or "0" for x in d.split("-")} | set(d.split("-"))
    return sorted(numbers(text) - have)


class FinalEvidenceCorrections(unittest.TestCase):
    """Sprint 07 review corrections D1-D6."""

    @classmethod
    def setUpClass(cls):
        cls.evidence, cls.ontology = registry.load_all()
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.gaps = {g["id"]: g for g in json.loads((REPO / "data" / "gaps.json").read_text(encoding="utf-8"))["gaps"]}
        cls.rows = build.matrix_rows(build.Model(cls.evidence, cls.ontology))

    def test_every_numeral_in_a_gap_statement_is_in_its_cited_records(self):
        for g in self.gaps.values():
            for st in g["established"]:
                self.assertEqual(unsupported_numbers(st["text"], [self.records[x] for x in st["evidence"]]), [],
                                 f"{g['id']}: {st['text']}")

    def test_every_numeral_in_an_attribute_is_in_its_cited_record(self):
        # Identifiers are not measurements: "ISO 639-3" names a standard.
        for e in self.ontology["entities"]:
            for a in e.get("attributes", []):
                value = a["value"].replace("ISO 639-3", "")
                self.assertEqual(unsupported_numbers(value, [self.records[a["evidence"]]]), [], f"{e['id']}: {a['name']}")

    def test_the_provenance_check_catches_a_misattributed_total(self):
        st = next(s for s in self.gaps["GAP-03"]["established"] if s["evidence"] == ["MAI-EV-0042"])
        self.assertEqual(unsupported_numbers(st["text"].replace("about 48", "about 58"), [self.records["MAI-EV-0042"]]), ["58"])
        self.assertEqual(unsupported_numbers("moving from 113th", [self.records["MAI-EV-0046"]]), ["113"])

    def test_gap_03_gives_the_preprints_figure_for_its_longest_run(self):
        st = next(s for s in self.gaps["GAP-03"]["established"] if s["evidence"] == ["MAI-EV-0042"])
        self.assertIn("about 48 GPU-hours for that longest run", st["text"])
        self.assertNotIn("58", json.dumps(self.gaps["GAP-03"]))
        self.assertTrue(any("approximately 48 GPU-hours" in x for x in self.records["MAI-EV-0042"]["source_excerpts"]))

    def test_the_strategy_figure_cites_the_strategy(self):
        st = next(s for s in self.gaps["GAP-06"]["established"] if "MAI-EV-0046" in s["evidence"])
        self.assertIn("MAI-EV-0002", st["evidence"])
        self.assertIn("113th", self.records["MAI-EV-0002"]["claim"])
        self.assertNotIn("113", " ".join([self.records["MAI-EV-0046"]["claim"], *self.records["MAI-EV-0046"]["source_excerpts"]]))

    def test_no_registry_text_asserts_that_a_text_is_not_published(self):
        texts = [r["verification_note"] for r in self.evidence["records"]]
        texts += [e.get(k, "") for e in self.ontology["entities"] for k in ("summary", "status", "note")]
        texts += [r.get("note", "") for r in self.ontology["relationships"]]
        texts += [json.dumps(g) for g in self.gaps.values()]
        for t in texts:
            self.assertNotRegex(t, r"(?i)\b(?:is|are) not published\b", t)

    def test_the_mobilised_figure_is_quoted_and_not_read_as_spending(self):
        r = self.records["MAI-EV-0044"]
        self.assertTrue(any("12 milliards de dirhams mobilisé sur deux phases" in x for x in r["source_excerpts"]))
        self.assertIn('"mobilisé sur deux phases"', r["verification_note"])
        self.assertIn("does not establish that any amount has been spent", r["verification_note"])
        self.assertNotRegex(r["verification_note"], r"(?i)all of the .* future tense|figures are stated in the future tense and are")

    def test_gazette_rows_are_distinguished_from_signing_reports(self):
        listed = {(r["subject"], r["predicate"], r["object"]) for r in registry.announcement_only(self.ontology, self.evidence)}
        unlisted = [r for r in self.ontology["relationships"] if r["predicate"] == "signatory_of"
                    and (r["subject"], r["predicate"], r["object"]) not in listed]
        gazette = [r for r in unlisted if any(self.records[x]["evidence_type"] == "official_gazette" for x in r["evidence"])]
        others = [r for r in unlisted if r not in gazette]
        self.assertEqual(len(gazette), 8)
        self.assertTrue(all(any(self.records[x]["evidence_type"] == "official_report" for x in r["evidence"]) for r in others))
        gap05 = self.gaps["GAP-05"]["unestablished"]
        self.assertIn("For eight signatures of the JAZARI ROOT and JAZARI Industrie X.0 conventions", gap05)
        self.assertIn("the other signatures not listed rest on an official report of the signing", gap05)
        for row in self.rows:
            cites = any(e["evidence_type"] == "official_gazette" for e in row["evidence"])
            self.assertEqual(build.SIGNED_GAZETTE_APPROVAL in row["qualifications"], cites and row["documented_as"] == "Signed", row["id"])
        q8 = visible("registry/questions/index.html")
        self.assertIn(f"for {len(gazette)}, an official gazette record (MAI-EV-0047) also documents the legal approval of the instrument", q8)
        matrix = visible("registry/matrix/index.html")
        line = matrix[matrix.index('For none of the'):][:600]
        self.assertNotIn("official gazette, ", line.split(")")[0])
        self.assertIn(f"{len(gazette)} rows also cite an official gazette record", line)
        definition = json.loads((REPO / "registry" / "matrix" / "matrix.json").read_text(encoding="utf-8"))
        value = definition["derivation"]["documentation_basis"]["values"]["includes-non-announcement-record"]
        self.assertIn("a regulatory record, an official gazette text, a technical repository", value)
        self.assertIn("an official gazette text records a legal act about it, such as its approval", value)
        self.assertIn(build.SIGNED_GAZETTE_APPROVAL, [q["text"] for q in definition["derivation"]["qualifications"]["rules"]])

    def test_gazette_note_names_the_groups_and_the_earlier_block_is_resolved(self):
        note = self.records["MAI-EV-0047"]["verification_note"]
        self.assertIn("for JAZARI EduTech and JAZARI Smart City, further ministries and public bodies", note)
        self.assertNotIn("the other two groups", note)
        self.assertIn("later retrieved and is recorded as MAI-EV-0044", self.records["MAI-EV-0030"]["verification_note"])


if __name__ == "__main__":
    unittest.main()
