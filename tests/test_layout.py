"""Rendered layout at narrow widths with the web fonts blocked.

Fallback fonts are wider than the self-hosted ones, so content that fits once the fonts load can push
a card past the screen edge while they load, or for good when a visitor's browser blocks them. These
tests render pages in headless Chromium from a copy of the site that has no font files, and fail if any
element outside a scrollable region extends past the viewport. They need a Chromium or Chrome binary
(CHROME_BIN, Playwright's Chromium or one on PATH; GitHub's Ubuntu runners include Chrome) and skip
without one.
"""
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WIDTHS = (320, 375)
# Pages that carry evidence cards, wide tables or long identifiers.
PAGES = ("registry/evidence/", "registry/idarati-ai/", "registry/sovereign-ai-marketplace/",
         "registry/ministry-digital-transition/", "registry/questions/", "registry/matrix/", "registry/gaps/",
         "registry/jazari-root/", "registry/toubkal-supercomputer/", "registry/nexus-ai-factory/", "data/", "")

PROBE = """<script>
addEventListener('load', () => setTimeout(() => {
  const scrolls = e => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      if (/(auto|scroll)/.test(getComputedStyle(p).overflowX)) return true; } return false; };
  const W = document.documentElement.clientWidth, out = [];
  for (const e of document.body.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width && r.right > W + 0.5 && !scrolls(e)) out.push(e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className ? '.' + e.className : ''));
  }
  const loaded = [...document.fonts].filter(f => f.status === 'loaded').length;
  const pre = document.createElement('pre'); pre.id = 'layout-probe';
  pre.textContent = JSON.stringify({width: W, loaded_fonts: loaded, overflowing: out.slice(0, 5), count: out.length});
  parent.document.body.appendChild(pre);
}, 300));
</script>"""


def find_browser():
    candidates = [os.environ.get("CHROME_BIN"), "/opt/pw-browsers/chromium"]
    candidates += [shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")]
    return next((c for c in candidates if c and os.access(c, os.X_OK)), None)


BROWSER = find_browser()
TMP = None


def site_without_fonts(dest, pages):
    """A copy of the pages and stylesheets with the probe injected and no font files."""
    shutil.copytree(REPO / "assets", dest / "assets", ignore=shutil.ignore_patterns("*.woff2"))
    for p in pages:
        html = (REPO / p / "index.html").read_text(encoding="utf-8")
        (dest / p).mkdir(parents=True, exist_ok=True)
        (dest / p / "index.html").write_text(html.replace("</body>", PROBE + "</body>"), encoding="utf-8")


def render(base, page, width):
    # Headless windows have a minimum width, so the page is rendered in an iframe of the exact width:
    # media queries and layout follow the iframe's viewport. The probe writes its result into the host page.
    host = f"frame-{width}-{page.strip('/').replace('/', '-') or 'home'}.html"
    (TMP / host).write_text(f'<!DOCTYPE html><html><body style="margin:0"><iframe src="/{page}" '
                            f'style="border:0;width:{width}px;height:800px"></iframe></body></html>', encoding="utf-8")
    out = subprocess.run([BROWSER, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                          "--window-size=800,900", "--virtual-time-budget=4000", "--dump-dom", base + host],
                         capture_output=True, text=True, timeout=60)
    m = re.search(r'<pre id="layout-probe">(.*?)</pre>', out.stdout, re.S)
    if not m:
        raise AssertionError(f"no layout result for /{page}: {out.stderr[-500:]}")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(BROWSER, "no Chromium or Chrome binary found")
class NarrowLayoutWithoutWebFonts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global TMP
        cls.tmp = TMP = Path(tempfile.mkdtemp())
        site_without_fonts(cls.tmp, PAGES)
        handler = functools.partial(QuietHandler, directory=str(cls.tmp))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        shutil.rmtree(cls.tmp)

    def test_nothing_extends_past_the_screen(self):
        for width in WIDTHS:
            for p in PAGES:
                with self.subTest(page="/" + p, width=width):
                    r = render(self.base, p, width)
                    self.assertEqual(r["width"], width, "the browser did not apply the requested viewport")
                    self.assertEqual(r["loaded_fonts"], 0, "web fonts were not blocked")
                    self.assertEqual(r["count"], 0, f"elements past the right edge: {r['overflowing']}")

    def test_the_probe_detects_overflow(self):
        # The check must be able to fail: a card holding one long unbroken token without the wrapping rule.
        page = self.tmp / "probe-check"
        page.mkdir(exist_ok=True)
        css = (self.tmp / "assets" / "registry.css").read_text(encoding="utf-8")
        (page / "index.html").write_text(
            '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f'<style>{css} .evidence-card {{ overflow-wrap: normal !important; min-width: auto !important; }}</style></head>'
            '<body><main class="page"><ul class="evidence-list"><li class="evidence-card"><p>'
            + "x" * 80 + "</p></li></ul></main>" + PROBE + "</body></html>", encoding="utf-8")
        self.assertGreater(render(self.base, "probe-check/", 375)["count"], 0)


if __name__ == "__main__":
    unittest.main()
