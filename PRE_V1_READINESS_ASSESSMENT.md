# Pre-v1 Readiness Assessment (Sprint 11A)

## Contract and trust audit of registry v0.10.1

**Verdict: v1.0 is NOT READY.** Five release blockers remain:
- two public statements are wrong (B1, B2);
- three gate items from `SPRINT_10_TIER_0_ASSESSMENT.md` §14 are still open (B3–B5).

None of the blockers needs a new predicate, lifecycle stage or entity. Four of them can be closed without breaking the v0.10 reference-state contract. The licence (B5) needs a decision only the operator can make.

This was a read-only sprint:
- No code, data, generated page or version changed.
- Nothing was published.
- This file is the only addition to the repository.

The only network activity was one run of the read-only source checker. Its report went to a scratch directory, outside `data/`.

---

## 1. Baseline

| Item | Value |
|---|---|
| `main` | `d45601b5f20531504ca76517862f6470180f0bd8` (PR #13), equal to the work branch before this file |
| Registry | v0.10.1, as of 2026-10-20 |
| Validator (`tools/registry.py`) | 0 problems |
| Build check (`tools/build.py --check`) | 80 generated files, 0 stale; same result under `PYTHONHASHSEED` 1 and 2 |
| Site check (`tools/check_site.py`, offline) | 75 pages, 0 problems |
| Unit tests | 383 run, OK (Python 3.13; layout tests ran with the bundled Chromium) |
| Example consumer (`--source . verify`) | OK: 63 records, 65 entities, 78 relationships, 43 matrix rows, 7 gaps |
| Source checker (network, run 2026-10-21) | 63 records: 47 all excerpts matched, 13 need manual review, 3 not checked (2 blocked, 1 unreachable) |

**Read for this assessment:**
- **Canonical files:** `evidence.json`, `ontology.json`, `gaps.json`, `changelog.json`.
- **Derived files:** `reference-state.json`, `matrix.json`, `registry/gaps/gaps.json`, `manifest.json`.
- **Code:** the validator's gap and reference-state rules; the example consumer's reference, gap and compatibility checks.
- **Pages:** the homepage, `/data/`, `/methodology/`, `/acquisition/`, `/registry/state/`.
- **Documents and CI:** README, the Sprint 10 assessments, the CI workflow.

**How figures were obtained:**
- Counts were computed from the files.
- Where a figure is a heuristic, it is labelled as one.

---

## 2. The pre-v1 gate (Sprint 10 §14), as of v0.10.1

| # | Gate item | Status | Finding |
|---|---|---|---|
| 1 | Conflicts governed and machine-readable | **Open** | B3 |
| 2 | Target/measurement semantics governed | **Open**; the defect is worse than recorded | B1, B4 |
| 3 | Every published reference field classified as reproducible or recorded-not-derivable | **Open** for `matrix.json` and `registry/gaps/gaps.json` | N3 |
| 4 | Actor-role strategy accepted or rejected | **Decision pending** | G3 |
| 5 | First-party provenance governed or declared out of scope | **Decision pending** | G4 |
| 6 | The v0.10 contract survives a full release cycle without breaking changes | **One release so far** (v0.10.1). What counts as a "full cycle" is undefined. | G5 |
| 7 | Data and content reuse rights declared | **Open** | B5, G1 |
| 8 | Ministry and actor continuity assessed | **Assessed here** (§3.3). It needs a recorded decision, not new semantics. | G2 |

---

## 3. Findings by audit area

### 3.1 Evidence conflicts and competing official measurements

**Evidence.**

*Recorded only as prose.* These conflicts appear only in `GAP-06.established[]` text and record notes:
- the OSI and EGDI wordings of the 50th-place objective (MAI-EV-0049 and MAI-EV-0062);
- the 75th and 85th EGDI targets for 2026 (0050 and 0052);
- the jobs figures of 190,000, 240,000 and 270,000 (0051, 0002, 0053, 0063);
- 148,500 offshoring jobs (0055) against the 130,000 baseline.

*No record at all.* One side of the enrolment discrepancy, 22,649 against 22,258, has no record. It exists only in MAI-EV-0056's note. It cannot be governed as a conflict between records unless a record is added.

*Structured.* Only DeepEcho's conflict is partly structured, through lifecycle `unresolved` and `superseded_by`.

*Not a conflict.* The MAD 1.7 bn statement against the finance laws is explicitly not matched. It is correctly not treated as a conflict.

**The public method statement is false for most conflicts.** The homepage rule list (static text in `index.html`, line 1025) says *"Conflicting evidence is marked unresolved"*:
- That is true only for one lifecycle (DeepEcho).
- The competing official target statements are "recorded side by side and not reconciled". No field marks them.
- The state page's wording gate does not cover this sentence, because it is homepage text that is not generated.

**Schema gap.** `gaps.json` `established[]` items have no closed schema.
- In a scratch copy, adding `kind` and `records_in_tension` keys to a GAP-06 statement passed the validator and the build.
- The v0.10.1 consumer still verified the result.
- An unreviewed key can therefore enter canonical data silently. The same openness also means a governed conflict model can be added without breaking consumers (§5, B3).

### 3.2 Progress claims against targets, allocations and reported outputs

**Main finding (B1): target attribution in the reference contract.**

`official_targets[].initiatives` lists every initiative among a target record's `related_entities`. Five of the ten OFFICIAL TARGET records are attached to `digital-morocco-2030`, although their own verification notes say they are not the strategy's targets:

| Record | What it is, per its own note | Snapshot shows |
|---|---|---|
| MAI-EV-0050 | Programme 429 performance target (2023 finance bill), EGDI 75th by 2026. "Not targets stated as the strategy's." | initiative `digital-morocco-2030`, covering gap GAP-06 |
| MAI-EV-0051 | Programme 429, 190,000 jobs by 2030 (same caveat) | same |
| MAI-EV-0052 | Programme 429, EGDI 85th by 2026 (same caveat) | same |
| MAI-EV-0053 | Programme 429, 270,000 jobs by 2030 (same caveat) | same |
| MAI-EV-0063 | Offshoring Circular 2025/15: 270,000 jobs and MAD 40 bn exports. The ministry *says* it is aligned with the strategy; the circular itself was not read. | same |

How this reaches readers:
- `/registry/state/` §05 renders the snapshot as **Official targets**, listed by initiative.
- An external consumer reading the contract learns that Digital Morocco 2030 has a target of "EGDI 75th by 2026". The registry's own notes deny that.
- The defect is reproducible by rule and passes every gate, because the rule does exactly what it says. The rule's meaning ("by initiative") is what misleads.
- Freezing this at v1.0 would freeze a misattribution.

**Record roles are prose-only (B4).** Whether a record is one of the following is recorded only in claims, notes and gap statements:
- a strategy target;
- another framework's target;
- an allocation (0054, 0059: payment appropriations, not expenditure);
- a reported figure (0003, 0055, 0056: UNVERIFIED CLAIM);
- an independent measurement (0046 UN EGDI; 0057 Cour des comptes);
- a pre-strategy baseline.

`evidence_type` and `classification` do not separate these roles. For example, a VERIFIED FACT can be an appropriation, a UN rank or an audit finding. A consumer cannot answer "which recorded figures are allocations, not spending?" without reading prose.

**What is already sound:**
- No progress field exists.
- No appropriations are summed.
- Targets are never shown as achieved.
- Every target initiative has an open gap.

### 3.3 Actor roles, institutional representatives and contracting parties

| Issue | Evidence | Assessment |
|---|---|---|
| Incomplete party lists | MAI-EV-0044 names four signatories of the Nexus memorandum. Only two are entities: the Ministry of Investment and AMDIE are not modelled. The matrix shows two signatory rows, with no statement that the list is partial. | `signatory_of` means "a recorded party", not "the parties". This is undocumented. Documentation-only fix (G3). |
| Acts by officers | MAI-EV-0008: the CGEM president signed, recorded as `cgem signatory_of`. MAI-EV-0048: the minister chaired, recorded as a ministry event. | Attribution to the represented body is consistent but unstated. Documentation-only fix (G3). |
| Ministry continuity | A new government was appointed on 16 Oct 2026. `ministry-digital-transition` carries `launched`, `presented`, `organized`, 2 `operates` and 5 `signatory_of` relationships, and publishes 10 of the 46 VERIFIED FACT records. `ministry-ai-digital-transformation` exists (MAI-EV-0014), and its attributions are unpublished. | Both entities exist, and the note already says succession is unverified. Present-tense operator statements, such as "Operator: Ministry of Digital Transition…" on the homepage and in Q6, read as current after a reorganisation. They are bounded by "as named on its services" only in the attribute value. Decision G2. |
| Roles from `domain` | Already refused by the validator and the state-page gate. | Sound. G3 asks only that the rejection be made formal. |

### 3.4 First-party claims and independently established facts

**What VERIFIED FACT means.** It is defined as "an event, act or status that the cited source documents directly". It does not mean independently established.

**Scale (heuristic, from `source_organization` and `source_type`).** At least 17 of 46 VERIFIED FACT records are published by a party to what they document:
- 10 by the Ministry of Digital Transition about its own acts (0005, 0006, 0007, 0018, 0034, 0035, 0038, 0044, 0045, 0048);
- 7 from the actor's own site, a signatory or an investor (0008, 0026, 0027, 0028, 0029, 0031, 0037).

**Examples:**
- `ministry-digital-transition signatory_of green-data-centres-agreement` rests only on the ministry's own report (0006).
- `um6p-data-centre-partnership` rests on 0007 and 0019.

**Why it cannot be derived.** `source_entity` exists on only 5 records, all of them operator-basis status records. A first-party view is therefore not derivable; that is why C10 was rejected in Sprint 10. This is a disclosure problem, not a data error. The methodology defines the term correctly, but the label "VERIFIED FACT" is easily read as independent confirmation.

**A second naming collision.** `verification_status: verified` means "excerpt matched". All 3 UNVERIFIED CLAIM records carry `verified`. Both definitions are published. An external reader still sees "UNVERIFIED CLAIM / verified" with no glossary warning.

**Homepage.** The homepage says the domains are "each populated only from verified records". That is static text. The domain counts include 3 UNVERIFIED CLAIM records and 1 `partial` record (MAI-EV-0017).

### 3.5 Entity-to-gap mapping when several gaps apply

**Today:**
- Every listed entity is in exactly one gap.
- Every targeted initiative is in exactly one gap.

**Latent ambiguities:**
1. `covering_gap` uses file-order selection (known; Sprint 10 limitation).
2. The validator's "every initiative with a target has a progress gap" check accepts any gap that lists the initiative. A governance gap that is ordered first would satisfy the check and become the `covering_gap`, with no failure.
3. `entities_in_open_gaps` covers entity-scoped gaps only. GAP-05 is relationship-scoped (`entities: []`). Its 11 relationships involve entities that appear under no gap in that map, for example `deepecho`, `swam-fraud-scoring`, `ai-movement` and `um6p-ventures`. The rule ("for each entity listed by an open gap") is accurate. A consumer asking "which open gaps concern X?" still gets an incomplete answer without being told.

### 3.6 Reproducible projections that rest on recorded editorial judgments

**Snapshot:** sound. Every field names its recorded judgments under `rests_on`. `scope` and `documentation` are labelled recorded-not-derivable.

**Other derived files:**
- `matrix.json.derivation` publishes rules, but no provenance labels. For example, `object.status_as_recorded` and `qualifications` are copied editorial text.
- `registry/gaps/gaps.json` publishes `derived_from` as paths without hashes. The snapshot's `derived_from` carries hashes.

**Generated vs hand-written text.** The homepage's static rules section is hand-written and outside every wording gate. The errors in §3.1 and §3.4 live there.

---

## 4. Licensing and third-party source restrictions

This section is not legal advice. Points marked *(counsel)* need a qualified opinion before v1.

1. **Nothing is licensed.**
   - There is no `LICENSE` file.
   - `manifest.rights` says no content or data licence has been declared.
   - Owning the repository gives the operator rights only over what the operator authored. It grants no rights over source materials.
   - Third parties currently have no grant to reuse anything, including the registry's own claims, notes, ontology and gap assessments, the generator, the validator and the published example consumer. The consumer is presented as something to run. Without a code licence, copying or adapting it is not permitted.
2. **Separable layers, each needing its own decision:**

   | Layer | Who holds rights |
   |---|---|
   | (a) Registry-authored data: claims, notes, structure, gap text, derived files | Operator |
   | (b) Verbatim excerpts | Their publishers. Excerpts total 63 records with 1–11 quotations each, in French, English and Arabic. |
   | (c) Code | Operator |
   | (d) Visual identity: logo and background image | Operator, if chain of title holds |
   | (e) Fonts | Already SIL OFL 1.1 |

3. **Excerpts.** A licence on (a) must explicitly exclude (b).
   - Quotation exceptions differ by jurisdiction *(counsel)*: Moroccan Law 2-00, EU, US fair use.
   - Official legislative and administrative texts (Bulletin Officiel, finance laws) may be outside copyright protection under Moroccan law *(counsel)*.
   - UN, TOP500, journal (OUP), arXiv, Hugging Face and company pages each have their own terms.
   - MAI-EV-0049's excerpts are a transcription of an image-only PDF.
4. **Chain of title for transfer.**
   - The acquisition page lists the logo and visual identity as transferable. Their origin is not documented in the repository.
   - Commits come from two operator identities and an AI co-author. The operator should be able to state ownership and authorship for a buyer *(counsel)*.
5. **No archived copies.** The registry does not keep copies of sources. That is good for third-party rights, but it makes evidence depend on publishers' URLs (§6). Any archiving proposal reopens the rights question.

---

## 5. Operational continuity and transferability

| Area | State | Risk |
|---|---|---|
| Build reproducibility | Standard library only; deterministic (byte-identical under different hash seeds); generated pages committed; CI runs validate, build check, site check and tests | Low |
| Hidden time dependency | `validate_evidence` uses `date.today()` only to refuse future-dated records | Low |
| CI external dependencies | `check_site.py --network` resolves the operator's mail domain through `dns.google`. Layout tests skip silently when no Chromium is present. | Medium: after a transfer, CI fails until `CONTACT` changes. A runner without a browser passes without layout coverage. |
| Operator identity in code | `CONTACT = "agent@sohadot.com"` is hard-coded in `tools/build.py`, `tools/check_site.py` and `tests/test_site.py` | Medium. One constant would make the handover a one-line change. |
| Version identification | No git tags. v0.9.0–v0.10.1 changelog entries carry a PR number and `commit: null`. Older versions are retrievable only through GitHub history. | Medium: citations of a version depend on the GitHub repository staying at the same path |
| Editorial knowledge | Rules are spread across the README, `/methodology/`, 11 sprint assessments and validator code. No operations or editorial handbook exists. | **High.** A successor can run the build without help, but cannot make the editorial judgments (classification, status basis, gap re-assessment) without reconstructing them from sprint history. |
| Source continuity | 2026-10-21 run: MAI-EV-0059 unreachable (finances.gov.ma, 2025 finance-law appropriation); 0041 and 0043 blocked. 13 records need manual review, mostly PDFs (Arabic, tables, one image-only). Manual inspection was not done here, so changed sources cannot be told apart from extraction limits. | Medium. 16 of 63 records (25%) cannot currently be re-verified mechanically by an outsider using the published tool. |
| Single operator | Corrections, acquisition and contact all go to one mailbox. There is no stated succession or abandonment policy. | Medium (G6) |

---

## 6. External usability

**Can an independent user understand, download, verify, cite and reuse the data without private explanations?**

| Capability | Today | Gap |
|---|---|---|
| Understand | `/data/`, `/methodology/`, published `derivation` rules, classification definitions | Two naming collisions (§3.4); `signatory_of` and `entities_in_open_gaps` scope not stated (§3.3, §3.5); record roles prose-only (§3.2) |
| Download | Manifest of 7 JSON files with sizes and hashes | Only the latest version is served; there are no versioned URLs |
| Verify | Standard-library consumer recomputes every reproducible field; the hashes' limits are stated honestly | The consumer is closed-world: any new top-level snapshot field, or new key in a snapshot value, fails it (`_check_reference`, lines 518–534). The contract has no extension rule (G5). 25% of excerpts are not mechanically re-matchable. |
| Cite | Stable record and entity IDs that are never reused | No citation guidance (which version, as-of date, URL, how to cite a record) |
| Reuse responsibly | Clear non-endorsement and non-affiliation statements | No licence (B5) |

---

## 7. Classified findings

### 7.1 Release blockers

| ID | Problem | Gate |
|---|---|---|
| **B1** | `official_targets` attributes 5 non-strategy target records to Digital Morocco 2030 | 2 |
| **B2** | False or overbroad public method statements on the homepage ("Conflicting evidence is marked unresolved"; "populated only from verified records") | Trust |
| **B3** | Conflicts are not machine-readable | 1 |
| **B4** | Target, allocation, reported-figure and measurement roles are not governed | 2 |
| **B5** | No licence for data or code | 7 |

### 7.2 Governance decisions required (operator)

| ID | Decision | Recommendation |
|---|---|---|
| **G1** | Licence model | Registry-authored data and derived files under CC BY 4.0, with excerpts explicitly excluded. Code under MIT or Apache-2.0. Alternative: CC0 for data, which maximises reuse but gives up attribution. Counsel to review the excerpt carve-out. |
| **G2** | Ministry continuity at v1 | Do not wait for the attributions decree. Record the continuity position explicitly: existing relationships stay with `ministry-digital-transition` as documented on their dates, and operator statements carry their observation date. Re-assess once attributions are published. |
| **G3** | Actor-role strategy | **Reject** inferred roles for v1. Roles exist only as predicates on evidenced relationships. `signatory_of` names recorded parties, not necessarily all parties. An act by an officer is attributed to the body the source says the officer represents. |
| **G4** | First-party provenance | **Declare out of scope for v1**, with explicit disclosure: VERIFIED FACT means documented directly by the cited source, which may be a party to the act. Defer a structured source-relation field. |
| **G5** | Contract stability and extension rule | Define a "full release cycle" as at least one further published release, plus a fixed observation period, with no breaking change to `reference-state.json`. Decide before v1 whether v1 consumers fail or warn on unknown additive fields; today they fail. |
| **G6** | Continuity and succession statement | Publish who maintains the registry, how corrections are handled, and what happens to the data if maintenance stops. Wording is the operator's. |
| **G7** | Statement-kind vocabulary (needed by B3 and B4) | Approve the closed vocabulary in §8, or amend it |

### 7.3 Non-blocking improvements

| ID | Improvement |
|---|---|
| N1 | Fail-closed check: each initiative with an OFFICIAL TARGET is listed by exactly one gap, so `covering_gap` can never depend on file order |
| N2 | State the scope of `entities_in_open_gaps` (relationship-scoped gaps excluded) in its rule and on the state page |
| N3 | Field-classification table (reproducible / recorded-not-derivable / editorial copy) for `matrix.json` and `registry/gaps/gaps.json` on `/data/` (gate 3) |
| N4 | Glossary note on `/data/` for "VERIFIED FACT" against independent confirmation, and `verification_status` against classification |
| N5 | Citation guidance on `/data/` |
| N6 | `CONTACT` defined once and imported; layout tests report "not run" visibly instead of skipping silently in CI |
| N7 | Operations and editorial handbook: an index of the rules, where each lives, and the re-assessment workflow |
| N8 | Manual review of the 16 records the checker could not confirm, recorded as a dated review note outside `data/` |

### 7.4 Explicitly deferred

| Matter | Why it is deferred |
|---|---|
| Structured target attribution in the snapshot (a `stated_for` field, or a change to `official_targets` values) | It breaks v0.10 consumers and restarts gate 6. B1 is closed without it (§8). Revisit for v2, or before v1 only if the operator rejects the non-breaking route. |
| Snapshot conflict field | It would contradict the fixed `scope` ("no conflict list"), which consumers hard-code. Conflicts stay in `gaps.json`. |
| Structured first-party field (`source_relation`) | G4 |
| Indicator-level modelling (C15) | Rejected in Sprint 10 |
| Archived source copies or mirror URLs | Rights question (§4.5) |
| Versioned download paths, git tags, DOI or repository deposit | These are publication acts, excluded by this sprint. Propose separately after G1. |
| Signed manifests | Outside scope; hashes remain consistency checks |
| Recording the 22,258 enrolment figure | Needs evidence acquisition, not governance |
| Arabic, French and Tamazight editions | Unchanged plan |

---

## 8. Proposed changes: detail

All proposals use existing fields and vocabularies, or an optional key inside `gaps.json` statements. None adds a predicate, lifecycle stage or entity.

### B1: target attribution

- **Problem and evidence:** §3.2 table; `reference-state.json` `official_targets`; record notes of 0050–0053 and 0063.
- **Smallest viable correction:** two parts, neither changing a snapshot value.
  1. Change the rule text of `derivation.official_targets` and the state-page heading and boundary text. `initiatives` becomes "the initiatives the record concerns (its related_entities), which is not necessarily the initiative that set the target", and §05 is relabelled accordingly.
  2. Carry the attribution in GAP-06 through B4's statement kinds: `target_for_initiative` against `target_other_framework`. That makes it machine-readable without changing the snapshot.
- **Contract impact:**
  - Rule text only: the consumer checks that a rule exists and is `reproducible`, not its text (`_check_reference`, lines 522–531).
  - No value changes.
  - The state page's `data-ref` values are unchanged; its static text changes, so the wording gate must accept the new boundary sentence.
- **Compatibility:** v0.6–v0.10.1 consumers are unaffected. No migration.
- **Validation and adversarial tests:**
  - The page states the "concerns, not set by" boundary; a test pins it independently of the build's list.
  - Mutant: the heading restored to "targets of {initiative}" is refused.
  - Mutant: a GAP-06 statement citing 0050 labelled `target_for_initiative` is refused, because the record note and kind disagree. This needs a recorded per-record expectation in the test, since notes are not parsed.
  - The consumer from `d45601b` still verifies.
- **Operator approval:** yes. It changes the approved Tier 2 wording.

### B2: public method statements

- **Problem and evidence:** `index.html` line 1025 and the section intro at line 896; §3.1 and §3.4.
- **Smallest viable correction:** reword the two sentences:
  - "Conflicting lifecycle evidence is marked unresolved; competing official statements are recorded side by side and not reconciled; outdated claims are marked superseded."
  - "each populated only from sourced records, classified as fact, target, plan, analysis or unverified claim".
- **Contract impact:** none. Homepage static text only.
- **Compatibility:** none needed.
- **Validation and adversarial tests:**
  - Extend the site check so that the homepage static rules block is covered by a refusal of "conflicting evidence is marked unresolved" and "only from verified records".
  - Mutants: restore each sentence and confirm it is refused.
- **Operator approval:** yes. It is public positioning text.

### B3 and B4: governed statement kinds in `gaps.json`

- **Problem and evidence:** §3.1 and §3.2. Conflicts and record roles exist only in prose.
- **Smallest viable correction:** an optional `kind` on each `established[]` item, from a closed vocabulary published in `gaps.json`, plus an optional `records_in_tension` (two or more records the statement places side by side without reconciling).
  - **Vocabulary proposed for approval (G7):**
    - `context`
    - `target_for_initiative`
    - `target_other_framework`
    - `allocation`
    - `reported_figure`
    - `independent_measurement`
  - **Requirement:** `kind` is required for every gap that lists an initiative with an OFFICIAL TARGET (today GAP-02 and GAP-06) and optional elsewhere.
  - **Validator closes the item schema** to `text`, `evidence`, `kind` and `records_in_tension`, ending the silent-key gap found in §3.1.
  - **Minimal kind rules** (the kind itself remains a recorded editorial judgment, labelled as such):
    - target kinds cite at least one OFFICIAL TARGET;
    - `allocation` and `independent_measurement` cite at least one VERIFIED FACT;
    - `reported_figure` cites at least one record;
    - `records_in_tension` is a subset of the statement's `evidence`, with at least two records.
  - **Feasibility check (illustrative, not an approved assessment):** every current statement maps to one kind.

    | Gap | Kind | Statements |
    |---|---|---|
    | GAP-06 | `context` | 2 (launch; conference) |
    | GAP-06 | `target_for_initiative` | 2 (objectives; OSI vs EGDI, with `records_in_tension` 0049 and 0062) |
    | GAP-06 | `target_other_framework` | 2 (programme 429, in tension with 0002; Circular 2025/15) |
    | GAP-06 | `allocation` | 1 (finance-law appropriations) |
    | GAP-06 | `reported_figure` | 2 (MAD 1.7 bn; offshoring jobs and enrolments) |
    | GAP-06 | `independent_measurement` | 2 (UN ranks; Cour des comptes) |
    | GAP-02 | `target_for_initiative` | 2 |
    | GAP-02 | `context` | 2 |

- **Contract impact:**
  - `data/gaps.json` and `registry/gaps/gaps.json` gain optional keys, copied verbatim.
  - **No snapshot field changes.** Only the snapshot's `derived_from` hash for `gaps.json` changes, as on any gap edit.
  - The meaning of published reference data changes, so the README rule requires a version change and a changelog entry. The version number is the operator's decision, not automatic.
- **Compatibility:**
  - **Tested in a scratch copy:** with the keys added to a GAP-06 statement, the v0.10.1 consumer verified the rebuilt site. It compares `established` between the two gap files as whole values and reads only `evidence` inside items.
  - Older consumers are expected to behave the same. This should be confirmed in 11B against the v0.6–v0.10.1 consumers.
  - The current consumer gains a check of the kind rules.
- **Validation and adversarial tests:**

  *Refusals:*
  - an unknown key;
  - an unknown kind;
  - a missing kind in GAP-02 or GAP-06;
  - `target_for_initiative` with no OFFICIAL TARGET;
  - `records_in_tension` with one record, or with a record not in `evidence`;
  - `allocation` citing only an UNVERIFIED CLAIM.

  *Compatibility:*
  - Old consumers verify the result.
  - The snapshot is byte-identical apart from `derived_from` and the version fields.

  *State page:*
  - Still shows no conflict count. The page renders only the snapshot, and the snapshot is unchanged.
  - Mutant: a "conflicts" section added from the new keys is refused by the existing gate.

  *Fingerprints:* unchanged, because gap text is outside the fingerprint by design. Test that adding kinds does not require re-fingerprinting.

- **Operator approval:** yes (G7). This is the governed conflict and measurement model that Sprint 10 deferred to pre-v1.

### B5: licence

- **Problem and evidence:** §4.
- **Smallest viable correction, after G1:**
  - add a `LICENSE` for code;
  - add a data-licence statement that excludes excerpts;
  - change the value of the existing `manifest.rights` field;
  - add README transfer notes and a `/data/` rights paragraph.
- **Contract impact:** a value change in `manifest.rights`. That field is not recomputed by consumers. This should be confirmed in 11B by running the old consumers.
- **Compatibility:** no structural change.
- **Validation and adversarial tests:**
  - A test pins that `rights`, `/data/` and README agree.
  - A test pins that the excerpt carve-out is present.
  - Mutant: removing the carve-out is refused.
- **Operator approval:** yes. It is the operator's decision alone, and counsel review is recommended.

### N1–N8

| ID | Contract impact | Tests | Approval |
|---|---|---|---|
| N1 | None. It is a new build failure condition that is false on current data. | Synthetic second gap listing `digital-morocco-2030` makes the build fail; current data passes | Yes (validator rule) |
| N2 | Rule text and page text only | Page states the scope; gate accepts it | Yes (Tier 2 wording) |
| N3 | `/data/` HTML only. No JSON change in 11B. | Table generated from a single source; every `matrix.json` derivation key classified; mutant: missing key fails the build | Yes |
| N4, N5 | `/data/` text only | Pinned text tests | Yes |
| N6 | None | Changing `CONTACT` in one place updates build, site check and tests; layout test absence is reported | No (engineering hygiene). Its inclusion in 11B is still proposed for approval. |
| N7 | New Markdown file | Links resolve | Yes (content) |
| N8 | None (report outside `data/`) | Not applicable | Yes, if any record changes as a result: that would be a separate data change |

---

## 9. Prioritised decision matrix

**Priority order:** trust risk first, then gate coverage, then cost.

| Rank | ID | Type | Trust risk if left | Closes gate item | Breaking? | Effort | Operator approval |
|---|---|---|---|---|---|---|---|
| 1 | B1 | Blocker | High: the contract misattributes targets | 2 (part) | No | S | Yes |
| 2 | B2 | Blocker | High: public method claim untrue | — | No | XS | Yes |
| 3 | G1 → B5 | Decision → blocker | High: no lawful reuse | 7 | No | S after decision | Yes (operator only) |
| 4 | G7 → B3/B4 | Decision → blocker | Medium-high | 1, 2 | No (tested) | M | Yes |
| 5 | G5 | Decision | Medium: v1 compatibility promise undefined | 6 | — | XS | Yes |
| 6 | G3, G4 | Decisions | Medium: misreading of roles and first-party sources | 4, 5 | No | XS (documentation) | Yes |
| 7 | G2 | Decision | Medium: stale operator wording after the reorganisation | 8 | No | XS | Yes |
| 8 | N3 | Improvement | Medium | 3 | No | S | Yes |
| 9 | N1, N2 | Improvement | Low now, high if gaps multiply | — | No | XS | Yes |
| 10 | N7, G6 | Improvement / decision | High for transfer, low for readers | — | No | M | Yes |
| 11 | N4, N5, N6, N8 | Improvement | Low to medium | — | No | XS–S | N6 no; others yes |

---

## 10. Sprint 11B: bounded implementation proposal

**Goal.** Close every release blocker and record every gate decision without breaking the v0.10 reference-state contract, so that gate item 6's cycle is not restarted.

**Preconditions.** Operator decisions on G1–G7. Where a decision is withheld, its dependent item drops out of 11B; nothing is assumed.

**In scope:**

| Order | Item | Files touched |
|---|---|---|
| 1 | B2: homepage statements and site-check refusal | `index.html` (static block), `tools/check_site.py`, tests |
| 2 | B1 part 1: `official_targets` rule text and state-page wording | `tools/build.py`, tests |
| 3 | B3/B4 and B1 part 2: statement kinds, validator schema closure, consumer check, kinds for GAP-02 and GAP-06 statements | `data/gaps.json`, `tools/registry.py`, `tools/build.py` (gap register copy, `/data/` docs), `examples/registry_consumer.py`, tests |
| 4 | N1: exactly-one-gap check for targeted initiatives | `tools/registry.py`, tests |
| 5 | N2, N3, N4, N5: `/data/` field classification, glossary, citation guidance, gap-map scope | `tools/build.py`, tests |
| 6 | G2, G3, G4, G5 recorded: methodology text and README; operator statements carry their observation date where they are already rendered | `tools/build.py`, README |
| 7 | B5 (if G1 is decided): licence files, `manifest.rights` value, `/data/` and README | `LICENSE*`, `tools/build.py`, README |
| 8 | N6: one `CONTACT` constant; visible layout-skip reporting | `tools/*.py`, tests |
| 9 | Version and changelog entry: only as the operator decides | `data/*.json` version fields, `data/changelog.json` |

**Out of scope:**
- any snapshot field or value change;
- new predicates, lifecycle stages, entities or records;
- evidence acquisition;
- N7 (handbook) and G6 (succession statement), unless the operator adds them;
- deferred items in §7.4;
- outreach, tags, deposits or any new publication channel.

**Exit criteria for 11B:**
1. Validator 0 problems; build check 0 stale; site check 0 problems (including `--network`); full suite passes with layout tests actually run.
2. The `reference-state.json` payload is byte-identical to v0.10.1 except `registry_version`, `as_of` (if changed) and `derived_from` hashes. Rule-text changes are confined to `derivation.official_targets` and, for N2, `derivation.entities_in_open_gaps`.
3. Consumers from v0.6.0, v0.7.0, v0.8.0, v0.9.0, v0.10.0 and v0.10.1 verify the 11B release.
4. Every mutant listed in §8 is caught.
5. Determinism: byte-identical rebuilds under four hash seeds.
6. A short implementation record, as in Sprint 10 Tier 2.

**After 11B.** Gate items 1, 2, 3, 4, 5, 7 and 8 would be closed or formally decided. Item 6 would still need its observation period under the G5 definition. v1.0 would remain a separate, explicit operator decision.

---

## 11. What this assessment does not claim

- It makes no claim about the accuracy of any record beyond what the files and the 2026-10-21 checker run show. The 16 records the checker could not confirm were not manually inspected.
- The first-party count (§3.4) is a heuristic lower bound based on source organisation. It is not a governed figure, and it should not be published as one.
- The licensing points are issues for counsel, not legal conclusions.
- It makes no claim of adoption, authority, institutional use or independent endorsement of the registry. None is documented.

---

## 12. Approval requested

Before any implementation, please confirm:
1. **G1–G7:** accept, amend or reject each recommendation in §7.2.
2. **Sprint 11B scope** as bounded in §10, including whether N6, N7 and G6 are in or out.
3. **Version handling** for the 11B release, or that the version stays as is until you decide.

No further work will be done until these are answered.
