"""Acquisition readiness (Issue #26): ownership, acquisition wording, rights, counts, dates, tables and the
independent evaluation tool.

The browser test drives /evaluation/ in headless Chromium (skipped when no browser is found, like test_layout).
Run: python3 -m unittest discover -s tests
"""
import functools
import html
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import check_site  # noqa: E402
import registry  # noqa: E402
from test_layout import BROWSER  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def visible(page):
    page = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))


def model():
    evidence, ontology = registry.load_all()
    return build.Model(evidence, ontology)


class Ownership(unittest.TestCase):
    def test_ownership_is_stated_once_clearly_on_the_acquisition_page_and_homepage(self):
        acq = visible((REPO / "acquisition" / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(acq.count(check_site.OWNERSHIP_STATEMENT), 1)
        self.assertNotIn("No institution has adopted or designated it", acq)  # covered by the statement and the table
        home = (REPO / "index.html").read_text(encoding="utf-8")
        acquire = home[home.index('id="acquire"'):home.index("</section>", home.index('id="acquire"'))]
        self.assertIn(check_site.OWNERSHIP_STATEMENT, visible(acquire))

    def test_every_page_footer_names_the_owner(self):
        for path in check_site.site_pages():
            self.assertIn("Owned and operated by Sohadot", visible(path.read_text(encoding="utf-8")), path)


class AcquisitionLanguage(unittest.TestCase):
    def setUp(self):
        self.text = visible((REPO / "acquisition" / "index.html").read_text(encoding="utf-8"))

    def test_no_negative_market_inference_and_no_invented_traction(self):
        claims = self.text.replace(check_site.OWNERSHIP_STATEMENT, " ")  # its "not ... endorsed by" is a negation
        for phrase in (r"Nothing on this site indicates", r"has expressed interest", r"no (buyer|institution|company) (has|is)",
                       r"(trusted|used|adopted|endorsed|recognised|recognized) by\b", r"\bbuyers? (have|are)\b",
                       r"\boffers? (received|made)\b", r"\b\d[\d,.]* (visitors|users|pageviews)\b"):
            self.assertNotRegex(claims, r"(?i)" + phrase)
        self.assertIn("no interest from any specific party is implied", self.text)  # the owner's view stays labelled

    def test_established_strengths_lead_and_link_to_their_evidence(self):
        page = (REPO / "acquisition" / "index.html").read_text(encoding="utf-8")
        for href in ('href="/registry/"', 'href="/data/"', 'href="/methodology/"', 'href="/methodology/#m6-h"',
                     'href="/data/evidence.json"', 'href="/registry/questions/"'):
            self.assertIn(href, page)
        self.assertIn("Owner's view of potential (not established)", self.text)
        self.assertIn("Arabic, French and Tamazight editions (planned, not published)", self.text)
        self.assertIn("Price and terms are discussed confidentially", self.text)

    def test_no_weak_or_unsupported_hedging_remains(self):
        self.assertNotIn("may include", self.text)
        self.assertNotIn("subject to verification of rights", self.text)
        self.assertNotIn("logo", self.text.lower())  # only the visual identity that exists on the site is listed


class Rights(unittest.TestCase):
    def test_acquisition_states_third_party_terms_without_promising_them(self):
        text = visible((REPO / "acquisition" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("owned and operated by Sohadot", text)
        self.assertIn("the definitive agreement sets out what is transferred and on what terms", text)
        self.assertIn("source excerpts, which are quotations of their publishers' material", text)
        self.assertIn("SIL Open Font License 1.1", text)
        self.assertNotRegex(text, r"(?i)\b(all rights|unrestricted|free of (any|all) (rights|claims)|full ownership of (all|every))\b")
        self.assertTrue((REPO / "assets" / "fonts" / "OFL.txt").exists())

    def test_reuse_disclosure_for_data_consumers_is_unchanged(self):
        manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["rights"], "No content or data licence has been declared. Source excerpts are quotations of "
                                             "third-party material and remain subject to their publishers' rights.")
        for rel in ("data/index.html", "methodology/index.html"):
            self.assertIn("No content or data licence has been declared", visible((REPO / rel).read_text(encoding="utf-8")), rel)


class Counts(unittest.TestCase):
    def setUp(self):
        self.m = model()
        self.home = (REPO / "index.html").read_text(encoding="utf-8")

    def test_acquisition_figures_match_the_data(self):
        text = visible((REPO / "acquisition" / "index.html").read_text(encoding="utf-8"))
        n_rec, n_ent, n_rel = len(self.m.records), len(self.m.entities), len(self.m.relationships)
        self.assertIn(f"{n_rec} evidence records, {n_ent} entities, {n_rel} relationships", text)
        self.assertIn(f"An evidence registry of {n_rec} sourced records and {n_ent} entities", text)

    def test_domain_figures_overlap_and_the_homepage_says_so(self):
        # Each domain card counts the records behind its entities; a record documenting entities in several domains
        # counts in each. The cards therefore add up to more than the unique records, by exactly the overlap.
        cards = [int(n) for n in re.findall(r'<span class="node-status">(\d+) records?</span>', self.home)]
        owners = {}
        for key in self.m.domains:
            for e in self.m.ontology["entities"]:
                if e.get("domain") == key:
                    for r in e["evidence"]:
                        owners.setdefault(r, set()).add(key)
        self.assertEqual(sum(cards), sum(len(d) for d in owners.values()))
        self.assertEqual(len(owners), len(self.m.records))
        self.assertGreater(sum(cards), len(self.m.records))
        self.assertIn(f"add up to more than the {len(self.m.records)} unique evidence records", visible(self.home))
        self.assertIn(f"<!--r:records-->{len(self.m.records)}<!--/r:records-->", self.home)


class Dates(unittest.TestCase):
    def test_footer_dates_the_data_not_the_build(self):
        with build.rendering(build.RenderContext("en")):
            expected = "Data as of " + build.human_date(model().as_of)
        for path in check_site.site_pages():
            text = visible(path.read_text(encoding="utf-8"))
            if "Registry v" in text and "Owned and operated by Sohadot" in text and path.name == "index.html" \
                    and path.parent != REPO:
                self.assertIn(expected, text, path)
                self.assertNotRegex(text, r"Registry v[\d.]+ · as of", path)


class Tables(unittest.TestCase):
    def test_hint_is_plain_and_only_shown_on_narrow_screens(self):
        for rel in ("acquisition/index.html", "registry/questions/index.html", "registry/matrix/index.html"):
            page = (REPO / rel).read_text(encoding="utf-8")
            hints = re.findall(r'<p class="table-hint">([^<]*)</p>', page)
            self.assertTrue(hints, rel)
            for h in hints:
                self.assertRegex(h, r"^Scroll horizontally to see (both|all( \d+)?) columns\.$", rel)
            for m in re.finditer(r'<div class="table-wrap" role="region" aria-label="[^"]+" tabindex="0">', page):
                pass
            self.assertEqual(len(re.findall(r'class="table-wrap" role="region" aria-label="[^"]+" tabindex="0"', page)), len(hints), rel)
        css = (REPO / "assets" / "registry.css").read_text(encoding="utf-8")
        self.assertIn(".table-hint { display: none; }", css)
        self.assertRegex(css, r"@media \(max-width: 700px\) \{[^}]*\}\s*\.table-hint \{ display: block;|\.table-hint \{ display: block;")


class Determinism(unittest.TestCase):
    def test_two_builds_are_byte_identical_and_match_the_repository(self):
        m = model()
        first, _ = build.build_outputs(m)
        second, _ = build.build_outputs(model())
        self.assertEqual(first, second)
        for rel in ("acquisition/index.html", "index.html", "data/manifest.json", "registry/questions/index.html"):
            self.assertEqual(first[rel], (REPO / rel).read_text(encoding="utf-8"), rel)


DRIVER = r"""
<script>
window.addEventListener("load", () => setTimeout(() => {
  const $ = id => document.getElementById(id), out = {};
  const fill = (f, s, l) => { $("finding").value = f; $("source").value = s; $("limits").value = l; };
  document.querySelector('[data-mode="specialist"]').click();
  out.start = $("eval-progress").textContent;
  fill("F1", "MAI-EV-0001", "L1");
  $("eval-next").click();
  out.focusAfterNext = document.activeElement && document.activeElement.id;
  fill("F2", "MAI-EV-0011", "L2");
  $("eval-next").click();
  out.third = $("eval-progress").textContent;
  out.nextHiddenOnLast = $("eval-next").hidden;
  out.prevVisibleOnLast = !$("eval-prev").hidden;
  fill("F3", "GAP-03", "L3");
  document.querySelector('input[name="difficulty"][value="Difficult"]').checked = true;
  $("eval-prev").click();
  out.backTo = $("eval-progress").textContent;
  out.restored = $("finding").value + "|" + $("source").value;
  $("eval-next").click();
  out.restored3 = $("finding").value + "|" + document.querySelector('input[name="difficulty"]:checked')?.value;
  document.querySelector('[data-mode="intro"]').click();
  out.intro = $("eval-progress").textContent + "|" + $("eval-prev").hidden + "|" + $("eval-next").hidden;
  document.querySelector('[data-mode="specialist"]').click();
  out.keptAfterSwitch = $("finding").value;
  $("eval-copy").click();
  out.report = $("eval-report").value;
  $("eval-clear").click();
  out.cleared = [$("eval-report").value, $("finding").value, $("eval-progress").textContent, $("eval-prev").hidden].join("|");
  out.headingFocusable = $("eval-task").tabIndex;
  const pre = document.createElement("pre"); pre.id = "eval-probe"; pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
}, 300));
</script>"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class EvaluationPrivacy(unittest.TestCase):
    def test_script_makes_no_network_or_storage_calls(self):
        js = (REPO / "assets" / "evaluation.js").read_text(encoding="utf-8")
        for api in ("fetch(", "XMLHttpRequest", "sendBeacon", "localStorage", "sessionStorage", "indexedDB", "WebSocket",
                    "document.cookie", "navigator.clipboard", ".submit("):
            self.assertNotIn(api, js)
        self.assertEqual(len(re.findall(r'^\s+"', js[js.index("specialist: ["):js.index("]", js.index("specialist: ["))], re.M)), 3)
        page = (REPO / "evaluation" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<h2 id="eval-task" tabindex="-1">', page)
        self.assertIn('id="eval-prev" hidden', page)
        self.assertIn("Three evidence interpretation tasks", page)


@unittest.skipUnless(BROWSER, "no Chromium or Chrome binary found")
class EvaluationInTheBrowser(unittest.TestCase):
    def test_all_three_specialist_tasks_can_be_completed_reviewed_reported_and_cleared(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        shutil.copytree(REPO / "assets", tmp / "assets", ignore=shutil.ignore_patterns("*.woff2"))
        (tmp / "evaluation").mkdir()
        page = (REPO / "evaluation" / "index.html").read_text(encoding="utf-8")
        (tmp / "evaluation" / "index.html").write_text(page.replace("</body>", DRIVER + "</body>"), encoding="utf-8")
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(tmp)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_address[1]}/evaluation/"
        out = subprocess.run([BROWSER, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=4000",
                              "--dump-dom", url], capture_output=True, text=True, timeout=60)
        m = re.search(r'<pre id="eval-probe">(.*?)</pre>', out.stdout, re.S)
        self.assertTrue(m, out.stderr[-500:])
        r = json.loads(html.unescape(m.group(1)))
        self.assertEqual(r["start"], "Specialist · Task 1 of 3")
        self.assertEqual(r["focusAfterNext"], "eval-task")
        self.assertEqual(r["third"], "Specialist · Task 3 of 3")
        self.assertTrue(r["nextHiddenOnLast"])
        self.assertTrue(r["prevVisibleOnLast"])
        self.assertEqual(r["backTo"], "Specialist · Task 2 of 3")
        self.assertEqual(r["restored"], "F2|MAI-EV-0011")
        self.assertEqual(r["restored3"], "F3|Difficult")
        self.assertEqual(r["intro"], "Introductory · Task 1 of 1|true|true")
        self.assertEqual(r["keptAfterSwitch"], "F1")
        for n, (f, s, l) in enumerate((("F1", "MAI-EV-0001", "L1"), ("F2", "MAI-EV-0011", "L2"), ("F3", "GAP-03", "L3")), 1):
            self.assertIn(f"Task {n}: ", r["report"])
            self.assertIn(f"Finding: {f}\nEvidence: {s}\nLimitations: {l}", r["report"])
        self.assertIn("Difficulty: Difficult", r["report"])
        self.assertIn("Voluntary participant observations; not independently validated.", r["report"])
        self.assertEqual(r["cleared"], "||Specialist · Task 1 of 3|true")
        self.assertEqual(r["headingFocusable"], -1)


if __name__ == "__main__":
    unittest.main()
