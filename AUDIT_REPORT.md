# TheMoroccoAI — Sprint 01 Repository Audit

- **Repository:** `Sohadot/TheMoroccoAI` (public, GitHub Pages enabled)
- **Starting HEAD:** `37c2a1f2141824191a5d4ea5d90ecdf81095983a` ("Update index.html", 2026-06-05)
- **Audit date:** 2026-10-18
- **Status key:** **VERIFIED**: supported by direct repository or runtime evidence. **PARTIAL**:
  implemented but incomplete. **MISSING**: absent. **BLOCKED**: cannot be verified or done without
  information or access this sprint did not have.

Line references in Part A point to `index.html` at the starting HEAD
(`git show 37c2a1f:index.html`).

---

## Part A — Baseline (state at starting HEAD)

### A1. Repository inventory

| File | Size | Notes |
| --- | --- | --- |
| `index.html` | 30,747 B | The entire site: one page with inline CSS (L12–746) and no JavaScript. |
| `CNAME` | 16 B | `themoroccoai.com` |
| `Background.png` | 3,417,597 B (2048×2048) | **Not referenced** by the current page. Used by the pre-June page; the reference was removed in `37c2a1f`. |
| `TheMoroccoailogo.png` | 3,825,234 B (2048×2048) | **Not referenced** by any page. |

There were no other files: no README, LICENSE, robots.txt, sitemap, data files, scripts, tests,
CI workflows or `.github/` directory. The history has 11 commits, all by the owner, mostly
"Add files via upload" and "Update index.html".

### A2. Deployment (VERIFIED)

| Check | Result |
| --- | --- |
| Host | `server: GitHub.com` (GitHub Pages behind Fastly), HTTP/2 200 |
| Live vs repository | Live `https://themoroccoai.com/` is byte-identical to `index.html` at HEAD (sha256 `62dccea3…5602` for both) |
| `http://` → | 301 to `https://themoroccoai.com/` |
| `www.` → | 301 to `https://themoroccoai.com/` |
| `/robots.txt`, `/sitemap.xml`, `/favicon.ico` | 404, 404, 404 |
| `/Background.png` | 200 (published although unused) |

DNS, the registrar and Cloudflare were not inspected or modified; they are out of scope.

### A3. Advertised capabilities vs. implementation

| Capability (where the page claims it) | Status | Evidence |
| --- | --- | --- |
| "Ontology" (L931–973; acquire stat L1040) | **MISSING** as an ontology | Six glossary terms (MAI-O-001…006) in static HTML. No entities, identifiers for real-world things, relationships, provenance or machine-readable form. |
| "Landscape" (L876–928) | **PARTIAL** | Six static cards with descriptive text and status labels ("Reference Layer", "Mapping Active", "Forthcoming") not backed by any data. No sources. |
| "Strategic intelligence" (meta description L7) | **MISSING** | No data, records or analysis anywhere in the repository. |
| "Governance" (L976–1019) | **PARTIAL** | The editorial doctrine is stated, but no mechanism enforces it. Several rules were false at HEAD (rows below). |
| "All pages carry source registry and last-verified date" (L998) | **MISSING** | The page cites no source and has no source registry. |
| "No phantom URLs" (L1002) | **Contradicted** | The footer language links AR/FR/ⵜⵣⵎ/EN are `href="#"` (L1065–1068). |
| "Tier 1 sources only" (L994; status bar L820) | **MISSING** | No source of any tier is cited. |
| "Versioned updates" (L1006) | **PARTIAL** | Public Git history exists, but content is not versioned (no changelog or data versions). |
| Languages "EN · AR · FR · TZM" (status L816; acquire L1044; "multilingual parity" L1014) | **MISSING** | Only English exists. The Arabic strings are decorative labels (L785, L889 …). The other language links go nowhere. |
| "Last Updated: June 2026" (L828) | **VERIFIED** for its date | Matches the last commit (2026-06-05). |
| Acquisition contact (L1026–1031, L1052) | **PARTIAL** | `mailto:agent@sohadot.com`. `sohadot.com` has an MX record (`0 webhost.dynadot.com.`) and SPF via DNS-over-HTTPS. Mailbox delivery and monitoring are **BLOCKED**: not verifiable without sending mail, which the sprint did not do. |

### A4. Positioning and claim restraint

| Finding | Location | Assessment |
| --- | --- | --- |
| Self-description as "sovereign reference infrastructure" | L7, L779, L793, L1063 | In a Moroccan context, "sovereign" reads as state-owned or official. It undermines the independent positioning and brand independence. **Risk.** |
| No statement of independence or non-affiliation anywhere | whole page | **MISSING** |
| "the only domain that names the category … with institutional gravity" | L849 | Unverifiable superlative presented as fact. |
| "Any sovereign institution … that does not hold this asset leaves the category's reference layer in unknown hands" | L869 | Pressure framing aimed at public bodies; could read as implying government buyer interest. |
| Thesis cells (L841–870) | — | Strategic framing presented without a "framing" label, which contradicts the page's own doctrine (L1010). |
| Landscape claims with no source: "CIH Bank fintech AI adoption", "Casablanca Tech City as a continental hub", "alignment with EU AI Act as a reference model", "sovereign fund positioning" | L902, L909, L916 | Unsourced. Not carried forward. |
| No distinction between policy, research, companies, models/datasets, infrastructure, regulation and funding | — | **MISSING** |

### A5. Metadata, SEO and machine readability

| Item | Status |
| --- | --- |
| `<title>`, meta description | VERIFIED (L6–7) |
| `<html lang>` | VERIFIED (`en`, L2) |
| Canonical URL, Open Graph, Twitter card | MISSING |
| Structured data (JSON-LD) | MISSING |
| Favicon | MISSING (404) |
| robots.txt, sitemap.xml | MISSING (404) |
| Machine-readable data | MISSING |

### A6. Accessibility, mobile and performance (tests executed)

The page was rendered in Chromium (Playwright) at 1280×800 and 375×740 with reduced motion, and
scanned with axe-core 4.10.2 (rules: WCAG 2 A/AA plus best-practice).

| Result at HEAD | Desktop | Mobile |
| --- | --- | --- |
| Serious `color-contrast` failures | 43 nodes | 42 nodes |
| Serious `scrollable-region-focusable` | — | 1 (status bar) |
| Horizontal overflow | none | none |

The contrast failures were gold `#b8892a` small text on paper (2.77:1), dim white on blue
(2.6–3.0:1) and footer text on ink (1.8–2.6:1). Other findings: the inline SVG logo was not hidden
from assistive technology. Navigation links are hidden below 700px (L729) with no alternative, so
mobile users see only "Acquire". There was no `prefers-reduced-motion` handling, and the hero
content starts at `opacity: 0`.

**External dependencies:** three requests to Google Fonts (L8–10: `fonts.googleapis.com` and
`fonts.gstatic.com`). These disclose every visitor's IP address to Google, and German courts have
held that this needs consent (LG München I, 3 O 17493/20, 20 Jan 2022). There was no other
third-party code and no analytics.

### A7. Tests and checks at HEAD

No tests or CI existed. The quality gates introduced in this sprint (`tools/check_site.py`) report
**14 problems** when run against the starting tree:

```
canonical missing · og:url missing · unlabelled <svg> · no independence disclaimer ·
'Sovereign Reference Infrastructure' self-description · 3 third-party font requests ·
4 placeholder links href="#" · robots.txt missing · sitemap.xml missing
```

---

## Part B — Sprint 01 changes and resulting status

### B1. Evidence registry v0.1 — `data/evidence.json` (VERIFIED)

There are 18 records. Each source was retrieved on 2026-10-18. Every excerpt was matched against
the retrieved text by script (whitespace, quote style and PDF hyphenation normalised), except
MAI-EV-0015 (below).

| Classification | Records |
| --- | --- |
| VERIFIED FACT | 13 (one with `partial` verification: MAI-EV-0017) |
| OFFICIAL TARGET | 2 (Digital Morocco 2030 and Morocco AI 2030 targets) |
| ANNOUNCED PLAN | 2 (JAZARI twelve-region network; sovereign AI marketplace and Idarati AI) |
| UNVERIFIED CLAIM | 1 (Head of Government's investment figures: the statement is verified, the figures are not) |
| INDEPENDENT ANALYSIS | 2, on relationships (conference → Morocco AI 2030; Nador institute ↔ JAZARI network) |

**Sources used:**

- maroc.ma (national portal): 2025-07-01 conference; 2026-03-11 JAZARI Industrie X.0; 2026-07-01
  investment statement; 2026-09-09 Morocco AI 2030; 2026-10-16 new government.
- Ministry of Digital Transition, *First National AI Conference synthesis report* (PDF, Sept. 2025,
  `mmsp.gov.ma/sites/default/files/2025-09/…`).
- MAP Express (state news agency): 2024-09-25 Digital Morocco 2030 launch; 2024-06-03 AI Movement.
- CGEM: 2026-01-13 Jazari ROOT constitutive convention.
- UNESCO: 2024-07-04 AI Movement as a Category 2 Centre.
- CNDP: Law 09-08 page.

### B2. Ontology v0.1 — `data/ontology.json` (VERIFIED)

The ontology has 41 entities across 7 types (institution, initiative, event, project,
legal_instrument, technology, sector) and 7 domains matching the Phase 1 distinctions. There are 48
typed relationships over 15 predicates, each with subject and object type constraints, a
classification and cited evidence. Identifiers are stable kebab-case strings that are also the URL
slugs. `tools/registry.py` enforces referential integrity in both directions (entity ↔ record), as
well as type constraints and classification support.

Two domains, **AI companies and commercial deployments** and **models and datasets**, have **0
entities**. No record meeting the sourcing bar was produced for them this sprint, and the pages say
so instead of padding them.

### B3. Public reference experience (VERIFIED)

- `/registry/` gives an overview, an independence notice, the classification legend, domain
  coverage, all entities and data downloads. It embeds JSON-LD `Dataset`.
- `/registry/<id>/` (41 pages) shows the entity's role, a fact sheet, documented relationships with
  their classification and evidence links, full evidence cards (claim, verbatim excerpt, source,
  publication and retrieval dates, verification note) and JSON-LD.
- `/registry/evidence/` lists every record, each addressable as `#MAI-EV-NNNN`.
- On the homepage, the Landscape section is generated from the ontology (records per domain, links
  into the registry). Status figures are generated, and the thesis is labelled as framing.

**Vertical slice:** Morocco AI 2030 → JAZARI Institutes network → Institut Jazari ROOT and JAZARI
Industrie X.0 → signatories (ministries, four universities, CGEM) → technologies (AI, IoT,
robotics, industrial data analytics) → sectors. Every hop shows its evidence and classification.

### B4. Positioning and acquisition corrections

- "Sovereign" self-descriptions are replaced with "Independent". "Not affiliated with the
  Government of Morocco" appears on every page, and a gate enforces it.
- Unverifiable or pressure claims are rewritten (L849, L869), and the thesis is labelled as the
  owner's framing.
- The false capability claims are corrected: languages now read "EN · AR · FR · TZM planned", and
  the governance rules were reworded so each one is true.
- The `href="#"` language links are removed.
- The acquisition section states that the asset is privately held and not a government platform.
  It lists the transferable components, and the mailto now carries a subject line. No prices,
  valuation, buyer lists or negotiation material were added; a gate blocks pricing terms.

### B5. Privacy, accessibility and metadata

- Fonts are self-hosted: woff2 subsets of the same families, ~245 KB in total, with OFL attached.
  Pages make **0 third-party requests** (verified in Chromium).
- Contrast is fixed with an added `--gold-ink` token (`#7a5a16`, ≥4.7:1 on both paper tones) and
  raised alpha for dim text on dark grounds. The status bar is focusable, the SVG logo is hidden from
  assistive technology, reduced motion is handled, and the Registry link stays visible on mobile.
- Added canonical, Open Graph, JSON-LD, `favicon.svg`, `robots.txt`, `sitemap.xml` (44 URLs) and
  `.nojekyll`.

### B6. Quality gates and test results

| Command | Result (2026-10-18) |
| --- | --- |
| `python3 tools/registry.py` | `0 problem(s)` |
| `python3 tools/build.py --check` | `45 generated files checked, 0 stale` |
| `python3 tools/check_site.py --network` | `44 pages checked, 0 problem(s)` (includes the MX lookup for `sohadot.com`) |
| `python3 -m unittest discover -s tests -v` | `Ran 50 tests … OK` |
| axe-core 4.10.2 via Playwright: `/`, `/registry/`, `/registry/evidence/` and 4 entity pages, desktop and mobile | 0 violations on all 14 runs. 0 external requests. No horizontal overflow at 375px. |

The axe/Playwright run is a one-off audit run from a scratch environment. It is **not** part of CI,
which runs only standard-library Python. CI is defined in `.github/workflows/quality.yml` and had
not run at the time of writing.

### B7. Remaining limitations and blockers

| Item | Status | Detail |
| --- | --- | --- |
| Acquisition mailbox delivery | **BLOCKED** | The MX record resolves and the gate checks it, but no message was sent, so delivery and monitoring are unverified. The owner should send a test from an external account. |
| mmsp.gov.ma news pages | **BLOCKED** | They return HTTP 403 ("Accès refusé") to the verification environment, so the ministry's own press releases could not be cited. The ministry PDF did download. |
| JAZARI approval decisions in the Bulletin Officiel | **BLOCKED** | Not located. Press reports (TelQuel) mention an August 2026 publication; BO n° 7522 was checked and does not contain them. |
| Law 09-08 promulgation references | **BLOCKED** | The official full-text hosts (sgg.gov.ma, adala.justice.gov.ma) were unreachable or returned 404, so MAI-EV-0017 is `partial` and has no publication date. |
| UNESCO page | PARTIAL | A bot challenge blocks command-line retrieval; it was read through a web-fetch tool. |
| New AI ministry (16 Oct 2026) | PARTIAL | The appointment is verified. Its attributions, and any succession from the Ministry of Digital Transition, are not, and the registry states this. |
| Companies, models and datasets domains | MISSING | Shown as empty. |
| Arabic, French and Tamazight editions | MISSING | Marked "planned" everywhere. |
| Data and content licence | MISSING | An owner decision. It matters for transferability and reuse. |
| `Background.png`, `TheMoroccoailogo.png` (7.2 MB, unused) | Unchanged | Left in place as owner assets. Recommend moving them to a brand-assets location or deleting them, and generating a 1200×630 social image from the logo. |
| Source link rot | Open | Records keep verbatim excerpts, but no archive snapshots (e.g. the Wayback Machine) are stored yet. |
