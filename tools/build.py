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
    "initiative": "Initiatives",
    "event": "Events",
    "project": "Projects",
    "legal_instrument": "Legal instruments",
    "technology": "Technologies",
    "sector": "Sectors",
}
TYPE_SINGULAR = {
    "institution": "Institution", "initiative": "Initiative", "event": "Event", "project": "Project",
    "legal_instrument": "Legal instrument", "technology": "Technology", "sector": "Sector",
}
SOURCE_TYPE_LABELS = {
    "government_portal": "Government portal",
    "government_publication": "Government publication",
    "state_news_agency": "State news agency",
    "signatory_organization": "Signatory organisation",
    "intergovernmental_organization": "Intergovernmental organisation",
    "regulator": "Regulator",
}
SIGIL = ('<svg viewBox="0 0 28 28" fill="none" aria-hidden="true" focusable="false">'
         '<polygon points="14,2 26,8 26,20 14,26 2,20 2,8" stroke="#1a2e4a" stroke-width="1" fill="none"/>'
         '<polygon points="14,7 21,10.5 21,17.5 14,21 7,17.5 7,10.5" stroke="#b8892a" stroke-width="0.75" fill="none"/>'
         '<circle cx="14" cy="14" r="2.5" fill="#b8892a"/></svg>')


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
    return f"""<li class="evidence-card" id="{rid}">
  <div class="evidence-top"><a class="evidence-id" href="/registry/evidence/#{rid}">{rid}</a>{badge(r["classification"])}</div>
  <{heading}>{escape(r["title"])}</{heading}>
  <p class="evidence-claim">{escape(r["claim"])}</p>
  <blockquote class="evidence-quote"{quote_lang} cite="{escape(r["source_url"])}">{quotes}</blockquote>
  <dl class="evidence-meta">
    <dt>Source</dt><dd><a href="{escape(r["source_url"])}" rel="noopener">{escape(r["source_organization"])}</a> · {escape(SOURCE_TYPE_LABELS[r["source_type"]])}</dd>
    <dt>Published</dt><dd>{escape(human_date(r["publication_date"]))}</dd>
    <dt>Retrieved</dt><dd>{escape(human_date(r["retrieval_date"]))}</dd>{target}
    <dt>Verification</dt><dd>{status_html}</dd>{entities}
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

    facts = [("Type", TYPE_SINGULAR[e["type"]])]
    if e.get("domain"):
        facts.append(("Domain", model.domains[e["domain"]]))
    if e.get("status"):
        facts.append(("Status", e["status"]))
    facts.append(("Identifier", f"<code>{escape(eid)}</code>"))
    facts.append(("Records", str(len(e["evidence"]))))
    facts_html = "".join(
        f"<dt>{k}</dt><dd>{v if k == 'Identifier' else escape(v)}</dd>" for k, v in facts
    )
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
        "institution": "Organization", "initiative": "Project", "project": "Project", "event": "Event",
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
    paths = ["/", "/registry/", "/registry/evidence/"] + [entity_url(e) for e in sorted(model.entities)]
    urls = "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{model.as_of}</lastmod></url>\n" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def outputs(model):
    files = {
        "registry/index.html": render_registry_index(model),
        "registry/evidence/index.html": render_evidence_index(model),
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
