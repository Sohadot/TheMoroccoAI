# Sprint 03 — Deployment evidence assessment

Internal working note. It contains no valuation, buyer list, traffic or revenue figures.

## Production verification (before development)

| State | Result |
| --- | --- |
| Repository | `main` = `d35d0df` (squash merge of PR #2); tree identical to the reviewed head `9c564b2` |
| CI | "Quality gates" passed on `d35d0df` |
| Deployment | "pages build and deployment" succeeded on `d35d0df` |
| Live | 84 of 84 published files byte-identical to `main`; 64 of 64 sitemap URLs return 200; live JSON v0.2.0 (31 records, 60 entities, 67 relationships); questions page and redirects correct |

There was no production blocker.

## Coverage audit (v0.2 baseline)

| Item | Finding |
| --- | --- |
| AI applications | 0 operational, 0 pilot, 1 in development (DeepEcho software), 2 announced (Idarati AI, sovereign marketplace) |
| Infrastructure | Toubkal operational (HPC, not an AI application); Nexus announced |
| Institutes and agreements | 7, all announced |
| Sectors with no entity | Finance, agriculture, energy, logistics |
| Narrower claims possible from existing evidence | None: no existing record documented use |
| Duplicates | None (60 unique names) |

## Candidates investigated and admission decisions

| Candidate | Sector | Primary source checked | Decision | Supported stage |
| --- | --- | --- | --- | --- |
| Idarati AI (citizen assistant) | Public administration | Ministry AI Marketplace (ai.mmsp.gov.ma); idarati.ma; chatbot.idarati.ma | ADMIT WITH QUALIFICATION | Operational, on the basis of public availability on the operator's own portals (observed 2026-10-18). Usage, accuracy and outcomes not documented |
| Sovereign AI Marketplace | Public administration | ai.mmsp.gov.ma | ADMIT WITH QUALIFICATION | Operational digital platform; not an AI application, so it does not count as a deployment |
| DeepEcho × Ministry of Health evaluation | Health | maroc.ma, 6 May 2026 | ADMIT | Announced: convention for a progressive deployment within an evaluative study; start not documented |
| DeepEcho software (existing) | Health | FDA 510(k) database (K242594); maroc.ma | CORRECTED | In development → unresolved: US clearance documented (May 2025); the developer site's disclaimer is outdated; no Moroccan use documented |
| SWAM fraud scoring (Visa VAA) | Finance | SWAM press release on swam.ma | ADMIT | Announced ("intégrera"); integration not documented as live |
| Attijariwafa "Simple AI" | Finance | attijariwafabank.com (bot challenge, not bypassed); simple.ma (no mention) | REVIEW REQUIRED | Press reports a preview for a test community; no operator source retrieved |
| Other AI Marketplace products (Legal AI, Bulletin Officiel Search, Adala Search, Meeting Assistant, Entrepreneur AI…) | Public administration | ai.mmsp.gov.ma | REVIEW REQUIRED | Listing is availability, not documented use; not published as entities |
| OCP Maintenance Solutions predictive maintenance | Industry | Press only | REVIEW REQUIRED | No operator-issued deployment record retrieved |
| AI-assisted screening at INO Rabat | Health | None found | EXCLUDE | No primary source |
| ONCF video, AI and hypervision master plan | Transport | Press only | EXCLUDE | A tender for a study; procurement is not use |
| ONEE, ORMVA, Tanger Med, Marsa Maroc | Energy, agriculture, logistics | None found | EXCLUDE | No documented deployment found |

**Totals:** 11 candidate groups investigated; 5 admitted or corrected (2 with qualification);
3 under review; 3 excluded. **Verified operational AI applications: 1** (Idarati AI, public
availability). Verified pilots: 0. Every admitted operational claim is current (evidence from
2026-10-18); none is documented only historically.

## Correction found by re-checking existing evidence

DeepEcho's website still says its claims are "not validated yet by the FDA" (MAI-EV-0029). The FDA
database shows 510(k) clearance K242594 on 23 May 2025 (MAI-EV-0032), and the Moroccan government
calls the solution FDA-approved (MAI-EV-0033). The disclaimer's quotation still matches its source,
so a mechanical check passes it. The claim it supported is nevertheless outdated, and it no longer
sets a lifecycle stage. This is the case for keeping claim review manual.

## Source freshness check

`tools/check_sources.py` was run on 2026-10-18 against all 37 records. All 37 sources were
reached and retrieved, and every excerpt matched (in the visible text, or in the raw source where
the content is embedded page data). None was blocked or changed. It is not part of CI: network
variability must not fail builds, and a failed fetch never alters a record.

## Questions the registry can now answer

From governed data on `/registry/questions/`:
- Which AI applications are deployed, who operates them (distinct from providers), on what basis,
  and how current the evidence is (Q6).
- Which projects are operational, pilot, unresolved or announced, by kind (Q2).
- Which sectors have a documented AI deployment in this registry: currently public administration
  only, with the basis stated (Q4).
- Which claims are unresolved, or documented only historically (Q7).

## Questions it still cannot answer

- How widely any system is used, or with what results. No usage or outcome evidence is recorded.
- Pilots: none is documented by an operator or independent source.
- Private-sector deployments in finance, industry, agriculture and energy, beyond announcements.
- Whether the press-reported Simple AI preview, or the other marketplace products, are in use.

## Practical reference value (demonstrated, not projected)

- **Institutional research:** one public-sector AI deployment, traceable to the operator's own
  portals, with its limits stated; one regulatory record (FDA) tied to a Moroccan company.
- **Market intelligence and partnership discovery:** operators and providers are recorded
  separately (Ministry/Berexia; SWAM/Visa; Ministry of Health/DeepEcho), each with its evidence.
- **Due diligence:** the registry caught an outdated self-description that contradicted a
  regulator record. That is the kind of discrepancy diligence needs to surface.
- **Acquisition assessment:** the asset's value here lies in its method, which is enforced by
  tests: availability is never counted as usage, announcements are never counted as delivery,
  and infrastructure and platforms are never counted as AI deployments.

## Next production-adjacent action

Gather operator-issued usage evidence for the deployed public services (annual reports,
parliamentary answers, open-data dashboards) to move Idarati AI from "public availability" to
"operator's report of use". Then re-check the review-required candidates against operator
sources.
