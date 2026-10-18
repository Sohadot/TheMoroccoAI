"""Static quality gates for the published site.

    python3 tools/check_site.py            all offline checks
    python3 tools/check_site.py --network  also resolve the acquisition contact's MX record

Checks internal links and anchors, third-party resource loading, page metadata and
canonical URLs, basic accessibility rules, the sitemap, the acquisition contact path,
independence wording, and that no confidential commercial terms or credentials are
committed. Standard library only.
"""
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://themoroccoai.com"
CONTACT = "agent@sohadot.com"
DISCLAIMER = "Not affiliated with the Government of Morocco"
SKIP_DIRS = {".git", "node_modules", "tests"}
# Phrases that must not appear on public pages: commercial terms that belong in private
# negotiation, and self-descriptions that could read as official status.
FORBIDDEN_PAGE_TEXT = [
    (re.compile(r"\b(minimum|reserve|asking|floor)\s+price\b", re.I), "pricing terms"),
    (re.compile(r"\bvaluation\b", re.I), "valuation"),
    (re.compile(r"\b(USD|EUR|MAD|\$|€)\s?\d[\d,.]*\s?(k|m|million)?\s*(offer|price)\b", re.I), "price figure"),
    (re.compile(r"sovereign reference infrastructure", re.I), "'sovereign' self-description (implies official status)"),
    (re.compile(r"\bofficial (platform|portal|website) of\b", re.I), "official-status claim"),
]
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".md", ".txt", ".xml", ".py", ".yml", ".yaml", ".svg"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.dup_ids = set(), set()
        self.links, self.resources, self.headings, self.imgs_no_alt = [], [], [], 0
        self.meta, self.canonical, self.lang, self.title = {}, None, None, ""
        self.h1, self.svgs_unlabelled, self.empty_links, self.styles = 0, 0, [], []
        self.text = []
        self._in_title = self._in_style = False
        self._link_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            (self.dup_ids if a["id"] in self.ids else self.ids).add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "style":
            self._in_style = True
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            if rel == "canonical":
                self.canonical = a.get("href")
            else:
                self.resources.append((f"link[{rel}]", a.get("href", "")))
        elif tag in ("script", "img", "iframe", "source", "video", "audio", "embed"):
            if a.get("src"):
                self.resources.append((tag, a["src"]))
            if tag == "img" and a.get("alt") is None:
                self.imgs_no_alt += 1
        elif tag == "a":
            self.links.append(a.get("href"))
            self._link_stack.append([a.get("href"), a.get("aria-label", ""), ""])
        elif tag == "svg":
            if a.get("aria-hidden") != "true" and not a.get("aria-label") and a.get("role") != "img":
                self.svgs_unlabelled += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
            if tag == "h1":
                self.h1 += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "style":
            self._in_style = False
        elif tag == "a" and self._link_stack:
            href, label, text = self._link_stack.pop()
            if not (label.strip() or text.strip()):
                self.empty_links.append(href)

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_style:
            self.styles.append(data)
        elif not self._in_title:
            self.text.append(data)
        for item in self._link_stack:
            item[2] += data


def site_pages():
    return sorted(p for p in ROOT.rglob("*.html") if not SKIP_DIRS & set(p.relative_to(ROOT).parts))


def url_path(file):
    rel = file.relative_to(ROOT).as_posix()
    return "/" + rel[: -len("index.html")] if rel.endswith("index.html") else "/" + rel


def resolve(base_file, href):
    """Map an internal href to (file, fragment), or None for external/non-file links."""
    parsed = urlparse(href)
    if parsed.scheme or href.startswith("//"):
        if parsed.netloc in ("themoroccoai.com", "www.themoroccoai.com"):
            parsed = urlparse(parsed.path + ("#" + parsed.fragment if parsed.fragment else ""))
        else:
            return None
    path = parsed.path
    if not path:
        target = base_file
    elif path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = (base_file.parent / path).resolve()
    if target.is_dir() or path.endswith("/"):
        target = target / "index.html"
    return target, parsed.fragment


def check(network=False):
    errors = []
    parsed = {}
    for f in site_pages():
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        parsed[f] = p

    for f, p in parsed.items():
        where = f.relative_to(ROOT).as_posix()
        path = url_path(f)
        # metadata
        if not p.title.strip():
            errors.append(f"{where}: missing <title>")
        desc = p.meta.get("description", "")
        if not 50 <= len(desc) <= 300:
            errors.append(f"{where}: meta description missing or not 50–300 characters ({len(desc)})")
        if p.canonical != SITE + path:
            errors.append(f"{where}: canonical {p.canonical!r} should be {SITE + path!r}")
        if p.meta.get("og:url") != SITE + path:
            errors.append(f"{where}: og:url does not match canonical")
        if "width=device-width" not in p.meta.get("viewport", ""):
            errors.append(f"{where}: missing responsive viewport meta")
        if not p.lang:
            errors.append(f"{where}: <html> has no lang attribute")
        # accessibility basics
        if p.h1 != 1:
            errors.append(f"{where}: expected exactly one <h1>, found {p.h1}")
        for prev, cur in zip(p.headings, p.headings[1:]):
            if cur > prev + 1:
                errors.append(f"{where}: heading level skips from h{prev} to h{cur}")
                break
        if p.imgs_no_alt:
            errors.append(f"{where}: {p.imgs_no_alt} <img> without alt")
        if p.svgs_unlabelled:
            errors.append(f"{where}: {p.svgs_unlabelled} <svg> neither labelled nor aria-hidden")
        if p.dup_ids:
            errors.append(f"{where}: duplicate ids {sorted(p.dup_ids)}")
        for href in p.empty_links:
            errors.append(f"{where}: link without accessible text ({href})")
        # independence wording
        text = " ".join(p.text)
        if DISCLAIMER.lower() not in re.sub(r"\s+", " ", text).lower():
            errors.append(f"{where}: missing independence disclaimer '{DISCLAIMER}'")
        for pattern, label in FORBIDDEN_PAGE_TEXT:
            m = pattern.search(text)
            if m:
                errors.append(f"{where}: forbidden public text ({label}): {m.group(0)!r}")
        # third-party resources: the page must load everything from this origin
        for kind, src in p.resources:
            u = urlparse(src)
            if u.scheme in ("http", "https") or src.startswith("//"):
                if u.netloc not in ("themoroccoai.com", "www.themoroccoai.com"):
                    errors.append(f"{where}: loads third-party resource {kind} {src}")
        for css in p.styles:
            for m in re.finditer(r"(?:url\(|@import\s+)['\"]?(https?:)?//", css):
                errors.append(f"{where}: inline CSS references a third-party URL")
        # internal links and anchors
        for href in p.links:
            if href is None or href.strip() in ("", "#"):
                errors.append(f"{where}: placeholder link href={href!r}")
                continue
            if href.startswith(("mailto:", "tel:")):
                continue
            r = resolve(f, href)
            if r is None:
                continue
            target, frag = r
            if not target.exists():
                errors.append(f"{where}: broken internal link {href}")
            elif frag and target.suffix == ".html":
                tp = parsed.get(target)
                if tp is None or frag not in tp.ids:
                    errors.append(f"{where}: link {href} points to a missing anchor")
        for kind, src in p.resources:
            if src and not urlparse(src).scheme and not src.startswith(("data:", "//")):
                r = resolve(f, src)
                if r and not r[0].exists():
                    errors.append(f"{where}: missing local resource {src}")

    for css in ROOT.rglob("*.css"):
        if SKIP_DIRS & set(css.relative_to(ROOT).parts):
            continue
        body = css.read_text(encoding="utf-8")
        if re.search(r"(?:url\(|@import\s+)['\"]?(https?:)?//", body):
            errors.append(f"{css.relative_to(ROOT)}: references a third-party URL")
        for m in re.finditer(r"url\(['\"]?([^'\")]+)['\"]?\)", body):
            if not m.group(1).startswith("data:") and not (css.parent / m.group(1)).exists():
                errors.append(f"{css.relative_to(ROOT)}: missing file {m.group(1)}")

    errors += check_sitemap(parsed)
    errors += check_contact(parsed, network)
    errors += check_secrets()
    return errors


def check_sitemap(parsed):
    errors = []
    sm = ROOT / "sitemap.xml"
    robots = ROOT / "robots.txt"
    if not robots.exists() or f"Sitemap: {SITE}/sitemap.xml" not in robots.read_text():
        errors.append("robots.txt: missing or does not reference the sitemap")
    if not sm.exists():
        return errors + ["sitemap.xml: missing"]
    locs = re.findall(r"<loc>([^<]+)</loc>", sm.read_text())
    if len(locs) != len(set(locs)):
        errors.append("sitemap.xml: duplicate URLs")
    listed = set()
    for loc in locs:
        if not loc.startswith(SITE + "/"):
            errors.append(f"sitemap.xml: {loc} is not on {SITE}")
            continue
        target = ROOT / loc[len(SITE) + 1:]
        target = target / "index.html" if loc.endswith("/") else target
        if not target.exists():
            errors.append(f"sitemap.xml: {loc} has no file")
        listed.add(target)
    for f in parsed:
        if f not in listed and f.name != "404.html":
            errors.append(f"sitemap.xml: {f.relative_to(ROOT)} is not listed")
    return errors


def check_contact(parsed, network):
    errors = []
    home = parsed.get(ROOT / "index.html")
    if home is None:
        return ["index.html: missing"]
    if "acquire" not in home.ids:
        errors.append("index.html: no #acquire section")
    mailtos = {urlparse(h).path for p in parsed.values() for h in p.links if h and h.startswith("mailto:")}
    if CONTACT not in {urlparse(h).path for h in home.links if h and h.startswith("mailto:")}:
        errors.append(f"index.html: no mailto link to the acquisition contact {CONTACT}")
    for addr in mailtos - {CONTACT}:
        errors.append(f"unexpected mailto address {addr}; all contact links must use {CONTACT}")
    if network:
        domain = CONTACT.split("@", 1)[1]
        try:
            with urllib.request.urlopen(f"https://dns.google/resolve?name={domain}&type=MX", timeout=20) as r:
                answer = json.load(r).get("Answer") or []
            if not [a for a in answer if a.get("type") == 15]:
                errors.append(f"contact domain {domain} has no MX record; mail cannot be delivered")
        except OSError as exc:
            errors.append(f"could not resolve MX for {domain}: {exc}")
    return errors


def check_secrets():
    errors = []
    for f in ROOT.rglob("*"):
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES or SKIP_DIRS & set(f.relative_to(ROOT).parts):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{f.relative_to(ROOT)}: looks like a committed credential ({pattern.pattern[:20]}…)")
    return errors


if __name__ == "__main__":
    problems = check(network="--network" in sys.argv)
    for p in problems:
        print("ERROR", p)
    print(f"{len(site_pages())} pages checked, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
