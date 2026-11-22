# Arabic and French translation pilot (Sprint 19B-5)

| | |
|---|---|
| Status | **Drafts prepared for owner review. Nothing is approved or published.** |
| Policy | [TMA-DEC-008](TRANSLATION_REVIEW_POLICY.md); workflow and security in [TRANSLATION_APPROVAL_SECURITY.md](TRANSLATION_APPROVAL_SECURITY.md) |
| Draft provenance | AI-assisted (`draft.method: machine-assisted`, `draft.by: ai-draft-01`); Modern Standard Arabic and French |
| Where the drafts are | **Not in this repository.** Two draft workspaces (`pilot-ar.json`, `pilot-fr.json`) and the review package were handed to the owner privately; every file on `main` is publicly served |

## 1. Scope: what a full translation of the three pages needs

Computed with `build.page_requirements()` on the current data:

| Page | Catalog messages | Canonical content units | Glossary terms |
|---|---|---|---|
| `/` | 164 | 42 (26 entity names, 7 domain labels, 4 evidence texts, 3 predicate labels, 2 attribute texts) | 3 |
| `/registry/` | 77 | 102 (90 entity names and statuses, 7 domain labels, 5 classification definitions) | 10 |
| `/methodology/` | 102 | 102 (97 changelog texts, 5 classification definitions) | 10 |
| **Union** | **302** (28 shared) | **208** | **13** |

Dependencies:
- **Localization-only units:** 5 units for the switcher, translation notice, fallback marker and policy disclosure.
- **Changelog texts:** 97, bound to stable identities.
- **Entity attributes:** 2, bound to stable identities.
- **Required disclosures:** ownership statement, independence, translation notice and policy.
- **Approval:** a page publishes only when every one of its units, and every glossary term it uses, is approved and current.
- **Size:** about 2,600 English words of catalog text and 4,400 of canonical text.

## 2. The pilot sample: 42 units per language

The sample is representative rather than exhaustive. No page could be published from it.

| Category | Units |
|---|---|
| Interface | `shell.skip_link`, `footer.as_of`, `date.month.10`, `page.home.status.records`, `page.home.domain.records.other` |
| Accessibility labels | `shell.nav.label`, `page.home.status.label`, `shell.skip_link` |
| Navigation | `shell.nav.registry`, `page.home.nav.coverage`, `page.home.hero.cta.registry` |
| Headings | `page.home.coverage.h2`, `page.methodology.h1`, `page.home.ex.idarati.question` |
| Metadata | `page.home.title`, `page.home.description` |
| Prose | `page.home.access.questions.text`, `page.registry.start.questions` |
| Research qualifications | `page.home.ex.idarati.use_qualifier`, `page.home.ex.2030.targets_qualifier`, `page.registry.legend.note`, `page.home.coverage.intro`, `vocab.lifecycle.availability_suffix`, `facts.currency.recent`, `page.home.ex.infra.announced` |
| Evidence and canonical research text | `evidence:MAI-EV-0011:claim`, `classification:VERIFIED FACT:definition`, `domain:government-policy:label`, `predicate:signatory_of:label` |
| Dynamic and identity-bound text | `changelog:changelog.v0-10-1.title:text`, `attribute:attribute.toubkal-supercomputer.name.06:text`, plus the placeholder units above |
| Institutional terminology | `ontology:ministry-digital-transition:name`, `ontology:um6p:name`, `ontology:cndp:name` |
| Glossary-linked terms | `vocab.lifecycle.operational`, `vocab.classification_inline.verified_fact`, `vocab.entity_type.institution.plural` |
| Disclosures | `footer.disclaimer`, `footer.owner_note`, `disclosure.ownership_statement`, `shell.translation_notice`, `shell.translation_notice.english`, `shell.translation_policy` |

**Terminology candidates.** 14 glossary candidates are shown in the package for information only: 12 editorial concepts, `classification:VERIFIED FACT` and `lifecycle:operational`. Glossary labels are approved separately.

**Institution names.** None is marked `official`. The drafts use `translation` or `established-usage` and ask the reviewer to confirm. A name becomes `official` only with the institution's own published Arabic or French name and its URL.

**Choices for the owner:**
- the Arabic month convention (Moroccan يوليوز، غشت، شتنبر… or the forms used elsewhere);
- Arabic number–noun agreement for counts filled at build time.

## 3. Automated results on the drafts

`python3 tools/translation_review.py check` reports **0 blocking problems** and 2 warnings, both left for the reviewer:
- **Arabic, `evidence:MAI-EV-0011:claim`:** `NEGATION_ADDED`. "غير مباشر" (*indirect*) contains the particle غير. This is a lexical false positive and shows a limit of word lists.
- **Arabic, `page.registry.legend.note`:** `HEDGE_LOST`. "what could not be checked" is rendered as "ما تعذر التحقق منه". The meaning is kept, but the reviewer should confirm.

Running the checks on the drafts also exposed five false positives in the word lists, which were corrected before the package was built:
- Arabic attached prefixes;
- نتيجة meaning *outcome*;
- the noun *state*;
- *reconfirmé*;
- *données à caractère personnel*.

## 4. Isolation, verified

- `git status` shows no draft file.
- No tracked file carries the workspace marker, and `check_site` passes. The marker appears only in ignored `__pycache__` bytecode.
- `i18n/ar` and `i18n/fr` are unchanged and still empty.
- `reviewers.json` is empty.
- `record` refuses the pilot: no reviewer is registered.
- `build.LOCALIZABLE_PAGES` is empty, and no output exists under `/ar/` or `/fr/`.

## 5. Next steps for the owner

1. Decide whether to register yourself as reviewer (procedure in [TRANSLATION_APPROVAL_SECURITY.md](TRANSLATION_APPROVAL_SECURITY.md) §5), and configure the GitHub settings (§4).
2. Review the package and export your decisions. Nothing is approved until you record and commit them yourself.
3. Approve glossary labels and the remaining units of one page before any page can be published. Publication is a separate decision.
