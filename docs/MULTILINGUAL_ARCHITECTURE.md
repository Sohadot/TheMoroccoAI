# Multilingual Reference Architecture

Status: **Accepted (TMA-DEC-007, 2026-11-22).** The design was proposed in Sprint 19A and accepted with the owner decisions Q1–Q9 recorded in [ADR_MULTILINGUAL_REFERENCE.md](ADR_MULTILINGUAL_REFERENCE.md). **Implementation:** the Sprint 19B-1 foundation (section 13), the Sprint 19B-2 rendering engine (section 14) and the Sprint 19B-3 extraction of `/registry/` and `/methodology/` (section 15) exist; no page is registered for localization yet. No translation has been drafted or reviewed, and no localized page or route is published. Section 1 is the Sprint 19A inventory at `728d475`, kept as recorded. The phased plan is in [MULTILINGUAL_IMPLEMENTATION_PLAN.md](MULTILINGUAL_IMPLEMENTATION_PLAN.md).

Governing policy: [TMA-DEC-003](DECISION_LOG.md) (accepted) says:
- English is the authoritative project language.
- French and Arabic are secondary localization priorities.
- Original-language excerpts stay intact, and translations are distinguished from quotations.
- Terminology is canonical, `hreflang` is correct, and incomplete translations are not indexed.

This architecture implements that policy. It does not reopen it. Section 12 lists where the Sprint 19A brief goes beyond TMA-DEC-003.

---

## 1. Verified current state (baseline `728d475`)

Verified on 2026-11-22 against `origin/main` = `728d475e4a3a73526be08defe279ea64e67b4bfb` ("Homepage: add independent evaluation invitation (#18)", parent `a32303a`). Nothing has been committed after it. Its tree is identical to the reviewed PR #18 head `09b8425`.

### 1.1 Serving

- **Hosting:** GitHub Pages serves the root of `main` as static files. `.nojekyll` is present and `CNAME` is `themoroccoai.com`. Cloudflare fronts Pages, and HTML is `cf-cache-status: DYNAMIC`.
- **Missing routes:** these return the GitHub Pages default 404, because the repository has no `404.html`. On 2026-11-22, `/ar/` and `/fr/` returned 404, with transient 503s on first requests (cause unverified).
- **Public files:** every file in the repository is publicly fetchable at its path, including `docs/`, `tools/` and `data/`. Anything committed to `main` is therefore published, whether or not it is linked.
- **No server logic:** there are no redirects, content negotiation or rewrites. Routing equals directory layout.

### 1.2 What is generated and what is hand-maintained

| Output | Produced by | Notes |
|---|---|---|
| 65 entity pages `registry/<id>/` | `tools/build.py` `render_entity` | One per ontology entity |
| `registry/`, `registry/evidence/`, `registry/questions/`, `registry/matrix/`, `registry/gaps/`, `registry/state/` | `tools/build.py` | `state/` is linted against `reference-state.json` by `state_page_errors` |
| `data/`, `methodology/`, `acquisition/` | `tools/build.py` | |
| `sitemap.xml` | `tools/build.py` `sitemap()` | Hard-coded list plus entity pages |
| `registry/matrix/matrix.json`, `registry/gaps/gaps.json`, `registry/reference-state.json`, `data/manifest.json` | `tools/build.py` | Machine-readable. Identifiers and enumerations only, in English |
| `index.html` | **Hand-maintained.** About 1,100 visible words written by hand, plus `<!--r:…-->` blocks injected by `build.py` | About 840 lines of CSS inline in `<style>` |
| `evaluation/index.html`, `assets/evaluation.js` | **Hand-maintained** | `noindex, follow`, excluded from the sitemap. 23 English task and status strings in JS. The footer must equal `build.footer()` (tested) |
| `robots.txt` | Hand-maintained | `Allow: /` and the sitemap |

`build.py --check` covers 80 generated files.

### 1.3 Canonical data (research authority)

- **`data/evidence.json`:** 63 records. Each has `source_language`: 28 `fr`, 28 `en`, 7 `ar`. `source_excerpts` (3,532 words) are verbatim in the source language. `build.py:230-231` renders non-English excerpts with `lang`, and Arabic ones with `dir="rtl"`.
- **`data/ontology.json`:** 65 entities.
  - `alt_names`: 31 entities have them, all Latin script (French official names and acronyms). **No entity has an Arabic name.**
  - `domain_labels_ar`: Arabic labels for the 7 domains. These are already in the canonical file and are shown on the homepage (`build.py:2141`). They predate this design. The design leaves them in place (see 4.4).
- **`data/gaps.json`:** 7 gaps, with English assessment prose.
- **Hash binding:** `registry/reference-state.json` embeds the SHA-256 of the three canonical inputs (`REFERENCE_INPUTS`, `build.py:1056`). `data/manifest.json` lists the published JSON with hashes. `examples/registry_consumer.py` re-verifies both.

**Consequence: any translation stored inside a canonical file changes its hash, the reference snapshot and the manifest. Consumers would see a data change where there is none. Translations must therefore live outside `data/`.**

### 1.4 English-only assumptions in code and gates

- **`build.py` page shell:** hard-codes `<html lang="en" dir="ltr">` (`build.py:185`). The navigation, breadcrumbs, footer and `OWNERSHIP_STATEMENT` are English literals.
- **Prose in `build.py`:** roughly 250 inline HTML prose fragments and about 190 quoted prose literals (heuristic count) across about 2,350 lines.
- **Label maps:** `TYPE_LABELS`, `TYPE_SINGULAR`, `LIFECYCLE_LABELS`, `ORIGIN_LABELS`, `KIND_LABELS`, `KIND_COUNT_LABELS`, `SOURCE_TYPE_LABELS` (13), `STATUS_BASIS_LABELS`, `DOCUMENTED_AS`, `DIMENSION_LABELS`, `KIND_PHRASES`, plus qualifier sentences such as `AVAILABILITY_SUFFIX`, `PLAN_NOT_DELIVERED` and `SIGNED_NOT_DELIVERED`.
- **Dates:** `human_date()` (`build.py:105`) uses `strftime("%B")`, which depends on the process locale. It cannot be reused for French or Arabic and must not be made locale-sensitive.
- **Site checks (`tools/check_site.py`):**
  - `DISCLAIMER`, `OWNER_NOTE` and `OWNERSHIP_STATEMENT` are English constants required on pages.
  - `FORBIDDEN_PAGE_TEXT` patterns are English only.
  - The `<html lang>` check only tests presence. There is no `hreflang`, `dir` or `og:locale` check.
- **`state_page_errors` and `STATE_FORBIDDEN`:** they reject judgment words and numbers in static text, and both are English regexes.
- **Tests:** about 160 `assertIn` checks across 8 test files pin English prose of four or more words. They protect English wording and stay valid for English pages. They do not cover any other language.
- **Structured data:** JSON-LD (`WebSite`, `Organization`, `Dataset`) has no `inLanguage`. There is no `og:locale`.

### 1.5 Fonts and scripts (assets/fonts, glyph coverage checked with fontTools)

| Font | Covers | Missing |
|---|---|---|
| Cormorant Garamond (roman, italic), DM Mono 300/400/500 | Latin, all French accents and `œ`, `« »` | U+202F (narrow no-break space, French typographic convention) |
| Noto Kufi Arabic (variable 300–600, 1,336 glyphs, 124 KB) | Arabic letters, Arabic-Indic digits U+0660–0669, `، ؛ ؟`, ZWNJ/ZWJ | n/a |
| none | n/a | **Tifinagh (U+2D30–2D7F): no bundled font.** The footer's `ⵜⵣⵎ` already depends on the visitor's system fonts |

- **Where the Arabic font is used:** Noto Kufi Arabic is referenced only by the homepage's inline CSS (`.hero-arabic`, `.node-ar`). `assets/registry.css` never names it, so the 7 Arabic evidence excerpts on generated pages render in a system fallback font. This is a pre-existing observation and is not changed here.
- **Direction-specific CSS:** there are 28 physical left/right declarations (`registry.css` 12, `evaluation.css` 2, homepage 14) against 1 logical one. Only `.evidence-quote[dir="rtl"]` has direction-specific CSS.
- **Arabic shaping:** DM Mono labels use `letter-spacing` of 0.06–0.2em and `text-transform: uppercase`. Letter-spacing breaks Arabic cursive joining, so these rules must not apply to Arabic text.

### 1.6 Existing multilingual signals

- **Homepage statements:** the homepage says "English · AR, FR, TZM planned" and "Only the English edition is published; the others are planned". The footer reads `EN · AR · FR · ⵜⵣⵎ planned`. These are public commitments and must stay true at each stage.
- **Evaluation:** `docs/EVALUATION_SPEC.md` fixes the evaluation language as "English (authoritative)".

---

## 2. Principles

1. **One research source.** Evidence, ontology, gaps, changelog and reference state exist once, in English, in `data/`. No language has its own records, entities, classifications, gaps or conclusions.
2. **Translation is representation, not research.** A translation may only re-express content that exists in English. If it adds, drops, softens or strengthens a claim, a qualifier, a number, a date or a classification, it is wrong. English prevails in any discrepancy.
3. **Derived, deterministic output.** Localized pages come from the same render functions and the same data, plus an approved translation catalog. The same inputs produce the same bytes, and `build.py --check` covers every language.
4. **Publish only what is complete, reviewed and current.** A localized page is generated only when every unit it needs is approved and fresh. Missing translations never fall back to English text inside a localized page.
5. **English never waits for translation.** A stale or missing translation withdraws the localized page. It never blocks or alters an English release.
6. **No runtime machinery.** No language detection, redirects, cookies or JavaScript switching, and no third-party requests or fonts.

---

## 3. Two authorities

| | Research authority | Translation authority |
|---|---|---|
| What | Canonical evidence, ontology, gaps, changelog, methodology rules, English page text | Reviewed linguistic representations of that content |
| Where | `data/*.json`, English strings in `tools/build.py` and `index.html` | `i18n/<lang>/*.json`, `i18n/glossary.json` |
| Changed by | Evidence and editorial process (existing validator and tests) | Translation lifecycle (section 6) |
| Can change meaning? | Yes; this is the reference | **Never.** Only form changes, in the target language |
| Versioned by | Registry version, `data/changelog.json` | Per-unit `source_sha256` and review record. Registry version is unaffected |

---

## 4. Source-to-translation data model

### 4.1 Layout

```
i18n/
  languages.json            # language registry: code, script, dir, native name, state
  glossary.json             # controlled terminology across languages
  en/messages.json          # English interface and page strings, extracted from build.py/index.html (authoritative)
  ar/messages.json          # translations of en/messages.json units
  ar/content.json           # translations of canonical prose fields, keyed by record/entity/gap id and field
  fr/messages.json
  fr/content.json
```

- **Why outside `data/`:** this keeps catalogs out of `REFERENCE_INPUTS`, the manifest and the consumer contract.
- **Publicity:** the catalogs are public files (section 1.1). Only approved units are committed to `main` (section 6.3).

### 4.2 Language registry (`i18n/languages.json`)

```json
{"languages": [
  {"code": "en", "bcp47": "en", "script": "Latn", "dir": "ltr", "native_name": "English", "state": "authoritative", "route": "/"},
  {"code": "ar", "bcp47": "ar", "script": "Arab", "dir": "rtl", "native_name": "العربية",  "state": "in-preparation", "route": "/ar/"},
  {"code": "fr", "bcp47": "fr", "script": "Latn", "dir": "ltr", "native_name": "Français", "state": "in-preparation", "route": "/fr/"}
]}
```

- **States:** `authoritative` (English only), `in-preparation` (nothing is generated), `published` (eligible pages are generated) and `withdrawn`.
- **Later waves:** `ary` (Arabic script) and `zgh` (Tifinagh) are added only in Sprint 19D, once their terminology, fonts and review capacity exist (Q7).

### 4.3 Translation unit

Both catalogs share one unit shape:

```json
{
  "id": "methodology.limits.intro",
  "source_sha256": "9f2c…",
  "text": "…",
  "status": "approved",
  "kind": "prose",
  "review": {
    "drafted_by": "translator-ar-01",
    "draft_method": "machine-assisted",
    "substantive_reviewer": "reviewer-sub-01",
    "linguistic_reviewer": "reviewer-ar-02",
    "approved_on": "2026-12-05",
    "glossary_version": "2026-12-01"
  }
}
```

**Fields**

| Field | Meaning |
|---|---|
| `id` | A stable message identifier. In `messages.json` it is assigned at extraction. In `content.json` it is `<file>:<record-or-entity-or-gap id>:<field>`, for example `evidence:MAI-EV-0011:claim` or `ontology:um6p:summary`. |
| `source_sha256` | The hash of the NFC-normalized English source text at the time of translation. A mismatch with the current English means the unit is **stale** (section 7). |
| `kind` | One of: `interface` (navigation, labels); `prose` (page text); `qualifier` (sentences that limit a claim, such as `PLAN_NOT_DELIVERED`, `AVAILABILITY_SUFFIX` or the recency notice); `disclosure` (ownership, independence, authority notice); `term` (glossary-bound labels); `name` (localized entity display name). |
| `name_basis` | Only on `name` units: `official` (with `name_source_url` and the retrieval date), `established-usage`, `transliteration` or `translation`. |
| `status` | `draft`, `terminology-checked`, `parity-reviewed`, `linguistically-reviewed`, `approved` or `stale`. Only `approved` with a matching hash is renderable. |
| `review` | Pseudonymous identifiers only (Q3), such as `reviewer-ar-02`; no other fields are allowed, so no personal data reaches a public file (TMA-DEC-006). `draft_method` is `human` or `machine-assisted` (Q9). Required on approved units. |

**Placeholders.** Numbers, dates, identifiers, URLs, entity links and counts are never literal in translatable text. They are named placeholders filled by the generator from canonical data, for example `"{count} evidence records, as of {date}"`. This makes number and identifier parity checkable by machine (section 9).

### 4.4 What is never translated

| Value | Rule |
|---|---|
| Evidence IDs (`MAI-EV-…`), entity IDs, gap IDs, page codes (`MAI-METHOD`, …) | Identical in all languages. Rendered left-to-right and isolated (section 8) |
| Source URLs, `source_organization`, source titles as cited | Unchanged. An organisation may be *glossed* by an approved `name` unit, never replaced |
| `source_excerpts` | Always verbatim, in the source language, with `lang` and `dir`. Not translated in the first two waves, and a translation is never presented as an original quotation (Q6) |
| Classification codes (`VERIFIED FACT`, `OFFICIAL TARGET`, `ANNOUNCED PLAN`, `UNVERIFIED CLAIM`, `INDEPENDENT ANALYSIS`) | Shown as the glossary-approved localized label **followed by the canonical code**, so a citation can be matched across languages. CSS class and `data-` values stay the canonical slug |
| Numbers, dates, years, counts, version numbers | Filled from data. The language changes only the presentation (section 5.7) |
| JSON outputs (`matrix.json`, `gaps.json`, `reference-state.json`, `manifest.json`) | Not localized and not duplicated per language |
| `domain_labels_ar` in `ontology.json` | Left unchanged (canonical data is not modified). The Arabic glossary uses it as seed values, subject to linguistic review. Any divergence is recorded in the glossary, and the canonical field is never rewritten from the translation layer |

### 4.5 Glossary (`i18n/glossary.json`)

```json
{"version": "2026-12-01", "terms": [
  {"id": "classification.verified-fact", "en": "VERIFIED FACT",
   "ar": {"label": "…", "status": "approved", "forbidden": ["…"]},
   "fr": {"label": "…", "status": "approved", "forbidden": ["…"]},
   "note": "Means: verified against the cited source. Must not be rendered as 'officially confirmed'."}
]}
```

**Scope.** The terms are those the reference depends on:
- 5 classifications and 2 verification statuses;
- 10 entity types and 7 lifecycle stages;
- 5 project kinds and 5 origins;
- 7 domains and 20 predicates;
- 13 source types and 4 status bases;
- the "documented as" and gap-dimension labels;
- the qualifier vocabulary ("announced", "target", "not verified as delivered", "public availability; use not documented", "not reconfirmed in 12 months");
- the independence and ownership vocabulary.

**Forbidden variants.** Each term lists forbidden variants: renderings that would strengthen or weaken meaning, or imply official status. One example would be an Arabic or French rendering of "independent registry" that reads as "official registry". `check_site` rejects forbidden variants on pages in that language.

**Who sets the target terms.** Linguistic and substantive reviewers set the target-language terms in Sprint 19B. This design deliberately proposes none.

### 4.6 How a localized page is produced

`build.py` iterates `languages.json` in a fixed order. For each `published` language, it renders every **eligible** page (section 5.2) through the same render functions, with:
- a message lookup `t(lang, id, **placeholders)`;
- a content lookup `c(lang, file, key, field)`;
- a locale formatter `fmt(lang, value)`.

For English, `t` and `c` return the English source. **Sprint 19B's first step is this extraction, with byte-identical English output** (proved by `build.py --check` reporting 0 stale before any translation exists).

---

## 5. URL, routing and SEO design

### 5.1 Routes: assessment of the proposed structure

| Language | Route | Assessment |
|---|---|---|
| English | `/` (unchanged) | Keeps every existing URL, canonical and backlink. No `/en/` prefix, because a prefix would need redirects that static Pages cannot serve |
| Arabic | `/ar/…` | Fits static Pages: a directory tree mirroring English paths, for example `/ar/registry/um6p/` |
| French | `/fr/…` | Same |
| Darija | `/ary/…` | Valid BCP 47 code. Deferred to Sprint 19D (Q7) |
| Amazigh | `/zgh/…` | Valid BCP 47 code. Deferred to Sprint 19D (Q7) |

**Verdict:** the structure is appropriate for this hosting model.
- **No collisions:** no top-level path or entity ID collides with these prefixes. The validator should reserve them.
- **Path mirroring:** each language mirrors the English path exactly, so equivalence is computable: `/ar` + English path.
- **No placeholders:** no route is generated until the page is published in that language. Unpublished routes keep returning 404.

### 5.2 Page eligibility per language

A page `P` is generated in language `L` only if all of the following hold:
1. `L` is `published` in `languages.json`.
2. `P` is in `L`'s eligible page set (the wave plan).
3. Every message and content unit that `P` renders exists for `L`, with `status: approved` and `source_sha256` equal to the current English hash.
4. The page-level parity checks pass (section 9).

If any condition fails, `P` is not generated in `L`. A page is never generated partly translated or with English fallback text, apart from the allowed untranslated values in 4.4.

### 5.3 Canonical, `hreflang`, `x-default`

- **Canonical:** each published page has a **self-referencing** canonical, for example `https://themoroccoai.com/ar/methodology/`. A translation is never canonicalized to English.
- **`hreflang` cluster:** this is the set of languages in which `P` is actually generated. If it has two or more members, every member carries `<link rel="alternate" hreflang="…" href="…">` for every member, itself included, plus `hreflang="x-default"` pointing to the **English** URL. If only English exists, no alternates are emitted, so the current English pages are byte-identical.
- **Reciprocity:** reciprocity is guaranteed by construction, because all members are rendered from the same cluster list. It is also verified by a check.
- **Withdrawn pages:** a withdrawn or stale page disappears from every other member's cluster in the same build.

### 5.4 Sitemap

`sitemap()` becomes data-driven: every generated, indexable page in every published language is listed. The existing `check_sitemap` already enforces "every indexable page listed, no `noindex` page listed, no listed URL without a file". It therefore covers localized pages without changes.

Alternates are declared in page `<head>` only. A sitemap `xhtml:link` mirror is optional and not proposed, because two sources of `hreflang` truth would need to be kept consistent.

### 5.5 Language switcher

- **Form:** a list of plain `<a>` links in the header. Each label is in its own language and script ("English", "العربية", "Français"), with `lang` and `hreflang` on each link and `aria-current="page"` on the current one. A visible text label carries the accessible name, not a flag.
- **Contents:** it lists only languages in which the current page's equivalent is generated. It never links to an unpublished route.
- **No automatic behaviour:** no redirect, cookie, `Accept-Language` sniffing or JavaScript.

### 5.6 Internal links, breadcrumbs, fallback

- **Internal links:** links inside a localized page go to the same-language equivalent when it is generated. Otherwise they go to the English page, with a visible localized marker such as "(in English)" and `hreflang="en"` on the link.
- **Breadcrumbs:** localized through `messages.json`. Their targets follow the same rule as other links.
- **Authority notice:** every localized page carries a `disclosure` unit stating that it is a translation of the English reference and that English prevails, with a link to the English equivalent.
- **Ownership and independence:** every localized page carries the approved translations of `OWNER_NOTE`, `DISCLAIMER` and, on pages listed in `OWNERSHIP_PAGES`, `OWNERSHIP_STATEMENT`. The localized footer links to `/<lang>/methodology/#ownership-h` once that page is published, and to the English section until then.

### 5.7 Language-specific presentation

- **`<html>` attributes:** `<html lang="ar" dir="rtl">` and `<html lang="fr" dir="ltr">`.
- **`og:locale`:** a language-region value such as `ar_MA` or `fr_MA`, with `og:locale:alternate` only for published members. `og:locale` uses the `_MA` region because the intended audience is Moroccan. `hreflang` stays language-only (`ar`, `fr`), because the content is not region-specific.
- **Dates:** explicit month tables per language in the generator, never `strftime` or locale settings. Every displayed date is wrapped in `<time datetime="YYYY-MM-DD">`. Arabic month names follow the convention chosen by the linguistic reviewers. Moroccan usage (يناير … ماي … يوليوز، غشت، شتنبر، نونبر، دجنبر) is the proposed default, to be confirmed in the glossary.
- **Numerals:** Western digits (0–9) in all languages, consistent with common Moroccan usage. This keeps numbers byte-identical across languages so they can be machine-checked. Arabic-Indic digits are rejected by a check unless policy changes.
- **French typography:** a no-break space before `; : ! ?` and inside `« »`. Use U+00A0, or extend the Latin font subset to U+202F in Sprint 19B.

### 5.8 Structured data

- **Language fields:** localized JSON-LD adds `inLanguage`. It adds `translationOfWork` (schema.org) pointing to the English URL, and the English page adds `workTranslation` only when a published translation exists.
- **Names:** `name` uses the approved localized name. `alternateName` keeps the English name and the canonical `alt_names`.
- **No new facts:** no new types or properties beyond what the English page already asserts.

### 5.9 Search discoverability without changing meaning

- **Titles and descriptions:** these are `prose` units, reviewed like any other text. They should read naturally in the target language rather than word for word. They must state nothing the English page does not.
- **Entity names:** Arabic searchers will look for institutions by their Arabic names, and many Moroccan searches mix French institutional names into Arabic queries.
  - Approved `name` units (official names cited to a source where possible) give Arabic pages the Arabic name.
  - The canonical French `alt_names` stay visible on Arabic pages as alternate names.
  - Transliterations are labelled `name_basis: transliteration`. They are never presented as official names.
- **Anchor text:** internal anchor text is localized through the same catalog.
- **Thin pages:** these are prevented by the 100% rule in 5.2. There is no page whose only localized part is the template.
- **No unsupported claims:** no keyword targeting may introduce a claim, and no search-volume or ranking claims are made. Readiness is verified technically in Sprint 19E. Indexing is observed afterwards, with webmaster tools if the owner chooses to enable them (Q8).

---

## 6. Translation lifecycle

```
source identified → drafted → terminology checked → substantive parity reviewed → linguistically reviewed → approved → published
                                                                                                 ↘ (English source changes) → stale → re-review
```

| Step | Who / what | Recorded as |
|---|---|---|
| Source identified | Build tool lists units required by the eligible pages, with current `source_sha256` | Work list (generated, not committed) |
| Drafted | Translator; machine translation may prepare drafts of already-public content, never replacing the reviews (Q9) | `drafted_by`, `draft_method` |
| Terminology checked | Automated glossary check, plus the translator | `glossary_version` |
| Substantive parity reviewed | A reviewer who reads English and the target language confirms that claims, qualifiers, numbers, dates and classifications are preserved | `substantive_reviewer` |
| Linguistically reviewed | A native or professional reviewer, distinct from the drafter | `linguistic_reviewer` |
| Approved | Both reviews recorded, all checks pass | `status: approved`, `approved_on` |
| Published | The Sohadot integration authority merges the PR. The build generates the page | Generated output under `/<lang>/` |

### 6.1 Separation of duties
The drafter cannot be either reviewer (enforced by `tools/i18n.py`). Two different reviewers are preferred; one person may perform both functions only if they did not draft the text (Q3).

### 6.2 What machines can and cannot establish
The automated checks in section 9 establish structural parity: identifiers, placeholders, numbers, dates, classifications, citations, qualifiers present, links, metadata and disclosures. **They cannot establish semantic equivalence.** Publication therefore always requires the two human reviews. A passing build is a necessary condition for publication, never a sufficient one.

### 6.3 Drafts and `main`
Because every file on `main` is publicly served (1.1), drafts stay on translation branches and in pull requests. `main` receives only units with `status: approved`. The build also refuses to render anything that is not approved and fresh, as a second safeguard. An unreviewed unit therefore cannot enter the public build silently.

---

## 7. Staleness strategy

- **Detection:** at build time, `build.py` recomputes the English source hash of every unit. If the stored `source_sha256` differs, the unit is stale.
- **Effect:** any page that needs a stale unit becomes ineligible (5.2). It is not generated, it leaves the sitemap and every `hreflang` cluster, and its route returns 404 again.
- **English is never blocked:** the English build is unaffected.
- **Visibility:**
  - `build.py --check` prints a **translation impact report**: the units made stale and the localized pages withdrawn.
  - A pull request that changes English text or data must show this report in CI output.
  - The integration authority sees the withdrawals before merging and can choose to update the translations in the same pull request.
- **Strictness by kind:** `prose`, `qualifier`, `disclosure`, `term` and content units have no grace period. Interface units have none either: there is no grace period for any kind (Q4).

---

## 8. Right-to-left, bidirectional text and scripts

1. **Logical CSS:** before any RTL page ships, convert the 28 physical left/right declarations to logical properties (`margin-inline-start`, `border-inline-start`, `inset-inline-*`, `text-align: start/end`), and mirror the gold rule borders and arrows. Verify that English (LTR) rendering is unchanged with screenshot comparisons at 1440 px and 390 px.
2. **Isolation of LTR tokens in RTL text:** evidence IDs, entity IDs, URLs, version strings, code and Latin proper names inside Arabic text are rendered as `<bdi>` or `<span dir="ltr">`. This is checked by a rule: on every `dir="rtl"` page, each `MAI-EV-\d{4}`, `http…` and `MAI-…` token must sit inside an isolating element.
3. **No bidi control characters in catalogs:** reject U+202A–U+202E and U+2066–U+2069 in translation text, and use markup instead. This also guards against bidirectional-override spoofing. Zero-width characters are rejected except ZWNJ/ZWJ where the glossary permits them.
4. **Unicode normalization:** all catalog text must be NFC, and the build rejects non-NFC text. Source hashes are computed on NFC text.
5. **Arabic typography:**
   - `:lang(ar)` sets `letter-spacing: 0` and `text-transform: none`, never italic, and a font stack that starts with the bundled Arabic face.
   - DM Mono has no Arabic glyphs, so Arabic labels need the Arabic face.
   - Noto Kufi Arabic covers the needed characters (1.5). Arabic pages begin with this font; another self-hosted face is added only if testing shows a genuine readability need (Q5).
6. **Mixed content:** Arabic paragraphs that quote French or English official names use `lang` on the inner span, so that screen readers switch voice and the browser picks the right font.
7. **Tifinagh (Sprint 19D):** this needs a bundled, OFL-licensed Tifinagh font subset covering at least U+2D30–U+2D67, U+2D6F and U+2D7F. Tifinagh is written left to right. It cannot reuse the Arabic font, and none of the current fonts covers it. Script choice and language tagging (`zgh` / `zgh-Tfng`) are decided in Sprint 19D.
8. **No new external requests:** all fonts are self-hosted subsets, as now.

---

## 9. Tests and quality gates

The existing English checks and their assertions stay unchanged. The new checks run for every published language:

| Check | Where | What fails |
|---|---|---|
| Catalog schema | `tools/registry.py` (new `validate_i18n`) | Unknown status or kind; missing provenance on approved units; non-NFC text; bidi controls; duplicate IDs |
| Staleness | `build.py` | Approved unit with `source_sha256` ≠ current English hash. The page is withdrawn and listed in the impact report |
| Placeholder parity | `validate_i18n` | Translation's `{placeholder}` set ≠ English set |
| Digit parity | `validate_i18n` | A digit sequence in the translation that does not occur in the English source. Arabic-Indic digits |
| Glossary | `validate_i18n`, `check_site` | Approved term not used where its message is used; forbidden variant present |
| Identifier and citation parity | `check_site` (page pairs) | Set of `MAI-EV-*` IDs, entity links and source URLs on `/<lang>/P` ≠ the English `P` |
| Classification parity | `check_site` | Sequence of canonical classification codes or `data-` values per evidence card differs from English |
| Date and number parity | `check_site` | Set of `<time datetime>` values or of `<data value>` values differs from English |
| Qualifier presence | `check_site` | A `qualifier` unit rendered on English `P` has no rendered counterpart on `/<lang>/P` |
| No English leakage | `check_site` | English catalog strings found on a localized page outside the allowed values (4.4) |
| Disclosures | `check_site` | Missing localized `OWNER_NOTE`, `DISCLAIMER`, authority notice, or `OWNERSHIP_STATEMENT` on `OWNERSHIP_PAGES` |
| Language metadata | `check_site` | `<html lang/dir>` wrong for the route; canonical not self; `hreflang` not reciprocal, pointing to an unpublished page, or missing `x-default` to English; `og:locale` wrong |
| Sitemap | existing `check_sitemap` | Unchanged rules, now covering localized pages |
| Forbidden wording | `check_site` | Per-language official-status and pricing patterns, equivalent to `FORBIDDEN_PAGE_TEXT` |
| Bidi isolation | `check_site` | A non-isolated Latin token in RTL text (section 8.2) |
| Links | existing `check_site` | Broken localized links or anchors |
| Layout | `tests/test_layout.py` extended | Overflow on narrow screens for one page per published language, including RTL |
| Evaluation boundary | `tests/test_site.py` | Any `/<lang>/evaluation/` route generated before it is approved (section 10) |

Each new gate gets a negative fixture test, following the existing `GatesCatchRegressions` pattern.

---

## 10. Page eligibility by wave (summary)

| Page | Wave | Reason |
|---|---|---|
| Homepage | 19B | Entry point. Its hand-written text must first move into the catalog (plan, step B2) |
| `/methodology/` | 19B | Holds `#ownership-h`, the limits and the classification definitions, which localized pages must be able to link to |
| `/registry/` (index) | 19B | Navigation hub. It renders entity names and labels only |
| `/acquisition/` | After the core reference pages | May be localized after the core pages, with a dedicated substantive and legal review of its commercial wording before publication (Q2) |
| Entity pages, `/registry/evidence/`, `/registry/questions/`, `/registry/gaps/`, `/registry/matrix/` | 19C | Need the content catalog (about 13,400 words of canonical prose) and per-page parity |
| `/registry/state/` | After 19C, possibly never | Its linter forbids numbers and judgment words in static text. A translated page would need a per-language linter that preserves those guarantees |
| `/data/` | Not planned | Developer documentation for English-keyed JSON. Low search value. Reversible |
| `/evaluation/` | **English only until separately approved** | Task wording must stay neutral (EVALUATION_SPEC), and responses must stay comparable. A translation needs its own neutrality review and an update to EVALUATION_SPEC. Localized pages link to it with an "(in English)" marker |
| JSON outputs | Never | Machine-readable and language-neutral by design |

---

## 11. Security and privacy

- **Nothing new at runtime:** no scripts, cookies, storage, redirects or third-party requests. Fonts stay self-hosted.
- **Bidirectional spoofing:** prevented by the bidi-control ban and the NFC requirement (8.3–8.4).
- **Reviewer privacy:** reviewers are identified pseudonymously by default (TMA-DEC-006 forbids personal data in the public repository).
- **Machine-translation services:** if used as a drafting aid, they receive only public content. No credentials are stored in the repository.
- **Drafts:** never committed to `main` (6.3).

---

## 12. Owner decisions

The points Sprint 19A found outside existing policy were resolved by the owner on 2026-11-22 (Q1–Q9 in the [ADR](ADR_MULTILINGUAL_REFERENCE.md); TMA-DEC-007 in the [decision log](DECISION_LOG.md)). TMA-DEC-007 refines the language set of TMA-DEC-003: Darija and Standard Moroccan Amazigh are future priorities, and Spanish is a possible later language without commitment.

## 13. Implemented foundation (Sprint 19B-1)

| Part | What exists |
|---|---|
| `i18n/languages.json` | `en` (authoritative, `/`), `ar` and `fr` (`in-preparation`). Nothing is generated for a language that is not published, and `tools/i18n.py` refuses `published` until a renderer exists (`RENDERING_LANGUAGES` is empty) |
| `i18n/en/messages.json` | 35 English source strings: page shell (skip link, navigation), footer (tagline, owner note, disclaimer, version, date, link labels), the canonical ownership statement, and date formats and month names |
| `i18n/ar/`, `i18n/fr/` | Empty `messages.json` and `content.json`: no translation unit is recorded before it is drafted and reviewed |
| `i18n/glossary.json` | Schema and version only; no term labels yet |
| `tools/i18n.py` | Fingerprints (SHA-256 of NFC English source); source resolution for messages and canonical fields (`evidence`, `ontology`, `gaps`); validation; stale and orphan report; `renderable_units` and `page_eligibility` |
| `tools/build.py` | Reads the shell, footer, ownership statement and dates from the English catalog. `human_date` no longer uses `strftime`. Output byte-identical (80 generated files) |
| `tools/registry.py` | Runs the i18n validation, so CI covers it without a workflow change. Stale and orphaned units are reported, never errors |
| `tools/check_site.py` | Fails a route directory for an unpublished or reserved language (`ar`, `fr`, `ary`, `zgh`, `es`), and `hreflang` to an unpublished language or a missing page |
| `tests/test_i18n.py` | Positive fixtures and a negative test for every rule |

**Validation rules** (`tools/i18n.py`):
- **Language registry:** codes, BCP 47 tags, scripts, direction, state, routes, a single authoritative English entry, no `published` without a renderer, no unregistered language directory.
- **English catalog:** message ids, duplicates, kinds, text hygiene.
- **Translation units:**
  - valid and committable status (approved only, since drafts stay off `main`), no duplicate ids, valid kind and `name_basis`;
  - a source reference that resolves, and a source fingerprint;
  - NFC text, with no bidirectional controls, invisible characters or markup;
  - placeholders, digits (Western digits only, none added) and identifiers/URLs identical to the English source;
  - review record complete, pseudonymous, independent of the drafter, dated, with no extra fields;
  - no forbidden glossary variant.
- **Glossary:** terms name canonical vocabulary, labels approved, no label containing its own forbidden variant.

**Never an error:** stale units (English source changed) and orphaned units (source removed) are reported and are never renderable, so English releases never wait for translation (Q4).

**Not established by validation:** semantic equivalence. Only the two recorded human reviews can establish it.

**Deferred extraction:** page-body prose in `build.py`, the hand-maintained homepage (inline CSS, about 1,100 words), the evaluation page (English only, TMA-DEC-002), the state page (English-specific linter), and the label maps that belong to the glossary. Each needs its own output-parity proof. The page-body extraction moves to Sprint 19B-3 (section 14).

## 14. Rendering engine and publication gates (Sprint 19B-2)

The generator can now render a page in `ar` or `fr` (`RENDERING_LANGUAGES`). Rendering is not publication. A page is generated in a language only if all of the following hold:
- the language is `published` in `i18n/languages.json`;
- the page is registered in `LOCALIZABLE_PAGES`;
- every gate below passes.

None of these holds today, so **no localized file is generated, listed or linked**. The English output is byte-identical, and `assets/registry.css` changed with no visible effect: 28 full-page screenshots at 1440 and 390 px are pixel-identical to `main`.

| Part | Implementation (`tools/build.py`, `tools/i18n.py`) |
|---|---|
| Render context | `RenderContext` (language, strict `Translator`, `hreflang` clusters, language registry) and `rendering()`. English is the default context, and every shell helper reads it |
| Text | `msg()` escapes catalog text. `msg_html()` fills `{name}` placeholders with generator-built HTML (links, isolated identifiers), so catalog text never holds markup. `human_date()` uses the context's month names. `Translator.term()` returns glossary-approved labels |
| Strictness | `i18n.Translator` reads only *renderable* units: approved, current fingerprint, complete and independent review, text and parity rules passed. A missing unit or term raises `Untranslated`, so the page is not generated. There is no English fallback |
| Routes | `route()` and `output_path()` mirror English paths under `/ar/` and `/fr/`. `local_href()` and `link()` point internal links to the same-language page when it is generated, and otherwise to English with `hreflang="en"` and a visible "(in English)" marker |
| Page shell | `<html lang dir>` comes from the registry. The canonical is self-referencing. A translation notice (English prevails, linked) appears on localized pages. The language switcher (`language_switcher()`) is plain links in native names, with `lang`, `dir`, `hreflang` and `aria-current`, and is shown only when the page exists in two or more languages |
| SEO | Reciprocal `hreflang` covers only generated equivalents, plus `x-default` pointing to English. `og:locale` and `og:locale:alternate` come from `og_locale` in the registry. JSON-LD gets `inLanguage`, with `translationOfWork` on localized pages and `workTranslation` on English. Sitemap entries come from the clusters. All of this is absent while no translation is generated |
| Eligibility (`localize()`) | Pass 1 renders each registered page per publishable language and runs the gates against the English rendering of the same path. Pass 2 renders the eligible pages with the final clusters. English pages are then rendered with those clusters |
| Page gates (`localized_page_errors`) | Correct `lang`/`dir`; self canonical; localized title and description. Identical to English: evidence and entity identifiers, source URLs, digits (numbers and dates), classification codes, and the set of rendered messages (so qualifiers are present). Localized owner note, disclaimer and translation notice present, plus the ownership statement where English has it. Identifiers, URLs and versions isolated in right-to-left text. No untranslated English text of three or more words |
| Site gates | `cluster_errors()` in the build, and `check_site` independently: reciprocity, self-inclusion, `x-default` to English, no unpublished or missing targets, correct `lang`/`dir` under a published language route |
| Withdrawal | `withdrawn_files()`: a file under `/ar/`, `/fr/`, `/ary/`, `/zgh/` or `/es/` that the build did not generate is deleted by `build.py` and reported as stale by `build.py --check`. A withdrawn or stale translation therefore cannot stay publicly served |
| CSS | `registry.css` now uses logical properties only. Arabic documents (`html[lang="ar"]`) start with the bundled Noto Kufi Arabic, with no letter-spacing, no italics and a longer line height. English pages, including their Arabic excerpts, are unaffected |

**Synthetic fixtures only.** `tests/test_multilingual.py` exercises all of the above with a test-only page and mechanically generated placeholder text in temporary directories. These are not translations and are never committed.

**Sprint 19B-3 (next):**
- extract the `/registry/` and `/methodology/` bodies into the catalogs, including content units for vocabulary definitions and domain labels;
- register those pages in `LOCALIZABLE_PAGES`;
- prove English parity again.

**Sprint 19B-4:** homepage templating.

**Typography to review with real Arabic text (Q5):** Latin runs inside Arabic pages currently fall back to DM Mono.

## 15. Extracted reference pages (Sprint 19B-3)

All presentation text of `/registry/` and `/methodology/` now comes from `i18n/en/messages.json`: 134 new units, plus 23 reused shell, footer, ownership-statement and date units. The per-unit inventory is in [MULTILINGUAL_CONTENT_INVENTORY.md](MULTILINGUAL_CONTENT_INVENTORY.md). Both pages, and every other generated file, are **byte-identical** to the previous output. The old and new renderers were also compared on deliberately altered data, so that every conditional branch was exercised. Neither page is registered for localization.

| Part | Implementation |
|---|---|
| Rich text | Links, emphasis and identifiers are `{name}` placeholders filled by the generator (`msg_html`). Catalog text cannot hold markup, and a brace outside a valid placeholder is rejected as a malformed rich-text token |
| Canonical text | Entity names and statuses, classification definitions and domain labels are **content units** resolved from `data/`: `ontology:<id>:name`, `ontology:<id>:status`, `classification:<code>:definition` and `domain:<key>:label`. They are never copied into the catalog. Identifiers inside them are isolated in right-to-left text (`content()`) |
| Terminology | The entity-type and source-type labels moved from `build.py` into `vocab.*` messages. The `TYPE_LABELS`, `TYPE_SINGULAR` and `SOURCE_TYPE_LABELS` dicts are derived from them, so other pages are unchanged. Entity-type messages carry a `term` link to the glossary, and a localized page using one needs an approved glossary label for that term |
| Requirements | `page_requirements()` returns exactly the messages, content units and glossary terms a page renders: `/registry/` 77, 102 and 10; `/methodology/` 102, 5 and 10. A localized rendering also needs the localization-only shell messages |
| Completeness | A pseudo-localization test replaces every letter of every catalog and canonical text. `/registry/` then shows no English, and `/methodology/` shows only the deferred changelog records |
| Gates added | Structural parity with English (heading sequence, element ids and anchor targets, internal links, sections, lists and tables). The literal text of every qualifier and disclosure the page renders must be present on the page. `/registry/` passes every gate end to end in synthetic Arabic and French |

**Deferred.** The 97 canonical changelog texts on `/methodology/` (note, entry titles, change lists, corrections, review fixes, breaking changes) still render as recorded in `data/changelog.json`.
- **Why:** translating them needs content units for list items, which means deciding how such items are identified:
  - position-based ids break when items are inserted;
  - content-addressed ids turn every edit into a new unit.
- **Consequence:** until that decision, `/methodology/` cannot be complete in another language.

**Plural forms.** Counts use two English forms (`records.one`, `records.other`). Arabic has more plural categories. Translators phrase these units neutrally until plural selection is added.

**Conditional units.** `page.registry.coverage.none` and `page.registry.coverage.gap` render only when a domain has no entity. They are in the inventory so they are translated together with the page. If they are needed but not translated, the page is withdrawn rather than shown with English.

