# Sprint 05 — Reference Reuse & External Verifiability

Baseline: `main` at `a0dedadc1188d15807cabd30dd7490b67dbb0052` (Sprint 04, production verified).
Registry after this sprint: v0.4.1, 19 October 2026. No record, entity or relationship was added or changed.

## 1. Read-only audit (before any change)

Published JSON on production: `/data/evidence.json`, `/data/ontology.json`, `/data/gaps.json`,
`/data/changelog.json` (canonical), `/registry/matrix/matrix.json`, `/registry/gaps/gaps.json` (derived). All
returned 200 as `application/json`, with `access-control-allow-origin: *` and `cache-control: max-age=600`.
`/data/` returned 404.

| Question | Finding |
| --- | --- |
| Which files suffice for independent consumption? | evidence.json and ontology.json are self-describing: they define every classification, verification status, entity type, stage, project kind, origin, domain and predicate they use. data/gaps.json holds the gap assessments, checks and digests. The derived files repeat canonical data with computed fields. |
| Can relationships and evidence be resolved without build code? | Identifiers resolve by plain lookup. Derived fields could not be recomputed without the build code: the matrix's `documented_as` and `documentation_basis`, the GAP-05 list, the gap checks and the gap digest. Their rules (subject and object types, formal-act predicates, announcement evidence types, digest fields) existed only in `tools/registry.py` and `tools/build.py`. |
| Missing documentation for a third party | No page for data users: nothing said which files are canonical or derived, how relationships are identified (they have no id field), what `null` and absent fields mean, that dates may be `YYYY-MM`, how versions work, or that third-party excerpts carry no reuse right. |
| Ambiguous or unstable fields | **Defect:** `ontology.json` said version 0.3.0, as of 18 October 2026, while the registry was v0.4.0 and the ontology's content had changed in v0.4.0 (Toubkal attributes). Two different files are both named `gaps.json`. Gap `state` values were not defined in data. `qualifications` and `object.stage` are display text. With a 10-minute cache, a consumer can receive files from two builds. |
| Can Q8 and Q9 be reproduced? | Mostly, once the rules are published. Parts rest on editorial judgments that the data records but cannot derive (section 4). |

Other findings:
- The registry index said "It does not yet cover AI companies, models or datasets". That has been false since v0.2.0.
- At 320 px, the homepage navigation's last link ended 10 px past the screen edge, even with the web fonts loaded.

### Bounded plan

1. Fix the evidence-card clipping with CSS, and add a regression test that renders with the fonts blocked.
2. Make ontology.json carry the registry version and date, enforced by the validator; define the gap states.
3. Publish the derivation rules inside the derived files, generated from the validator's constants so they cannot drift.
4. Publish a manifest with SHA-256 hashes and a data reference page at `/data/`.
5. Add a standard-library consumer in `examples/` that reads only manifest-listed files.
6. Add tests: adversarial copies, determinism, and Q8/Q9 compared with the published page and the generator.

There is no new schema, no copy of the canonical data, no server, no analytics and no licence.

## 2. Mobile defect

Cause: `.evidence-list` is a grid, and a grid item's minimum width defaults to its longest unbreakable
string. MAI-EV-0034 quotes `"url":"https://chatbot.idarati.ma","badge":"Service phare"`. In the wider fallback
fonts that string exceeds a phone screen, so every card in the list widens (370.6 px in a 343 px column at
375 px). This happens while the web fonts load, and permanently when they are blocked. It affected the
evidence index and every entity page that shows that card.

Fix: `.evidence-card { min-width: 0; overflow-wrap: anywhere; }`, so the string wraps inside the card and
nothing is hidden. For the homepage at 320 px or narrower: navigation padding 16 px and tighter link
letter-spacing.

`tests/test_layout.py` renders 9 pages at 320 and 375 px in headless Chromium from a copy of the site with no
font files. Each page sits in an iframe of the exact width, because headless windows cannot be narrower than
500 px. The test asserts:
- the viewport width was applied;
- no font loaded;
- no element outside a scroll region passes the right edge.

A control test confirms that the probe detects overflow. Without the fix, the test fails on 9 page and width
combinations.

Browser check (local build, fonts loaded): 9 pages at 1366, 375 and 320 px, with 0 overflowing elements, 0
WCAG 2 A/AA violations (axe-core) and no third-party requests. At 1366 and 1024 px, card, navigation, heading
and section geometry is identical to the production baseline.

## 3. Production changes

| Change | Where |
| --- | --- |
| Data reference: files, identifiers, provenance, null and absent values, versions and updates, coverage, what can be recomputed, how to check, corrections | `/data/` (generated) |
| Manifest: each published JSON file, its role, purpose, size and SHA-256 in this build; rights status; consumer location | `/data/manifest.json` (generated) |
| `derived_from` and `derivation` (row selection, `documented_as` table, formal-act predicates, announcement evidence types, field meanings) | `/registry/matrix/matrix.json` |
| `derived_from`, `states` and `derivation` (check semantics, digest algorithm and fields) | `/registry/gaps/gaps.json` |
| `states` defined | `/data/gaps.json` |
| Version 0.4.1 and as-of date 2026-10-19, matching evidence.json; validator rule | `/data/ontology.json`, `tools/registry.py` |
| Example consumer | `/examples/registry_consumer.py` |
| Footer "Data" link points to `/data/`; registry index and methodology link to it; stale coverage sentence corrected | all pages |
| Changelog v0.4.1 (pull request #6) | `/data/changelog.json`, `/methodology/` |

`documented_as()` in the generator now reads the same tables that matrix.json publishes.

## 4. External consumer and reproducibility

`examples/registry_consumer.py`:
- Uses the Python 3.10+ standard library only. A test parses its imports and rejects anything outside the standard library, as well as `registry` and `build`.
- Starts from the manifest and fetches only the files it lists, checking each hash.
- Every command first verifies the data:
  - versions agree;
  - every defined value is defined in its file;
  - every reference resolves, and predicate types are respected;
  - the matrix is recomputed and compared row by row, including evidence dates and URLs;
  - the GAP-05 list is recomputed;
  - each gap's data checks are re-run and its digest recomputed;
  - no record postdates a gap's assessment.
- Exit codes: 1 for inconsistent data (every problem printed); 2 for a fetch, usage or lookup error. A missing field fails cleanly, without a traceback.

Demonstrations, run against the local build and over HTTP:
- `verify`: `OK: registry 0.4.1 as of 2026-10-19: 41 records, 65 entities, 78 relationships, 43 matrix rows and 5 gaps checked …`
- `relationship ministry-digital-transition operates idarati-ai`:
  - **DOCUMENTED:** classification and definition; matrix wording and basis; Idarati AI's stage, shown as `operational (public-availability-observed)`; each of MAI-EV-0034, 0035 and 0038 with source, URL, dates (undated sources are labelled as such), verification, claim and excerpts.
  - **LIMITATIONS:** the relationship note; each record's verification note; a reminder that a stage is not evidence of use, scale, outcomes or later operation.
- `gap GAP-03`: what is established, with records; what is not; the evidence needed. Digest `82be8209a0580f53` recomputed and unchanged; check "no AI application linked to toubkal-supercomputer: holds". The established and not-established text is labelled as the editor's assessment.
- `gap GAP-05`: 19 of 33 formal-act relationships recomputed.
- Against production before merge: `ERROR cannot fetch https://themoroccoai.com/data/manifest.json: HTTP Error 404`, exit 2.

Reproducibility, tested against both `registry/questions/index.html` and the generator:

| Answer part | Status |
| --- | --- |
| Q8: organisations, their projects and relationships, `documented_as`, evidence, summary counts (15 organisations, 12 projects, 24 relationships: signed 16, announced or planned 4, operated 2, developed 1, documented 1; 15 announcement-only) | Reproduced exactly |
| Q8: each relationship's classification and cited records; each project's stage | Recorded, not derivable (editorial) |
| Q8: caveat sentences | Fixed wording |
| Q9: targets, their strategies, included projects and stages, covering gap and its state | Reproduced exactly |
| Q9: "no recorded evidence measures progress" for Morocco AI 2030 (GAP-02 open) | **Editorial assessment.** GAP-02 has no data check. Its digest shows only that the data it rests on is unchanged since assessment. |
| Q9: Digital Morocco 2030 "not yet assessed" | Reproduced (no gap covers it) |

The consumer's recomputed matrix, GAP-05 list and all gap digests equal the generator's.

## 5. Tests and mutation testing

- Gates: validator 0 problems; 78 generated files, 0 stale; `check_site --network` 74 pages, 0 problems.
- Tests: **240** (188 before), none skipped locally:
  - `test_consumer.py`: 50;
  - `test_layout.py`: 2.

  In CI, one test (identifier history) skipped because the checkout was shallow; see section 8.
- Determinism: rebuilt under `C` / Asia/Tokyo / `PYTHONHASHSEED=11` and `C.UTF-8` / America/Los_Angeles / `PYTHONHASHSEED=999`, with 0 files differing. Consumer output is identical across three hash seeds for every command.

Adversarial copies: one defect per copy of the published files, each rejected with exit 1 and a specific message.
- **Broken references:** evidence; entity; record naming a missing entity; relationship naming a missing entity.
- **Wrong resolution:** wrong predicate types; matrix row resolving to the wrong entity; upgraded `documented_as`; missing row; evidence dates differing.
- **Unknown values:** stage, classification, gap state, gap check type.
- **Stale or mismatched files:** a file from another build (SHA-256); mismatched versions; stale derived file; derived file without its rules.
- **Gap integrity:**
  - a gap resting on changed data (digest);
  - a new record postdating an assessment;
  - each gap-check type triggered: stage moved, report of use, AI-application link, empty computed list;
  - an outdated GAP-05 list;
  - derived gap text differing.

Targeted mutations: **39 of 40 caught.** Coverage spans CSS (3), validator (2), consumer checks, recomputation and output (27), generator rules, manifest and wording (7), and data (1). The survivor (M27, dropping the Q9 lifecycle filter) is equivalent: the validator requires every project to have a lifecycle, so the filter cannot change the output.

Three mutations survived a first run: a relationship naming a missing entity, records postdating a gap, and the manifest hashing stale files. Each gained a test and is now caught.

## 6. Remaining limitations

- The consumer verifies internal consistency and recomputes derived data. It does not re-fetch sources; that remains `tools/check_sources.py`, maintainer side.
- Judgments are recorded, not derivable: classifications, stages, and gap text and state. GAP-02 has no data check at all.
- Hashes prove that files belong to one build, not who published them; there is no signature.
- `test_layout.py` needs a Chromium or Chrome binary. GitHub's Ubuntu runners include Chrome, but the test skips where none is found.
- External reuse is not measured, and nothing here claims adoption.
- Earlier limitations stand:
  - all gaps are open;
  - the GemMaroc study has not been retrieved;
  - MAI-EV-0041 is blocked to automated checks.

## 7. Owner decisions requested

1. **Licence and reuse.** None is declared. The pages say third-party excerpts remain subject to their publishers' rights. Any licence for the registry's own structure and text, separate from cited sources, is your decision.
2. **Identifier policy.** The page states a fact: since v0.1.0 no evidence or entity id has been removed, renamed or reused. Should that become a formal commitment, such as ids are never reused and removals are tombstoned?
3. **Versioning policy.** The page says each change to evidence.json, ontology.json or gaps.json gets a new version and a changelog entry. Is a patch/minor scheme (0.4.1 here for a documentation and metadata release) acceptable?
4. **Measuring reuse.** Nothing is measured, and analytics were not added. Any measurement (for example, asking reusers to cite the version and as-of date, or a voluntary contact) needs your approval.

## 8. Owner pre-merge review

### Owner decisions, applied

| Decision | Applied as |
| --- | --- |
| No licence now | Unchanged: none declared. Pages state that source excerpts remain subject to their publishers' rights. |
| Identifiers | `/data/` and README: published identifiers are never reused; a record, entity or relationship may be corrected or withdrawn, with the change in the changelog; a withdrawn identifier stays retired. |
| Versioning | A new version when published reference data or its meaning changes (records, entities, relationships, gap assessments, definitions); an editorial change that affects neither may be published without one. |
| Usage measurement | None added. |

### 1. Manifest integrity

- **Real mixed versions.** The v0.4.0 `evidence.json` from `main`, served next to the current manifest, is rejected twice: on its SHA-256 and on its version. The v0.4.0 `ontology.json` is rejected on its version (0.3.0) even when the manifest is re-signed around it.
- **Stated limit.** A test shows that a consistent edit with a re-signed manifest passes: whoever can rewrite the files can rewrite the manifest. `/data/`, the manifest's `note` and the consumer's `verify` output now say that the hashes are not a signature, and that they do not show who published the files or that their content is accurate.

### 2. Reproducibility without hidden rules

Two clean-room passes were run by an agent that could read only a copy of the published JSON and the `/data/` page as text. It could not see the site's code, tests or consumer, and it wrote its own standard-library code.

- **Pass 1** (published files at `35c0885`'s parent): every hash, all 43 matrix rows, GAP-05 (19 of 33), all gap digests and checks, and Q8/Q9 reproduced. But it had to guess at 13 points:
  - the Q8 scope;
  - row and evidence order;
  - the GAP-05 scope and N of M;
  - the digest's structure;
  - the meaning of "postdates" and of a check "holding";
  - check direction and missing lifecycles;
  - undefined values of `status_basis`, `evidence_type` and `source_type`;
  - unpublished caveat rules;
  - the Q9 join;
  - build membership of files without a version.
- **Fixes**, each now published in `matrix.json` / `gaps.json` `derivation`, the manifest or `/data/`:
  - the accepted values for `source_type`, `evidence_type` and `status_basis` (which the consumer checks);
  - the qualification rules;
  - the ordering rules;
  - the exact digest structure;
  - the check semantics;
  - the Q8 and Q9 scope and joins.

  The review also showed that the operational stage definition ("by a source independent of announcements") could be read as requiring an independent source. It now says what the rules allow and that availability is not use. The announced definition no longer states an absence of evidence.
- **Pass 2** (revised files): every comparison passed, including row order, qualifications and digests. It still found three things:
  - `object.stage` had no rule, and the documentation said every operational stage states its basis, which is untrue for Toubkal's independent listing;
  - M in "19 of 33" was not published;
  - `/data/` said every stage rests on a declaring record, which is untrue for announced and unresolved stages.

  All three are fixed:
  - the stage-label rule is published and the consumer recomputes every label;
  - GAP-05 publishes `formal_act_relationships` (33);
  - the validator's classification-support rules are published in the manifest and checked by the consumer.

  The Q8 and Q9 ordering, grouping and evidence lists are specified.

Still not reproducible from the files, and labelled as such:
- the editorial judgments (classifications, stages, gap text and state; GAP-02 has no data check);
- the validator's rules beyond classification support (operator naming, source independence), which are described in prose only.

### 3. Identifier stability

All four published data states on `main` were audited (`6bc8d9a`, `d35d0df`, `391006a`, `a0dedad`):
- No evidence or entity identifier was ever removed.
- None changed its source URL, title, publisher, publication date or classification (records), or its type or name (entities).
- The only removal is one relationship, replaced as a correction in v0.2.0 and listed in the changelog.

The claim is therefore supported. The test behind it was weak, and is now fixed:
- It checked only v0.1.0's identifiers, and it **skipped in CI** because the checkout was shallow.
- It now checks every first-parent version of the data against the current files: no removal, same source address, same entity type, with a `WITHDRAWN` list for documented withdrawals.
- CI fetches full history, and the test fails in CI instead of skipping when history is missing. A further test checks the workflow setting.
- Verified behaviour: removing a published entity fails by name; a shallow local clone skips; a shallow CI clone fails.

`/data/` notes that earlier versions are not published as files, so the check is repeated from the public repository's history.

### Mutation testing of the review changes

- Review round: 9 mutations. 7 caught directly. The test-only mutation was replaced by a real removal, which is caught. The shallow-CI mutation is now caught by the workflow test.
- Clean-room round: 6 mutations, all caught. The mixed-basis stage-label mutation was caught after a dedicated test was added.

### Observations for the owner (not changed)

- **Q8 wording.** The question says "AI or computing projects", but Q8 counts every project: AI institutes, signed agreements, and the AI Marketplace, which the data classes as a digital platform rather than an AI deployment. Options: reword the question, or narrow the count.
- **"Signed" on a news dispatch alone.** Nine matrix rows read "Signed" while resting only on a news dispatch; their caveat and `documentation_basis` say so. A reader of `documented_as` alone could miss it.
- **GAP-05 includes announced plans.** It includes relationships already classified as announced plans, so part of its count is a second statement of the same limit.
- **Digital Morocco 2030.** It has an official target but no gap, so Q9 reports it as not assessed.

### Final figures

- Tests: **252**, all passing locally and in CI.
- Gates: validator 0 problems; 78 generated files, 0 stale; `check_site --network` 74 pages, 0 problems.
