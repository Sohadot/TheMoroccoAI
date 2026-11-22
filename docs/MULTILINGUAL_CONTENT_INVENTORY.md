# Multilingual content inventory: `/`, `/registry/` and `/methodology/` (Sprints 19B-3 and 19B-4)

Generated from `i18n/en/messages.json` and `build.page_requirements()`; `tests/test_extraction.py` fails if a unit any extracted page needs is missing from this list. English is authoritative (TMA-DEC-007). **No translation exists and no page is registered for localization.** Review rules: [TRANSLATION_REVIEW_POLICY.md](TRANSLATION_REVIEW_POLICY.md) (TMA-DEC-008).

## Summary

| | Count |
|---|---|
| Catalog units the three pages render with the current data | 302 (`/` 164, `/registry/` 77, `/methodology/` 102) |
| Listed below, including conditional units | 320 |
| New in Sprint 19B-4 (homepage, shared vocabulary, translation-policy disclosure) | 161 |
| Canonical content units (resolved from `data/`, never copied) | 208 (`/` 42) |
| Glossary terms required | 13 |
| Deferred texts | 0 |

Semantic classes of the listed units: disclosure 19, heading 53, interface 62, metadata 11, navigation 26, prose 53, qualifier 47, term 49.

Columns: **kind** is the semantic class (`qualifier` marks text that limits a claim or states what the reference does not establish; `disclosure` marks ownership, independence and authority statements; `term` labels are linked to glossary vocabulary). **Context** names the unit a fragment is inserted into: such fragments must be translated together with their parent. **Status** is `new` for units added in Sprint 19B-4 and `reused` for units already in the catalog. Localization-only shell units (language switcher, translation notice, fallback marker and the translation-policy disclosure `shell.translation_policy`) render only on localized pages and are listed in `build.LOCALIZATION_ONLY_MESSAGES`, not below. A `⏎` marks a line break kept in the English source so that the homepage stays byte-identical; line breaks inside a paragraph are insignificant whitespace and a translation need not reproduce them.

## Catalog units

| Key | Kind | English source | Placeholders | Rendered by | Scope | Status | Context |
|---|---|---|---|---|---|---|---|
| `breadcrumb.registry` | navigation | Registry | — | both renderers | /methodology/ | reused | — |
| `date.day_month_year` | interface | {day} {month} {year} | `{day}`, `{month}`, `{year}` | `human_date()` | shell (every page) | reused | — |
| `date.month.02` | interface | February | — | `human_date()` | /methodology/ | reused | — |
| `date.month.06` | interface | June | — | — | / | reused | — |
| `date.month.10` | interface | October | — | `human_date()` | shell (every page) | reused | — |
| `date.month_year` | interface | {month} {year} | `{month}`, `{year}` | — | / | reused | — |
| `disclosure.ownership_statement` | disclosure | TheMoroccoAI.com is an independently developed digital asset owned and operated by Sohadot. It is not affiliated with, endorsed by, or operated on behalf of any government, public institution, or third-party organization or company. References to external organizations, initiatives and sources do not imply their endorsement of or participation in the project. | — | `page()` / `footer()` | /, /methodology/ | reused | — |
| `facts.currency.recent` | qualifier | Latest supporting evidence {date}, within {months} months; operation after that date not reconfirmed | `{date}`, `{months}` | `deployment_facts()` | / | new | — |
| `facts.currency.stale` | qualifier | Latest supporting evidence {date} is more than {months} months old; current operation has not been reconfirmed | `{date}`, `{months}` | `deployment_facts()` | / (conditional: data-dependent label) | new | — |
| `facts.observed` | interface | {date} (observed) | `{date}` | `deployment_facts()` | / | new | inside `facts.currency.*` |
| `footer.as_of` | interface | as of {date} | `{date}` | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.disclaimer` | disclosure | Not affiliated with the Government of Morocco | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `footer.link.acquisition` | interface | Acquisition | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `footer.link.data` | interface | Data | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `footer.link.evaluation` | interface | Independent evaluation | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `footer.link.methodology` | interface | Methodology | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `footer.link.ownership` | interface | Ownership and independence | — | `page()` / `footer()` | /methodology/, /registry/ | reused | — |
| `footer.owner_note` | disclosure | Owned and operated by Sohadot | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `footer.registry_version` | interface | Registry v{version} | `{version}` | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.tagline` | interface | Independent evidence registry | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `link.data_guide` | interface | Using the registry data | — | both renderers | /methodology/, /registry/ | reused | page.methodology.corrections.reuse / page.registry.data.intro |
| `link.gap_register` | interface | evidence gap register | — | both renderers | /methodology/, /registry/ | reused | page.methodology.conflicts.gaps / page.registry.start.matrix |
| `page.home.access.evidence.text` | prose | Source, verbatim excerpt, dates and classification for every claim. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.evidence.title` | navigation | Evidence records | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.evidence_json.text` | prose | All {count} evidence records, machine-readable. | `{count}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.gaps.text` | prose | What the registry cannot yet establish, and what evidence would settle it. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.gaps.title` | navigation | Evidence gaps | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.h2` | heading | Inspect the evidence{break}and the data. | `{break}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.matrix.text` | prose | Who is documented as connected to which project, how, and on what evidence. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.matrix.title` | navigation | Institutional matrix | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.methodology.text` | prose | Admission rules, limits, corrections and the public change history. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.methodology.title` | navigation | Methodology and changelog | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.number` | heading | 02 — ACCESS | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.ontology_json.text` | prose | {types} entity types, {entities} entities and their typed relationships. | `{entities}`, `{types}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.questions.text` | prose | Answers computed from the data, each linked to its records. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.questions.title` | navigation | Questions | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.registry.text` | prose | Every entity with its relationships, lifecycle stage and evidence. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.access.registry.title` | navigation | Registry | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.acquire.number` | heading | 06 — ACQUISITION | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.acquire.text` | disclosure | {ownership} The domain and its reference assets are available for strategic acquisition. The {acquisition} separates what exists today from the owner’s view of its potential. Confidential enquiries: {email}. | `{acquisition}`, `{email}`, `{ownership}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.acquire.text.link` | navigation | acquisition page | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.acquire.text` |
| `page.home.acquire.title` | heading | Ownership and acquisition | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.coverage.h2` | heading | What the registry{break}covers so far. | `{break}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.coverage.intro` | qualifier | {count} domains, each populated only from verified records. Coverage is partial: if an organisation or project is absent, the registry has not documented it yet. That is not evidence that it does not exist. | `{count}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.coverage.number` | heading | 01 — COVERAGE | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.description` | metadata | An independent, evidence-backed registry of institutions, initiatives, projects, models and datasets in Morocco's AI ecosystem, with sources, classifications and open JSON data. Not a government platform. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.domain.cta.status` | interface | Open | — | `homepage_blocks` | / | new | — |
| `page.home.domain.cta.text` | prose | Every entity, relationship and source excerpt, plus the JSON data. | — | `homepage_blocks` | / | new | — |
| `page.home.domain.cta.title` | navigation | Open the full registry → | — | `homepage_blocks` | / | new | link label |
| `page.home.domain.empty.status` | qualifier | Not yet sourced | — | `homepage_blocks` | / (conditional) | new | — |
| `page.home.domain.empty.text` | qualifier | No verified record yet. This domain stays empty until primary sources support an entry. | — | `homepage_blocks` | / (conditional) | new | — |
| `page.home.domain.members` | prose | {names}. | `{names}` | `homepage_blocks` | / | new | — |
| `page.home.domain.members_more` | prose | {names} and {count} more. | `{count}`, `{names}` | `homepage_blocks` | / | new | — |
| `page.home.domain.records.one` | interface | {count} record | `{count}` | `homepage_blocks` | / | new | — |
| `page.home.domain.records.other` | interface | {count} records | `{count}` | `homepage_blocks` | / | new | — |
| `page.home.evaluate.cta` | navigation | Start independent evaluation | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.evaluate.label` | heading | {code} — Independent evaluation | `{code}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.evaluate.note` | disclosure | Independent feedback is welcome. Participation does not imply endorsement, affiliation or institutional recognition, and no external validation of the registry has been performed. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.evaluate.text` | prose | Take part in a structured, voluntary evaluation of the registry’s methodology, evidence transparency and research usability: an introductory task of about 5 minutes, or a specialist set of 15–20 minutes. No account or tracking, and nothing is sent unless you choose to email your report. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.evaluate.title` | heading | Evaluate TheMoroccoAI | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.ex.2030.included` | prose | The roadmap is recorded as including {count} projects, on the basis of the ministry's presentation: {projects}. | `{count}`, `{projects}` | `homepage_examples` | / | new | — |
| `page.home.ex.2030.question` | heading | What has Morocco AI 2030 set as targets, and what is verified so far? | — | `homepage_examples` | / | new | — |
| `page.home.ex.2030.status_qualifier` | qualifier | A project's status is not a measure of progress toward the quantified targets. | — | `homepage_examples` | / | new | — |
| `page.home.ex.2030.targets_qualifier` | qualifier | The registry shows targets as targets, never as outcomes, and records no target as achieved. | — | `homepage_examples` | / | new | — |
| `page.home.ex.2030.verified` | prose | Verified: it is {relations}. | `{relations}` | `homepage_examples` | / | new | follows `page.home.ex.2030.included` |
| `page.home.ex.evidence` | interface | Evidence: {links} | `{links}` | `homepage_examples` | / | new | evidence link line under each example |
| `page.home.ex.idarati.answer` | prose | {entity}: {stage}. Operator: {operators}. Basis: {basis}. {currency}. | `{basis}`, `{currency}`, `{entity}`, `{operators}`, `{stage}` | `homepage_examples` | / | new | — |
| `page.home.ex.idarati.question` | heading | What is the documented status of Idarati AI? | — | `homepage_examples` | / | new | — |
| `page.home.ex.idarati.use_qualifier` | qualifier | Public availability is not evidence of use: no usage, accuracy or outcome evidence is recorded. | — | `homepage_examples` | / | new | follows `page.home.ex.idarati.answer` |
| `page.home.ex.infra.announced` | qualifier | {announced} of these {total} projects are only announced or signed: no record shows them built or running. A signature is recorded as a signature. | `{announced}`, `{total}` | `homepage_examples` | / | new | — |
| `page.home.ex.infra.basis` | qualifier | (basis: {basis}; {currency}) | `{basis}`, `{currency}` | `homepage_examples` | / | new | inside each infrastructure list item |
| `page.home.ex.infra.question` | heading | Which institutions are documented as connected to computing and data-centre infrastructure? | — | `homepage_examples` | / | new | — |
| `page.home.ex.infra.workload.none` | qualifier | Compute infrastructure is not an AI application: the registry documents capacity, not what runs on it, and records no AI workload on these systems. | — | `homepage_examples` | / (conditional) | new | — |
| `page.home.ex.infra.workload.reported` | qualifier | Compute infrastructure is not an AI application. Reported AI workloads are shown only where a source states them, with who reported them; they do not establish the scale, users or outcomes of AI use (GAP-03). | — | `homepage_examples` | / | new | — |
| `page.home.ex.link.entity_page` | navigation | entity page | — | `homepage_examples` | / | new | — |
| `page.home.ex.link.q2` | navigation | Q2 projects by stage | — | `homepage_examples` | / | new | — |
| `page.home.ex.link.q5` | navigation | Q5 relationships | — | `homepage_examples` | / | new | — |
| `page.home.ex.link.q6` | navigation | Q6 deployments | — | `homepage_examples` | / | new | — |
| `page.home.examples.h2` | heading | Three questions{break}the evidence answers. | `{break}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.examples.intro` | qualifier | Each answer below is generated from the registry data when the site is built, and links to the records behind it. More answers are on the {questions}. | `{questions}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.examples.intro.link` | navigation | questions page | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.examples.intro` |
| `page.home.examples.number` | heading | 03 — QUESTIONS | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.footer.languages` | qualifier | {english} · AR · FR · {tamazight} planned | `{english}`, `{tamazight}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.footer.links` | navigation | {ownership} · {methodology} · {data} · {evaluation} · {acquisition} | `{acquisition}`, `{data}`, `{evaluation}`, `{methodology}`, `{ownership}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.footer.ownership` | navigation | Ownership | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.footer.links` |
| `page.home.hero.cta.examples` | navigation | See questions it answers | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.cta.registry` | navigation | Open the registry | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.h1` | heading | Morocco’s AI ecosystem, {emphasis} | `{emphasis}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.h1.emphasis` | heading | on the record. | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.hero.h1` |
| `page.home.hero.label` | heading | {code} — Independent evidence registry | `{code}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.lede` | prose | TheMoroccoAI.com is an {emphasis} of the institutions, initiatives, ⏎       projects, models and datasets in Morocco’s artificial intelligence ecosystem. Every entry cites ⏎       its source, with a verbatim excerpt and dates, and facts, official targets, announced plans and ⏎       the registry’s own analysis are labelled separately. | `{emphasis}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.lede.emphasis` | prose | independent registry | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.hero.lede` |
| `page.home.hero.meta` | interface | Independent evidence registry · AI · Morocco | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.notice` | disclosure | {independent} Not affiliated with the Government of Morocco, ⏎       and not endorsed or operated by any institution it lists. Records quote public sources; they are ⏎       not official statements. | `{independent}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.hero.notice.independent` | disclosure | Independent. | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.hero.notice` |
| `page.home.jsonld.description` | metadata | Independent evidence registry for Morocco's AI ecosystem. Not affiliated with the Government of Morocco. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.h2` | heading | Method{break}and limits. | `{break}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.more` | navigation | Full methodology, limits and changelog → | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.number` | heading | 04 — METHOD | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rule.1` | qualifier | Targets and plans are never shown as outcomes | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rule.2` | qualifier | Public availability is never counted as use; no outcome is recorded as fact | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rule.3` | qualifier | Conflicting evidence is marked unresolved; outdated claims are marked superseded, not hidden | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rule.4` | qualifier | Versioned data with a {changelog}; no silent changes | `{changelog}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rule.4.link` | qualifier | public changelog | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.method.rule.4` |
| `page.home.method.rule.5` | qualifier | Coverage is partial: absence from the registry is not absence in Morocco | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rule.6` | qualifier | The registry establishes no official status, endorsement or legal identity | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rules.label` | heading | {code} — Editorial rules | `{code}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.method.rules.text` | qualifier | Every claim in the registry cites a source whose type is labelled, with a verbatim excerpt and dates. ⏎         Primary sources are preferred; press may support only an announced plan or an unverified claim. ⏎         Verified facts, official targets, announced plans, the registry’s own analysis and unverified ⏎         claims are kept separate. The rules are enforced by a validator and tests on every change. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.nav.coverage` | navigation | Coverage | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.nav.method` | navigation | Method | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.nav.questions` | navigation | Questions | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.nav.thesis` | navigation | Thesis | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.og_description` | metadata | Independent research infrastructure documenting Morocco's evolving AI ecosystem through structured evidence and transparent methodology. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.og_title` | metadata | TheMoroccoAI — Mapping Morocco's AI Landscape | — | `homepage.tmpl` / `render_homepage` | / | new | og:title and twitter:title (social sharing) |
| `page.home.twitter_description` | metadata | Structured evidence and independent research on Morocco's evolving AI ecosystem. | — | `homepage.tmpl` / `render_homepage` | / | new | twitter:description |
| `page.home.twitter_image_alt` | metadata | TheMoroccoAI — mapping Morocco's AI landscape. | — | `homepage.tmpl` / `render_homepage` | / | new | twitter:image:alt |
| `shell.og_image_alt` | metadata | TheMoroccoAI — independent research infrastructure mapping Morocco's AI landscape. | — | `page()` / `social_image_meta()` | /, /methodology/, /registry/ | new | og:image:alt of the shared social image on every page |
| `page.home.status.as_of` | interface | Sources checked | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.edition` | interface | Edition | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.edition_value` | qualifier | English · AR, FR, TZM planned | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.entities` | interface | Entities | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.label` | interface | Current registry coverage | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.records` | interface | Evidence records | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.relationships` | interface | Relationships | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.status.version` | interface | Registry version | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.1.body` | prose | In the owner’s view, Morocco has long served as a knowledge bridge between Africa, Europe and the Arab world, and the AI transition continues that role rather than breaking with it. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.1.title` | heading | Civilizational positioning | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.2.body` | prose | TheMoroccoAI.com names the category at the national level in one short .com. The owner considers such a name scarce: it cannot be recreated, only acquired. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.2.title` | heading | Category name | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.3.body` | prose | Arabic, Tamazight, French and English editions, each serving a different institutional audience. Only the English edition is published; the others are planned. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.3.title` | heading | Language architecture | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.4.body` | prose | As AI-generated content multiplies, the owner expects governed references, with explicit sources, versions and claim restraint, to become scarce and valuable. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.4.title` | heading | Governance as a moat | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.5.body` | prose | Morocco’s {roadmap} and the 2030 targets of {digital} are recorded in the registry as targets. The owner’s view is that a reference layer is most useful before the market matures. | `{digital}`, `{roadmap}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.5.body.roadmap` | prose | AI 2030 roadmap | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.thesis.5.body` |
| `page.home.thesis.5.title` | heading | Timing | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.6.body` | prose | The intended role is a category-level reference on Moroccan AI. That role is an aim: no institution has adopted, endorsed or designated the site. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.6.title` | heading | Category-level reference | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.cell.ambition` | disclosure | {code} · Ambition | `{code}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.cell.intended_role` | disclosure | {code} · Intended role | `{code}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.cell.owner_view` | disclosure | {code} · Owner’s view | `{code}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.framing` | disclosure | {framing} This section is the owner’s interpretation of why a structured reference on Moroccan AI matters and what role this site is intended to play. It is not sourced evidence, a government designation or a prediction. Sourced facts are in the {registry}. | `{framing}`, `{registry}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.framing.lead` | disclosure | Framing, not findings. | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.thesis.framing` |
| `page.home.thesis.framing.registry` | navigation | registry | — | `homepage.tmpl` / `render_homepage` | / | new | inside `page.home.thesis.framing` |
| `page.home.thesis.h2` | heading | The owner’s{break}strategic thesis. | `{break}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.number` | heading | 05 — THESIS | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.quote` | prose | “The intelligence of a civilization entering AI.” | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.thesis.quote.attribution` | disclosure | — the owner’s founding line for the project | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.title` | metadata | TheMoroccoAI — Independent Evidence Registry for Morocco’s AI Ecosystem | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.1.definition` | prose | The institutional, infrastructural, regulatory and talent capacity of a nation to absorb and produce AI systems at scale. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.1.term` | heading | AI Readiness | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.2.definition` | prose | A geographic and cultural position that works as a translation and routing layer between knowledge traditions. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.2.term` | heading | Civilizational Node | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.3.definition` | prose | A governed knowledge resource that defines category terms without depending on a single institutional authority. Used here as an aim, not as a claim of official status. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.3.term` | heading | Sovereign Reference | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.4.definition` | prose | Structuring multilingual content as institutional access layers, not as translations of one primary text. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.4.term` | heading | Language Architecture | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.5.definition` | prose | A domain whose name, structure and reference depth could make it the default reference for a category. A strategic aim. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.5.term` | heading | Category Anchor | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.6.definition` | prose | The accumulated risk of an AI ecosystem that grows without explicit sources, claim restraint or versioned accountability. | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.6.term` | heading | Governance Debt | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.head` | heading | Framing vocabulary | — | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.home.vocab.note` | disclosure | The owner’s working terms. They are not part of the registry’s ontology, which is published as {file}. | `{file}` | `homepage.tmpl` / `render_homepage` | / | new | — |
| `page.methodology.admission.basis` | prose | An operational or pilot claim states its basis (public availability, an operator's report of use, or an independent source) and names the operator separately from any developer or provider. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.admission.h2` | heading | How evidence is admitted | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.admission.inference` | prose | Inferences drawn by the registry are labelled independent analysis and need at least two records. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.admission.retrieved` | prose | A record is added only after the original source has been retrieved and the excerpt matched against it. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.admission.stage` | prose | A lifecycle stage beyond "announced" needs a verified record that declares that stage. A signature, announcement, procurement notice, market clearance or official gazette text never establishes operation: a gazette text shows legal establishment, not activity. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.admission.unpublished` | prose | Candidates that do not meet these rules are not published. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.breadcrumb` | navigation | Methodology | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.changelog.breaking` | heading | Breaking changes to the data contract | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.changelog.corrections` | heading | Corrections to previously published content | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.changelog.figures` | interface | v{version} · {records} records, {entities} entities, {relationships} relationships | `{entities}`, `{records}`, `{relationships}`, `{version}` | `render_methodology` | /methodology/ | reused | changelog entry metadata line |
| `page.methodology.changelog.h2` | heading | Changelog | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.changelog.pull_request` | interface | pull request #{number} | `{number}` | `render_methodology` | /methodology/ | reused | changelog entry reference |
| `page.methodology.changelog.review_fixes` | heading | Found in pre-release review (never published) | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.conflicts.gaps` | prose | Questions the evidence cannot yet answer are published in the {gap_register}, with what is established, what is not and what would resolve them. A gap must be re-assessed whenever a new record concerns it. | `{gap_register}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.conflicts.h2` | heading | Unsupported, conflicting and outdated claims | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.conflicts.questions_page` | interface | questions page | — | `render_methodology` | /methodology/ | reused | page.methodology.conflicts.recency |
| `page.methodology.conflicts.recency` | qualifier | When the latest evidence for an operational claim is more than 12 months old, the {questions_page} says current operation has not been reconfirmed. Elapsed time never changes a stage by itself. | `{questions_page}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.conflicts.superseded` | qualifier | A record whose quotation still matches its source but whose claim later evidence contradicts is marked superseded and can no longer set a stage. It stays visible. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.conflicts.unresolved` | qualifier | Where sources conflict or are insufficient, the stage is "unresolved", with the reason stated. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.conflicts.unverified` | qualifier | Statements the registry could not check are kept only as unverified claims, with a note saying what was not checked. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.corrections.h2` | heading | Corrections and reuse | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.corrections.process` | prose | Corrections are made in the data, re-validated and published as a new commit on the {repository}, so every change is visible in its history. The record's verification note says what changed and why. Corrections with a source can be sent to {contact}. | `{contact}`, `{repository}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.corrections.repository` | interface | public repository | — | `render_methodology` | /methodology/ | reused | page.methodology.corrections.process |
| `page.methodology.corrections.reuse` | disclosure | The data is published as {evidence_json} and {ontology_json}, with the gap register and derived files; {data_guide} explains how to read and verify them. No content or data licence has been declared yet; that is the owner's decision. | `{data_guide}`, `{evidence_json}`, `{ontology_json}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.description` | metadata | How TheMoroccoAI's evidence registry admits, classifies and corrects claims, what it does not establish, and a changelog tied to its public repository. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.documents.h2` | heading | What the registry documents | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.documents.source_count` | interface | {type}: {count} | `{count}`, `{type}` | `render_methodology` | /methodology/ | reused | {sources} list items |
| `page.methodology.documents.sources` | prose | Sources by type: {sources}. Primary sources are preferred; secondary press may support only an announced plan or an unverified claim. | `{sources}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.documents.summary` | prose | Version {version}, sources checked {date}: {records} evidence records, {entities} entities and {relationships} typed relationships. Entity types: {types}. Each record carries the source URL, a verbatim excerpt, the publication and retrieval dates, and one classification: | `{date}`, `{entities}`, `{records}`, `{relationships}`, `{types}`, `{version}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.documents.type_count` | interface | {type} ({count}) | `{count}`, `{type}` | `render_methodology` | /methodology/ | reused | {types} list items |
| `page.methodology.h1` | heading | Methodology, limits and changelog | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.label` | interface | {code} — How the registry works | `{code}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.lede` | prose | What the registry documents, what it does not establish, how evidence is admitted, and how claims are corrected. The rules below are enforced by the validator and tests that run on every change. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.completeness` | qualifier | {term} The registry covers what it has documented so far. An absent organisation, project or sector is a gap in coverage, not evidence of absence in Morocco. | `{term}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.completeness.term` | qualifier | Completeness. | — | `render_methodology` | /methodology/ | reused | page.methodology.limits.completeness (bold lead-in) |
| `page.methodology.limits.h2` | heading | What it does not establish | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.identity` | qualifier | {term} A matching name does not make two organisations the same legal entity; such links are labelled as associations. | `{term}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.identity.term` | qualifier | Legal identity. | — | `render_methodology` | /methodology/ | reused | page.methodology.limits.identity (bold lead-in) |
| `page.methodology.limits.operation` | qualifier | {term} An operational stage rests on its latest evidence; operation after that date is not reconfirmed. | `{term}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.operation.term` | qualifier | Current operation. | — | `render_methodology` | /methodology/ | reused | page.methodology.limits.operation (bold lead-in) |
| `page.methodology.limits.status` | qualifier | {term} Records quote public sources; they are not official statements, and the registry speaks for no institution. | `{term}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.status.term` | qualifier | Official status. | — | `render_methodology` | /methodology/ | reused | page.methodology.limits.status (bold lead-in) |
| `page.methodology.limits.targets` | qualifier | {term} Official targets and announced plans are shown as such, never as outcomes. | `{term}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.targets.term` | qualifier | Delivery of targets and plans. | — | `render_methodology` | /methodology/ | reused | page.methodology.limits.targets (bold lead-in) |
| `page.methodology.limits.use` | qualifier | {term} Public availability is not adoption. No usage, accuracy, performance or impact figure is recorded as fact. | `{term}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.limits.use.term` | qualifier | Use and outcomes. | — | `render_methodology` | /methodology/ | reused | page.methodology.limits.use (bold lead-in) |
| `page.methodology.notice` | disclosure | {independent} {statement} No institution has adopted or designated it as an official reference. | `{independent}`, `{statement}` | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.ownership.h2` | heading | Ownership and editorial independence | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.ownership.private` | disclosure | This is a privately governed research resource, not an official registry. Source attribution is not a claim of institutional partnership or endorsement. Evidence classifications, limitations and corrections are documented below. English is the authoritative editorial language; other language editions are planned and are not represented as complete. | — | `render_methodology` | /methodology/ | reused | — |
| `page.methodology.title` | metadata | Methodology, Limits and Changelog — TheMoroccoAI | — | `render_methodology` | /methodology/ | reused | — |
| `page.notice.independent` | disclosure | Independent. | — | both renderers | /methodology/, /registry/ | reused | page.methodology.notice / page.registry.notice |
| `page.registry.coverage.count` | interface | {entities} entities · {records} records | `{entities}`, `{records}` | `render_registry_index` | /registry/ | reused | domain cell |
| `page.registry.coverage.gap` | qualifier | No record has been verified for this domain yet. It stays empty rather than holding unsourced entries. | — | `render_registry_index` | /registry/ (conditional) | reused | domain cell when a domain has no entity |
| `page.registry.coverage.h2` | heading | Coverage by domain | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.coverage.none` | interface | 0 entities | — | `render_registry_index` | /registry/ (conditional) | reused | domain cell when a domain has no entity |
| `page.registry.data.all_evidence` | prose | {link}, each record addressable as {pattern}. | `{link}`, `{pattern}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.all_evidence_link` | interface | All evidence on one page | — | `render_registry_index` | /registry/ | reused | page.registry.data.all_evidence |
| `page.registry.data.evidence` | prose | {file}: every evidence record, with its source URL, dates, verbatim excerpts, classification and verification status. | `{file}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.h2` | heading | Machine-readable data | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.intro` | prose | {data_guide} describes the files, identifiers, null values and versions, says which answers can be recomputed, and links to an example that checks the data independently. | `{data_guide}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.manifest` | prose | {file}: the list of published JSON files, with the SHA-256 of each in this version. | `{file}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.ontology` | prose | {file}: entity types, domains, predicates, entities and typed relationships, each citing its evidence. | `{file}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.state` | prose | {state}: what the registry currently records (classifications, documented lifecycle stages, official target records and open gaps), generated from {file}. | `{file}`, `{state}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.data.state_link` | interface | Reference state | — | `render_registry_index` | /registry/ | reused | page.registry.data.state |
| `page.registry.description` | metadata | Independent, evidence-backed registry of Morocco's AI ecosystem: institutions, initiatives and projects tied to primary sources, with facts, targets and plans labelled separately. | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.entities.h2` | heading | All entities | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.h1` | heading | Morocco’s AI ecosystem, {emphasis} | `{emphasis}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.h1.emphasis` | heading | on the record. | — | `render_registry_index` | /registry/ | reused | page.registry.h1 |
| `page.registry.jsonld.description` | metadata | Primary-source evidence records and an ontology of institutions, initiatives and projects in Morocco's AI ecosystem, with claims classified as verified fact, official target, announced plan, independent analysis or unverified claim. | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.jsonld.name` | metadata | TheMoroccoAI Evidence Registry | — | `render_registry_index` | /, /registry/ | reused | — |
| `page.registry.jsonld.place` | metadata | Morocco | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.label` | interface | {code} — Reference Registry v{version} | `{code}`, `{version}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.lede` | prose | Institutions, initiatives and projects in Morocco’s artificial intelligence ecosystem. Every entry cites its source, whose type is labelled, with a verbatim excerpt and dates, and {emphasis}. | `{emphasis}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.lede.emphasis` | prose | facts, official targets, announced plans and our own analysis are labelled separately | — | `render_registry_index` | /registry/ | reused | page.registry.lede |
| `page.registry.legend.h2` | heading | How claims are classified | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.legend.note` | qualifier | Counts cover evidence records, plus relationships for independent analysis. An official target is never shown as an outcome. A record marked “partial” states what could not be checked. | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.method.h2` | heading | Method and limits | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.method.selective` | qualifier | The registry is deliberately selective: it omits facts it could not verify against an original source, and an absent entry is a gap in coverage. Corrections can be sent to {contact}. | `{contact}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.method.validation` | prose | Each record was retrieved from its source on the stated retrieval date, and its excerpt was matched against the retrieved text. An automated validator checks every build. It requires unique identifiers, https source URLs, valid dates and complete fields, and that every entity and relationship cites existing evidence. It also blocks forward-looking wording in records classified as fact, and rejects any relationship whose classification its evidence does not support. | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.notice` | disclosure | {independent} TheMoroccoAI is an independent reference project. It is not affiliated with, endorsed by or operated by the Government of Morocco or any institution listed here. Records quote public sources and link to them; they are not official statements. | `{independent}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.records.one` | interface | {count} record | `{count}` | `render_registry_index` | /registry/ | reused | entity list item metadata (one record) |
| `page.registry.records.other` | interface | {count} records | `{count}` | `render_registry_index` | /registry/ | reused | entity list item metadata (other counts) |
| `page.registry.start.chain` | prose | The fullest chain in this version runs from {ai2030} to the announced {jazari_network}, its planned core institute {jazari_root} and the {jazari_x0} convention signed in Fès. It then goes on to the signatories, the stated technologies and the targeted sectors. Each page shows the source excerpt, the publication and retrieval dates, and the classification of every claim. | `{ai2030}`, `{jazari_network}`, `{jazari_root}`, `{jazari_x0}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.start.h2` | heading | Start here | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.start.matrix` | prose | The {matrix} shows which organisations are documented as connected to which projects and initiatives, and on what evidence. The {gaps} lists what the registry cannot yet establish. | `{gaps}`, `{matrix}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.start.matrix_link` | interface | institutional matrix | — | `render_registry_index` | /registry/ | reused | page.registry.start.matrix |
| `page.registry.start.questions` | prose | {questions} lists which organisations have documented AI activity, which projects are operational or only announced, which models and datasets are public, and which relationships are verified. Each answer links to its evidence. | `{questions}` | `render_registry_index` | /registry/ | reused | — |
| `page.registry.start.questions_link` | interface | Questions the registry answers | — | `render_registry_index` | /registry/ | reused | page.registry.start.questions |
| `page.registry.stats.checked` | interface | Sources checked | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.stats.entities` | interface | Entities | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.stats.format` | interface | Format | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.stats.format_value` | interface | Static HTML · JSON | — | `render_registry_index` | /registry/ | reused | stats panel (Format) |
| `page.registry.stats.label` | interface | Registry status | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.stats.records` | interface | Evidence records | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.stats.relationships` | interface | Relationships | — | `render_registry_index` | /registry/ | reused | — |
| `page.registry.title` | metadata | Reference Registry — TheMoroccoAI | — | `render_registry_index` | /registry/ | reused | — |
| `punct.list_comma` | interface | ,  | — | both renderers | /, /methodology/ | reused | {types} list in page.methodology.documents.summary |
| `punct.list_semicolon` | interface | ;  | — | both renderers | /, /methodology/ | reused | {sources} list in page.methodology.documents.sources |
| `shell.nav.acquisition` | interface | Acquisition | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `shell.nav.evidence` | interface | Evidence | — | `page()` / `footer()` | /methodology/, /registry/ | reused | — |
| `shell.nav.gaps` | interface | Gaps | — | `page()` / `footer()` | /methodology/, /registry/ | reused | — |
| `shell.nav.label` | interface | Primary | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `shell.nav.matrix` | interface | Matrix | — | `page()` / `footer()` | /methodology/, /registry/ | reused | — |
| `shell.nav.methodology` | interface | Methodology | — | `page()` / `footer()` | /methodology/, /registry/ | reused | — |
| `shell.nav.questions` | interface | Questions | — | `page()` / `footer()` | /methodology/, /registry/ | reused | — |
| `shell.nav.registry` | interface | Registry | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `shell.skip_link` | interface | Skip to content | — | `page()` / `footer()` | /, /methodology/, /registry/ | reused | — |
| `vocab.classification_inline.announced_plan` | term | announced plan | — | `homepage_examples` | / (conditional: data-dependent label) | new | — |
| `vocab.classification_inline.independent_analysis` | term | independent analysis | — | `homepage_examples` | / (conditional: data-dependent label) | new | — |
| `vocab.classification_inline.official_target` | term | official target | — | `homepage_examples` | / (conditional: data-dependent label) | new | — |
| `vocab.classification_inline.unverified_claim` | term | unverified claim | — | `homepage_examples` | / (conditional: data-dependent label) | new | — |
| `vocab.classification_inline.verified_fact` | term | verified fact | — | `homepage_examples` | / | new | — |
| `vocab.entity_type.company.plural` | term | Companies | — | — | /registry/ | reused | — |
| `vocab.entity_type.company.singular` | term | Company | — | — | /methodology/ | reused | — |
| `vocab.entity_type.dataset.plural` | term | Datasets | — | — | /registry/ | reused | — |
| `vocab.entity_type.dataset.singular` | term | Dataset | — | — | /methodology/ | reused | — |
| `vocab.entity_type.event.plural` | term | Events | — | — | /registry/ | reused | — |
| `vocab.entity_type.event.singular` | term | Event | — | — | /methodology/ | reused | — |
| `vocab.entity_type.initiative.plural` | term | Initiatives | — | — | /registry/ | reused | — |
| `vocab.entity_type.initiative.singular` | term | Initiative | — | — | /methodology/ | reused | — |
| `vocab.entity_type.institution.plural` | term | Institutions | — | — | /registry/ | reused | — |
| `vocab.entity_type.institution.singular` | term | Institution | — | — | /methodology/ | reused | — |
| `vocab.entity_type.legal_instrument.plural` | term | Legal instruments | — | — | /registry/ | reused | — |
| `vocab.entity_type.legal_instrument.singular` | term | Legal instrument | — | — | /methodology/ | reused | — |
| `vocab.entity_type.model.plural` | term | Models | — | — | /registry/ | reused | — |
| `vocab.entity_type.model.singular` | term | Model | — | — | /methodology/ | reused | — |
| `vocab.entity_type.project.plural` | term | Projects | — | — | /registry/ | reused | — |
| `vocab.entity_type.project.singular` | term | Project | — | — | /methodology/ | reused | — |
| `vocab.entity_type.sector.plural` | term | Sectors | — | — | /registry/ | reused | — |
| `vocab.entity_type.sector.singular` | term | Sector | — | — | /methodology/ | reused | — |
| `vocab.entity_type.technology.plural` | term | Technologies | — | — | /registry/ | reused | — |
| `vocab.entity_type.technology.singular` | term | Technology | — | — | /methodology/ | reused | — |
| `vocab.lifecycle.announced` | term | Announced | — | `stage_label()` | / | new | — |
| `vocab.lifecycle.availability_suffix` | qualifier | (public availability; use not documented) | — | `stage_label()` | / | new | appended to an operational or pilot stage label |
| `vocab.lifecycle.discontinued` | term | Discontinued | — | `stage_label()` | / (conditional: data-dependent label) | new | — |
| `vocab.lifecycle.in_development` | term | In development | — | `stage_label()` | / (conditional: data-dependent label) | new | — |
| `vocab.lifecycle.operational` | term | Operational | — | `stage_label()` | / | new | — |
| `vocab.lifecycle.pilot` | term | Pilot | — | `stage_label()` | / (conditional: data-dependent label) | new | — |
| `vocab.lifecycle.released` | term | Released | — | `stage_label()` | / (conditional: data-dependent label) | new | — |
| `vocab.lifecycle.unresolved` | term | Unresolved | — | `stage_label()` | / (conditional: data-dependent label) | new | — |
| `vocab.project_kind_phrase.agreement` | term | agreement | — | `_stage_with_kind()` | / | new | — |
| `vocab.project_kind_phrase.compute_infrastructure` | term | compute infrastructure | — | `_stage_with_kind()` | / | new | — |
| `vocab.project_kind_phrase.digital_platform` | term | digital platform, not an AI application | — | `_stage_with_kind()` | / | new | — |
| `vocab.project_kind_phrase.institute` | term | institute | — | `_stage_with_kind()` | / (conditional: data-dependent label) | new | — |
| `vocab.source_type.academic_journal` | term | Peer-reviewed journal | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.academic_preprint` | term | Academic preprint | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.government_portal` | term | Government portal | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.government_publication` | term | Government publication | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.independent_list` | term | Independent list | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.intergovernmental_organization` | term | Intergovernmental organisation | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.investor_publication` | term | Investor publication | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.organization_website` | term | Organisation's own website | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.regulator` | term | Regulator | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.secondary_press` | term | Secondary press | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.signatory_organization` | term | Signatory organisation | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.state_news_agency` | term | State news agency | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.source_type.technical_repository` | term | Technical repository | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | reused | — |
| `vocab.status_basis.independent_listing` | qualifier | independent listing | — | `deployment_facts()` | / | new | — |
| `vocab.status_basis.independent_report_of_use` | qualifier | independent report of use | — | `deployment_facts()` | / (conditional: data-dependent label) | new | — |
| `vocab.status_basis.operator_report_of_use` | qualifier | operator's report of use | — | `deployment_facts()` | / (conditional: data-dependent label) | new | — |
| `vocab.status_basis.public_availability_observed` | qualifier | public availability on the operator's own service (usage not documented) | — | `deployment_facts()` | / | new | — |

## Canonical content units (not in the catalog)

Their English text is read from canonical data at render time, so it cannot drift from the reference; a translation records the fingerprint of that canonical text.

| Unit pattern | Count on these pages |
|---|---|
| `attribute:<id>:text` | 2 |
| `changelog:<id>:text` | 97 |
| `classification:<id>:definition` | 5 |
| `domain:<id>:label` | 7 |
| `evidence:<id>:claim` | 2 |
| `evidence:<id>:verification_note` | 2 |
| `ontology:<id>:name` | 65 |
| `ontology:<id>:status` | 25 |
| `predicate:<id>:label` | 3 |

- `classification:<code>:definition`, `domain:<key>:label`, `ontology:<id>:name|status`, `evidence:<id>:claim|verification_note` and `predicate:<key>:label` are addressed by canonical ids.
- `changelog:<item id>:text` and `attribute:<item id>:text` are addressed by the stable ids in `i18n/changelog-identity.json` and `i18n/attribute-identity.json` (see *Identity-bound texts* below).
- `ontology:<id>:name` has kind `name` and needs `name_basis`.

## Homepage specifics

- **Template.** `tools/templates/homepage.tmpl` holds the structure, styles and markers. Every visible, metadata (title, description, Open Graph), JSON-LD and accessibility text (`aria-label`, skip link) is a catalog token; `render_homepage()` fills it. `index.html` is generated and checked byte for byte by `build.py --check`.
- **Generated figures** keep their `<!--r:key-->` markers and are filled from the data, never from the catalog.
- **Links.** Internal page links go through `link()` or `{{href:…}}`, so a localized homepage links to the same-language page when it exists and otherwise to English, marked `hreflang="en"`. Data files, anchors and the contact address stay literal.
- **Presentation rules kept in code** (documented, English-neutral where possible): a predicate label's trailing ` of` is dropped in the infrastructure list; the first letter of an inserted currency sentence or attribute value is lower-cased.
- **Not translated on the homepage:** the brand, the Arabic tagline and Arabic domain labels (already Arabic, marked `lang="ar"`), the Tamazight name `ⵜⵣⵎ`, the language code `EN`, the format name `JSON`, decorative glyphs (`◆`, `→`) and the contact address with its subject line.

## Not translated

| Content | Reason |
|---|---|
| Evidence and entity IDs, page codes (`MAI-METHOD`, `MAI-REG`, `MAI-ROOT-001`, `MAI-EV-NNNN`) | Identifiers; passed as isolated placeholders, never in catalog text |
| Classification codes in badges (`VERIFIED FACT`, …) | Canonical codes; matched across languages |
| File names and paths (`evidence.json`, `/data/manifest.json`, …) and code | Technical tokens |
| Contact address and the e-mail subject line | Technical token; messages reach an English-speaking owner |
| Brand (`TheMoroccoAI`, `TheMoroccoAI.com`) and commit references | Names and identifiers |
| Numbers, counts, dates and versions | Filled from canonical data; only month names are localized |
| Source excerpts | Not on these pages; never translated (TMA-DEC-007 Q6) |

## Conditional units

`page_requirements()` reports what a page renders **with the current data**. Units marked *conditional* render only for other data (an empty domain; a project with another lifecycle stage, status basis or kind; no reported AI workload). If the data changes so that one appears and it is not translated, the localized page becomes ineligible and is withdrawn; it never shows English text. Translators should therefore translate them with the rest of the page.

## Identity-bound texts (no longer deferred)

Sprint 19B-3 deferred the 97 changelog texts on `/methodology/`. Since Sprint 19B-4 each changelog text and each entity attribute text has a stable id in an explicit identity map (`i18n/changelog-identity.json`, 97 items; `i18n/attribute-identity.json`, 66 items). Identity survives reordering; an edit keeps the id and makes approved translations stale; a new text needs a new id; retired ids are never reused; an unregistered, orphaned or ambiguous text stops the build. Neither positional nor content-hash identity is used. `python3 tools/i18n.py --identity-report` proposes repairs and never applies them.

Plural forms: counts use two English forms (`records.one`, `records.other`); Arabic has more plural categories. Translators must phrase these units neutrally until plural selection is added (see Arch section 15).

## Translation pilot and terminology (Sprint 19B-5)

- **Pilot:** a representative sample of 42 of these units per language was drafted in Arabic and French for owner review. The drafts are kept outside the repository; see [TRANSLATION_PILOT.md](TRANSLATION_PILOT.md).
- **Terminology:** `i18n/glossary.json` now lists 14 editorial concepts (`concept:<id>`). Each English form occurs in the catalog above. No label is approved.

## Social-sharing metadata

Every page carries the shared social image (`assets/social/themoroccoai-og.png`) with `og:image:alt` from `shell.og_image_alt`. The homepage also has its own Open Graph title and description and X title, description and image alt. Those are catalog units, so a localized page gets translated values. The image itself carries English text: it is the same in every language.

