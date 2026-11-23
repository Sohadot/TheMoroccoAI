"""Source intelligence: watch cited sources, detect meaningful changes, stage candidates for human review.

    python3 tools/observatory.py validate                       check sources/watchlist.json against the registry
    python3 tools/observatory.py observe [--source SRC-001]     retrieve active sources (robots.txt honoured)
    python3 tools/observatory.py report                         what changed, what needs review, what is unreliable
    python3 tools/observatory.py candidates                     list staged candidates and their states
    python3 tools/observatory.py review CAND-ID --to STATE --by REVIEWER --note "why"
    python3 tools/observatory.py propose CAND-ID --decision decision.json   draft an evidence record for a person to admit

Three different things are kept apart:
  1. a source page changed                      -> an observation and a comparison (this tool)
  2. a claim about the world may have changed   -> a candidate, reviewed by a person (this tool, staging only)
  3. the registry admitted verified knowledge   -> a commit to data/ by a person; tools/changes.py then shows it

Nothing here writes to data/ or to the published site. Observations, candidates and review notes live in a staging
directory OUTSIDE the public repository ($THEMOROCCOAI_OBSERVATORY, default ~/.themoroccoai-observatory); every file
there carries a marker that tools/check_site.py rejects if it ever appears in the repository. Retrieval reuses
tools/check_sources.py (fetch, block and error classification, text matching), checks robots.txt first, waits between
requests to a host, and never bypasses a login, paywall or challenge. A failed retrieval is never a disappearance.
Standard library only.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_sources  # noqa: E402
import registry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / "sources" / "watchlist.json"
STAGING_MARKER = "themoroccoai-" + "observatory-staging"  # assembled so this file does not carry it
SCHEMA_VERSION = "1.0"
SOURCE_ID = re.compile(r"^SRC-\d{3}$")
STATUSES = ("active", "paused", "retired")
FREQUENCIES = ("daily", "weekly", "monthly", "quarterly")
OUTCOMES = ("retrieved", "blocked", "http-error", "unreachable", "robots-disallowed", "unreadable-format")
UNRELIABLE_AFTER = 3  # consecutive failed observations before a source is reported as unreliable

# Review workflow. States describe where a candidate is in review, never whether its claim is true.
STATES = ("detected", "awaiting_review", "under_verification", "needs_additional_evidence", "accepted_for_admission",
          "rejected", "duplicate", "deferred")
TRANSITIONS = {
    "detected": {"awaiting_review", "duplicate"},
    "awaiting_review": {"under_verification", "rejected", "duplicate", "deferred"},
    "under_verification": {"needs_additional_evidence", "accepted_for_admission", "rejected", "duplicate", "deferred"},
    "needs_additional_evidence": {"under_verification", "rejected", "deferred"},
    "deferred": {"awaiting_review"},
    "accepted_for_admission": set(),
    "rejected": set(),
    "duplicate": set(),
}
AUTOMATED_ACTOR = "observatory"
AUTOMATED_TRANSITIONS = {("detected", "awaiting_review"), ("detected", "duplicate")}
AUTOMATED_ID = re.compile(r"(?:^|-)(?:ai|bot|ci|claude|gpt|llm|machine|auto|automated|assistant|model|pipeline|script|observatory)(?:-|$)")
REVIEWER_ID = re.compile(r"^[a-z][a-z0-9-]{2,40}$")

AI_TERMS = re.compile(r"(?i)\b(artificial intelligence|intelligence artificielle|machine learning|apprentissage automatique|"
                      r"deep learning|large language model|LLM|generative|g[ée]n[ée]rati[fv]e?|chatbot|agentic|IA|AI|GPU|"
                      r"supercomput\w*|data ?cent(?:re|er)s?|datacenters?)\b|الذكاء الاصطناعي|ذكاء اصطناعي|تعلم آلي")
VOLATILE = [
    (re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"), "<time>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?\b"), "<timestamp>"),
    (re.compile(r"\b[0-9a-f]{16,}\b", re.I), "<token>"),
    (re.compile(r"(?i)(©|\(c\)|copyright)\s*\d{4}(?:\s*[-–]\s*\d{4})?"), "© <year>"),
]
BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "dt", "dd", "div", "section", "article", "header",
              "footer", "br", "tr", "blockquote", "pre", "figcaption", "caption", "title", "option", "button", "label", "a"}
SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}


class StagingError(Exception):
    pass


# ─── Watchlist ────────────────────────────────────────────────────────────

def load_watchlist(path=WATCHLIST):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_watchlist(watchlist, evidence, ontology):
    """Every source is a cited source: its URL is the source_url of each record it lists. Inclusion in the
    watchlist is never a statement about the publisher."""
    errors, seen_ids, seen_urls = [], set(), set()
    records = {r["evidence_id"]: r for r in evidence["records"]}
    entities = {e["id"] for e in ontology["entities"]}
    if watchlist.get("schema_version") != SCHEMA_VERSION or not isinstance(watchlist.get("sources"), list):
        return [f"sources/watchlist.json: needs schema_version {SCHEMA_VERSION} and a 'sources' list"]
    allowed = {"id", "slug", "name", "url", "category", "language", "relevance", "records", "entities", "method",
               "frequency", "access", "status", "status_reason", "added", "ignore_patterns"}
    for s in watchlist["sources"]:
        where = f"sources/watchlist.json {s.get('id')!r}"
        if not isinstance(s.get("id"), str) or not SOURCE_ID.match(s["id"]):
            errors.append(f"{where}: id must look like SRC-001")
        if s.get("id") in seen_ids:
            errors.append(f"{where}: duplicate id (ids are never reused)")
        seen_ids.add(s.get("id"))
        if s.get("url") in seen_urls:
            errors.append(f"{where}: duplicate URL")
        seen_urls.add(s.get("url"))
        if set(s) - allowed:
            errors.append(f"{where}: unexpected fields {sorted(set(s) - allowed)}")
        if not str(s.get("url", "")).startswith("https://"):
            errors.append(f"{where}: url must be https")
        if s.get("category") not in registry.SOURCE_TYPES:
            errors.append(f"{where}: category must be a registry source type")
        if s.get("language") not in ("ar", "fr", "en", "zgh", "ary"):
            errors.append(f"{where}: unknown language")
        if s.get("status") not in STATUSES:
            errors.append(f"{where}: status must be one of {list(STATUSES)}")
        if s.get("status") in ("paused", "retired") and not s.get("status_reason"):
            errors.append(f"{where}: a {s.get('status')} source needs a status_reason")
        if s.get("frequency") not in FREQUENCIES:
            errors.append(f"{where}: frequency must be one of {list(FREQUENCIES)}")
        if s.get("method") != "http-get":
            errors.append(f"{where}: only the http-get method is implemented")
        recs = s.get("records") or []
        if not recs:
            errors.append(f"{where}: must list the evidence records that cite it (only cited sources are watched)")
        for rid in recs:
            if rid not in records:
                errors.append(f"{where}: unknown record {rid}")
            elif records[rid]["source_url"] != s.get("url"):
                errors.append(f"{where}: {rid} cites a different URL")
        for eid in s.get("entities") or []:
            if eid not in entities:
                errors.append(f"{where}: unknown entity {eid}")
        for pattern in s.get("ignore_patterns") or []:
            try:
                re.compile(pattern)
            except re.error:
                errors.append(f"{where}: invalid ignore pattern {pattern!r}")
        for field in ("name", "relevance", "access", "added"):
            if not s.get(field):
                errors.append(f"{where}: {field} is required")
    return errors


# ─── Staging store (outside the repository) ───────────────────────────────

def store_dir(path=None):
    path = Path(path or os.environ.get("THEMOROCCOAI_OBSERVATORY") or Path.home() / ".themoroccoai-observatory").resolve()
    if path == ROOT.resolve() or ROOT.resolve() in path.parents:
        raise StagingError(f"{path}: the staging store must be outside the public repository")
    return path


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dict(data, marker=STAGING_MARKER)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def observations(store, source_id):
    folder = Path(store) / "observations" / source_id
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))] if folder.exists() else []


def load_candidates(store):
    path = Path(store) / "candidates.json"
    return json.loads(path.read_text(encoding="utf-8"))["candidates"] if path.exists() else {}


def save_candidates(store, candidates):
    _write(Path(store) / "candidates.json", {"schema_version": SCHEMA_VERSION, "candidates": candidates})


# ─── Normalisation ────────────────────────────────────────────────────────

class _Blocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.current, self.skip = [], [], 0

    def _flush(self):
        text = "".join(self.current)
        if text.strip():
            self.blocks.append(text)
        self.current = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
        elif tag in BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if not self.skip:
            self.current.append(data)

    def close(self):
        super().close()
        self._flush()


def normalise_block(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    for pattern, repl in VOLATILE:
        text = pattern.sub(repl, text)
    return text


def blocks_from(body, content_type, ignore=()):
    """Visible text blocks in document order, normalised and with volatile tokens masked; blocks matching a
    source's ignore patterns (counters, relative times) and exact repeats are dropped."""
    raw = check_sources._decode(body, content_type)
    parser = _Blocks()
    parser.feed(raw)
    parser.close()
    ignore = [re.compile(p) for p in ignore]
    out, seen = [], set()
    for b in parser.blocks:
        n = normalise_block(b)
        if len(n) < 3 or any(p.search(n) for p in ignore) or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out, "�" in raw


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ─── Observation ──────────────────────────────────────────────────────────

class Robots:
    """robots.txt per host, read once per run. An unreadable robots.txt allows retrieval, as the standard says."""

    def __init__(self, agent=check_sources.USER_AGENT):
        self.agent, self.cache = agent, {}

    def allowed(self, url):
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.cache:
            rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
            try:
                rp.read()
            except Exception:  # noqa: BLE001 - unreadable robots.txt: treat as no rule
                rp = None
            self.cache[base] = rp
        rp = self.cache[base]
        return True if rp is None else rp.can_fetch(self.agent, url)


def observe(source, fetcher=check_sources.fetch, robots=None, now=None, evidence=None):
    """One observation of one source. It never raises on network trouble: the outcome says what happened. With
    the evidence registry, it also records where each excerpt of the records citing this source was found
    (check_sources.match_excerpts: visible text, raw source, or missing); the raw page itself is not kept."""
    now = now or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    obs = {"source_id": source["id"], "url": source["url"], "observed_at": now, "method": source["method"],
           "agent": check_sources.USER_AGENT}
    if robots is not None and not robots.allowed(source["url"]):
        return dict(obs, outcome="robots-disallowed")
    status, body, content_type, error, final = fetcher(source["url"])
    outcome = check_sources.classify(status, body, content_type, error)
    obs.update(outcome=outcome, http_status=status, final_url=final, redirected=final != source["url"],
               content_type=content_type, error=error)
    if outcome != "retrieved":
        return obs
    if body[:4] == b"%PDF" or "html" not in (content_type or "html"):
        return dict(obs, outcome="unreadable-format")
    blocks, encoding_issue = blocks_from(body, content_type, source.get("ignore_patterns") or ())
    obs.update(raw_sha256=hashlib.sha256(body).hexdigest(), text_sha256=_sha("\n".join(blocks)), blocks=blocks,
               block_count=len(blocks), encoding_issue=encoding_issue)
    if evidence is not None:
        visible, raw = check_sources.texts_from(body, content_type)
        matches = {}
        for r in evidence["records"]:
            if r["evidence_id"] in source.get("records", []):
                found = check_sources.match_excerpts(visible, raw, r.get("source_excerpts", []))
                if "missing" in found:
                    # Same rule as tools/check_sources.py: also read the page's own same-host scripts (single-page
                    # applications keep their text there). One more retrieval, only when an excerpt is missing.
                    found = check_sources.check_record(r, fetcher)["excerpts"]
                matches[r["evidence_id"]] = found
        obs["excerpt_matches"] = matches
    return obs


def compare(prev, cur):
    """What changed between two observations of the same source. A failed retrieval is never a change."""
    if prev is None:
        return {"kind": "first-observation"}
    if cur["outcome"] != "retrieved":
        return {"kind": "not-comparable", "reason": f"current retrieval: {cur['outcome']}"}
    if prev["outcome"] != "retrieved":
        return {"kind": "not-comparable", "reason": f"previous retrieval: {prev['outcome']}"}
    if prev["text_sha256"] == cur["text_sha256"]:
        return {"kind": "formatting-only" if prev["raw_sha256"] != cur["raw_sha256"] else "unchanged"}
    before, after = prev["blocks"], cur["blocks"]
    added = [b for b in after if b not in set(before)]
    removed = [b for b in before if b not in set(after)]
    if not added and not removed:
        return {"kind": "reordered"}
    return {"kind": "substantive", "added": added, "removed": removed}


def availability(history):
    """'reliable', 'unreliable' (the last UNRELIABLE_AFTER observations all failed) or 'unknown'."""
    if not history:
        return "unknown"
    tail = history[-UNRELIABLE_AFTER:]
    if len(tail) == UNRELIABLE_AFTER and all(o["outcome"] != "retrieved" for o in tail):
        return "unreliable"
    return "reliable" if history[-1]["outcome"] == "retrieved" else "failed-last"


# ─── Candidates ───────────────────────────────────────────────────────────

def language_of(text):
    if re.search(r"[؀-ۿ]", text):
        return "ar"
    words = set(re.findall(r"[a-zà-ÿ]+", text.lower()))
    fr = len(words & {"le", "la", "les", "des", "du", "et", "pour", "une", "dans", "est", "au", "aux", "avec"})
    en = len(words & {"the", "of", "and", "for", "with", "is", "in", "to", "a", "on", "by", "are"})
    return "fr" if fr > en else "en" if en > fr else "und"


def entity_terms(ontology):
    terms = {}
    for e in ontology["entities"]:
        for name in [e["name"], *(e.get("alt_names") or [])]:
            if len(name) >= 4:
                terms[check_sources.fold(name)] = e["id"]
    return terms


def _known_excerpts(evidence):
    return [(r["evidence_id"], check_sources.fold(x)) for r in evidence["records"] for x in r.get("source_excerpts", [])]


def candidate_id(source_id, block):
    return "CAND-" + _sha(source_id + "\n" + check_sources.fold(block))[:12]


def detect_candidates(source, obs, comparison, evidence, ontology, existing):
    """Candidates from substantive additions that mention a known entity or AI. Deterministic ids: the same
    text from the same source is one candidate, however often it is seen."""
    if comparison.get("kind") != "substantive":
        return []
    terms, excerpts, out = entity_terms(ontology), _known_excerpts(evidence), []
    for block in comparison["added"]:
        folded = check_sources.fold(block)
        related = sorted({eid for term, eid in terms.items() if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", folded)})
        ai = bool(AI_TERMS.search(block))
        if not related and not ai:
            continue
        cid = candidate_id(source["id"], block)
        if cid in existing:
            continue
        dup_evidence = sorted({rid for rid, x in excerpts if x and (x in folded or (len(folded) > 40 and folded in x))})
        out.append({
            "id": cid, "source_id": source["id"], "source_url": source["url"], "observed_at": obs["observed_at"],
            "observation_text_sha256": obs["text_sha256"], "excerpt": block, "language": language_of(block),
            "related_entities": related or sorted(source.get("entities") or []),
            "significance": ("mentions " + ", ".join(related)) if related else "AI-related text on a watched source",
            "duplicate_of_evidence": dup_evidence, "duplicate_of_candidate": None, "supersedes": None,
            "state": "detected", "notes": [],
            "history": [{"state": "detected", "at": obs["observed_at"], "by": AUTOMATED_ACTOR,
                         "note": "Detected in a substantive change; not verified."}],
        })
    return out


def reassessment_signals(source, obs, evidence):
    """Records citing this source whose recorded excerpts no longer appear in what was retrieved. A signal for a
    person to check, not a finding: the page may have moved the text, changed format or been restructured."""
    if obs is None or obs["outcome"] != "retrieved" or "excerpt_matches" not in obs:
        return []
    out = []
    for rid, matches in sorted(obs["excerpt_matches"].items()):
        missing = matches.count("missing")
        if missing:
            out.append({"record": rid, "missing_excerpts": missing, "total_excerpts": len(matches)})
    return out


def transition(candidate, to, by, note, at=None):
    """Move a candidate along the review workflow. Automated actors may only triage; every other move is a
    person's decision with a reason, recorded in the candidate's history."""
    at = at or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = candidate["state"]
    if to not in STATES:
        raise StagingError(f"unknown state {to!r}")
    if to not in TRANSITIONS[state]:
        raise StagingError(f"{candidate['id']}: {state} -> {to} is not an allowed transition")
    if by == AUTOMATED_ACTOR:
        if (state, to) not in AUTOMATED_TRANSITIONS:
            raise StagingError(f"{candidate['id']}: {state} -> {to} needs a human reviewer")
    elif not isinstance(by, str) or not REVIEWER_ID.match(by) or AUTOMATED_ID.search(by):
        raise StagingError(f"{by!r}: a reviewer is a pseudonymous person (e.g. reviewer-owner-01), never an automated identity")
    if by != AUTOMATED_ACTOR and not (note or "").strip():
        raise StagingError("a reviewer's decision needs a note")
    return dict(candidate, state=to, history=candidate["history"] + [{"state": to, "at": at, "by": by, "note": note}])


def triage(candidates):
    """Automated triage: an exact repeat of another candidate's text is a duplicate; everything else waits for a
    person. Nothing is accepted or rejected automatically."""
    by_text = {}
    out = {}
    for cid in sorted(candidates):
        c = candidates[cid]
        if c["state"] == "detected":
            key = check_sources.fold(c["excerpt"])
            if key in by_text:
                c = dict(transition(c, "duplicate", AUTOMATED_ACTOR, f"Same text as {by_text[key]}."), duplicate_of_candidate=by_text[key])
            else:
                c = transition(c, "awaiting_review", AUTOMATED_ACTOR, "Queued for human review.")
        by_text.setdefault(check_sources.fold(c["excerpt"]), cid)
        out[cid] = c
    return out


# ─── Admission proposal ───────────────────────────────────────────────────

DECISION_FIELDS = ("title", "claim", "classification", "verification_status", "verification_note", "evidence_type",
                   "source_type", "source_organization", "publication_date", "related_entities", "source_excerpts")


def propose_admission(candidate, decision, obs, evidence, ontology, reviewer):
    """A draft evidence record for a person to review and commit. It needs a candidate accepted for admission,
    a human reviewer, and excerpts quoted verbatim from what was retrieved (in their original language). It never
    writes to data/; it returns the draft and the validator's verdict on the registry with the draft added."""
    if candidate["state"] != "accepted_for_admission":
        raise StagingError(f"{candidate['id']}: only a candidate accepted for admission can be proposed (state: {candidate['state']})")
    if not REVIEWER_ID.match(reviewer or "") or AUTOMATED_ID.search(reviewer):
        raise StagingError("an admission proposal is prepared by a human reviewer")
    missing = [f for f in DECISION_FIELDS if f not in decision]
    if missing:
        raise StagingError(f"the reviewer's decision lacks {missing}")
    observed = check_sources.fold(" ".join(obs.get("blocks") or []))
    not_verbatim = [x for x in decision["source_excerpts"] if check_sources.fold(x) not in observed]
    if not decision["source_excerpts"] or not_verbatim:
        raise StagingError(f"excerpts must be quoted verbatim from the observed source: {not_verbatim[:1]}")
    numbers = sorted(int(r["evidence_id"].split("-")[-1]) for r in evidence["records"])
    record = {"evidence_id": f"MAI-EV-{numbers[-1] + 1:04d}", "source_url": candidate["source_url"],
              "source_language": candidate["language"] if candidate["language"] != "und" else decision.get("source_language", "en"),
              "retrieval_date": obs["observed_at"][:10], **{k: decision[k] for k in DECISION_FIELDS}}
    trial = dict(evidence, records=evidence["records"] + [record])
    problems = registry.validate(trial, ontology)
    return {"marker": STAGING_MARKER, "candidate": candidate["id"], "prepared_by": reviewer, "record": record,
            "validation": problems,
            "next_steps": ["Review the record against the source.",
                           "Add it to data/evidence.json and link it from the relevant entities or gaps in a reviewed PR.",
                           "Bump the registry version and add a changelog entry; tools/changes.py will show the admission."]}


# ─── Report ───────────────────────────────────────────────────────────────

def report(watchlist, store, evidence):
    """Answers the research questions from the staging store: what changed, what is relevant, what needs review,
    what duplicates existing evidence, which records may need reassessment, which sources are unreliable, and
    which candidates were admitted."""
    candidates = load_candidates(store)
    admitted_sources = {(r["source_url"], r.get("retrieval_date")) for r in evidence["records"]}
    rows = []
    for s in watchlist["sources"]:
        hist = observations(store, s["id"])
        last = hist[-1] if hist else None
        cmp = compare(hist[-2] if len(hist) > 1 else None, last) if last else {"kind": "never-observed"}
        rows.append({"source": s["id"], "slug": s["slug"], "status": s["status"],
                     "last_observed": last and last["observed_at"], "last_outcome": last and last["outcome"],
                     "last_successful": next((o["observed_at"] for o in reversed(hist) if o["outcome"] == "retrieved"), None),
                     "availability": availability(hist), "change": cmp["kind"],
                     "reassessment": reassessment_signals(s, last, evidence) if last else []})
    by_state = {}
    for c in candidates.values():
        by_state.setdefault(c["state"], []).append(c["id"])
    return {"sources": rows,
            "changed": [r["source"] for r in rows if r["change"] == "substantive"],
            "unreliable": [r["source"] for r in rows if r["availability"] == "unreliable"],
            "candidates_by_state": {k: sorted(v) for k, v in sorted(by_state.items())},
            "duplicates_of_evidence": sorted(c["id"] for c in candidates.values() if c["duplicate_of_evidence"]),
            "admitted": sorted(c["id"] for c in candidates.values()
                               if c["state"] == "accepted_for_admission" and (c["source_url"], c["observed_at"][:10]) in admitted_sources)}


# ─── CLI ──────────────────────────────────────────────────────────────────

def run_observation(watchlist, store, evidence, ontology, only=None, fetcher=check_sources.fetch, robots=None, sleep=time.sleep):
    robots = robots or Robots()
    candidates = load_candidates(store)
    last_host_at = {}
    summary = []
    for s in watchlist["sources"]:
        if (only and s["id"] != only) or s["status"] != "active":
            continue
        host = urlparse(s["url"]).netloc
        if host in last_host_at:
            sleep(max(0.0, check_sources.DELAY_PER_HOST - (time.monotonic() - last_host_at[host])))
        hist = observations(store, s["id"])
        obs = observe(s, fetcher, robots, evidence=evidence)
        last_host_at[host] = time.monotonic()
        # A sequence number keeps every observation, even two within the same second, in order.
        _write(Path(store) / "observations" / s["id"] / f"{len(hist) + 1:06d}-{obs['observed_at'].replace(':', '')}.json", obs)
        prev = next((o for o in reversed(hist) if o["outcome"] == "retrieved"), hist[-1] if hist else None)
        cmp = compare(prev, obs)
        for c in detect_candidates(s, obs, cmp, evidence, ontology, candidates):
            candidates[c["id"]] = c
        summary.append((s["id"], obs["outcome"], cmp["kind"]))
    save_candidates(store, triage(candidates))
    return summary


def main(argv):
    if not argv or argv[0] not in ("validate", "observe", "report", "candidates", "review", "propose"):
        print(__doc__)
        return 2
    evidence, ontology = registry.load_all()
    watchlist = load_watchlist()
    try:
        if argv[0] == "validate":
            errors = validate_watchlist(watchlist, evidence, ontology)
            for e in errors:
                print("ERROR", e)
            print(f"{len(watchlist['sources'])} sources, {len(errors)} problem(s)")
            return 1 if errors else 0
        store = store_dir()
        if argv[0] == "observe":
            only = argv[argv.index("--source") + 1] if "--source" in argv else None
            for sid, outcome, kind in run_observation(watchlist, store, evidence, ontology, only):
                print(sid, outcome, kind)
            return 0
        if argv[0] == "report":
            print(json.dumps(report(watchlist, store, evidence), ensure_ascii=False, indent=1))
            return 0
        candidates = load_candidates(store)
        if argv[0] == "candidates":
            for c in sorted(candidates.values(), key=lambda c: c["id"]):
                print(c["id"], c["state"], c["source_id"], c["significance"], "|", c["excerpt"][:100])
            return 0
        cid = argv[1]
        if cid not in candidates:
            raise StagingError(f"unknown candidate {cid}")
        if argv[0] == "review":
            to, by = argv[argv.index("--to") + 1], argv[argv.index("--by") + 1]
            note = argv[argv.index("--note") + 1] if "--note" in argv else ""
            candidates[cid] = transition(candidates[cid], to, by, note)
            save_candidates(store, candidates)
            print(cid, "->", to)
            return 0
        decision = json.loads(Path(argv[argv.index("--decision") + 1]).read_text(encoding="utf-8"))
        c = candidates[cid]
        obs = next(o for o in observations(store, c["source_id"]) if o["observed_at"] == c["observed_at"])
        proposal = propose_admission(c, decision, obs, evidence, ontology, decision.get("reviewer", ""))
        out = Path(store) / "proposals" / f"{cid}.json"
        _write(out, proposal)
        print(f"wrote {out}; validator problems: {len(proposal['validation'])}. Nothing was written to data/.")
        return 0
    except (StagingError, ValueError, KeyError, StopIteration) as exc:
        print("ERROR", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
