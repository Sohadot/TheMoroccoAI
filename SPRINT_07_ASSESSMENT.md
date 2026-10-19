# Sprint 07 — Evidence Acquisition & Independent Corroboration

Baseline: `main` at 28031671be7e4b7612e0d07a2990c289b7f083db (registry v0.5.0, Sprint 06 closed and verified in production).
Result: registry v0.6.0, with six new records, two reclassified relationships, three re-assessed gaps and three corrections. No gap is closed and no lifecycle stage changes.

The aim was better evidence, not more of it. Most of the sources found were not admitted (see Phase 4).

## Phase 1 — Inventory and research matrix (read-only)

| Gap | Question | Records assessed (v0.5.0) | What would move it | Priority | Research track |
|---|---|---|---|---|---|
| GAP-05 | Formal-act relationships that rest only on announcements | computed: 19 of 33 | The published texts of conventions, or Bulletin Officiel acts | 1 | A, C |
| GAP-04 | Construction or operation of data-centre and computing projects | 0006, 0007, 0019, 0030 | Permits, commissioning, confirmation by an operator or an independent party; at least an official confirmation of the signings | 2 | E |
| GAP-03 | Independent documentation of AI workloads on Toubkal | 0020, 0041 | Usage reports; papers by non-UM6P authors; the GemMaroc study's own statement of where it ran | 3 | D |
| GAP-06 | Measured progress towards the Digital Morocco 2030 targets | 0001, 0002, 0003, 0018 | UN EGDI editions; official indicator reports; finance-law documents | 4 | B |
| GAP-02 | Measured progress towards the Morocco AI 2030 targets | 0011, 0013, 0040 | Official indicator reporting | 5 | B |
| GAP-01 | Use and outcomes of Idarati AI | 0013, 0034, 0035, 0038, 0040 | An operator's usage report; an independent evaluation | 6 | E |

Priority is based on how likely primary, freely readable evidence was to exist. Gazette acts and ministry releases were likely; usage statistics were not.

## Phase 2 — Search strategy

- Four research tracks ran in parallel (A+C, B, D, E). Each followed the same rules:
  - report a source only after opening and reading it;
  - quote it verbatim with its location;
  - classify it on a fixed scale (from press announcement up to complete signed instrument, legal establishment act, or evidence of operation);
  - record a blocked page as BLOCKED rather than work around it.
- Every candidate reported by a research track was then **re-read independently** before any admission decision:
  - HTML pages were fetched with curl and their text extracted;
  - PDFs were read with pdftotext;
  - the Arabic Bulletin Officiel was read **from its rendered page images**, because its text layer reverses Arabic word order.
- The figures were checked against the sources, not against the research tracks' summaries. This found two errors in the registry's existing data (see Corrections).
- Sources searched:
  - the Bulletin Officiel (Arabic and French editions, French up to 7544);
  - ministry sites (mmsp.gov.ma, maroc.ma);
  - the UN E-Government Knowledgebase;
  - finance-law notes (finances.gov.ma);
  - the Cour des comptes;
  - arXiv;
  - Europe PMC;
  - Hugging Face model cards;
  - TOP500;
  - the idarati.ma portal and the chatbot's public JavaScript bundle (read only; no form was submitted);
  - Moroccan and regional press.

## Phase 3 — Admission assessment of the admitted sources

| Record | Source (publisher, date) | Type, standing | Where the support is | Affects | Limits |
|---|---|---|---|---|---|
| MAI-EV-0047 | [BO 7534, Arabic edition](https://www.sgg.gov.ma/BO/AR/3111/2026/BO_7534_Ar.pdf), SGG, 13 Aug 2026 | official_gazette, primary | pp. 5224–5229: joint orders 1535.26 (16 Jul 2026, ROOT), 1618.26 (EduTech), 1619.26 (Industrie X.0), 1620.26 (Smart City) (22 Jul 2026) | 8 JAZARI signatures; JAZARI entity status | Publishes summaries, not the signed texts, and no signing dates. It is legal establishment, not operation. It names further founding members, which are not recorded. There is no act for Nador. Excerpts were transcribed from page images. |
| MAI-EV-0044 | [Ministry release](https://www.mmsp.gov.ma/fr/actualites/nexus-core-systems-lance-au-maroc-une-%C2%AB-ai-factory-plateform%C2%BB), 8 Apr 2026 | official_announcement, primary (party to the MoU) | the release body: four signatories | Nexus signatures (ANNOUNCED PLAN → VERIFIED FACT); GAP-04 | The MoU text is not published. The investment and capacity figures are future-tense commitments. |
| MAI-EV-0045 | [Ministry release](https://www.mmsp.gov.ma/fr/actualites/signature-d%E2%80%99une-convention-pour-l%E2%80%99op%C3%A9rationnalisation-du-campus-datacenter-vert-%C2%AB-igoudar-num%C3%A9rique-%C2%BB-%C3%A0-dakhla), 14 Apr 2026 | official_announcement, primary | the release body | Green data-centre agreement; GAP-04 | It launches studies; it is not construction. The release dates the parent agreement "1er juillet 2025"; the registry keeps 2 July, its other sources' date. |
| MAI-EV-0046 | [UN egovkb, Morocco](https://publicadministration.un.org/egovkb/en-us/Data/Country-Information/id/115-Morocco), UN DESA, undated | ranking_entry, independent | the rank-history table | Digital Morocco 2030; GAP-06; the 113 baseline | The 2024 edition (90th, EGDI 0.6841) measures the starting position. No 2026 edition had been published. No edition shows 113th. |
| MAI-EV-0042 | [arXiv 2505.17082v1](https://arxiv.org/pdf/2505.17082v1), Skiredj et al., 20 May 2025 | preprint, operator-affiliated (3 of 5 authors are UM6P) | §4 Hardware and cost; footnote 1 | Toubkal; GAP-03; correction of "Belkasmi" | Not peer-reviewed. Does not say where the runs were made. The cost uses a Runpod public rate. |
| MAI-EV-0043 | [GeneLM, Briefings in Bioinformatics](https://doi.org/10.1093/bib/bbaf311), 3 Jul 2025 | journal_article, operator-affiliated | methods: 2 A100 GPUs, 37 h, on Toubkal | Toubkal; GAP-03 | The publisher blocks automated access (403). Excerpts were matched against Europe PMC PMC12222049. The authors are UM6P. |

## Phase 4 — Decision gate

### ADMIT

- The six records above.
- Two corrections, verified personally:
  - The Toubkal article ([open-access copy](https://d-nb.info/1383883793/34)) attributes the GemMaroc runs to "Belkasmi et al. [57]". Its reference 57 is the preprint by Skiredj et al. No author of that preprint is named Belkasmi.
  - The strategy's 113th EGDI starting point appears in no UN edition. The history is 90 (2024), 101 (2022), 106, 110, 85, 82, 120, 126, 140, 138, 138, 131.

### REVIEW REQUIRED (backlog; not admitted)

| Candidate | Why not admitted now |
|---|---|
| [CIO Africa](https://cioafrica.co/fivenines-joins-nexus-on-20mw-ai-data-centre-in-morocco/), 16 Oct 2026: Nexus at the design and permitting stage | Trade press. Its figures conflict with the ministry's. It does not show construction. |
| [Yabiladi](https://en.yabiladi.com/articles/details/193710/morocco-nexus-core-systems-purchases.html): Nexus land purchase | Relays Africa Intelligence (paywalled); the primary source cannot be read. |
| [La Quotidienne](https://laquotidienne.ma/article/economie/ia-maroc), 12 Sep 2026: data-centre plans | Plans only. |
| Ministry Bilan 2024 ([Arabic PDF](https://www.mmsp.gov.ma/sites/default/files/publications/Bilan_2024_MTNRA_19112025_Ar.pdf)) and [Bilan 2025](https://www.mmsp.gov.ma/sites/default/files/publications/Bilan_MTNRA_2025_07092026.pdf) | Outputs reported by the implementer: 148,500 offshoring jobs, a metric that is not the strategy's 240,000 direct digital jobs; 22,649 digital enrolments; 650+ services. Admitting them needs an owner decision on recording self-reported outputs against targets. Bilan 2024 repeats 113. |
| PLF 2023/2024 performance projects | Give an EGDI baseline of 101 and revised targets, including a jobs target of 270,000 vs 240,000. Needs a decision on how to record conflicting official targets. |
| [PLF 2026 presentation note](https://www.finances.gov.ma/Publication/db/2026/note-presentation_Fr.pdf): MAD 1.5 bn | An allocation only; it is not progress. |
| [Le Matin](https://lematin.ma/societe/suivi-prenatal-lia-deployee-dans-les-zones-rurales-a-beni-mellal-khenifra/369275/amp), 8 Oct 2026: AI prenatal ultrasound pilot, 10→40 centres | Does not name DeepEcho, so it cannot be tied to the registry's project. |
| [Le Matin](https://lematin.ma/economie/assises-de-lia-le-maroc-passe-a-laction-avec-une-serie-daccords/288961), 3 Jul 2025: additional Nador signatories (the Governor, the Regional Council president) | Press only. Admitting it would mean new relationships. |
| Full founding-member lists in BO 7534 | Would add relationships and entities; this needs an owner decision (see below). |
| French translation of BO 7534 | Not published on the retrieval date. |

### NO CHANGE

- **Idarati AI.**
  - No usage figures exist. The "12k visiteurs par mois" on idarati.ma is hard-coded and undated, and its Indicateurs section says "Bientôt disponible".
  - Reading the chatbot bundle confirms that the demo branch is disabled (`Pe=!1`). The earlier functional check therefore reached the live `/api/agent` backend, and MAI-EV-0038 stands.
- **Ministry pages on the UM6P and green data-centre signings.** They duplicate existing evidence.
- **GemMaroc Hugging Face model cards.** No infrastructure statement.
- **Generic Toubkal acknowledgements.** They name no AI workload.
- **Toubkal user counts (309 in 2024; 345 in H1 2025).** They cover all users, not AI users.
- **UN E-Government Survey 2026.** Not published.
- **Cour des comptes 2024-25.** No audit of either strategy.
- **Moorish Times and [Morocco World News](https://www.moroccoworldnews.com/2026/08/334868/morocco-establishes-four-institutes-to-drive-ai-industry-and-smart-cities/) on the BO.** Superseded by the BO itself.

### BLOCKED (not bypassed)

- **Press:**
  - ledesk.ma (the [Nexus investigation](https://ledesk.ma/grandangle/nexus-ai-factory-lenvers-du-decor-dun-projet-a-12-milliards-de-dirhams/) and DeepEcho);
  - telquel.ma;
  - lnt.ma.
- **Government sites:**
  - chambredesrepresentants.ma (403);
  - add.gov.ma;
  - numerique.gov.ma;
  - digital.gov.ma (certificate error).
- **Africa Intelligence:** paywall.
- **Publishers:**
  - link.springer.com (bot challenge);
  - academic.oup.com (403).
- **OpenAlex:** rate limit.

## Phase 5 — Evidence diff

- **Records.** MAI-EV-0042 to 0047 were added.
- **Corrections to existing records.**
  - MAI-EV-0041 claim: the article "attributes [the runs] to \"Belkasmi et al.\" while citing the GemMaroc preprint by Skiredj et al."
  - MAI-EV-0002 note: 113th is the source's figure.
- **Relationships.**
  - cgem → jazari-root and the 7 Industrie X.0 signatures now also cite MAI-EV-0047.
  - The signatures of nexus-core-systems and ministry-digital-transition on nexus-ai-factory change from ANNOUNCED PLAN to VERIFIED FACT, on MAI-EV-0030 and MAI-EV-0044, with the note "the memorandum's text is not published".
  - No relationship was added or removed.
- **Entities.**
  - Status text updated for:
    - jazari-root, jazari-industrie-x0, jazari-edutech and jazari-smart-city ("approved by joint order … operation not documented");
    - jazari-network;
    - nexus-ai-factory;
    - green-data-centres-agreement.
  - Toubkal: the GemMaroc attribute is reworded, and a GeneLM attribute is added (operator-affiliated).
  - Every lifecycle stage is unchanged.
- **Vocabulary.** New evidence type `official_gazette`. The validator rejects it as evidence of a lifecycle stage, of use, or of an operator.
- **Presentation.**
  - Arabic excerpts carry `dir="rtl"`, use logical CSS borders and are not shown in italics.
  - The breaking-change migration note states the current version.
- **Version.** v0.6.0, with a changelog entry for PR 8. All identifiers are stable. The data contract is unchanged apart from the added vocabulary value, and the v0.5.0 consumer contract still holds (the consumer verifies OK).

### Effect on each gap

| Gap | Before | After | State |
|---|---|---|---|
| GAP-01 | — | unchanged; no usage evidence found | open |
| GAP-02 | — | unchanged; Bilan outputs held for review | open |
| GAP-03 | 0020, 0041 | + 0042, 0043. Operator-affiliated runs are documented with sizes. Independent documentation is still missing, and the GemMaroc location is unstated. | open |
| GAP-04 | 0006, 0007, 0019, 0030 | + 0044, 0045. The Nexus signing is confirmed by the ministry; the Dakhla studies were launched. Still no construction. | open |
| GAP-05 | 19 of 33 | **11 of 33**. The 8 JAZARI signatures now cite the gazette. | open |
| GAP-06 | 0001–0003, 0018 | + 0046. Independent starting position (2024); no post-launch edition yet. | open |

Signed matrix rows rise from 16 to 18 (the Nexus signatures). None is documented by its signed text.

## Phase 6 — Verification

### Machine checks

| Check | Result |
|---|---|
| `tools/registry.py` | 0 problems |
| `tools/build.py --check` | 78 generated files, 0 stale |
| Deterministic rebuild after commit (run twice) | 0 changed files |
| `python3 -m unittest discover -s tests` | 281 tests OK. Counts are computed from the data. Includes the layout probe at 320 and 375 px, now also on jazari-root, toubkal-supercomputer and nexus-ai-factory. |
| Sprint 07 adversarial tests (`tests/test_precision.py::EvidenceAcquisition`) | A gazette cannot set a stage, show use or document an operator. JAZARI stages stay announced. The 8 gazette signatures leave GAP-05, and the page shows the computed N of M. Nexus signatures are VF on 0044, with no construction wording. No registry text attributes GemMaroc to Belkasmi. The 0042 note says where the runs were made is unknown. 0046 is a starting position. Arabic excerpts are RTL. All gaps are open. |
| Ad-hoc mutations | 9 of 9 caught: a gazette sets operational; a gazette is relabelled signed_instrument; the UN record is edited without re-assessment; a VF release carries a future claim; an MoU sets in-development; an MoU sets under-construction; a record is linked to an entity that does not cite it; a gap is closed with an invalid state; a gap is resolved without resolved_by. |
| `examples/registry_consumer.py verify` | OK for 0.6.0: 47 records, 65 entities, 78 relationships, 43 rows, 6 gaps |
| `tools/check_site.py --network` | 74 pages, 0 problems |
| `tools/check_sources.py` (all 47 records) | 42 records: all excerpts matched. Exceptions below. |

Source-check exceptions:

- **MAI-EV-0047:** 10 of 11 excerpts missing, as expected. The Arabic text layer is reversed, and the note says automated matching cannot be relied on.
- **MAI-EV-0042:** 1 of 4 excerpts missing. The text layer splits the small-capital "GEMMAROC" and drops the hyphen in "H100-80GB" at a line break. The excerpt was checked against the rendered page, and the note now says so.
- **MAI-EV-0041:** blocked (Springer bot challenge, not bypassed).
- **MAI-EV-0043:** blocked (OUP 403, not bypassed).
- **MAI-EV-0029:** unreachable (TLS certificate error). Already superseded by 0032 and 0039.

### Editorial judgments (not machine-checkable)

- The BO summaries are treated as legal establishment, not as signed instruments. A gazette summary is not the signed text, so `signed_instrument` stays unused.
- A ministry release is adequate primary evidence that the ministry itself signed. The Nexus reclassification rests on that judgement; the MoU text is still unpublished.
- Operator-affiliated research papers are admitted as reports by operator-affiliated authors, never as independent documentation.
- The UN 2024 edition is read as a starting position, not progress, because it was published in the strategy's launch year.
- The Arabic excerpts were transcribed by reading page images. A second reader fluent in Arabic should spot-check them against pp. 5224–5229.

## Decisions for the owner

1. **BO founding members.** BO 7534 names further founding members of each group, for example the SGG, national police, the CNDP, ADD and the Rabat-Salé-Kénitra region for ROOT. Should they be added as `signatory_of` (or a new `founding_member_of`) relationships with new entities? This sprint did not add them.
2. **A JAZARI delivery gap.** Legal establishment is now documented, but operation is not (premises, staff, programmes). Should the registry open a gap on the delivery of the JAZARI network?
3. **Nador.** No gazette act concerns the Al Jazari institute in Nador. Should the registry record that absence, as it stands, or wait?
4. **Self-reported outputs (Bilan 2024/2025) and conflicting official targets (PLF 2023/2024).** Should they be recorded? If so, record them as UNVERIFIED CLAIM or as a distinct "reported output" kind, and never as progress?
5. **Outreach.** Should the owner contact the GemMaroc authors and the African Supercomputing Center about where the runs were made and about usage reports? Not done: this needs explicit owner approval.
