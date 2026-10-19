# Sprint 03.5 — Institutional credibility and reference-first positioning

Internal working note. It contains no valuation, buyer list, traffic or revenue figures.
Baseline: `main` = `391006a` (Sprint 03 merge), verified byte-for-byte against production.

## Phase 1 — Claim audit (before editing)

Classes: **F** verified factual statement · **C** supported description of an existing capability ·
**S** owner's strategic interpretation · **A** future ambition · **P** commercial proposition.

| # | Location | Claim (abridged) | Class | Finding | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | Hero `<h1>` | "The intelligence of a civilization entering AI." | S | The site's main heading is strategic framing, so the first thing a visitor reads is the owner's interpretation, not what the site provides | `<h1>` now describes the registry; the line moves to the labelled thesis |
| 2 | Hero label | "MAI-ROOT-001 — Category Anchor" | S/P | A commercial self-classification presented as a status label | "Independent evidence registry" |
| 3 | Hero paragraph | "civilizational node — four languages, three continents, millennia of knowledge translation" | S | Interpretation in the reference voice | Moved to the thesis, labelled as the owner's view |
| 4 | Hero paragraph | "independent … every reference claim is tied to its source" | C | Supported by the validator and the published records | Kept |
| 5 | Status bar | "Asset ID", "Category: AI Reference Infrastructure" | S/P | Commercial labels in a bar that looks like data | Replaced by generated coverage figures |
| 6 | Status bar, acquisition block, footer | "EN · AR · FR · TZM planned" | F (ambiguous) | Reads as Arabic and French being live; only English is published | "English · Arabic, French, Tamazight planned" |
| 7 | Status bar; acquisition block | "Evidence Registry v0.1"; "Registry v0.1" | F (**inaccurate**) | The data is v0.3.0 | Version generated from `evidence.json` |
| 8 | Ontology intro | "The operational ontology has seven entity types" | F (**inaccurate**) | It has 10 entity types | Generated from `ontology.json` |
| 9 | Status bar; governance; registry index | "Source requirement: primary & institutional"; "every reference claim … tied to a verifiable institutional, governmental or academic source" | F (**inaccurate**) | 6 records cite organisation websites, 4 technical repositories, 1 an investor publication, 1 an independent list and 1 secondary press | Reworded: every claim cites a source whose type is labelled; primary sources preferred; press only for plans or unverified claims |
| 10 | Thesis heading | "Why this asset is inevitable." | S | Inevitability stated as a heading, although the intro labels the section as framing | "The owner's thesis"; framing label kept and strengthened |
| 11 | Thesis MAI-T-002 | "cannot be recreated, only acquired or conceded" | S/P | Category-scarcity and acquisition framing | Kept inside the labelled thesis, attributed to the owner |
| 12 | Thesis MAI-T-004 | "the scarcest digital asset class" | S | Interpretation | Kept, attributed to the owner |
| 13 | Thesis MAI-T-006 | "Buyer logic" | P | Commercial proposition on the reference homepage | Moved to `/acquisition/` |
| 14 | Ontology section | "The language this asset defines"; Civilizational Node, Sovereign Reference, Category Anchor… | S | Owner's framing vocabulary shown beside the published ontology, so it can be mistaken for it | Moved into the thesis as "framing vocabulary", stated not to be part of `/data/ontology.json` |
| 15 | Governance rules | "Versioned data with a public change history" | C | Supported: the repository is public and every version is a commit | Kept; now links to a public changelog |
| 16 | Governance rules | "No phantom URLs" | C | Supported by the site gates (link and sitemap checks) | Kept |
| 17 | Acquisition section | "This asset is acquirable."; "Asset class: Category Anchor Domain"; "Buyer type" | P | A full-width sales block is the homepage's closing section, and "Acquire" is a button on every page | Moved to `/acquisition/`; the homepage keeps a short, discreet section; the navigation shows a plain "Acquisition" link |
| 18 | Landscape heading | "The nodes of Morocco's AI ecosystem." | F (overreach) | Implies completeness | "What the registry covers so far", with a coverage limitation |
| 19 | Thesis MAI-T-005 | "A reference layer has to exist before the market matures." | S | Interpretation | Kept, attributed to the owner |
| 20 | Title and meta description | "Morocco AI Reference Infrastructure" | C | Acceptable but generic | "Independent evidence registry for Morocco's AI ecosystem" |

No evidence classification, record or relationship needed to change: every inaccuracy was in
presentation, not in the registry data.

## Phase 2 — Homepage information architecture

| Before | After |
| --- | --- |
| 1 Hero: civilizational framing | 1 Hero: independent evidence registry, unmistakable non-affiliation notice |
| 2 Status bar: asset ID, category, v0.1 (stale) | 2 Current coverage: generated version, counts and date; coverage by domain |
| 3 Thesis ("inevitable") | 3 Access: registry, questions, evidence, JSON datasets, methodology |
| 4 Landscape | 4 Three questions answered from the evidence (generated) |
| 5 Ontology vocabulary | 5 Methodology and limitations |
| 6 Governance | 6 The owner's strategic thesis (labelled; includes the framing vocabulary) |
| 7 Acquisition (full sales block) | 7 Acquisition: one short paragraph and a link to `/acquisition/` |

## Phase 3 — Three questions answered from the evidence

Selected after checking the data. Each is generated at build time from `evidence.json` and
`ontology.json` and links to its supporting registry output:

| Question | What the data supports | Links |
| --- | --- | --- |
| What is the documented status of Idarati AI? | Operational on public availability only; operator named; basis and latest evidence date; no usage, accuracy or outcome evidence | Entity page, Q6, MAI-EV-0034/0035/0038 |
| What has Morocco AI 2030 set as targets, and what is verified so far? | The official 2030 targets (MAD 100 billion, 50,000 jobs, 200,000 talents) shown as targets; the two projects it is recorded as including, with their stages; its verified link to the JAZARI network | Entity page, MAI-EV-0011, Q2 |
| Which institutions are documented as connected to AI compute and data-centre infrastructure? | Toubkal (operational compute, hosted by UM6P); Nexus AI Factory and two data-centre agreements, signed or announced only, with no record of anything built | Entity pages, Q5, Q2 |

No ranking, national total or completeness claim is made.

## Phases 4 to 6 — Thesis, acquisition page, transparency

- **Thesis:** all six propositions are kept, under "The owner's strategic thesis", with the label
  "Framing, not findings". Each cell is marked as the owner's view, an ambition or an intended role.
  The founding line ("The intelligence of a civilization entering AI.") is kept as an attributed
  quotation. The framing vocabulary is moved into the thesis and stated not to be part of the
  ontology. The buyer logic is moved to the acquisition page.
- **`/acquisition/`:** transferable assets (counts generated from the data); a table separating what
  exists today from the owner's view of potential, marked "not established"; ownership and
  non-affiliation; no price, traffic or revenue figures and no implied interest; confidential
  enquiries to agent@sohadot.com. The homepage keeps a short `#acquire` note, and every page links
  to the acquisition page from its navigation and footer.
- **`/methodology/`:** what the registry documents (figures generated from the data), what it does not
  establish, how evidence is admitted, how unsupported, conflicting and outdated claims are handled,
  how corrections are made, and the data-licence status. It ends with a changelog built from
  `data/changelog.json`, where each entry links to its commit on the public repository. The dates,
  counts and corrections in each entry were checked against `git show` at that commit.

## Phase 7 — Quality

- Registry validation: 0 problems. `evidence.json` and `ontology.json` are unchanged.
- Site checks: 71 pages, 0 problems. The contact gate now also requires the acquisition page and a
  homepage link to it; the homepage requirement is kept.
- 151 tests (15 new; plus 2 new gate cases). 13 of 13 mutations caught: framing leaking into the hero,
  a hand-written stale version, a lost acquisition link, a lost framing label or non-affiliation
  notice, returning sales language, homepage counts drifting from the data, a lost availability
  qualifier or evidence links, a lost contact, a button-styled "Acquire" link, unmarked potential,
  and a changelog out of step with the data.
- Deterministic across locales and time zones (72 generated files); 67 JSON-LD blocks valid;
  71 sitemap URLs with matching canonical URLs.
- axe-core: 0 violations and 0 external requests on 9 pages at desktop and mobile widths, with no
  horizontal overflow. Mobile fixes: the navigation gap, and framing definitions (with their caveats)
  now shown on phones instead of hidden.

## Remaining risks

- The thesis keeps ambitious language (civilizational framing, category scarcity). It is labelled
  and attributed, but a reader quoting a single sentence out of context could still misread it.
- The changelog is maintained by hand. A test checks that the latest entry matches the data;
  descriptions of past corrections depend on review.
- No content or data licence is declared, which limits reuse by institutions. The decision is the
  owner's.
- The three example answers depend on specific entity ids (`idarati-ai`, `morocco-ai-2030`). Removing
  or renaming one fails the build loudly; it cannot publish a silently wrong answer.
