# Sprint 08 — Institutional Reality & Measurable Outcomes

**Baseline:** `main` at 48eac8a880e045459efff9e4cab29783cbbd23b7 (registry v0.6.0; Sprint 07 closed and verified in production).
**This PR:** Tier 1 only, as approved. Registry v0.7.0.
**Not in this PR:** Tier 2 (strategy measurement records) and Tier 3 (new entities or a new predicate). Both await separate approval.

## 1. Research findings (read-only phase)

Two research agents searched the sources. Every source below was then re-read independently; gazette, brochure and finance-law pages were read from rendered page images.

### 1.1 The "113th" baseline

- **What the strategy's own brochure says.** The official Digital Morocco 2030 brochure is published by the ministry, linked from its news page of 25 September 2024 (MAI-EV-0049). Its objectives page sets « Passer de la 113ᵉ place mondiale à la 50ᵉ place sur le classement EGDI* des services publics en ligne ». The footnote reads « EGDI = « Online Services Index », composant de l'indice « E-Government Development Index » des Nations Unies ». Its page on public services gives 113th worldwide for 2022, 85th for 2026 and 50th for 2030.
- **What v0.6.0 got wrong.** v0.6.0 followed the news-agency dispatch (MAI-EV-0002) in calling the objective the overall EGDI, then compared 113 with Morocco's overall EGDI ranks. That comparison was with the wrong measure.
- **What the UN page gives.** It gives Morocco's Online Service Index values (0.47210 in 2022, 0.56184 in 2024) but no rank on that index. The full UN dataset sits behind a form, which was not submitted.
- **Conclusion.** The 113th OSI place is the strategy's figure and remains unverified.

### 1.2 JAZARI institutions

| Stage | ROOT | EduTech | Industrie X.0 | Smart City | Nador |
|---|---|---|---|---|---|
| Founding agreement | signed 12 Jan 2026 | thematic agreements co-signed 12 Jan 2026, not individually named | signed 10 Mar 2026 | as EduTech | memorandum, 2 Jul 2025 |
| Legal approval | BO 7534, order 1535.26 | BO 7534, order 1618.26 | BO 7534, order 1619.26 | BO 7534, order 1620.26 | none located |
| Governance event | general assembly, 8 Sept 2026 | same | same | same | regional council approved a founding project, 6 Jul 2026 (press) |
| Staff, premises, activity, outputs | not found | not found | not found | not found | not found |

Other findings:
- **A sixth institute.** A protocol signed on 14 Apr 2025 for a JAZARI Institute in Guelmim-Oued Noun is not in the registry. The PLF 2026 note plans its construction for 2026.
- **Unsupported operation claims.** LesEco says Industrie X.0 has been "opérationnel … depuis mars 2026", and Tech Review Africa says "inaugurated". Neither gives a source, and both contradict the official chronology.

### 1.3 Strategy measurement

These findings are recorded here only; no Tier 2 records were added.

- **Conflicting targets.** The finance-law performance projects of the digital ministry set different targets from the strategy:
  - EGDI 75th by 2026 (PLF 2023), then 85th by 2026 (PLF 2024);
  - jobs created: 190,000 by 2030 (PLF 2023), then 270,000 (PLF 2024);
  - the PLF 2024 project gives the 2022 EGDI baseline as 101.
- **Reported outputs, under definitions that differ from the targets:**
  - 148,500 offshoring jobs at end-2024;
  - 22,649 new digital enrolments in 2024–25.
- **Allocation, not spending.** The 2026 finance law allocates MAD 1.5 bn ("Mise en œuvre de la stratégie Maroc Digital"). No actual expenditure was found.
- **Audit finding.** The Cour des comptes reports 605 services digitalised at end-2023, of which no more than 23% were fully digitalised.
- **Morocco AI 2030.** The targets are 200,000 talents trained and certified by 2030, and separately 100,000 new digital talents a year. No official progress count was found.

## 2. Evidence and relationship diff (this PR)

| Change | Detail |
|---|---|
| **MAI-EV-0048 (new)** | Ministry release, 8 Sept 2026: the general assemblies of JAZARI ROOT, EduTech, Industrie X.0 and Smart City were held in Rabat. VERIFIED FACT, official announcement. Four excerpts, all matched against the live page. |
| **MAI-EV-0049 (new)** | Official Digital Morocco 2030 brochure: the ranking objective defined as the Online Services Index. OFFICIAL TARGET, `target_year` 2030. The PDF is image-only, so the excerpts were transcribed from page images. |
| **MAI-EV-0002 (C3)** | Claim now says "what the dispatch calls the e-government development index". The note separates the strategy's OSI figure, the UN OSI values and the overall EGDI ranks. |
| **MAI-EV-0046 (C3)** | Title, claim and a new excerpt (the OSI value row) record the UN's OSI values without a rank. The note no longer says that no edition shows 113th. |
| **MAI-EV-0008 (C1)** | The stale statement that the gazette text "was not located" now points to MAI-EV-0047. |
| **MAI-EV-0047 (C2)** | The Nador statement is limited to BO 7534 and does not imply that no other act exists. |
| **Entities** | ROOT, EduTech, Industrie X.0 and Smart City cite MAI-EV-0048, and their status records the general assembly. Stage stays `announced`; `lifecycle_evidence` is unchanged. The digital-morocco-2030 summary names the Online Services Index and states that the 113th place is not verified. The ministry entity cites the two new records. |
| **Relationships** | None added or changed (see R1). |
| **Gaps** | GAP-06 re-assessed (fingerprint `ddbac4d9fb7806a1`), still open. GAP-07 added (fingerprint `d088b8596a699577`), open. |
| **Version** | v0.7.0, as of 2026-10-20: 49 records, 65 entities, 78 relationships, 7 gaps. |

## 3. OSI/EGDI correction audit

Every place that spoke of the 113th baseline was found and reviewed:

| Location | Before | After |
|---|---|---|
| MAI-EV-0002 claim | "…113th to 50th place … in the e-government development index" | "… in what the dispatch calls the e-government development index" |
| MAI-EV-0002 note | "no edition of the United Nations index ranks Morocco 113th" | The strategy defines the ranking as OSI; 113th is its 2022 figure, not verified. Overall EGDI: 101st (2022), 90th (2024). |
| MAI-EV-0046 note and claim | "No edition shows Morocco at 113th…" | OSI values without a rank; neither confirms nor contradicts the 113th OSI place |
| GAP-06, objectives statement | "…in the e-government development index" | Strategy's OSI definition and the dispatch's wording; cites MAI-EV-0002 and 0049 |
| GAP-06, UN statement | "no edition shows the 113th place…" | Overall EGDI ranks; OSI values without a rank; 113th not verified; cites 0046, 0049 and 0002 |
| GAP-06, not established and evidence needed | — | Adds the OSI rank in any edition and the UN OSI ranking |
| digital-morocco-2030 summary | "…in the e-government development index" | "…on the United Nations ranking of online public services, which the strategy's brochure defines as the Online Services Index…; the 113th place is the strategy's figure, not verified by the registry" |
| v0.6.0 changelog correction | "no United Nations edition ranks Morocco 113th…" | Kept as published, annotated "(Corrected in v0.7.0 …)" |
| v0.7.0 changelog | — | A correction entry describing the change |

Tests forbid any current text that compares 113th with an overall EGDI edition, or that presents 113th as verified. The SPRINT_07 assessment document is a historical record and is unchanged.

## 4. GAP-07: scope and closure rules

- **Question:** which JAZARI institutes have documented governance, staff, premises, operational activity or outputs, beyond their founding agreements and legal approval?
- **Scope:** ROOT, EduTech, Industrie X.0, Smart City and Nador. There is no Guelmim entity in this PR.
- **Per-institute assessment.** `entity_assessments` is a new, additive field, defined once in `data/gaps.json` under `entity_assessment` and published in `registry/gaps/gaps.json`.
  - **Dimensions:** legal approval, governance event, staffing, premises, operational activity, outputs, documented non-commencement, documented discontinuation.
  - **Qualifying records:** only a VERIFIED FACT about the institute can document a dimension. Announced plans, targets and descriptions of intent qualify for none.
  - **Operating path:** operational activity and outputs each have a record, staffing or premises has a record, and the stage is pilot or operational under the existing status rules.
  - **Not-commenced path:** documented non-commencement has a record (a dated record that the institute has not begun operating, or will not); no activity or outputs are recorded; and the stage is not pilot, operational or discontinued. No stage change is required.
  - **Discontinued path:** documented discontinuation and operational activity each have a record, and the stage is `discontinued`. An institute that stopped before any activity meets the not-commenced path instead.
  - **Unknown:** an institute that meets no path has an unknown operational status and stays open. Missing records never resolve an institute.
  - **Conflicts:** records of both non-commencement and activity or outputs for the same institute are an error that forces re-assessment.
  - **Never sufficient:** a legal approval or a governance event never resolves an institute.
  - **Partial resolution:** a resolved institute stays listed, marked resolved, while the others remain open. The gap resolves only when every institute has.
  - **Enforced, not just documented.** The validator and the example consumer both enforce the paths:
    - an institute that meets a path but is still open is an error;
    - so is a resolved institute that meets no path;
    - so is a resolved gap with an open institute.
- **Current state:**
  - The four approved institutes have legal approval (MAI-EV-0047) and a governance event (MAI-EV-0048). Every other dimension is "not documented".
  - Nador has nothing documented. Its note records the 2 Jul 2025 memorandum and that BO 7534 contains no act on it, "which does not show that none exists".
  - A `lifecycle_in` check makes any stage change force re-assessment.
- **No overlap with other gaps:**
  - GAP-04 covers computing and data-centre infrastructure;
  - GAP-05 covers how formal acts are documented;
  - GAP-02 covers national target progress.

## 5. R1: semantic decision (deferred)

The BO 7534 summary for ROOT reads « من جهة الدولة ممثلة في الموقعين أسفله »: the State is the party, represented by the undersigned officeholders. Those officeholders include ministers, the Director-General of National Security and the president of the CNDP, who sits on the State's side.

`signatory_of` has no published definition. The matrix renders it as "Signed" by the subject entity, and Q8 counts it as an organisation's connection. Recording `ministry-digital-transition`, `ministry-economy-finance`, `ministry-higher-education`, `ministry-energy-transition` or `cndp` as `signatory_of jazari-root` would present each as a contracting party in its own right. That contradicts the gazette's distinction, most clearly for the CNDP.

**R1 is therefore deferred.** No relationship was added, and no predicate was introduced or redefined. The same ambiguity applies to the existing Industrie X.0 and Nador ministry signatures, recorded before this audit. Resolving it needs an owner decision on publishing a definition of `signatory_of`, or on a separate predicate, in a later sprint.

## 6. Verification

| Check | Result |
|---|---|
| `tools/registry.py` | 0 problems |
| `tools/build.py --check` | 78 files, 0 stale |
| Deterministic rebuild after commit | 0 changed files (two runs) |
| `python3 -m unittest discover -s tests` | **310 OK**: 290 existing plus 20 in `tests/test_operational_evidence.py`. Three existing tests now take the registry date and the gap count from the data instead of constants. |
| Example consumer, v0.7.0 | `verify` OK: 49 records, 65 entities, 78 relationships, 43 matrix rows, 7 gaps |
| Previous consumer (from 48eac8a) on v0.7.0 data | `verify` OK; also a test |
| Consumer mutation | A copy resolving ROOT on legal approval and a governance event alone exits 1 with the rule's message |
| Targeted mutations | **14 of 14 caught**: the C1, C2 and C3 reversions; 113th presented as verified; the OSI excerpt dropped; the general assembly promoting a stage; Nador dropped from scope (2 variants); ROOT resolved on approval plus assembly; the validator's resolution path or record rule disabled; the consumer check removed; a CNDP signature slipped in |
| `check_site.py` | 74 pages, 0 problems |
| Source check | MAI-EV-0002, 0008, 0046 (including the new OSI excerpt) and 0048 all match. MAI-EV-0049 is image-only and MAI-EV-0047 has a reversed Arabic text layer; both are recorded in their notes. |
| Accessibility and layout | 21 pages at 320, 375 and 1366 px, plus 320 and 375 with fonts blocked: no page-level horizontal overflow. axe-core WCAG 2.x A/AA: 0 violations once the page has settled. The known homepage fade-in transient appears only on a first load; 0 of 9 settled runs flag it. The GAP-07 table scrolls inside its frame on phones. |

## 7. Remaining limitations

- **113th OSI place:** unverified; the UN OSI ranking was not obtained.
- **Nador:** whether a legal act exists remains unknown. sgg.gov.ma was unreachable during research, though it answered during this PR's source check.
- **Strategy measurements (Tier 2):** not recorded, so GAP-02 and GAP-06 still show no measured progress.
- **Guelmim institute and founding members (Tier 3):** not recorded. That covers the EduTech and Smart City founding members and the Oriental Regional Council.
- **`signatory_of` semantics:** unresolved. It affects the existing ministry signatures as well as the deferred ROOT relationships.
- **MAI-EV-0049 excerpts:** transcribed from images, so automated matching is not possible.

## 8. Review correction: non-commencement is not discontinuation

The first version of GAP-07 resolved an institute that does not operate only with the stage `discontinued`. That conflated an institute that never began operating with one that stopped after operating.

**Why the lifecycle vocabulary cannot carry this.** The project lifecycle stages are announced, in-development, pilot, operational, discontinued and unresolved.
- `discontinued` is defined as "Documented as stopped or withdrawn".
- `announced` and `in-development` describe plans, not a documented decision or statement that operation has not begun.
- No stage means "never began operating".
- Adding one would change the ontology for every project, which is outside this PR.

**The bounded correction stays inside GAP-07, its validation and its published rules:**
- The single non-operation dimension is split into **documented non-commencement** and **documented discontinuation**.
- The resolution paths are **operating**, **not_commenced** and **discontinued**:
  - *not_commenced* needs a non-commencement record, no recorded activity or outputs, and a stage other than pilot, operational or discontinued, so no stage change is forced;
  - *discontinued* needs a discontinuation record, recorded activity and the `discontinued` stage.
- An institute meeting no path has an **unknown** operational status and stays open; missing records never resolve.
- Non-commencement recorded alongside activity or outputs is a conflict error.
- A resolution records the status at the date of its records; a later record about the institute already forces re-assessment (assessed_records and fingerprint).

**Proposed for a later sprint (not implemented):** a lifecycle stage for "abandoned before operation", if the owner wants the distinction outside GAP-07 as well.

`entity_assessments` was introduced in this unmerged PR, so the change breaks no published consumer. The v0.6.0 consumer still verifies the data.

# Tier 2: strategy measurement evidence (registry v0.8.0)

Approved scope: targets, allocations, ministry-reported outputs and independent findings for Digital Morocco 2030 and Morocco AI 2030, each kept in its own kind. No predicate, schema, entity, relationship or lifecycle change.

## Evidence diff and classification

| Record | Source (location) | Kind | Classification | Why |
|---|---|---|---|---|
| MAI-EV-0050 | Ministry's programme 429 performance project, 2023 finance bill (printed p.38) | Target: EGDI rank 75th by 2026; 2021 realisation 106 | OFFICIAL TARGET, `target_year` 2026 | Finance-law target. It predates the strategy and is the overall EGDI, not OSI. |
| MAI-EV-0051 | Same document (p.39) | Targets: jobs created 190,000 by 2030; digitalised procedures 2,000 by 2030 | OFFICIAL TARGET, 2030 | The document leaves "job created" undefined. |
| MAI-EV-0052 | Performance project, 2024 finance bill (pp.48, 49, 100; Arabic) | Target: EGDI 85th by 2026; 2022 realisation 101; UN values 110 / 106 / 101 | OFFICIAL TARGET, 2026 | Overall EGDI, the average of three indices. Arabic transcribed from page images. |
| MAI-EV-0053 | Same document (pp.51–52) | Target: jobs created 270,000 by 2030; defined as digital-economy jobs on formal contracts (CNSS) | OFFICIAL TARGET, 2030 | Its 2022 realisation of 130,000 covers offshoring only. |
| MAI-EV-0054 | 2026 finance law, detailed budget (PDF p.343) | Allocation: MAD 1,500,000,000 in payment appropriations, programme 429, project 20 "Mise en œuvre de la stratégie Maroc Digital" | VERIFIED FACT about the law | An authorisation to spend, not expenditure. Execution would need the loi de règlement. |
| MAI-EV-0055 | Ministry activity report 2025 (printed p.32; Arabic) | Reported output: more than 148,500 offshoring-sector jobs at end-2024 | UNVERIFIED CLAIM | Ministry-reported and unchecked. Offshoring sector only, not total digital jobs. |
| MAI-EV-0056 | Same report (p.47) | Reported output: 22,649 new digital-training enrolments in 2024–25 (21,125 in 2023–24) | UNVERIFIED CLAIM | Enrolments, not graduates or certified talents. |
| MAI-EV-0057 | Cour des comptes, *Principaux axes* 2023–2024 (p.13) | Independent audit finding: 605 digitalised services at end-2023; no more than 23 per cent fully digitalised | VERIFIED FACT of the Court's statement | Pre-strategy baseline. The summary does not set out its method. |
| MAI-EV-0058 | Ministry release, 8 Sept 2026 | Targets: MAD 100 bn, 50,000 jobs, 200,000 talents trained and certified; separately, 100,000 new digital talents a year | OFFICIAL TARGET, 2030 | The yearly flow is a different measure from the cumulative certified count. |

## Indicator definitions and source conflicts (recorded, not reconciled)

- **E-government ranking:**
  - the strategy: 113th → 50th on the **Online Services Index** (MAI-EV-0049; the 113th is unverified);
  - finance-law performance projects: **overall EGDI** 75th by 2026 (2023 bill) and 85th by 2026 (2024 bill);
  - the UN: overall EGDI 101st (2022) and 90th (2024), plus OSI values without ranks (MAI-EV-0046).
- **Jobs:**
  - the strategy: 240,000 direct jobs, with no year in the brochure;
  - 2023 bill: 190,000 jobs created by 2030, undefined;
  - 2024 bill: 270,000 by 2030, digital-economy jobs on formal contracts, with a 2022 baseline that covers offshoring only;
  - ministry report: 148,500 offshoring-sector jobs at end-2024, a stock and not jobs created.
- **Talent:**
  - Morocco AI 2030: 200,000 trained and certified;
  - 100,000 new digital talents trained each year;
  - ministry report: 22,649 new enrolments.
- **Money:**
  - MAD 1.5 bn appropriated for 2026;
  - the Head of Government's MAD 1.7 bn (2024) stays an unchecked statement (MAI-EV-0003);
  - no expenditure is recorded.

## GAP-02 and GAP-06 re-assessment

- **GAP-02** (Morocco AI 2030) adds the ministry's own statement of the targets and the separate annual talent objective. Neither has a baseline, definition or count reached. Still open.
- **GAP-06** (Digital Morocco 2030) adds four statements:
  - the conflicting finance-law targets, beside the strategy's own;
  - the 2026 allocation, explicitly not expenditure;
  - the two ministry-reported outputs, with the definitions that keep them apart from the objectives;
  - the Court's pre-strategy finding.

  "Not established" now names measured progress after the launch, the OSI rank, and any amount actually spent. "Evidence needed" asks for post-2024 measurements of the strategy's own indicators, the UN OSI ranking, budget execution data and a ministry reconciliation of objectives with indicators. Still open.
- **Q9** now lists every target record per strategy: 8 rows, each showing no measured progress. Its introduction states that finance-law targets, some predating the strategy, appear with their source, and that conflicts are recorded in the gap.

## Test correction found during Tier 2

A Sprint 07 test meant to forbid progress wording in GAP-06 read a field named `statement`, which gap statements do not have, so it checked only empty strings. It now reads each statement's text, in GAP-02 and GAP-06, and allows progress wording only in a sentence that negates it.

## Verification

- **Gates:** validator 0 problems; build check 0 stale; two rebuilds after the commit change no file; `check_site` 74 pages, 0 problems.
- **Tests:** 324 pass, 9 of them new in `tests/test_strategy_measurement.py`.
- **Consumers:** the current consumer verifies v0.8.0 (58 records, 7 gaps), and so do the v0.6.0 and v0.7.0 consumers (the latter tested).
- **Mutations:** 13 of 13 caught:
  - outputs promoted to VERIFIED FACT (both);
  - the allocation said to be spent, or its "not expenditure" removed;
  - offshoring jobs equated with digital jobs;
  - enrolments equated with certified talents;
  - the audit finding read as progress;
  - the targets silently reconciled;
  - GAP-06 closed;
  - the finance-law rank called OSI;
  - a target year dropped;
  - a GAP-06 number not found in its sources;
  - the Q9 provenance sentence removed.
- **Accessibility and layout:** questions, gaps, evidence, the two strategy pages, the ministry page, the public-administration page, data and methodology at 320, 375 and 1366 px: 0 axe violations, no page-level horizontal scroll.
- **Source check:** MAI-EV-0057 and 0058 match in full. The other excerpts are table rows or Arabic passages, read from rendered pages because the PDF text layers split cells or reverse Arabic; each record's note says so.

## Remaining limitations

- No actual expenditure: the budget settlement law and execution reports were not obtained.
- No measurement of the strategy's own indicators after its launch.
- No UN OSI ranking.
- Performance projects for 2025–2027 were not obtained, because the finance ministry's server reset connections.
- The ministry's outputs remain unverified, and the Court's method is not stated in the summary.
