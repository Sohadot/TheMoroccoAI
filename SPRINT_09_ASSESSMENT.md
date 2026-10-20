# Sprint 09: Execution Evidence and Outcome Measurement

## Tier 1 evidence assessment (read-only)

- **Baseline:** registry v0.8.0 at `59c4221`: 58 records, 65 entities, 78 relationships and 7 open gaps.
- **Research date:** 20 October 2026.
- **Registry changes:** none. No registry file, branch commit or version number has been changed. Everything below is a proposal for the owner to approve or reject.
- **Governing distinction:** target ≠ allocation ≠ expenditure ≠ output ≠ outcome.
- **How figures were checked:** every figure proposed for admission was read from a rendered image of the original page, or from the original table text in the case of the UN annexes. The Arabic tables (loi de règlement, Cour des comptes, ministry Bilan) have broken or reversed text layers, so the page image was used as the authority for them. Each record proposed from them needs a note saying manual visual verification was required.

---

## 1. Result by dimension

| # | Question | Stopping state |
|---|---|---|
| 1 | Money committed, disbursed or spent on Digital Morocco 2030 | **NOT ESTABLISHED** at strategy or project level. **FOUND BUT NON-COMPARABLE** at ministry level (2024 loi de règlement, Treasury 2025 annual report). |
| 2 | Digital Morocco 2030 indicators measured after launch | **NOT ESTABLISHED** for jobs, GDP contribution and the share of fully digitalised services. The only new figures are ministry-reported outputs on other definitions, which are FOUND BUT NON-COMPARABLE. |
| 3 | Morocco AI 2030 indicators measured | **NOT ESTABLISHED.** Only targets exist; they are already recorded as MAI-EV-0058. |
| 4 | Later documents reconciling the conflicting targets | **NOT ESTABLISHED.** One new conflict was found (EGDI top 50 against OSI 50th), plus one scope attribution (270,000 = offshoring sector) that is not a reconciliation. |
| 5 | UN-published OSI rank for Morocco | **NOT ESTABLISHED.** The 2022 and 2024 survey annexes publish OSI values without a rank column. The UN does not publish a rank on this index, and the registry does not compute one. |

As the Sprint 09 brief requires, NOT ESTABLISHED is a statement about what this search covered. It is not evidence that no such data exists.

---

## 2. W1: Budget execution

### 2.1 Project 20 changes meaning between years (key finding)

Programme 429 (Transition numérique), project 20, investment budget:

| Finance law | Label of project 20 | CP for the year (MAD) | Source (visually verified) |
|---|---|---|---|
| LF 2024 | Développement de l'Administration Numérique | 273,000,000 | Morasse_2024_FR.pdf, printed p.329 / PDF p.333 |
| LF 2025 | Mise en œuvre de la stratégie Maroc Digital | 1,500,000,000 | Tome3_2025_FR.pdf, printed p.330 / PDF p.69 |
| LF 2026 | Mise en œuvre de la stratégie Maroc Digital | 1,500,000,000 | Morasse_2026_FR.pdf, printed p.339 / PDF p.343 (MAI-EV-0054) |

In 2024 programme 429 was split into projects 20 (administration), 30 (economy, MAD 600,000,000) and 40 (inclusion, MAD 506,500,000). There is no "Maroc Digital" line in 2024.

So **no series can be built on the code "429/20" alone**. Any execution figure for project 20 in budget year 2024 would measure a different line, not the strategy.

The operating budget (matériel et dépenses diverses) has its own line for the same project: MAD 14,230,000 in both 2025 (Tome 3, PDF p.68) and 2026 (Morasse 2026, printed p.337). The registry records only the investment line.

### 2.2 Lead A: verified, but at a different URL

`/Publication/db/2025/Morasse_2025_FR.pdf` returns 404. The 2025 finance law is published as `Tome1/2/3_2025_FR.pdf` under `/Publication/db/2024/`.

On Tome 3, printed page 330:
- page heading "BUDGET D'INVESTISSEMENT POUR L'ANNÉE BUDGETAIRE 2025";
- chapter 1.2.2.2.0.33.000;
- column "Crédits de Paiement pour l'année budgétaire 2025";
- row "490 | 20 | Mise en œuvre de la stratégie Maroc Digital | 1 500 000 000";
- Total Programme 429: 1,545,000,000;
- TOTAL CHAPITRE: 1,779,225,000;
- the commitment-credit column ("Crédits d'Engagement pour 2026 et suivants") is blank.

The page, the year and the column are all confirmed. **Admissible (C1).**

### 2.3 Lead B: 2024 loi de règlement (law n° 04.26)

**Source.** Enacted text: Bulletin officiel n° 7533, 10 August 2026, Dahir n° 1.26.57 of 28 July 2026 (`PLR 2024_BO_7533-fr.pdf`; the content is Arabic despite the file name). Its figures are identical to the bill `PLRn0426LF2024.pdf`.

**Investment, table "ج".** Bill p.14, BO p.5160; rotated page image checked. Chapter 1.2.2.2.0.33.000 (the ministry):

| CP LF 2024 | Carried over | Total credits | **Expenditure (النفقات)** | CP available at year end |
|---|---|---|---|---|
| 1,758,725,000.00 | 6,031,428.48 | 1,764,756,428.48 | **1,704,114,014.52** | 60,642,413.96 |

The other credit columns (assistance funds, minister's decisions, additional credits) are all 0.00.

**Operating, table "ب".** Matériel et dépenses diverses: credits 190,000,700.00; expenditure 59,454,923.33.

**What is and is not available.** These are **ministry-chapter totals only**. The law has no programme or project rows. No programme-level annex and no ministry performance report (RAP) for 2024 was found: mmsp.gov.ma lists only performance plans (PDPs), and the RAP URLs return 404.

**Fund caveat.** The fund "صندوق تحديث الإدارة العمومية ودعم الانتقال الرقمي واستعمال الأمازيغية" (CAS 3.x.0.0.1.33.001; public administration modernisation, digital transition and use of Amazigh) received MAD 1,684,403,680 in 2024 and spent MAD 837,465,520.95. Its 2024 resources (1,684.4 m) are close to the ministry's investment expenditure (1,704.1 m), which suggests the investment expenditure may largely consist of transfers into this fund. **No document states this.** It is therefore not established, and the 1,704.1 m must not be read as money spent on digital projects.

**Classification.** Actual expenditure, ministry level, budget year 2024. Comparability with the strategy: none. The strategy launched in September 2024, and the 2024 budget had no strategy line. **Admissible as ministry-level execution (C2), on the owner's decision.**

### 2.4 Treasury (TGR) execution reports

**2025 annual report** (`Rapport-Annuel-executionLF2025.pdf`, p.11, image checked). Investment by ministry, "TRANSITION NUMERIQUE ET REFORME DE L'ADMINISTRATION":

| LF 2025 (MDH) | December 2025 (MDH) | Réalisé |
|---|---|---|
| 1.779,2 | 1.348,7 | 75,8% |

The basis has two limits. Footnote 6 says the LF column excludes carry-overs and other credit movements. The report does not say whether the "Décembre 2025" column counts payment orders or payments.

These figures are provisional pending the 2025 loi de règlement. They are ministry level and not comparable with the loi de règlement basis, which includes carry-overs. **Candidate (C3); recommended for admission with that boundary.**

**Q2 2026 report.** 1 579,2 / 2,1 / 0,1%. This is half-year, cumulative and ministry level. **Not recommended:** a mid-year figure invites a misleading reading.

### 2.5 Cour des comptes, report on the execution of the 2024 finance law (June 2026)

Table 41, p.46 (image checked), ministry row: 1.764,8 | 1.704,1 | **96,6%**. The 2023 and 2022 rates are 98,1 and 99,2. The 2021 cell is merged with the next row, so it is not used.

The table's stated source is "مشروع قانون التصفية لسنة 2024 – معالجة المجلس الأعلى للحسابات" (draft 2024 settlement law, processed by the Court). It therefore **re-presents the loi de règlement figures and is not an independent measurement**. Recommended use: as a corroborating excerpt in C2, not as a separate record.

### 2.6 Not admissible or not needed (W1)

| Candidate | Classification | Reason |
|---|---|---|
| Fund (CAS 33.001) commitments 852.7 m and payment orders 837.5 m (2024) | Non-comparable | Fund-level, and it mixes administration reform, digital transition and use of Amazigh. |
| Cour des comptes table 61 (cancellations) | Insufficient for the question | Credit management, not spending. |
| TGR operating and personnel lines | Non-comparable | Not strategy-specific. |
| 2023 loi de règlement (n° 07.25) | Not used | Scanned, and precedes the strategy. |
| Ministry RAP 2024 | Not established | No URL found. |

---

## 3. W2: Digital Morocco 2030, post-launch measurements

| Source | Finding | Classification |
|---|---|---|
| Ministry Bilan 2025 (7 Sep 2026), p.34–35 | Offshoring jobs: 130,000 (2022), 140,938 (2023), 148,501 (2024); offshoring exports MAD 27,083 m (2025) | Ministry-reported output. Offshoring scope only. The 148,500 figure is already MAI-EV-0055. **Non-comparable** with 240,000 total direct digital jobs. |
| Bilan 2025, p.34 (printed), image checked | Circular 2025/15 (in force 1 Jul 2025): 270,000 direct jobs and MAD 40 bn offshoring exports by 2030, "from 130 thousand" and from MAD 15.78 bn in 2022 | **OFFICIAL TARGET, offshoring sector (C5).** Same page, 9 Dec 2025: the offer "Offshoring Maroc" "provides 130 thousand direct jobs", which conflicts with 148,500 at end-2024 in the same report. To be recorded in the note, not resolved. |
| Bilan 2025, printed p.15, image checked | Strategy objectives: simplification 40%, shorter delays 50%, digital use 50%, user satisfaction 80% | **Insufficient.** No baseline, no definitions, and no target year other than the strategy's name. Hold. |
| Bilan 2025, printed p.15 | The ministry says it surpassed an expected EGDI ceiling of 93rd "by three full ranks" | Implementer narrative about the UN 2024 EGDI 90th, which is already recorded (MAI-EV-0046). Not admitted. |
| Bilan 2025, printed p.20–21 | More than 600 services online; national portal (14 Feb 2025) with more than 650 e-services | Ministry-reported output. "Fully digitalised" is not defined. **Non-comparable** with the Cour des comptes figures (605 services, 23%). Not recommended. |
| PLF 2026 presentation note (MEF, Oct 2025) | Enrolments 21,125 → 22,649 (PDF p.58), but **22,258** for the same 2024-25 programme at PDF p.83 | **Conflict inside an official document** affecting MAI-EV-0056 (22,649). Propose recording it in that record's note (C6). |
| Cour des comptes annual report 2024-25 (BO 7476 bis, 23 Jan 2026) | No chapter on the strategy; no update of 605 services / 23% | Not established. MAI-EV-0057 remains the latest independent figure. |
| Office des changes, balance of payments 2025 (Oct 2026) | Computer services receipts MAD 12,717 m (2025) against 13,471 m (2024) | Measured, but of a related aggregate with no offshoring line. **Non-comparable.** Not recommended. |
| HCP, labour force survey 2025 | No ICT, digital or offshoring employment breakdown | Not established. |

**No independent post-launch measurement was found for the jobs, GDP-contribution or services objectives.** The UN 2024 survey, already recorded, was published within days of the strategy's launch. It cannot measure progress under the strategy.

## 4. W3: Morocco AI 2030

- The ministry release of 8 September 2026 (already MAI-EV-0058) gives targets only: MAD 100 bn value added, 50,000 jobs and 200,000 talents trained and certified. It lists "la mesure de la performance" as one of ten programmes but gives no baseline, definition or measurement.
- The AI section of the Bilan 2025 is narrative.
- The FRMF (Moroccan football federation) programme "to train 200,000 young people" is a programme target, distinct from the 200,000 trained and certified talents.

**NOT ESTABLISHED. No candidates.**

## 5. W4: Reconciliation and the OSI rank

### 5.1 New conflicting statement of the ranking objective (C4)

The PLF 2025 presentation note (MEF, 18 Oct 2024, after launch), printed p.110 / PDF p.120, image checked, says:

> "Il a aussi pour ambition de faire figurer le Maroc, d'ici 2030, au top 50 mondial sur l'EGDI (E-Government Development Index) des Nations Unies"

The strategy's brochure (MAI-EV-0049) defines the same objective as 50th on the **OSI**. The finance ministry's document states it on the **EGDI** and does not explain the difference.

This is a conflict to record side by side in GAP-06, not a reconciliation. On the same page the note breaks down "100.000 nouveaux talents (digital talents) par an" as 45,000 trained, 50,000 reconverted and 6,000 foreign talents attracted. That supports keeping the existing separation from the AI 2030 "200,000 trained and certified".

### 5.2 The 270,000 figure

The Bilan 2025 attributes 270,000 by 2030 to the offshoring sector, under Circular 2025/15, from a 2022 baseline of 130,000. This matches the PDP 2024 definition already recorded (MAI-EV-0053).

**No document states how 190,000, 240,000 and 270,000 relate.** Under the out-of-scope rule ("no reconciliation by inference"), GAP-06 must still say the registry does not reconcile them. It may add that a 2025 ministry report attributes 270,000 to the offshoring sector.

### 5.3 Performance plans (PDPs) for 2025 to 2027

Not established. mmsp.gov.ma lists PDPs up to 2024 only. The PLF 2025 to 2027 pages on finances.gov.ma return 404, and lof.finances.gov.ma resets the connection.

### 5.4 UN OSI rank

**2022 annex, table A.8, "Online Service Index (OSI) and its components".** Columns: Country | OSI Group | OSI 2022 | IF | CP | SP | EPI | TEC | EGDI Group | EGDI 2022. Morocco: Middle OSI, 0.4721. **No rank column.** Only EGDI (101), EPI (128) and LOSI are ranked.

**2024 technical appendix, table 7.** Same structure. Morocco: High OSI, 0.5618. **No rank column.** EGDI is ranked 90 (table 2.1) and EPI 102 (table 9).

**A rank computed from the published values.** During research a position was computed for each edition: one plus the number of the 193 countries with a strictly higher OSI value, the competition ranking the UN uses for EGDI. Each computation was repeated from a second table of the same edition. **The computed values are deliberately not reproduced in this document, the registry or the site**: they are a calculation, not a figure any source publishes, and recording them here would let them circulate as if they were. Anyone can repeat the calculation from the annex tables named above.

**Decision (owner, Tier 2): no derived rank is published.** Rule 1 requires an identified original source. The registry publishes only what the UN does: OSI values without ranks. MAI-EV-0046 and GAP-06 say that the annex tables contain no UN rank on this index, and that the registry does not compute one.

---

## 6. Proposed records (Tier 2, on the owner's approval)

These would be MAI-EV-0059 onward. Figures are as read from the page images.

**C1: LF 2025 allocation**
- **Source:** Tome3_2025_FR.pdf (MEF, Volume 3/3), printed p.330.
- **Classification:** VERIFIED FACT, allocation.
- **Related:** digital-morocco-2030, ministry-digital-transition.
- **Claim:** The 2025 finance law's investment budget for the Ministry Delegate in charge of Digital Transition and Administration Reform provides, under programme 429, MAD 1,500,000,000 in payment appropriations for 2025 for project 20, "Mise en œuvre de la stratégie Maroc Digital".
- **Kind:** allocation (flow, one year).
- **Negative boundary:** not expenditure. It must not be added to the 2026 appropriation to give a cumulative amount; each law opens a separate year's credits, and execution is unknown. The commitment-credit column is blank. In 2024, project 20 was a different line.

**C2: 2024 ministry-level execution**
- **Source:** law n° 04.26, BO n° 7533 (10 Aug 2026), table ج, BO p.5160.
- **Classification:** VERIFIED FACT, expenditure.
- **Related:** ministry-digital-transition only, **not** the strategy.
- **Claim:** The 2024 settlement law records, for the investment chapter of the Ministry Delegate in charge of Digital Transition and Administration Reform, expenditure of MAD 1,704,114,014.52 against total credits of MAD 1,764,756,428.48.
- **Excerpts:** the row as printed. Cour des comptes table 41 (96.6%) as a corroborating second excerpt, noted as derived from the settlement-law draft.
- **Kind:** expenditure, ministry level, budget year 2024.
- **Negative boundary:** not spending on Digital Morocco 2030. The 2024 budget had no strategy line, and project 20 was "Développement de l'Administration Numérique". The law gives no programme or project breakdown. Whether part of the expenditure was transfers to the special Treasury account is not established. The law does not say whether it counts payment orders or payments.
- **Note:** manual visual verification was required (rotated Arabic table).

**C3: 2025 provisional ministry-level execution**
- **Source:** TGR, Rapport annuel sur l'exécution de la loi de finances – 2025, p.11.
- **Classification:** VERIFIED FACT, of what the Treasury reports.
- **Related:** ministry-digital-transition only.
- **Claim:** The Treasury's 2025 execution report shows, for the Ministry of Digital Transition and Administration Reform's investment spending, MAD 1,348.7 million executed by December 2025 against MAD 1,779.2 million in the 2025 finance law, or 75.8 per cent.
- **Kind:** execution measure, ministry level, provisional.
- **Negative boundary:** not spending on the strategy line. The initial-law basis excludes carry-overs and is not comparable with the settlement law's basis. Pending the 2025 settlement law. The measure (payment orders or payments) is not stated.

**C4: Post-launch EGDI statement of the ranking objective**
- **Source:** PLF 2025 note de présentation, printed p.110.
- **Classification:** OFFICIAL TARGET, target_year 2030.
- **Related:** digital-morocco-2030.
- **Claim:** The finance ministry's presentation note to the 2025 finance bill states that Digital Morocco 2030 aims to place Morocco in the world's top 50 on the United Nations E-Government Development Index by 2030.
- **Negative boundary:** conflicts with the brochure's OSI definition (MAI-EV-0049). The registry does not reconcile the two. Not a measurement.

**C5: Offshoring-sector target under Circular 2025/15**
- **Source:** Bilan MTNRA 2025, printed p.34.
- **Classification:** OFFICIAL TARGET, target_year 2030.
- **Related:** digital-morocco-2030.
- **Claim:** The ministry's 2025 activity report states that Circular 2025/15 on the offshoring sector, in force from 1 July 2025, aims at 270,000 direct jobs and MAD 40 billion in offshoring service exports by 2030, from 130,000 jobs and MAD 15.78 billion in 2022.
- **Negative boundary:** offshoring jobs, not total digital jobs. It does not state a relation to the strategy's 240,000. It is not a reconciliation. The same page's statement that the offer provides 130,000 direct jobs conflicts with the 148,500 reported for end-2024.
- **Note:** manual visual verification was required.

**C6: Note amendment to MAI-EV-0056 (no new record)**
- **Change:** add that the PLF 2026 presentation note gives 22,649 (PDF p.58) and also 22,258 (PDF p.83) for the 2024-25 intake.
- **Classification:** unchanged.
- **Rule:** the conflict is preserved, not resolved. The historical record is not rewritten; the note is extended.

**Held or not admitted:**
- the derived OSI ranks;
- the Q2 2026 TGR figure;
- the special-account figures;
- the Bilan's undefined service-simplification targets;
- the Bilan's figures for "more than 600" and "650" services;
- Office des changes and HCP aggregates.

## 7. Impact on the gaps

**GAP-02 (Morocco AI 2030): stays open, with no change of statement.** No new qualifying evidence was found. Re-assessment confirms the current text. The PLF 2025 note's breakdown of the 100,000 talents does not concern the AI roadmap's targets, so it is not assessed under GAP-02.

**GAP-06 (Digital Morocco 2030): stays open.**

*Additions to "established", if C1 to C5 are admitted:*
- The 2025 and 2026 laws each appropriate MAD 1,500,000,000 for the strategy line. These are allocations, not expenditure.
- Execution is published only at ministry level. The ministry's 2024 investment expenditure under the settlement law, and its 2025 Treasury execution rate, are ministry totals, not spending on the strategy.
- The ranking objective is stated on the OSI by the brochure and on the EGDI by the finance ministry's 2025 note. It is unreconciled, and is added to the existing conflict statement.
- A 2025 ministry report attributes 270,000 to the offshoring sector. The registry still does not reconcile 190,000, 240,000 and 270,000.

*Proposed "unestablished" wording change:*
- Old: "Morocco's rank on the Online Services Index in any edition".
- New: "a rank on the Online Services Index published by the United Nations (the 2022 and 2024 survey annexes publish values without ranks)".
- "Any amount actually spent on the strategy" stays as it is.

**Fingerprints.** GAP-06 records and relationships would change, so its fingerprint and assessed_records need re-assessment. GAP-02 needs only a re-assessment date.

## 8. Tier 2 proposal

**Option A (recommended): v0.9.0.**
- Admit C1 to C5 and the C6 note.
- Update GAP-06 as in section 7.
- Tests protecting each distinction:
  - an allocation is never summed across years;
  - ministry execution is never related to a strategy entity;
  - a project code is never compared across years where its label differs;
  - TGR and settlement-law bases are never combined;
  - the EGDI and OSI statements of the 50th objective stay side by side;
  - no derived OSI rank is published anywhere;
  - the two enrolment figures both appear.
- The Q9 row count rises from 8 to 10 (C4 and C5), and the test is data-derived.
- Gap and entity counts are unchanged: 63 records, 65 entities, 78 relationships, 7 gaps. No new predicate, schema or entity.

**Option B: minimal.** Admit only C1 and the C6 note; no version bump beyond a patch. This leaves the ministry-level execution evidence out of the registry, so the "spent" question stays answered only by absence.

**Option C: no mutation.** Record this assessment only. This is valid under the brief, but the new EGDI/OSI conflict and the enrolment conflict would then be known and unrecorded.

**Owner decisions needed:**
1. Choose option A, B or C.
2. Whether C2 and C3 may relate to ministry-digital-transition: they record ministry-level money, and no strategy relation is proposed.
3. Confirm that the derived OSI rank stays unpublished.

---

## Appendix: Sources inspected

**Finance laws**
- finances.gov.ma/Publication/db/2024/Tome3_2025_FR.pdf
- finances.gov.ma/Publication/db/2024/Morasse_2024_FR.pdf
- finances.gov.ma/Publication/db/2026/Morasse_2026_FR.pdf

**Settlement law and execution reports**
- finances.gov.ma/Publication/db/2026/PLRn0426LF2024.pdf
- finances.gov.ma/Publication/db/2026/PLR 2024_BO_7533-fr.pdf
- finances.gov.ma/Publication/tgr/2026/Rapport-Annuel-executionLF2025.pdf
- finances.gov.ma/Publication/tgr/2026/Rapport-Trim-executionLF-2026-2T.pdf

**Cour des comptes**
- courdescomptes.ma/wp-content/uploads/2026/07/RELF-2024-VD.pdf
- sgg.gov.ma/BO/AR/3111/2026/BO_7476-bis_Ar.pdf (annual report 2024-25)

**Ministry**
- mmsp.gov.ma/sites/default/files/publications/Bilan_MTNRA_2025_07092026.pdf
- Ministry news item of 8 Sep 2026 (Maroc IA 2030)

**Finance-bill presentation notes**
- finances.gov.ma/Publication/db/2025/note-presentation_Fr.pdf (PLF 2025)
- finances.gov.ma/Publication/db/2026/note-presentation_Fr.pdf (PLF 2026)

**UN E-Government Survey**
- 2022 Annexes (desapublications.un.org …/2022-09/Annexes+cover.pdf)
- 2024 Technical Appendix (…/2024-10/Technical Appendix (Web version) 30102024.pdf)

**Other statistics**
- Office des changes, Rapport annuel BP & PEG 2025
- HCP, Activité, emploi et chômage 2025

**Blocked**
- lof.finances.gov.ma (connection reset)
- PLF 2027 note URL (404)
- RAP URLs on mmsp.gov.ma (404)
- the UN data-centre download (an ASP.NET postback, not attempted)

---

# Tier 2: execution evidence (registry v0.9.0)

**Owner decision:** Option A approved. C2 and C3 relate to `ministry-digital-transition` only. No strategy attribution. Derived OSI ranks are not published, in the registry or in this document. GAP-02 and GAP-06 stay open. No change to schema, predicates, entities, relationships or lifecycle.

## Records

| ID | Proposal | Kind | Related entities |
|---|---|---|---|
| MAI-EV-0059 | C1: LF 2025, project 20, MAD 1,500,000,000 CP | VERIFIED FACT, allocation | digital-morocco-2030, ministry-digital-transition |
| MAI-EV-0060 | C2: loi de règlement 2024 (law 04.26, BO 7533), ministry investment expenditure | VERIFIED FACT, expenditure (ministry total) | ministry-digital-transition only |
| MAI-EV-0061 | C3: TGR annual report 2025, ministry investment execution | VERIFIED FACT, provisional execution (ministry total) | ministry-digital-transition only |
| MAI-EV-0062 | C4: PLF 2025 note, top 50 on the EGDI by 2030 | OFFICIAL TARGET 2030 | digital-morocco-2030 |
| MAI-EV-0063 | C5: Circular 2025/15, offshoring targets, as the Bilan 2025 presents them | OFFICIAL TARGET 2030 | digital-morocco-2030, ministry-digital-transition |

**Note changes:**
- **MAI-EV-0056 (C6, a correction):** records the PLF 2026 note's two enrolment figures, 22,649 and 22,258, without resolving them.
- **MAI-EV-0046:** records that the 2022 and 2024 UN annex tables publish OSI values without a rank column, and that the registry does not compute one.
- **Re-check of the BO 7533 row:** the 2024 figures were re-read from the enacted text, BO p.5160, not only the bill.

## Gaps

**GAP-06** has a new fingerprint, `cdb898ad5ad8dfc7`, and three changes:

*New statements:*
- the 2025 and 2026 appropriations are not added together, and the 2024 project code designated a different line;
- the EGDI top-50 statement, placed directly after the brochure's OSI objective and unreconciled;
- the offshoring attribution of 270,000, unreconciled.

*Extended statement:* the UN statement now says the annex tables give values without a rank column.

*Unestablished text:*
- it now names "a rank on the Online Services Index published by the United Nations", where it previously said "Morocco's rank on the Online Services Index in any edition";
- it states that budget execution is recorded only as ministry-level totals, which are not spending on the strategy.

The execution records cannot be cited by GAP-06: the validator requires a gap's evidence to concern its entities. That enforces the owner's decision structurally.

**GAP-02:** re-assessed, no change.

## Protection

`tests/test_execution_evidence.py` has 11 tests, covering:
- each record's kind;
- ministry execution never related to, cited for, or worded as spending on a strategy;
- appropriations never summed;
- project 20 never compared across years;
- the TGR and settlement-law bases never combined;
- the EGDI and OSI statements adjacent;
- the offshoring figure not treated as a reconciliation;
- both enrolment figures kept;
- no OSI rank beyond those the sources state, in any data, page or root Markdown document;
- counts and Q9 (10 target rows);
- the v0.8.0 consumer verifies v0.9.0.

**Mutation checks:** 11 of 11 caught, either by the validator or by these tests. The mutations were:
- C2 linked to the strategy;
- C2 cited in GAP-06;
- a cumulative MAD 3 bn figure;
- a derived rank, in two wordings;
- the enrolment conflict dropped;
- the EGDI statement dropped;
- the offshoring figure "reconciled";
- ministry money described as spent on the strategy;
- the two execution bases combined;
- project 20 compared with 2024.

## Results

- 63 records, 65 entities, 78 relationships, 7 gaps (all open).
- Validator: 0 problems. Build check: 0 stale files. Site check: 74 pages, 0 problems. 335 tests pass.
- Consumers v0.6.0, v0.7.0, v0.8.0 and current all verify v0.9.0.
- Accessibility (axe, WCAG 2.1 AA, at 320, 375 and 1366 px): 0 violations and no page-level horizontal scroll on the nine changed page types.
- Live excerpt check:
  - MAI-EV-0061 matches.
  - MAI-EV-0059's table row is unmatched, like MAI-EV-0054's, because plain extraction splits the cells.
  - MAI-EV-0060, MAI-EV-0062 and MAI-EV-0063 are unmatched because their text layers are rotated tables, outlines or broken Arabic ligatures.
  - Each note discloses this, and each was verified visually.
