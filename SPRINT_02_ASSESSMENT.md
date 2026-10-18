# Sprint 02 — Strategic value assessment

Internal working note. It contains no valuation, buyer list or negotiation material.

## Baseline (main `6bc8d9a`, 2026-10-18)

Production was healthy: all 68 published files matched `main`, and every gate and test passed.
Coverage was 18 records and 41 entities, with **0 entities** in two domains: *AI companies and
commercial deployments* and *models and datasets*. There was no lifecycle status, so the registry
could not distinguish a signed agreement from a running system.

## What changed

| | Before | After |
| --- | --- | --- |
| Evidence records | 18 | 31 |
| Entities | 41 | 60 (4 companies, 3 models, 1 dataset, 3 new institutions) |
| Relationships | 48 | 67 |
| Projects with a lifecycle stage | 0 | 12 (1 operational compute infrastructure, 1 AI application in development, 10 announced) |
| Domains with no entity | 2 | 0 |

**Corrected:** the higher-education ministry is again a *signatory* of the Nador Al Jazari
memorandum. The Sprint 01 review had downgraded it to "involved in" for lack of a source naming
the signatories; maroc.ma (MAI-EV-0019) names them.

## Questions the registry can now answer

Each answer is generated from the data on `/registry/questions/`:

1. **Organisations with documented AI activity**, with origin for companies (Moroccan, or foreign
   with a Moroccan presence).
2. **Operational versus announced projects, by kind.** The only operational project is compute
   infrastructure (Toubkal, from the June 2026 TOP500). It is not an AI application, and no AI
   workload on it is documented. One AI application is in development (DeepEcho, by its
   developer's own disclaimer), and ten projects are announced. No AI application is yet documented
   as operational or in pilot in this registry.
3. **Public models and datasets** with a documented connection to Morocco: Atlas-Chat, DarijaBERT,
   Al-Atlas-0.5B and Darija-SFT-Mixture. For most, the connection is the language (Darija), not a
   Moroccan developer, and the page says which.
4. **Sectors with verified deployments.** No qualifying deployment has yet been documented in this
   registry. That reflects its coverage, not the state of AI use in Morocco.
5. **Relationships by evidence strength** (41 verified fact, 21 announced plan, 2 official target,
   3 independent analysis).

## Who this serves (demonstrated, not projected)

- **Researchers** get a citable list of Darija models and datasets, each tied to its repository
  and paper, and the developer is named. Atlas-Chat, for example, is developed by a Paris lab, not
  a Moroccan institution.
- **Investors and companies** get a status-aware view: which AI infrastructure exists
  (Toubkal) and which is planned (Nexus AI Factory, the JAZARI institutes), plus who created and
  funded DeepEcho.
- **Institutional users** get the signatories of the 2025–2026 AI agreements, with the source for
  each name.

## Why it is hard to replace

The utility comes from the method more than the volume:
- Every claim quotes its source and carries a retrieval date.
- Lifecycle stages are enforced by rules. "Operational" cannot rest on an announcement, a
  company's own website or the press.
- Self-promotional statements ("first", benchmark wins, accuracy figures) are systematically
  excluded.
- The data is published as JSON, under stable identifiers.

A list of names is easy to copy. A maintained record of which claims are verified, by which
source, as of when, is not. That depends on continued maintenance.

## Remaining gaps

- Only four companies. AI adoption by large Moroccan firms (telecoms, banks, OCP) is not
  recorded, because no primary source was retrieved this sprint.
- No pilot deployments in public services, and no sector with a verified operational deployment.
- Gated Hugging Face datasets (e.g. DODa, Atlaset) and other AtlasIA models were not inspected.
- The Nexus AI Factory rests on secondary press. The ministry's own release (mmsp.gov.ma) is
  blocked from the verification environment.
- Hugging Face repository dates are creation dates, not release announcements.
- The validator checks structure and consistency, not whether a claim's wording is entailed by its
  excerpt; that still needs human review.

## Recommended next production improvement

**Deployment evidence in public services and regulated sectors** (health, administration,
finance), sourced from operators' own documentation or regulators. That is the empty answer to Q4
and the question an institutional user or acquirer will ask first. Second: an automated
source-freshness check (re-fetch each URL and re-match each excerpt), so records do not silently go
stale.

## Pre-merge review (PR #2, reviewed head `4851cef`)

The review re-fetched all 13 new sources (all HTTP 200), re-matched all 45 excerpts with a newly
written checker, and confirmed that all four models and datasets download without authentication.
It also probed the validator adversarially.

| # | Severity | Finding | Correction |
| --- | --- | --- | --- |
| 1 | MAJOR | The validator accepted "operational" or "pilot" on any VERIFIED FACT record from a non-self source, including a convention signature. Jazari ROOT, the Nador institute, Industrie X.0 and the DeepEcho software could all be marked operational or pilot from signature or investor records. The published data was correct, but the advertised safeguard did not hold. | Records now declare `status_evidence`; any stage beyond `announced` needs a matching record. 4 exploit cases are regression tests, plus mutation-checked. |
| 2 | MAJOR | Toubkal, HPC infrastructure, appeared as the operational project on the questions page with no distinction from AI applications. MAI-EV-0020's note claimed a 2026 Linpack run, but the Rmax value is unchanged since June 2021. | `project_kind` added; Q2 shows the kind and states that no AI application is documented as operational; Q4 counts only AI applications; Toubkal wording and note corrected. |
| 3 | MAJOR | The `aiox-labs develops darijabert` relationship was a VERIFIED FACT, but the card names "AIOX Lab"; equating it with AIOX Labs is a name-based inference. | Reclassified as INDEPENDENT ANALYSIS with a note. AIOX Labs no longer appears as a verified developer. |
| 4 | MINOR | Company origins were coarse. AIOX Labs ("roots in Morocco", a self-description) and Nexus (subsidiary reported only by press) were labelled like independently confirmed origins. UM6P Ventures' origin cited a record with no excerpt about its location. | Origin values refined; independent origins now need an independent source (tested); UM6P Ventures set to `unresolved`. |
| 5 | MINOR | Q4 said "No sector yet has…", which reads as a statement about Morocco. Q1 asked about AI activity "in Morocco" while listing a Paris lab. Q3 said "verified link to Morocco" where the link is mostly the language. | Answers scoped to the registry. A "Connection to Morocco" column was added, backed by cited attributes. |
| 6 | MINOR | Entity wording overstated: "operate a Moroccan subsidiary" (Nexus); "Morocco-based" stated as fact (DeepEcho, UM6P Ventures); Atlas-Chat's developer mixed with its Morocco link. | Reworded to what the sources state. |
| 7 | INFO | No registration, headquarters, regulatory clearance or deployment is verified for any company or product; the DeepEcho software is recorded as in development only. | Disclosed in notes and status fields. |
