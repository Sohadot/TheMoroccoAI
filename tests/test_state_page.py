"""Sprint 10 Tier 2: /registry/state/ presents /registry/reference-state.json. The snapshot decides every value, member
and group; the canonical files only supply display names, titles and definitions for items already in the snapshot."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import build  # noqa: E402
import registry  # noqa: E402

PAGE = REPO / "registry" / "state" / "index.html"


def parse(text):
    p = build._StateParser()
    p.feed(text)
    return p


def ids_under(p, prefix, field="id"):
    return {json.loads(raw) for ptr, raw, _ in p.refs if re.fullmatch(re.escape(prefix) + r"/\d+/" + field, ptr)}


def main_text(text):
    m = text[text.index("<main"):text.index("</main>")]
    return " ".join(re.sub(r"<[^>]+>", " ", m).split())


class StatePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.s = json.loads((REPO / "registry" / "reference-state.json").read_text(encoding="utf-8"))
        cls.evidence, cls.ontology = registry.load_all()
        cls.model = build.Model(cls.evidence, cls.ontology)
        cls.gaps = registry.load(registry.ROOT / "data" / "gaps.json")
        cls.p = parse(cls.html)

    def render(self, s=None, model=None):
        return build.render_state(model or self.model, s or self.s, self.gaps)

    def errors(self, html, s=None, model=None):
        return build.state_page_errors(html, s or self.s, model or self.model, self.gaps)

    def inject(self, fragment):
        return self.html.replace("</main>", fragment + "</main>")

    # ─── Data fidelity ─────────────────────────────────────────────────────

    def test_page_is_generated_and_faithful(self):
        self.assertEqual(self.render(), self.html)
        self.assertEqual(self.errors(self.html), [])

    def test_every_displayed_value_equals_the_snapshot(self):
        self.assertTrue(self.p.refs)
        for ptr, raw, text in self.p.refs:
            value = build._resolve(self.s, ptr)
            self.assertEqual(json.loads(raw), value, ptr)
            if isinstance(value, int) and not isinstance(value, bool):
                self.assertEqual(text.strip(), str(value), ptr)

    def test_every_snapshot_value_is_shown(self):
        shown = {ptr for ptr, _, _ in self.p.refs}
        for leaf in build._leaves({k: v for k, v in self.s.items() if k != "derivation"}):
            self.assertIn(leaf, shown)

    def test_displayed_counts(self):
        refs = {ptr: json.loads(raw) for ptr, raw, _ in self.p.refs}
        self.assertEqual((refs["/counts/records"], refs["/counts/entities"], refs["/counts/relationships"], refs["/open_gaps#count"]), (63, 65, 78, 7))
        self.assertEqual(refs["/counts/records_by_classification/OFFICIAL TARGET"], 10)
        for k, v in self.s["counts"]["entities_by_type"].items():
            self.assertEqual(refs[f"/counts/entities_by_type/{k}"], v)

    def test_members_match_their_projections(self):
        self.assertEqual(ids_under(self.p, "/operational_or_pilot"), {x["id"] for x in self.s["operational_or_pilot"]})
        self.assertEqual(ids_under(self.p, "/lifecycle/entities"), {x["id"] for x in self.s["lifecycle"]["entities"]})
        self.assertEqual(ids_under(self.p, "/official_targets", "evidence_id"), {x["evidence_id"] for x in self.s["official_targets"]})
        self.assertEqual(ids_under(self.p, "/open_gaps"), {g["id"] for g in self.s["open_gaps"]})
        for k, ids in self.s["announced_projects_by_kind"].items():
            self.assertEqual({json.loads(raw) for ptr, raw, _ in self.p.refs if re.fullmatch(rf"/announced_projects_by_kind/{re.escape(k)}/\d+", ptr)}, set(ids))

    def test_gap07_dimensions_unaltered(self):
        shown = {ptr: json.loads(raw) for ptr, raw, _ in self.p.refs if ptr.startswith("/entity_assessments/")}
        for ptr, value in shown.items():
            self.assertEqual(build._resolve(self.s, ptr), value)
        dims = {ptr.split("/")[6] for ptr in shown if "/dimensions/" in ptr}
        self.assertLessEqual(dims, set(self.gaps["entity_assessment"]["dimension_order"]))
        self.assertNotRegex(main_text(self.html), r"(?i)dimension score|out of \d")

    def test_unresolved_lifecycle_and_origin_stay_separate(self):
        section = self.html[self.html.index('id="s8-h"'):self.html.index('id="s9-h"')]
        lifecycle_part, origin_part = section.split("Unresolved company origin</h3>")
        self.assertIn("/unresolved_lifecycle/", lifecycle_part)
        self.assertNotIn("/unresolved_origin/", lifecycle_part)
        self.assertIn("/unresolved_origin/", origin_part)
        self.assertNotIn("/unresolved_lifecycle/", origin_part)
        self.assertIn("Two different concepts, kept apart.", section)

    # ─── Semantic boundaries ───────────────────────────────────────────────

    def test_no_initiative_in_a_lifecycle_or_operational_member(self):
        shown = {json.loads(raw) for ptr, raw, _ in self.p.refs
                 if re.match(r"/(operational_or_pilot|lifecycle/entities|unresolved_lifecycle|announced_projects_by_kind)/", ptr)
                 and isinstance(json.loads(raw), str)}
        self.assertFalse({x for x in shown if x in self.model.entities and self.model.entities[x]["type"] == "initiative"})

    def test_platform_and_compute_are_not_ai_deployments(self):
        refs = {ptr: (json.loads(raw), text) for ptr, raw, text in self.p.refs}
        for i, x in enumerate(self.s["operational_or_pilot"]):
            value, text = refs[f"/operational_or_pilot/{i}/counts_as_ai_deployment"]
            self.assertEqual((value, text), (x["project_kind"] == "ai-application", "Yes" if x["project_kind"] == "ai-application" else "No"), x["id"])
        self.assertIn("Operational does not automatically mean AI deployment.", self.html)
        self.assertIn("compute infrastructure and digital platforms do not", self.html)

    def test_wording_boundaries(self):
        # The page's own wording: governed values and canonical labels (record titles, gap questions) are excluded,
        # since they are quoted from the data, not written by the page.
        text = " ".join(" ".join(self.p.static).split())
        self.assertIn("Availability is not evidence of use", text)
        self.assertIn("Announced means no later lifecycle stage is recorded here.", text)
        self.assertIn("A target is not a result", text)
        self.assertIn("It does not prove that the underlying activity does not exist.", text)
        for bad in (r"\bin use\b", r"\badopt\w*", r"widely deployed", r"not delivered", r"failed to launch", r"\bachiev\w*",
                    r"on track", r"targets? met", r"no progress"):
            self.assertNotRegex(text, rf"(?i){bad}")
        for sentence in re.split(r"(?<=[.;])\s+", text):
            if re.search(r"(?i)does not exist", sentence):
                self.assertRegex(sentence, r"(?i)not prove|not that", sentence)

    def test_sections_are_the_approved_ones(self):
        headings = re.findall(r'<h2 id="s\d-h"><span class="section-number">\d+</span>([^<]+)</h2>', self.html)
        self.assertEqual(headings, ["Registry composition", "Lifecycle reference", "Operational and pilot projects", "Announced projects",
                                    "Official targets", "Open evidence gaps", "Evidence transparency", "Unresolved cases",
                                    "Machine-readable verification"])
        self.assertNotRegex(main_text(self.html), r"(?i)where official sources disagree|conflict count|progress tracker")

    # ─── The build gate refuses what the page must not say ─────────────────

    def test_forbidden_concepts_are_refused(self):
        for fragment in ("<p>Confidence: high.</p>", "<p>Completeness of the record.</p>", "<p>Evidence state: documented.</p>",
                         "<p>Conflicts between sources.</p>", "<p>Strategy progress.</p>", "<p>Targets met.</p>",
                         "<p>Ranking of organisations.</p>", "<p>Cumulative appropriations.</p>", "<p>Leading funders.</p>",
                         "<p>Government actors.</p>", "<p>First-party sources only.</p>", "<p>AI readiness.</p>",
                         "<p>The platform is widely adopted.</p>", "<p>Not delivered.</p>"):
            self.assertTrue(self.errors(self.inject(fragment)), fragment)

    def test_static_numbers_are_refused(self):
        self.assertTrue(any("static text carries a number" in e for e in self.errors(self.inject("<p>Three of 12 projects.</p>"))))

    def test_a_value_that_differs_from_the_snapshot_is_refused(self):
        bad = self.html.replace('data-ref="/counts/records" data-value="63">63<', 'data-ref="/counts/records" data-value="64">64<')
        self.assertNotEqual(bad, self.html)
        self.assertTrue(self.errors(bad))
        lying_text = self.html.replace('data-ref="/counts/records" data-value="63">63<', 'data-ref="/counts/records" data-value="63">64<')
        self.assertTrue(any("displays" in e for e in self.errors(lying_text)))

    def test_provenance_wording_separates_governed_values_from_lookups(self):
        # The page may not claim that every value comes from the snapshot: names, titles and definitions are canonical lookups.
        text = re.sub(r"\s+([;,.])", r"\1", main_text(self.html))
        self.assertIn("Every governed value below is read from reference-state.json; human-readable names, titles and definitions "
                      "are presentation lookups from the canonical registry files.", text)
        self.assertNotRegex(text, r"(?i)\bevery value (below|on (this|the) page)\b")
        self.assertNotRegex(text, r"(?i)\ball values? (below |on (this|the) page )?(is|are) (read )?from")
        v0101 = next(e for e in json.loads((REPO / "data" / "changelog.json").read_text(encoding="utf-8"))["entries"] if e["version"] == "0.10.1")
        self.assertTrue(any(c.startswith("Every governed value on the page is read from the snapshot") for c in v0101["changes"]))
        self.assertFalse(any("Every value on the page" in c for c in v0101["changes"]))

    def test_required_disclaimers_are_present(self):
        # Pinned here, independently of build.STATE_BOUNDARY, so that removing one from the build cannot pass silently.
        required = ["Independent; not affiliated with the Government of Morocco.",
                    "This page describes what the registry records, not the totality of Morocco's AI ecosystem.",
                    "Absence from the registry is not evidence of absence.",
                    "A target is not a result.",
                    "Availability is not evidence of use.",
                    "Announced is not operational.",
                    "Conflicting official statements are not resolved by inference."]
        box = self.html[self.html.index('<div class="notice state-boundary">'):]
        box = box[:box.index("</div>")]
        self.assertEqual(re.findall(r"<li>(.*?)</li>", box.replace("&#x27;", "'")), required)
        self.assertIn('data-ref="/as_of"', box)

    def test_a_missing_boundary_statement_is_refused(self):
        bad = self.html.replace("<li>A target is not a result.</li>", "")
        self.assertTrue(any("boundary statement missing" in e for e in self.errors(bad)))

    # ─── Snapshot is the source; canonical data is presentation only ───────

    def test_removing_an_item_from_the_snapshot_removes_it_from_the_page(self):
        s = copy.deepcopy(self.s)
        s["operational_or_pilot"] = [x for x in s["operational_or_pilot"] if x["id"] != "toubkal-supercomputer"]
        s["operational_or_pilot_by_status_basis"].pop("independent-listing")
        html = self.render(s)
        section = html[html.index('id="s3-h"'):html.index('id="s4-h"')]
        self.assertNotIn("toubkal-supercomputer", section)
        self.assertIn("idarati-ai", section)

    def test_canonical_only_data_does_not_appear(self):
        ontology = copy.deepcopy(self.ontology)
        extra = copy.deepcopy(next(e for e in ontology["entities"] if e["id"] == "idarati-ai"))
        extra.update(id="canonical-only-project", name="Canonical Only Project")
        ontology["entities"].append(extra)
        model = build.Model(self.evidence, ontology)
        html = self.render(model=model)
        self.assertNotIn("canonical-only-project", html)
        self.assertNotIn("Canonical Only Project", html)
        self.assertEqual(html, self.html)

    def test_lookup_changes_names_only(self):
        ontology = copy.deepcopy(self.ontology)
        e = next(e for e in ontology["entities"] if e["id"] == "idarati-ai")
        e["name"] = "Renamed Service"
        e["lifecycle"] = "announced"   # a canonical change the snapshot does not carry must not move it
        model = build.Model(self.evidence, ontology)
        html = self.render(model=model)
        p = parse(html)
        self.assertIn("Renamed Service", html)
        self.assertEqual([(a, b) for a, b, _ in p.refs], [(a, b) for a, b, _ in self.p.refs])
        section = html[html.index('id="s3-h"'):html.index('id="s4-h"')]
        self.assertIn("idarati-ai", section)
        self.assertIn('data-ref="/operational_or_pilot/0/lifecycle" data-value="&quot;operational&quot;">Operational<', html)

    def test_lookups_only_label_items_in_the_snapshot(self):
        for label, text in self.p.labels:
            kind, _, key = label.partition(":")
            self.assertIn(kind, ("entity", "record-title", "gap-question", "classification", "predicate"))
        self.assertNotIn('"cndp"', json.dumps(self.s))
        bad = self.inject('<p><span data-label="entity:cndp">National Commission for the Control of Personal Data Protection (CNDP)</span></p>')
        self.assertTrue(any("absent from the snapshot" in e for e in self.errors(bad)))
        renamed = self.inject('<p><span data-label="entity:idarati-ai">Something else</span></p>')
        self.assertTrue(any("does not match the canonical data" in e for e in self.errors(renamed)))

    # ─── Metadata, navigation and structure ────────────────────────────────

    def test_metadata_and_sitemap(self):
        self.assertIn('<link rel="canonical" href="https://themoroccoai.com/registry/state/">', self.html)
        self.assertIn('<meta property="og:url" content="https://themoroccoai.com/registry/state/">', self.html)
        self.assertIn("<title>Reference State — TheMoroccoAI</title>", self.html)
        self.assertIn('<html lang="en"', self.html)
        self.assertEqual(self.html.count("<h1>"), 1)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', self.html, re.S).group(1))
        self.assertEqual((ld["@type"], ld["version"], ld["distribution"][0]["contentUrl"]),
                         ("Dataset", self.s["registry_version"], "https://themoroccoai.com/registry/reference-state.json"))
        self.assertIn("<loc>https://themoroccoai.com/registry/state/</loc>", (REPO / "sitemap.xml").read_text(encoding="utf-8"))

    def test_entry_points_and_verification_links(self):
        for page in ("registry/index.html", "data/index.html"):
            self.assertIn('href="/registry/state/"', (REPO / page).read_text(encoding="utf-8"), page)
        for href in ("/registry/reference-state.json", "/data/manifest.json", "/data/", "/examples/registry_consumer.py", "/methodology/"):
            self.assertIn(f'href="{href}"', self.html, href)
        self.assertIn("Hashes establish build consistency, not truth or authorship.", self.html)

    def test_expandable_content_is_keyboard_accessible(self):
        self.assertEqual(self.html.count("<details"), self.html.count("<summary"))
        self.assertNotIn('tabindex="-1"', self.html)
        for summary in re.findall(r"<summary>(.*?)</summary>", self.html, re.S):
            self.assertNotRegex(summary, r"<(a|button|input|select|textarea)\b", "a summary must not contain another interactive element")
        self.assertGreaterEqual(self.html.count("<details"), 3)

    def test_no_runtime_script_or_third_party_resource(self):
        scripts = re.findall(r"<script(?![^>]*application/ld\+json)[^>]*>", self.html)
        self.assertEqual(scripts, [])
        for url in re.findall(r'(?:src|href)="(https?://[^"]+)"', self.html):
            self.assertTrue(url.startswith("https://themoroccoai.com"), url)

    def test_reference_contract_unchanged(self):
        self.assertEqual(set(self.s), set(registry.REFERENCE_FIELDS))
        self.assertEqual(registry.validate_reference_state(self.s, self.evidence, self.ontology), [])


if __name__ == "__main__":
    unittest.main()
