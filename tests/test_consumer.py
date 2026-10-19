"""The external-consumer example, the data reference and the reproducibility of published answers.

The consumer in examples/ must work from the published JSON alone. These tests run it against the committed
site, against copies of the published files with one defect each, and compare what it recomputes with what the
generator published and with the questions page.
"""
import ast
import contextlib
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import build  # noqa: E402
import registry  # noqa: E402

# Identifiers withdrawn by a correction: identifier -> the version whose changelog entry records it. None so far.
WITHDRAWN = {}
BASELINE_V040 = "a0dedadc1188d15807cabd30dd7490b67dbb0052"  # registry v0.4.0 on main


def git_show(commit, path):
    p = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=REPO, capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def need_history(test):
    """Skip without repository history locally; in CI (which fetches full history) its absence is a failure."""
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=REPO, capture_output=True, text=True)
    if shallow.returncode or shallow.stdout.strip() != "false" or git_show(BASELINE_V040, "data/evidence.json") is None:
        if os.environ.get("CI"):
            test.fail("repository history is required in CI (actions/checkout fetch-depth: 0)")
        test.skipTest("repository history not available")


def published_states():
    log = subprocess.run(["git", "log", "--first-parent", "--reverse", "--format=%H", "HEAD", "--",
                          "data/evidence.json", "data/ontology.json"], cwd=REPO, capture_output=True, text=True, check=True)
    return [(c, json.loads(git_show(c, "data/evidence.json")), json.loads(git_show(c, "data/ontology.json")))
            for c in log.stdout.split()]


CONSUMER_PATH = REPO / "examples" / "registry_consumer.py"
_spec = importlib.util.spec_from_file_location("registry_consumer", CONSUMER_PATH)
consumer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(consumer)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = consumer.main(argv)
    return code, out.getvalue(), err.getvalue()


class PublishedCopy:
    """A copy of the files the manifest lists, which a test can alter and then re-sign or leave stale."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp())
        self.manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
        for res in self.manifest["resources"] + [{"path": consumer.MANIFEST}]:
            dest = self.root / res["path"].lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / res["path"].lstrip("/"), dest)

    def load(self, path):
        return json.loads((self.root / path.lstrip("/")).read_text(encoding="utf-8"))

    def save(self, path, data, *, resign=True):
        raw = (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        (self.root / path.lstrip("/")).write_bytes(raw)
        if resign:
            for res in self.manifest["resources"]:
                if res["path"] == path:
                    res["sha256"] = hashlib.sha256(raw).hexdigest()
            (self.root / "data" / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def edit(self, path, change, *, resign=True):
        data = self.load(path)
        change(data)
        self.save(path, data, resign=resign)

    def verify(self):
        return run(["--source", str(self.root), "verify"])

    def cleanup(self):
        shutil.rmtree(self.root)


class IndependentConsumer(unittest.TestCase):
    def test_uses_only_the_standard_library(self):
        tree = ast.parse(CONSUMER_PATH.read_text(encoding="utf-8"))
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertLessEqual(imported, set(sys.stdlib_module_names), imported - set(sys.stdlib_module_names))
        self.assertNotIn("registry", imported)
        self.assertNotIn("build", imported)
        self.assertNotIn("tools", CONSUMER_PATH.read_text(encoding="utf-8"))

    def test_reads_only_files_the_manifest_publishes(self):
        copy = PublishedCopy()
        try:
            # The copy holds the manifest and its resources only: no tools/, no unpublished data.
            files = sorted(str(p.relative_to(copy.root)) for p in copy.root.rglob("*") if p.is_file())
            self.assertEqual(len(files), len(copy.manifest["resources"]) + 1)
            code, out, err = copy.verify()
            self.assertEqual(code, 0, err)
            self.assertIn("OK: registry", out)
        finally:
            copy.cleanup()

    def test_published_site_verifies(self):
        code, out, err = run(["--source", str(REPO), "verify"])
        self.assertEqual(code, 0, err)

    def test_runs_as_a_standalone_script(self):
        # Isolated mode: no site directory on the import path, no user site-packages.
        p = subprocess.run([sys.executable, "-I", str(CONSUMER_PATH), "--source", str(REPO), "verify"],
                           capture_output=True, text=True, cwd=tempfile.gettempdir(), timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_output_is_deterministic(self):
        commands = [["verify"], ["q8"], ["q9"], ["q8", "--json"], ["gap", "GAP-05"], ["gap", "GAP-01"],
                    ["relationship", "ministry-digital-transition", "operates", "idarati-ai"]]
        for cmd in commands:
            outs = set()
            for seed in ("0", "1", "4242"):
                argv = [sys.executable, "-I", str(CONSUMER_PATH), "--source", str(REPO)]
                if cmd[-1] == "--json":
                    argv += ["--json", cmd[0]]
                else:
                    argv += cmd
                p = subprocess.run(argv, capture_output=True, text=True, timeout=120,
                                   env={**os.environ, "PYTHONHASHSEED": seed})
                self.assertEqual(p.returncode, 0, p.stderr)
                outs.add(p.stdout)
            self.assertEqual(len(outs), 1, cmd)

    def test_unknown_relationship_or_gap_is_reported_not_guessed(self):
        code, _, err = run(["--source", str(REPO), "relationship", "cndp", "operates", "law-09-08"])
        self.assertEqual(code, 2)
        self.assertIn("no relationship cndp|operates|law-09-08", err)
        code, _, err = run(["--source", str(REPO), "gap", "GAP-99"])
        self.assertEqual(code, 2)

    def test_missing_source_fails_clearly(self):
        code, _, err = run(["--source", str(REPO / "no-such-site"), "verify"])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)


class RelationshipAndGapInspection(unittest.TestCase):
    def test_relationship_traces_to_its_evidence(self):
        code, out, err = run(["--source", str(REPO), "relationship", "ministry-digital-transition", "operates", "idarati-ai"])
        self.assertEqual(code, 0, err)
        documented, limits = out.split("\nLIMITATIONS\n")
        ev = json.loads((REPO / "data" / "evidence.json").read_text(encoding="utf-8"))
        rel = next(r for r in json.loads((REPO / "data" / "ontology.json").read_text(encoding="utf-8"))["relationships"]
                   if (r["subject"], r["predicate"], r["object"]) == ("ministry-digital-transition", "operates", "idarati-ai"))
        for x in rel["evidence"]:
            rec = next(r for r in ev["records"] if r["evidence_id"] == x)
            self.assertIn(f"URL: {rec['source_url']}", documented)
            self.assertIn(f"retrieved {rec['retrieval_date']}", documented)
            self.assertIn(rec["verification_note"], limits)
        self.assertIn("undated (publication_date is null)", documented)
        self.assertIn("operational (public-availability-observed)", documented)
        self.assertIn("not evidence of use", limits)
        # Limitations are never printed as documented facts.
        self.assertNotIn("how many people use it", documented)

    def test_gap_inspection_separates_assessment_from_data_checks(self):
        code, out, err = run(["--source", str(REPO), "gap", "GAP-03"])
        self.assertEqual(code, 0, err)
        self.assertIn("This is not a finding that Toubkal is not used for AI", out)
        self.assertIn("unchanged since assessment", out)
        self.assertIn("Check: no AI application linked to toubkal-supercomputer: holds", out)
        code, out, _ = run(["--source", str(REPO), "gap", "GAP-02"])
        self.assertIn("No data check is defined: the state rests on the editor's assessment alone.", out)
        code, out, _ = run(["--source", str(REPO), "gap", "GAP-05"])
        model = build.Model(*registry.load_all())
        n = len(registry.announcement_only(model.ontology, model.evidence))
        self.assertIn(f"Recomputed: {n} of {len(registry.formal_act_relationships(model.ontology))} formal-act relationships", out)


class DefectsAreDetected(unittest.TestCase):
    """Each copy carries one defect; the consumer must report it and exit 1."""

    def setUp(self):
        self.copy = PublishedCopy()

    def tearDown(self):
        self.copy.cleanup()

    def assertRejected(self, fragment):
        code, out, err = self.copy.verify()
        self.assertEqual(code, 1, out + err)
        self.assertIn("INCONSISTENT DATA", err)
        self.assertIn(fragment, err)

    def test_broken_evidence_reference(self):
        self.copy.edit("/data/ontology.json", lambda d: d["relationships"][0].update(evidence=["MAI-EV-9999"]))
        self.assertRejected("cites MAI-EV-9999, which is not in evidence.json")

    def test_missing_entity(self):
        def drop(d):
            d["entities"] = [e for e in d["entities"] if e["id"] != "law-09-08"]
        self.copy.edit("/data/ontology.json", drop)
        self.assertRejected("names law-09-08, which is not in ontology.json")

    def test_relationship_naming_a_missing_entity(self):
        self.copy.edit("/data/ontology.json", lambda d: d["relationships"][0].update(object="no-such-project"))
        self.assertRejected("subject or object names no-such-project, which is not in ontology.json")

    def test_new_record_postdating_a_gap_assessment(self):
        def add(d):
            r = json.loads(json.dumps(next(r for r in d["records"] if r["evidence_id"] == "MAI-EV-0020")))
            r["evidence_id"] = "MAI-EV-0099"
            d["records"].append(r)
        self.copy.edit("/data/evidence.json", add)
        self.assertRejected("GAP-03: MAI-EV-0099 concern this gap but postdate its assessment")

    def test_record_naming_a_missing_entity(self):
        self.copy.edit("/data/evidence.json", lambda d: d["records"][0]["related_entities"].append("no-such-entity"))
        self.assertRejected("names no-such-entity")

    def test_relationship_with_wrong_types(self):
        def flip(d):
            r = next(r for r in d["relationships"] if r["predicate"] == "operates")
            r["subject"], r["object"] = r["object"], r["subject"]
        self.copy.edit("/data/ontology.json", flip)
        self.assertRejected("is not allowed for operates")

    def test_matrix_row_resolving_to_the_wrong_entity(self):
        def wrong(d):
            d["rows"][0]["object"]["id"] = "law-09-08" if d["rows"][0]["object"]["id"] != "law-09-08" else "idarati-ai"
        self.copy.edit("/registry/matrix/matrix.json", wrong)
        self.assertRejected("has object")

    def test_matrix_row_upgraded(self):
        def upgrade(d):
            row = next(r for r in d["rows"] if r["documented_as"] == "Announced or planned")
            row["documented_as"] = "Signed"
        self.copy.edit("/registry/matrix/matrix.json", upgrade)
        self.assertRejected("has documented_as 'Signed'")

    def test_matrix_row_missing(self):
        self.copy.edit("/registry/matrix/matrix.json", lambda d: d["rows"].pop())
        self.assertRejected("matrix.json: missing row")

    def test_matrix_evidence_dates_differ(self):
        self.copy.edit("/registry/matrix/matrix.json", lambda d: d["rows"][0]["evidence"][0].update(retrieval_date="2020-01-01"))
        self.assertRejected("differently from evidence.json")

    def test_unknown_lifecycle_stage(self):
        self.copy.edit("/data/ontology.json", lambda d: next(e for e in d["entities"] if e.get("lifecycle")).update(lifecycle="paused"))
        self.assertRejected("lifecycle stage 'paused' is not defined")

    def test_unknown_evidence_type_or_basis(self):
        self.copy.edit("/data/evidence.json", lambda d: d["records"][0].update(evidence_type="rumour"))
        self.assertRejected("evidence type 'rumour' is not defined")

    def test_unknown_status_basis(self):
        self.copy.edit("/data/evidence.json", lambda d: next(r for r in d["records"] if r.get("status_basis")).update(status_basis="vibes"))
        self.assertRejected("status basis 'vibes' is not defined")

    def test_unknown_classification(self):
        self.copy.edit("/data/evidence.json", lambda d: d["records"][0].update(classification="PROBABLE FACT"))
        self.assertRejected("classification 'PROBABLE FACT' is not defined")

    def test_unknown_gap_state(self):
        self.copy.edit("/data/gaps.json", lambda d: d["gaps"][0].update(state="closed"))
        self.assertRejected("state 'closed' is not defined")

    def test_unknown_gap_check(self):
        self.copy.edit("/data/gaps.json", lambda d: d["gaps"][0]["checks"].append({"type": "sentiment"}))
        self.assertRejected("check 'sentiment' is not defined")

    def test_file_from_another_build(self):
        self.copy.edit("/data/evidence.json", lambda d: d["records"][0].update(title="Edited"), resign=False)
        self.assertRejected("/data/evidence.json: SHA-256 differs from the manifest")

    def test_files_from_two_real_versions(self):
        # The v0.4.0 evidence.json from main, served next to the current manifest and ontology.
        need_history(self)
        (self.copy.root / "data" / "evidence.json").write_text(git_show(BASELINE_V040, "data/evidence.json"), encoding="utf-8")
        self.assertRejected("/data/evidence.json: SHA-256 differs from the manifest")
        self.assertRejected("evidence.json: version 0.4.0 as of 2026-10-19, but the manifest is version")

    def test_real_older_ontology_even_when_re_signed(self):
        need_history(self)
        self.copy.save("/data/ontology.json", json.loads(git_show(BASELINE_V040, "data/ontology.json")))
        self.assertRejected("ontology.json: version 0.3.0 as of 2026-10-18")

    def test_hashes_are_not_a_signature(self):
        # The limit, stated on /data/ and by the consumer: whoever can rewrite the files can re-sign the manifest.
        # A consistent edit with a re-signed manifest passes; only the cited sources establish accuracy.
        self.copy.edit("/data/evidence.json", lambda d: d["records"][0].update(title="Altered and re-signed"))
        code, out, err = self.copy.verify()
        self.assertEqual(code, 0, err)
        self.assertIn("the hashes are not a signature", out)
        self.assertIn("the sources were not re-fetched", out)

    def test_mismatched_versions(self):
        self.copy.edit("/data/ontology.json", lambda d: d.update(version="0.3.0"))
        self.assertRejected("ontology.json: version 0.3.0")

    def test_stale_derived_file(self):
        self.copy.edit("/registry/gaps/gaps.json", lambda d: d.update(registry_version="0.4.0"))
        self.assertRejected("registry/gaps/gaps.json: version 0.4.0")

    def test_gap_resting_on_changed_data(self):
        self.copy.edit("/data/evidence.json", lambda d: next(r for r in d["records"] if r["evidence_id"] == "MAI-EV-0041").update(claim="Edited."))
        self.assertRejected("GAP-03: the data it rests on has changed since it was assessed")

    def test_open_gap_contradicted_by_the_data(self):
        def operational(d):
            next(e for e in d["entities"] if e["id"] == "nexus-ai-factory").update(lifecycle="operational")
        self.copy.edit("/data/ontology.json", operational)
        self.assertRejected("GAP-04: open, but the data no longer satisfies")

    def test_open_gap_with_a_new_ai_application_link(self):
        def link(d):
            d["relationships"].append({"subject": "toubkal-supercomputer", "predicate": "related_to", "object": "idarati-ai",
                                       "evidence": ["MAI-EV-0020"], "classification": "VERIFIED FACT"})
        self.copy.edit("/data/ontology.json", link)
        self.assertRejected("GAP-03: open, but the data no longer satisfies: no AI application linked to toubkal-supercomputer")

    def test_open_gap_with_a_report_of_use(self):
        self.copy.edit("/data/evidence.json", lambda d: next(r for r in d["records"] if r["evidence_id"] == "MAI-EV-0038").update(status_basis="operator-report-of-use"))
        self.assertRejected("GAP-01: open, but the data no longer satisfies: no status record for idarati-ai")

    def test_computed_gap_with_nothing_left_to_list(self):
        def formal(d):
            for r in d["records"]:
                if r["evidence_type"] in ("news_dispatch", "press_release", "official_announcement", "official_statement",
                                          "organization_page", "case_study", "press_article"):
                    r["evidence_type"] = "official_report"
        self.copy.edit("/data/evidence.json", formal)
        self.assertRejected("GAP-05: open, but the data no longer satisfies: at least one relationship documented only by announcements")

    def test_old_derived_file_without_rules_fails_cleanly(self):
        self.copy.edit("/registry/matrix/matrix.json", lambda d: d.pop("derivation"))
        self.assertRejected("unexpected structure: KeyError 'derivation'")

    def test_classification_stronger_than_its_records(self):
        def upgrade(d):
            r = next(r for r in d["relationships"] if r["classification"] == "ANNOUNCED PLAN" and r["predicate"] == "operates")
            r["classification"] = "UNVERIFIED CLAIM"
        self.copy.edit("/data/ontology.json", upgrade)
        self.assertRejected("classified UNVERIFIED CLAIM but cites no UNVERIFIED CLAIM record")

    def test_stage_without_a_declaring_record(self):
        self.copy.edit("/data/ontology.json", lambda d: next(e for e in d["entities"] if e["id"] == "nexus-ai-factory").update(lifecycle="pilot"))
        self.assertRejected("nexus-ai-factory: stage pilot is not declared by any of its lifecycle_evidence records")

    def test_stage_label_out_of_date(self):
        def relabel(d):
            next(r for r in d["rows"] if r["object"]["id"] == "idarati-ai")["object"]["stage"] = "Operational"
        self.copy.edit("/registry/matrix/matrix.json", relabel)
        self.assertRejected("has object_stage 'Operational'")

    def test_wrong_formal_act_count(self):
        self.copy.edit("/registry/gaps/gaps.json", lambda d: next(g for g in d["gaps"] if g["id"] == "GAP-05").update(formal_act_relationships=43))
        self.assertRejected("GAP-05 states 43 formal-act relationships")

    def test_derived_gap_list_out_of_date(self):
        self.copy.edit("/registry/gaps/gaps.json", lambda d: next(g for g in d["gaps"] if g["id"] == "GAP-05")["relationships"].pop())
        self.assertRejected("GAP-05 lists")

    def test_derived_gap_text_differs(self):
        self.copy.edit("/registry/gaps/gaps.json", lambda d: d["gaps"][0].update(state="resolved"))
        self.assertRejected("GAP-01 state differs from data/gaps.json")


class ReproducedAnswers(unittest.TestCase):
    """Q8 and Q9 recomputed by the consumer match the questions page and the generator."""

    @classmethod
    def setUpClass(cls):
        cls.reg = consumer.Registry(str(REPO))
        cls.model = build.Model(*registry.load_all())
        page = (REPO / "registry" / "questions" / "index.html").read_text(encoding="utf-8")
        cls.q8_html = page[page.index('id="q8-h"'):page.index('id="q9-h"')]
        cls.q9_html = page[page.index('id="q9-h"'):page.index('id="q5-h"')]

    @staticmethod
    def rows(section):
        body = section[section.index("<tbody>"):section.index("</tbody>")]
        return [re.findall(r"<td>(.*?)</td>", tr, re.S) for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S)]

    def test_matrix_recomputed_independently_matches_the_generator(self):
        mine = self.reg.matrix_rows()
        theirs = build.matrix_rows(self.model)
        self.assertEqual([r["id"] for r in mine], [r["id"] for r in theirs])
        for a, b in zip(mine, theirs):
            self.assertEqual((a["documented_as"], a["documentation_basis"], a["classification"], a["evidence"]),
                             (b["documented_as"], b["documentation_basis"], b["classification"], [e["id"] for e in b["evidence"]]))

    def test_gap_digests_and_list_recomputed_independently(self):
        for g in self.reg.gaps["gaps"]:
            self.assertEqual(self.reg.fingerprint(g), registry.gap_fingerprint(g, self.model.evidence, self.model.ontology), g["id"])
        self.assertEqual([r["id"] for r in self.reg.announcement_only()],
                         ["|".join(k) for k in sorted((r["subject"], r["predicate"], r["object"])
                                                      for r in registry.announcement_only(self.model.ontology, self.model.evidence))])

    def test_q8_summary_matches_the_published_answer(self):
        a = self.reg.q8()
        text = html.unescape(re.sub(r"<[^>]+>", "", self.q8_html))
        tally = ", ".join(f"{k.lower()} {v}" for k, v in a["documented_as"].items())
        self.assertIn(f"{a['organisations']} organisations are documented as connected to {a['projects']} projects, through "
                      f"{a['relationships']} relationships: {tally}. {a['announcement_only']} of these rest only on announcements", text)

    def test_q8_rows_match_the_published_answer(self):
        a = self.reg.q8()
        published = self.rows(self.q8_html)
        self.assertEqual(len(published), a["organisations"])
        for row, org in zip(published, a["rows"]):
            self.assertIn(f'href="/registry/{org["organisation"]}/"', row[0])
            projects = re.findall(r'href="/registry/([a-z0-9-]+)/">[^<]*</a> \(([^;]+);', row[1])
            self.assertEqual(projects, [(p["project"], p["documented_as"].lower()) for p in org["projects"]])
            self.assertEqual(re.findall(r">(MAI-EV-\d{4})<", row[2]), org["evidence"])

    def test_q9_rows_match_the_published_answer(self):
        a = self.reg.q9()
        published = self.rows(self.q9_html)
        self.assertEqual(len(published), len(a["rows"]))
        for row, mine in zip(published, a["rows"]):
            self.assertIn(f'href="/registry/{mine["strategy"]}/"', row[0])
            self.assertIn(mine["target_record"], row[1])
            self.assertEqual(re.findall(r'href="/registry/([a-z0-9-]+)/"', row[2]), [p["project"] for p in mine["included"]])
            if mine["gap"]:
                self.assertIn(f'#{mine["gap"].lower()}"', row[3])
                self.assertIn(html.escape(mine["progress"]), row[3])
            else:
                self.assertIn("Not yet assessed in the gap register.", row[3])

    def test_q9_flags_its_editorial_boundary(self):
        rows = {r["strategy"]: r for r in self.reg.q9()["rows"]}
        self.assertIn("editorial assessment only", rows["morocco-ai-2030"]["progress_basis"])
        self.assertEqual(rows["digital-morocco-2030"]["progress_basis"], "not assessed")
        page = (REPO / "data" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Editorial assessment", page)
        self.assertIn("No data check backs this judgment", page)

    def test_targets_are_never_presented_as_outcomes(self):
        for r in self.reg.q9()["rows"]:
            self.assertNotRegex(r["progress"], r"(?i)achieved|reached|met\b")


class DataReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (REPO / "data" / "index.html").read_text(encoding="utf-8")
        cls.manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
        cls.evidence, cls.ontology = registry.load_all()

    def test_manifest_matches_the_published_files(self):
        self.assertEqual((self.manifest["registry_version"], self.manifest["as_of"]), (self.evidence["version"], self.evidence["as_of"]))
        for res in self.manifest["resources"]:
            raw = (REPO / res["path"].lstrip("/")).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), res["sha256"], res["path"])
            self.assertEqual(len(raw), res["bytes"])
            self.assertIn(f'href="{res["path"]}"', self.page)
        self.assertEqual({r["role"] for r in self.manifest["resources"]}, {"canonical", "derived"})

    def test_manifest_hashes_the_files_of_its_own_build(self):
        model = build.Model(self.evidence, self.ontology)
        files = {"registry/matrix/matrix.json": '{"changed": true}\n'}
        res = {r["path"]: r for r in build.manifest(model, files)["resources"]}
        self.assertEqual(res["/registry/matrix/matrix.json"]["sha256"], hashlib.sha256(b'{"changed": true}\n').hexdigest())

    def test_derived_files_name_their_sources_and_rules(self):
        matrix = json.loads((REPO / "registry" / "matrix" / "matrix.json").read_text(encoding="utf-8"))
        gaps = json.loads((REPO / "registry" / "gaps" / "gaps.json").read_text(encoding="utf-8"))
        self.assertEqual(matrix["derived_from"], ["/data/ontology.json", "/data/evidence.json"])
        self.assertEqual(matrix["derivation"]["documentation_basis"]["formal_act_relationships"], list(registry.FORMAL_ACT_PREDICATES))
        self.assertEqual(matrix["derivation"]["documentation_basis"]["announcement_evidence_types"], list(registry.ANNOUNCEMENT_TYPES))
        self.assertEqual(gaps["derivation"]["assessed_fingerprint"]["record_fields"], list(registry.GAP_RECORD_FIELDS))
        self.assertEqual(gaps["derivation"]["assessed_fingerprint"]["entity_fields"], list(registry.GAP_ENTITY_FIELDS))
        self.assertEqual(set(gaps["derivation"]["checks"]) - {"rule"},
                         {"no_status_basis", "lifecycle_in", "no_ai_application_link", "computed_relationships"})
        self.assertEqual(set(gaps["states"]), set(registry.GAP_STATES))

    def test_published_rules_cover_every_derived_field(self):
        # The clean-room review found these undocumented; each now has a published rule.
        d = json.loads((REPO / "registry" / "matrix" / "matrix.json").read_text(encoding="utf-8"))["derivation"]
        for key in ("row_order", "qualifications", "relationship_label", "object.status_as_recorded", "evidence"):
            self.assertIn(key, d)
        texts = [q["text"] for q in d["qualifications"]["rules"][1:]]
        for row in json.loads((REPO / "registry" / "matrix" / "matrix.json").read_text(encoding="utf-8"))["rows"]:
            for q in row["qualifications"]:
                self.assertTrue(q in texts or q == next(r.get("note") for r in self.ontology["relationships"]
                                                       if "|".join((r["subject"], r["predicate"], r["object"])) == row["id"]), q)
        v = self.manifest["vocabularies"]
        self.assertEqual(set(v["source_type"]), set(registry.SOURCE_TYPES))
        self.assertEqual(v["evidence_type"], list(registry.EVIDENCE_TYPES))
        self.assertEqual(set(v["status_basis"]), set(registry.STATUS_BASES))

    def test_generator_uses_the_published_rules(self):
        # documented_as is computed from the same tables matrix.json publishes.
        for cls in registry.CLASSIFICATIONS:
            for pred in self.ontology["predicates"]:
                level = build.documented_as({"classification": cls, "predicate": pred})
                expected = (build.DOCUMENTED_AS_VERIFIED.get(pred, build.DOCUMENTED_AS_VERIFIED_OTHERWISE)
                            if cls == "VERIFIED FACT" else build.DOCUMENTED_AS[cls])
                self.assertEqual(level, expected)

    def test_reference_covers_what_a_consumer_needs(self):
        text = html.unescape(re.sub(r"<[^>]+>", " ", self.page))
        for phrase in ("No content or data licence has been declared", "remain subject to their publishers' rights",
                       "publication_date: null", "YYYY-MM", "An absent optional field means", "is an error",
                       "the validator enforces", "SHA-256", "Since v0.1.0, no evidence or entity identifier has been removed or reused",
                       "Published identifiers are not reused", "they are not a signature", "may be published without a new version",
                       "not a complete map", "is not measured", "registry_consumer.py verify", "Corrections"):
            self.assertIn(phrase, text)
        self.assertIn(f'href="/{build.CONSUMER}"', self.page)
        self.assertTrue((REPO / build.CONSUMER).exists())

    def test_no_adoption_or_licence_is_claimed(self):
        text = re.sub(r"<[^>]+>", " ", self.page)
        self.assertNotRegex(text, r"(?i)\b(used by|adopted by|trusted by|recognised by|recognized by|endorsed by)\b")
        self.assertNotRegex(text, r"(?i)\b(CC[- ]BY|creative commons|open data licen[cs]e|ODbL|public domain|freely (re)?usable)\b")
        self.assertNotRegex(self.manifest["rights"], r"(?i)licensed under|you may")

    def test_published_identifiers_are_never_removed_or_reused(self):
        need_history(self)
        # /data/ states that no evidence or entity identifier has been removed or reused since v0.1.0. Every version of
        # the data on the first-parent line of HEAD (main's published states) is checked against the current files.
        states = published_states()
        current_ev = {r["evidence_id"]: r["source_url"] for r in self.evidence["records"]}
        current_ent = {e["id"]: e["type"] for e in self.ontology["entities"]}
        log = json.dumps(registry.load(REPO / "data" / "changelog.json"))
        self.assertGreaterEqual(len(states), 4)
        for commit, ev, ont in states:
            for rid, url in ((r["evidence_id"], r["source_url"]) for r in ev["records"]):
                if rid in WITHDRAWN:
                    self.assertIn(rid, log, f"{rid} is withdrawn but the changelog does not say so")
                    continue
                self.assertIn(rid, current_ev, f"{rid}, published at {commit[:7]}, has been removed")
                self.assertEqual(current_ev[rid], url, f"{rid} now names another source than at {commit[:7]}")
            for eid, etype in ((e["id"], e["type"]) for e in ont["entities"]):
                if eid in WITHDRAWN:
                    self.assertIn(eid, log, f"{eid} is withdrawn but the changelog does not say so")
                    continue
                self.assertIn(eid, current_ent, f"entity {eid}, published at {commit[:7]}, has been removed")
                self.assertEqual(current_ent[eid], etype, f"entity {eid} now has another type than at {commit[:7]}")
        for x in WITHDRAWN:
            self.assertNotIn(x, current_ev)
            self.assertNotIn(x, current_ent)

    def test_ci_fetches_the_history_the_identifier_check_needs(self):
        workflow = (REPO / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"uses: actions/checkout@v4\n\s+with:\n\s+fetch-depth: 0")

    def test_ontology_and_evidence_versions_must_agree(self):
        ont = json.loads(json.dumps(self.ontology))
        ont["version"] = "0.3.0"
        self.assertTrue(any("version '0.3.0' differs" in e for e in registry.validate_ontology(ont, self.evidence)))
        ont = json.loads(json.dumps(self.ontology))
        ont["as_of"] = "2026-10-18"
        self.assertTrue(any("as_of '2026-10-18' differs" in e for e in registry.validate_ontology(ont, self.evidence)))

    def test_gap_states_must_be_defined(self):
        gaps = registry.load(REPO / "data" / "gaps.json")
        gaps["states"].pop("resolved")
        self.assertTrue(any("states must define" in e for e in registry.validate_gaps(gaps, self.evidence, self.ontology)))


if __name__ == "__main__":
    unittest.main()
