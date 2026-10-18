"""Load and validate the evidence registry and ontology.

Standard library only. `validate(evidence, ontology)` returns a list of error
strings; an empty list means both files are consistent.
"""
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = ROOT / "data" / "evidence.json"
ONTOLOGY_PATH = ROOT / "data" / "ontology.json"

CLASSIFICATIONS = (
    "VERIFIED FACT",
    "OFFICIAL TARGET",
    "ANNOUNCED PLAN",
    "INDEPENDENT ANALYSIS",
    "UNVERIFIED CLAIM",
)
VERIFICATION_STATUSES = ("verified", "partial")
SOURCE_TYPES = (
    "government_portal",
    "government_publication",
    "state_news_agency",
    "signatory_organization",
    "intergovernmental_organization",
    "regulator",
    "organization_website",
    "technical_repository",
    "academic_preprint",
    "investor_publication",
    "independent_list",
    "secondary_press",
)
# Self-published or secondary sources: they cannot alone establish that something is operational.
NON_INDEPENDENT_SOURCES = ("organization_website", "secondary_press")
EVIDENCE_TYPES = (
    "news_dispatch",
    "official_report",
    "official_statement",
    "official_announcement",
    "press_release",
    "regulatory_page",
    "model_card",
    "dataset_card",
    "preprint",
    "organization_page",
    "case_study",
    "ranking_entry",
    "press_article",
)
REQUIRED_EVIDENCE_FIELDS = (
    "evidence_id", "title", "source_organization", "source_type", "source_url",
    "source_language", "publication_date", "retrieval_date", "evidence_type",
    "claim", "source_excerpts", "classification", "verification_status",
    "verification_note", "related_entities",
)
# Entity types that must be backed by at least one record and carry a domain.
DOCUMENTED_TYPES = ("institution", "company", "initiative", "event", "project", "legal_instrument", "model", "dataset")
LIFECYCLE_TYPES = ("project", "model", "dataset")
# Which lifecycle stages each type may take, and which record classes can support each stage.
LIFECYCLE_ALLOWED = {
    "project": ("announced", "in-development", "pilot", "operational", "discontinued"),
    "model": ("announced", "in-development", "released", "discontinued"),
    "dataset": ("announced", "in-development", "released", "discontinued"),
}
# Stages that need a record explicitly declaring that status (status_evidence); a signature,
# presentation or announcement record never declares one, so it cannot establish delivery.
STATUS_STAGES = ("in-development", "pilot", "operational", "released", "discontinued")
PROJECT_KINDS_REQUIRED = ("project",)
# Origins that need a source independent of the company itself.
INDEPENDENT_ORIGINS = ("based-in-morocco", "foreign-moroccan-operations-verified")
LIFECYCLE_SUPPORT = {
    "announced": {"ANNOUNCED PLAN", "VERIFIED FACT"},
    "in-development": {"VERIFIED FACT"},
    "pilot": {"VERIFIED FACT"},
    "operational": {"VERIFIED FACT"},
    "released": {"VERIFIED FACT"},
    "discontinued": {"VERIFIED FACT"},
}

EVIDENCE_ID = re.compile(r"^MAI-EV-\d{4}$")
ENTITY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KEY = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}(?:-\d{2})?$")
# Wording that describes something not yet true; a VERIFIED FACT must not use it.
FORWARD_LOOKING = re.compile(
    r"\b(aims?|aiming|target(?:s|ed)?|will|plans?|planned|intends?|objectives?|by 20\d\d)\b",
    re.IGNORECASE,
)
# Wording that presents an outcome as achieved; targets and plans must not use it.
ACHIEVED = re.compile(r"\b(achieved|has reached|have reached|completed|accomplished)\b", re.IGNORECASE)
# The relationship classification must be supported by at least one record of these classes.
RELATION_SUPPORT = {
    "VERIFIED FACT": {"VERIFIED FACT"},
    "OFFICIAL TARGET": {"OFFICIAL TARGET"},
    "ANNOUNCED PLAN": {"ANNOUNCED PLAN", "VERIFIED FACT", "OFFICIAL TARGET"},
    "UNVERIFIED CLAIM": {"UNVERIFIED CLAIM"},
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all():
    return load(EVIDENCE_PATH), load(ONTOLOGY_PATH)


def _parse_date(value):
    """Return a date for YYYY-MM-DD or YYYY-MM (first of month), or None if not a real calendar date."""
    if not isinstance(value, str) or not DATE.match(value):
        return None
    parts = [int(p) for p in value.split("-")]
    try:
        return datetime.date(parts[0], parts[1], parts[2] if len(parts) > 2 else 1)
    except ValueError:
        return None


def _check_url(url):
    if not isinstance(url, str) or url != url.strip() or re.search(r"\s", url):
        return "contains whitespace or is not a string"
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return "must use https"
    if not parsed.netloc or "." not in parsed.netloc:
        return "has no valid host"
    if parsed.netloc.endswith("themoroccoai.com"):
        return "must point to the original source, not to this site"
    return None


def validate_evidence(evidence, today=None):
    errors = []
    today = today or datetime.date.today()
    as_of = _parse_date(evidence.get("as_of"))
    if not as_of or len(evidence.get("as_of")) != 10:
        errors.append("evidence.json: as_of missing or not a valid YYYY-MM-DD date")
    records = evidence.get("records") or []
    if not records:
        errors.append("evidence.json: registry has no records")
    seen = set()
    for i, r in enumerate(records):
        rid = r.get("evidence_id", f"records[{i}]")
        where = f"{rid}:"
        for field in REQUIRED_EVIDENCE_FIELDS:
            if field not in r:
                errors.append(f"{where} missing field '{field}'")
        if not EVIDENCE_ID.match(str(r.get("evidence_id", ""))):
            errors.append(f"{where} evidence_id must match MAI-EV-NNNN")
        if rid in seen:
            errors.append(f"{where} duplicate evidence_id")
        seen.add(rid)
        for field in ("title", "source_organization", "claim"):
            if not str(r.get(field, "")).strip():
                errors.append(f"{where} '{field}' is empty")
        problem = _check_url(r.get("source_url"))
        if problem:
            errors.append(f"{where} source_url {problem}")
        if r.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{where} unknown source_type {r.get('source_type')!r}")
        if r.get("evidence_type") not in EVIDENCE_TYPES:
            errors.append(f"{where} unknown evidence_type {r.get('evidence_type')!r}")
        retrieval = _parse_date(r.get("retrieval_date"))
        if not retrieval or len(r.get("retrieval_date")) != 10:
            errors.append(f"{where} retrieval_date must be a valid YYYY-MM-DD date")
            retrieval = None
        elif retrieval > today:
            errors.append(f"{where} retrieval_date is in the future")
        elif as_of and retrieval > as_of:
            errors.append(f"{where} retrieval_date is after the registry as_of date")
        pub = r.get("publication_date")
        if pub is not None:
            pub_date = _parse_date(pub)
            if not pub_date:
                errors.append(f"{where} publication_date must be a valid YYYY-MM-DD, YYYY-MM or null")
            elif retrieval and pub_date > retrieval:
                errors.append(f"{where} publication_date is after retrieval_date")
        elif not str(r.get("verification_note", "")).strip():
            errors.append(f"{where} null publication_date needs a verification_note")
        excerpts = r.get("source_excerpts")
        if not isinstance(excerpts, list) or not excerpts or not all(str(e).strip() for e in excerpts):
            errors.append(f"{where} needs at least one non-empty source excerpt")
        if not isinstance(r.get("related_entities"), list) or not r.get("related_entities"):
            errors.append(f"{where} needs at least one related entity")

        cls = r.get("classification")
        status = r.get("verification_status")
        claim = str(r.get("claim", ""))
        if cls not in CLASSIFICATIONS:
            errors.append(f"{where} unknown classification {cls!r}")
        if status not in VERIFICATION_STATUSES:
            errors.append(f"{where} unknown verification_status {status!r}")
        if status == "partial" and not str(r.get("verification_note", "")).strip():
            errors.append(f"{where} partial verification needs a verification_note")
        if cls == "INDEPENDENT ANALYSIS":
            errors.append(f"{where} INDEPENDENT ANALYSIS belongs on relationships, not on sourced records")
        if cls == "VERIFIED FACT" and FORWARD_LOOKING.search(claim):
            errors.append(f"{where} VERIFIED FACT claim uses forward-looking wording "
                          f"({FORWARD_LOOKING.search(claim).group(0)!r}); classify it as OFFICIAL TARGET or ANNOUNCED PLAN")
        if cls in ("OFFICIAL TARGET", "ANNOUNCED PLAN") and ACHIEVED.search(claim):
            errors.append(f"{where} {cls} claim presents an outcome as achieved")
        if cls == "OFFICIAL TARGET" and not isinstance(r.get("target_year"), int):
            errors.append(f"{where} OFFICIAL TARGET needs an integer target_year")
        status = r.get("status_evidence")
        if status is not None:
            if status not in STATUS_STAGES:
                errors.append(f"{where} unknown status_evidence {status!r}")
            if cls != "VERIFIED FACT":
                errors.append(f"{where} status_evidence requires a VERIFIED FACT record")
            if status == "released" and r.get("source_type") != "technical_repository":
                errors.append(f"{where} 'released' must be evidenced by the technical repository itself")
            if status in ("operational", "pilot") and r.get("source_type") in NON_INDEPENDENT_SOURCES:
                errors.append(f"{where} '{status}' cannot be evidenced by the actor's own website or press")
        if r.get("source_type") == "secondary_press" and cls not in ("ANNOUNCED PLAN", "UNVERIFIED CLAIM"):
            errors.append(f"{where} secondary press can support only ANNOUNCED PLAN or UNVERIFIED CLAIM, not {cls}")
        if cls == "UNVERIFIED CLAIM" and not str(r.get("verification_note", "")).strip():
            errors.append(f"{where} UNVERIFIED CLAIM needs a verification_note saying what was not checked")
    return errors


def _check_entity_facets(e, where, ev, records, stages, origins, kinds=None):
    """Lifecycle, origin and attributes: each must be allowed for the type and backed by the entity's own evidence."""
    errors = []
    etype = e.get("type")
    stage = e.get("lifecycle")
    if etype in LIFECYCLE_TYPES:
        if stage not in stages or stage not in LIFECYCLE_ALLOWED[etype]:
            errors.append(f"{where} {etype} needs a lifecycle from {', '.join(LIFECYCLE_ALLOWED[etype])} (got {stage!r})")
        basis = e.get("lifecycle_evidence") or []
        if not basis:
            errors.append(f"{where} lifecycle needs lifecycle_evidence")
        if any(x not in ev for x in basis):
            errors.append(f"{where} lifecycle_evidence must be a subset of the entity's evidence")
        cited = [records[x] for x in basis if x in records]
        if stage in LIFECYCLE_SUPPORT and not any(r.get("classification") in LIFECYCLE_SUPPORT[stage] for r in cited):
            errors.append(f"{where} lifecycle '{stage}' is not supported by a {' or '.join(sorted(LIFECYCLE_SUPPORT[stage]))} record")
        if stage in STATUS_STAGES and not any(r.get("status_evidence") == stage for r in cited):
            errors.append(f"{where} lifecycle '{stage}' needs a lifecycle_evidence record whose status_evidence is '{stage}'")
        if stage == "operational" and not any(
                r.get("classification") == "VERIFIED FACT" and r.get("source_type") not in NON_INDEPENDENT_SOURCES for r in cited):
            errors.append(f"{where} 'operational' needs a verified record from a source other than the actor's own website or press")
    elif "lifecycle" in e or "lifecycle_evidence" in e:
        errors.append(f"{where} {etype} entities take no lifecycle")
    kinds = kinds or {}
    if etype in PROJECT_KINDS_REQUIRED:
        if e.get("project_kind") not in kinds:
            errors.append(f"{where} project needs a project_kind from {', '.join(kinds)} (got {e.get('project_kind')!r})")
    elif "project_kind" in e:
        errors.append(f"{where} only projects take a project_kind")
    origin = e.get("origin")
    if etype == "company":
        if origin not in origins:
            errors.append(f"{where} company needs an origin from {', '.join(origins)} (got {origin!r})")
        basis = e.get("origin_evidence") or []
        if origin != "unresolved" and not basis:
            errors.append(f"{where} origin '{origin}' needs origin_evidence")
        if any(x not in ev for x in basis):
            errors.append(f"{where} origin_evidence must be a subset of the entity's evidence")
        name = str(e.get("name", "")).casefold()
        independent = [r for r in (records.get(x, {}) for x in basis)
                       if r.get("source_type") not in NON_INDEPENDENT_SOURCES
                       and not str(r.get("source_organization", "")).casefold().startswith(name)]
        if origin in INDEPENDENT_ORIGINS and not independent:
            errors.append(f"{where} origin '{origin}' needs origin_evidence from a source independent of the company")
    elif "origin" in e or "origin_evidence" in e:
        errors.append(f"{where} only company entities take an origin")
    for a in e.get("attributes") or []:
        if not str(a.get("name", "")).strip() or not str(a.get("value", "")).strip():
            errors.append(f"{where} attribute needs a name and a value")
        if a.get("evidence") not in ev:
            errors.append(f"{where} attribute '{a.get('name')}' must cite one of the entity's own records")
    return errors


def validate_ontology(ontology, evidence):
    errors = []
    records = {r.get("evidence_id"): r for r in evidence.get("records") or []}
    types = ontology.get("entity_types") or {}
    domains = ontology.get("domains") or {}
    predicates = ontology.get("predicates") or {}
    entities = ontology.get("entities") or []
    if not entities:
        errors.append("ontology.json: no entities")
    # Keys are written into HTML ids and URLs by the generator, so they must be plain slugs.
    stages = ontology.get("lifecycle_stages") or {}
    origins = ontology.get("origins") or {}
    for kind, keys in (("domain", domains), ("entity type", types), ("predicate", predicates),
                       ("lifecycle stage", stages), ("origin", origins),
                       ("project kind", ontology.get("project_kinds") or {})):
        for k in keys:
            if not KEY.match(str(k)):
                errors.append(f"ontology.json: {kind} key {k!r} must be a lowercase slug")

    by_id = {}
    for i, e in enumerate(entities):
        eid = e.get("id", f"entities[{i}]")
        where = f"entity {eid}:"
        if not ENTITY_ID.match(str(e.get("id", ""))):
            errors.append(f"{where} id must be lowercase kebab-case")
        if eid in by_id:
            errors.append(f"{where} duplicate entity id")
        by_id[eid] = e
        if e.get("type") not in types:
            errors.append(f"{where} unknown type {e.get('type')!r}")
        if not str(e.get("name", "")).strip() or not str(e.get("summary", "")).strip():
            errors.append(f"{where} needs a name and a summary")
        if e.get("type") in DOCUMENTED_TYPES:
            if e.get("domain") not in domains:
                errors.append(f"{where} unknown or missing domain {e.get('domain')!r}")
        elif "domain" in e:
            errors.append(f"{where} {e.get('type')} entities are cross-cutting and take no domain")
        ev = e.get("evidence") or []
        if not ev:
            errors.append(f"{where} has no supporting evidence")
        errors += _check_entity_facets(e, where, ev, records, stages, origins, ontology.get("project_kinds"))
        for x in ev:
            if x not in records:
                errors.append(f"{where} cites missing evidence {x}")
            elif eid not in records[x].get("related_entities", []):
                errors.append(f"{where} cites {x}, but {x} does not list it in related_entities")

    for rid, r in records.items():
        for x in r.get("related_entities") or []:
            if x not in by_id:
                errors.append(f"{rid}: related entity '{x}' does not exist in ontology.json")
            elif rid not in (by_id[x].get("evidence") or []):
                errors.append(f"{rid}: lists '{x}', but that entity does not cite {rid}")

    seen = set()
    for i, rel in enumerate(ontology.get("relationships") or []):
        s, p, o = rel.get("subject"), rel.get("predicate"), rel.get("object")
        where = f"relationship {s} {p} {o}:"
        key = (s, p, o)
        if key in seen:
            errors.append(f"{where} duplicate relationship")
        seen.add(key)
        if s not in by_id or o not in by_id:
            errors.append(f"{where} references a missing entity")
            continue
        spec = predicates.get(p)
        if not spec:
            errors.append(f"{where} unknown predicate")
            continue
        if by_id[s].get("type") not in spec["subject"] or by_id[o].get("type") not in spec["object"]:
            errors.append(f"{where} predicate does not accept {by_id[s].get('type')} → {by_id[o].get('type')}")
        cls = rel.get("classification")
        if cls not in CLASSIFICATIONS:
            errors.append(f"{where} unknown classification {cls!r}")
        ev = rel.get("evidence") or []
        if not ev:
            errors.append(f"{where} has no supporting evidence")
        for x in ev:
            if x not in records:
                errors.append(f"{where} cites missing evidence {x}")
            elif not {s, o} & set(records[x].get("related_entities", [])):
                errors.append(f"{where} cites {x}, which documents neither end of the relationship")
        cited = {records[x].get("classification") for x in ev if x in records}
        if cls == "INDEPENDENT ANALYSIS":
            if len(ev) < 2 or not str(rel.get("note", "")).strip():
                errors.append(f"{where} INDEPENDENT ANALYSIS needs a note and at least two records")
        elif cls in RELATION_SUPPORT and not cited & RELATION_SUPPORT[cls]:
            errors.append(f"{where} classified {cls} but no cited record supports that class "
                          f"(cited: {', '.join(sorted(c for c in cited if c))})")
    return errors


def validate(evidence, ontology, today=None):
    return validate_evidence(evidence, today) + validate_ontology(ontology, evidence)


if __name__ == "__main__":
    import sys
    problems = validate(*load_all())
    for p in problems:
        print("ERROR", p)
    print(f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
