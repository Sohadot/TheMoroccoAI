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
UNIT_STATUSES = ("draft", "terminology-checked", "parity-reviewed", "linguistically-reviewed", "approved")
# Every file on main is publicly served, so catalogs on main hold approved units only (Arch §6.3). A
# translation pull request therefore stays red until both reviews are recorded: that is intended.
COMMITTABLE_STATUSES = ("approved",)
KINDS = ("interface", "prose", "qualifier", "disclosure", "term", "name")
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

# Canonical prose a content unit may translate: '<file>:<id>:<field>'.
CONTENT_FIELDS = {
    "evidence": ("title", "claim", "verification_note"),
    "ontology": ("name", "summary", "note"),
    "gaps": ("question", "established", "unestablished", "evidence_needed"),
}
CONTENT_ID = re.compile(r"^(evidence|ontology|gaps):([^:]+):([a-z_]+)$")
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


# ─── Source resolution ────────────────────────────────────────────────────

class Sources:
    """English source text for message ids, canonical content ids and glossary term ids."""

    def __init__(self, root=ROOT, evidence=None, ontology=None, gaps=None):
        root = Path(root)
        self.messages = english_messages(root)
        self.evidence = evidence if evidence is not None else _load(root / "data" / "evidence.json")
        self.ontology = ontology if ontology is not None else _load(root / "data" / "ontology.json")
        self.gaps = gaps if gaps is not None else _load(root / "data" / "gaps.json")
        self.records = {r["evidence_id"]: r for r in self.evidence["records"]}
        self.entities = {e["id"]: e for e in self.ontology["entities"]}
        self.gap_items = {g["id"]: g for g in self.gaps["gaps"]}

    def message(self, unit_id):
        return self.messages.get(unit_id)

    def content(self, unit_id):
        """(text, problem): text is None if the record or field no longer exists (an orphan)."""
        m = CONTENT_ID.match(unit_id)
        if not m:
            return None, "malformed"
        kind, key, field = m.groups()
        if field not in CONTENT_FIELDS[kind]:
            return None, "malformed"
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


def validate_english(catalog):
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


def _review_problems(review, where, today):
    if not isinstance(review, dict):
        return [f"{where}: approved unit has no review record"]
    errors = []
    for key in ("drafted_by", "substantive_reviewer", "linguistic_reviewer"):
        value = review.get(key)
        if not isinstance(value, str) or not PSEUDONYM.match(value):
            errors.append(f"{where}: review.{key} must be a pseudonymous identifier such as 'reviewer-ar-02'")
    drafter = review.get("drafted_by")
    for key in ("substantive_reviewer", "linguistic_reviewer"):
        if drafter and review.get(key) == drafter:
            errors.append(f"{where}: review.{key} must be independent of the drafter")
    if review.get("draft_method") not in DRAFT_METHODS:
        errors.append(f"{where}: review.draft_method must be one of {list(DRAFT_METHODS)}")
    try:
        approved = datetime.date.fromisoformat(review.get("approved_on", ""))
        if approved > today:
            errors.append(f"{where}: review.approved_on is in the future")
    except (TypeError, ValueError):
        errors.append(f"{where}: review.approved_on must be an ISO date")
    if not isinstance(review.get("glossary_version"), str) or not review["glossary_version"]:
        errors.append(f"{where}: review.glossary_version is required")
    unknown = set(review) - {"drafted_by", "draft_method", "substantive_reviewer", "linguistic_reviewer",
                             "approved_on", "glossary_version"}
    if unknown:
        errors.append(f"{where}: unexpected review fields {sorted(unknown)} (no personal data in a public file)")
    return errors


def validate_catalog(lang, kind, catalog, sources, forbidden, today):
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
            errors.append(f"{where}: unknown status {u.get('status')!r}")
        elif u["status"] not in COMMITTABLE_STATUSES:
            errors.append(f"{where}: status {u['status']!r} is not publishable; drafts stay off main")
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
        if u.get("status") == "approved":
            errors += _review_problems(u.get("review"), where, today)
        if problem == "orphan":
            report["orphaned"].append(f"{lang}:{uid}")
            continue
        if isinstance(u.get("text"), str):
            errors += _parity_problems(u["text"], source, where)
        if isinstance(u.get("source_sha256"), str) and u["source_sha256"] != fingerprint(source):
            report["stale"].append(f"{lang}:{uid}")
    return errors, report


def validate_glossary(glossary, sources, languages):
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
    targets = [lang["code"] for lang in registry["languages"] if lang["code"] != "en"]
    gerrors, forbidden = validate_glossary(glossary, sources, targets)
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
            cerrors, creport = validate_catalog(lang, kind, catalog, sources, forbidden[lang], today)
            errors += cerrors
            report["stale"] += creport["stale"]
            report["orphaned"] += creport["orphaned"]
    for lang_dir in sorted(p.name for p in base.iterdir() if p.is_dir()):
        if lang_dir != "en" and lang_dir not in targets:
            errors.append(f"i18n/{lang_dir}/: language is not registered in i18n/languages.json")
    return errors, report


# ─── Publication eligibility ─────────────────────────────────────────────

def renderable_texts(lang, root=ROOT, evidence=None, ontology=None, gaps=None, today=None):
    """{id: text} of the units in `lang` that may be rendered. A unit is renderable only if it is approved,
    its review is complete and independent of the drafter, its text passes every text and parity rule, and
    its fingerprint matches the current English source. Stale, orphaned, unapproved or invalid units are never
    renderable (no grace period, Q4), whether or not the validator was run."""
    root = Path(root)
    today = today or datetime.date.today()
    sources = Sources(root, evidence, ontology, gaps)
    out = {}
    for kind in ("messages", "content"):
        path = root / "i18n" / lang / f"{kind}.json"
        if not path.exists():
            continue
        for u in _load(path).get("units", []):
            uid, text = u.get("id"), u.get("text")
            source = sources.message(uid) if kind == "messages" else sources.content(uid or "")[0]
            if (source is None or u.get("status") != "approved" or u.get("source_sha256") != fingerprint(source)
                    or _review_problems(u.get("review"), uid, today) or _text_problems(text, uid)
                    or _parity_problems(text, source, uid)):
                continue
            out[uid] = text
    return out


def renderable_units(lang, root=ROOT, evidence=None, ontology=None, gaps=None, today=None):
    return set(renderable_texts(lang, root, evidence, ontology, gaps, today))


def approved_terms(lang, root=ROOT):
    """{term id: label} of glossary terms with an approved, well-formed label in `lang`."""
    out = {}
    for term in _load(Path(root) / "i18n" / "glossary.json").get("terms", []):
        entry = term.get("translations", {}).get(lang)
        if entry and entry.get("status") in COMMITTABLE_STATUSES and not _text_problems(entry.get("label"), "") \
                and not any(v and v.lower() in entry["label"].lower() for v in entry.get("forbidden", [])):
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
        if lang == "en":
            self.texts, self.terms = self.english, None
        else:
            self.texts = renderable_texts(lang, root, evidence, ontology, gaps, today)
            self.terms = approved_terms(lang, root)

    def template(self, message_id):
        self.used.append(message_id)
        if message_id not in self.texts:
            if message_id not in self.english:
                raise KeyError(f"unknown message id {message_id!r}")
            raise Untranslated(f"{self.lang}: message {message_id!r} has no approved, current translation")
        return self.texts[message_id]

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
    problems, rep = validate()
    for p in problems:
        print("ERROR", p)
    for key in ("stale", "orphaned"):
        for uid in rep[key]:
            print(key.upper(), uid, "(not renderable; English is unaffected)")
    print(f"{len(problems)} problem(s); {len(rep['stale'])} stale, {len(rep['orphaned'])} orphaned translation unit(s)")
    sys.exit(1 if problems else 0)
