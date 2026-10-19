# Sprint 04 — Institutional utility and evidence expansion

Internal working note. It contains no valuation, buyer list, traffic or revenue figures.
Baseline: `main` = `6094fd5` (Sprint 03.5), verified identical to production. Canonical data at the
start: registry v0.3.0, 39 records, 65 entities, 78 relationships, 10 entity types, 7 domains; 155 tests.

## Stage 1 — Utility audit (read-only)

**Existing capabilities reused:** the evidence and ontology validator; lifecycle stages with their bases
(`stage_label`, `deployment_facts`); questions Q1 to Q7; generated JSON-LD, sitemap and site gates; the
source checker; the reference-first homepage.

**Questions classified against the data**

| Question | Class | Basis |
| --- | --- | --- |
| Which projects are operational, announced or planned? | A — answerable now | Q2 already answers it from lifecycle stages; reused, not duplicated |
| Which institutions are connected to which AI or computing projects, and on what evidence? | A | 43 organisation- and initiative-level relationships, each with records; scattered across entity pages and Q5, so no single view existed |
| Which of those connections rest on a formal record rather than an announcement? | A | Computable from each record's `evidence_type`, for relationships that assert a formal act: 19 of 33 (see the semantic audit) |
| What do national targets say, and what progress is recorded? | B — partially | Targets are recorded (MAI-EV-0002, MAI-EV-0011); no record measures progress |
| Is Idarati AI used, and with what results? | C — not answerable | Public availability only (MAI-EV-0034/35/38) |
| Does Toubkal run AI workloads? | B (after this sprint) | TOP500 documents capacity; a peer-reviewed article by the operator's own authors reports LLM fine-tuning (MAI-EV-0041); nothing independent |
| Have the signed data-centre or AI-factory projects been built? | C | Signatures and press reports only |

**Gaps in evidence and relationships:** use and outcomes of the one operational AI application; any
progress measurement for either national strategy; independent workload evidence for Toubkal;
construction evidence for any computing or data-centre project; the signed instruments behind most
signature relationships.

**Minimum implementation chosen:** a generated matrix and gap register over the existing data, two
questions (Q8, Q9) that use them, and evidence expansion only where an authoritative source closes or
narrows a gap. No change to lifecycle semantics; two type values added to the evidence schema.

**Risks of misleading interpretation, and the safeguard for each**

| Risk | Safeguard |
| --- | --- |
| A matrix reads as a complete map | Scope notice; no totals for Morocco |
| A signature reads as delivery | "Documented as: signed" plus a qualifier when the project is only announced |
| A project's status reads as progress toward a target | Stated in the matrix, Q2 and Q9 |
| A gap reads as an accusation or a proof of absence | Fixed wording ("No qualifying evidence is currently recorded in this registry."); the validator rejects "no evidence exists" |
| A gap goes stale | The build fails when new evidence concerns a gap's entities, or when its checks no longer hold |

**Acceptance criteria:** every matrix row and gap statement resolves to valid records; HTML and JSON
agree; Q1 to Q7 do not regress; all gates pass; mutation tests catch the listed regressions.

## Evidence expansion (Phase E)

| Candidate gap | Source examined | Decision |
| --- | --- | --- |
| Morocco AI 2030 progress | maroc.ma, French dispatch on the roadmap's "main advances" (9 Sept 2026) | **Admitted (MAI-EV-0040).** It gives no quantified progress towards the three targets; it lists the items presented. GAP-02 is narrowed, not resolved |
| Toubkal AI workloads | *The Journal of Supercomputing* (Springer), October 2025, open access | **Admitted (MAI-EV-0041).** Peer-reviewed; all authors affiliated with the host university, so recorded as the operator's own report. GAP-03 is narrowed, not resolved |
| Idarati AI usage | Searches for ministry or parliamentary figures | Nothing found. GAP-01 stays open |
| Nexus AI Factory construction | Press only (no construction reported) | Not admitted; the existing press record suffices. GAP-04 stays open |

Schema: source type `academic_journal` and evidence type `journal_article` were added, because a
peer-reviewed article is not a preprint. No rule changed. Registry v0.4.0, as of 19 October 2026: 41
records, 65 entities, 78 relationships. Source check on 19 October 2026: 40 of 41 matched. MAI-EV-0041
was blocked by the publisher's bot challenge and not bypassed; that is now reported as "blocked", not
as a changed source (a checker fix with its own test).

## Stage 2 — Delivered

- `/registry/matrix/` and `matrix.json`: 43 relationships among 24 organisations and initiatives.
- `/registry/gaps/` and `gaps.json`: five open gaps (GAP-01 to GAP-05). GAP-05 is computed: 19 of the
  33 relationships that assert a formal act rest only on announcements, news reports or descriptions
  (corrected in the semantic audit below; first published in this PR as 29 of 43).
- Q8 (organisations and projects) and Q9 (targets and recorded progress); Q2 reused for status
  comparison and linked to the new pages.
- The homepage infrastructure example now shows the operator's own workload report, with its limits.
- Discoverability: registry navigation, registry index, homepage access cards, methodology.

## Independent evidence and semantic audit of PR #5 (on `0d1488b`)

Requested by the owner before merge: does each new inference stay within its evidence? No new
evidence was added and no new feature built; corrections were made on the same branch.

**Findings**

| # | Severity | Finding | Correction |
| --- | --- | --- | --- |
| 1 | MAJOR | **GAP-05 measured the wrong set.** It classified all 43 matrix relationships by record type, counting declarations and public events ("presented", "launched", "organised", a programme's stated composition). For those, an official announcement is the primary record, so listing them as weakly documented was wrong | Restricted to the 33 relationships that assert a formal act (signature, creation, designation, investment, development, operation, hosting, framework listing): **19 of 33**, not 29 of 43. Declarations are marked "declaration-or-event" in `matrix.json` and carry no GAP-05 qualifier. Every count now says it describes documentation in this registry, not whether a relationship is true |
| 2 | MAJOR | **Re-assessment covered only new records.** A gap could stay stale if an assessed record was reclassified, superseded or reworded, or if a relationship, stage or attribute changed without a new record | Each gap stores a fingerprint of everything it rests on: the substance of its records, its entities' stage, attributes and status, and every relationship touching them. Any change fails the build until the gap is re-assessed (`python3 tools/registry.py --gap-fingerprints`). All four entity gaps were re-assessed and fingerprinted |
| 3 | MINOR | **MAI-EV-0041 under-stated what the paper documents.** The record supported "fine-tuning has been run", but the paper's section 5.4 names the actual runs (the GemMaroc Darija models, Belkasmi et al.) | Claim, excerpts (two added, all six matched against the retrieved page), note and Toubkal attribute now name those runs. The note states it is not evidence of the scale, share or continuity of AI use, and that the cited study has not been retrieved |
| 4 | MINOR | **GAP-03 could be read as a denial of AI use** ("No qualifying evidence…" after "independent documentation") | GAP-03 now says explicitly that it is not a finding that Toubkal is not used for AI, and names the cited GemMaroc study as the first evidence that would resolve it |
| — | OK | MAI-EV-0040 ("main advances") | Supports only "the article gives no quantified progress"; the validator now also rejects "no progress has been made" and "nothing has been built" in gap text |

**Contested claims: permitted and excluded inferences**

| Claim | Source text | Permitted inference | Not permitted | Guard |
| --- | --- | --- | --- | --- |
| Toubkal LLM fine-tuning (MAI-EV-0041) | "we present a practical benchmark demonstrating the fine-tuning of a large language model (LLM) performed on the Toubkal supercomputer by Belkasmi et al."; "both of which have been successfully run on Toubkal" | Specific fine-tuning runs (GemMaroc) were executed on Toubkal, as reported by authors affiliated with its operator | That AI is a routine, major or continuing workload; its scale or share; model quality; independent confirmation; any change to Toubkal's stage | `test_mai_ev_0041_supports_execution_not_scale_or_independence`; mutations "execution excerpt removed", "claim inflated" |
| GAP-03 | TOP500 note: "does not document current utilisation, users, or any AI workload"; the article above | Independent, quantified documentation of AI workloads is not recorded in this registry | That Toubkal is not used for AI | `test_gap_03_does_not_deny_ai_use`; mutation "non-denial clause removed" |
| GAP-05 | e.g. MAI-EV-0009, a news dispatch reporting a convention signing | 19 of 33 formal-act relationships are documented here only by announcements, news reports or descriptions; their instruments are not recorded | That these relationships are false or doubtful; that declarations or public events are weakly documented | `test_gap_05_measures_only_formal_acts_and_says_so`, `test_declarations_are_not_marked_as_weakly_documented`; mutations "counts declarations again", "caveat removed" |
| Gap re-assessment | — | A gap's text is valid for the data fingerprinted when it was assessed | That an assessment stays valid after an edited or superseded record, a new relationship, or a changed stage or attribute | Four fingerprint tests; mutation "fingerprint disabled" |
| Maroc IA 2030 progress (MAI-EV-0040, GAP-02, Q9) | "les principales avancées de la feuille de route" with the three 2030 objectives restated, no figures | The article gives no quantified progress; this registry records none | That no progress has been made; that a project's status measures progress | `test_mai_ev_0040_limits_absence_to_the_article`, `test_q9_never_shows_a_target_as_achieved` |
| "Signed" in the matrix | e.g. "signature d'une convention" | A signing is documented | That anything was implemented or delivered | `test_signed_but_undelivered_is_qualified` |

**After the audit:** 188 tests. Mutation testing: 21 of 21 caught, including 7 targeting the audit
corrections. All other gates pass. Data: 41 records, 65 entities, 78 relationships, all unchanged in
number; only MAI-EV-0041, the Toubkal attribute, and the GAP-03 and GAP-05 wording changed.
