"""Re-check evidence sources against their recorded excerpts. Network access; never run by the site build.

    python3 tools/check_sources.py                    check every record, print a JSON report
    python3 tools/check_sources.py --ids MAI-EV-0020  check selected records
    python3 tools/check_sources.py --out report.json --baseline previous.json
    python3 tools/check_sources.py --strict           exit 1 unless every excerpt matched

For each record the report separates what can be checked mechanically: whether the URL was
reachable, whether content was retrieved or blocked (login, bot challenge, rate limit) or refused
with an HTTP error, where redirects led, how many excerpts matched (in visible text, raw source or
the page's own same-host scripts), and whether the content hash changed since a baseline report.
None of this authenticates the publisher or shows a claim is still true: a quotation can match a
page whose claim is outdated. Claim support always needs a person and is reported as "manual".
The tool only reads; a failed or blocked fetch never alters or removes a record, and its report is
never written into data/.
Standard library only (plus `pdftotext`, if installed, for PDF sources).
"""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402

USER_AGENT = "TheMoroccoAI-source-check/1.0 (+https://themoroccoai.com/registry/)"
TIMEOUT = 30
DELAY_PER_HOST = 2.0  # seconds between requests to the same host
MAX_BYTES = 25_000_000  # larger responses are truncated and reported
MAX_SCRIPTS = 3  # same-host scripts read for a single-page application, when excerpts are missing
CHALLENGE = re.compile(r"just a moment|cf-chl|captcha|access denied|accès refusé|please log in|must have access|"
                       r"client challenge|enable javascript to proceed", re.I)


class _Visible(HTMLParser):
    SKIP = {"script", "style", "noscript", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.depth = [], 0

    def handle_starttag(self, tag, attrs):
        self.depth += tag in self.SKIP

    def handle_endtag(self, tag):
        self.depth -= tag in self.SKIP

    def handle_data(self, data):
        if self.depth <= 0:
            self.parts.append(data)


def fold(text):
    text = unicodedata.normalize("NFKC", html.unescape(text))
    text = text.translate({0x2019: "'", 0x2018: "'", 0x201C: '"', 0x201D: '"', 0xA0: " ", 0x202F: " ", 0xAD: None})
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _charset(content_type):
    m = re.search(r"charset=([\w.-]+)", content_type or "", re.I)
    return m.group(1) if m else "utf-8"


def _decode(body, content_type):
    try:
        return body.decode(_charset(content_type), "replace")
    except LookupError:
        return body.decode("utf-8", "replace")


def texts_from(body, content_type):
    """Return (visible text, raw source) for matching, or (None, None) if the format can't be read here."""
    if body[:4] == b"%PDF" or "pdf" in content_type:
        if not shutil.which("pdftotext"):
            return None, None
        out = subprocess.run(["pdftotext", "-", "-"], input=body, capture_output=True, timeout=60).stdout
        text = out.decode("utf-8", "ignore")
        return text, text
    raw = _decode(body, content_type)
    p = _Visible()
    p.feed(raw)
    return " ".join(p.parts), raw


def match_excerpts(visible, raw, excerpts):
    v, r = fold(visible), fold(raw)
    results = []
    for e in excerpts:
        f = fold(e)
        results.append("visible" if f in v else "raw-source" if f in r else "missing")
    return results


def classify(status, body, content_type, error=None):
    """Mechanical outcome of one fetch, before any excerpt matching."""
    if error is not None:
        return "unreachable"
    if status in (401, 403, 407, 429) or (status == 200 and len(body) < 20000 and CHALLENGE.search(body[:20000].decode("utf-8", "ignore"))):
        return "blocked"
    if status != 200:
        return "http-error"
    return "retrieved"


def fetch(url):
    """Return (status, body, content type, error, final URL after redirects)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read(MAX_BYTES + 1), resp.headers.get("Content-Type", ""), None, resp.geturl()
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_BYTES) if exc.fp else b""
        return exc.code, body, exc.headers.get("Content-Type", "") if exc.headers else "", None, exc.geturl() or url
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, b"", "", str(exc), url


def _host(url):
    return urlparse(url).netloc.lower().removeprefix("www.")


def _same_host_scripts(raw, page_url):
    host = urlparse(page_url).netloc
    srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", raw, re.I)
    urls = [urljoin(page_url, x) for x in srcs]
    return [u for u in dict.fromkeys(urls) if urlparse(u).netloc == host and urlparse(u).scheme == "https"][:MAX_SCRIPTS]


def check_record(record, fetcher=fetch, baseline=None):
    res = fetcher(record["source_url"])
    status, body, ctype, error = res[:4]
    final = res[4] if len(res) > 4 and res[4] else record["source_url"]
    outcome = classify(status, body, ctype, error)
    entry = {"evidence_id": record["evidence_id"], "url": record["source_url"], "http_status": status,
             "fetch": outcome, "claim_check": "manual"}
    if record.get("superseded_by"):
        entry["superseded_by"] = record["superseded_by"]  # a matching quotation here does not make the claim current
    if final != record["source_url"]:
        entry["final_url"] = final
    off_host = _host(final) != _host(record["source_url"])
    if error:
        entry["error"] = error
    if len(body) > MAX_BYTES:
        body, entry["truncated"] = body[:MAX_BYTES], True
    if outcome != "retrieved":
        entry["result"] = "not-checked: " + outcome + " (record kept unchanged)"
        return entry
    entry["content_sha256"] = hashlib.sha256(body).hexdigest()
    if baseline and baseline.get("content_sha256"):
        entry["changed_since_baseline"] = baseline["content_sha256"] != entry["content_sha256"]
    visible, raw = texts_from(body, ctype)
    if visible is None:
        entry["result"] = "manual review: format not readable here"
        return entry
    matches = match_excerpts(visible, raw, record["source_excerpts"])
    if "missing" in matches and visible is not raw:  # HTML page (for PDFs both texts are the same object)
        scripts = []
        for u in _same_host_scripts(raw, final):
            s_status, s_body, s_ctype, s_error = fetcher(u)[:4]
            if s_status == 200 and not s_error:
                scripts.append(_decode(s_body[:MAX_BYTES], s_ctype))
        if scripts:
            folded = fold(" ".join(scripts))
            matches = ["page-script" if m == "missing" and fold(x) in folded else m
                       for m, x in zip(matches, record["source_excerpts"])]
    entry["excerpts"] = matches
    found = sum(m != "missing" for m in matches)
    if off_host:
        entry["result"] = "manual review: redirected to another host; the publisher must be re-established"
    elif found == len(matches):
        entry["result"] = "all excerpts matched"
    elif found:
        entry["result"] = "manual review: some excerpts missing (source may have changed)"
    else:
        entry["result"] = "manual review: no excerpt found (source changed or moved)"
    return entry


def run(records, fetcher=fetch, baseline=None, sleep=time.sleep):
    """Check records in order, at most one request per URL per run, spaced per host."""
    report, last, cache = [], {}, {}
    prior = {e["evidence_id"]: e for e in (baseline or [])}

    def polite(url):
        if url not in cache:
            host = urlparse(url).netloc
            if host in last:
                wait = DELAY_PER_HOST - (time.monotonic() - last[host])
                if wait > 0:
                    sleep(wait)
            cache[url] = fetcher(url)
            last[host] = time.monotonic()
        return cache[url]

    for r in records:
        report.append(check_record(r, polite, prior.get(r["evidence_id"])))
    return report


def _safe_out(path):
    """Refuse to write a report over the registry's own data or code."""
    target = Path(path).resolve()
    root = registry.ROOT.resolve()
    if target.suffix != ".json" or target.is_relative_to(root / "data") or target.is_relative_to(root / "tools"):
        raise SystemExit(f"refusing to write the report to {path}: choose a .json path outside data/ and tools/")
    return target


def main(argv):
    evidence, _ = registry.load_all()
    records = evidence["records"]
    if "--ids" in argv:
        wanted = set(argv[argv.index("--ids") + 1].split(","))
        records = [r for r in records if r["evidence_id"] in wanted]
    baseline = json.loads(Path(argv[argv.index("--baseline") + 1]).read_text()) if "--baseline" in argv else None
    out = _safe_out(argv[argv.index("--out") + 1]) if "--out" in argv else None
    report = run(records, baseline=baseline)
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if out:
        out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    summary = {}
    for e in report:
        summary[e["result"].split(":")[0]] = summary.get(e["result"].split(":")[0], 0) + 1
    print(json.dumps(summary), file=sys.stderr)
    if "--strict" in argv and any(e["result"] != "all excerpts matched" for e in report):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
