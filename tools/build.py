"""Generate the public registry pages from data/evidence.json and data/ontology.json.

    python3 tools/build.py          validate, then write all generated files
    python3 tools/build.py --check  validate, then fail if any generated file is stale

Generated outputs (committed, because GitHub Pages serves the repository as-is):
    registry/index.html, registry/evidence/index.html, registry/<entity-id>/index.html,
    sitemap.xml, and the marked blocks inside index.html.
Standard library only.
"""
import datetime
import hashlib
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
KIND_COUNT_LABELS = {
    "ai-application": ("AI application", "AI applications"), "compute-infrastructure": ("compute infrastructure", "compute infrastructure"),
    "institute": ("institute", "institutes"), "agreement": ("agreement", "agreements"), "digital-platform": ("digital platform", "digital platforms"),
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
    "academic_journal": "Peer-reviewed journal",
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
    {nav_link("/registry/matrix/", "Matrix", "matrix", "nav-optional")}
    {nav_link("/registry/gaps/", "Gaps", "gaps", "nav-optional")}
    {nav_link("/registry/evidence/", "Evidence", "evidence", "nav-optional")}
    {nav_link("/methodology/", "Methodology", "methodology", "nav-optional")}
    {nav_link("/acquisition/", "Acquisition", "acquisition", "nav-optional")}
  </ul>
</nav>
<main id="content">
<div class="page">
{body}
</div>
</main>
<footer>
  <div class="footer-inner">
    <span class="footer-brand">TheMoroccoAI.com · Independent evidence registry</span>
    <span class="footer-note">Not affiliated with the Government of Morocco · Registry v{escape(model.evidence["version"])} · as of {escape(human_date(model.as_of))}</span>
    <span class="footer-note"><a href="/methodology/">Methodology and changelog</a> · <a href="/data/">Data</a> · <a href="/acquisition/">Acquisition</a></span>
  </div>
</footer>
</body>
</html>
"""


def evidence_card(model, r, *, heading="h3", show_entities=True):
    rid = r["evidence_id"]
    quotes = "".join(f"<p>“{escape(q)}”</p>" for q in r["source_excerpts"])
    lang = r.get("source_language", "en")
    quote_lang = (f' lang="{escape(lang)}"' if lang != "en" else "") + (' dir="rtl"' if lang in ("ar", "he", "fa", "ur") else "")
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
  <p class="lede">Institutions, initiatives and projects in Morocco’s artificial intelligence ecosystem. Every entry cites its source, whose type is labelled, with a verbatim excerpt and dates, and <strong>facts, official targets, announced plans and our own analysis are labelled separately</strong>.</p>
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
  <p class="prose">The <a href="/registry/matrix/">institutional matrix</a> shows which organisations are documented as connected to which projects and initiatives, and on what evidence. The <a href="/registry/gaps/">evidence gap register</a> lists what the registry cannot yet establish.</p>
  <p class="prose">The fullest chain in this version runs from <a href="{entity_url("morocco-ai-2030")}">Morocco AI 2030</a> to the announced <a href="{entity_url("jazari-network")}">JAZARI Institutes network</a>, its planned core institute <a href="{entity_url("jazari-root")}">Institut Jazari ROOT</a> and the <a href="{entity_url("jazari-industrie-x0")}">JAZARI Industrie X.0</a> convention signed in Fès. It then goes on to the signatories, the stated technologies and the targeted sectors. Each page shows the source excerpt, the publication and retrieval dates, and the classification of every claim.</p>
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
  <p class="prose"><a href="/data/">Using the registry data</a> describes the files, identifiers, null values and versions, says which answers can be recomputed, and links to an example that checks the data independently.</p>
  <ul class="data-links">
    <li><a href="/data/manifest.json"><code>/data/manifest.json</code></a>: the list of published JSON files, with the SHA-256 of each in this version.</li>
    <li><a href="/data/evidence.json"><code>/data/evidence.json</code></a>: every evidence record, with its source URL, dates, verbatim excerpts, classification and verification status.</li>
    <li><a href="/data/ontology.json"><code>/data/ontology.json</code></a>: entity types, domains, predicates, entities and typed relationships, each citing its evidence.</li>
    <li><a href="/registry/evidence/">All evidence on one page</a>, each record addressable as <code>/registry/evidence/#MAI-EV-NNNN</code>.</li>
  </ul>
</section>

<section aria-labelledby="method-h">
  <h2 id="method-h"><span class="section-number">06</span>Method and limits</h2>
  <div class="prose">
    <p>Each record was retrieved from its source on the stated retrieval date, and its excerpt was matched against the retrieved text. An automated validator checks every build. It requires unique identifiers, https source URLs, valid dates and complete fields, and that every entity and relationship cites existing evidence. It also blocks forward-looking wording in records classified as fact, and rejects any relationship whose classification its evidence does not support.</p>
    <p>The registry is deliberately selective: it omits facts it could not verify against an original source, and an absent entry is a gap in coverage. Corrections can be sent to <a href="mailto:{CONTACT}?subject=TheMoroccoAI%20registry%20correction">{CONTACT}</a>.</p>
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


AVAILABILITY_SUFFIX = " (public availability; use not documented)"


def stage_label(model, e):
    """Lifecycle label; an operational or pilot stage resting only on observed availability says so."""
    label = LIFECYCLE_LABELS[e["lifecycle"]]
    if e.get("lifecycle") in ("operational", "pilot"):
        bases = {model.records[x].get("status_basis") for x in e.get("lifecycle_evidence") or []
                 if model.records[x].get("status_evidence") == e["lifecycle"]}
        if bases == {"public-availability-observed"}:
            label += AVAILABILITY_SUFFIX
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
    # Q8: organisations connected to projects, from the matrix rows.
    mrows = [r for r in matrix_rows(model) if r["object"]["type"] == "project" and r["subject"]["type"] in org_types]
    q8, orgs8 = [], []
    for sid in sorted({r["subject"]["id"] for r in mrows}, key=lambda i: ents[i]["name"].lower()):
        mine = [r for r in mrows if r["subject"]["id"] == sid]
        orgs8.append(sid)
        q8.append([_ent_link(model, sid),
                   "; ".join(f'{_ent_link(model, r["object"]["id"])} ({escape(r["documented_as"].lower())}; {escape((r["object"]["stage"] or "").lower())})' for r in mine),
                   _ev_links(sorted({e["id"] for r in mine for e in r["evidence"]})) + f' · <a href="/registry/matrix/#m-{sid}">matrix</a>'])
    lv = {}
    for r in mrows:
        lv[r["documented_as"]] = lv.get(r["documented_as"], 0) + 1
    q8_line = (f"{len(orgs8)} organisations are documented as connected to {len({r['object']['id'] for r in mrows})} projects, through "
               f"{len(mrows)} relationships: " + ", ".join(f"{k.lower()} {v}" for k, v in sorted(lv.items(), key=lambda kv: (-kv[1], kv[0])))
               + f". {sum(1 for r in mrows if r['documentation_basis'] == 'announcement-or-description')} of these rest only on announcements or news reports in this registry; that describes how they are documented here, not whether they are true. "
               "A signature or an announcement is not delivery, and these connections are the ones recorded here, not all that exist.")
    projects8 = [ents[x] for x in sorted({r["object"]["id"] for r in mrows})]
    kinds8 = {}
    for e in projects8:
        kinds8[e["project_kind"]] = kinds8.get(e["project_kind"], 0) + 1
    stages8 = {}
    for e in projects8:
        stages8[e["lifecycle"]] = stages8.get(e["lifecycle"], 0) + 1
    signed8 = [r for r in mrows if r["documented_as"] == "Signed"]
    text8 = sum(1 for r in signed8 if SIGNED_TEXT_NOT_RECORDED not in r["qualifications"])
    gazette8 = [r for r in signed8 if SIGNED_GAZETTE_APPROVAL in r["qualifications"]]
    gazette8_ids = sorted({e["id"] for r in gazette8 for e in r["evidence"] if e["evidence_type"] == "official_gazette"})
    q8_scope = (f"The {len(projects8)} projects are all the projects these organisations are connected to, of every kind recorded: "
                + ", ".join(f"{v} {KIND_COUNT_LABELS[k][v != 1]}" for k, v in sorted(kinds8.items(), key=lambda kv: (-kv[1], kv[0])))
                + ". By stage: " + ", ".join(f"{v} {LIFECYCLE_LABELS[k].lower()}" for k, v in sorted(stages8.items(), key=lambda kv: (-kv[1], kv[0])))
                + (". A digital platform here is a catalogue of AI solutions, not itself an AI system. " if "digital-platform" in kinds8 else ". ")
                + (f"None of the {len(signed8)} signatures is documented by its signed text: each rests on a report of the signing"
                   + (f"; for {len(gazette8)}, an official gazette record ({', '.join(gazette8_ids)}) also documents the legal approval "
                      f"of the instrument, which is not its signed text." if gazette8 else ".")
                   if not text8 else f"{text8} of the {len(signed8)} signatures are documented by their signed text."))

    # Q9: official targets against what the registry records about progress.
    gaps = registry.load(registry.ROOT / "data" / "gaps.json")
    q9 = []
    for r in sorted((r for r in model.records.values() if r["classification"] == "OFFICIAL TARGET"), key=lambda r: r["evidence_id"]):
        inits = [e for e in r["related_entities"] if ents[e]["type"] == "initiative"]
        for i in inits:
            inc = [x["object"] for x in rels if x["subject"] == i and x["predicate"] == "includes" and ents[x["object"]].get("lifecycle")]
            gap = next((g for g in gaps["gaps"] if i in g["entities"]), None)
            progress = (f'{escape(gaps["open_wording"])} <a href="/registry/gaps/#{gap["id"].lower()}">{gap["id"]}</a>' if gap and gap["state"] == "open"
                        else (f'See <a href="/registry/gaps/#{gap["id"].lower()}">{gap["id"]}</a>' if gap else "Not yet assessed in the gap register."))
            q9.append([_ent_link(model, i), f'{escape(r["claim"])} {_ev_links([r["evidence_id"]])}',
                       "; ".join(f'{_ent_link(model, x)} ({escape(stage_label(model, ents[x]).lower())})' for x in inc) or "None recorded",
                       progress])

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
  <p class="prose">Who is connected to each project is in Q8 and the <a href="/registry/matrix/">institutional matrix</a>; what the registry cannot yet establish is in the <a href="/registry/gaps/">evidence gap register</a>.</p>
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
<section aria-labelledby="q8-h">
  <h2 id="q8-h"><span class="section-number">Q8</span>Which organisations are connected to the AI-related and computing projects recorded in this registry, and what establishes each connection?</h2>
  <p class="prose">{escape(q8_line)}</p>
  <p class="prose">{escape(q8_scope)} The full set, with sources and qualifications, is in the <a href="/registry/matrix/">institutional matrix</a>.</p>
  {_table("Organisations and the projects they are documented as connected to", ["Organisation", "Projects (documented as; project stage)", "Evidence"], q8, "No organisation is connected to a project.")}
</section>
<section aria-labelledby="q9-h">
  <h2 id="q9-h"><span class="section-number">Q9</span>What does the registry establish about national targets, and which outcomes remain unverified?</h2>
  <p class="prose">Each official target as its source states it, the projects the strategy is recorded as including, and what the registry records about measured progress. Targets are never shown as outcomes, and a project's status is not progress toward a target.</p>
  {_table("Official targets and recorded progress", ["Strategy", "Official target", "Projects recorded as included (stage)", "Measured progress"], q9, "No official target recorded.")}
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


# ─── INSTITUTIONAL MATRIX AND EVIDENCE GAPS ────────────────────────────────

DOCUMENTED_AS = {"ANNOUNCED PLAN": "Announced or planned", "OFFICIAL TARGET": "Target",
                 "INDEPENDENT ANALYSIS": "Registry inference", "UNVERIFIED CLAIM": "Unverified claim"}
DOCUMENTED_AS_VERIFIED = {"signatory_of": "Signed", "operates": "Operated", "develops": "Developed"}
DOCUMENTED_AS_VERIFIED_OTHERWISE = "Documented"
SIGNED_TEXT_NOT_RECORDED = "The signing is documented by a report of it; the signed text is not recorded in this registry."
SIGNED_GAZETTE_APPROVAL = ("A cited official gazette record documents the legal approval of the instrument, not its signed text, "
                           "and is not a report of the signing.")
SIGNED_NOT_DELIVERED = "A signature is recorded as a signature; delivery is not documented."
PLAN_NOT_DELIVERED = "Not verified as delivered."
GAP05_CAVEAT = "Documented here only by announcements, news reports or descriptions (GAP-05)."
QUALIFICATION_RULES = [
    {"when": "The relationship has a note in ontology.json", "text": "the note"},
    {"when": "documented_as is Signed and no cited record is a signed_instrument whose instrument.signatories include the subject", "text": SIGNED_TEXT_NOT_RECORDED},
    {"when": "documented_as is Signed and a cited record has evidence_type official_gazette", "text": SIGNED_GAZETTE_APPROVAL},
    {"when": "documented_as is Signed and object.lifecycle is announced", "text": SIGNED_NOT_DELIVERED},
    {"when": "documented_as is Announced or planned", "text": PLAN_NOT_DELIVERED},
    {"when": "documentation_basis is announcement-or-description", "text": GAP05_CAVEAT},
]
DOCUMENTATION_BASIS = {
    "announcement-or-description": "A formal-act relationship whose every cited record has one of the announcement evidence types. These are listed in GAP-05.",
    "includes-non-announcement-record": ("A formal-act relationship that cites at least one record of another type: an official report, a "
                                         "regulatory record, an official gazette text, a technical repository, a publication, a ranking or a direct observation. "
                                         "Such a record is not the instrument itself: an official gazette text records a legal act about it, such "
                                         "as its approval, and a signed text would have evidence_type signed_instrument."),
    "declaration-or-event": "Any other relationship: declarations, public events and a programme's stated composition, whose primary record is an announcement. Not measured this way.",
}


def documented_as(rel):
    """What the relationship's own classification supports, in plain words. It never upgrades a record."""
    cls = rel["classification"]
    if cls != "VERIFIED FACT":
        return DOCUMENTED_AS[cls]
    return DOCUMENTED_AS_VERIFIED.get(rel["predicate"], DOCUMENTED_AS_VERIFIED_OTHERWISE)


def matrix_derivation():
    """The rules that turn ontology.json and evidence.json into matrix rows, published with the rows so that a
    consumer can recompute them without this code."""
    return {
        "row_selection": {"subject_types": list(registry.MATRIX_SUBJECT_TYPES), "object_types": list(registry.MATRIX_OBJECT_TYPES),
                          "rule": "Every relationship in ontology.json whose subject has one of subject_types and whose object has one of object_types."},
        "row_id": "subject|relationship|object, joined with '|'. A relationship is identified by this triple, which is unique in ontology.json.",
        "row_order": "Rows are sorted by the tuple (subject, relationship, object), compared element by element as strings; not by row_id, so 'um6p|…' sorts before 'um6p-ventures|…'. Each row's evidence keeps the order of the relationship's evidence list in ontology.json.",
        "documented_as": {"by_classification": DOCUMENTED_AS,
                          "verified_fact_by_relationship": DOCUMENTED_AS_VERIFIED,
                          "verified_fact_otherwise": DOCUMENTED_AS_VERIFIED_OTHERWISE,
                          "rule": "Derived from the relationship's classification and, for VERIFIED FACT, its relationship type. It never upgrades a record."},
        "documentation_basis": {"formal_act_relationships": list(registry.FORMAL_ACT_PREDICATES),
                                "announcement_evidence_types": list(registry.ANNOUNCEMENT_TYPES),
                                "values": DOCUMENTATION_BASIS,
                                "assignment": {"not_a_formal_act": "declaration-or-event", "every_record_an_announcement": "announcement-or-description",
                                               "otherwise": "includes-non-announcement-record"},
                                "rule": ("For a relationship whose type is in formal_act_relationships: announcement-or-description when every record it "
                                         "cites has an evidence_type in announcement_evidence_types, otherwise includes-non-announcement-record. For any other "
                                         "relationship: declaration-or-event. Describes how a relationship is documented in this registry, not whether it is true. "
                                         "documented_as and documentation_basis are independent: a row can read Signed while resting only on an announcement.")},
        "object.lifecycle": "The related entity's lifecycle key from ontology.json (defined in its lifecycle_stages); null for entity types without a lifecycle.",
        "object.stage": {"labels": LIFECYCLE_LABELS, "availability_suffix": AVAILABILITY_SUFFIX,
                         "rule": ("A display label: labels[object.lifecycle], followed by availability_suffix when the stage is operational or pilot "
                                  "and every lifecycle_evidence record declaring that stage (status_evidence equal to it) has status_basis "
                                  "public-availability-observed. Other bases (an operator's or independent report of use, an independent listing) "
                                  "add nothing to the label. Use object.lifecycle and the records' status_basis for machine processing.")},
        "qualifications": {"rule": "Explanatory sentences for readers, in this order, each added when its condition holds. Not a controlled vocabulary.",
                           "rules": QUALIFICATION_RULES},
        "relationship_label": "The predicate's label in ontology.json (predicates.<relationship>.label).",
        "subject.name, object.name, object.type": "Copied from the entity in ontology.json.",
        "object.status_as_recorded": "The related entity's free-text status field in ontology.json; null when absent.",
        "evidence": "For each record the relationship cites: its id, source_url, source_type, evidence_type, publication_date and retrieval_date, copied from evidence.json.",
    }


def _record_date(r):
    return (human_date(r["publication_date"]), "published") if r["publication_date"] else (human_date(r["retrieval_date"]), "retrieved")


def matrix_rows(model):
    """One row per matrix relationship, deterministic, every field traceable to the canonical data."""
    announcement_only = {(r["subject"], r["predicate"], r["object"]) for r in registry.announcement_only(model.ontology, model.evidence)}
    rows = []
    for rel in sorted(registry.matrix_relationships(model.ontology), key=lambda r: (r["subject"], r["predicate"], r["object"])):
        subj, obj = model.entities[rel["subject"]], model.entities[rel["object"]]
        key = (rel["subject"], rel["predicate"], rel["object"])
        level = documented_as(rel)
        quals = []
        if rel.get("note"):
            quals.append(rel["note"])
        if level == "Signed" and not any(model.records[x]["evidence_type"] == "signed_instrument"
                                         and rel["subject"] in model.records[x]["instrument"]["signatories"] for x in rel["evidence"]):
            quals.append(SIGNED_TEXT_NOT_RECORDED)
        if level == "Signed" and any(model.records[x]["evidence_type"] == "official_gazette" for x in rel["evidence"]):
            quals.append(SIGNED_GAZETTE_APPROVAL)
        if level == "Signed" and obj.get("lifecycle") == "announced":
            quals.append(SIGNED_NOT_DELIVERED)
        if level == "Announced or planned":
            quals.append(PLAN_NOT_DELIVERED)
        if key in announcement_only:
            quals.append(GAP05_CAVEAT)
        rows.append({
            "id": "|".join(key),
            "subject": {"id": subj["id"], "name": subj["name"], "type": subj["type"]},
            "relationship": rel["predicate"],
            "relationship_label": model.predicates[rel["predicate"]]["label"],
            "object": {"id": obj["id"], "name": obj["name"], "type": obj["type"],
                       "lifecycle": obj.get("lifecycle"), "stage": stage_label(model, obj) if obj.get("lifecycle") else None,
                       "status_as_recorded": obj.get("status")},
            "classification": rel["classification"],
            "documented_as": level,
            "documentation_basis": ("announcement-or-description" if key in announcement_only
                                    else "includes-non-announcement-record" if rel["predicate"] in registry.FORMAL_ACT_PREDICATES
                                    else "declaration-or-event"),
            "evidence": [{"id": x, "source_url": model.records[x]["source_url"], "source_type": model.records[x]["source_type"],
                          "evidence_type": model.records[x]["evidence_type"], "publication_date": model.records[x]["publication_date"],
                          "retrieval_date": model.records[x]["retrieval_date"]} for x in rel["evidence"]],
            "qualifications": quals,
        })
    return rows


def _evidence_cell(model, ev):
    out = []
    for x in ev:
        r = model.records[x["id"]] if isinstance(x, dict) else model.records[x]
        date, how = _record_date(r)
        out.append(f'<a href="/registry/evidence/#{r["evidence_id"]}">{r["evidence_id"]}</a> '
                   f'<span class="ev-meta">{escape(SOURCE_TYPE_LABELS[r["source_type"]])} · {how} {escape(date)} · '
                   f'<a href="{escape(r["source_url"])}" rel="noopener">source</a></span>')
    return "<br>".join(out)


def render_matrix(model):
    rows = matrix_rows(model)
    order = {"institution": 0, "company": 1, "initiative": 2}
    subjects = sorted({r["subject"]["id"] for r in rows}, key=lambda i: (order[model.entities[i]["type"]], model.entities[i]["name"].lower()))
    levels = {}
    for r in rows:
        levels[r["documented_as"]] = levels.get(r["documented_as"], 0) + 1
    level_line = " · ".join(f"{k}: {v}" for k, v in sorted(levels.items(), key=lambda kv: (-kv[1], kv[0])))
    n_ann = sum(1 for r in rows if r["documentation_basis"] == "announcement-or-description")
    n_acts = len(registry.formal_act_relationships(model.ontology))
    signed = [r for r in rows if r["documented_as"] == "Signed"]
    n_text = sum(1 for r in signed if SIGNED_TEXT_NOT_RECORDED not in r["qualifications"])
    kinds = sorted({e["evidence_type"].replace("_", " ") for r in signed for e in r["evidence"] if e["evidence_type"] != "official_gazette"})
    n_gazette = sum(1 for r in signed if SIGNED_GAZETTE_APPROVAL in r["qualifications"])
    signed_line = (f'For none of the {len(signed)} "Signed" rows is the signed text recorded: each signing is documented by a report of it '
                   f'({", ".join(kinds)})'
                   + (f', and {n_gazette} rows also cite an official gazette record of the instrument\'s legal approval, which is neither '
                      f'the signed text nor a report of the signing' if n_gazette else '')
                   + ', as the evidence column shows.'
                   if not n_text else
                   f'The signed text is recorded for {n_text} of the {len(signed)} "Signed" rows; the others rest on a report of the signing.')
    head = "".join(f'<th scope="col">{h}</th>' for h in ("Related entity", "Relationship", "Documented as", "Status of the related entity", "Evidence", "Qualification"))
    bodies = []
    for sid in subjects:
        subj = model.entities[sid]
        trs = [f'<tr class="group-row"><th scope="rowgroup" colspan="6" id="m-{sid}">{_ent_link(model, sid)} '
               f'<span class="ev-meta">{escape(TYPE_SINGULAR[subj["type"]])}</span></th></tr>']
        for r in (x for x in rows if x["subject"]["id"] == sid):
            o = r["object"]
            status = escape(o["stage"]) if o["stage"] else (f'As recorded: {escape(o["status_as_recorded"])}' if o["status_as_recorded"] else "—")
            trs.append(f'<tr><td>{_ent_link(model, o["id"])} <span class="ev-meta">{escape(TYPE_SINGULAR[o["type"]])}</span></td>'
                       f'<td>{escape(r["relationship_label"])}</td><td>{escape(r["documented_as"])}<br>{badge(r["classification"])}</td>'
                       f'<td>{status}</td><td>{_evidence_cell(model, r["evidence"])}</td>'
                       f'<td>{escape(" ".join(r["qualifications"])) or "—"}</td></tr>')
        bodies.append("<tbody>" + "".join(trs) + "</tbody>")
    index = " · ".join(f'<a href="#m-{sid}">{escape(model.entities[sid]["name"])}</a>' for sid in subjects)
    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / Institutional matrix</p>
  <p class="label">MAI-MATRIX — Generated from the registry data</p>
  <h1>Institutional evidence matrix</h1>
  <p class="lede">What each organisation or initiative recorded here is documented as doing with projects, initiatives, instruments and models, with the classification of each relationship, the status of the related entity and the records behind it.</p>
  <p class="notice"><strong>Scope.</strong> This matrix covers the {len(rows)} relationships recorded in this registry between {len(subjects)} organisations and initiatives and what they act on. It is not a complete map of Morocco's AI ecosystem, and an absent relationship is a gap in coverage. Machine-readable: <a href="/registry/matrix/matrix.json">matrix.json</a>.</p>
</header>
<section aria-labelledby="mx1-h">
  <h2 id="mx1-h"><span class="section-number">01</span>How to read it</h2>
  <ul class="prose">
    <li><strong>Documented as</strong> says only what the relationship's classification supports: {escape(level_line)}. "Signed" means the signature is documented, not that anything was delivered; "Operated" means a verified operator; "Announced or planned" is not verified as delivered. {escape(signed_line)}</li>
    <li><strong>Status of the related entity</strong> is its own lifecycle stage, with its basis. A project's status is not a measure of progress toward any national target.</li>
    <li>Of the {n_acts} relationships that assert a formal act (a signature, creation, designation, investment, development or operation), {n_ann} rest only on announcements, news reports or descriptions (<a href="/registry/gaps/#gap-05">GAP-05</a>); the others also cite another kind of record, such as an official report. This describes how they are documented in this registry, not whether they are true. Declarations and public events (presented, launched, organised, a programme's stated composition) are not measured this way: an official announcement is their primary record.</li>
    <li>An association between organisations is not a legal identity or a formal partnership unless a record says so.</li>
  </ul>
  <p class="prose">Jump to: {index}</p>
</section>
<section aria-labelledby="mx2-h">
  <h2 id="mx2-h"><span class="section-number">02</span>Relationships by organisation and initiative</h2>
  {_table_bodies("Institutional evidence matrix", head, bodies)}
</section>"""
    return page(model, path="/registry/matrix/", current="matrix",
                title="Institutional Evidence Matrix — TheMoroccoAI",
                description="Which institutions, companies and initiatives are documented as connected to Moroccan AI projects, how each connection is classified, and the evidence behind it.",
                body=body)


def _table_bodies(label, head, bodies):
    return (f'<p class="table-hint">Scroll the table sideways to see all columns.</p>'
            f'<div class="table-wrap" role="region" aria-label="{escape(label)}" tabindex="0">'
            f'<table class="qtable"><thead><tr>{head}</tr></thead>{"".join(bodies)}</table></div>')


def gap_register(model, gaps):
    """The gaps with their computed parts resolved, shared by the HTML page and the JSON output."""
    out = []
    for g in gaps["gaps"]:
        item = {k: g[k] for k in ("id", "question", "entities", "unestablished", "evidence_needed", "assessed", "state")}
        item["entities"] = [{"id": e, "name": model.entities[e]["name"]} for e in g["entities"]]
        item["established"] = g["established"]
        item["open_wording"] = gaps["open_wording"] if g["state"] == "open" else None
        item["resolved_by"] = g.get("resolved_by")
        item["entity_assessments"] = g.get("entity_assessments")
        item["relationships"] = None
        item["formal_act_relationships"] = None
        if any(c["type"] == "computed_relationships" for c in g.get("checks") or []):
            item["formal_act_relationships"] = len(registry.formal_act_relationships(model.ontology))
            item["relationships"] = [
                {"id": f'{r["subject"]}|{r["predicate"]}|{r["object"]}', "subject": r["subject"], "relationship": r["predicate"],
                 "object": r["object"], "classification": r["classification"], "evidence": r["evidence"],
                 "evidence_types": [model.records[x]["evidence_type"] for x in r["evidence"]]}
                for r in sorted(registry.announcement_only(model.ontology, model.evidence), key=lambda r: (r["subject"], r["predicate"], r["object"]))]
        out.append(item)
    return out


DIMENSION_LABELS = {"legal_approval": "Legal approval", "governance_event": "Governance event", "staffing": "Staffing",
                    "premises": "Premises", "operational_activity": "Operational activity", "outputs": "Outputs",
                    "documented_non_commencement": "Documented non-commencement",
                    "documented_discontinuation": "Documented discontinuation"}


def gap_derivation():
    """How the gap register is checked against the data, published so that a consumer can repeat the checks."""
    return {
        "computed_relationships": ("A gap with a computed_relationships check (list announcement_only) lists the matrix rows whose documentation_basis "
                                   "is announcement-or-description under the rules in /registry/matrix/matrix.json (derivation.documentation_basis), "
                                   "in the matrix's row order, each entry giving id, subject, relationship, object, classification, evidence (ids) and "
                                   "evidence_types (in the same order). Its count is stated as N of M: N is the length of relationships and M, "
                                   "published as formal_act_relationships, the number of matrix rows whose relationship type is a formal act. Every formal-act relationship type joins types inside the matrix's row selection, so these "
                                   "are all such relationships in ontology.json. The list measures documentation, not truth, and may include "
                                   "relationships already classified as announced plans."),
        "checks": {
            "no_status_basis": "Triggered when a record in the entity's lifecycle_evidence has a status_basis listed in the check's bases.",
            "lifecycle_in": "Triggered when a listed entity's lifecycle is not one of the check's stages; an entity without a lifecycle counts as not in them.",
            "no_ai_application_link": "Triggered when any relationship, of any type and in either direction, joins the entity to an entity whose project_kind is ai-application.",
            "computed_relationships": "Triggered when the computed list is empty.",
            "rule": ("The checks and digests are in /data/gaps.json. A check type not listed here is an error, not a check to skip. "
                     "A check holds when it is not triggered; a triggered check is an error only while the gap is open. An open gap must be re-assessed, "
                     "and the build refuses to publish it, when a check is triggered, when its digest no longer matches, or when a record "
                     "whose related_entities include one of its entities is missing from its assessed_records (whatever that record's dates)."),
        },
        "entity_assessments": ("A gap with entity_assessments is assessed per entity, under the definitions in entity_assessment: "
                               "one assessment per entity, in the gap's entity order, each listing the records cited for every dimension "
                               "in the defined order. A cited record must exist, be a VERIFIED FACT and list the entity in related_entities. "
                               "The dimensions are listed in dimension_order, the order in which they are displayed. An entity meets the operating path when operational_activity and outputs each cite a record, staffing or premises "
                               "cites a record, and its lifecycle is pilot or operational; it meets the not_commenced path when "
                               "documented_non_commencement cites a record, operational_activity and outputs cite none, and its lifecycle is not "
                               "pilot, operational or discontinued; it meets the discontinued path when documented_discontinuation and "
                               "operational_activity each cite a record and its lifecycle is discontinued. An entity that meets no path has an "
                               "unknown operational status. Non-commencement recorded together with activity or outputs is an error. An entity is resolved exactly when "
                               "it meets a path, with resolved_by listing records it cites; an open entity that meets a path, a resolved one "
                               "that meets none, and a resolved gap with an open entity are errors. An empty list means no qualifying record "
                               "is recorded in this registry, not that the thing does not exist."),
        "assessed_fingerprint": {
            "record_fields": list(registry.GAP_RECORD_FIELDS),
            "entity_fields": list(registry.GAP_ENTITY_FIELDS),
            "rule": ("The first 16 hexadecimal digits of the SHA-256 of a UTF-8 JSON text with sorted keys, non-ASCII characters "
                     "unescaped and the separators ', ' and ': ' (Python's json.dumps(value, sort_keys=True, ensure_ascii=False)). "
                     "The value is an object with three keys, each holding a list of JSON arrays (not objects). records: for each "
                     "record whose related_entities (not associated_entities) include one of the gap's entities, superseded records "
                     "included, the array [evidence_id] followed by the values of record_fields in that order (null when absent), "
                     "sorted by evidence_id. entities: for each of the gap's entities, [id] followed by the values of entity_fields "
                     "(null when absent), sorted by id. relationships: for each relationship whose subject or object is one of the gap's "
                     "entities, [subject, predicate, object, classification, evidence, note] with evidence in its ontology.json order and "
                     "note null when absent, the arrays sorted by subject, then predicate, then object (unique, so later elements are "
                     "never compared). Field values are copied as they are in the files, lists unsorted. A gap without entities has no digest."),
        },
    }


def render_gaps(model, gaps):
    items = gap_register(model, gaps)
    arts = []
    for g in items:
        state = "Open" if g["state"] == "open" else "Resolved"
        ents = ", ".join(_ent_link(model, e["id"]) for e in g["entities"]) or "Relationships listed below"
        est = "".join(f'<li>{escape(x["text"])} {_ev_links(x["evidence"])}</li>' for x in g["established"]) or "<li>See the relationships listed below.</li>"
        need = "".join(f"<li>{escape(x)}</li>" for x in g["evidence_needed"])
        open_line = f' <strong>{escape(g["open_wording"])}</strong>' if g["open_wording"] else ""
        resolved = f'<p class="prose">Resolved by: {_ev_links(g["resolved_by"])}</p>' if g["resolved_by"] else ""
        table = ""
        if g["entity_assessments"]:
            dims = gaps["entity_assessment"]["dimension_order"]
            rows = []
            for a in g["entity_assessments"]:
                cells = [_ev_links(a["dimensions"][d]) if a["dimensions"][d] else '<span class="ev-meta">Not documented</span>' for d in dims]
                state = "Resolved: " + _ev_links(a["resolved_by"]) if a["state"] == "resolved" else "Open"
                rows.append([_ent_link(model, a["entity"])] + cells + [state])
            notes = "".join(f'<li>{_ent_link(model, a["entity"])}: {escape(a["note"])}</li>' for a in g["entity_assessments"] if a.get("note"))
            defs = "".join(f"<li><strong>{escape(DIMENSION_LABELS[d])}</strong>: {escape(gaps['entity_assessment']['dimensions'][d])}</li>"
                           for d in dims)
            res = gaps["entity_assessment"]["resolution"]
            table = (f'<h3>Assessment by institute</h3><p class="prose">{escape(gaps["entity_assessment"]["note"])}</p>'
                     + _table("Evidence recorded for each institute, by dimension",
                              ["Institute"] + [DIMENSION_LABELS[d] for d in dims] + ["State"], rows, "")
                     + (f'<ul class="prose">{notes}</ul>' if notes else "")
                     + f'<ul class="prose">{defs}</ul>'
                     + f'<p class="prose">{escape(gaps["entity_assessment"]["qualifying_records"])} An institute resolves when it is documented as operating ({escape(res["operating"].rstrip("."))}), as not having commenced operation ({escape(res["not_commenced"].rstrip("."))}), or as discontinued after operating ({escape(res["discontinued"].rstrip("."))}); otherwise its operational status is unknown and it stays open. {escape(res["rule"])}</p>')
        if g["relationships"]:
            rows = [[_ent_link(model, r["subject"]), escape(model.predicates[r["relationship"]]["label"]), _ent_link(model, r["object"]),
                     badge(r["classification"]), _ev_links(r["evidence"]) + " <span class=\"ev-meta\">" + escape(", ".join(sorted(set(t.replace("_", " ") for t in r["evidence_types"])))) + "</span>"]
                    for r in g["relationships"]]
            table = (f'<p class="prose">{len(rows)} of the {len(registry.formal_act_relationships(model.ontology))} relationships that assert a formal act, computed from the data on every build. '
                     f'Declarations and public events (presented, launched, organised, a programme\'s stated composition) are not listed: an official announcement is their primary record.</p>'
                     + _table("Relationships documented only by announcements, news reports or descriptions",
                              ["Organisation or initiative", "Relationship", "Related entity", "Classification", "Evidence and record type"], rows, ""))
        arts.append(f"""<article class="gap" id="{g["id"].lower()}" aria-labelledby="{g["id"].lower()}-h">
  <h2 id="{g["id"].lower()}-h"><span class="section-number">{g["id"]}</span>{escape(g["question"])}</h2>
  <p class="gap-meta"><span class="badge badge-gap-{g["state"]}">{state}</span> Last assessed {escape(human_date(g["assessed"]))} · Concerns: {ents}</p>
  <h3>What this registry establishes</h3>
  <ul class="prose">{est}</ul>
  <h3>What it does not establish</h3>
  <p class="prose">{escape(g["unestablished"])}{open_line}</p>
  {resolved}
  <h3>Evidence that would resolve it</h3>
  <ul class="prose">{need}</ul>
  {table}
</article>""")
    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / Evidence gaps</p>
  <p class="label">MAI-GAPS — Open evidence questions</p>
  <h1>Evidence gap register</h1>
  <p class="lede">Questions this registry cannot yet answer, with what it does establish, what it does not, and what evidence would settle each one.</p>
  <p class="notice"><strong>A gap is a limit of this registry's coverage.</strong> The statement "{escape(gaps["open_wording"].rstrip("."))}" does not mean that no such evidence exists, nor that anything failed. Machine-readable: <a href="/registry/gaps/gaps.json">gaps.json</a>.</p>
</header>
<p class="prose">{escape(gaps["note"])}</p>
{"".join(arts)}"""
    return page(model, path="/registry/gaps/", current="gaps",
                title="Evidence Gap Register — TheMoroccoAI",
                description="Open evidence questions about Morocco's AI ecosystem: what the registry establishes, what it does not, and what evidence would resolve each question.",
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


# ─── DATA REFERENCE ───────────────────────────────────────────────────────

RESOURCES = (
    ("data/evidence.json", "canonical", "Evidence records: source URL and organisation, publication and retrieval dates, verbatim excerpts, classification, verification status and note. Defines the classifications and verification statuses it uses."),
    ("data/ontology.json", "canonical", "Entity types, lifecycle stages, project kinds, origins, domains and predicates (each defined), then entities and typed relationships, each citing records in evidence.json."),
    ("data/gaps.json", "canonical", "Evidence gaps: what is established (with records), what is not, what would resolve each, the records and data digest each assessment rests on, and the data checks re-run on every build."),
    ("data/changelog.json", "canonical", "Published registry versions, corrections, and the commit or pull request behind each."),
    ("registry/matrix/matrix.json", "derived", "One row per relationship between an organisation or initiative and what it acts on, with the rules used to derive each row."),
    ("registry/gaps/gaps.json", "derived", "The gap register as published, with computed relationship lists resolved; it omits the checks and digests kept in data/gaps.json."),
)
CONSUMER = "examples/registry_consumer.py"
# Changes that make data valid under one version invalid under another. Each is listed in the manifest, on /data/
# and in the changelog. The old value is not accepted anywhere: there is no alias.
BREAKING_CHANGES = [
    {"version": "0.5.0", "file": "/registry/matrix/matrix.json", "field": "rows[].documentation_basis",
     "old": "includes-formal-record", "new": "includes-non-announcement-record",
     "reason": ("The value marks a formal-act relationship that cites at least one record other than an announcement: an "
                "official report, a regulatory record, a repository, a publication, a ranking or a direct observation. The old "
                "name described these as formal records of the act, which for signatures read as the signed text; no such "
                "text is recorded for any signature. The rows it applies to are unchanged; only the name changed."),
     "consumer_effect": ("A consumer that compares this field with the old value fails: the v0.4.1 example consumer exits with "
                         "status 1 and reports, for each row, \"has documentation_basis 'includes-non-announcement-record'; the "
                         "published data gives 'includes-formal-record'\"."),
     "migration": ("Replace the old value with the new one, or read the names from derivation.documentation_basis.assignment in "
                   "matrix.json, as the v0.5.0 example consumer does.")},
]


def manifest(model, files):
    """A catalogue of the published JSON with the SHA-256 of each file in this build, so that a consumer can tell
    whether the files it fetched belong together."""
    resources = []
    for path, role, purpose in RESOURCES:
        content = files[path].encode("utf-8") if path in files else (ROOT / path).read_bytes()
        resources.append({"path": "/" + path, "role": role, "purpose": purpose, "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest()})
    return {
        "registry": model.evidence["registry"], "registry_version": model.evidence["version"], "as_of": model.as_of,
        "publisher": model.evidence["publisher"], "site": SITE, "documentation": "/data/",
        "consumer_example": "/" + CONSUMER,
        "classification_support": {
            "note": ("Two of the validator's rules, published so that they can be checked. Its other rules (for example that an operational "
                     "stage names its operator, or that a source is independent) are described in the methodology and README, not here."),
            "relationship": {**{k: sorted(v) for k, v in registry.RELATION_SUPPORT.items()},
                             "INDEPENDENT ANALYSIS": "at least two cited records and a note"},
            "relationship_rule": "A relationship with a classification listed here must cite at least one record whose classification is in its list.",
            "lifecycle": {k: sorted(v) for k, v in registry.LIFECYCLE_SUPPORT.items()},
            "status_stages": list(registry.STATUS_STAGES),
            "lifecycle_rule": ("An entity's lifecycle_evidence must include a record whose classification is in the stage's list. For a stage in "
                               "status_stages, one of those records must also declare it (status_evidence equal to the stage). announced and "
                               "unresolved need no declaring record; unresolved needs a note instead."),
        },
        "vocabularies": {
            "note": "Values the validator accepts in evidence.json, with display labels where the site uses them. Other defined values are defined in the file that uses them.",
            "source_type": {k: SOURCE_TYPE_LABELS[k] for k in registry.SOURCE_TYPES},
            "evidence_type": list(registry.EVIDENCE_TYPES),
            "status_basis": {k: STATUS_BASIS_LABELS[k] for k in registry.STATUS_BASES},
        },
        "breaking_changes": BREAKING_CHANGES,
        "rights": "No content or data licence has been declared. Source excerpts are quotations of third-party material and remain subject to their publishers' rights.",
        "note": "Canonical files are maintained by hand and validated on every build; derived files are generated from them. Each sha256 is that of the file published in the same build: a mismatch means a file came from a different build (for example while a new version propagates through caches) or was altered. The hashes are published by the same site as the files and are not a signature: they show that a set of files belongs together, not who published it or that its content is accurate.",
        "resources": resources,
    }


def render_data_reference(model, gaps, man):
    ver, repo = model.evidence["version"], "https://github.com/Sohadot/TheMoroccoAI"
    res_rows = [[f'<a href="{r["path"]}"><code>{escape(r["path"])}</code></a>', escape(r["role"]), escape(r["purpose"])] for r in man["resources"]]
    q8_rows = [
        ["Which organisations are connected to which projects, through which relationships", "Reproducible", "Matrix rows whose subject has type institution or company and whose object has type project, of any project kind (institutes, agreements, digital platforms, compute infrastructure and AI applications). Models, datasets and initiatives are not included. Organisations are listed by name compared in lower case; each organisation's rows keep matrix order, one line per relationship (an organisation with two relationships to one project has two); its evidence is the distinct ids of all its rows, sorted. Projects are counted as distinct entities"],
        ["How each connection is documented (signed, developed, announced or planned, and so on)", "Reproducible", "The published documented_as rule, from the relationship's classification"],
        ["How many connections rest only on announcements, news reports or descriptions", "Reproducible", "Rows whose documentation_basis is announcement-or-description, under the published rule"],
        ["The counts in the summary sentence", "Reproducible", "Counting the rows above"],
        ["Each relationship's classification, and the records it cites", "Recorded, not derivable", "An editorial judgment, made under the evidence rules and recorded in ontology.json"],
        ["Each project's lifecycle stage and its basis", "Recorded, not derivable", "An editorial judgment; the validator checks that it is supported (manifest: classification_support): a stage beyond announced cites a record that declares it"],
        ["The caveats (a signature is not delivery; these are the connections recorded here)", "Fixed wording", "Part of the answer's text, not computed"],
    ]
    q9_rows = [
        ["Which official targets are recorded, and for which strategy", "Reproducible", "Each record classified OFFICIAL TARGET, in evidence_id order, superseded or not; its claim (the registry's summary; the source's words are its excerpts); and each entity of type initiative among its related_entities, in that order. The targets relationships from strategies to sectors are not used"],
        ["Which projects each strategy is recorded as including, and their stages", "Reproducible", "includes relationships from the strategy to entities with a lifecycle, in ontology.json order"],
        ["Which gap covers the strategy, and whether it is open", "Reproducible", "data/gaps.json: the first gap, in file order, whose entities include the strategy, and its state"],
        ["That no recorded evidence measures progress towards the targets of Morocco AI 2030 or Digital Morocco 2030", "Editorial assessment", "GAP-02 and GAP-06 are open because an editor judged that their assessed records quantify no progress: for Morocco AI 2030 these include the ministry's presentation of main advances (MAI-EV-0040); for Digital Morocco 2030, a statement about digital spending (MAI-EV-0003), which is an unchecked input figure, not progress. No data check backs this judgment; a consumer can confirm that the data it rests on has not changed since (its digest) but cannot re-derive the judgment"],
        ["That every strategy with an official target has a gap on its progress", "Reproducible", "The build refuses to publish an initiative related to an OFFICIAL TARGET record that no gap's entities include"],
    ]
    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / Data</p>
  <p class="label">MAI-DATA — Registry v{escape(ver)} · as of {escape(human_date(model.as_of))}</p>
  <h1>Using the registry data</h1>
  <p class="lede">The registry is published as JSON files that can be read and checked without this site's code. This page describes the files and their identifiers, where each statement comes from, what null and absent values mean, how versions work, and which answers can be recomputed from the data.</p>
  <p class="notice"><strong>Rights.</strong> No content or data licence has been declared for the registry. Each record quotes a third-party source, and those quotations remain subject to their publishers' rights: nothing here grants a right to republish source material. TheMoroccoAI is independent and is not affiliated with the Government of Morocco or any institution it lists.</p>
</header>
<section aria-labelledby="d1-h">
  <h2 id="d1-h"><span class="section-number">01</span>Files</h2>
  <p class="prose">Start with <a href="/data/manifest.json"><code>/data/manifest.json</code></a>. It lists each file with its role and the SHA-256 of the version published in the same build. Canonical files are maintained by hand and validated on every build; derived files are generated from them and say so in <code>derived_from</code>. Every file is plain UTF-8 JSON and needs no authentication.</p>
  {_table("Published JSON files", ["File", "Role", "Contents"], res_rows, "")}
  <p class="prose">The HTML pages are generated from the same files. Every entity page also embeds its entity as JSON-LD.</p>
</section>
<section aria-labelledby="d2-h">
  <h2 id="d2-h"><span class="section-number">02</span>Identifiers</h2>
  <ul class="prose">
    <li><strong>Evidence records:</strong> <code>MAI-EV-NNNN</code> (<code>evidence_id</code> in evidence.json). Readable at <code>/registry/evidence/#MAI-EV-NNNN</code>.</li>
    <li><strong>Entities:</strong> a lowercase slug (<code>id</code> in ontology.json), also the page address <code>/registry/&lt;id&gt;/</code>.</li>
    <li><strong>Relationships:</strong> have no separate identifier. Each is the triple <code>subject</code>, <code>predicate</code>, <code>object</code>, which the validator keeps unique; matrix.json writes it as <code>subject|predicate|object</code>.</li>
    <li><strong>Gaps:</strong> <code>GAP-NN</code>, readable at <code>/registry/gaps/#gap-nn</code>.</li>
    <li><strong>Defined values:</strong> classifications, verification statuses, entity types, lifecycle stages, project kinds, origins, domains, predicates and gap states are keys of dictionaries that define them in the same file.</li>
  </ul>
  <p class="prose">Published identifiers are not reused. A record, entity or relationship may be corrected or withdrawn; each such change is listed in the <a href="/methodology/#m6-h">changelog</a>, and a withdrawn identifier is never assigned to anything else. A record whose claim later evidence contradicts is kept and marked <code>superseded_by</code>.</p>
  <p class="prose">Since v0.1.0, no evidence or entity identifier has been removed or reused: every identifier published in any version is still present, with the same source address for records and the same type for entities. Earlier versions are not published as files; a test checks this against every version of the data in the <a href="{repo}" rel="noopener">public repository's</a> history on each build, and anyone can repeat it from that history. One relationship has been replaced as a correction (v0.2.0).</p>
</section>
<section aria-labelledby="d3-h">
  <h2 id="d3-h"><span class="section-number">03</span>Provenance</h2>
  <ul class="prose">
    <li>Every entity cites records in <code>evidence</code>; a lifecycle stage cites <code>lifecycle_evidence</code>, an origin <code>origin_evidence</code>, and each attribute its own record.</li>
    <li>Every relationship cites records in <code>evidence</code> and carries one <code>classification</code>, which is never stronger than its records support.</li>
    <li>Every record gives the <code>source_url</code>, <code>source_organization</code>, <code>source_type</code>, <code>publication_date</code>, <code>retrieval_date</code>, verbatim <code>source_excerpts</code> in <code>source_language</code>, and a <code>verification_status</code> with a <code>verification_note</code> that states the record's limits.</li>
    <li><code>claim</code> is the registry's summary of what the source documents; the excerpts are the source's own words.</li>
    <li>A record's classification describes what its source documents, not whether a plan was delivered or a target met.</li>
    <li>A signature is documented by a report of it unless a record of the signed text itself is cited (evidence_type <code>signed_instrument</code>). Such a record is admitted only when the registry has read the signed text in full, from a party to it or an official publisher of it; a report, summary, press release or news item about the signing never qualifies, even from a signatory or the government. An official gazette text approving an instrument, with or without a published summary of it, records a legal act about the instrument: it is neither the signed text nor a report of the signing, and it never qualifies either. The validator checks what it can (classification, verification, source type, the instrument's title, date, signatories and declared access, and that each signatory_of relationship citing it names one of its signatories); that the text was in fact read is an editorial requirement. {"No such record exists yet: every signature in the registry rests on a report of the signing, and some also cite an official gazette record of the instrument's approval." if not any(r["evidence_type"] == "signed_instrument" for r in model.records.values()) else "Rows citing one say so in matrix.json."}</li>
  </ul>
</section>
<section aria-labelledby="d4-h">
  <h2 id="d4-h"><span class="section-number">04</span>Null, absent and unknown values</h2>
  <ul class="prose">
    <li><code>publication_date: null</code> means the source is undated. Use <code>retrieval_date</code>, the day the source was read, which is always present. Dates are <code>YYYY-MM-DD</code>, or <code>YYYY-MM</code> where the source gives only a month.</li>
    <li>An absent optional field means "not recorded", never "no" or "none". For example, an entity without <code>lifecycle</code> is of a type that has no stage, and a record without <code>status_evidence</code> declares no stage.</li>
    <li>In matrix.json, <code>object.lifecycle</code> and <code>object.stage</code> are null for entity types without a stage.</li>
    <li>An empty list means none is recorded here, not that none exists.</li>
    <li>A defined value (classification, stage, predicate, gap state) that is not defined in its file is an error. A consumer should stop rather than guess its meaning; the example below does.</li>
    <li>The values accepted for <code>source_type</code>, <code>evidence_type</code> and <code>status_basis</code> are listed in the manifest under <code>vocabularies</code>.</li>
    <li>Free-text fields (<code>status</code>, <code>note</code>, <code>summary</code>, <code>qualifications</code>) are for readers and are not a controlled vocabulary.</li>
  </ul>
</section>
<section aria-labelledby="d5-h">
  <h2 id="d5-h"><span class="section-number">05</span>Versions and updates</h2>
  <ul class="prose">
    <li>evidence.json and ontology.json carry the same <code>version</code> and <code>as_of</code> date, which the validator enforces; derived files carry them as <code>registry_version</code> and <code>as_of</code>. <code>as_of</code> is the date the registry's sources were last checked.</li>
    <li>The registry version changes, with a <a href="/methodology/#m6-h">changelog</a> entry, whenever the published reference data or its meaning changes: records, entities, relationships, gap assessments or the definitions they use. An editorial change that affects neither, such as a typo in a note, may be published without a new version. Every change is a commit in the <a href="{repo}" rel="noopener">public repository</a>.</li>
    <li>data/gaps.json and data/changelog.json carry no version of their own: their place in a build is shown by the manifest only.</li>
    <li>Fetch the manifest first and compare each file's SHA-256. A mismatch means the file came from a different build, for example while a new version propagates through caches; fetch again later.</li>
    <li>The hashes are published by the same site as the files. They show that the files you fetched belong to one build and were not changed after it; they are not a signature, and they do not show who published the files or that their content is accurate. Accuracy rests on the cited sources, which each record links to.</li>
    <li>When the data a gap rests on changes, the build fails until the gap is re-assessed. Each gap in data/gaps.json stores the records it was assessed against and a digest of that data (<code>assessed_fingerprint</code>), which a consumer can recompute.</li>
    <li>A gap with <code>entity_assessments</code> is assessed per entity: for each entity, the records documenting each evidence dimension defined in <code>entity_assessment</code> (legal approval, governance event, staffing, premises, operational activity, outputs, documented non-commencement, documented discontinuation). Only a VERIFIED FACT about the entity can document a dimension. An entity resolves only through a published resolution path (documented operation, documented non-commencement, or documented discontinuation after operation), never on a legal approval, a governance event or missing records, and stays listed while the others remain open; the gap resolves when every entity has. An empty dimension means no qualifying record is recorded here, not that the thing does not exist.</li>
  </ul>
</section>
<section aria-labelledby="d6-h">
  <h2 id="d6-h"><span class="section-number">06</span>Coverage and limits</h2>
  <p class="prose">The registry holds what it has documented so far: {len(model.records)} records, {len(model.entities)} entities and {len(model.relationships)} relationships. It is not a complete map of Morocco's AI ecosystem, and an absent organisation, relationship or record is a gap in coverage. Public availability is not use, a signature or an announcement is not delivery, and a target is not an outcome. The <a href="/methodology/">methodology</a> sets out what the registry does not establish, and the <a href="/registry/gaps/">gap register</a> lists {len(gaps["gaps"])} questions it cannot yet answer. Whether others use the data, and how, is not measured.</p>
</section>
<section aria-labelledby="d7-h">
  <h2 id="d7-h"><span class="section-number">07</span>Which answers can be recomputed</h2>
  <p class="prose">An answer is reproducible when it follows from the published data and published rules. Some parts rest on judgments that the data records but cannot derive; they are marked below. matrix.json publishes the rules for its derived fields, row order and caveats under <code>derivation</code>; registry/gaps/gaps.json publishes the gap checks and the digest algorithm.</p>
  <h3 id="d7-q8">Q8: organisations and projects</h3>
  {_table("Q8: what can be recomputed", ["Part of the answer", "Status", "From"], q8_rows, "")}
  <h3 id="d7-q9">Q9: official targets and recorded progress</h3>
  {_table("Q9: what can be recomputed", ["Part of the answer", "Status", "From"], q9_rows, "")}
</section>
<section aria-labelledby="d8-h">
  <h2 id="d8-h"><span class="section-number">08</span>Checking the data yourself</h2>
  <p class="prose"><a href="/{CONSUMER}"><code>/{CONSUMER}</code></a> (also in the <a href="{repo}/blob/main/{CONSUMER}" rel="noopener">repository</a>) reads only the published JSON. It uses the Python 3.10+ standard library and does not import this site's code. It stops with an error if a reference is missing, a value is undefined or the files do not belong to the same build.</p>
  <ul class="prose">
    <li><code>python3 registry_consumer.py verify</code>: checks the manifest and every reference. It also recomputes the matrix, the GAP-05 list, each gap's data checks and digest, and compares them with the published files.</li>
    <li><code>python3 registry_consumer.py relationship ministry-digital-transition operates idarati-ai</code>: a relationship, its classification, and each supporting record with its source, dates and limits.</li>
    <li><code>python3 registry_consumer.py gap GAP-03</code>: what a gap establishes and does not, with the result of its data checks.</li>
    <li><code>python3 registry_consumer.py q8</code> and <code>q9</code>: the reproducible parts of those answers.</li>
  </ul>
  <p class="prose">By default it reads {SITE}. Use <code>--source</code> with another address or a local copy of the site.</p>
</section>
<section aria-labelledby="d9-h">
  <h2 id="d9-h"><span class="section-number">09</span>Changes to the data contract</h2>
  <p class="prose">A breaking change makes data that a consumer accepted under one version fail under the next. Each is listed here, in the manifest (<code>breaking_changes</code>) and in the <a href="/methodology/#m6-h">changelog</a>. Old values are not accepted as aliases, so a consumer built for an earlier version fails rather than misreads the data.</p>
  {_table("Breaking changes to the published data", ["Version", "Field", "Old value", "New value", "Why", "Effect on an earlier consumer", "Migration"],
          [[escape(c["version"]), f'<code>{escape(c["file"])}</code> <code>{escape(c["field"])}</code>', f'<code>{escape(c["old"])}</code>',
            f'<code>{escape(c["new"])}</code>', escape(c["reason"]) + f" In v{escape(model.evidence['version'])} it applies to {sum(1 for r in matrix_rows(model) if r['documentation_basis'] == c['new'])} rows.",
            escape(c["consumer_effect"]), escape(c["migration"])] for c in BREAKING_CHANGES], "")}
  <p class="prose">Other changes in v0.5.0 add to the data without changing what existing values mean: a sentence in the qualifications of every Signed row, a sixth gap (GAP-06), and the evidence type <code>signed_instrument</code> in the manifest's vocabularies. A consumer that compares qualifications or gap lists exactly will see the additions.</p>
</section>
<section aria-labelledby="d10-h">
  <h2 id="d10-h"><span class="section-number">10</span>Corrections</h2>
  <p class="prose">Send corrections, with the record or entity identifier and a source, to <a href="mailto:{CONTACT}?subject=TheMoroccoAI.com%20%E2%80%94%20data%20correction">{CONTACT}</a>. Corrections are made in the canonical files and re-validated, then published as a new version, with the change listed in the changelog.</p>
</section>"""
    return page(model, path="/data/", title="Using the Registry Data — TheMoroccoAI",
                description="How to read, verify and reuse TheMoroccoAI's published JSON: files, identifiers, provenance, null values, versions, coverage limits and which answers can be recomputed.",
                body=body)


# ─── HOMEPAGE BLOCKS ──────────────────────────────────────────────────────

def render_methodology(model, changelog):
    n_rec, n_ent, n_rel = len(model.records), len(model.entities), len(model.relationships)
    types = ", ".join(f"{TYPE_SINGULAR.get(t, t).lower()} ({sum(1 for e in model.entities.values() if e['type'] == t)})"
                      for t in model.ontology["entity_types"])
    classes = "".join(f'<div class="legend-row">{badge(c)}<span class="legend-def">{escape(model.evidence["classifications"][c])}</span></div>'
                      for c in registry.CLASSIFICATIONS)
    sources = {}
    for r in model.records.values():
        sources[r["source_type"]] = sources.get(r["source_type"], 0) + 1
    source_line = "; ".join(f"{SOURCE_TYPE_LABELS[k].lower()}: {v}" for k, v in sorted(sources.items(), key=lambda kv: (-kv[1], kv[0])))
    repo = changelog["repository"]
    entries = []
    for c in changelog["entries"]:
        figures = (f' · v{escape(c["version"])} · {c["records"]} records, {c["entities"]} entities, {c["relationships"]} relationships'
                   if c.get("version") else "")
        ref = (f'<a href="{repo}/commit/{c["commit"]}" rel="noopener">{c["commit"][:7]}</a>' if c.get("commit")
               else f'<a href="{repo}/pull/{c["pull_request"]}" rel="noopener">pull request #{c["pull_request"]}</a>')
        changes = "".join(f"<li>{escape(x)}</li>" for x in c.get("changes", []))
        fixes = "".join(f"<li>{escape(x)}</li>" for x in c.get("corrections", []))
        fixes = f'<p class="change-sub">Corrections to previously published content</p><ul>{fixes}</ul>' if fixes else ""
        review = "".join(f"<li>{escape(x)}</li>" for x in c.get("review_fixes", []))
        fixes += f'<p class="change-sub">Found in pre-release review (never published)</p><ul>{review}</ul>' if review else ""
        breaking = "".join(f"<li>{escape(x)}</li>" for x in c.get("breaking_changes", []))
        fixes += f'<p class="change-sub">Breaking changes to the data contract</p><ul>{breaking}</ul>' if breaking else ""
        entries.append(f"""<li class="change">
  <p class="change-meta"><time datetime="{c["date"]}">{escape(human_date(c["date"]))}</time> · {ref}{figures}</p>
  <h3>{escape(c["title"])}</h3>
  <ul>{changes}</ul>{fixes}
</li>""")
    body = f"""<header class="page-head">
  <p class="breadcrumb"><a href="/registry/">Registry</a> / Methodology</p>
  <p class="label">MAI-METHOD — How the registry works</p>
  <h1>Methodology, limits and changelog</h1>
  <p class="lede">What the registry documents, what it does not establish, how evidence is admitted, and how claims are corrected. The rules below are enforced by the validator and tests that run on every change.</p>
  <p class="notice"><strong>Independent.</strong> TheMoroccoAI is not affiliated with, endorsed by or operated by the Government of Morocco or any institution it lists. No institution has adopted or designated it as a reference.</p>
</header>
<section aria-labelledby="m1-h">
  <h2 id="m1-h"><span class="section-number">01</span>What the registry documents</h2>
  <p class="prose">Version {escape(model.evidence["version"])}, sources checked {escape(human_date(model.as_of))}: {n_rec} evidence records, {n_ent} entities and {n_rel} typed relationships. Entity types: {escape(types)}. Each record carries the source URL, a verbatim excerpt, the publication and retrieval dates, and one classification:</p>
  <div class="legend">{classes}</div>
  <p class="prose">Sources by type: {escape(source_line)}. Primary sources are preferred; secondary press may support only an announced plan or an unverified claim.</p>
</section>
<section aria-labelledby="m2-h">
  <h2 id="m2-h"><span class="section-number">02</span>What it does not establish</h2>
  <ul class="prose">
    <li><strong>Completeness.</strong> The registry covers what it has documented so far. An absent organisation, project or sector is a gap in coverage, not evidence of absence in Morocco.</li>
    <li><strong>Use and outcomes.</strong> Public availability is not adoption. No usage, accuracy, performance or impact figure is recorded as fact.</li>
    <li><strong>Delivery of targets and plans.</strong> Official targets and announced plans are shown as such, never as outcomes.</li>
    <li><strong>Current operation.</strong> An operational stage rests on its latest evidence; operation after that date is not reconfirmed.</li>
    <li><strong>Legal identity.</strong> A matching name does not make two organisations the same legal entity; such links are labelled as associations.</li>
    <li><strong>Official status.</strong> Records quote public sources; they are not official statements, and the registry speaks for no institution.</li>
  </ul>
</section>
<section aria-labelledby="m3-h">
  <h2 id="m3-h"><span class="section-number">03</span>How evidence is admitted</h2>
  <ul class="prose">
    <li>A record is added only after the original source has been retrieved and the excerpt matched against it.</li>
    <li>A lifecycle stage beyond "announced" needs a verified record that declares that stage. A signature, announcement, procurement notice, market clearance or official gazette text never establishes operation: a gazette text shows legal establishment, not activity.</li>
    <li>An operational or pilot claim states its basis (public availability, an operator's report of use, or an independent source) and names the operator separately from any developer or provider.</li>
    <li>Inferences drawn by the registry are labelled independent analysis and need at least two records.</li>
    <li>Candidates that do not meet these rules are not published.</li>
  </ul>
</section>
<section aria-labelledby="m4-h">
  <h2 id="m4-h"><span class="section-number">04</span>Unsupported, conflicting and outdated claims</h2>
  <ul class="prose">
    <li>Statements the registry could not check are kept only as unverified claims, with a note saying what was not checked.</li>
    <li>Where sources conflict or are insufficient, the stage is "unresolved", with the reason stated.</li>
    <li>A record whose quotation still matches its source but whose claim later evidence contradicts is marked superseded and can no longer set a stage. It stays visible.</li>
    <li>Questions the evidence cannot yet answer are published in the <a href="/registry/gaps/">evidence gap register</a>, with what is established, what is not and what would resolve them. A gap must be re-assessed whenever a new record concerns it.</li>
    <li>When the latest evidence for an operational claim is more than 12 months old, the <a href="/registry/questions/#q7-h">questions page</a> says current operation has not been reconfirmed. Elapsed time never changes a stage by itself.</li>
  </ul>
</section>
<section aria-labelledby="m5-h">
  <h2 id="m5-h"><span class="section-number">05</span>Corrections and reuse</h2>
  <p class="prose">Corrections are made in the data, re-validated and published as a new commit on the <a href="{repo}" rel="noopener">public repository</a>, so every change is visible in its history. The record's verification note says what changed and why. Corrections with a source can be sent to <a href="mailto:{CONTACT}?subject=TheMoroccoAI.com%20%E2%80%94%20correction">{CONTACT}</a>.</p>
  <p class="prose">The data is published as <a href="/data/evidence.json">evidence.json</a> and <a href="/data/ontology.json">ontology.json</a>, with the gap register and derived files; <a href="/data/">Using the registry data</a> explains how to read and verify them. No content or data licence has been declared yet; that is the owner's decision.</p>
</section>
<section aria-labelledby="m6-h">
  <h2 id="m6-h"><span class="section-number">06</span>Changelog</h2>
  <p class="prose">{escape(changelog["note"])}</p>
  <ol class="changelog">{"".join(entries)}</ol>
</section>"""
    return page(model, path="/methodology/", current="methodology",
                title="Methodology, Limits and Changelog — TheMoroccoAI",
                description="How TheMoroccoAI's evidence registry admits, classifies and corrects claims, what it does not establish, and a changelog tied to its public repository.",
                body=body)


def render_acquisition(model):
    n_rec, n_ent, n_rel = len(model.records), len(model.entities), len(model.relationships)
    mail = f"mailto:{CONTACT}?subject=TheMoroccoAI.com%20%E2%80%94%20confidential%20acquisition%20enquiry"
    body = f"""<header class="page-head">
  <p class="label">MAI-ACQ — Acquisition</p>
  <h1>Acquisition</h1>
  <p class="lede">TheMoroccoAI.com and its reference assets are privately held and available for strategic acquisition. Confidential enquiries: <a href="{mail}">{CONTACT}</a>. This page separates what exists today, which can be inspected, from the owner's view of its potential, which is set out in the <a href="/#thesis">owner's thesis</a>.</p>
  <p class="notice"><strong>Independent.</strong> The asset is not a government platform. It is not affiliated with, endorsed by or operated by the Government of Morocco or any institution it lists, and no institution has adopted or designated it.</p>
</header>
<section aria-labelledby="a1-h">
  <h2 id="a1-h"><span class="section-number">01</span>What could be transferred</h2>
  <ul class="prose">
    <li>The TheMoroccoAI.com domain name.</li>
    <li>The site source: pages, static generator, validator, source checker and tests.</li>
    <li>The evidence registry and ontology data: version {escape(model.evidence["version"])}, {n_rec} records, {n_ent} entities, {n_rel} relationships.</li>
    <li>The visual identity and logo.</li>
  </ul>
  <p class="prose">No content or data licence has been declared. Bundled fonts remain under the SIL Open Font License.</p>
</section>
<section aria-labelledby="a2-h">
  <h2 id="a2-h"><span class="section-number">02</span>Existing assets and future potential</h2>
  {_table("Existing assets compared with potential", ["Exists today, and can be inspected", "Owner's view of potential (not established)"], [
      ["The exact-match domain TheMoroccoAI.com, serving this registry",
       "A national category name for AI in Morocco that cannot be recreated, only acquired"],
      [f'An evidence registry of {n_rec} sourced records and {n_ent} entities, each claim classified (<a href="/registry/">registry</a>)',
       "A category-level reference on Morocco's AI ecosystem"],
      ['Machine-readable data (<a href="/data/evidence.json">evidence.json</a>, <a href="/data/ontology.json">ontology.json</a>) and a <a href="/registry/questions/">questions page</a> generated from it',
       "A data layer that organisations working on Moroccan AI could build on"],
      ['Published rules enforced by a validator and automated tests on every change (<a href="/methodology/">methodology</a>)',
       "A governed reference whose method can be audited"],
      ['A public change history tied to each published version (<a href="/methodology/#m6-h">changelog</a>)',
       "Provenance a successor can keep extending without a break in its record"],
      ["An English edition", "Arabic, French and Tamazight editions (planned, not published)"],
  ], "")}
  <p class="prose">Nothing on this site indicates that any institution or company has expressed interest. No price, traffic or revenue figures are published.</p>
</section>
<section aria-labelledby="a3-h">
  <h2 id="a3-h"><span class="section-number">03</span>Who it may suit, in the owner's view</h2>
  <p class="prose">Organisations that need a neutral, inspectable reference layer on Moroccan AI: AI companies entering African markets, investors focused on MENA–Africa technology, research and policy institutions, and data or media businesses. This is the owner's assessment; no interest from any specific party is implied.</p>
</section>
<section aria-labelledby="a4-h">
  <h2 id="a4-h"><span class="section-number">04</span>Confidential enquiry</h2>
  <p class="prose">Enquiries are handled confidentially: <a href="{mail}">{CONTACT}</a>.</p>
</section>"""
    return page(model, path="/acquisition/", current="acquisition",
                title="Acquisition — TheMoroccoAI",
                description="TheMoroccoAI.com is privately held. What could be transferred, what exists today compared with the owner's view of its potential, and a confidential enquiry address.",
                body=body)


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
        "version": escape(model.evidence["version"]),
        "records": str(len(model.records)),
        "entities": str(len(model.entities)),
        "relationships": str(len(model.relationships)),
        "domains": str(len(model.domains)),
        "entity-types": str(len(model.ontology["entity_types"])),
        "as-of": human_date(model.as_of).split(" ", 1)[-1] if model.as_of else "",
        "examples": "\n" + homepage_examples(model) + "\n    ",
    }


KIND_PHRASES = {"compute-infrastructure": "compute infrastructure", "digital-platform": "digital platform, not an AI application",
                "institute": "institute", "agreement": "agreement"}


def _stage_with_kind(model, e):
    kind = KIND_PHRASES.get(e.get("project_kind"), "")
    return f"{kind}; {stage_label(model, e).lower()}" if kind else stage_label(model, e).lower()


def _example(qid, question, answer, links):
    link_html = " · ".join(f'<a href="{href}">{escape(label)}</a>' for href, label in links)
    return f"""      <article class="example" aria-labelledby="{qid}">
        <h3 class="example-q" id="{qid}">{escape(question)}</h3>
        <div class="example-a">{answer}</div>
        <p class="example-links">Evidence: {link_html}</p>
      </article>"""


def homepage_examples(model):
    """Three questions answered entirely from the registry data, each linking to its supporting output."""
    ents, rels = model.entities, model.relationships
    out = []

    # 1. The documented status of Idarati AI.
    e = ents["idarati-ai"]
    f = deployment_facts(model, e)
    ops = ", ".join(_ent_link(model, o) for o, c in f["operators"] if c == "VERIFIED FACT") or "not documented"
    use = (" Public availability is not evidence of use: no usage, accuracy or outcome evidence is recorded."
           if set(model.records[x].get("status_basis") for x in f["status_ids"]) == {"public-availability-observed"} else "")
    out.append(_example(
        "ex-idarati", "What is the documented status of Idarati AI?",
        f'<p>{_ent_link(model, e["id"])}: {escape(stage_label(model, e))}. Operator: {ops}. '
        f'Basis: {escape("; ".join(f["bases"]))}. {escape(f["currency"])}.{escape(use)}</p>',
        [(entity_url(e["id"]), "entity page"), ("/registry/questions/#q6-h", "Q6 deployments")]
        + [(f"/registry/evidence/#{x}", x) for x in f["status_ids"]]))

    # 2. Morocco AI 2030: official targets versus what is verified.
    plan = ents["morocco-ai-2030"]
    targets = [r for r in model.records.values() if r["classification"] == "OFFICIAL TARGET" and plan["id"] in r["related_entities"]]
    included = [ents[r["object"]] for r in rels if r["subject"] == plan["id"] and r["predicate"] == "includes"]
    target_text = " ".join(f'{escape(r["claim"])} {escape(r["verification_note"])}' for r in targets)
    include_ids = sorted({x for r in rels if r["subject"] == plan["id"] and r["predicate"] == "includes" for x in r["evidence"]})
    parts = "; ".join(f'{_ent_link(model, x["id"])} ({escape(_stage_with_kind(model, x))})' for x in included)
    verified = [r for r in rels if r["subject"] == plan["id"] and r["classification"] == "VERIFIED FACT"]
    via = ", ".join(f'{escape(model.predicates[r["predicate"]]["label"])} {_ent_link(model, r["object"])}' for r in verified)
    via = f" Verified: it is {via}." if via else ""
    out.append(_example(
        "ex-2030", "What has Morocco AI 2030 set as targets, and what is verified so far?",
        f'<p>{target_text} The registry shows targets as targets, never as outcomes, and records no target as achieved.</p>'
        f'<p>The roadmap is recorded as including {len(included)} projects, on the basis of the ministry\'s presentation: {parts}.{via} '
        f'A project\'s status is not a measure of progress toward the quantified targets.</p>',
        [(entity_url(plan["id"]), "entity page")]
        + [(f"/registry/evidence/#{x}", x) for x in [r["evidence_id"] for r in targets] + include_ids]
        + [("/registry/questions/#q2-h", "Q2 projects by stage")]))

    # 3. Institutions documented as connected to compute and data-centre infrastructure.
    infra_tech = ("high-performance-computing", "data-centres")
    infra = sorted((x for x in ents.values() if x["type"] == "project" and (
        x.get("project_kind") == "compute-infrastructure"
        or any(r["subject"] == x["id"] and r["predicate"] == "applies" and r["object"] in infra_tech for r in rels))),
        key=lambda x: (x["lifecycle"] != "operational", x["name"].lower()))
    rows = []
    for x in infra:
        links = [r for r in rels if r["object"] == x["id"] and ents[r["subject"]]["type"] in ("institution", "company")]
        who = "; ".join(f'{_ent_link(model, r["subject"])}, {escape(model.predicates[r["predicate"]]["label"].removesuffix(" of"))} '
                        f'<span class="example-cls">({escape(r["classification"].lower())})</span>' for r in links) or "no organisation recorded"
        basis = ""
        if x["lifecycle"] in ("operational", "pilot"):
            f = deployment_facts(model, x)
            basis = f' (basis: {escape("; ".join(f["bases"]))}; {escape(f["currency"][0].lower() + f["currency"][1:])})'
        reported = [a for a in x.get("attributes") or [] if a["name"].startswith("Reported AI workloads")]
        work = "".join(f'; {escape(a["name"])}: {escape(a["value"][0].lower() + a["value"][1:])} {_ev_links([a["evidence"]])}' for a in reported)
        rows.append(f'<li>{_ent_link(model, x["id"])}, {escape(_stage_with_kind(model, x))}{basis}: {who}{work}</li>')
    announced = sum(1 for x in infra if x["lifecycle"] == "announced")
    ids = {x["id"] for x in infra}
    runs_ai = any({r["subject"], r["object"]} & ids and ents[r["subject"] if r["object"] in ids else r["object"]].get("project_kind") == "ai-application"
                  for r in rels)
    reports = any(a["name"].startswith("Reported AI workloads") for x in infra for a in x.get("attributes") or [])
    if not runs_ai and not reports:
        workload = ("Compute infrastructure is not an AI application: the registry documents capacity, not what runs on it, "
                    "and records no AI workload on these systems.")
    else:
        workload = ("Compute infrastructure is not an AI application. Reported AI workloads are shown only where a source states them, "
                    "with who reported them; they do not establish the scale, users or outcomes of AI use (GAP-03).")
    out.append(_example(
        "ex-infra", "Which institutions are documented as connected to computing and data-centre infrastructure?",
        f'<ul>{"".join(rows)}</ul><p>{announced} of these {len(infra)} projects are only announced or signed: no record shows them built '
        f'or running. A signature is recorded as a signature. {workload}</p>',
        [(f"/registry/evidence/#{x}", x) for x in sorted({y for i in infra for y in i["lifecycle_evidence"]})]
        + [("/registry/questions/#q5-h", "Q5 relationships"), ("/registry/questions/#q2-h", "Q2 projects by stage")]))
    return "\n".join(out)


def inject(html_text, blocks):
    for key, value in blocks.items():
        pattern = re.compile(rf"(<!--r:{re.escape(key)}-->)(.*?)(<!--/r:{re.escape(key)}-->)", re.S)
        if not pattern.search(html_text):
            raise SystemExit(f"index.html: missing marker <!--r:{key}-->")
        html_text = pattern.sub(lambda m: m.group(1) + value + m.group(3), html_text)
    return html_text


def sitemap(model):
    paths = (["/", "/registry/", "/registry/questions/", "/registry/matrix/", "/registry/gaps/", "/registry/evidence/", "/data/", "/methodology/", "/acquisition/"]
             + [entity_url(e) for e in sorted(model.entities)])
    urls = "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{model.as_of}</lastmod></url>\n" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def _json(data):
    return json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def outputs(model):
    gaps = registry.load(registry.ROOT / "data" / "gaps.json")
    files = {
        "registry/index.html": render_registry_index(model),
        "registry/evidence/index.html": render_evidence_index(model),
        "registry/questions/index.html": render_questions(model),
        "registry/matrix/index.html": render_matrix(model),
        "registry/matrix/matrix.json": _json({"registry_version": model.evidence["version"], "as_of": model.as_of,
                                              "scope": "Relationships recorded in this registry between organisations or initiatives and what they act on; not a complete map.",
                                              "derived_from": ["/data/ontology.json", "/data/evidence.json"],
                                              "derivation": matrix_derivation(), "documentation": "/data/",
                                              "rows": matrix_rows(model)}),
        "registry/gaps/index.html": render_gaps(model, gaps),
        "registry/gaps/gaps.json": _json({"registry_version": model.evidence["version"], "as_of": model.as_of, "note": gaps["note"],
                                          "derived_from": ["/data/gaps.json", "/data/ontology.json", "/data/evidence.json"],
                                          "states": gaps["states"], "entity_assessment": gaps.get("entity_assessment"),
                                          "documentation": "/data/", "derivation": gap_derivation(),
                                          "gaps": gap_register(model, gaps)}),
        "methodology/index.html": render_methodology(model, registry.load(registry.ROOT / "data" / "changelog.json")),
        "acquisition/index.html": render_acquisition(model),
        "sitemap.xml": sitemap(model),
    }
    files["data/manifest.json"] = _json(manifest(model, files))
    files["data/index.html"] = render_data_reference(model, gaps, json.loads(files["data/manifest.json"]))
    for eid, e in model.entities.items():
        files[f"registry/{eid}/index.html"] = render_entity(model, e)
    files["index.html"] = inject((ROOT / "index.html").read_text(encoding="utf-8"), homepage_blocks(model))
    return files


def main(argv):
    check = "--check" in argv
    evidence, ontology = registry.load_all()
    errors = registry.validate(evidence, ontology) + registry.validate_gaps(registry.load(registry.ROOT / "data" / "gaps.json"), evidence, ontology)
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
