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
| Which of those connections rest on a formal record rather than an announcement? | A | Computable from each record's `evidence_type`: 29 of 43 rest only on news reports, press releases or descriptions |
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
- `/registry/gaps/` and `gaps.json`: five open gaps (GAP-01 to GAP-05). GAP-05 is computed: 29
  relationships rest only on announcements, news reports or descriptions.
- Q8 (organisations and projects) and Q9 (targets and recorded progress); Q2 reused for status
  comparison and linked to the new pages.
- The homepage infrastructure example now shows the operator's own workload report, with its limits.
- Discoverability: registry navigation, registry index, homepage access cards, methodology.
