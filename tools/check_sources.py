"""Re-check evidence sources against their recorded excerpts. Network access; never run by the site build.

    python3 tools/check_sources.py                    check every record, print a JSON report
    python3 tools/check_sources.py --ids MAI-EV-0020  check selected records
    python3 tools/check_sources.py --out report.json --baseline previous.json
    python3 tools/check_sources.py --strict           exit 1 unless every excerpt matched

For each record the report separates what can be checked mechanically: whether the URL was
reachable, whether content was retrieved or blocked (login, bot challenge, rate limit), how many
excerpts matched (in visible text or raw source), and whether the content hash changed since a
baseline report. Whether the claim is still supported always needs a person and is reported as
"manual". The tool only reads; a failed or blocked fetch never alters or removes a record.
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
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402

USER_AGENT = "TheMoroccoAI-source-check/1.0 (+https://themoroccoai.com/registry/)"
TIMEOUT = 30
DELAY_PER_HOST = 2.0  # seconds between requests to the same host
CHALLENGE = re.compile(r"just a moment|cf-chl|captcha|access denied|accès refusé|please log in|must have access", re.I)


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


def texts_from(body, content_type):
    """Return (visible text, raw source) for matching, or (None, None) if the format can't be read here."""
    if body[:4] == b"%PDF" or "pdf" in content_type:
        if not shutil.which("pdftotext"):
            return None, None
        out = subprocess.run(["pdftotext", "-", "-"], input=body, capture_output=True, timeout=60).stdout
        text = out.decode("utf-8", "ignore")
        return text, text
    raw = body.decode("utf-8", "ignore")
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
        return "unreachable"
    return "retrieved"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", ""), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() if exc.fp else b"", exc.headers.get("Content-Type", "") if exc.headers else "", None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, b"", "", str(exc)


def check_record(record, fetcher=fetch, baseline=None):
    status, body, ctype, error = fetcher(record["source_url"])
    outcome = classify(status, body, ctype, error)
    entry = {"evidence_id": record["evidence_id"], "url": record["source_url"], "http_status": status,
             "fetch": outcome, "claim_check": "manual"}
    if error:
        entry["error"] = error
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
    entry["excerpts"] = matches
    found = sum(m != "missing" for m in matches)
    if found == len(matches):
        entry["result"] = "all excerpts matched"
    elif found:
        entry["result"] = "manual review: some excerpts missing (source may have changed)"
    else:
        entry["result"] = "manual review: no excerpt found (source changed or moved)"
    return entry


def run(records, fetcher=fetch, baseline=None, sleep=time.sleep):
    report, last = [], {}
    prior = {e["evidence_id"]: e for e in (baseline or [])}
    for r in records:
        host = urlparse(r["source_url"]).netloc
        if host in last and fetcher is fetch:
            wait = DELAY_PER_HOST - (time.monotonic() - last[host])
            if wait > 0:
                sleep(wait)
        report.append(check_record(r, fetcher, prior.get(r["evidence_id"])))
        last[host] = time.monotonic()
    return report


def main(argv):
    evidence, _ = registry.load_all()
    records = evidence["records"]
    if "--ids" in argv:
        wanted = set(argv[argv.index("--ids") + 1].split(","))
        records = [r for r in records if r["evidence_id"] in wanted]
    baseline = json.loads(Path(argv[argv.index("--baseline") + 1]).read_text()) if "--baseline" in argv else None
    report = run(records, baseline=baseline)
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if "--out" in argv:
        Path(argv[argv.index("--out") + 1]).write_text(text + "\n", encoding="utf-8")
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
