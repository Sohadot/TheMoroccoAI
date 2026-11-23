"""Evidence change intelligence (tools/changes.py, /registry/changes/, entity record history).

Synthetic snapshots test each classification rule, including the ones that guard against false real-world
inferences; the repository's own history tests the published output. Synthetic data lives in memory or in
temporary git repositories; canonical data is never modified.
Run: python3 -m unittest discover -s tests
"""
import copy
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import changes  # noqa: E402
import check_site  # noqa: E402
import registry  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "registry" / "changes" / "index.html"
JSON_PATH = REPO / "registry" / "changes" / "changes.json"


def need_history(test):
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=REPO, capture_output=True, text=True)
    if shallow.returncode or shallow.stdout.strip() != "false":
        if os.environ.get("CI"):
            test.fail("repository history is required in CI (actions/checkout fetch-depth: 0)")
        test.skipTest("repository history not available")


def snap(evidence=None, ontology=None, gaps="default", version="1.0.0", as_of="2026-01-01"):
    ev = {"version": version, "as_of": as_of, "records": evidence or []}
    on = {"entities": (ontology or {}).get("entities", []), "relationships": (ontology or {}).get("relationships", [])}
    gp = {"gaps": []} if gaps == "default" else gaps
    files = {"evidence.json": ev, "ontology.json": on, "gaps.json": gp}
    return changes._snapshot(files)


def record(rid="MAI-EV-0001", **over):
    r = {"evidence_id": rid, "title": "A title", "claim": "A claim.", "classification": "VERIFIED FACT",
         "verification_status": "verified", "source_url": "https://example.org/a", "source_excerpts": ["quote"],
         "publication_date": "2025-05-01", "retrieval_date": "2026-01-01", "verification_note": "Checked.",
         "related_entities": ["e1"]}
    r.update(over)
    return r


def entity(eid="e1", **over):
    e = {"id": eid, "name": "Entity", "type": "project", "summary": "Summary.", "evidence": ["MAI-EV-0001"]}
    e.update(over)
    return e


def classes(t):
    return sorted(c["class"] for c in t["changes"])


class Classification(unittest.TestCase):
    def test_identical_snapshots_have_no_change(self):
        a = snap([record()], {"entities": [entity()]})
        self.assertEqual(changes.transition(a, copy.deepcopy(a))["changes"], [])

    def test_reordering_is_not_a_change(self):
        a = snap([record(), record("MAI-EV-0002")],
                 {"entities": [entity(evidence=["MAI-EV-0001", "MAI-EV-0002"],
                                      attributes=[{"name": "x", "value": "1", "evidence": "MAI-EV-0001"},
                                                  {"name": "y", "value": "2", "evidence": "MAI-EV-0002"}])]})
        b = copy.deepcopy(a)
        b["files"]["evidence.json"]["records"].reverse()
        b["files"]["ontology.json"]["entities"][0]["evidence"].reverse()
        b["files"]["ontology.json"]["entities"][0]["attributes"].reverse()
        self.assertEqual(changes.transition(a, b)["changes"], [])

    def test_admission_is_dated_by_the_source_and_retrieval_never_by_an_event(self):
        t = changes.transition(snap([]), snap([record(publication_date=None)], version="1.1.0"))
        [c] = t["changes"]
        self.assertEqual(c["class"], "evidence.added")
        self.assertEqual(c["dates"], {"source_published": None, "retrieved": "2026-01-01"})
        self.assertNotIn("event", json.dumps(t))

    def test_a_property_first_recorded_is_not_a_change(self):
        a = snap([record()], {"entities": [entity()]})
        b = snap([record(status_basis="independent-listing")],
                 {"entities": [entity(lifecycle="announced", lifecycle_evidence=["MAI-EV-0001"], project_kind="agreement")]})
        self.assertEqual(classes(changes.transition(a, b)),
                         ["entity.field_recorded", "entity.lifecycle_recorded", "evidence.field_recorded",
                          "schema.field_added", "schema.field_added", "schema.field_added", "schema.field_added"])

    def test_a_real_stage_change_is_reported_with_its_evidence(self):
        a = snap([record()], {"entities": [entity(lifecycle="announced", lifecycle_evidence=["MAI-EV-0001"])]})
        b = snap([record(), record("MAI-EV-0002")],
                 {"entities": [entity(lifecycle="operational", lifecycle_evidence=["MAI-EV-0002"])]})
        lc = [c for c in changes.transition(a, b)["changes"] if c["class"] == "entity.lifecycle_changed"]
        self.assertEqual(len(lc), 1)
        self.assertEqual(lc[0]["fields"][0], {"field": "lifecycle", "before": "announced", "after": "operational"})
        self.assertEqual(lc[0]["evidence"], ["MAI-EV-0002"])

    def test_editorial_and_undetermined_wording(self):
        a = snap([record(claim="The ministry launched the portal.")])
        editorial = snap([record(claim="The ministry  launched the portal")])
        revised = snap([record(claim="The ministry announced the portal.")])
        self.assertEqual(classes(changes.transition(a, editorial)), ["evidence.text_editorial"])
        self.assertEqual(classes(changes.transition(a, revised)), ["evidence.text_revised"])
        self.assertEqual(changes.CLASSES["evidence.text_revised"][0], "undetermined")

    def test_research_changes_to_evidence(self):
        a = snap([record()])
        b = snap([record(classification="ANNOUNCED PLAN", verification_status="partial", superseded_by=["MAI-EV-0009"],
                         source_url="https://example.org/b", retrieval_date="2026-02-01")])
        self.assertEqual(classes(changes.transition(a, b)),
                         ["evidence.rechecked", "evidence.reclassified", "evidence.source_changed", "evidence.superseded",
                          "evidence.verification_changed", "schema.field_added"])
        self.assertEqual(changes.CLASSES["evidence.rechecked"][0], "structural")

    def test_relationships_by_identity(self):
        rel = {"subject": "a", "predicate": "operates", "object": "b", "evidence": ["MAI-EV-0001"], "classification": "ANNOUNCED PLAN"}
        a = snap([record()], {"relationships": [rel]})
        b = snap([record()], {"relationships": [dict(rel, classification="VERIFIED FACT"),
                                                {"subject": "c", "predicate": "hosts", "object": "b", "evidence": [], "classification": "VERIFIED FACT"}]})
        self.assertEqual(classes(changes.transition(a, b)), ["relationship.added", "relationship.reclassified"])
        self.assertEqual(classes(changes.transition(b, a)), ["relationship.reclassified", "relationship.removed"])

    def test_a_new_gap_register_begins_and_never_removes(self):
        gaps = {"gaps": [{"id": "GAP-01", "question": "Q?", "state": "open", "assessed_records": ["MAI-EV-0001"]}]}
        t = changes.transition(snap([record()], gaps=None), snap([record()], gaps=gaps))
        self.assertEqual(classes(t), ["gap.opened", "gap.register_started"])
        closed = {"gaps": [dict(gaps["gaps"][0], state="resolved", assessed_records=["MAI-EV-0001", "MAI-EV-0002"])]}
        self.assertEqual(classes(changes.transition(snap(gaps=gaps), snap(gaps=closed))), ["gap.reassessed", "gap.state_changed"])

    def test_change_ids_are_unique_and_classes_known(self):
        log = changes.change_log([snap([]), snap([record()], {"entities": [entity()]}, version="1.1.0")])
        for t in log["transitions"]:
            for c in t["changes"]:
                self.assertIn(c["class"], changes.CLASSES)
                self.assertIn(c["materiality"], log["materiality"])
                self.assertTrue(c["id"].startswith(t["to"]["version"] + ":"))


class Snapshots(unittest.TestCase):
    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=SYNTHETIC", "-c", "user.email=s@example.invalid", "-c", "commit.gpgsign=false", *args],
                       cwd=self.root, check=True, capture_output=True)

    def write(self, version, records):
        (self.root / "data").mkdir(exist_ok=True)
        (self.root / "data" / "evidence.json").write_text(json.dumps({"version": version, "as_of": "2026-01-01", "records": records}))
        (self.root / "data" / "ontology.json").write_text(json.dumps({"entities": [], "relationships": []}))

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.git("init", "-q")

    def test_one_snapshot_per_version_identified_by_content_not_commit(self):
        self.write("1.0.0", [])
        self.git("add", "."); self.git("commit", "-q", "-m", "v1.0.0")
        self.write("1.1.0", [record()])
        self.git("add", "."); self.git("commit", "-q", "-m", "work in progress")
        self.write("1.1.0", [record(), record("MAI-EV-0002")])
        self.git("add", "."); self.git("commit", "-q", "-m", "v1.1.0 final")
        snaps = changes.snapshots(self.root)
        self.assertEqual([s["version"] for s in snaps], ["1.0.0", "1.1.0"])
        self.assertEqual(len(snaps[1]["files"]["evidence.json"]["records"]), 2)  # the version's last state
        log = changes.change_log(snaps)
        self.assertNotRegex(json.dumps(log), r"\b[0-9a-f]{40}\b")  # no commit hashes in the output

    def test_the_working_tree_is_the_newest_snapshot(self):
        self.write("1.0.0", [])
        self.git("add", "."); self.git("commit", "-q", "-m", "v1.0.0")
        self.write("1.1.0", [record()])  # not committed
        snaps = changes.snapshots(self.root)
        self.assertEqual([s["version"] for s in snaps], ["1.0.0", "1.1.0"])

    def test_without_history_it_fails_loudly(self):
        bare = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, bare)
        with self.assertRaises(RuntimeError):
            changes.snapshots(bare)


class PublishedHistory(unittest.TestCase):
    def setUp(self):
        need_history(self)
        self.log = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        self.by_version = {t["to"]["version"]: t for t in self.log["transitions"]}

    def test_committed_change_log_is_reproducible(self):
        self.assertEqual(changes.change_log(changes.snapshots(REPO)), self.log)
        self.assertEqual(build.change_log(), self.log)

    def test_snapshots_cover_every_published_version(self):
        versions = [s["version"] for s in self.log["snapshots"]]
        changelog = [e["version"] for e in registry.load(REPO / "data" / "changelog.json")["entries"] if e.get("version")]
        self.assertEqual(sorted(versions), sorted(changelog))
        self.assertEqual(versions[-1], json.loads((REPO / "data" / "evidence.json").read_text())["version"])

    def test_known_history_is_classified_correctly(self):
        # v0.2.0 introduced the lifecycle field: stages were first recorded, none changed.
        v020 = self.by_version["0.2.0"]
        self.assertEqual(v020["counts"].get("entity.lifecycle_changed"), None)
        self.assertEqual(v020["counts"]["entity.lifecycle_recorded"], 9)
        # v0.3.0: Idarati AI moved from announced to operational on new evidence.
        [c] = [c for c in self.by_version["0.3.0"]["changes"]
               if c["class"] == "entity.lifecycle_changed" and c["subject"]["id"] == "idarati-ai"]
        self.assertEqual(c["fields"][0], {"field": "lifecycle", "before": "announced", "after": "operational"})
        self.assertEqual(c["evidence"], ["MAI-EV-0034", "MAI-EV-0035", "MAI-EV-0038"])
        # v0.3.0: MAI-EV-0029 was superseded by later records (a finding, not a property first recorded).
        [sup] = [c for c in self.by_version["0.3.0"]["changes"] if c["class"] == "evidence.superseded"]
        self.assertEqual((sup["subject"]["id"], sup["fields"][0]["after"]), ("MAI-EV-0029", ["MAI-EV-0032", "MAI-EV-0039"]))
        # v0.4.0 begins the gap register; v0.10.0 and v0.10.1 did not change the record.
        self.assertIn("gap.register_started", self.by_version["0.4.0"]["counts"])
        for v in ("0.4.1", "0.10.0", "0.10.1"):
            self.assertEqual(self.by_version[v]["changes"], [], v)

    def test_every_reference_resolves(self):
        records = {r["evidence_id"] for r in json.loads((REPO / "data" / "evidence.json").read_text())["records"]}
        for t in self.log["transitions"]:
            for c in t["changes"]:
                self.assertLessEqual(set(c.get("evidence", [])), records, c["id"])
        self.assertNotIn("event_date", json.dumps(self.log))
        self.assertEqual(self.log["schema_version"], changes.SCHEMA_VERSION)


class PublishedPage(unittest.TestCase):
    def setUp(self):
        self.html = PAGE.read_text(encoding="utf-8")
        self.text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", self.html)))

    def test_page_separates_record_changes_from_events(self):
        self.assertIn("Record changes, not events", self.text)
        for label in ("Sources checked", "Source published", "Retrieved", "Event date"):
            self.assertIn(label, self.text)
        self.assertIn("Not inferred", self.text)
        self.assertNotRegex(self.text, r"(?i)\b(was launched|became operational|happened) in v\d")
        self.assertIn("lifecycle stage first recorded as announced", self.text)
        self.assertIn("lifecycle stage changed from announced to operational", self.text)

    def test_page_is_wired_into_the_site(self):
        p = check_site.Page()
        p.feed(self.html)
        self.assertEqual(p.h1, 1)
        self.assertEqual(p.canonical, "https://themoroccoai.com/registry/changes/")
        self.assertEqual(check_site.social_meta_errors("registry/changes/index.html", p), [])
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', self.html, re.S).group(1))
        self.assertEqual(ld["@type"], "Dataset")
        self.assertIn("https://themoroccoai.com/registry/changes/</loc>", (REPO / "sitemap.xml").read_text())
        manifest = json.loads((REPO / "data" / "manifest.json").read_text())
        [res] = [r for r in manifest["resources"] if r["path"] == "/registry/changes/changes.json"]
        import hashlib
        self.assertEqual(res["sha256"], hashlib.sha256(JSON_PATH.read_bytes()).hexdigest())
        self.assertEqual(res["role"], "derived")
        for e in ("idarati-ai", "um6p"):
            page = (REPO / "registry" / e / "index.html").read_text(encoding="utf-8")
            self.assertIn('<h2 id="hist-h"><span class="section-number">03</span>Record history</h2>', page)
            self.assertIn('href="/registry/changes/', page)

    def test_every_version_has_a_section_and_newest_comes_first(self):
        ids = re.findall(r'<h2 id="(v[0-9-]+)">', self.html)
        self.assertEqual(len(ids), len(json.loads(JSON_PATH.read_text())["transitions"]))
        self.assertEqual(ids[0], "v0-10-1")
        self.assertEqual(ids[-1], "v0-2-0")


if __name__ == "__main__":
    unittest.main()
