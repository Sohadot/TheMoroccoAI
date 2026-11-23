"""Source intelligence pipeline (tools/observatory.py, sources/watchlist.json).

Every page below is a SYNTHETIC fixture served by a fake fetcher: no network, no real source, no real development.
Synthetic pages name real registry entities only to exercise entity matching; their text is invented and marked so.
The staging store is a temporary directory outside the repository.
Run: python3 -m unittest discover -s tests
"""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import check_site  # noqa: E402
import observatory as ob  # noqa: E402
import registry  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NOW = "2026-11-23T10:00:00Z"
LATER = "2026-11-30T10:00:00Z"


def page(*paragraphs, script="var t = 1;", extra=""):
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return (f'<html><head><title>SYNTHETIC fixture</title><script>{script}</script></head>'
            f'<body {extra}><nav><a href="/">Home</a></nav>{body}<footer>© 2026 Synthetic publisher</footer></body></html>').encode()


def fetcher(responses):
    """A fake fetcher: url -> (status, body, content type, error, final url)."""
    calls = []

    def fetch(url):
        calls.append(url)
        r = responses.get(url, (200, page("SYNTHETIC default page."), "text/html; charset=utf-8", None, url))
        return r
    fetch.calls = calls
    return fetch


class AllowAll:
    def allowed(self, url):
        return True


class DenyAll:
    def allowed(self, url):
        return False


SOURCE = {"id": "SRC-901", "slug": "synthetic", "name": "SYNTHETIC source", "url": "https://synthetic.example/",
          "category": "government_portal", "language": "en", "relevance": "Synthetic.", "records": [], "entities": ["idarati-ai"],
          "method": "http-get", "frequency": "weekly", "access": "Synthetic.", "status": "active", "added": "2026-11-23"}


def ok(body, url=SOURCE["url"], final=None, ct="text/html; charset=utf-8"):
    return (200, body, ct, None, final or url)


class Base(unittest.TestCase):
    def setUp(self):
        self.evidence, self.ontology = registry.load_all()
        self.store = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.store)

    def obs(self, body, now=NOW, source=SOURCE, **kw):
        return ob.observe(source, fetcher({source["url"]: ok(body, **kw)}), AllowAll(), now)


class Watchlist(unittest.TestCase):
    def setUp(self):
        self.evidence, self.ontology = registry.load_all()
        self.wl = ob.load_watchlist()

    def test_committed_watchlist_is_valid_and_only_cites_cited_sources(self):
        self.assertEqual(ob.validate_watchlist(self.wl, self.evidence, self.ontology), [])
        records = {r["evidence_id"]: r for r in self.evidence["records"]}
        self.assertGreaterEqual(len(self.wl["sources"]), 10)
        for s in self.wl["sources"]:
            for rid in s["records"]:
                self.assertEqual(records[rid]["source_url"], s["url"])
        self.assertTrue(all(s["status"] == "paused" for s in self.wl["sources"] if "robots" in s.get("status_reason", "")))

    def test_invalid_entries_are_rejected(self):
        cases = [
            ({"url": "https://not-cited.example/"}, "cites a different URL"),
            ({"records": []}, "only cited sources are watched"),
            ({"status": "paused"}, "needs a status_reason"),
            ({"category": "blog"}, "registry source type"),
            ({"id": "SRC-1"}, "id must look like"),
            ({"ignore_patterns": ["("]}, "invalid ignore pattern"),
            ({"partner_priority": "high"}, "unexpected fields"),
        ]
        for over, fragment in cases:
            wl = copy.deepcopy(self.wl)
            wl["sources"][0].update(over)
            errors = ob.validate_watchlist(wl, self.evidence, self.ontology)
            self.assertTrue(any(fragment in e for e in errors), (over, errors))
        wl = copy.deepcopy(self.wl)
        wl["sources"].append(dict(wl["sources"][0]))
        self.assertTrue(any("duplicate id" in e for e in ob.validate_watchlist(wl, self.evidence, self.ontology)))

    def test_cli_validate(self):
        self.assertEqual(ob.main(["validate"]), 0)


class Observation(Base):
    def test_deterministic_with_stable_fingerprints(self):
        a, b = self.obs(page("SYNTHETIC alpha.", "SYNTHETIC beta.")), self.obs(page("SYNTHETIC alpha.", "SYNTHETIC beta."))
        self.assertEqual(a, b)
        self.assertEqual(a["outcome"], "retrieved")
        self.assertEqual(a["text_sha256"], ob._sha("\n".join(a["blocks"])))
        self.assertNotIn("var t", " ".join(a["blocks"]))  # scripts are not content

    def test_formatting_noise_is_suppressed(self):
        a = self.obs(page("SYNTHETIC alpha  text.", "Updated 10:42 today.", script="var t=1"))
        b = self.obs(page("SYNTHETIC alpha text.", "Updated 11:07 today.", script="var t=2; var cachebust='9f8e7d6c5b4a39281706'", extra='class="x"'))
        self.assertEqual(ob.compare(a, b)["kind"], "formatting-only")
        self.assertEqual(ob.compare(a, a)["kind"], "unchanged")
        self.assertEqual(ob.compare(self.obs(page("SYNTHETIC one.", "SYNTHETIC two.")), self.obs(page("SYNTHETIC two.", "SYNTHETIC one.")))["kind"], "reordered")

    def test_source_ignore_patterns(self):
        src = dict(SOURCE, ignore_patterns=[r"(?i)^downloads? last month"])
        a = self.obs(page("SYNTHETIC model card.", "Downloads last month 1,204"), source=src)
        b = self.obs(page("SYNTHETIC model card.", "Downloads last month 9,876"), source=src)
        self.assertEqual(ob.compare(a, b)["kind"], "formatting-only")

    def test_substantive_change_lists_added_and_removed_text(self):
        a = self.obs(page("SYNTHETIC alpha.", "SYNTHETIC beta."))
        b = self.obs(page("SYNTHETIC alpha.", "SYNTHETIC gamma."), now=LATER)
        self.assertEqual(ob.compare(a, b), {"kind": "substantive", "added": ["SYNTHETIC gamma."], "removed": ["SYNTHETIC beta."]})

    def test_failures_are_never_changes_or_disappearances(self):
        good = self.obs(page("SYNTHETIC alpha."))
        for response, outcome in (((None, b"", "", "timed out", SOURCE["url"]), "unreachable"),
                                  ((403, b"denied", "text/html", None, SOURCE["url"]), "blocked"),
                                  ((503, b"down", "text/html", None, SOURCE["url"]), "http-error")):
            bad = ob.observe(SOURCE, fetcher({SOURCE["url"]: response}), AllowAll(), LATER)
            self.assertEqual(bad["outcome"], outcome)
            self.assertEqual(ob.compare(good, bad)["kind"], "not-comparable")
            self.assertEqual(ob.compare(bad, good)["kind"], "not-comparable")
            self.assertEqual(ob.detect_candidates(SOURCE, bad, ob.compare(good, bad), self.evidence, self.ontology, {}), [])
        fail = {"outcome": "unreachable"}
        self.assertEqual(ob.availability([good, fail, fail]), "failed-last")
        self.assertEqual(ob.availability([good, fail, fail, fail]), "unreliable")
        self.assertEqual(ob.availability([fail, fail, fail, good]), "reliable")

    def test_robots_disallowed_means_no_request(self):
        f = fetcher({})
        o = ob.observe(SOURCE, f, DenyAll(), NOW)
        self.assertEqual(o["outcome"], "robots-disallowed")
        self.assertEqual(f.calls, [])

    def test_redirects_encodings_and_formats(self):
        o = self.obs(page("SYNTHETIC moved."), final="https://synthetic.example/new/")
        self.assertTrue(o["redirected"])
        self.assertEqual(o["final_url"], "https://synthetic.example/new/")
        bad = ob.observe(SOURCE, fetcher({SOURCE["url"]: ok(b"<p>SYNTHETIC caf\xe9 broken \xff</p>")}), AllowAll(), NOW)
        self.assertTrue(bad["encoding_issue"])
        pdf = ob.observe(SOURCE, fetcher({SOURCE["url"]: ok(b"%PDF-1.7 synthetic", ct="application/pdf")}), AllowAll(), NOW)
        self.assertEqual(pdf["outcome"], "unreadable-format")

    def test_arabic_and_french_text_keep_their_language(self):
        o = self.obs(page("نص تجريبي عن الذكاء الاصطناعي (SYNTHETIC).", "Texte SYNTHETIC sur l'intelligence artificielle pour les services."))
        self.assertIn("نص تجريبي عن الذكاء الاصطناعي (SYNTHETIC).", o["blocks"])
        ar = next(b for b in o["blocks"] if "نص" in b)
        fr = next(b for b in o["blocks"] if "Texte" in b)
        self.assertEqual((ob.language_of(ar), ob.language_of(fr)), ("ar", "fr"))


class Candidates(Base):
    def change(self, before, after):
        a, b = self.obs(page(*before)), self.obs(page(*after), now=LATER)
        return b, ob.compare(a, b)

    def test_relevant_additions_become_candidates_irrelevant_ones_do_not(self):
        b, cmp = self.change(["SYNTHETIC home."], ["SYNTHETIC home.", "SYNTHETIC: Idarati AI now answers in Amazigh.", "SYNTHETIC cookie policy updated."])
        [c] = ob.detect_candidates(SOURCE, b, cmp, self.evidence, self.ontology, {})
        self.assertEqual(c["related_entities"], ["idarati-ai"])
        self.assertEqual(c["state"], "detected")
        self.assertEqual(c["observed_at"], LATER)
        self.assertEqual(c["id"], ob.candidate_id(SOURCE["id"], c["excerpt"]))
        self.assertEqual(c["history"][0]["by"], ob.AUTOMATED_ACTOR)

    def test_ids_are_stable_and_repeats_are_not_duplicated(self):
        b, cmp = self.change(["SYNTHETIC."], ["SYNTHETIC.", "SYNTHETIC generative AI programme announced."])
        [c] = ob.detect_candidates(SOURCE, b, cmp, self.evidence, self.ontology, {})
        self.assertEqual(ob.detect_candidates(SOURCE, b, cmp, self.evidence, self.ontology, {c["id"]: c}), [])

    def test_text_already_in_the_registry_is_flagged_as_duplicate_evidence(self):
        rec = next(r for r in self.evidence["records"] if r["source_excerpts"] and len(r["source_excerpts"][0]) > 40)
        b, cmp = self.change(["SYNTHETIC."], ["SYNTHETIC.", rec["source_excerpts"][0] + " (AI)"])
        [c] = ob.detect_candidates(SOURCE, b, cmp, self.evidence, self.ontology, {})
        self.assertIn(rec["evidence_id"], c["duplicate_of_evidence"])

    def test_triage_queues_or_marks_duplicates_and_never_decides(self):
        b, cmp = self.change(["SYNTHETIC."], ["SYNTHETIC.", "SYNTHETIC AI lab opens."])
        [c1] = ob.detect_candidates(SOURCE, b, cmp, self.evidence, self.ontology, {})
        other = dict(SOURCE, id="SRC-902", url="https://synthetic-two.example/")
        c2 = dict(c1, id=ob.candidate_id("SRC-902", c1["excerpt"]), source_id="SRC-902")
        out = ob.triage({c1["id"]: c1, c2["id"]: c2})
        states = sorted(c["state"] for c in out.values())
        self.assertEqual(states, ["awaiting_review", "duplicate"])
        self.assertFalse(any(c["state"] in ("accepted_for_admission", "rejected") for c in out.values()))


class ReviewWorkflow(Base):
    def candidate(self):
        return {"id": "CAND-synthetic01", "state": "detected", "history": [], "excerpt": "SYNTHETIC", "source_url": SOURCE["url"],
                "source_id": SOURCE["id"], "observed_at": NOW, "language": "en"}

    def test_allowed_path_to_admission(self):
        c = ob.transition(self.candidate(), "awaiting_review", ob.AUTOMATED_ACTOR, "Queued.")
        for to in ("under_verification", "needs_additional_evidence", "under_verification", "accepted_for_admission"):
            c = ob.transition(c, to, "reviewer-owner-01", f"SYNTHETIC decision: {to}.")
        self.assertEqual([h["state"] for h in c["history"]],
                         ["awaiting_review", "under_verification", "needs_additional_evidence", "under_verification", "accepted_for_admission"])

    def test_forbidden_moves(self):
        c = ob.transition(self.candidate(), "awaiting_review", ob.AUTOMATED_ACTOR, "Queued.")
        with self.assertRaisesRegex(ob.StagingError, "needs a human reviewer"):
            ob.transition(c, "under_verification", ob.AUTOMATED_ACTOR, "x")
        with self.assertRaisesRegex(ob.StagingError, "not an allowed transition"):
            ob.transition(c, "accepted_for_admission", "reviewer-owner-01", "skip verification")
        with self.assertRaisesRegex(ob.StagingError, "never an automated identity"):
            ob.transition(c, "under_verification", "claude-reviewer", "x")
        with self.assertRaisesRegex(ob.StagingError, "needs a note"):
            ob.transition(c, "under_verification", "reviewer-owner-01", " ")
        rejected = ob.transition(c, "rejected", "reviewer-owner-01", "SYNTHETIC: not about Morocco.")
        with self.assertRaisesRegex(ob.StagingError, "not an allowed transition"):
            ob.transition(rejected, "awaiting_review", "reviewer-owner-01", "reopen")
        with self.assertRaisesRegex(ob.StagingError, "unknown state"):
            ob.transition(c, "verified", "reviewer-owner-01", "x")


class Admission(Base):
    def setUp(self):
        super().setUp()
        self.observation = self.obs(page("SYNTHETIC home.", "SYNTHETIC: the ministry lists a new AI service for citizens."), now=LATER)
        self.c = {"id": "CAND-synthetic02", "state": "accepted_for_admission", "history": [], "source_url": SOURCE["url"],
                  "source_id": SOURCE["id"], "observed_at": LATER, "language": "en",
                  "excerpt": "SYNTHETIC: the ministry lists a new AI service for citizens."}
        self.decision = {"title": "SYNTHETIC title", "claim": "SYNTHETIC claim.", "classification": "VERIFIED FACT",
                         "verification_status": "verified", "verification_note": "SYNTHETIC note.", "evidence_type": "official_announcement",
                         "source_type": "government_portal", "source_organization": "SYNTHETIC publisher", "publication_date": None,
                         "related_entities": ["idarati-ai"], "source_excerpts": ["the ministry lists a new AI service for citizens"]}

    def test_proposal_is_a_draft_and_never_touches_data(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((REPO / "data").glob("*.json"))}
        p = ob.propose_admission(self.c, self.decision, self.observation, self.evidence, self.ontology, "reviewer-owner-01")
        after = {p_: hashlib.sha256(p_.read_bytes()).hexdigest() for p_ in sorted((REPO / "data").glob("*.json"))}
        self.assertEqual(before, after)
        last = max(int(r["evidence_id"][-4:]) for r in self.evidence["records"])
        self.assertEqual(p["record"]["evidence_id"], f"MAI-EV-{last + 1:04d}")
        self.assertEqual(p["record"]["retrieval_date"], "2026-11-30")
        self.assertEqual(p["record"]["source_url"], SOURCE["url"])
        self.assertIsInstance(p["validation"], list)  # the validator's verdict travels with the draft
        self.assertEqual(p["marker"], ob.STAGING_MARKER)

    def test_admission_boundaries(self):
        for state in ("detected", "awaiting_review", "under_verification", "rejected", "duplicate"):
            with self.assertRaisesRegex(ob.StagingError, "accepted for admission"):
                ob.propose_admission(dict(self.c, state=state), self.decision, self.observation, self.evidence, self.ontology, "reviewer-owner-01")
        with self.assertRaisesRegex(ob.StagingError, "human reviewer"):
            ob.propose_admission(self.c, self.decision, self.observation, self.evidence, self.ontology, "observatory")
        with self.assertRaisesRegex(ob.StagingError, "verbatim"):
            ob.propose_admission(self.c, dict(self.decision, source_excerpts=["an AI summary of what the page says"]),
                                 self.observation, self.evidence, self.ontology, "reviewer-owner-01")
        with self.assertRaisesRegex(ob.StagingError, "lacks"):
            ob.propose_admission(self.c, {"title": "x"}, self.observation, self.evidence, self.ontology, "reviewer-owner-01")


class StagingIsolation(Base):
    def test_store_is_outside_the_repository_and_marked(self):
        with self.assertRaisesRegex(ob.StagingError, "outside the public repository"):
            ob.store_dir(REPO / "staging")
        with self.assertRaisesRegex(ob.StagingError, "outside the public repository"):
            ob.store_dir(REPO)
        self.assertEqual(ob.store_dir(self.store), self.store.resolve())
        ob.save_candidates(self.store, {})
        self.assertIn(ob.STAGING_MARKER, (self.store / "candidates.json").read_text())

    def test_site_gate_rejects_staging_material_in_the_repository(self):
        site = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, site)
        ob.save_candidates(site / "leaked", {})
        original = check_site.ROOT
        check_site.ROOT = site
        self.addCleanup(setattr, check_site, "ROOT", original)
        errors = check_site.check_draft_leaks()
        self.assertTrue(any("observatory staging" in e for e in errors), errors)
        check_site.ROOT = original
        self.assertEqual(check_site.check_draft_leaks(), [])

    def test_no_candidate_material_reaches_the_published_site(self):
        evidence, ontology = registry.load_all()
        files, _ = build.build_outputs(build.Model(evidence, ontology))
        self.assertFalse([p for p in files if "observ" in p or p.startswith("sources/")])
        joined = "".join(files.values())
        self.assertNotIn(ob.STAGING_MARKER, joined)
        self.assertNotIn("CAND-", joined)
        self.assertNotIn("/sources/watchlist.json", (REPO / "sitemap.xml").read_text())


class PipelineAndReport(Base):
    def test_end_to_end_on_fixtures_answers_the_research_questions(self):
        rec = next(r for r in self.evidence["records"] if r["source_excerpts"])
        src = dict(SOURCE, records=[rec["evidence_id"]], url=rec["source_url"])
        wl = {"schema_version": "1.0", "sources": [src, dict(SOURCE, id="SRC-902", slug="down", url="https://down.example/")]}
        first = page("SYNTHETIC home.", *rec["source_excerpts"])
        second = page("SYNTHETIC home.", "SYNTHETIC: Idarati AI adds a new service.")  # the cited excerpts vanished
        down = (None, b"", "", "timed out", "https://down.example/")
        for body in (first, second):
            f = fetcher({src["url"]: ok(body, url=src["url"]), "https://down.example/": down})
            ob.run_observation(wl, self.store, self.evidence, self.ontology, fetcher=f, robots=AllowAll(), sleep=lambda s: None)
        ob.run_observation(wl, self.store, self.evidence, self.ontology, only="SRC-902",
                           fetcher=fetcher({"https://down.example/": down}), robots=AllowAll(), sleep=lambda s: None)
        r = ob.report(wl, self.store, self.evidence)
        rows = {x["source"]: x for x in r["sources"]}
        self.assertEqual(r["changed"], ["SRC-901"])
        self.assertEqual(r["unreliable"], ["SRC-902"])
        self.assertEqual(rows["SRC-901"]["reassessment"][0]["record"], rec["evidence_id"])
        self.assertEqual(list(r["candidates_by_state"]), ["awaiting_review"])
        self.assertEqual(r["admitted"], [])
        self.assertEqual(len(ob.observations(self.store, "SRC-901")), 2)  # same-second observations are both kept
        stored = json.loads((self.store / "candidates.json").read_text())
        self.assertEqual(stored["marker"], ob.STAGING_MARKER)


if __name__ == "__main__":
    unittest.main()
