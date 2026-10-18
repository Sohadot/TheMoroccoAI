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
| Projects with a lifecycle stage | 0 | 12 (1 operational, 1 in development, 10 announced) |
| Domains with no entity | 2 | 0 |

**Corrected:** the higher-education ministry is again a *signatory* of the Nador Al Jazari
memorandum. The Sprint 01 review had downgraded it to "involved in" for lack of a source naming
the signatories; maroc.ma (MAI-EV-0019) names them.

## Questions the registry can now answer

Each answer is generated from the data on `/registry/questions/`:

1. **Organisations with documented AI activity**, with origin for companies (Moroccan, or foreign
   with a Moroccan presence).
2. **Operational versus announced projects.** One project is verified operational (Toubkal, from
   the June 2026 TOP500), one is in development (DeepEcho, by its developer's own regulatory
   disclaimer), and ten are announced.
3. **Public models and datasets** with a Morocco link: Atlas-Chat, DarijaBERT, Al-Atlas-0.5B and
   Darija-SFT-Mixture, with developer, licence and documented characteristics.
4. **Sectors with verified deployments.** The answer is currently *none*, and the page says so.
   This is a finding, not a gap in the page.
5. **Relationships by evidence strength** (42 verified fact, 21 announced plan, 2 official target,
   2 independent analysis).

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
