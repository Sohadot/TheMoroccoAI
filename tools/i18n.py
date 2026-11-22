"""Translation layer for TheMoroccoAI (decision TMA-DEC-007; design in docs/MULTILINGUAL_ARCHITECTURE.md).

    python3 tools/i18n.py            validate i18n/ and print the staleness and orphan report

English is the only research authority. This module never reads or writes a translation into data/:
canonical evidence, ontology and gaps stay single and hash-bound (REFERENCE_INPUTS, manifest). It
provides:

- the English message lookup used by tools/build.py (t, english_messages);
- source fingerprints (SHA-256 of the NFC English source) that make translations traceable and staleness
  detectable;
- structural validation of the language registry, catalogs, review metadata and glossary;
- publication eligibility: a unit is renderable only if it is approved and its fingerprint matches the
  current English source; a language can be 'published' only once a renderer for it exists.

Passing validation proves structure, provenance and parity of placeholders, digits and identifiers. It
does not and cannot prove that a translation means the same as the English: that is the job of the
two human reviews recorded on each unit. Standard library only.
"""
import datetime
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGUAGE_STATES = ("authoritative", "in-preparation", "published", "withdrawn")
# Languages tools/build.py can render (Sprint 19B-2). Rendering is not publication: a page is generated in one
# of these languages only when the language is 'published' in i18n/languages.json and the page is eligible
# (every unit it uses approved, reviewed and current; page gates passed). ary and zgh have no renderer.
RENDERING_LANGUAGES = frozenset({"ar", "fr"})
# Translation governance in force: TMA-DEC-008 (human-approved, AI-assisted translation), which supersedes the
# two-review provisions of TMA-DEC-007. An approval records this policy id; any other id is not accepted.
GOVERNANCE_POLICY = "TMA-DEC-008"
# Stored statuses. STALE is computed (source or approved text changed after approval) and never stored.
UNIT_STATUSES = ("DRAFT", "NEEDS_REVISION", "APPROVED", "REJECTED")
# Every file on main is publicly served, so catalogs on main hold approved units only (Arch §6.3). A
# translation pull request therefore stays red until both reviews are recorded: that is intended.
COMMITTABLE_STATUSES = ("APPROVED",)
REVIEWER_KINDS = ("human", "certified-translator")
# Escalation criteria (TMA-DEC-008): an open escalation blocks publication of the unit until a second, qualified
# registered reviewer resolves it.
ESCALATION_CRITERIA = ("reviewer-uncertain", "legal-ambiguity", "specialist-term", "research-qualification",
                       "language-expertise", "independent-review-claimed", "certified-translation-required")
# Identities that denote tools, AI systems or automated processes. They may draft, never approve.
AUTOMATED_ID = re.compile(r"(?:^|-)(?:ai|bot|ci|claude|gpt|llm|machine|auto|automated|assistant|model|pipeline|script)(?:-|$)")
DRAFTER_ID = re.compile(r"^[a-z]+(?:-[a-z]+)*(?:-[0-9]{2,})?$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z$")
KINDS = ("interface", "navigation", "heading", "metadata", "prose", "qualifier", "disclosure", "term", "name")
DRAFT_METHODS = ("human", "machine-assisted")
NAME_BASES = ("official", "established-usage", "transliteration", "translation")

LANG_CODE = re.compile(r"^[a-z]{2,3}$")
BCP47 = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2})?$")
MESSAGE_ID = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")
# Pseudonymous reviewer identifiers only (TMA-DEC-006, TMA-DEC-007 Q3): lowercase words and a number,
# for example 'reviewer-ar-02'. Names, e-mail addresses and spaces are rejected.
PSEUDONYM = re.compile(r"^[a-z]+(?:-[a-z]+)*-[0-9]{2,}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDER = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
# Identifiers and URLs must pass through a translation unchanged.
IDENTIFIER = re.compile(r"MAI-[A-Z0-9]+(?:-[A-Z0-9]+)*|https?://[^\s\"'<>)\]]+")
DIGITS = re.compile(r"[0-9]+")
ARABIC_INDIC_DIGITS = re.compile(r"[٠-٩۰-۹]")
# Direction overrides and isolates (U+202A–202E, U+2066–2069), direction marks, and invisible
# characters: direction is set with markup, never hidden in text. ZWNJ/ZWJ (U+200C/200D) are allowed.
FORBIDDEN_CHARS = {c: f"U+{c:04X}" for c in
                   [*range(0x202A, 0x202F), *range(0x2066, 0x206A), 0x200B, 0x200E, 0x200F, 0x2060, 0xFEFF]}

# Canonical prose a content unit may translate: '<file>:<id>:<field>' for records, entities and gaps, and
# '<vocabulary>:<key>:<field>' for canonical vocabulary text (classification definitions, domain labels).
# The English text is always read from data/, never copied into a catalog.
CONTENT_FIELDS = {
    "evidence": ("title", "claim", "verification_note"),
    "ontology": ("name", "summary", "note", "status"),
    "gaps": ("question", "established", "unestablished", "evidence_needed"),
    "classification": ("definition",),
    "domain": ("label",),
    "predicate": ("label",),
    # List items without an identifier of their own get an explicit, stable id in an identity map (below):
    # 'changelog:<item id>:text' (i18n/changelog-identity.json), 'attribute:<item id>:text' (i18n/attribute-identity.json).
    "changelog": ("text",),
    "attribute": ("text",),
}
CONTENT_ID = re.compile(r"^(evidence|ontology|gaps|classification|domain|predicate|changelog|attribute):([^:]+):([a-z_]+)$")
# Canonical vocabulary a glossary term may name: '<vocabulary>:<canonical value>'.
GLOSSARY_VOCABULARIES = ("classification", "verification_status", "entity_type", "lifecycle", "project_kind",
                         "origin", "domain", "predicate")


def nfc(text):
    return unicodedata.normalize("NFC", text)


def fingerprint(text):
    """SHA-256 of the NFC-normalised English source text: a translation records it to stay traceable."""
    return hashlib.sha256(nfc(text).encode("utf-8")).hexdigest()


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─── English source catalog (used by tools/build.py) ─────────────────────

def english_messages(root=ROOT):
    return {m["id"]: m["text"] for m in _load(Path(root) / "i18n" / "en" / "messages.json")["messages"]}


_EN = None


def t(message_id, **values):
    """English text for message_id with {name} placeholders filled. Unknown ids and missing values fail."""
    global _EN
    if _EN is None:
        _EN = english_messages()
    return fill(_EN[message_id], values, message_id)


# ─── Stable identity for canonical list items ────────────────────────────
# Changelog texts and entity attributes are list items in canonical data with no identifier of their own. An
# identity map (i18n/<kind>-identity.json) gives each a stable id without touching canonical data. Binding is by
# the recorded fingerprint of the text inside a stable entry key (changelog version or commit, entity id), never
# by array position or presentation order, so a reorder changes nothing. Everything else fails closed:
# - an inserted text has no identity: register a new id (never a retired one);
# - a deleted text leaves an orphaned identity: retire it (status "retired"; its id is never reused);
# - an edited text keeps its id once the maintainer records the new fingerprint, which makes every translation of
#   it stale until it is approved again;
# - identical texts in one entry and field are told apart only by an explicit "occurrence" number.

IDENTITY_FIELDS = {"changelog": ("note", "title", "changes", "corrections", "review_fixes", "breaking_changes"),
                   "attribute": ("name", "value")}
IDENTITY_ITEM_ID = re.compile(r"^(changelog|attribute)\.[a-z0-9-]+\.[a-z_]+(?:\.[0-9]{2,})?$")


def changelog_entries(changelog):
    """Canonical changelog texts as [(entry key, {field: [texts]})]; the key never depends on position."""
    out = [({"document": "changelog"}, {"note": [changelog["note"]]})] if changelog.get("note") else []
    for e in changelog["entries"]:
        key = ({"version": e["version"]} if e.get("version") else {"commit": e["commit"]} if e.get("commit")
               else {"pull_request": e.get("pull_request")})
        fields = {"title": [e["title"]]}
        for f in ("changes", "corrections", "review_fixes", "breaking_changes"):
            if e.get(f):
                fields[f] = list(e[f])
        out.append((key, fields))
    return out


def attribute_entries(ontology):
    return [({"entity": e["id"]}, {"name": [a["name"] for a in e["attributes"]], "value": [a["value"] for a in e["attributes"]]})
            for e in ontology["entities"] if e.get("attributes")]


def bind_identity(kind, entries, identity):
    """Bind canonical texts to identity ids. Returns (bindings, texts, errors): bindings maps
    (entry index, field, position) to an id; texts maps each bound id to its current canonical text."""
    errors, bindings, texts, seen = [], {}, {}, set()
    where = f"i18n/{kind}-identity.json"
    ientries = identity.get("entries") if isinstance(identity, dict) else None
    if not isinstance(ientries, list):
        return bindings, texts, [f"{where}: needs an 'entries' list"]
    by_key = {}
    for ie in ientries:
        eid, key = ie.get("id"), ie.get("key")
        if not isinstance(eid, str) or not re.fullmatch(r"[a-z0-9-]+", eid or ""):
            errors.append(f"{where}: entry id {eid!r} must be lowercase letters, digits and hyphens")
        if eid in seen:
            errors.append(f"{where}: duplicate identity {eid!r}")
        seen.add(eid)
        k = json.dumps(key, sort_keys=True)
        if k in by_key:
            errors.append(f"{where}: two identity entries share the key {key}")
        by_key[k] = ie
        for it in ie.get("items", []):
            iid = it.get("id")
            if not isinstance(iid, str) or not IDENTITY_ITEM_ID.match(iid) or not iid.startswith(f"{kind}.{eid}."):
                errors.append(f"{where}: item id {iid!r} must look like '{kind}.{eid}.<field>[.NN]'")
            if iid in seen:
                errors.append(f"{where}: duplicate identity {iid!r} (ids are never reused, retired ones included)")
            seen.add(iid)
            if it.get("field") not in IDENTITY_FIELDS[kind]:
                errors.append(f"{where}: {iid!r} has unknown field {it.get('field')!r}")
            if it.get("status") not in ("active", "retired"):
                errors.append(f"{where}: {iid!r} status must be 'active' or 'retired'")
            if not isinstance(it.get("source_sha256"), str) or not SHA256.match(it["source_sha256"]):
                errors.append(f"{where}: {iid!r} needs the source_sha256 of the text it identifies")
            if "occurrence" in it and (not isinstance(it["occurrence"], int) or it["occurrence"] < 1):
                errors.append(f"{where}: {iid!r} occurrence must be a positive integer")
            if set(it) - {"id", "field", "status", "source_sha256", "occurrence"}:
                errors.append(f"{where}: {iid!r} has unexpected fields")
    if errors:
        return bindings, texts, errors
    canonical_keys = [json.dumps(k, sort_keys=True) for k, _ in entries]
    for k in {k for k in canonical_keys if canonical_keys.count(k) > 1}:
        errors.append(f"{where}: canonical entries share the key {k}; their identity is ambiguous")
    matched = set()
    for index, (key, fields) in enumerate(entries):
        k = json.dumps(key, sort_keys=True)
        ie = by_key.get(k)
        if ie is None:
            errors.append(f"{where}: canonical entry {key} has no registered identity")
            continue
        matched.add(k)
        for field in IDENTITY_FIELDS[kind]:
            values = fields.get(field, [])
            active = [it for it in ie.get("items", []) if it["field"] == field and it["status"] == "active"]
            groups = {}
            for pos, text in enumerate(values):
                groups.setdefault(fingerprint(text), []).append(pos)
            items = {}
            for it in active:
                items.setdefault(it["source_sha256"], []).append(it)
            for fp, positions in groups.items():
                cands = items.get(fp, [])
                if not cands:
                    errors.append(f"{where}: {key} {field} text {values[positions[0]][:60]!r} has no active identity "
                                  "(new text: register a new id; edited text: record its new source_sha256 on the existing id)")
                    continue
                if len(cands) != len(positions):
                    errors.append(f"{where}: {key} {field}: {len(positions)} identical text(s) but {len(cands)} active id(s); ambiguous")
                    continue
                if len(positions) == 1 and "occurrence" not in cands[0]:
                    pairs = [(positions[0], cands[0])]
                else:
                    occ = sorted(c.get("occurrence", 0) for c in cands)
                    if occ != list(range(1, len(cands) + 1)):
                        errors.append(f"{where}: {key} {field}: identical texts need occurrence numbers 1..{len(cands)}; ambiguous")
                        continue
                    pairs = list(zip(positions, sorted(cands, key=lambda c: c["occurrence"])))
                for pos, it in pairs:
                    bindings[(index, field, pos)] = it["id"]
                    texts[it["id"]] = values[pos]
            for fp, its in items.items():
                if fp not in groups:
                    for it in its:
                        errors.append(f"{where}: active identity {it['id']!r} matches no canonical text "
                                      "(deleted: retire it; edited: record the new source_sha256)")
    for k, ie in by_key.items():
        if k not in matched and any(it.get("status") == "active" for it in ie.get("items", [])):
            errors.append(f"{where}: identity entry {ie['id']!r} matches no canonical entry; retire its items")
    return bindings, texts, errors


def load_identity(kind, root=ROOT, changelog=None, ontology=None):
    """(bindings, texts, errors) for 'changelog' or 'attribute' from the canonical data and its identity map."""
    root = Path(root)
    path = root / "i18n" / f"{kind}-identity.json"
    if not path.exists():
        return {}, {}, [f"i18n/{kind}-identity.json: missing"]
    def data(name):  # canonical data of this root, or of the repository when the root holds only i18n/
        return _load(root / "data" / name if (root / "data" / name).exists() else ROOT / "data" / name)
    if kind == "changelog":
        entries = changelog_entries(changelog if changelog is not None else data("changelog.json"))
    else:
        entries = attribute_entries(ontology if ontology is not None else data("ontology.json"))
    return bind_identity(kind, entries, _load(path))


def identity_proposals(kind, entries, identity):
    """Suggested repairs for the maintainer, never applied automatically: an edited text where exactly one text
    and one identity are unmatched in the same entry and field; new ids for inserted texts; retirement for
    orphaned identities."""
    out, used = [], {it["id"] for ie in identity.get("entries", []) for it in ie.get("items", [])}
    by_key = {json.dumps(ie["key"], sort_keys=True): ie for ie in identity.get("entries", [])}
    for key, fields in entries:
        ie = by_key.get(json.dumps(key, sort_keys=True))
        if ie is None:
            out.append(f"register an identity entry for {key}")
            continue
        for field in IDENTITY_FIELDS[kind]:
            fps = [fingerprint(t) for t in fields.get(field, [])]
            active = [it for it in ie["items"] if it["field"] == field and it["status"] == "active"]
            unbound = [i for i, fp in enumerate(fps) if fp not in {it["source_sha256"] for it in active}]
            orphan = [it for it in active if it["source_sha256"] not in fps]
            if len(unbound) == 1 and len(orphan) == 1:
                out.append(f"{orphan[0]['id']}: if the text was edited, set source_sha256 to {fps[unbound[0]]}")
                continue
            for i in unbound:
                n = 1
                while f"{kind}.{ie['id']}.{field}.{n:02d}" in used:
                    n += 1
                used.add(f"{kind}.{ie['id']}.{field}.{n:02d}")
                out.append(f"new text in {key} {field}: register {kind}.{ie['id']}.{field}.{n:02d} with source_sha256 {fps[i]}")
            for it in orphan:
                out.append(f"{it['id']}: matches no text; set status to 'retired' (its id is never reused)")
    return out


# ─── Source resolution ────────────────────────────────────────────────────

class Sources:
    """English source text for message ids, canonical content ids and glossary term ids."""

    def __init__(self, root=ROOT, evidence=None, ontology=None, gaps=None):
        root = Path(root)
        self.root = root
        self.messages = english_messages(root)
        self.evidence = evidence if evidence is not None else _load(root / "data" / "evidence.json")
        self.ontology = ontology if ontology is not None else _load(root / "data" / "ontology.json")
        self.gaps = gaps if gaps is not None else _load(root / "data" / "gaps.json")
        self.records = {r["evidence_id"]: r for r in self.evidence["records"]}
        self.entities = {e["id"]: e for e in self.ontology["entities"]}
        self.gap_items = {g["id"]: g for g in self.gaps["gaps"]}

    def message(self, unit_id):
        return self.messages.get(unit_id)

    def identity_texts(self, kind):
        cache = self.__dict__.setdefault("_identity", {})
        if kind not in cache:
            cache[kind] = load_identity(kind, self.root, ontology=self.ontology)[1]
        return cache[kind]

    def content(self, unit_id):
        """(text, problem): text is None if the record or field no longer exists (an orphan)."""
        m = CONTENT_ID.match(unit_id)
        if not m:
            return None, "malformed"
        kind, key, field = m.groups()
        if field not in CONTENT_FIELDS[kind]:
            return None, "malformed"
        if kind == "classification":
            text = self.evidence["classifications"].get(key)
            return (text, None) if isinstance(text, str) and text else (None, "orphan")
        if kind == "domain":
            text = self.ontology["domains"].get(key)
            return (text, None) if isinstance(text, str) and text else (None, "orphan")
        if kind == "predicate":
            text = (self.ontology["predicates"].get(key) or {}).get("label")
            return (text, None) if isinstance(text, str) and text else (None, "orphan")
        if kind in ("changelog", "attribute"):
            if not IDENTITY_ITEM_ID.match(key) or not key.startswith(kind + "."):
                return None, "malformed"
            text = self.identity_texts(kind).get(key)
            return (text, None) if text else (None, "orphan")
        table = {"evidence": self.records, "ontology": self.entities, "gaps": self.gap_items}[kind]
        item = table.get(key)
        if item is None or not isinstance(item.get(field), str) or not item.get(field):
            return None, "orphan"
        return item[field], None

    def vocabulary(self, name):
        o, e = self.ontology, self.evidence
        return {
            "classification": set(e["classifications"]),
            "verification_status": set(e["verification_statuses"]),
            "entity_type": set(o["entity_types"]),
            "lifecycle": set(o["lifecycle_stages"]),
            "project_kind": set(o["project_kinds"]),
            "origin": set(o["origins"]),
            "domain": set(o["domains"]),
            "predicate": set(o["predicates"]),
        }[name]


# ─── Validation ───────────────────────────────────────────────────────────

def _text_problems(text, where):
    errors = []
    if not isinstance(text, str) or not text.strip():
        return [f"{where}: empty text"]
    if text != nfc(text):
        errors.append(f"{where}: text is not Unicode NFC")
    bad = sorted({FORBIDDEN_CHARS[ord(ch)] for ch in text if ord(ch) in FORBIDDEN_CHARS})
    if bad:
        errors.append(f"{where}: prohibited invisible or bidirectional control characters {bad}")
    if "<" in text or ">" in text:
        errors.append(f"{where}: markup is not allowed in catalog text (keep it in the generator)")
    if "{" in PLACEHOLDER.sub("", text) or "}" in PLACEHOLDER.sub("", text):
        errors.append(f"{where}: malformed rich-text token: braces are allowed only as {{name}} placeholders")
    return errors


def validate_languages(registry):
    errors, codes = [], []
    langs = registry.get("languages") if isinstance(registry, dict) else None
    if not isinstance(langs, list) or not langs:
        return ["i18n/languages.json: 'languages' must be a non-empty list"]
    for i, lang in enumerate(langs):
        where = f"i18n/languages.json[{i}]"
        missing = {"code", "bcp47", "script", "dir", "native_name", "state", "route", "og_locale"} - set(lang)
        if missing:
            errors.append(f"{where}: missing {sorted(missing)}")
            continue
        code = lang["code"]
        codes.append(code)
        if not LANG_CODE.match(code):
            errors.append(f"{where}: invalid language code {code!r}")
        if not BCP47.match(lang["bcp47"]) or lang["bcp47"].split("-")[0] != code:
            errors.append(f"{where}: bcp47 {lang['bcp47']!r} does not match code {code!r}")
        if not re.match(r"^[A-Z][a-z]{3}$", lang["script"]):
            errors.append(f"{where}: script must be an ISO 15924 code such as 'Arab'")
        if lang["dir"] not in ("ltr", "rtl"):
            errors.append(f"{where}: dir must be 'ltr' or 'rtl'")
        if not re.match(r"^[a-z]{2,3}_[A-Z]{2}$", lang["og_locale"]) or lang["og_locale"].split("_")[0] != code:
            errors.append(f"{where}: og_locale {lang['og_locale']!r} must look like '{code}_MA'")
        if lang["state"] not in LANGUAGE_STATES:
            errors.append(f"{where}: unknown state {lang['state']!r}")
        errors += _text_problems(lang["native_name"], f"{where}.native_name")
        if code == "en":
            if lang["state"] != "authoritative" or lang["route"] != "/":
                errors.append(f"{where}: English must be 'authoritative' at route '/'")
        else:
            if lang["state"] == "authoritative":
                errors.append(f"{where}: only English may be authoritative (TMA-DEC-003, TMA-DEC-007)")
            if lang["route"] != f"/{code}/":
                errors.append(f"{where}: route must be '/{code}/'")
            if lang["state"] == "published" and code not in RENDERING_LANGUAGES:
                errors.append(f"{where}: '{code}' cannot be 'published': no localized renderer exists for it")
    if len(codes) != len(set(codes)):
        errors.append("i18n/languages.json: duplicate language codes")
    if "en" not in codes:
        errors.append("i18n/languages.json: English ('en') must be registered as authoritative")
    return errors


def validate_english(catalog, sources=None):
    errors, seen = [], set()
    if catalog.get("language") != "en" or not isinstance(catalog.get("messages"), list):
        return ["i18n/en/messages.json: must declare language 'en' and a 'messages' list"]
    for m in catalog["messages"]:
        where = f"i18n/en/messages.json {m.get('id')!r}"
        if not isinstance(m.get("id"), str) or not MESSAGE_ID.match(m["id"]):
            errors.append(f"{where}: invalid message id")
        elif m["id"] in seen:
            errors.append(f"{where}: duplicate message id")
        seen.add(m.get("id"))
        if m.get("kind") not in KINDS:
            errors.append(f"{where}: unknown kind {m.get('kind')!r}")
        if "term" in m:
            vocab, _, value = str(m["term"]).partition(":")
            if m.get("kind") != "term" or vocab not in GLOSSARY_VOCABULARIES or (sources and value not in sources.vocabulary(vocab)):
                errors.append(f"{where}: term link {m['term']!r} must name canonical vocabulary on a 'term' message")
        errors += _text_problems(m.get("text"), where)
    return errors


def _parity_problems(text, source, where):
    errors = []
    if set(PLACEHOLDER.findall(text)) != set(PLACEHOLDER.findall(source)):
        errors.append(f"{where}: placeholders {sorted(set(PLACEHOLDER.findall(text)))} differ from the English "
                      f"source {sorted(set(PLACEHOLDER.findall(source)))}")
    if ARABIC_INDIC_DIGITS.search(text):
        errors.append(f"{where}: Arabic-Indic digits are not used; numbers keep Western digits in every language")
    extra = set(DIGITS.findall(PLACEHOLDER.sub("", text))) - set(DIGITS.findall(source))
    if extra:
        errors.append(f"{where}: numbers {sorted(extra)} do not occur in the English source")
    if sorted(IDENTIFIER.findall(text)) != sorted(IDENTIFIER.findall(source)):
        errors.append(f"{where}: identifiers or URLs differ from the English source "
                      f"({sorted(IDENTIFIER.findall(text))} vs {sorted(IDENTIFIER.findall(source))})")
    return errors


def load_reviewers(root=ROOT):
    """{id: entry} from i18n/reviewers.json: the pseudonymous human reviewers the owner has registered."""
    path = Path(root) / "i18n" / "reviewers.json"
    return {r["id"]: r for r in _load(path).get("reviewers", [])} if path.exists() else {}


def validate_reviewers(data, languages):
    errors, seen = [], set()
    if not isinstance(data.get("reviewers"), list):
        return ["i18n/reviewers.json: needs a 'reviewers' list"]
    for r in data["reviewers"]:
        rid = r.get("id")
        where = f"i18n/reviewers.json {rid!r}"
        if not isinstance(rid, str) or not PSEUDONYM.match(rid):
            errors.append(f"{where}: reviewer id must be pseudonymous, such as 'reviewer-ar-02'")
        elif AUTOMATED_ID.search(rid):
            errors.append(f"{where}: an automated or AI identity cannot be registered as a reviewer")
        if rid in seen:
            errors.append(f"{where}: duplicate reviewer id")
        seen.add(rid)
        if r.get("kind") not in REVIEWER_KINDS:
            errors.append(f"{where}: kind must be one of {list(REVIEWER_KINDS)}")
        if not isinstance(r.get("languages"), list) or not r["languages"] or set(r["languages"]) - set(languages):
            errors.append(f"{where}: languages must be registered translation languages")
        if set(r) - {"id", "kind", "languages"}:
            errors.append(f"{where}: unexpected fields {sorted(set(r) - {'id', 'kind', 'languages'})} (no personal data)")
    return errors


def _timestamp_problems(value, field, where, today):
    if not isinstance(value, str) or not ISO_UTC.match(value):
        return [f"{where}: {field} must be a UTC timestamp such as 2026-12-01T09:30:00Z"]
    if datetime.date.fromisoformat(value[:10]) > today:
        return [f"{where}: {field} is in the future"]
    return []


def _draft_problems(u, where):
    d = u.get("draft")
    if not isinstance(d, dict) or d.get("method") not in DRAFT_METHODS or not isinstance(d.get("by"), str) \
            or not DRAFTER_ID.match(d["by"]) or set(d) - {"method", "by"}:
        return [f"{where}: draft must record method {list(DRAFT_METHODS)} and 'by' (a pseudonym or a process id)"]
    return []


def _approval_problems(u, lang, reviewers, today, where):
    """Errors in the human approval of an APPROVED unit (TMA-DEC-008). Approval is a deliberate, attributable
    human decision bound to exact source and translation versions: it is never inferred from a passing check,
    a commit, a merge or repository access, and no automated or AI identity can give it."""
    a = u.get("approval")
    if not isinstance(a, dict):
        return [f"{where}: APPROVED unit has no human approval record"]
    errors = []
    allowed = {"reviewer", "decision", "reviewed_at", "policy", "source_sha256", "translation_sha256",
               "glossary_version", "escalation"}
    if set(a) - allowed:
        errors.append(f"{where}: unexpected approval fields {sorted(set(a) - allowed)} (no personal data)")
    reviewer = a.get("reviewer")
    if not isinstance(reviewer, str) or not PSEUDONYM.match(reviewer):
        errors.append(f"{where}: approval.reviewer must be a pseudonymous identifier such as 'reviewer-ar-02'")
    elif AUTOMATED_ID.search(reviewer):
        errors.append(f"{where}: an automated or AI identity cannot approve a translation")
    elif reviewer not in reviewers:
        errors.append(f"{where}: approval.reviewer {reviewer!r} is not a registered human reviewer (i18n/reviewers.json)")
    elif lang not in reviewers[reviewer].get("languages", []):
        errors.append(f"{where}: reviewer {reviewer!r} is not registered for '{lang}'")
    if reviewer and (u.get("draft") or {}).get("by") == reviewer:
        errors.append(f"{where}: a reviewer cannot approve a translation recorded as their own draft")
    if a.get("decision") != "approved":
        errors.append(f"{where}: approval.decision must be 'approved' for an APPROVED unit")
    errors += _timestamp_problems(a.get("reviewed_at"), "approval.reviewed_at", where, today)
    if a.get("policy") != GOVERNANCE_POLICY:
        errors.append(f"{where}: approval.policy {a.get('policy')!r} is not the policy in force ({GOVERNANCE_POLICY})")
    if a.get("source_sha256") != u.get("source_sha256"):
        errors.append(f"{where}: the approval covers a different English source version")
    if not isinstance(a.get("translation_sha256"), str) or not SHA256.match(a["translation_sha256"]):
        errors.append(f"{where}: approval.translation_sha256 must record the approved translation")
    if not isinstance(a.get("glossary_version"), str) or not a["glossary_version"]:
        errors.append(f"{where}: approval.glossary_version is required")
    esc = a.get("escalation")
    if esc is not None:
        if not isinstance(esc, dict) or not esc.get("criteria") or set(esc.get("criteria", [])) - set(ESCALATION_CRITERIA):
            errors.append(f"{where}: escalation.criteria must be a non-empty subset of {list(ESCALATION_CRITERIA)}")
        elif esc.get("status") == "open":
            errors.append(f"{where}: escalation {esc['criteria']} is unresolved; publication is blocked")
        elif esc.get("status") != "resolved":
            errors.append(f"{where}: escalation.status must be 'open' or 'resolved'")
        else:
            by = esc.get("resolved_by")
            need = "certified-translator" if "certified-translation-required" in esc["criteria"] else None
            if by not in reviewers or by == reviewer or lang not in reviewers[by].get("languages", []):
                errors.append(f"{where}: an escalation is resolved only by a second registered reviewer for '{lang}'")
            elif need and reviewers[by].get("kind") != need:
                errors.append(f"{where}: certified translation was required; {by!r} is not a certified translator")
            errors += _timestamp_problems(esc.get("resolved_at"), "escalation.resolved_at", where, today)
        if isinstance(esc, dict) and set(esc) - {"criteria", "status", "resolved_by", "resolved_at"}:
            errors.append(f"{where}: unexpected escalation fields")
    return errors


def _approved_current(u, text):
    """True when the approved translation text is exactly the version the reviewer approved."""
    a = u.get("approval") or {}
    return isinstance(text, str) and a.get("translation_sha256") == fingerprint(text)


def validate_catalog(lang, kind, catalog, sources, forbidden, today, reviewers=None):
    """Returns (errors, report). report lists stale and orphaned units: they are not errors, so English
    publishing never waits for translation (TMA-DEC-007 Q4), but they are never renderable."""
    path = f"i18n/{lang}/{kind}.json"
    errors, report, seen = [], {"stale": [], "orphaned": []}, set()
    if catalog.get("language") != lang or not isinstance(catalog.get("units"), list):
        return [f"{path}: must declare language {lang!r} and a 'units' list"], report
    for u in catalog["units"]:
        uid = u.get("id")
        where = f"{path} {uid!r}"
        if not isinstance(uid, str):
            errors.append(f"{where}: missing id")
            continue
        if uid in seen:
            errors.append(f"{where}: duplicate translation id")
        seen.add(uid)
        if kind == "messages":
            if not MESSAGE_ID.match(uid):
                errors.append(f"{where}: invalid message id")
                continue
            source, problem = sources.message(uid), None if uid in sources.messages else "orphan"
        else:
            source, problem = sources.content(uid)
            if problem == "malformed":
                errors.append(f"{where}: not a translatable canonical field (expected <file>:<id>:<field>)")
                continue
        if u.get("status") not in UNIT_STATUSES:
            errors.append(f"{where}: unknown status {u.get('status')!r} (STALE is computed, never stored)")
        elif u["status"] not in COMMITTABLE_STATUSES:
            errors.append(f"{where}: status {u['status']!r} is not publishable; drafts stay off main")
        errors += _draft_problems(u, where)
        if u.get("kind") not in KINDS:
            errors.append(f"{where}: unknown kind {u.get('kind')!r}")
        if u.get("kind") == "name" and u.get("name_basis") not in NAME_BASES:
            errors.append(f"{where}: a name unit needs name_basis in {list(NAME_BASES)}")
        if not isinstance(u.get("source_sha256"), str) or not SHA256.match(u["source_sha256"]):
            errors.append(f"{where}: missing or invalid source_sha256 (source reference)")
        errors += _text_problems(u.get("text"), where)
        lowered = (u.get("text") or "").lower()
        for variant in forbidden:
            if variant.lower() in lowered:
                errors.append(f"{where}: uses forbidden glossary variant {variant!r}")
        if u.get("status") == "APPROVED":
            errors += _approval_problems(u, lang, reviewers or {}, today, where)
        if problem == "orphan":
            report["orphaned"].append(f"{lang}:{uid}")
            continue
        if isinstance(u.get("text"), str):
            errors += _parity_problems(u["text"], source, where)
        if isinstance(u.get("source_sha256"), str) and u["source_sha256"] != fingerprint(source):
            report["stale"].append(f"{lang}:{uid}")
        elif u.get("status") == "APPROVED" and isinstance(u.get("approval"), dict) and not _approved_current(u, u.get("text")):
            report["stale"].append(f"{lang}:{uid}")  # text changed after approval: renewed approval needed
    return errors, report


def _term_unit(term_id, entry):
    """A glossary label as an approvable unit: its source is the canonical term value."""
    return dict(entry, id=term_id, text=entry.get("label"), source_sha256=fingerprint(term_id.partition(":")[2]))


def validate_glossary(glossary, sources, languages, reviewers=None, today=None):
    errors, seen, forbidden = [], set(), {lang: [] for lang in languages}
    if not isinstance(glossary.get("version"), str) or not isinstance(glossary.get("terms"), list):
        return ["i18n/glossary.json: needs a 'version' string and a 'terms' list"], forbidden
    for term in glossary["terms"]:
        tid = term.get("id")
        where = f"i18n/glossary.json {tid!r}"
        if tid in seen:
            errors.append(f"{where}: duplicate term id")
        seen.add(tid)
        vocab, _, value = (tid or "").partition(":")
        if vocab not in GLOSSARY_VOCABULARIES or value not in sources.vocabulary(vocab):
            errors.append(f"{where}: does not name canonical vocabulary (expected e.g. 'classification:VERIFIED FACT')")
        for lang, entry in term.get("translations", {}).items():
            if lang not in languages:
                errors.append(f"{where}: language {lang!r} is not a registered translation language")
                continue
            errors += _text_problems(entry.get("label"), f"{where}.{lang}.label")
            if entry.get("status") not in COMMITTABLE_STATUSES:
                errors.append(f"{where}.{lang}: status {entry.get('status')!r} is not approved")
            else:
                unit = _term_unit(tid, entry)
                errors += _draft_problems(unit, f"{where}.{lang}")
                errors += _approval_problems(unit, lang, reviewers or {}, today or datetime.date.today(), f"{where}.{lang}")
            for variant in entry.get("forbidden", []):
                if variant and variant.lower() in (entry.get("label") or "").lower():
                    errors.append(f"{where}.{lang}: label contains its own forbidden variant {variant!r}")
                forbidden[lang].append(variant)
    return errors, forbidden


def validate(root=ROOT, evidence=None, ontology=None, gaps=None, today=None):
    """Validate i18n/. Returns (errors, report); report = {'stale': [...], 'orphaned': [...]}."""
    root = Path(root)
    today = today or datetime.date.today()
    report = {"stale": [], "orphaned": []}
    base = root / "i18n"
    try:
        registry = _load(base / "languages.json")
        english = _load(base / "en" / "messages.json")
        glossary = _load(base / "glossary.json")
    except (OSError, ValueError) as exc:
        return [f"i18n: cannot read the language registry, English catalog or glossary ({exc})"], report
    errors = validate_languages(registry) + validate_english(english)
    if errors:
        return errors, report
    sources = Sources(root, evidence, ontology, gaps)
    errors += [e for e in validate_english(english, sources) if "term link" in e]
    targets = [lang["code"] for lang in registry["languages"] if lang["code"] != "en"]
    reviewers_path = base / "reviewers.json"
    if not reviewers_path.exists():
        return errors + ["i18n/reviewers.json: missing (the registry of human reviewers, empty until the owner adds one)"], report
    errors += validate_reviewers(_load(reviewers_path), targets)
    reviewers = load_reviewers(root)
    for kind in ("changelog", "attribute"):
        errors += load_identity(kind, root, ontology=sources.ontology)[2]
    gerrors, forbidden = validate_glossary(glossary, sources, targets, reviewers, today)
    errors += gerrors
    for lang in targets:
        for kind in ("messages", "content"):
            path = base / lang / f"{kind}.json"
            if not path.exists():
                continue
            try:
                catalog = _load(path)
            except ValueError as exc:
                errors.append(f"i18n/{lang}/{kind}.json: invalid JSON ({exc})")
                continue
            cerrors, creport = validate_catalog(lang, kind, catalog, sources, forbidden[lang], today, reviewers)
            errors += cerrors
            report["stale"] += creport["stale"]
            report["orphaned"] += creport["orphaned"]
    for lang_dir in sorted(p.name for p in base.iterdir() if p.is_dir()):
        if lang_dir != "en" and lang_dir not in targets:
            errors.append(f"i18n/{lang_dir}/: language is not registered in i18n/languages.json")
    return errors, report


# ─── Publication eligibility ─────────────────────────────────────────────

def renderable_texts(lang, root=ROOT, evidence=None, ontology=None, gaps=None, today=None):
    """{id: text} of the units in `lang` that may be rendered. A unit is renderable only if it is APPROVED by a
    registered human reviewer under the policy in force (TMA-DEC-008), the approval covers exactly the current
    English source and the current translation text, no escalation is open, and the text passes every text and
    parity rule. Stale, orphaned, unapproved or invalid units are never renderable (no grace period), whether or
    not the validator was run. Nothing here, nor any check or merge, can create an approval."""
    root = Path(root)
    today = today or datetime.date.today()
    sources = Sources(root, evidence, ontology, gaps)
    reviewers = load_reviewers(root)
    out = {}
    for kind in ("messages", "content"):
        path = root / "i18n" / lang / f"{kind}.json"
        if not path.exists():
            continue
        for u in _load(path).get("units", []):
            uid, text = u.get("id"), u.get("text")
            source = sources.message(uid) if kind == "messages" else sources.content(uid or "")[0]
            if (source is None or u.get("status") != "APPROVED" or u.get("source_sha256") != fingerprint(source)
                    or _draft_problems(u, uid) or _approval_problems(u, lang, reviewers, today, uid)
                    or not _approved_current(u, text) or _text_problems(text, uid) or _parity_problems(text, source, uid)):
                continue
            out[uid] = text
    return out


def renderable_units(lang, root=ROOT, evidence=None, ontology=None, gaps=None, today=None):
    return set(renderable_texts(lang, root, evidence, ontology, gaps, today))


def approved_terms(lang, root=ROOT, today=None):
    """{term id: label} of glossary terms whose label in `lang` is well formed and human-approved (TMA-DEC-008)
    for exactly that label."""
    out, reviewers, today = {}, load_reviewers(root), today or datetime.date.today()
    for term in _load(Path(root) / "i18n" / "glossary.json").get("terms", []):
        entry = term.get("translations", {}).get(lang)
        if not entry or entry.get("status") not in COMMITTABLE_STATUSES or _text_problems(entry.get("label"), ""):
            continue
        unit = _term_unit(term["id"], entry)
        if any(v and v.lower() in entry["label"].lower() for v in entry.get("forbidden", [])) \
                or _draft_problems(unit, "") or _approval_problems(unit, lang, reviewers, today, "") \
                or not _approved_current(unit, entry["label"]):
            continue
        out[term["id"]] = entry["label"]
    return out


class Untranslated(Exception):
    """A page needs a unit or term that has no approved, current translation: the page is not eligible."""


def fill(template, values, message_id="", transform=str):
    """Replace {name} placeholders; the placeholder set must equal the values given. `transform` is applied
    to the template text outside placeholders (for example HTML escaping), never to the values."""
    names = set(PLACEHOLDER.findall(template))
    if names != set(values):
        raise KeyError(f"{message_id}: placeholders {sorted(names)} but values {sorted(values)}")
    parts, last = [], 0
    for m in PLACEHOLDER.finditer(template):
        parts += [transform(template[last:m.start()]), str(values[m.group(1)])]
        last = m.end()
    return "".join(parts + [transform(template[last:])])


class Translator:
    """Strict lookup for one language while rendering. English reads the source catalog; any other language
    reads only renderable units and approved glossary terms, and raises Untranslated otherwise (no English
    fallback). Every id looked up is recorded, so a page's required units are exactly those it used."""

    def __init__(self, lang, root=ROOT, evidence=None, ontology=None, gaps=None, today=None):
        self.lang, self.used, self.terms_used = lang, [], []
        self.english = english_messages(root)
        catalog = _load(Path(root) / "i18n" / "en" / "messages.json")["messages"]
        self.term_links = {m["id"]: m["term"] for m in catalog if "term" in m}
        self.kinds = {m["id"]: m["kind"] for m in catalog}
        if lang == "en":
            self.texts, self.terms = self.english, None
        else:
            self.texts = renderable_texts(lang, root, evidence, ontology, gaps, today)
            self.terms = approved_terms(lang, root, today)

    def template(self, message_id):
        self.used.append(message_id)
        if message_id not in self.texts:
            if message_id not in self.english:
                raise KeyError(f"unknown message id {message_id!r}")
            raise Untranslated(f"{self.lang}: message {message_id!r} has no approved, current translation")
        if self.lang != "en" and message_id in self.term_links:
            self.term(self.term_links[message_id], self.english[message_id])  # terminology must be approved too
        return self.texts[message_id]

    def content(self, unit_id, english):
        """Canonical prose: the canonical English value itself for 'en', else its renderable translation."""
        self.used.append(unit_id)
        if self.lang == "en":
            return english
        if unit_id not in self.texts:
            raise Untranslated(f"{self.lang}: canonical text {unit_id!r} has no approved, current translation")
        return self.texts[unit_id]

    def text(self, message_id, **values):
        return fill(self.template(message_id), values, message_id)

    def term(self, term_id, english):
        """Glossary-controlled label: the canonical English value for 'en', else the approved label."""
        self.terms_used.append(term_id)
        if self.lang == "en":
            return english
        if term_id not in self.terms:
            raise Untranslated(f"{self.lang}: glossary term {term_id!r} has no approved label")
        return self.terms[term_id]


def page_eligibility(lang, unit_ids, root=ROOT, evidence=None, ontology=None, gaps=None):
    """(eligible, missing): a page is generated in `lang` only if the language is published and renderable
    there, and every unit the page needs is renderable. There is no partial page and no English fallback."""
    registry = {x["code"]: x for x in _load(Path(root) / "i18n" / "languages.json")["languages"]}
    lang_entry = registry.get(lang)
    if lang_entry is None or lang_entry["state"] != "published" or lang not in RENDERING_LANGUAGES:
        return False, sorted(unit_ids)
    missing = sorted(set(unit_ids) - renderable_units(lang, root, evidence, ontology, gaps))
    return not missing, missing


if __name__ == "__main__":
    if "--identity-report" in sys.argv:
        for kind, entries in (("changelog", changelog_entries(_load(ROOT / "data" / "changelog.json"))),
                              ("attribute", attribute_entries(_load(ROOT / "data" / "ontology.json")))):
            for line in identity_proposals(kind, entries, _load(ROOT / "i18n" / f"{kind}-identity.json")):
                print(kind.upper(), line)
        print("Proposals only: review them and edit the identity map by hand.")
        sys.exit(0)
    problems, rep = validate()
    for p in problems:
        print("ERROR", p)
    for key in ("stale", "orphaned"):
        for uid in rep[key]:
            print(key.upper(), uid, "(not renderable; English is unaffected)")
    print(f"{len(problems)} problem(s); {len(rep['stale'])} stale, {len(rep['orphaned'])} orphaned translation unit(s)")
    sys.exit(1 if problems else 0)
