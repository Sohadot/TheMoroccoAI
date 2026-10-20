# Sprint 10 — Morocco AI Reference Model

## Tier 0: reference-model design assessment, updated with the owner's decisions

The Tier 0 assessment was read-only and produced no file. This document records it as approved, with the owner's decisions applied. A separate section at the end documents the Tier 1 implementation.

## 1. Baseline

| Item | Value |
|---|---|
| `main` at Tier 0 | `8ffc6d05b6faea90d0575248dc3e3cc515b0f11b` (PR #11, squash-merged); re-verified before Tier 1 began |
| Registry | v0.9.0, as of 2026-10-20, production verified |
| Records | 63: VERIFIED FACT 46, OFFICIAL TARGET 10, ANNOUNCED PLAN 4, UNVERIFIED CLAIM 3. 62 `verified`, 1 `partial` (MAI-EV-0017). 1 superseded (MAI-EV-0029). |
| Entities | 65: institution 19, project 14, technology 10, sector 8, company 5, initiative 3, model 3, event 1, legal_instrument 1, dataset 1 |
| Relationships | 78: VERIFIED FACT 49, ANNOUNCED PLAN 23, INDEPENDENT ANALYSIS 4, OFFICIAL TARGET 2 |
| Gaps | 7, all open |

**What was read:**
- the canonical data;
- both derived JSON files and the manifest;
- the questions, data and methodology pages;
- the validator's rules and the build's question generators;
- the example consumer, README, tests, and the Sprint assessments through 09.

All counts were computed from the data, not estimated.

## 2. Existing architecture relevant to a reference model

**Canonical files** are maintained by hand:
- `evidence.json`;
- `ontology.json`;
- `gaps.json` (assessments, machine checks, digests);
- `changelog.json`.

**Derived files** before Tier 1:
- `registry/matrix/matrix.json`, with a published `derivation`;
- `registry/gaps/gaps.json`;
- `manifest.json`;
- every HTML page.

Q1–Q7 had no machine-readable output.

**Semantics already governed by the validator:**
- **Record classification.** INDEPENDENT ANALYSIS is forbidden on records and allowed only on relationships.
- **Wording.** No forward-looking wording in facts, and no "achieved" wording in targets or plans. A target needs a `target_year`.
- **Lifecycle** (projects, models, datasets only):
  - a stage beyond `announced` needs a VERIFIED FACT whose `status_evidence` declares that stage;
  - `operational` and `pilot` need a `status_basis`;
  - an operator basis needs the record's `source_entity` to be a verified operator;
  - an independent basis cannot rest on a self-published or press source.
- **Project kind.** Only `ai-application` counts as an AI deployment. A digital platform never counts as one.
- **Origin** (companies).
- **Supersession.**
- **Relationship classifications**, which may never be stronger than the records they cite.
- **Gaps.** Each gap is fingerprinted and has machine checks re-run on every build. GAP-07 has per-entity assessments with resolution paths.
- **Targets need a gap.** Every initiative with a target must be covered by a gap.

The `/data/` page §07 already sorts every part of Q8 and Q9 into one of four labels:
- **reproducible**;
- **recorded, not derivable**;
- **editorial assessment**;
- **fixed wording**.

**A reference layer must inherit this labelling rather than invent its own.**

## 3. Ecosystem-map feasibility

| Category | In the ontology? | Verdict |
|---|---|---|
| Initiatives (strategies, roadmaps, programmes) | `type: initiative` (3) | Derivable |
| AI applications | `project_kind: ai-application` (4) | Derivable |
| Models and datasets | `type` (3 + 1) | Derivable |
| Compute infrastructure | `project_kind: compute-infrastructure` (2) | Derivable. The digital platform (1) stays separate. |
| Institutes and research structures | Two unrelated groups: `project_kind: institute` (5, all announced) and research-domain institutions (9) | Misleading if merged |
| Companies | `type: company` (5), with an origin facet | Derivable |
| Government, regulatory, funding or talent "actors" | Not encoded. `domain` is a thematic label. CGEM and UNESCO carry `funding-partnerships`. Talent appears only as a target sector. | Not derivable without new semantics |

**Decision:**
- Use `(type, project_kind)` as the structural keys.
- `domain` may appear only as a labelled thematic facet, never as a role, function, funder status or regulator status.
- No new categories.
- Technologies and sectors are cross-cutting dimensions, not actors.

## 4. Evidence-State feasibility

| Candidate | Best rule | Why it fails |
|---|---|---|
| DOCUMENTED | Cites at least one VERIFIED FACT | 46 of 47 entities qualify, including institutes whose operation is unknown |
| PARTIALLY DOCUMENTED | Would need an expected-evidence model | It would be a hidden completeness score |
| CONFLICTED | Lifecycle `unresolved`, or a superseded record | Duplicates lifecycle, and misses every target conflict |
| EVIDENCE GAP | Listed by an open gap | Implies that unlisted entities are complete |
| UNRESOLVED | Lifecycle or origin `unresolved` | Merges two unrelated vocabularies |

**Decision: no aggregate Evidence State.** Only facets that each come independently from one existing field are allowed:
- lifecycle and status basis;
- origin;
- the open gaps listing the entity;
- the verbatim GAP-07 assessment;
- classification counts;
- supersession.

## 5. Higher-order derivations

**Approved for the reference layer:**

| Id | Derivation |
|---|---|
| C1 | Lifecycle counts by type and project kind |
| C3 | Operational and pilot projects grouped by existing status basis |
| C4 | Announced projects by kind |
| C5 | GAP-07 institute dimensions, exactly as governed |
| C6 | Official target records by initiative, with their covering gap |
| C8 | UNVERIFIED CLAIM, ANNOUNCED PLAN and partial-verification views |
| C11 | Entities and relationships covered by open gaps |
| C13 | INDEPENDENT ANALYSIS relationships |
| C14 | Superseded records, unresolved lifecycle and unresolved origin, kept as separate concepts |

The existing Q2/Q6, Q4 and GAP-05 derivations may be reused.

**Rejected:**

| Id | Derivation | Reason |
|---|---|---|
| C7 | Conflict lists or counts | Conflicts are prose only |
| C10 | First-party-only entities | `source_entity` exists only on operator-basis records |
| C15 | Indicator-level measurement status | Indicators are not encoded; a target record can hold several |

"Which AI initiatives are operational?" is a category error: initiatives have no lifecycle.

## 6. Reference-state contract (as approved)

The artifact is `registry/reference-state.json`. It is derived and listed in the manifest. Each field has a rule under `derivation` with its provenance. Tier 1 makes every field `reproducible`, and names the recorded judgments it copies or counts under `rests_on`.

**Manifest dependency cycle (correction to the Tier 0 design).** Tier 0 proposed deriving `derived_from` from the manifest, which would have created a manifest → reference state → manifest cycle. As approved:
- the snapshot is computed from the canonical files only;
- it records their direct SHA-256 under `derived_from`;
- the manifest is generated afterwards and lists the snapshot's own SHA-256;
- the manifest is never a semantic input.

**Progress (correction).** Tier 0 proposed a `progress_assessment[]` field labelled editorial. It is **omitted**. The snapshot exposes only:
- the official target records;
- their initiatives;
- each initiative's covering gap;
- that gap's state.

The interpretation that no qualifying measurement establishes progress stays in the governed gap text.

**Must not appear:**
- scores, confidence or completeness measures;
- an aggregate evidence state;
- conflict lists or counts;
- progress fields or counts, or "targets met / not met";
- derived OSI ranks;
- sums of annual appropriations;
- a first-party classification;
- roles inferred from `domain`;
- indicator counts;
- generated summaries;
- any field that upgrades a classification;
- an "operational" initiative.

## 7. Public reference surface

The page is **deferred to Tier 2**, which needs separate approval after the snapshot is reviewed. No "where official sources disagree" section will be generated until conflicts are formally governed.

The constraints identified in Tier 0 still apply:
- render only from the snapshot;
- no totalising title;
- no "progress, achieved, deployed, used by" wording;
- disclaimers on coverage, absence of evidence, availability not being use, targets not being results, allocations not being expenditure, independence, and the as-of date.

## 8. Conflict-model audit

| Conflict | Where it is encoded |
|---|---|
| The 50th objective stated on OSI (MAI-EV-0049) vs EGDI (MAI-EV-0062) | GAP-06 statements (prose) |
| EGDI 75th (0050) vs 85th (0052) by 2026 | GAP-06 statement |
| Jobs: 190,000 / 240,000 / 270,000 | GAP-06 statements |
| Enrolments: 22,649 vs 22,258 | MAI-EV-0056 note only. The second figure has no record. |
| Offshoring jobs: "provides 130,000" vs 148,500 | MAI-EV-0063 note |
| DeepEcho: FDA listing vs developer's site | Lifecycle `unresolved` plus `superseded_by` (partly structured) |
| Head of Government's MAD 1.7 bn vs the settlement law | Explicitly not matched (not a conflict) |

**Conclusion.** Conflicts cannot be derived reliably. A governed form would need a data-contract change to `gaps.json`, for example a marked statement kind with a list of conflicting records, but no new predicate. It is **deferred to a separately approved pre-v1 sprint**. Tier 1 contains no conflict field and parses no prose.

## 9. Gap-model audit

| Gap | Entities | Machine check |
|---|---|---|
| GAP-01 | Idarati AI | `no_status_basis` |
| GAP-02 | Morocco AI 2030 | none (editorial) |
| GAP-03 | Toubkal | `no_ai_application_link` |
| GAP-04 | 3 compute or data-centre projects | `lifecycle_in` |
| GAP-05 | relationship-scoped | `computed_relationships` (11) |
| GAP-06 | Digital Morocco 2030 | none (editorial) |
| GAP-07 | 5 JAZARI institutes | `lifecycle_in`, plus per-entity assessment |

- Gaps enter the snapshot verbatim (state, entities, assessed date, fingerprint, GAP-07 assessments) and are never re-evaluated.
- **Question-to-gap mapping (correction): deferred.** Tier 1 uses only the relationships already encoded: target record → initiative, and gap → entities. A general governed mapping needs separate approval.
- **Reusable patterns:**
  - the target-progress gap (GAP-02, GAP-06), already enforced for every initiative with targets;
  - the per-entity dimension assessment with resolution paths (GAP-07);
  - the machine-checked absence of a qualifying field (GAP-01, GAP-03, GAP-04).

## 10. Risks of semantic overreach

| Risk | Mitigation in Tier 1 |
|---|---|
| A second hidden lifecycle | No state labels |
| Counts without a kind or basis | Every operational entry carries its kind, basis and `counts_as_ai_deployment` |
| Category errors (operational initiatives, domain as role) | Refused by the validator and tests |
| Editorial judgment presented as computed | No progress field |
| Conflicts parsed from prose | No conflict field |
| Indicators counted from records | Rejected |
| Completeness illusion | A scope statement in the file; empty lists mean "none recorded" |

## 11. What remains unchanged

- The classifications.
- Lifecycle stages and their status, basis and source rules.
- `project_kind` semantics.
- Predicates.
- Gap resolution rules, fingerprints, checks and GAP-07 paths.
- Record-level provenance.
- The reproducibility labels on `/data/`.
- The rule that no derived figure is published as sourced.
- Consumer backward compatibility.
- Every Sprint 09 distinction.

## 12. Implementation tiers

| Tier | Scope | Status |
|---|---|---|
| 1 | `registry/reference-state.json` with derivation, manifest entry, consumer recomputation, validator and tests (v0.10.0) | **Implemented** (below) |
| 2 | Public page rendered from the snapshot | Deferred; needs approval |
| Pre-v1 | Governed conflict model; target/measurement semantics; formal field classification; actor-role decision; first-party provenance decision; licence; ministry continuity | Separately approved sprints |

## 13. Tests

The required tests are implemented: see the Tier 1 section.

## 14. v1.0 readiness: NOT READY

v0.10.0 is an intermediate reference layer, not v1.0. **The pre-v1 gate:**
1. Conflicts become governed and machine-readable.
2. Target/measurement semantics become explicitly governed.
3. Every snapshot field is formally classified as reproducible or recorded-not-derivable. Tier 1 does this for the snapshot; the gate stays until it covers every published reference field.
4. The actor-role strategy is explicitly accepted or rejected.
5. First-party provenance is governed, or explicitly declared out of scope.
6. The v0.10 reference contract survives a full release cycle without breaking changes.
7. Data and content reuse rights are declared.
8. Current ministry and actor continuity is assessed.

The licence (7) and ministry continuity (8) do not block Tier 1 and are scheduled for pre-v1 hardening.

## 15. Owner decisions (recorded)

1. **Option B approved:** v0.10.0 intermediate.
2. **No aggregate Evidence State:** facets only.
3. **Structure:** `(type, project_kind)` keys. `domain` only as a labelled thematic facet. No new categories.
4. **Conflicts:** no conflict field, count or inferred group, and no prose parsing. The governed model is deferred to pre-v1.
5. **Progress:** no progress field. The snapshot holds target records, their initiatives, the covering gap and its state.
6. **Question-to-gap mapping:** deferred. Only encoded relationships are used.
7. **Derivations:** C1, C3, C4, C5, C6, C8, C11, C13 and C14 approved. C7, C10 and C15 rejected.
8. **Public page:** deferred to Tier 2.
9. **v1.0:** NOT READY. The gate is as in §14.
10. **Licence and ministry continuity:** pre-v1. They do not block Tier 1.

---

# Tier 1 implementation

## What was built

**Branch.** The session's designated branch, restarted from the verified baseline `8ffc6d05`. `main` was confirmed equal to the baseline before any change.

**Changed files**
- `registry/reference-state.json` (new, generated).
- `tools/build.py`:
  - `REFERENCE_INPUTS`, `reference_derivation()` and `reference_state()`;
  - the snapshot is generated before the manifest, from the canonical bytes;
  - it is added to the manifest's resources;
  - the build refuses to write when the snapshot fails validation;
  - the `/data/` §07 table is generated from the published derivation.
- `tools/registry.py`:
  - `REFERENCE_FIELDS` and `validate_reference_state()`;
  - it refuses fields outside the contract, missing rules, an undefined provenance, and field names that would carry a score, aggregate state, conflict, progress, rank, sum, domain role, first-party class or indicator;
  - it checks the integrity of the lifecycle, status basis and AI-deployment projections.
- `examples/registry_consumer.py`:
  - `reference_state()` recomputes every field from `evidence.json`, `ontology.json` and `gaps.json`, using the published raw bytes for `derived_from`;
  - `_check_reference()` compares every field and requires a reproducible rule for each;
  - standard library only, no import of `tools/`.
- **Version metadata:** `data/evidence.json` and `data/ontology.json` move to 0.10.0, and `data/changelog.json` gains the v0.10.0 entry.
- **Generated pages and files** changed only through the version, counts and the new `/data/` table.
- `README.md` gains a file-table row.
- **Tests:**
  - `tests/test_reference_state.py` is new;
  - `tests/test_consumer.py`: in the "hashes are not a signature" test, the forger now also rewrites the snapshot's `derived_from`, because the snapshot pins the canonical hashes;
  - `tests/test_execution_evidence.py`: the version is no longer hard-coded.

**Accurate scope.** No semantic change was made to the existing evidence records, entities, relationships, predicates, lifecycle or gap assessments. The only changes to canonical files are the version and changelog metadata needed to publish the new derived contract.

## The reference-state contract

| Field | Content | Provenance |
|---|---|---|
| `registry_version`, `as_of` | From `evidence.json` | reproducible |
| `scope`, `documentation`, `derivation` | Fixed statement, link, and the rules | (contract text) |
| `derived_from` | Path and SHA-256 of `/data/evidence.json`, `/data/ontology.json`, `/data/gaps.json` | reproducible |
| `counts` | records, entities, relationships; by classification (records and relationships), by verification status, entities by type | reproducible |
| `superseded_records` | evidence_id and superseded_by | reproducible |
| `lifecycle.entities` | Project, model and dataset projections: type, project_kind, lifecycle, lifecycle_evidence, status_bases (from records declaring the stage only) | reproducible |
| `lifecycle.by_type_and_kind` | Counts per (type, project_kind, lifecycle) | reproducible |
| `operational_or_pilot` | The above, plus status_evidence_records and `counts_as_ai_deployment` (true only for ai-application) | reproducible |
| `operational_or_pilot_by_status_basis` | Basis → entity ids | reproducible |
| `announced_projects_by_kind` | project_kind → ids | reproducible |
| `unresolved_lifecycle`, `unresolved_origin` | Separate lists | reproducible |
| `official_targets` | evidence_id, target_year, initiatives with covering_gap and gap_state | reproducible |
| `open_gaps` | id, entities, assessed, assessed_fingerprint, has_entity_assessments | reproducible |
| `entities_in_open_gaps` | entity → open gap ids | reproducible |
| `entity_assessments` | Verbatim copy of GAP-07's assessments | reproducible |
| `announcement_only_relationships` | The GAP-05 list | reproducible |
| `independent_analysis_relationships` | The 4 inferred relationships | reproducible |
| `records_unverified_claim`, `records_announced_plan`, `records_partially_verified` | Sorted ids | reproducible |

`derivation.not_included` lists what the file deliberately omits.

## Current values

| Value | Result |
|---|---|
| Records | 63 (46 / 10 / 4 / 0 INDEPENDENT ANALYSIS / 3) |
| Entities | 65 |
| Relationships | 78 (49 VERIFIED FACT / 23 ANNOUNCED PLAN / 4 INDEPENDENT ANALYSIS / 2 OFFICIAL TARGET) |
| Verification status | 62 verified, 1 partial |
| Lifecycle entities | 18 (14 projects, 3 models, 1 dataset) |
| Operational or pilot | 3: Idarati AI (AI application, public availability, counts as AI deployment); Sovereign AI marketplace (digital platform, public availability, not an AI deployment); Toubkal (compute, independent listing, not an AI deployment) |
| Announced projects | 10: institute 5, agreement 2, ai-application 2, compute 1 |
| Unresolved lifecycle | 1 (DeepEcho software) |
| Unresolved origin | 1 (UM6P Ventures) |
| Superseded records | 1 (MAI-EV-0029) |
| Official target records | 10: GAP-06 for 8, GAP-02 for 2, all open |
| Open gaps | 7, covering 12 entities |
| GAP-07 entity assessments | 5 |
| Announcement-only relationships | 11 |
| Inferred relationships | 4 |
| UNVERIFIED CLAIM records | 3 |
| ANNOUNCED PLAN records | 4 |
| Partially verified records | 1 |

## Tests and gates

- **New tests:** 22 in `tests/test_reference_state.py`:
  - deterministic byte-identical generation;
  - direct canonical-input hashes;
  - no manifest/snapshot cycle;
  - a reproducible rule for every field;
  - consumer recomputation parity, and the consumer rejecting a snapshot that does not follow;
  - v0.6.0, v0.7.0, v0.8.0 and v0.9.0 consumers verifying v0.10.0;
  - lifecycle and status-basis integrity, with a synthetic case for bases from records that don't declare the stage;
  - no initiative in any lifecycle list;
  - platforms and compute not counted as AI deployments;
  - the exact target-to-gap derivation;
  - GAP-07 copied verbatim;
  - GAP-05 parity;
  - open-gap coverage and separate unresolved concepts;
  - no forbidden field names or judgment words in values, and no aggregate state;
  - no domain or role, and no numbers beyond counts and target years;
  - no ordinal and no summed appropriation;
  - the validator refusing out-of-contract snapshots.
- **Full suite:** 357 tests pass.
- **Validator:** 0 problems.
- **Build check:** 0 stale files.
- **Site check:** 74 pages, 0 problems.
- **Determinism:** two consecutive rebuilds are identical, and the snapshot is byte-identical under four different hash seeds.
- **Manifest:** all 7 resource hashes match their files.
- **Consumers:** the current consumer recomputes and verifies the snapshot. The v0.6.0 (`2803167`), v0.7.0 (`0d0fa8f`), v0.8.0 (`59c4221`) and v0.9.0 (`8ffc6d0`) consumers verify v0.10.0. They fetch and hash the new resource without interpreting it.

**Mutations: 23 of 23 caught.** All 23 were applied to the generator. Each was caught by the build's validator, the new tests or the consumer:
- adding a conflicts field, or a conflict count;
- adding progress or a "met" flag on targets;
- a confidence score;
- an aggregate evidence state;
- a platform counted as AI;
- an initiative listed as operational;
- announced projects upgraded;
- status bases taken from records that don't declare the stage (caught after adding the synthetic test: on current data this mutant is equivalent);
- `derived_from` reading the manifest, or carrying a stale hash;
- targets mapped to non-initiatives;
- the GAP-07 note dropped;
- the GAP-05 list widened;
- domain used as a role;
- summed appropriations;
- a derived OSI ordinal;
- a first-party class;
- unsorted lifecycle order;
- the two unresolved concepts merged;
- a rule removed;
- provenance relabelled.

## Design limitations found during implementation

- **Provenance.** "Reproducible" describes the projection. Every field also rests on recorded editorial judgments (classifications, lifecycle stages, gap states), named under `rests_on`. That is the honest boundary, and the reason pre-v1 gate item 3 remains open.
- **Forger model.** A forger who rewrites a canonical file must now also rewrite the snapshot's `derived_from`. The snapshot does not stop forgery, since the hashes are not a signature, but an incomplete forgery now fails verification.
- **Status bases.** On current data every status record declares its entity's stage, so the rule "bases from declaring records only" is checked by a synthetic case rather than by the published data.
- **Key order.** JSON object keys are written sorted, so the display order of GAP-07's dimensions comes from `entity_assessment.dimension_order` in `/registry/gaps/gaps.json`, not from key order.
- **Older consumers** verify the new release by hash only. They do not check the snapshot's content; only the current consumer does.
- **Field-name guard.** The validator's guard is a deny-list for unknown structures plus an exact whitelist of top-level fields. A new judgment smuggled under an allowed field with an innocuous name would still have to pass consumer parity and the value-word tests.
