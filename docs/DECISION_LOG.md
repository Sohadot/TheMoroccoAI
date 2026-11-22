# Decision Log — TheMoroccoAI

This public log records governance decisions, not completed implementation or external validation. English is the authoritative project language. Entries are append-only in substance: superseded decisions retain their history and link to successors. Confidential commercial strategy, evaluator responses, scoring keys, personal data and credentials must never be committed here.

## TMA-DEC-001 — Ownership and independence
- Date: 2026-11-22
- Domain: Governance / public representation
- Decision status: Accepted
- Implementation status: Implemented in PR #15 (merged as f096de6); wording consistency, footer synchronization and regression gates completed in PR #16 (merged as bbb5d1a); external review pending
- Decision: State that TheMoroccoAI.com is an independently developed digital asset owned and operated by Sohadot, and is not affiliated with, endorsed by, or operated on behalf of any government, public institution, or third-party organization or company. References to external sources do not imply endorsement or participation.
- Rationale: Distinguish ownership, editorial independence, source provenance and institutional authority.
- Constraints: Do not claim ownership of third-party source materials or assert an unverified corporate legal form.
- Implementation: Canonical statement (`OWNERSHIP_STATEMENT` in tools/build.py and tools/check_site.py) published in the methodology ownership section (/methodology/#ownership-h) and on the homepage, acquisition and evaluation pages; every page carries the footer note "Owned and operated by Sohadot" and links to the ownership section. Enforced by tools/check_site.py and tests/test_site.py.

## TMA-DEC-002 — Independent Research Evaluation
- Date: 2026-11-22
- Domain: Research usability / privacy
- Decision status: Accepted
- Implementation status: Implemented in PR #14; deployment and independent validation pending
- External validation status: Not performed
- Decision: Introduce /evaluation/ with an introductory (~5 minute) and specialist (~15–20 minute) independent research evaluation. The first release is static, privacy-minimizing, and requires no login, tracking service or third-party form provider.
- Rationale: Obtain independently interpretable evidence of research usability without conflating participation, completion or opinions with external validation.
- Constraints: No answer keys, scoring rubrics or participant records in the public repository. No correct-answer feedback, guided deep links or prefilled responses. Responses are locally drafted and optionally copied for voluntary submission. No automatic upload. Explain that copied text is not submitted.
- Indexing: noindex, follow; adapt sitemap checks to explicitly handle excluded pages.
- Implementation: See docs/EVALUATION_SPEC.md.

## TMA-DEC-003 — Language authority and localization
- Date: 2026-11-22
- Domain: Content / localization
- Decision status: Accepted
- Implementation status: Pending
- Decision: English is the official, authoritative project language. French and Arabic are secondary localization priorities; Tamazight and Spanish may follow after language-specific quality review.
- Constraints: Keep original-language evidence excerpts intact, distinguish translations from quotations, use canonical terminology, correct hreflang, and do not index incomplete translations.
- Rationale: Preserve one semantic reference while widening accessibility.
- Refined by: TMA-DEC-007 (2026-11-22), which adds Darija and Standard Moroccan Amazigh as future priorities, keeps Spanish as a possible later language without commitment, and sets the translation architecture. The decision above is otherwise unchanged.

## TMA-DEC-004 — External human validation
- Date: 2026-11-22
- Domain: Validation / funding
- Decision status: Accepted
- Implementation status: Pending
- External validation status: Pending
- Decision: Defer paid international human evaluation until 2027 due to payment constraints; permit voluntary evaluation without pressure or unsubstantiated validation claims.
- Rationale: Preserve financial constraints and integrity of validation claims.

## TMA-DEC-005 — Licensing and acquisition optionality
- Date: 2026-11-22
- Domain: Rights / acquisition
- Decision status: Accepted
- Implementation status: Deferred
- Decision: Do not declare a new public content/data license before explicit rights and acquisition-strategy review.
- Rationale: Avoid accidentally granting rights inconsistent with source provenance or future transfer.
- Constraints: Respect third-party rights and existing bundled-font licenses.

## TMA-DEC-006 — Public/private documentation boundary
- Date: 2026-11-22
- Domain: Information security
- Decision status: Accepted
- Implementation status: Implemented in documentation; Drive access restrictions require owner verification
- Decision: Public GitHub is the source of truth for non-sensitive implementation, tests and decisions. Restricted operational notes, private scoring criteria, non-public evaluation responses and commercial negotiation material belong in a separately access-controlled private workspace, such as Google Drive.
- Constraints: No credentials in Drive documents; use a secrets manager. No participant data without informed consent, a retention policy and restricted access. Never place sensitive data in a public PR, issue or commit history.

## TMA-DEC-007 — Multilingual reference architecture
- Date: 2026-11-22
- Domain: Content / localization / architecture
- Decision status: Accepted (Sohadot integration authority)
- Implementation status: Foundation added in Sprint 19B-1 (translation layer, validation, English interface strings read from a catalog with unchanged output). Rendering engine, publication gates, multilingual SEO and right-to-left support added in Sprint 19B-2 with unchanged English output. Presentation text of /registry/ and /methodology/ extracted into the catalog in Sprint 19B-3 with byte-identical English output. No translation drafted or reviewed; no page registered for localization; no localized page or route published.
- Refines: TMA-DEC-003 (language set). Relies on TMA-DEC-001 (ownership disclosures on every localized page), TMA-DEC-002 (evaluation stays English until a separate neutrality review) and TMA-DEC-006 (pseudonymous review records; no drafts on the public branch).
- Decision: Publish the single English reference in other languages as reviewed translations derived from the same canonical data, as set out in docs/ADR_MULTILINGUAL_REFERENCE.md. English is the sole authoritative research language. Modern Standard Arabic and French are the first publication languages; Moroccan Darija (Arabic script) and Standard Moroccan Amazigh (Tifinagh) are future priorities; Spanish is a possible later language without a publication commitment. No language introduces research conclusions or duplicates canonical evidence.
- Constraints: Translations live in i18n/, outside data/ and the reference contract. A page is published in a language only when every unit it needs has a substantive and a linguistic review by reviewers independent of the drafter (two different reviewers preferred), recorded pseudonymously, and matches the current English source. No grace period for stale translations; English publishing never waits for translation. Source excerpts stay verbatim and untranslated in the first two waves. /acquisition/ follows the core reference pages and needs a dedicated substantive and legal review. Begin with the existing self-hosted Arabic font; add a font only on a demonstrated readability need. Machine translation may draft already-public content but never replaces the human reviews, and no review is claimed unless it took place. Webmaster tools may be used to assess indexing; account connection, ownership verification or DNS changes are separately authorized operations; no invasive tracking or analytics. No placeholder routes or premature publication.
- Rationale: Widen access to one reference without creating a second body of research, keep every translation traceable to its English source, and keep the English reference independent of translation readiness.
- Detail: docs/ADR_MULTILINGUAL_REFERENCE.md (owner decisions Q1–Q9), docs/MULTILINGUAL_ARCHITECTURE.md, docs/MULTILINGUAL_IMPLEMENTATION_PLAN.md.
- Superseded in part by: TMA-DEC-008 (2026-11-22), for the review requirements only: the two review functions, reviewers independent of the drafter, and the preference for two different reviewers (Q3 and the matching sentence of Constraints above). Every other provision of this decision stands. The text above is kept as decided.

## TMA-DEC-008 — Human-approved, AI-assisted translation governance
- Date: 2026-11-22
- Domain: Content / localization / review governance
- Decision status: Accepted (project owner)
- Implementation status: Approval contract, reviewer registry, escalation and publication gates implemented in Sprint 19B-4. The reviewer registry is empty: no reviewer is registered, no translation has been approved and no localized page is published.
- Supersedes: in TMA-DEC-007, only (a) "each published translation requires two review functions: substantive accuracy and linguistic quality"; (b) "reviewers are independent of the drafter"; (c) "two different reviewers are preferred; one reviewer may perform both functions only if they did not draft the text"; and the matching Constraints sentence "a substantive and a linguistic review by reviewers independent of the drafter (two different reviewers preferred)". TMA-DEC-007 otherwise stands: English authority, language order, staleness without grace, source excerpts, pseudonymous review records, machine translation only as drafting, no claimed review that did not occur, future-language conditions (Darija, Amazigh) and everything else.
- Decision: For ordinary Arabic and French informational translations, one documented, competent human reviewer may give final editorial approval, provided every mandatory automated integrity and publication check passes. The project owner may act as that reviewer. A sworn or certified translator is not required for ordinary informational publication, and a second human reviewer is not universally required. Additional qualified review (escalation) is required when the reviewer cannot confidently verify the language, terminology or specialist meaning, when a legal or regulatory statement is materially ambiguous, when a translation may alter a significant research qualification, when a publication is represented as independently reviewed, or when a binding external requirement calls for certified translation; an open escalation blocks publication of the affected unit.
- Constraints: AI may prepare, compare, critique and revise drafts; it is never recorded as a human review, and an automated or AI identity can never approve. Automated checks are never recorded as human approval, and a passing check, a commit, a merge or repository access never implies approval. Source citations are not evidence of translation accuracy. Each approval records a registered pseudonymous human reviewer, the decision, a UTC timestamp, this policy id, and the fingerprints of the exact English source and the exact translation it approves; any later change to either makes the unit stale until it is approved again. A reviewer cannot approve a translation recorded as their own draft. Reviewers are registered only by the owner, pseudonymously, with no personal data. The approval record is an attestation kept in the public repository, not cryptographic proof of identity; its integrity rests on repository access control and review history.
- Rationale: Keep every published translation accountable to a named (pseudonymous) human decision and to exact source and text versions, while making publication feasible for ordinary informational content; reserve additional review for the cases where one reviewer cannot be sufficient.
- Detail: docs/TRANSLATION_REVIEW_POLICY.md (policy text, version TMA-DEC-008), docs/MULTILINGUAL_ARCHITECTURE.md section 16.

