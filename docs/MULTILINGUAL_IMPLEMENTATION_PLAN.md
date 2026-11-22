# Multilingual Implementation Plan

Status: **Accepted (TMA-DEC-007, 2026-11-22).** Owner decisions Q1–Q9 are recorded in the ADR. **Progress:** Sprint 19B-1 added the foundation (part of B1, and B4). Sprint 19B-2 added the rendering engine, publication gates, multilingual SEO, logical/RTL CSS and the language switcher (B3, B7 and the remaining B4 gates; Arch §14). Sprint 19B-3 extracted all presentation text of `/registry/` and `/methodology/` (byte-identical English; Arch §15). Sprint 19B-4 generated the homepage from a catalog-driven template (B2), gave changelog and attribute texts stable identities, and adopted TMA-DEC-008: one documented human approval per translation, with risk-based escalation (Arch §16, [TRANSLATION_REVIEW_POLICY.md](TRANSLATION_REVIEW_POLICY.md)). No page is registered for localization yet, no translation exists and no localized page is published. Its design is in [MULTILINGUAL_ARCHITECTURE.md](MULTILINGUAL_ARCHITECTURE.md) (cited below as "Arch §n"), and the decision is in [ADR_MULTILINGUAL_REFERENCE.md](ADR_MULTILINGUAL_REFERENCE.md). Approval questions are numbered as in the ADR (Q1–Q9).

## Sequencing rules for every sprint

These apply to every sprint below:
- English output is never changed as a side effect. Each refactoring step proves `build.py --check` reports 0 stale against the previous English output before any translation work lands.
- A sprint ends with its own pull request, green CI, and a decision by the Sohadot integration authority. Nothing is merged by an agent.
- No language becomes `published` in `i18n/languages.json` until its first page set passes every gate (Arch §9) and its human approvals are recorded (TMA-DEC-008; Arch §16).

---

## Sprint 19B — Core bilingual rollout (Arabic, French)

**Goal:** reviewed Arabic and French versions of three core pages: the homepage, `/methodology/` and `/registry/`. `/acquisition/` is not part of this rollout: it follows the core reference pages and needs a dedicated substantive and legal review of its commercial wording (Q2).

**Split:**
- 19B-1: foundation (done).
- 19B-2: rendering engine and gates (done).
- 19B-3: `/registry/` and `/methodology/` bodies into the catalogs (done; neither registered as localizable).
- 19B-4: homepage templating (B2), stable changelog and attribute identity, TMA-DEC-008 approval contract (done; nothing registered as localizable).
- Then B5, B6 and B8.

### Steps

| # | Step | Proof that English is unchanged |
|---|---|---|
| B1 | Extract interface and page strings from `tools/build.py` into `i18n/en/messages.json`. Add `t()`, `c()` and `fmt()`. Replace `human_date()` with explicit month tables (English output identical). **19B-1 done:** shell, footer, ownership statement and dates, with `t()` and catalog-based `human_date()`. **Remaining (19B-2):** page-body prose, label maps, `c()` and localized `fmt()` | `build.py --check`: 0 stale; full test suite unchanged |
| B2 | Make the homepage renderable per language. Move its inline CSS to `assets/home.css`, and its hand-written text into `i18n/en/messages.json` under a homepage template rendered by `build.py`. **19B-4 done:** `tools/templates/homepage.tmpl` and `render_homepage()`; the CSS stays inline in the template so that `index.html` remains byte-identical (moving it is a separate, visual-only change) | Text of every element identical (DOM text diff); screenshots at 1440 and 390 px identical; existing homepage tests pass unchanged |
| B3 | Convert physical CSS properties to logical ones (Arch §8.1). Add Arabic typography rules. Reference the Arabic face from `registry.css`. **19B-2 done:** rules scoped to `html[lang="ar"]`, 28 English screenshots pixel-identical | LTR screenshot comparison unchanged at 1440 and 390 px |
| B4 | Add the language registry, glossary schema, `validate_i18n` and the new `check_site` gates, each with negative fixture tests (Arch §9). **19B-1 done** for the catalog-level rules and the route and `hreflang` gates (Arch §13). **Remaining:** the page-pair parity gates (identifiers, citations, classifications, dates, numbers, qualifiers, English leakage, localized disclosures, bidi isolation, RTL layout), which need a localized renderer | New gates pass vacuously with no published language |
| B5 | Glossary: settle Arabic and French terms for the reference vocabulary (Arch §4.5), including forbidden variants. Settle the Arabic month-name and numeral conventions | Glossary review recorded |
| B6 | Translate and review the units for the B-wave pages, including localized `OWNER_NOTE`, `DISCLAIMER`, `OWNERSHIP_STATEMENT` and the authority notice | One human approval recorded per unit (TMA-DEC-008), escalated where a criterion applies |
| B7 | Language switcher, `hreflang` clusters, self canonicals, `og:locale`, sitemap entries and JSON-LD `inLanguage` / `translationOfWork` for the generated pages. **19B-2 done** as infrastructure; it takes effect only when a page is generated | English pages gain `hreflang` only where a translation is published |
| B8 | Update the homepage and footer statements ("AR, FR, TZM planned") to say exactly what is published, in the same pull request that publishes | Tests pin the statement to `languages.json` |

### Dependencies
- Owner decisions Q2, Q3, Q5 and Q9 (recorded 2026-11-22). Arabic pages begin with the existing Noto Kufi Arabic font; another face is added only on a demonstrated readability need (Q5).
- Available reviewers: at least one registered human reviewer per language (TMA-DEC-008); a second registered reviewer for escalations.

### Acceptance criteria
- `/ar/`, `/ar/methodology/`, `/ar/registry/`, `/fr/`, `/fr/methodology/` and `/fr/registry/` are generated, and nothing else under `/ar/` or `/fr/`.
- Each page meets all of the following:
  - Self canonical.
  - Reciprocal `hreflang` across en/ar/fr, with `x-default` pointing to English.
  - Correct `lang`/`dir`.
  - Present in the sitemap.
  - Localized disclosures and the authority notice present.
  - Identifier, number, date, classification and qualifier parity with English.
- `/ar/methodology/#ownership-h` exists, and localized footers link to it.
- Links from localized pages to untranslated pages go to English and are marked "(in English)". `/evaluation/` is linked this way and is not translated.
- No English page changes, apart from the added `hreflang` / `x-default` links and the language switcher on the three pages that now have translations.
- All existing gates pass, plus the new ones. CI passes.

### Main risks

| Risk | Mitigation |
|---|---|
| B1/B2 refactor silently changes English text | Byte-identical `--check` and DOM-text diff gates. Separate PRs for B1, B2 and B3 |
| RTL layout breaks on mobile | B3 screenshot comparisons. `test_layout` extended to an `/ar/` page |
| Terminology drift in early translations | Glossary approved before B6 begins |
| Reviewer capacity | Small page set. If reviewers are unavailable, the sprint ends after B4 with nothing published |

---

## Sprint 19C — Reference coverage expansion (Arabic, French)

**Goal:** extend the same system to entity pages, `/registry/evidence/`, `/registry/questions/`, `/registry/gaps/` and `/registry/matrix/`, using `i18n/<lang>/content.json`. No canonical data is duplicated.

### Steps
1. Generate the content work list for the eligible pages:
   - entity summaries and notes;
   - evidence titles, claims and verification notes;
   - relationship notes;
   - gap prose.

   This is about 13,400 English words in total.
2. Add approved `name` units for entities, using official Arabic names cited to a source where possible (`name_basis`, Arch §4.3).
3. Translate and review in batches by page group, with entity pages first. A page publishes when its own units are complete. There is no all-or-nothing language switch.
4. Add page-pair parity checks for evidence cards: classification codes, `<time>` values, source URLs and qualifier presence.

### Acceptance criteria
- Every published localized page meets the 19B criteria and the evidence-card parity checks.
- No `source_excerpts` are translated (Q6: not in the first two waves). Excerpts are shown verbatim with `lang`/`dir`.
- The translation impact report runs in CI. A data pull request that would withdraw localized pages lists them.
- `/registry/state/` and `/data/` stay English only (Arch §10).

### Dependencies
- 19B merged and reviewed in production (Sprint 19E checks for the 19B pages).
- Reviewer capacity matching the volume.

### Main risks

| Risk | Mitigation |
|---|---|
| English data changes faster than review, so pages churn in and out | Batch data releases. Update translations in the same PR. Impact report before merge |
| Name translations presented as official | `name_basis` required. Only `official` names may be presented as official, with a source |
| Qualifiers lost in fluent translation | Qualifiers are separate `qualifier` units, and their presence is machine-checked. The human reviewer focuses on them, helped by semantic-risk warnings |

---

## Sprint 19D — Additional language support (Darija, Amazigh)

**Goal:** introduce `ary` (Arabic script) and `zgh` (Tifinagh) only when the prerequisites below are met (Q1, Q7). Spanish remains a possible later language without a publication commitment.

### Prerequisites
- The language set is settled: TMA-DEC-007 refines TMA-DEC-003 (Q1).
- For each language:
  - the script (decided: Arabic script for Darija, Tifinagh for Amazigh) and the language tag;
  - a glossary covering the reference vocabulary;
  - a named review capacity.
- For `zgh`: a bundled, OFL-licensed Tifinagh font subset (Arch §8.7), verified on Android, iOS, macOS and Windows.
- A check of current search-engine guidance on `hreflang` for ISO 639-3 codes (`ary`, `zgh`), which have no ISO 639-1 equivalent.
  - The HTML `lang` attribute is valid either way.
  - Whether a given search engine honours these `hreflang` values must be checked, not assumed.

### Acceptance criteria
The same as 19B for the chosen pages. In addition:
- **Script rendering:** checked on real devices for Tifinagh.
- **Terminology and register:** for Darija, documented in the glossary.

### Main risks
- **No standardised written register for Darija:** this causes terminology instability. Mitigation: the glossary and a single editor for wave 1.
- **Tifinagh rendering gaps on some platforms:** mitigation: a bundled font plus device testing.
- **Search-engine support for these language codes:** unverified. Mitigation: verify before publishing and report the result.

---

## Sprint 19E — Production validation

Run after each publishing sprint (19B, 19C, 19D).

### Checks
- **Production parity:** live `/<lang>/` files are byte-identical to `main`, using the same method as the post-deployment audit for PR #16.
- **Routes:** every generated route returns 200. Unpublished language routes still return 404, and no placeholder pages exist.
- **Metadata:** canonical, `hreflang` reciprocity, `x-default`, sitemap entries, `lang`/`dir` and `og:locale` are correct on live pages.
- **Browser:** desktop and mobile in LTR and RTL. Keyboard and visible focus on the language switcher. No overflow, no console errors, only same-origin requests. Correct Arabic shaping: no letter-spacing on Arabic text.
- **Disclosures:** present on every live localized page, and the authority notice links to the English equivalent.
- **Indexing readiness:** a technical review only. Webmaster tools may be used (Q8); connecting an account, verifying ownership or changing DNS is a separately authorized operation. Observe coverage reports afterwards. No ranking or traffic claims.

### Acceptance criteria
Every check passes, or the failing ones are reported with severity. Live pages match `main`.

---

## Risk register (cross-sprint)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | A translation changes a claim's meaning | Medium | High | Placeholders, parity gates and qualifier units. Semantic-risk warnings. One documented human approval, escalated to a second reviewer where a criterion applies (TMA-DEC-008). English prevails, and the notice on every page says so |
| R2 | Unreviewed text reaches production | Low | High | Drafts never on `main`. The build renders only approved and fresh units. CI gates |
| R3 | English releases blocked by translation lag | Low | High | Staleness withdraws localized pages and never blocks English |
| R4 | Localized pages go stale and drop out often | Medium | Medium | Impact report. Translations updated in the same PR. Batched data releases |
| R5 | Duplicate-content or wrong-canonical SEO problems | Low | Medium | Self canonicals, reciprocal `hreflang`, no placeholders, the 100% rule |
| R6 | RTL or bidi rendering defects (IDs, URLs, mixed scripts) | Medium | Medium | Logical CSS, `<bdi>`, isolation check, RTL layout test |
| R7 | Reviewer identity exposure | Low | Medium | Pseudonymous reviewer IDs (Q3) |
| R8 | Public statements ("AR, FR, TZM planned") drift from reality | Medium | Low | Statements generated from `languages.json` and pinned by tests (B8) |
| R9 | Evaluation comparability lost through translation | n/a while English-only | High | Evaluation stays English until a separate neutrality review and a spec change |
| R10 | Translation layer mistaken for research data by consumers | Low | Medium | Catalogs kept outside `data/` and out of the manifest. Registry version unaffected |
