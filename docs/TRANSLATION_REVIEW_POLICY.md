# Translation review policy

| | |
|---|---|
| Policy version | **TMA-DEC-008** (the value an approval must record in `approval.policy`) |
| Status | Accepted by the project owner, 2026-11-22 |
| Replaces | The review requirements of TMA-DEC-007 (two review functions, reviewers independent of the drafter, two reviewers preferred). History: [DECISION_LOG.md](DECISION_LOG.md) |
| Enforced by | `tools/i18n.py` (validation and eligibility), `tools/build.py` (publication gates), `tests/test_i18n.py`, `tests/test_multilingual.py`, `tests/test_extraction.py`, `tests/test_governance.py`, `tests/test_homepage.py`; stable identity: `tests/test_changelog_identity.py` |
| Current state | **No reviewer is registered. No translation has been approved. No localized page is published.** |

## What is decided

1. **English is the authoritative research version.** Every other language is a translation of it, and English prevails over any translation.
2. **One human approval.** For ordinary Arabic and French informational translations, one documented, competent human reviewer may give final editorial approval, provided every automated integrity and publication check passes.
   - The project owner may act as that reviewer.
   - A sworn or certified translator is not required for ordinary informational publication.
   - A second reviewer is not required for every page.
3. **AI is a drafting aid only.** AI may prepare, compare, critique and revise drafts. It is never recorded as a human review, and no AI, tool or automated process can approve.
4. **Checks are not approval.** Automated checks protect identifiers, references, numbers, dates, classifications, qualifiers, disclosures and structure. They do not establish meaning, and a passing check, commit, merge or repository access never counts as approval.
5. **A citation is not proof of translation accuracy.** Source reliability, factual verification, translation fidelity and editorial approval are separate questions.

## Who can approve

- **Registry:** reviewers are listed in `i18n/reviewers.json` with a pseudonymous id (for example `reviewer-ar-02`), a kind (`human` or `certified-translator`) and the languages they may approve.
  - No names, e-mail addresses or other personal data are allowed.
  - Only the owner adds reviewers.
  - Ids that denote AI systems, bots, CI or other automated processes are rejected.
- **No self-approval:** a reviewer cannot approve a translation recorded as their own draft (`draft.by`). A draft prepared with AI assistance records the drafting process in `draft.by` and `draft.method: "machine-assisted"`. The reviewer, including the owner, then approves or revises it.

## The approval record

Every published unit carries this record:

```json
{"id": "page.registry.legend.note", "kind": "qualifier", "status": "APPROVED",
 "text": "…", "source_sha256": "<English source fingerprint>",
 "draft": {"method": "machine-assisted", "by": "ai-draft-01"},
 "approval": {"reviewer": "reviewer-ar-02", "decision": "approved", "reviewed_at": "2026-12-01T09:30:00Z",
              "policy": "TMA-DEC-008", "source_sha256": "<same as above>",
              "translation_sha256": "<fingerprint of the approved text>", "glossary_version": "2026-11-22"}}
```

- **Statuses:**
  - `DRAFT`: a translation exists but is not approved.
  - `NEEDS_REVISION`: the reviewer asked for changes.
  - `APPROVED`: a registered reviewer approved these exact source and translation versions.
  - `REJECTED`: the translation was rejected.
- **STALE:** this is computed, never stored. A unit is stale when the English source or the approved text changes after approval, and a stale unit is never published until it is approved again.
- **Drafts stay off the published branch.** Only `APPROVED` units are committed to `main`, because every repository file is publicly served.
- **Approvals cannot be generated.** The build never writes approvals. No tool may invent reviewer ids or timestamps, or mark its own drafts as approved.
- **Limitation:** an approval record is an attestation kept in the public repository. It is **not** cryptographic proof that the named reviewer made it. Its integrity rests on repository access control and the review history of the change that added it.

## Escalation

The reviewer records an escalation in `approval.escalation` when any of these applies:

| Criterion | When |
|---|---|
| `reviewer-uncertain` | The reviewer cannot confidently assess the translation |
| `legal-ambiguity` | A legal or regulatory statement is materially ambiguous |
| `specialist-term` | A specialised technical term cannot be resolved reliably |
| `research-qualification` | The translation may alter a significant research qualification |
| `language-expertise` | The language needs expertise the reviewer lacks |
| `independent-review-claimed` | The publication is to be represented as independently reviewed |
| `certified-translation-required` | A binding external requirement calls for certified translation |

- **Open escalation:** while it is open, the unit is not publishable.
- **Resolution:** it is resolved only by a second registered reviewer for that language. For `certified-translation-required`, that reviewer must be registered as a `certified-translator`.
- **Not automatic:** legal references are not automatically escalated, and high-risk material is not automatically waived.

## Public disclosure on translated pages

Every localized page carries, in its own language, the translation notice and this statement (catalog id `shell.translation_policy`):

> English is the authoritative version of this reference; this page is translated from it. Translations may be prepared with AI assistance, and each published translation is approved by a documented human reviewer. Automated checks protect identifiers, references, numbers and structure, but do not establish meaning. Corrections and source updates may require renewed review.

- **Where it appears:** only on localized pages, none of which is published. English pages are unchanged.
- **What it does not claim:** independent third-party review, certification or guaranteed accuracy. It names no reviewer.

## Not changed by this policy

TMA-DEC-007 still governs everything else:
- English authority;
- the language order (Arabic and French first, then Darija and Amazigh under their own conditions);
- no grace period for stale translations;
- verbatim, untranslated source excerpts;
- pseudonymous records;
- the acquisition page's dedicated substantive and legal review;
- the evaluation staying English;
- no placeholder routes.
