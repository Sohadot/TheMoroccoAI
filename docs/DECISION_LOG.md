# Decision Log — TheMoroccoAI

This public log records governance decisions, not completed implementation or external validation. English is the authoritative project language. Entries are append-only in substance: superseded decisions retain their history and link to successors. Confidential commercial strategy, evaluator responses, scoring keys, personal data and credentials must never be committed here.

## TMA-DEC-001 — Ownership and independence
- Date: 2026-11-22
- Domain: Governance / public representation
- Decision status: Accepted
- Implementation status: Pending
- Decision: State that TheMoroccoAI.com is an independently developed digital asset owned and operated by Sohadot, and is not affiliated with, endorsed by, or operated on behalf of any government, public institution, or third-party organization or company. References to external sources do not imply endorsement or participation.
- Rationale: Distinguish ownership, editorial independence, source provenance and institutional authority.
- Constraints: Do not claim ownership of third-party source materials or assert an unverified corporate legal form.
- Implementation: About/independence disclosure, acquisition page and site footer, with corresponding quality gates.

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
