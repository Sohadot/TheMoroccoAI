# Multilingual content inventory: `/registry/` and `/methodology/` (Sprint 19B-3)

Generated from `i18n/en/messages.json` and `build.page_requirements()` at the time of extraction; `tests/test_extraction.py` fails if a unit either page needs is missing from this list. English is authoritative (TMA-DEC-007). **No translation exists and neither page is registered for localization.**

## Summary

| | Count |
|---|---|
| Catalog units either page renders with the current data | 155 (`/registry/` 77, `/methodology/` 102) |
| Newly extracted in this sprint | 134 (132 rendered with the current data, 2 conditional) |
| Reused from Sprints 19B-1/19B-2 (shell, footer, ownership statement, dates) | 23 |
| Also extracted, used by the label maps on other pages only (`vocab.*` source types not on these pages) | 0 |
| Canonical content units (resolved from `data/`, never copied) | 102 |
| Glossary terms required (entity types) | 10 |
| Deferred canonical changelog texts on `/methodology/` | 97 |

Semantic classes of the catalog units: disclosure 8, heading 19, interface 46, metadata 7, navigation 2, prose 22, qualifier 18, term 33.

Columns: **kind** is the semantic class (`qualifier` marks text that limits a claim or states what the reference does not establish; `disclosure` marks ownership, independence and authority statements; `term` labels are linked to glossary vocabulary). **Context** names the unit a fragment is inserted into: such fragments must be translated together with their parent.

## Catalog units

| Key | Kind | English source | Placeholders | Rendered by | Scope | Status | Context |
|---|---|---|---|---|---|---|---|
| `breadcrumb.registry` | navigation | Registry | — | both renderers | /methodology/ | new | — |
| `date.day_month_year` | interface | {day} {month} {year} | `{day}`, `{month}`, `{year}` | `human_date()` | shell (every page) | reused | — |
| `date.month.02` | interface | February | — | `human_date()` | shell (every page) | reused | — |
| `date.month.10` | interface | October | — | `human_date()` | shell (every page) | reused | — |
| `disclosure.ownership_statement` | disclosure | TheMoroccoAI.com is an independently developed digital asset owned and operated by Sohadot. It is not affiliated with, endorsed by, or operated on behalf of any government, public institution, or third-party organization or company. References to external organizations, initiatives and sources do not imply their endorsement of or participation in the project. | — | `page()` / `footer()` | /methodology/ | reused | — |
| `footer.as_of` | interface | as of {date} | `{date}` | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.disclaimer` | disclosure | Not affiliated with the Government of Morocco | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.link.acquisition` | interface | Acquisition | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.link.data` | interface | Data | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.link.evaluation` | interface | Independent evaluation | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.link.methodology` | interface | Methodology | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.link.ownership` | interface | Ownership and independence | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.owner_note` | disclosure | Owned and operated by Sohadot | — | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.registry_version` | interface | Registry v{version} | `{version}` | `page()` / `footer()` | shell (every page) | reused | — |
| `footer.tagline` | interface | Independent evidence registry | — | `page()` / `footer()` | shell (every page) | reused | — |
| `link.data_guide` | interface | Using the registry data | — | both renderers | shared | new | page.methodology.corrections.reuse / page.registry.data.intro |
| `link.gap_register` | interface | evidence gap register | — | both renderers | shared | new | page.methodology.conflicts.gaps / page.registry.start.matrix |
| `page.methodology.admission.basis` | prose | An operational or pilot claim states its basis (public availability, an operator's report of use, or an independent source) and names the operator separately from any developer or provider. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.admission.h2` | heading | How evidence is admitted | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.admission.inference` | prose | Inferences drawn by the registry are labelled independent analysis and need at least two records. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.admission.retrieved` | prose | A record is added only after the original source has been retrieved and the excerpt matched against it. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.admission.stage` | prose | A lifecycle stage beyond "announced" needs a verified record that declares that stage. A signature, announcement, procurement notice, market clearance or official gazette text never establishes operation: a gazette text shows legal establishment, not activity. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.admission.unpublished` | prose | Candidates that do not meet these rules are not published. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.breadcrumb` | navigation | Methodology | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.changelog.breaking` | heading | Breaking changes to the data contract | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.changelog.corrections` | heading | Corrections to previously published content | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.changelog.figures` | interface | v{version} · {records} records, {entities} entities, {relationships} relationships | `{entities}`, `{records}`, `{relationships}`, `{version}` | `render_methodology` | /methodology/ | new | changelog entry metadata line |
| `page.methodology.changelog.h2` | heading | Changelog | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.changelog.pull_request` | interface | pull request #{number} | `{number}` | `render_methodology` | /methodology/ | new | changelog entry reference |
| `page.methodology.changelog.review_fixes` | heading | Found in pre-release review (never published) | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.conflicts.gaps` | prose | Questions the evidence cannot yet answer are published in the {gap_register}, with what is established, what is not and what would resolve them. A gap must be re-assessed whenever a new record concerns it. | `{gap_register}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.conflicts.h2` | heading | Unsupported, conflicting and outdated claims | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.conflicts.questions_page` | interface | questions page | — | `render_methodology` | /methodology/ | new | page.methodology.conflicts.recency |
| `page.methodology.conflicts.recency` | qualifier | When the latest evidence for an operational claim is more than 12 months old, the {questions_page} says current operation has not been reconfirmed. Elapsed time never changes a stage by itself. | `{questions_page}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.conflicts.superseded` | qualifier | A record whose quotation still matches its source but whose claim later evidence contradicts is marked superseded and can no longer set a stage. It stays visible. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.conflicts.unresolved` | qualifier | Where sources conflict or are insufficient, the stage is "unresolved", with the reason stated. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.conflicts.unverified` | qualifier | Statements the registry could not check are kept only as unverified claims, with a note saying what was not checked. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.corrections.h2` | heading | Corrections and reuse | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.corrections.process` | prose | Corrections are made in the data, re-validated and published as a new commit on the {repository}, so every change is visible in its history. The record's verification note says what changed and why. Corrections with a source can be sent to {contact}. | `{contact}`, `{repository}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.corrections.repository` | interface | public repository | — | `render_methodology` | /methodology/ | new | page.methodology.corrections.process |
| `page.methodology.corrections.reuse` | disclosure | The data is published as {evidence_json} and {ontology_json}, with the gap register and derived files; {data_guide} explains how to read and verify them. No content or data licence has been declared yet; that is the owner's decision. | `{data_guide}`, `{evidence_json}`, `{ontology_json}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.description` | metadata | How TheMoroccoAI's evidence registry admits, classifies and corrects claims, what it does not establish, and a changelog tied to its public repository. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.documents.h2` | heading | What the registry documents | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.documents.source_count` | interface | {type}: {count} | `{count}`, `{type}` | `render_methodology` | /methodology/ | new | {sources} list items |
| `page.methodology.documents.sources` | prose | Sources by type: {sources}. Primary sources are preferred; secondary press may support only an announced plan or an unverified claim. | `{sources}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.documents.summary` | prose | Version {version}, sources checked {date}: {records} evidence records, {entities} entities and {relationships} typed relationships. Entity types: {types}. Each record carries the source URL, a verbatim excerpt, the publication and retrieval dates, and one classification: | `{date}`, `{entities}`, `{records}`, `{relationships}`, `{types}`, `{version}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.documents.type_count` | interface | {type} ({count}) | `{count}`, `{type}` | `render_methodology` | /methodology/ | new | {types} list items |
| `page.methodology.h1` | heading | Methodology, limits and changelog | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.label` | interface | {code} — How the registry works | `{code}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.lede` | prose | What the registry documents, what it does not establish, how evidence is admitted, and how claims are corrected. The rules below are enforced by the validator and tests that run on every change. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.completeness` | qualifier | {term} The registry covers what it has documented so far. An absent organisation, project or sector is a gap in coverage, not evidence of absence in Morocco. | `{term}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.completeness.term` | qualifier | Completeness. | — | `render_methodology` | /methodology/ | new | page.methodology.limits.completeness (bold lead-in) |
| `page.methodology.limits.h2` | heading | What it does not establish | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.identity` | qualifier | {term} A matching name does not make two organisations the same legal entity; such links are labelled as associations. | `{term}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.identity.term` | qualifier | Legal identity. | — | `render_methodology` | /methodology/ | new | page.methodology.limits.identity (bold lead-in) |
| `page.methodology.limits.operation` | qualifier | {term} An operational stage rests on its latest evidence; operation after that date is not reconfirmed. | `{term}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.operation.term` | qualifier | Current operation. | — | `render_methodology` | /methodology/ | new | page.methodology.limits.operation (bold lead-in) |
| `page.methodology.limits.status` | qualifier | {term} Records quote public sources; they are not official statements, and the registry speaks for no institution. | `{term}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.status.term` | qualifier | Official status. | — | `render_methodology` | /methodology/ | new | page.methodology.limits.status (bold lead-in) |
| `page.methodology.limits.targets` | qualifier | {term} Official targets and announced plans are shown as such, never as outcomes. | `{term}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.targets.term` | qualifier | Delivery of targets and plans. | — | `render_methodology` | /methodology/ | new | page.methodology.limits.targets (bold lead-in) |
| `page.methodology.limits.use` | qualifier | {term} Public availability is not adoption. No usage, accuracy, performance or impact figure is recorded as fact. | `{term}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.limits.use.term` | qualifier | Use and outcomes. | — | `render_methodology` | /methodology/ | new | page.methodology.limits.use (bold lead-in) |
| `page.methodology.notice` | disclosure | {independent} {statement} No institution has adopted or designated it as an official reference. | `{independent}`, `{statement}` | `render_methodology` | /methodology/ | new | — |
| `page.methodology.ownership.h2` | heading | Ownership and editorial independence | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.ownership.private` | disclosure | This is a privately governed research resource, not an official registry. Source attribution is not a claim of institutional partnership or endorsement. Evidence classifications, limitations and corrections are documented below. English is the authoritative editorial language; other language editions are planned and are not represented as complete. | — | `render_methodology` | /methodology/ | new | — |
| `page.methodology.title` | metadata | Methodology, Limits and Changelog — TheMoroccoAI | — | `render_methodology` | /methodology/ | new | — |
| `page.notice.independent` | disclosure | Independent. | — | both renderers | shared | new | page.methodology.notice / page.registry.notice |
| `page.registry.coverage.count` | interface | {entities} entities · {records} records | `{entities}`, `{records}` | `render_registry_index` | /registry/ | new | domain cell |
| `page.registry.coverage.h2` | heading | Coverage by domain | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.all_evidence` | prose | {link}, each record addressable as {pattern}. | `{link}`, `{pattern}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.all_evidence_link` | interface | All evidence on one page | — | `render_registry_index` | /registry/ | new | page.registry.data.all_evidence |
| `page.registry.data.evidence` | prose | {file}: every evidence record, with its source URL, dates, verbatim excerpts, classification and verification status. | `{file}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.h2` | heading | Machine-readable data | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.intro` | prose | {data_guide} describes the files, identifiers, null values and versions, says which answers can be recomputed, and links to an example that checks the data independently. | `{data_guide}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.manifest` | prose | {file}: the list of published JSON files, with the SHA-256 of each in this version. | `{file}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.ontology` | prose | {file}: entity types, domains, predicates, entities and typed relationships, each citing its evidence. | `{file}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.state` | prose | {state}: what the registry currently records (classifications, documented lifecycle stages, official target records and open gaps), generated from {file}. | `{file}`, `{state}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.data.state_link` | interface | Reference state | — | `render_registry_index` | /registry/ | new | page.registry.data.state |
| `page.registry.description` | metadata | Independent, evidence-backed registry of Morocco's AI ecosystem: institutions, initiatives and projects tied to primary sources, with facts, targets and plans labelled separately. | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.entities.h2` | heading | All entities | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.h1` | heading | Morocco’s AI ecosystem, {emphasis} | `{emphasis}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.h1.emphasis` | heading | on the record. | — | `render_registry_index` | /registry/ | new | page.registry.h1 |
| `page.registry.jsonld.description` | metadata | Primary-source evidence records and an ontology of institutions, initiatives and projects in Morocco's AI ecosystem, with claims classified as verified fact, official target, announced plan, independent analysis or unverified claim. | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.jsonld.name` | metadata | TheMoroccoAI Evidence Registry | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.jsonld.place` | metadata | Morocco | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.label` | interface | {code} — Reference Registry v{version} | `{code}`, `{version}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.lede` | prose | Institutions, initiatives and projects in Morocco’s artificial intelligence ecosystem. Every entry cites its source, whose type is labelled, with a verbatim excerpt and dates, and {emphasis}. | `{emphasis}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.lede.emphasis` | prose | facts, official targets, announced plans and our own analysis are labelled separately | — | `render_registry_index` | /registry/ | new | page.registry.lede |
| `page.registry.legend.h2` | heading | How claims are classified | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.legend.note` | qualifier | Counts cover evidence records, plus relationships for independent analysis. An official target is never shown as an outcome. A record marked “partial” states what could not be checked. | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.method.h2` | heading | Method and limits | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.method.selective` | qualifier | The registry is deliberately selective: it omits facts it could not verify against an original source, and an absent entry is a gap in coverage. Corrections can be sent to {contact}. | `{contact}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.method.validation` | prose | Each record was retrieved from its source on the stated retrieval date, and its excerpt was matched against the retrieved text. An automated validator checks every build. It requires unique identifiers, https source URLs, valid dates and complete fields, and that every entity and relationship cites existing evidence. It also blocks forward-looking wording in records classified as fact, and rejects any relationship whose classification its evidence does not support. | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.notice` | disclosure | {independent} TheMoroccoAI is an independent reference project. It is not affiliated with, endorsed by or operated by the Government of Morocco or any institution listed here. Records quote public sources and link to them; they are not official statements. | `{independent}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.records.one` | interface | {count} record | `{count}` | `render_registry_index` | /registry/ | new | entity list item metadata (one record) |
| `page.registry.records.other` | interface | {count} records | `{count}` | `render_registry_index` | /registry/ | new | entity list item metadata (other counts) |
| `page.registry.start.chain` | prose | The fullest chain in this version runs from {ai2030} to the announced {jazari_network}, its planned core institute {jazari_root} and the {jazari_x0} convention signed in Fès. It then goes on to the signatories, the stated technologies and the targeted sectors. Each page shows the source excerpt, the publication and retrieval dates, and the classification of every claim. | `{ai2030}`, `{jazari_network}`, `{jazari_root}`, `{jazari_x0}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.start.h2` | heading | Start here | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.start.matrix` | prose | The {matrix} shows which organisations are documented as connected to which projects and initiatives, and on what evidence. The {gaps} lists what the registry cannot yet establish. | `{gaps}`, `{matrix}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.start.matrix_link` | interface | institutional matrix | — | `render_registry_index` | /registry/ | new | page.registry.start.matrix |
| `page.registry.start.questions` | prose | {questions} lists which organisations have documented AI activity, which projects are operational or only announced, which models and datasets are public, and which relationships are verified. Each answer links to its evidence. | `{questions}` | `render_registry_index` | /registry/ | new | — |
| `page.registry.start.questions_link` | interface | Questions the registry answers | — | `render_registry_index` | /registry/ | new | page.registry.start.questions |
| `page.registry.stats.checked` | interface | Sources checked | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.stats.entities` | interface | Entities | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.stats.format` | interface | Format | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.stats.format_value` | interface | Static HTML · JSON | — | `render_registry_index` | /registry/ | new | stats panel (Format) |
| `page.registry.stats.label` | interface | Registry status | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.stats.records` | interface | Evidence records | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.stats.relationships` | interface | Relationships | — | `render_registry_index` | /registry/ | new | — |
| `page.registry.title` | metadata | Reference Registry — TheMoroccoAI | — | `render_registry_index` | /registry/ | new | — |
| `punct.list_comma` | interface | ,  | — | both renderers | /methodology/ | new | {types} list in page.methodology.documents.summary |
| `punct.list_semicolon` | interface | ;  | — | both renderers | /methodology/ | new | {sources} list in page.methodology.documents.sources |
| `shell.nav.acquisition` | interface | Acquisition | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.evidence` | interface | Evidence | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.gaps` | interface | Gaps | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.label` | interface | Primary | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.matrix` | interface | Matrix | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.methodology` | interface | Methodology | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.questions` | interface | Questions | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.nav.registry` | interface | Registry | — | `page()` / `footer()` | shell (every page) | reused | — |
| `shell.skip_link` | interface | Skip to content | — | `page()` / `footer()` | shell (every page) | reused | — |
| `vocab.entity_type.company.plural` | term → `entity_type:company` | Companies | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.company.singular` | term → `entity_type:company` | Company | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.dataset.plural` | term → `entity_type:dataset` | Datasets | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.dataset.singular` | term → `entity_type:dataset` | Dataset | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.event.plural` | term → `entity_type:event` | Events | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.event.singular` | term → `entity_type:event` | Event | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.initiative.plural` | term → `entity_type:initiative` | Initiatives | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.initiative.singular` | term → `entity_type:initiative` | Initiative | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.institution.plural` | term → `entity_type:institution` | Institutions | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.institution.singular` | term → `entity_type:institution` | Institution | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.legal_instrument.plural` | term → `entity_type:legal_instrument` | Legal instruments | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.legal_instrument.singular` | term → `entity_type:legal_instrument` | Legal instrument | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.model.plural` | term → `entity_type:model` | Models | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.model.singular` | term → `entity_type:model` | Model | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.project.plural` | term → `entity_type:project` | Projects | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.project.singular` | term → `entity_type:project` | Project | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.sector.plural` | term → `entity_type:sector` | Sectors | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.sector.singular` | term → `entity_type:sector` | Sector | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.entity_type.technology.plural` | term → `entity_type:technology` | Technologies | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /registry/ | new | — |
| `vocab.entity_type.technology.singular` | term → `entity_type:technology` | Technology | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.academic_journal` | term | Peer-reviewed journal | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.academic_preprint` | term | Academic preprint | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.government_portal` | term | Government portal | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.government_publication` | term | Government publication | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.independent_list` | term | Independent list | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.intergovernmental_organization` | term | Intergovernmental organisation | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.investor_publication` | term | Investor publication | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.organization_website` | term | Organisation's own website | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.regulator` | term | Regulator | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.secondary_press` | term | Secondary press | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.signatory_organization` | term | Signatory organisation | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.state_news_agency` | term | State news agency | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `vocab.source_type.technical_repository` | term | Technical repository | — | both renderers; `TYPE_LABELS`/`TYPE_SINGULAR`/`SOURCE_TYPE_LABELS` (all pages) | /methodology/ | new | — |
| `page.registry.coverage.gap` | qualifier | No record has been verified for this domain yet. It stays empty rather than holding unsourced entries. | — | `render_registry_index` | /registry/ (conditional) | new | domain cell when a domain has no entity |
| `page.registry.coverage.none` | interface | 0 entities | — | `render_registry_index` | /registry/ (conditional) | new | domain cell when a domain has no entity |

## Canonical content units (not in the catalog)

Their English text is read from canonical data at render time, so it cannot drift from the reference; a translation records the fingerprint of that canonical text.

| Unit pattern | Source | Count | Notes |
|---|---|---|---|
| `classification:<id>:definition` | `data/evidence.json` `classifications` | 5 | methodological definitions |
| `domain:<id>:label` | `data/ontology.json` `domains` | 7 | domain headings |
| `ontology:<id>:name` | `data/ontology.json` entity `name` | 65 | kind `name`; needs `name_basis` |
| `ontology:<id>:status` | `data/ontology.json` entity `status` | 25 | research prose with qualifiers, dates and evidence IDs (isolated in RTL) |

## Not translated

| Content | Reason |
|---|---|
| Evidence and entity IDs, page codes (`MAI-METHOD`, `MAI-REG`, `MAI-EV-NNNN`) | Identifiers; passed as isolated placeholders, never in catalog text |
| Classification codes in badges (`VERIFIED FACT`, …) | Canonical codes; matched across languages |
| File names and paths (`evidence.json`, `/data/manifest.json`, …) and code | Technical tokens |
| Contact address and the e-mail subject line | Technical token; messages reach an English-speaking owner |
| Brand (`TheMoroccoAI`, `TheMoroccoAI.com`) and commit references | Names and identifiers |
| Numbers, counts, dates and versions | Filled from canonical data; only month names are localized |
| Source excerpts | Not on these pages; never translated (TMA-DEC-007 Q6) |

## Conditional units

`page_requirements()` reports what a page renders **with the current data**. Two units render only when a domain has no entity: `page.registry.coverage.none` and `page.registry.coverage.gap` (a qualifier). If the data changes so that they appear and they are not translated, the localized page becomes ineligible and is withdrawn; it never shows English text. Translators should therefore translate them with the rest of `/registry/`. The extraction of every conditional branch (empty domain, single-record entity, entity without status, changelog entries by commit or pull request, with and without version or correction lists, and canonical text containing quotes, apostrophes, ampersands and angle brackets) was verified byte-identical against the previous renderer.

## Deferred

The `/methodology/` changelog renders **97** canonical texts from `data/changelog.json` as recorded: note 1, entry titles 13, changes 55, corrections 16, review_fixes 11, breaking_changes 1. They are canonical history, like evidence; translating them needs content units for list items, which requires a decision on their identity (position-based ids break when items are inserted; content-addressed ids turn an edit into a new unit). Until that decision, `/methodology/` cannot be complete in another language and is not registered for localization. `/registry/` has no deferred text.

Plural forms: counts use two English forms (`records.one`, `records.other`); Arabic has more plural categories. Translators must phrase these units neutrally until plural selection is added (see Arch section 15).
