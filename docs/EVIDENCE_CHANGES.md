# Evidence change intelligence (Sprint 29)

| | |
|---|---|
| Status | Implemented and published: `/registry/changes/`, `/registry/changes/changes.json`, and a *Record history* section on every entity page |
| Engine | `tools/changes.py` (standard library, deterministic) |
| Tests | `tests/test_changes.py`, plus the existing site, layout and consumer gates |
| Schema | `changes.json` `schema_version` 1.0 |

## 1. What it does

It compares consecutive **published versions** of the canonical files (`data/evidence.json`, `data/ontology.json`, `data/gaps.json`) and classifies every difference.

| Subject | Classes |
|---|---|
| Evidence record | `added`; `reclassified`; `verification_changed`; `superseded`; `source_changed`; `excerpts_changed`; `date_corrected`; `links_changed`; `field_recorded`; `text_revised` (undetermined); `text_editorial`; `rechecked` (retrieval date only, structural); `metadata_changed` |
| Entity | `added`; `lifecycle_changed`; `lifecycle_recorded`; `classification_changed`; `renamed`; `attributes_changed`; `evidence_changed`; `dates_changed`; `field_recorded`; `text_revised`; `text_editorial`; `metadata_changed` |
| Relationship (identified by `subject\|predicate\|object`, which is unique) | `added`; `removed`; `reclassified`; `evidence_changed`; `text_revised`; `text_editorial` |
| Evidence gap | `opened`; `state_changed`; `reassessed`; `removed`; `text_revised`; `register_started` |
| Data contract | `field_added`; `field_removed` |

Each class has a **materiality**:
- `research`: a documented finding changed;
- `editorial`: formatting only;
- `structural`: format, schema or bookkeeping;
- `undetermined`: a wording revision whose effect on the finding is not judged automatically, so the page shows its before and after text.

## 2. Guards against false inferences

- **A record, not an event.** A record admitted in a version documents something that may have happened much earlier.
  - The page and the JSON say so.
  - No event date is inferred: changes carry `source_published` (the source's date) and `retrieved` (the registry's retrieval date) only.
  - Each version carries `as_of`, the date its sources were last checked.
- **First recorded is not changed.** A property absent before is *first recorded*. When v0.2.0 introduced the lifecycle field, 9 entities received a stage; none moved between stages. Being superseded is the one exception: it is always a finding.
- **Reordering is not a change.** Reordered records, evidence lists and attributes produce nothing.
- **A new register is not a removal.** `gaps.json` first appears in v0.4.0, where the register begins.
- **Editorial changes are narrow.** A wording change is `editorial` only if it differs in whitespace, case or punctuation.
- **Source changes are not detected here.** Source disappearance or modification is detected by `tools/check_sources.py`, not by this engine; only a recorded correction appears as a change.

## 3. Architecture decision

**Chosen design.** Snapshots are the published versions on the first-parent history of the current branch: one per registry version (the last commit carrying it), plus the working tree when it holds a newer version.
- Each snapshot is identified by **version, `as_of` and the SHA-256 of its canonical content**. Commit hashes are not used, so the output does not change when a pull request is squash-merged.
- `tools/build.py` computes the change log during the build.
- The change log is published as a derived file listed in the manifest, and rendered as a page and as entity record histories.

| Alternative | Why rejected |
|---|---|
| A database or service | Unnecessary: 12 snapshots, 287 changes, 0.2 s to compute |
| A crawler or scheduled collection | Out of scope; source permissions, reliability and maintenance not established |
| Committed copies of every snapshot | Duplicates canonical data and its hashes |
| A hand-written change list | Unverifiable; the narrative changelog already exists for prose |
| Commit hashes as snapshot identity | Squash merges rewrite them, which would make `main`'s output stale |

**Requirements:**
- The build needs the repository's full history. CI fetches it (`fetch-depth: 0`); a shallow clone fails loudly rather than publish a partial history.
- One registry version per pull request: the existing practice that every data change bumps the version keeps snapshots well defined.

## 4. Publication gate

The page is published because the data supports it:
- 12 published versions and 11 transitions;
- 287 classified changes, 221 of them to documented findings;
- substantive transitions: 3 lifecycle changes, 4 relationships reclassified from ANNOUNCED PLAN to VERIFIED FACT, 1 record superseded, 1 relationship withdrawn, 7 gap reassessments.

Versions that did not change the record (v0.4.1, v0.10.0, v0.10.1) are shown as such, not padded.

## 5. Questions it answers that the static pages do not

All answers below come from the published change log. Each entity page shows only its **current** state.

1. **When did the registry first record Idarati AI as operational, and on what evidence?**
   - v0.2.0: first recorded as *announced* on MAI-EV-0013.
   - v0.3.0 (sources checked 18 October 2026): changed to *operational* on MAI-EV-0034, MAI-EV-0035 and MAI-EV-0038.
   - The same version reclassified its `applies` and `targets` relationships from ANNOUNCED PLAN to VERIFIED FACT, adding MAI-EV-0034 to MAI-EV-0013.
2. **Which documented relationships were upgraded from an announced plan to a verified fact, and on what evidence?**
   - Idarati AI `applies` agentic AI assistants, and `targets` public administration (v0.3.0, MAI-EV-0013, MAI-EV-0034).
   - The ministry, and Nexus Core Systems, as `signatory_of` the Nexus AI Factory (v0.6.0, MAI-EV-0030, MAI-EV-0044).
3. **Which evidence gaps were reassessed, and which records moved them?**
   - GAP-03 (v0.6.0, MAI-EV-0042, MAI-EV-0043).
   - GAP-04 (v0.6.0, MAI-EV-0044, MAI-EV-0045).
   - GAP-02 (v0.8.0, MAI-EV-0058).
   - GAP-06, reassessed four times (v0.6.0 to v0.9.0, MAI-EV-0046 to MAI-EV-0063).
4. **Which records were corrected or withdrawn?**
   - MAI-EV-0029 was superseded by MAI-EV-0032 and MAI-EV-0039 (v0.3.0).
   - A relationship between the Ministry of Higher Education and JAZARI Institute Nador was withdrawn from the record (v0.2.0).
   - DeepEcho AI ultrasound software moved from *in development* to *unresolved* (v0.3.0).

## 6. Temporal knowledge: assessment and minimal design

What the canonical data supports today:

| Question | Data | Supported? |
|---|---|---|
| Relationships valid during a period | 0 of 78 relationships carry a date | No |
| Historical states of initiatives | Lifecycle stages per published version, from v0.2.0 | Yes, as *recorded* states with their versions, through this change log |
| Changes in organisational participation | Relationship added, removed or reclassified per version | Yes, as recorded changes |
| Announcement-to-implementation transitions | Lifecycle changes and relationship reclassifications with evidence | Yes, as recorded (for example Idarati AI, v0.3.0) |
| Source-supported dates of developments | 53 of 63 records carry a publication date (7 to the month); 1 entity (an event) carries start and end dates | Partly: dates of sources, not of developments |

**Minimal, backward-compatible design. Proposed, not implemented; no migration.**
- Optional `valid_from` and `valid_until` on a relationship.
  - Each value is a date with its precision (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`).
  - Each value is set **only** where a cited record states it (`valid_from_evidence`).
  - Absent means unknown, never "always".
- The validator would require the cited record to contain the date in an excerpt.
- **Recorded time** (when the registry knew something) is already derived from this change log and must stay separate from **valid time** (when it was true in the world).
- **Gate:** implement only when at least one source-stated relationship date exists to record. Backfilling is not allowed.

## 7. Search and internal linking (Issue #28)

| Page | User question | Why existing pages do not answer it | Linking | Indexation | Maintenance |
|---|---|---|---|---|---|
| `/registry/changes/` | "What changed in the documented record of Moroccan AI initiatives, and when was a status first recorded?" | Entity pages show the current state; the changelog is narrative, by sprint, not by record | From the methodology changelog and every entity's record history; links to every changed record, entity and gap | Indexable; canonical self; in the sitemap; Open Graph and X metadata; JSON-LD `Dataset` with a `DataDownload` for `changes.json` | None by hand: regenerated by the build from history when a version is published |
| Record history (65 entity pages) | "Has this initiative's status changed, and on what evidence?" | Not answered before | Links to the changes page and to each record | Part of each entity page; no new URL | None by hand |

Deliberately not created:
- one page per change, per version or per class (no unique utility beyond the anchors);
- landing pages for keywords;
- any claim about rankings or traffic.

Remaining Issue #28 work (competitive benchmark, search-intent matrix, Search Console measurement) is not part of this sprint.

## 8. Multilingual

`changes.json` is language-neutral: class codes, identifiers, dates and canonical values. The page and record histories are English, like the other pages not yet extracted to the catalog.
- **Future localization:** move their labels and sentence templates to `i18n/en/messages.json`. Canonical values stay as they are and are never duplicated.
- **Hashes:** the reference hashes are untouched (the change log is derived, not canonical).
- **No new translation is published.**
