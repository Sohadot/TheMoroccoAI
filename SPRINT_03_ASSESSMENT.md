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
| Idarati AI (citizen assistant) | Public administration | Ministry AI Marketplace (ai.mmsp.gov.ma); idarati.ma; chatbot.idarati.ma | ADMIT WITH QUALIFICATION | Operational, on the basis of public availability on the operator's own services: listed, linked and answering a test question on 2026-10-18. Usage, accuracy, outcomes and later operation not documented; no provider established |
| Sovereign AI Marketplace | Public administration | ai.mmsp.gov.ma | ADMIT WITH QUALIFICATION | Operational digital platform; not an AI application, so it does not count as a deployment |
| DeepEcho × Ministry of Health evaluation | Health | maroc.ma, 6 May 2026 | ADMIT | Announced: convention for a progressive deployment within an evaluative study; start not documented |
| DeepEcho software (existing) | Health | FDA 510(k) database and clearance letter (K242594); maroc.ma | CORRECTED | In development → unresolved: an associated US 510(k) clearance is documented (May 2025); the developer site's disclaimer is outdated; no Moroccan use documented; the applicant's legal identity with the Moroccan company is not established |
| SWAM fraud scoring (Visa VAA) | Finance | SWAM press release on swam.ma | ADMIT | Announced ("intégrera"); integration not documented as live |
| Attijariwafa "Simple AI" | Finance | attijariwafabank.com (bot challenge, not bypassed); simple.ma (no mention) | REVIEW REQUIRED | Press reports a preview for a test community; no operator source retrieved |
| Other AI Marketplace products (Legal AI, Bulletin Officiel Search, Adala Search, Meeting Assistant, Entrepreneur AI…) | Public administration | ai.mmsp.gov.ma | REVIEW REQUIRED | Listing is availability, not documented use; not published as entities |
| OCP Maintenance Solutions predictive maintenance | Industry | Press only | REVIEW REQUIRED | No operator-issued deployment record retrieved |
| AI-assisted screening at INO Rabat | Health | None found | EXCLUDE | No primary source |
| ONCF video, AI and hypervision master plan | Transport | Press only | EXCLUDE | A tender for a study; procurement is not use |
| ONEE, ORMVA, Tanger Med, Marsa Maroc | Energy, agriculture, logistics | None found | EXCLUDE | No documented deployment found |

**Totals:** 11 candidate groups investigated; 5 admitted or corrected (2 with qualification);
3 under review; 3 excluded. **Verified operational AI applications: 1** (Idarati AI, public
availability). Verified pilots: 0. The latest supporting evidence for every admitted operational
claim is from 2026-10-18; operation after that date has not been reconfirmed.

## Correction found by re-checking existing evidence

DeepEcho's website still says its claims are "not validated yet by the FDA" (MAI-EV-0029). The FDA
database shows 510(k) clearance K242594 on 23 May 2025 (MAI-EV-0032, MAI-EV-0039), and the Moroccan
government says the solution obtained FDA "approbation" (MAI-EV-0033), which is inaccurate
terminology for a clearance. The disclaimer's quotation still matches its source, so a mechanical
check passes it. The claim it supported is nevertheless outdated: the record is now marked
`superseded_by` and can no longer set a lifecycle stage. This is the case for keeping claim review
manual.

## Source freshness check

`tools/check_sources.py` was run on 2026-10-18 against all 39 records (after the review's
corrections). All 39 sources were reached and retrieved, none redirected to another host, and every
excerpt matched (in the visible text, in the raw source where the content is embedded page data, or
in the page's own same-host script for the chatbot.idarati.ma interface). None was blocked. A
match shows the quotation is still there; it does not show the claim is still true (MAI-EV-0029 is
flagged as superseded). It is not part of CI: network
variability must not fail builds, and a failed fetch never alters a record.

## Questions the registry can now answer

From governed data on `/registry/questions/`:
- Which AI applications are deployed, who operates them (distinct from providers), on what basis,
  and how current the evidence is (Q6).
- Which projects are operational, pilot, unresolved or announced, by kind (Q2).
- Which sectors have a documented AI deployment in this registry: currently public administration
  only, with the basis stated (Q4).
- Which claims are unresolved, and which operational claims have not been reconfirmed within 12
  months (Q7). The 12-month threshold is an evidence-recency convention: it never changes a stage.

## Questions it still cannot answer

- How widely any system is used, or with what results. No usage or outcome evidence is recorded.
- Pilots: none is documented by an operator or independent source.
- Private-sector deployments in finance, industry, agriculture and energy, beyond announcements.
- Whether the press-reported Simple AI preview, or the other marketplace products, are in use.

## Practical reference value (demonstrated, not projected)

- **Institutional research:** one public-sector AI deployment, traceable to the operator's own
  services, with its limits stated; one regulatory record (FDA) associated with a Moroccan company,
  with the identity question stated rather than assumed.
- **Market intelligence and partnership discovery:** operators and providers are recorded
  separately where a source names both (SWAM/Visa; Ministry of Health/DeepEcho). Where a
  provider's role is not established (Berexia, named only in idarati.ma interface text), none is
  recorded.
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

## Independent pre-merge review (Sprint 03 review)

Reviewed head `a330505` against base `d35d0df`. Every Sprint 03 source was re-retrieved on
2026-10-18; findings, impact and corrections:

| # | Severity | Finding | Correction |
| --- | --- | --- | --- |
| 1 | MAJOR | **Berexia shown as Idarati AI's provider.** "Powered by Berexia" exists only in idarati.ma's interface text. In a browser, the portal's "Assistant Idarati" button opens chatbot.idarati.ma, which names no provider and does not display the label. Publishing a commercial role on that basis misattributes it | Provider attribute removed; Q6 shows "Not documented"; MAI-EV-0035 claim and note rewritten; regression test |
| 2 | MAJOR | **Public availability displayed as bare "Operational"** on the entity page and in the Q2 and Q4 tables, which reads as use | Wherever the stage appears, it is now labelled "Operational (public availability; use not documented)" when availability is the only basis; tests |
| 3 | MAJOR | **The service's response had not been verified.** The evidence was a page listing and interface strings, and chatbot.idarati.ma serves only a script shell | One of the assistant's own suggested questions was submitted through the public interface (no personal data); a generated answer was returned. Recorded as MAI-EV-0038. Direct API calls were refused without the interface's session proof and were not pursued. The classification stands, on stronger evidence |
| 4 | MAJOR | **FDA terminology and identity.** The registry's own relationship note called the solution "FDA-approved", and the FDA record was attached to the Moroccan company without saying that legal identity is not established | Wording corrected to clearance; FDA clearance letter and 510(k) summary added (MAI-EV-0039); verdict **qualified association**; records marked `associated_entities`; validator rejects approval wording outside quotations |
| 5 | MAJOR | **Validator gaps.** It accepted a market clearance as evidence of operation; any record as proof that an organisation operates a service (so a provider label could make an operator); usage or continuity claims in an availability observation; a superseded quotation as status; and an associated record as company origin | Five rules added; 11 attack cases now all rejected (6 were accepted before) |
| 6 | MINOR | **Recency wording read as a finding.** "Current:" and "Historical:" labels implied present or past operation; 365 days was used for "12 months"; a discontinued project would have been labelled "continued operation not documented" | Wording changed to evidence recency ("current operation has not been reconfirmed"); 12 calendar months; only operational and pilot stages; boundary tests (exact day, one day over, month-only dates, leap day, undated observations) |
| 7 | MINOR | **Source checker:** redirects not reported, declared charset ignored, duplicate requests for a shared URL, unbounded reads, HTTP errors merged with network failures, `--out` could overwrite registry data, interface strings of single-page apps unreachable | Fixed; final URL and off-host redirects reported (manual review); one request per URL per run; 25 MB cap; `http-error` state; output refused inside `data/` and `tools/`; up to 3 same-host scripts read; superseded records flagged |
| 8 | MINOR | "Only one" deployment not stated as registry coverage | Q2 now says it is the only one currently documented in this registry, not necessarily the only one in Morocco |
| 9 | MINOR | Wide tables on phones give no visible cue that they scroll sideways | Short hint on narrow screens; tables remain focusable, labelled regions that scroll by keyboard and touch; no page overflow |
| 10 | INFORMATIONAL | Whether a quotation supports a claim, and whether a self-described operator is really a vendor, remain human checks; dynamic pages change hash on every fetch; SWAM, Ministry of Health/DeepEcho and the marketplace were re-checked and need no change | Documented |

**Idarati AI.** P1 official identification as an AI assistant: yes (ministry AI Marketplace).
P2 operator: Ministry of Digital Transition, named on all three services. P3 provider: not
established. P4 public accessibility: yes, listed, linked from idarati.ma and answering on
2026-10-18. P5 use: no evidence. P6 continued operation: one observation date only.
P7 outcomes: none. Classification: operational on public availability, displayed as such. A new
lifecycle state was not needed: `status_basis` already separates availability from reported use.

**DeepEcho.** FDA K242594: applicant "DeepEcho" (Delaware address); device DEEPECHO, Class II,
pulsed Doppler imaging system, product codes IYN, IYO and QIH; "substantially equivalent", 23 May
2025. That is a 510(k) clearance for US marketing, for machine-learning detection of fetal
biometry views and measurement assistance by trained professionals. Connecting indicators: same
name and device type, the deepecho.io e-mail domain, Moroccan training and test sites (including
Casablanca), UM6P Ventures' 2023 note of an FDA submission, and the government's statement. No
source establishes legal identity with the Morocco-based company: verdict **B, qualified
association**. The Moroccan evaluation remains announced; no deployment is documented as started.

**Quality after corrections:** 39 records, 65 entities, 78 relationships; validator 0 problems;
136 tests; 18 of 18 mutations of the new rules caught; 70 generated files up to date; 69 pages
pass the site gates; deterministic under C.UTF-8 and C locales with America/Los_Angeles and
Asia/Tokyo time zones; 67 JSON-LD blocks valid; axe-core 0 violations and 0 external requests
on 9 pages at desktop and mobile widths.
