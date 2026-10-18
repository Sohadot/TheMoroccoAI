"""Generate the public registry pages from data/evidence.json and data/ontology.json.

    python3 tools/build.py          validate, then write all generated files
    python3 tools/build.py --check  validate, then fail if any generated file is stale

Generated outputs (committed, because GitHub Pages serves the repository as-is):
    registry/index.html, registry/evidence/index.html, registry/<entity-id>/index.html,
    sitemap.xml, and the marked blocks inside index.html.
Standard library only.
"""
import datetime
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402

ROOT = registry.ROOT
SITE = "https://themoroccoai.com"
CONTACT = "agent@sohadot.com"
TYPE_LABELS = {
    "institution": "Institutions",
    "company": "Companies",
    "initiative": "Initiatives",
    "event": "Events",
    "project": "Projects",
    "legal_instrument": "Legal instruments",
    "model": "Models",
    "dataset": "Datasets",
    "technology": "Technologies",
    "sector": "Sectors",
}
TYPE_SINGULAR = {
    "institution": "Institution", "initiative": "Initiative", "event": "Event", "project": "Project",
    "legal_instrument": "Legal instrument", "technology": "Technology", "sector": "Sector",
    "company": "Company", "model": "Model", "dataset": "Dataset",
}
LIFECYCLE_LABELS = {
    "announced": "Announced", "in-development": "In development", "pilot": "Pilot",
    "operational": "Operational", "released": "Released", "discontinued": "Discontinued",
    "unresolved": "Unresolved",
}
ORIGIN_LABELS = {
    "based-in-morocco": "Based in Morocco (independent source)",
    "self-described-moroccan": "Self-described Moroccan",
    "foreign-moroccan-subsidiary-reported": "Moroccan subsidiary reported (secondary press)",
    "foreign-moroccan-operations-verified": "Foreign, Moroccan operations verified",
    "unresolved": "Unresolved",
}
KIND_LABELS = {
    "ai-application": "AI application", "compute-infrastructure": "Compute infrastructure",
    "institute": "Institute", "agreement": "Agreement", "digital-platform": "Digital platform (not AI)",
}
SOURCE_TYPE_LABELS = {
    "government_portal": "Government portal",
    "government_publication": "Government publication",
    "state_news_agency": "State news agency",
    "signatory_organization": "Signatory organisation",
    "intergovernmental_organization": "Intergovernmental organisation",
    "regulator": "Regulator",
    "organization_website": "Organisation's own website",
    "technical_repository": "Technical repository",
    "academic_preprint": "Academic preprint",
    "investor_publication": "Investor publication",
    "independent_list": "Independent list",
    "secondary_press": "Secondary press",
}
SIGIL = ('<svg viewBox="0 0 28 28" fill="none" aria-hidden="true" focusable="false">'
         '<polygon points="14,2 26,8 26,20 14,26 2,20 2,8" stroke="#1a2e4a" stroke-width="1" fill="none"/>'
         '<polygon points="14,7 21,10.5 21,17.5 14,21 7,17.5 7,10.5" stroke="#b8892a" stroke-width="0.75" fill="none"/>'
         '<circle cx="14" cy="14" r="2.5" fill="#b8892a"/></svg>')


STATUS_BASIS_LABELS = {
    "public-availability-observed": "public availability on the operator's own service (usage not documented)",
    "operator-report-of-use": "operator's report of use",
    "independent-listing": "independent listing",
    "independent-report-of-use": "independent report of use",
}
# Evidence-recency convention, not a lifecycle rule: operational or pilot evidence whose latest record is
# more than this many calendar months before the registry's as-of date is flagged as not reconfirmed.
# Elapsed time never changes a lifecycle stage; only a record declaring a new status can.
RECENCY_MONTHS = 12


def slug(classification):
    return classification.lower().replace(" ", "-")


def badge(classification):
    return f'<span class="badge badge-{slug(classification)}">{escape(classification)}</span>'


def human_date(value):
    if not value:
        return "Not stated"
    parts = value.split("-")
    d = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 1)
    return d.strftime("%-d %B %Y") if len(parts) > 2 else d.strftime("%B %Y")


def entity_url(eid):
    return f"/registry/{eid}/"


class Model:
    def __init__(self, evidence, ontology):
        self.evidence = evidence
        self.ontology = ontology
        self.records = {r["evidence_id"]: r for r in evidence["records"]}
        self.entities = {e["id"]: e for e in ontology["entities"]}
        self.relationships = ontology["relationships"]
        self.predicates = ontology["predicates"]
        self.domains = ontology["domains"]
        self.as_of = evidence["as_of"]

    def relations_of(self, eid):
        rows = []
        for rel in self.relationships:
            spec = self.predicates[rel["predicate"]]
            if rel["subject"] == eid:
                rows.append((spec["label"], rel["object"], rel))
            elif rel["object"] == eid:
                rows.append((spec["inverse"], rel["subject"], rel))
        return rows

    def by_type(self, etype):
        return sorted((e for e in self.ontology["entities"] if e["type"] == etype), key=lambda e: e["name"].lower())

    def counts(self):
        cls = {c: 0 for c in registry.CLASSIFICATIONS}
        for r in self.evidence["records"]:
            cls[r["classification"]] += 1
        for rel in self.relationships:
            if rel["classification"] == "INDEPENDENT ANALYSIS":
                cls["INDEPENDENT ANALYSIS"] += 1
        return cls


# ─── PAGE SHELL ────────────────────────────────────────────────────────────

def page(model, *, path, title, description, body, jsonld=None, current=""):
    canonical = SITE + path
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, indent=1).replace("</", "<\\/") + "</script>\n"

    def nav_link(href, label, key, cls=""):
        cur = ' aria-current="page"' if key == current else ""
        c = f' class="{cls}"' if cls else ""
        return f'<li><a href="{href}"{c}{cur}>{label}</a></li>'

    return f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="TheMoroccoAI">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<link rel="stylesheet" href="/assets/registry.css">
{ld}</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<div class="zellige-bg" aria-hidden="true"></div>
<nav class="site-nav" aria-label="Primary">
  <a class="nav-mark" href="/">{SIGIL}<span class="nav-name">TheMoroccoAI</span></a>
  <ul class="nav-links">
    {nav_link("/registry/", "Registry", "registry")}
    {nav_link("/registry/questions/", "Questions", "questions", "nav-optional")}
    {nav_link("/registry/evidence/", "Evidence", "evidence", "nav-optional")}
    {nav_link("/#acquire", "Acquire", "acquire", "nav-acquire")}
  </ul>
</nav>
<main id="content">
<div class="page">
{body}
</div>
</main>
<footer>
  <div class="footer-inner">
    <span class="footer-brand">TheMoroccoAI.com · Independent reference infrastructure</span>
    <span class="footer-note">Not affiliated with the Government of Morocco · Registry v{escape(model.evidence["version"])} · as of {escape(human_date(model.as_of))}</span>
  </div>
</footer>
</body>
</html>
"""


def evidence_card(model, r, *, heading="h3", show_entities=True):
    rid = r["evidence_id"]
    quotes = "".join(f"<p>“{escape(q)}”</p>" for q in r["source_excerpts"])
    lang = r.get("source_language", "en")
    quote_lang = f' lang="{escape(lang)}"' if lang != "en" else ""
    target = f'<dt>Target year</dt><dd>{r["target_year"]}</dd>' if r.get("target_year") else ""
    status = r["verification_status"]
    status_html = "Verified against source" if status == "verified" else '<span class="badge badge-partial">Partial verification</span>'
    entities = ""
    if show_entities:
        links = ", ".join(
            f'<a href="{entity_url(e)}">{escape(model.entities[e]["name"])}</a>' for e in r["related_entities"]
        )
        entities = f"<dt>Related</dt><dd>{links}</dd>"
    note = f'<p class="evidence-note">{escape(r["verification_note"])}</p>' if r["verification_note"] else ""
    caveats = ""
    if r.get("superseded_by"):
        later = ", ".join(f'<a href="/registry/evidence/#{x}">{x}</a>' for x in r["superseded_by"])
        caveats += f"<dt>Superseded</dt><dd>The quotation still matches its source, but the claim is no longer current; see {later}.</dd>"
    if r.get("associated_entities"):
        names = ", ".join(f'<a href="{entity_url(e)}">{escape(model.entities[e]["name"])}</a>' for e in r["associated_entities"])
        caveats += f"<dt>Identity</dt><dd>Associated with {names} by name and other indicators; not established as the same legal entity.</dd>"
    return f"""<li class="evidence-card" id="{rid}">
  <div class="evidence-top"><a class="evidence-id" href="/registry/evidence/#{rid}">{rid}</a>{badge(r["classification"])}</div>
  <{heading}>{escape(r["title"])}</{heading}>
  <p class="evidence-claim">{escape(r["claim"])}</p>
  <blockquote class="evidence-quote"{quote_lang} cite="{escape(r["source_url"])}">{quotes}</blockquote>
  <dl class="evidence-meta">
    <dt>Source</dt><dd><a href="{escape(r["source_url"])}" rel="noopener">{escape(r["source_organization"])}</a> · {escape(SOURCE_TYPE_LABELS[r["source_type"]])}</dd>
    <dt>Published</dt><dd>{escape(human_date(r["publication_date"]))}</dd>
    <dt>Retrieved</dt><dd>{escape(human_date(r["retrieval_date"]))}</dd>{target}
    <dt>Verification</dt><dd>{status_html}</dd>{entities}{caveats}
  </dl>
  {note}
</li>"""


# ─── PAGES ────────────────────────────────────────────────────────────────

def render_entity(model, e):
    eid = e["id"]
    rels = model.relations_of(eid)
    rel_items = []
    for label, other_id, rel in sorted(rels, key=lambda x: (x[0], model.entities[x[1]]["name"].lower())):
        other = model.entities[other_id]
        ev_links = " ".join(
            f'<a href="{"" if x in e["evidence"] else "/registry/evidence/"}#{x}">{x}</a>' for x in rel["evidence"]
        )
        note = f'<span class="rel-note">{escape(rel["note"])}</span>' if rel.get("note") else ""
        rel_items.append(
            f'<li><span class="rel-predicate">{escape(label)}</span>'
            f'<span class="rel-target"><a href="{entity_url(other_id)}">{escape(other["name"])}</a></span>'
            f'<span class="rel-type">{escape(TYPE_SINGULAR[other["type"]])}</span>'
            f'{badge(rel["classification"])}<span class="rel-evidence">{ev_links}</span>{note}</li>'
        )
    relations_html = (f'<ul class="relations">{"".join(rel_items)}</ul>' if rel_items
                      else '<p class="prose">No relationship to another entity is documented yet.</p>')
    records = sorted((model.records[x] for x in e["evidence"]),
                     key=lambda r: (r["publication_date"] or "", r["evidence_id"]), reverse=True)
    cards = "\n".join(evidence_card(model, r) for r in records)

    def cite(ids):
        return " ".join(f'<a class="rel-evidence" href="#{x}">{x}</a>' for x in ids)

    # Values are pre-escaped HTML.
    facts = [("Type", escape(TYPE_SINGULAR[e["type"]]))]
    if e.get("domain"):
        facts.append(("Domain", escape(model.domains[e["domain"]])))
    if e.get("project_kind"):
        facts.append(("Kind", escape(KIND_LABELS[e["project_kind"]])))
    if e.get("lifecycle"):
        facts.append(("Lifecycle", f'{escape(stage_label(model, e))} · {cite(e["lifecycle_evidence"])}'))
    if e.get("origin"):
        basis = f' · {cite(e["origin_evidence"])}' if e.get("origin_evidence") else ""
        facts.append(("Origin", f'{escape(ORIGIN_LABELS[e["origin"]])}{basis}'))
    if e.get("status"):
        facts.append(("Status", escape(e["status"])))
    for a in e.get("attributes") or []:
        facts.append((escape(a["name"]), f'{escape(a["value"])} · {cite([a["evidence"]])}'))
    facts.append(("Identifier", f"<code>{escape(eid)}</code>"))
    facts.append(("Records", str(len(e["evidence"]))))
    facts_html = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts)
    alt = f'<p class="alt-names">{escape(" · ".join(e["alt_names"]))}</p>' if e.get("alt_names") else ""
    note = f'<p class="notice"><strong>Note.</strong> {escape(e["note"])}</p>' if e.get("note") else ""

    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / {escape(TYPE_LABELS[e["type"]])}</p>
  <p class="label">{escape(TYPE_SINGULAR[e["type"]])}{" · " + escape(model.domains[e["domain"]]) if e.get("domain") else ""}</p>
  <h1>{escape(e["name"])}</h1>
  {alt}
  <p class="lede">{escape(e["summary"])}</p>
  {note}
  <dl class="facts">{facts_html}</dl>
</header>
<section aria-labelledby="rel-h">
  <h2 id="rel-h"><span class="section-number">01</span>Documented relationships</h2>
  {relations_html}
</section>
<section aria-labelledby="ev-h">
  <h2 id="ev-h"><span class="section-number">02</span>Evidence</h2>
  <ul class="evidence-list">
{cards}
  </ul>
</section>
<section aria-labelledby="data-h">
  <h2 id="data-h"><span class="section-number">03</span>Machine-readable</h2>
  <p class="prose">This entity is <code>{escape(eid)}</code> in <a href="/data/ontology.json">/data/ontology.json</a>. Its records are in <a href="/data/evidence.json">/data/evidence.json</a>. The same data is embedded in this page as JSON-LD.</p>
</section>"""

    schema_type = {
        "institution": "Organization", "company": "Organization", "initiative": "Project", "project": "Project",
        "event": "Event", "model": "SoftwareApplication", "dataset": "Dataset",
        "legal_instrument": "Legislation", "technology": "DefinedTerm", "sector": "DefinedTerm",
    }[e["type"]]
    jsonld = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "@id": SITE + entity_url(eid),
        "name": e["name"],
        "description": e["summary"],
        "url": SITE + entity_url(eid),
        "identifier": eid,
        "subjectOf": [
            {"@type": "CreativeWork", "name": r["title"], "url": r["source_url"],
             "publisher": {"@type": "Organization", "name": r["source_organization"]},
             **({"datePublished": r["publication_date"]} if r["publication_date"] else {})}
            for r in records
        ],
    }
    if e.get("alt_names"):
        jsonld["alternateName"] = e["alt_names"]
    if e["type"] == "event":
        jsonld.update({"startDate": e["start_date"], "endDate": e["end_date"],
                       "location": {"@type": "Place", "name": e["location"]}})
    if schema_type == "DefinedTerm":
        jsonld["inDefinedTermSet"] = SITE + "/registry/"

    title = f"{e['name']} — TheMoroccoAI Registry"
    desc = e["summary"] if len(e["summary"]) <= 200 else e["summary"][:197].rsplit(" ", 1)[0] + "…"
    if len(desc) < 80:
        desc += f" {TYPE_SINGULAR[e['type']]} entry in TheMoroccoAI's evidence-backed registry of Morocco's AI ecosystem."
    return page(model, path=entity_url(eid), title=title, description=desc, body=body, jsonld=jsonld)


def render_registry_index(model):
    counts = model.counts()
    n_rec, n_ent, n_rel = len(model.records), len(model.entities), len(model.relationships)
    legend = "".join(
        f'<div class="legend-row">{badge(c)}<span class="legend-def">{escape(model.evidence["classifications"][c])}</span>'
        f'<span class="legend-count">{counts[c]}</span></div>'
        for c in registry.CLASSIFICATIONS
    )

    coverage = []
    for key, label in model.domains.items():
        members = sorted((e for e in model.ontology["entities"] if e.get("domain") == key), key=lambda e: e["name"].lower())
        if members:
            recs = {x for e in members for x in e["evidence"]}
            items = "".join(f'<li><a href="{entity_url(e["id"])}">{escape(e["name"])}</a></li>' for e in members)
            coverage.append(f'<div class="coverage-cell" id="domain-{key}"><h3>{escape(label)}</h3>'
                            f'<p class="coverage-count">{len(members)} entities · {len(recs)} records</p><ul>{items}</ul></div>')
        else:
            coverage.append(f'<div class="coverage-cell" id="domain-{key}"><h3>{escape(label)}</h3>'
                            f'<p class="coverage-count">0 entities</p>'
                            f'<p class="coverage-gap">No record has been verified for this domain yet. It stays empty rather than holding unsourced entries.</p></div>')

    groups = []
    for etype, label in TYPE_LABELS.items():
        items = []
        for e in model.by_type(etype):
            meta = f'{len(e["evidence"])} record{"s" if len(e["evidence"]) != 1 else ""}'
            status = f'<span class="entity-status">{escape(e["status"])}</span>' if e.get("status") else ""
            items.append(f'<li><a href="{entity_url(e["id"])}">{escape(e["name"])}</a><span class="entity-meta">{meta}</span>{status}</li>')
        if items:
            groups.append(f'<div class="entity-group"><h3>{escape(label)}</h3><ul class="entity-list">{"".join(items)}</ul></div>')

    body = f"""<header class="page-head">
  <p class="label">MAI-REG — Reference Registry v{escape(model.evidence["version"])}</p>
  <h1>Morocco’s AI ecosystem, <em>on the record.</em></h1>
  <p class="lede">Institutions, initiatives and projects in Morocco’s artificial intelligence ecosystem. Every entry is tied to a primary or institutional source, and <strong>facts, official targets, announced plans and our own analysis are labelled separately</strong>.</p>
  <p class="notice"><strong>Independent.</strong> TheMoroccoAI is an independent reference project. It is not affiliated with, endorsed by or operated by the Government of Morocco or any institution listed here. Records quote public sources and link to them; they are not official statements.</p>
  <div class="stats" role="group" aria-label="Registry status">
    <div class="stat"><div class="stat-key">Evidence records</div><div class="stat-val">{n_rec}</div></div>
    <div class="stat"><div class="stat-key">Entities</div><div class="stat-val">{n_ent}</div></div>
    <div class="stat"><div class="stat-key">Relationships</div><div class="stat-val">{n_rel}</div></div>
    <div class="stat"><div class="stat-key">Sources checked</div><div class="stat-val">{escape(human_date(model.as_of))}</div></div>
    <div class="stat"><div class="stat-key">Format</div><div class="stat-val">Static HTML · JSON</div></div>
  </div>
</header>

<section aria-labelledby="start-h">
  <h2 id="start-h"><span class="section-number">01</span>Start here</h2>
  <p class="prose"><a href="/registry/questions/">Questions the registry answers</a> lists which organisations have documented AI activity, which projects are operational or only announced, which models and datasets are public, and which relationships are verified. Each answer links to its evidence.</p>
  <p class="prose">The fullest chain in this version runs from <a href="{entity_url("morocco-ai-2030")}">Morocco AI 2030</a> to the <a href="{entity_url("jazari-network")}">JAZARI Institutes network</a>, its core institute <a href="{entity_url("jazari-root")}">Institut Jazari ROOT</a> and the <a href="{entity_url("jazari-industrie-x0")}">JAZARI Industrie X.0</a> convention signed in Fès. It then goes on to the signatories, the stated technologies and the targeted sectors. Each page shows the source excerpt, the publication and retrieval dates, and the classification of every claim.</p>
</section>

<section aria-labelledby="legend-h">
  <h2 id="legend-h"><span class="section-number">02</span>How claims are classified</h2>
  <div class="legend">{legend}</div>
  <p class="prose" style="margin-top:14px">Counts cover evidence records, plus relationships for independent analysis. An official target is never shown as an outcome. A record marked “partial” states what could not be checked.</p>
</section>

<section aria-labelledby="coverage-h">
  <h2 id="coverage-h"><span class="section-number">03</span>Coverage by domain</h2>
  <div class="coverage">{"".join(coverage)}</div>
</section>

<section aria-labelledby="entities-h">
  <h2 id="entities-h"><span class="section-number">04</span>All entities</h2>
  {"".join(groups)}
</section>

<section aria-labelledby="data-h">
  <h2 id="data-h"><span class="section-number">05</span>Machine-readable data</h2>
  <ul class="data-links">
    <li><a href="/data/evidence.json"><code>/data/evidence.json</code></a>: every evidence record, with its source URL, dates, verbatim excerpts, classification and verification status.</li>
    <li><a href="/data/ontology.json"><code>/data/ontology.json</code></a>: entity types, domains, predicates, entities and typed relationships, each citing its evidence.</li>
    <li><a href="/registry/evidence/">All evidence on one page</a>, each record addressable as <code>/registry/evidence/#MAI-EV-NNNN</code>.</li>
  </ul>
</section>

<section aria-labelledby="method-h">
  <h2 id="method-h"><span class="section-number">06</span>Method and limits</h2>
  <div class="prose">
    <p>Each record was retrieved from its source on the stated retrieval date, and its excerpt was matched against the retrieved text. An automated validator checks every build. It requires unique identifiers, https source URLs, valid dates and complete fields, and that every entity and relationship cites existing evidence. It also blocks forward-looking wording in records classified as fact, and rejects any relationship whose classification its evidence does not support.</p>
    <p>This version is deliberately small. It does not yet cover AI companies, models or datasets, and it omits facts it could not verify against an original source. Corrections can be sent to <a href="mailto:{CONTACT}?subject=TheMoroccoAI%20registry%20correction">{CONTACT}</a>.</p>
  </div>
</section>"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "TheMoroccoAI Evidence Registry",
        "description": "Primary-source evidence records and an ontology of institutions, initiatives and projects in Morocco's AI ecosystem, with claims classified as verified fact, official target, announced plan, independent analysis or unverified claim.",
        "url": SITE + "/registry/",
        "version": model.evidence["version"],
        "dateModified": model.as_of,
        "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "TheMoroccoAI", "url": SITE + "/"},
        "spatialCoverage": {"@type": "Place", "name": "Morocco"},
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE + "/data/evidence.json"},
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE + "/data/ontology.json"},
        ],
    }
    return page(model, path="/registry/", current="registry",
                title="Reference Registry — TheMoroccoAI",
                description="Independent, evidence-backed registry of Morocco's AI ecosystem: institutions, initiatives and projects tied to primary sources, with facts, targets and plans labelled separately.",
                body=body, jsonld=jsonld)


def _ev_links(ids):
    return " ".join(f'<a href="/registry/evidence/#{x}">{x}</a>' for x in ids)


def _ent_link(model, eid):
    return f'<a href="{entity_url(eid)}">{escape(model.entities[eid]["name"])}</a>'


def _table(label, headers, rows, empty):
    if not rows:
        return f'<p class="prose">{escape(empty)}</p>'
    head = "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<p class="table-hint">Scroll the table sideways to see all {len(headers)} columns.</p>'
            f'<div class="table-wrap" role="region" aria-label="{escape(label)}" tabindex="0">'
            f'<table class="qtable"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def _evidence_date(r):
    """Date a status record speaks for: its publication date, or the retrieval date for undated observations."""
    value = r["publication_date"] or r["retrieval_date"]
    parts = [int(x) for x in value.split("-")]
    return datetime.date(parts[0], parts[1], parts[2] if len(parts) > 2 else 1), value, not r["publication_date"]


def _months_before(day, months):
    """The same calendar day `months` earlier (clamped to the month's last day, e.g. 29 Feb -> 28 Feb)."""
    y, m = divmod(day.year * 12 + day.month - 1 - months, 12)
    m += 1
    last = (datetime.date(y + m // 12, m % 12 + 1, 1) - datetime.timedelta(days=1)).day
    return datetime.date(y, m, min(day.day, last))


def stage_label(model, e):
    """Lifecycle label; an operational or pilot stage resting only on observed availability says so."""
    label = LIFECYCLE_LABELS[e["lifecycle"]]
    if e.get("lifecycle") in ("operational", "pilot"):
        bases = {model.records[x].get("status_basis") for x in e.get("lifecycle_evidence") or []
                 if model.records[x].get("status_evidence") == e["lifecycle"]}
        if bases == {"public-availability-observed"}:
            label += " (public availability; use not documented)"
    return label


def deployment_facts(model, e):
    """Operator, provider, sectors, basis and evidence currency for a project, computed from the registry."""
    rels = model.relationships
    operators = [(r["subject"], r["classification"]) for r in rels if r["predicate"] == "operates" and r["object"] == e["id"]]
    sectors = [r["object"] for r in rels if r["predicate"] == "targets" and r["subject"] == e["id"]]
    provider = next((a["value"] for a in e.get("attributes") or [] if a["name"].startswith("Provider")), "")
    status = [model.records[x] for x in e.get("lifecycle_evidence") or [] if model.records[x].get("status_evidence") == e.get("lifecycle")]
    latest = max((_evidence_date(r) for r in status), default=None)
    currency, stale = "", False
    if latest and e.get("lifecycle") in ("operational", "pilot"):
        as_of = datetime.date(*[int(x) for x in model.as_of.split("-")])
        label = f"{human_date(latest[1])}{' (observed)' if latest[2] else ''}"
        stale = latest[0] < _months_before(as_of, RECENCY_MONTHS)
        currency = (f"Latest supporting evidence {label} is more than {RECENCY_MONTHS} months old; current operation has not been reconfirmed"
                    if stale else
                    f"Latest supporting evidence {label}, within {RECENCY_MONTHS} months; operation after that date not reconfirmed")
    bases = sorted({STATUS_BASIS_LABELS[r["status_basis"]] for r in status if r.get("status_basis")})
    return {"operators": operators, "sectors": sectors, "provider": provider, "bases": bases, "currency": currency,
            "stale": stale, "status_ids": [r["evidence_id"] for r in status]}


def render_questions(model):
    rels = model.relationships
    ents = model.entities
    org_types = ("institution", "company")
    activity_preds = ("develops", "hosts", "operates", "created", "invested_in", "signatory_of")

    # Q1: organisations with documented AI activity (verified relationships only, plus every company).
    orgs = {}
    for r in rels:
        if r["predicate"] in activity_preds and r["classification"] == "VERIFIED FACT" and ents[r["subject"]]["type"] in org_types:
            orgs.setdefault(r["subject"], []).append(r)
    for eid, e in ents.items():
        if e["type"] == "company":
            orgs.setdefault(eid, [])
    q1 = []
    for eid in sorted(orgs, key=lambda x: (ents[x]["type"] != "company", ents[x]["name"].lower())):
        e = ents[eid]
        kind = TYPE_SINGULAR[e["type"]]
        if e.get("origin"):
            kind += f" · {ORIGIN_LABELS[e['origin']]}"
        acts = "; ".join(f'{escape(model.predicates[r["predicate"]]["label"])} {_ent_link(model, r["object"])}'
                         for r in orgs[eid]) or "No verified role yet; see entity page."
        ev = sorted({x for r in orgs[eid] for x in r["evidence"]} | set(e.get("origin_evidence") or []))
        q1.append([_ent_link(model, eid), escape(kind), acts, _ev_links(ev)])

    # Q2: projects by lifecycle stage.
    order = ["operational", "pilot", "in-development", "unresolved", "announced", "discontinued"]
    projects = sorted((e for e in ents.values() if e["type"] == "project"),
                      key=lambda e: (order.index(e["lifecycle"]), e["name"].lower()))
    q2 = [[_ent_link(model, e["id"]), escape(KIND_LABELS[e["project_kind"]]), escape(stage_label(model, e)),
           " ".join(badge(model.records[x]["classification"]) + " " + _ev_links([x]) for x in e["lifecycle_evidence"]),
           escape(e.get("status", ""))] for e in projects]
    counts = {st: sum(1 for e in projects if e["lifecycle"] == st) for st in order}
    stage_line = " · ".join(f"{LIFECYCLE_LABELS[st]}: {n}" for st, n in counts.items() if n)
    ai_running = [e for e in projects if e["project_kind"] == "ai-application" and e["lifecycle"] in ("operational", "pilot")]
    listed = "; ".join(f"{e['name']} ({LIFECYCLE_LABELS[e['lifecycle']].lower()}, basis: {', '.join(deployment_facts(model, e)['bases'])})"
                       for e in ai_running)
    if len(ai_running) == 1:
        ai_line = (f"One AI application recorded here is documented as operational or in pilot: {listed}. It is the only one "
                   "currently documented in this registry, not necessarily the only one in Morocco.")
    elif ai_running:
        ai_line = (f"AI applications documented as operational or in pilot: {listed}. These are the ones currently documented "
                   "in this registry, not necessarily all those in Morocco.")
    else:
        ai_line = ("No AI application recorded here is yet documented as operational or in pilot. This reflects the registry's "
                   "current coverage, not the state of AI use in Morocco.")

    # Q3: models and datasets.
    q3 = []
    for e in sorted((e for e in ents.values() if e["type"] in ("model", "dataset")), key=lambda e: e["name"].lower()):
        devs = [r["subject"] for r in rels if r["predicate"] == "develops" and r["object"] == e["id"] and r["classification"] == "VERIFIED FACT"]
        conn = [a for a in e.get("attributes") or [] if a["name"] == "Connection to Morocco"]
        attrs = "; ".join(f'{escape(a["name"])}: {escape(a["value"])}' for a in e.get("attributes") or [] if a not in conn)
        q3.append([_ent_link(model, e["id"]), escape(TYPE_SINGULAR[e["type"]]),
                   ", ".join(_ent_link(model, d) for d in devs) or "Not recorded",
                   escape(conn[0]["value"]) if conn else "Not recorded", attrs,
                   f'{escape(LIFECYCLE_LABELS[e["lifecycle"]])} · {_ev_links(e["lifecycle_evidence"])}'])

    # Q4: sectors, and whether any targeting project is verified as running.
    q4, verified_sectors = [], []
    for e in sorted((e for e in ents.values() if e["type"] == "sector"), key=lambda e: e["name"].lower()):
        links = [r for r in rels if r["predicate"] == "targets" and r["object"] == e["id"]]
        if not links:
            continue
        cells = []
        for r in links:
            src = ents[r["subject"]]
            stage = stage_label(model, src) if src.get("lifecycle") else TYPE_SINGULAR[src["type"]]
            cells.append(f'{_ent_link(model, src["id"])} ({escape(stage)})')
            if (src.get("project_kind") == "ai-application" and src.get("lifecycle") in ("operational", "pilot")
                    and r["classification"] == "VERIFIED FACT"):
                verified_sectors.append(e["id"])
        q4.append([_ent_link(model, e["id"]), "; ".join(cells)])
    if verified_sectors:
        sector_line = ("Sectors with a documented operational or pilot AI application in this registry: " + ", ".join(
            _ent_link(model, x) for x in dict.fromkeys(verified_sectors)) + ". See Q6 for the basis of each: public "
            "availability is not evidence of how widely a system is used. Sectors not listed have no qualifying deployment "
            "documented in this registry, which reflects its coverage, not the state of AI use in Morocco.")
    else:
        sector_line = ("No qualifying deployment has yet been documented in this registry: no AI application recorded here "
                       "has a verified operational or pilot status in a sector. This reflects the registry's current coverage, "
                       "not the state of AI use in Morocco. The sectors below are targeted only by announced or "
                       "in-development projects, or by initiatives.")

    # Q6: AI applications and their deployment facts.
    q6 = []
    apps = [e for e in projects if e["project_kind"] == "ai-application"]
    for e in apps:
        f = deployment_facts(model, e)
        ops = ", ".join(f'{_ent_link(model, o)}{"" if c == "VERIFIED FACT" else " (planned)"}' for o, c in f["operators"]) or "Not documented"
        q6.append([_ent_link(model, e["id"]), ", ".join(_ent_link(model, x) for x in f["sectors"]) or "Not recorded", ops,
                   escape(f["provider"]) or "Not documented", escape(stage_label(model, e)),
                   escape("; ".join(f["bases"])) or "—", (escape(f["currency"]) + " · " + _ev_links(f["status_ids"])) if f["status_ids"] else "—"])

    # Q7: unresolved stages, and operation whose latest evidence is past the recency convention.
    q7 = []
    for e in sorted((e for e in ents.values() if e.get("lifecycle") == "unresolved"), key=lambda e: e["name"].lower()):
        q7.append([_ent_link(model, e["id"]), "Unresolved", escape(e.get("note", "")) + " " + _ev_links(e["lifecycle_evidence"])])
    for e in projects:
        f = deployment_facts(model, e)
        if f["stale"]:
            q7.append([_ent_link(model, e["id"]), f"Not reconfirmed in {RECENCY_MONTHS} months",
                       escape(f["currency"]) + " " + _ev_links(f["status_ids"])])

    # Q5: relationships between organisations and what they sign, build, host or fund, by classification.
    q5 = []
    for cls in registry.CLASSIFICATIONS:
        for r in rels:
            if r["classification"] == cls and ents[r["subject"]]["type"] in org_types and r["predicate"] in activity_preds + ("launched", "presented", "organized", "designated", "lists_in_framework"):
                q5.append([badge(cls), f'{_ent_link(model, r["subject"])} <span class="rel-type">{escape(model.predicates[r["predicate"]]["label"])}</span> {_ent_link(model, r["object"])}',
                           _ev_links(r["evidence"])])
    by_cls = {c: sum(1 for r in rels if r["classification"] == c) for c in registry.CLASSIFICATIONS}
    cls_line = " · ".join(f"{c.title()}: {n}" for c, n in by_cls.items() if n)

    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / Questions</p>
  <p class="label">MAI-Q — Generated from the registry data</p>
  <h1>Questions the registry answers</h1>
  <p class="lede">Each answer is computed from <a href="/data/ontology.json">ontology.json</a> and <a href="/data/evidence.json">evidence.json</a> and links to the records behind it. Where the evidence does not support an answer, the page says so.</p>
</header>
<section aria-labelledby="q1-h">
  <h2 id="q1-h"><span class="section-number">Q1</span>Which organisations have a verified role in Morocco-related AI work?</h2>
  <p class="prose">Organisations that verified records show developing, hosting, creating, funding or signing for a project, model or company recorded here, plus every company in the registry. Inclusion means a documented connection to Morocco-related AI work, not that an organisation is Moroccan or operates in Morocco: MBZUAI France Lab, for example, is in Paris. Origin is shown for companies as the evidence states it. This list is limited to the registry's current coverage.</p>
  {_table("Organisations with a verified role", ["Organisation", "Kind", "Verified role", "Evidence"], q1, "No organisation recorded.")}
</section>
<section aria-labelledby="q2-h">
  <h2 id="q2-h"><span class="section-number">Q2</span>Which projects are operational, and which are only announced?</h2>
  <p class="prose">{escape(stage_line)}. A stage other than "announced" requires a verified record that explicitly documents that stage. "Operational" and "pilot" must rest on a record published by a verified operator of the project or by an independent source, never on a developer's or vendor's page, press, a procurement notice, a signature or an announcement. The kind column separates AI applications from compute infrastructure and digital platforms, neither of which counts as an AI deployment.</p>
  <p class="prose">{escape(ai_line)}</p>
  {_table("Projects by lifecycle stage", ["Project", "Kind", "Lifecycle", "Basis", "Status"], q2, "No project recorded.")}
</section>
<section aria-labelledby="q3-h">
  <h2 id="q3-h"><span class="section-number">Q3</span>What AI models and datasets are publicly documented?</h2>
  <p class="prose">Models and datasets with a documented connection to Morocco, recorded from their own repositories and papers. For most, the connection is the language (Moroccan Darija), not a Moroccan developer; the "Connection to Morocco" column says which. "Developed by" lists only developers a source names; a relationship the registry infers is shown on the entity page as independent analysis. Technical details are listed only where the source states them; self-reported benchmark results are not recorded.</p>
  {_table("Models and datasets", ["Name", "Type", "Developed by", "Connection to Morocco", "Documented characteristics", "Availability"], q3, "No model or dataset recorded.")}
</section>
<section aria-labelledby="q4-h">
  <h2 id="q4-h"><span class="section-number">Q4</span>Which sectors have verified AI deployments?</h2>
  <p class="prose">{sector_line}</p>
  {_table("Sectors and the projects that target them", ["Sector", "Targeted by"], q4, "No sector is targeted by a recorded project.")}
</section>
<section aria-labelledby="q6-h">
  <h2 id="q6-h"><span class="section-number">Q6</span>Which AI applications are deployed, who operates them, and how current is the evidence?</h2>
  <p class="prose">Every AI application in the registry, with its operator (distinct from any provider or developer), sector, lifecycle stage, the basis of that stage, and the date of the latest status evidence. Public availability shows that a service is offered, not how many people use it. The recency column is a convention, not a finding: when the latest supporting evidence is more than twelve months before the registry date, it says that current operation has not been reconfirmed. Elapsed time never changes a lifecycle stage, old evidence does not show that a system stopped, and recent evidence does not show that it is still running. Deployment is not evidence of performance or outcomes, and none are recorded here.</p>
  {_table("AI applications and their deployment evidence", ["Application", "Sector", "Operator", "Provider", "Lifecycle", "Basis", "Evidence recency"], q6, "No AI application recorded.")}
</section>
<section aria-labelledby="q7-h">
  <h2 id="q7-h"><span class="section-number">Q7</span>Which claims remain unresolved, and which deployments have not been reconfirmed recently?</h2>
  <p class="prose">Entities whose evidence conflicts or is insufficient to establish a stage, and operational or pilot projects whose latest supporting evidence is more than twelve months before the registry date. Such a project keeps its stage: the registry records a discontinuation only when a source documents one. Candidates still under review are not published until they pass the registry's evidence rules.</p>
  {_table("Unresolved and not recently reconfirmed entries", ["Entity", "Status", "Why"], q7, "No unresolved or not recently reconfirmed entry is recorded.")}
</section>
<section aria-labelledby="q5-h">
  <h2 id="q5-h"><span class="section-number">Q5</span>Which institutional relationships are supported by evidence?</h2>
  <p class="prose">All relationships by classification: {escape(cls_line)}. The table lists those between organisations and what they launch, sign, build, host or fund.</p>
  {_table("Institutional relationships by classification", ["Classification", "Relationship", "Evidence"], q5, "No relationship recorded.")}
</section>"""
    return page(model, path="/registry/questions/", current="questions",
                title="Questions the Registry Answers — TheMoroccoAI",
                description="Evidence-linked answers about Morocco's AI ecosystem: organisations with documented AI activity, deployed versus announced AI applications and their operators, public models and datasets, sectors and verified relationships.",
                body=body)


def render_evidence_index(model):
    records = sorted(model.evidence["records"], key=lambda r: (r["publication_date"] or "", r["evidence_id"]), reverse=True)
    cards = "\n".join(evidence_card(model, r, heading="h2") for r in records)
    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / Evidence</p>
  <p class="label">MAI-EV — {len(records)} records</p>
  <h1>Evidence records</h1>
  <p class="lede">Every source behind the registry, newest first. Each record quotes its source verbatim, gives publication and retrieval dates, and carries one classification.</p>
</header>
<ul class="evidence-list">
{cards}
</ul>"""
    return page(model, path="/registry/evidence/", current="evidence",
                title="Evidence Records — TheMoroccoAI Registry",
                description="All primary-source evidence records behind TheMoroccoAI registry, with verbatim excerpts, dates and claim classifications.",
                body=body)


# ─── HOMEPAGE BLOCKS ──────────────────────────────────────────────────────

def homepage_blocks(model):
    nodes = []
    for i, (key, label) in enumerate(model.domains.items(), 1):
        members = sorted((e for e in model.ontology["entities"] if e.get("domain") == key),
                         key=lambda e: (-len(e["evidence"]), e["name"].lower()))
        if members:
            recs = {x for e in members for x in e["evidence"]}
            status = f"{len(recs)} record{'s' if len(recs) != 1 else ''}"
            names = ", ".join(f'<a href="{entity_url(e["id"])}">{escape(e["name"])}</a>' for e in members[:3])
            more = f" and {len(members) - 3} more" if len(members) > 3 else ""
            desc = f"{names}{more}."
        else:
            status = "Not yet sourced"
            desc = "No verified record yet. This domain stays empty until primary sources support an entry."
        nodes.append(f"""      <div class="landscape-node">
        <span class="node-status">{status}</span>
        <div class="node-id">MAI-D-{i:03d}</div>
        <h3 class="node-title"><a href="/registry/#domain-{key}">{escape(label)}</a></h3>
        <p class="node-desc">{desc}</p>
        <div class="node-ar" lang="ar" dir="rtl">{escape(model.ontology.get("domain_labels_ar", {}).get(key, ""))}</div>
      </div>""")
    nodes.append("""      <div class="landscape-node landscape-node-cta">
        <span class="node-status">Open</span>
        <div class="node-id">MAI-REG</div>
        <h3 class="node-title"><a href="/registry/">Open the full registry →</a></h3>
        <p class="node-desc">Every entity, relationship and source excerpt, plus the JSON data.</p>
      </div>""")
    return {
        "landscape": "\n" + "\n".join(nodes) + "\n      ",
        "records": str(len(model.records)),
        "entities": str(len(model.entities)),
        "as-of": human_date(model.as_of).split(" ", 1)[-1] if model.as_of else "",
    }


def inject(html_text, blocks):
    for key, value in blocks.items():
        pattern = re.compile(rf"(<!--r:{re.escape(key)}-->)(.*?)(<!--/r:{re.escape(key)}-->)", re.S)
        if not pattern.search(html_text):
            raise SystemExit(f"index.html: missing marker <!--r:{key}-->")
        html_text = pattern.sub(lambda m: m.group(1) + value + m.group(3), html_text)
    return html_text


def sitemap(model):
    paths = ["/", "/registry/", "/registry/questions/", "/registry/evidence/"] + [entity_url(e) for e in sorted(model.entities)]
    urls = "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{model.as_of}</lastmod></url>\n" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def outputs(model):
    files = {
        "registry/index.html": render_registry_index(model),
        "registry/evidence/index.html": render_evidence_index(model),
        "registry/questions/index.html": render_questions(model),
        "sitemap.xml": sitemap(model),
    }
    for eid, e in model.entities.items():
        files[f"registry/{eid}/index.html"] = render_entity(model, e)
    files["index.html"] = inject((ROOT / "index.html").read_text(encoding="utf-8"), homepage_blocks(model))
    return files


def main(argv):
    check = "--check" in argv
    evidence, ontology = registry.load_all()
    errors = registry.validate(evidence, ontology)
    if errors:
        for e in errors:
            print("ERROR", e)
        return 1
    files = outputs(Model(evidence, ontology))
    expected_dirs = {str(Path(p).parent) for p in files if p.startswith("registry/")}
    stale_dirs = [d for d in (ROOT / "registry").glob("*/") if str(d.relative_to(ROOT)) not in expected_dirs] \
        if (ROOT / "registry").exists() else []
    if check:
        stale = [p for p, c in files.items() if not (ROOT / p).exists() or (ROOT / p).read_text(encoding="utf-8") != c]
        stale += [str(d.relative_to(ROOT)) + "/ (orphaned)" for d in stale_dirs]
        for p in stale:
            print("STALE", p)
        print(f"{len(files)} generated files checked, {len(stale)} stale")
        return 1 if stale else 0
    for d in stale_dirs:
        shutil.rmtree(d)
    for p, c in files.items():
        target = ROOT / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(c, encoding="utf-8")
    print(f"Wrote {len(files)} files ({len(ontology['entities'])} entity pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
