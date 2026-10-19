# Sprint 06 — Evidence Precision & Coverage Integrity

Baseline: `main` at `c6211538caa4285b446644d3cf38cd2e55ae7f7f` (Sprint 05, production verified).
Result: registry v0.5.0, 19 October 2026.

No record, entity or relationship was added, removed or changed. No classification, lifecycle stage or source
interpretation changed. The corrections are to presentation, derived labels, one gap's text, one new gap, and one
validator rule.

## Stage 1 — Read-only semantic audit

### A. Q8 scope and terminology

**Question as published:** "Which organisations are connected to documented AI or computing projects, and what
establishes each connection?"

**Selection rule:** every matrix row whose subject is an institution or company and whose object is a project, of
any project kind, with no stage filter. Result: 15 organisations, 12 projects, 24 relationships.

The 12 projects:

| Kind | Projects | Stage |
| --- | --- | --- |
| AI application (4) | Idarati AI; DeepEcho public-health evaluation; DeepEcho ultrasound software; SWAM fraud scoring | operational; announced; unresolved; announced |
| Institute (3) | Jazari ROOT; JAZARI Industrie X.0; Jazari institute Nador (all AI institutes) | announced |
| Agreement (2) | Green data centres agreement; UM6P data-centre partnership | announced |
| Compute infrastructure (2) | Toubkal; Nexus AI Factory | operational; announced |
| Digital platform (1) | AI Marketplace (a catalogue of AI solutions, "not itself an AI system") | operational |

**Finding.** The topic qualifier "AI or computing" is accurate: every project is AI-related (institutes, AI
applications, an AI catalogue) or computing-related (data centres, HPC). My Sprint 05 note suggested Q8 might
overstate its topic; on inspection it does not. The overstatement is elsewhere:

- "documented … projects" can be read as projects documented as existing or delivered. In fact 8 of the 12 are
  announced only, one is unresolved, and the five institutes and agreements are signed commitments.
- One counted project is a catalogue platform, which the ontology says is not itself an AI system.

Nothing on the page disclosed either point.

**Resolution (narrowest accurate wording).**
- Question: "Which organisations are connected to the AI-related and computing projects recorded in this registry,
  and what establishes each connection?"
- A sentence computed from the data now states the kinds and stages counted ("4 AI applications, 3 institutes, 2
  agreements, 2 compute infrastructure, 1 digital platform. By stage: 8 announced, 3 operational, 1 unresolved"),
  that the digital platform is a catalogue rather than an AI system, and that no signature is documented by its
  signed text.

The scope is unchanged: no project kind was added or removed.

### B. Signed institutional relationships

**Count correction.** The brief, and my Sprint 05 report, spoke of nine "Signed" rows resting only on announcements.
The data has **ten**. "Nine" came from the clean-room agent's report and I relayed it without checking.

**A wider finding.** No `signatory_of` relationship in the registry cites the signed text:
- 10 Signed rows rest only on a news dispatch or a signatory's own press release (GAP-05);
- 6 rest on the First National AI Conference synthesis report (`official_report`, MAI-EV-0005/0006/0007), sometimes
  with a news dispatch.

`matrix.json` labelled those six `includes-formal-record`. The code comment called an official report "a formal
record of [the act]", while GAP-05's text equated "formal record" with "the signed text, founding act …", and the
matrix page said the instrument "is not recorded" only for the GAP-05 rows. Read together, these imply that the
other signatures have their instrument recorded. They do not.

| Relationship(s) | Evidence | What it establishes | Signed text? | VERIFIED FACT defensible? | Qualification | Missing evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 7 signatories (3 ministries, 4 universities) → JAZARI Industrie X.0 | MAI-EV-0009, Maroc.ma national portal news dispatch, 11 Mar 2026 | A convention "pour la création" of the institute was signed in Fès on 10 March 2026; it names all seven parties | No: a report of the signing | Yes: an official government source reports the act and names each party | The signing rests on a report; the text is not recorded; delivery is not documented; announcement-only (GAP-05) | The convention text; the institute's founding act |
| CGEM → Jazari ROOT | MAI-EV-0008, CGEM's own press release, 13 Jan 2026 | CGEM's president signed the constitutive convention of the GIP on 12 January 2026, "aux côtés de plusieurs départements ministériels" (not named, so not recorded) | No | Yes: a party's own account of its own act. It is first-party, not independent, and says nothing of the GIP's legal constitution (the note records that the Bulletin Officiel approval was not located) | As above | Convention text; Bulletin Officiel approval decision |
| DeepEcho and Ministry of Health → DeepEcho public-health evaluation | MAI-EV-0033, Maroc.ma news dispatch, 6 May 2026 | A partnership convention was signed at GITEX Future Health Africa, setting a framework for dissemination, adoption and clinical evaluation | No | Yes for the signing. The deployment is correctly an ANNOUNCED PLAN (`ministry-health operates`), and the article's FDA "approbation" is already corrected in the note | As above | Convention text; evidence that the evaluative study has started |
| 6 rows (ministries, UM6P → green data centres agreement, UM6P partnership, Nador institute) | MAI-EV-0005/0006/0007 ministry synthesis report, with MAI-EV-0019 news dispatch for some | The organiser's official report lists the signings | No: an official report of the signing | Yes | The signing rests on a report; the text is not recorded; delivery is not documented. Not GAP-05: they cite an official report | The agreement texts |

**Resolution.**
- **No classification changes.** Each signing is documented by an official or first-party public source, and the
  brief excludes downgrading for want of the agreement.
- **Presentation now separates a reported signing from an inspected agreement:**
  - Every "Signed" row carries: "The signing is documented by a report of it; the signed text is not recorded in
    this registry."
  - The matrix page states that this holds for all 16, naming the record types.
  - The Q8 answer states it as well.
- **The basis value `includes-formal-record` is renamed `includes-non-announcement-record`,** with a definition
  saying such a record is not the instrument. `matrix.json` publishes the old-to-new mapping (`renamed`) and the
  `assignment` of each value.
- **GAP-05 and the matrix page** no longer imply that the instrument is recorded outside GAP-05. GAP-05 now says
  the other relationships cite another kind of record, which for a signature is still a report of the signing.
- **New evidence type `signed_instrument`,** for a record of a signed text. It is unused. When such a record is
  cited, the caveat lifts mechanically (tested), so the distinction cannot silently go stale.

### C. Digital Morocco 2030 coverage

| Category | What the registry records |
| --- | --- |
| Published targets | MAI-EV-0002 (OFFICIAL TARGET, 2030): 240,000 direct jobs with a GDP contribution; digitalised public services; e-government index rank 113th → 50th |
| Recorded projects or initiatives | None `includes`. The First National AI Conference is `framed_by` the strategy (MAI-EV-0018); the strategy targets two sectors (OFFICIAL TARGET relationships) |
| Verified implementation | Launch on 25 September 2024 (MAI-EV-0001), which is an act, not implementation |
| Quantified progress against targets | None. MAI-EV-0003 is the Head of Government's statement that digital public investment rose from MAD 11 million (2021) to over MAD 1.7 billion (2024): an UNVERIFIED CLAIM, and spending is an input, not a target measure |
| Absence within this registry | Q9 said "Not yet assessed in the gap register" |

**Finding.** Morocco AI 2030 has the same limitation (targets, no measured progress) and is covered by GAP-02. Q9
therefore gave two different answers to the same evidentiary situation: "open gap" for one strategy, "not assessed"
for the other. That inconsistency is a methodological gap, not a symmetry preference. Q9 asks, for each official
target, which outcomes remain unverified, and for Digital Morocco 2030 it published no answer.

The registry does not hold, and this sprint did not add, any progress measurement. Absence in the registry is not
evidence that progress has not occurred, and GAP-06 states only what is recorded.

## Stage 2 — Gap methodology

Admission rule, now stated in `data/gaps.json`: a gap is opened when a reference question asks something the
records cannot answer. Every strategy with an official target has a gap on its measured progress, and the build
enforces it: a new validator rule names any initiative related to an OFFICIAL TARGET record that no gap covers. The
rule flagged exactly Digital Morocco 2030.

**GAP-06**, "What publicly documented measurements show progress toward the official targets of Digital Morocco 2030?":
- **Scope:** the strategy entity; assessed against its four existing records (0001, 0002, 0003, 0018).
- **Established:** the launch; the targets; the spending statement, labelled unchecked and an input; the
  conference framing.
- **Not established:** any measured progress on the four objectives.
- **Evidence needed:** official indicator reporting; the UN E-Government Survey rankings, which the ranking
  objective refers to; finance-law documents for the spending figures.
- **Checks:** none. Like GAP-02, the conclusion is an editor's judgment and is labelled so on `/data/` and in the
  consumer. The mechanical part is the fingerprint `995977d4b1f1ba0b` and `assessed_records`: any edit to these
  records, a new record about the strategy, or a changed relationship fails the build until the gap is re-assessed
  (tested).

**Not changed: JAZARI institutes.** The JAZARI institutes have the same delivery limitation as GAP-04's
infrastructure: signed conventions, no evidence of constitution or operation. No reference answer currently
reports them as unassessed, because Q2 shows their stage as announced. A gap would add symmetry rather than answer
an open question, so none was created. This is listed below as an owner decision.

## Stage 3 — Changes

| Change | Where |
| --- | --- |
| Q8 question wording; computed kinds, stages and signed-text sentence | `/registry/questions/` |
| Signed-text qualification on every Signed row; basis renamed, with `assignment` and `renamed`; qualification rules updated | `matrix.json`, `/registry/matrix/` |
| GAP-05 text; GAP-06; gap admission rule in the note | `data/gaps.json`, `/registry/gaps/`, `gaps.json` |
| Validator: progress gap required for every strategy with an official target | `tools/registry.py` |
| Evidence type `signed_instrument` (reserved; no record uses it) | `tools/registry.py`, manifest vocabularies |
| `/data/`: signed-text statement; Q9 reproducibility rows updated (GAP-02 and GAP-06 editorial; target-coverage rule) | `/data/` |
| Consumer reads basis names from `matrix.json` | `examples/registry_consumer.py` |
| Version 0.5.0; changelog entry (PR #7) with both corrections | `data/*.json`, `/methodology/` |

## Stage 4 — Verification

- **Gates:** validator 0 problems; 78 generated files, 0 stale; `check_site --network` 74 pages, 0 problems.
- **Tests:** **267** (252 before), all passing. `tests/test_precision.py` adds 15 tests:
  - signed-relationship basis distinctions: all 16 Signed rows carry the caveat; 10 announcement-only against 6
    official-report; a `signed_instrument` record would lift the caveat;
  - classifications and stages unchanged;
  - no published text implies a recorded instrument;
  - Q8 heading and scope disclosure match the data, with no kind filtered;
  - target and progress language, and the target-coverage rule;
  - GAP-06 separates spending from progress and is re-assessed when its data moves;
  - consumer compatibility: the consumer verifies v0.5.0, takes basis names from the data, rejects the v0.4.1 name
    clearly, and the vocabulary reserves `signed_instrument`.
- **Mutations:** **14 of 14 caught.**
  - generator: S01–S07;
  - validator: S08, S13;
  - data: S09, S10, S14;
  - consumer: S11, S12.
- **Determinism:** two rebuilds under different locale, time zone and hash seed leave 0 files differing.
- **Layout and accessibility:** 11 pages at 320, 375 and 1366 px, with fonts loaded and blocked: 0 overflow,
  0 WCAG 2 A/AA violations, no third-party requests.
- **Consumer:** `verify` reports OK for v0.5.0 with 6 gaps. Q9 shows Digital Morocco 2030 under GAP-06, labelled
  editorial assessment.
- **Compatibility with v0.4.1 tools:**
  - The v0.4.1 consumer exits 1 with 14 problems, each naming the renamed basis value.
  - The clean-room checker written against v0.4.1 fails 3 of 13 comparisons: the two matrix-row comparisons (the
    rename) and the qualifications (the new caveat).

  Both fail closed with explicit messages, so nothing passes silently. It is still a breaking change for v0.4.1
  consumers; see decision 1.

## Remaining evidence limitations

- No signed text is recorded for any of the 16 signatures. The convention texts, the institutes' founding acts and
  the Bulletin Officiel approval decisions have not been obtained.
- Measured progress on both national strategies rests on editorial gap assessments with no data check
  (GAP-02, GAP-06).
- The Digital Morocco 2030 spending figure remains an unchecked claim.
- All six gaps are open.

## Decisions for the owner

1. **Basis rename.** `includes-formal-record` → `includes-non-announcement-record` breaks consumers written against
   v0.4.1 (they fail closed). The alternative is to keep the old token and correct only its definition: no break,
   but the token keeps suggesting a recorded instrument. I implemented the rename; reverting it is a one-line change
   in the generator plus regeneration.
2. **JAZARI institutes delivery.** Should a gap cover the institutes' constitution and operation, parallel to
   GAP-04? I did not create one, because no reference answer currently leaves it unanswered.
3. **`signed_instrument`.** The type is reserved but unused. Please confirm that reading a signed text should be
   recorded this way when one is obtained. (The pre-merge review below now defines its admission rules.)

## Pre-merge compatibility review (owner request)

### 1–2. Breaking change and migration note

- **Where it is declared.** The rename of `matrix.json` `rows[].documentation_basis` from `includes-formal-record` to
  `includes-non-announcement-record` is now declared as a breaking change to the data contract in three places:
  - the manifest (`breaking_changes`: version, file, field, old, new, reason, consumer effect, migration);
  - `/data/` section 09, "Changes to the data contract";
  - the v0.5.0 changelog entry (`breaking_changes`, rendered on `/methodology/`).
- **What the note says:**
  - The rows the value covers are unchanged (14). Only the name changed, because the old one read as "the signed text
    is recorded".
  - The old value is accepted nowhere: there is no alias.
  - A v0.4.1 consumer fails closed. A test runs the v0.4.1 example consumer from `c621153` and confirms it exits 1
    with the documented message.
  - Migration: replace the literal, or read the names from `derivation.documentation_basis.assignment`.
- **Additive changes**, listed as such: a sentence added to the qualifications, GAP-06, and the
  `signed_instrument` vocabulary value.
- **Removed:** the interim `renamed` key in `matrix.json`, so that no mapping in a data file could be read as an alias.

### 3. `signed_instrument` admission

**Enforced by the validator:**
- the record is a VERIFIED FACT with `verification_status: verified`;
- its source type is a party or an official publisher (`government_publication`, `government_portal`,
  `signatory_organization`, `regulator`, `intergovernmental_organization`). News agencies, the press, repositories
  and lists are rejected;
- it carries an `instrument` field with `title`, `signed_on`, `signatories` (at least two, each among
  `related_entities`) and `access: full-text-read`;
- only such a record may carry `instrument`;
- a `signatory_of` relationship citing it must name one of its signatories;
- the Signed caveat lifts only for a subject listed among those signatories.

**Not enforceable mechanically, and stated as an editorial admission requirement** in the README and on `/data/`:
the registry must have read the signed text in full. A report, summary, press release or news item about the
signing never qualifies, even from a signatory or the government.

10 negative cases are tested. No record has this type.

### 4. JAZARI evidence audit

- **No implication of delivery or operation.** All five JAZARI institutes are `announced`, each status says operation
  or constitution is not verified, and their relationships are signatures (VERIFIED FACT, reported), composition
  (VERIFIED FACT, or ANNOUNCED PLAN for Smart City and EduTech) and stated technologies and sectors (ANNOUNCED PLAN).
- **The signed-text defect from Stage 1 recurred**, and is corrected:
  - the network's `status` said "Signed founding instruments are documented for JAZARI ROOT and JAZARI Industrie
    X.0";
  - the MAI-EV-0010 note said the registry "documents signed instruments";
  - the MAI-EV-0012 note and the Smart City and EduTech texts contrasted themselves with instruments that are not
    held.
- **The registry index** called JAZARI ROOT the network's "core institute". It now says "planned core institute",
  and the network "announced".
- **`morocco-ai-2030 implemented_through jazari-network`** (VERIFIED FACT, MAI-EV-0012) records the ministry's
  description of the roadmap's design. It read as "Documented" with no qualification. It now carries a note:
  implementation through the network is not documented. The classification is unchanged.
- **GAP-02 re-assessed.** The note touches Morocco AI 2030, so the build required it. The text is unchanged; the
  fingerprint is now `a0f5768748f67c38`.
- **No new gap.** No published answer leaves JAZARI delivery unassessed: Q2 shows every institute as announced.
  The parallel with GAP-04 remains an owner decision.

### 5. Re-run

- **Gates:** validator 0 problems; 78 generated files, 0 stale; `check_site --network` 74 pages, 0 problems.
- **Consumer:** `verify` OK on v0.5.0, 6 gaps.
- **Tests:** **271**, all passing.
- **Mutations:**
  - this review: 13 of 13 caught (R01–R13);
  - the Sprint 06 set re-run: 13 caught. S02 no longer applies, because its target line was rewritten; R06 tests the
    same behaviour.
- **Determinism:** two rebuilds under different locale, time zone and hash seed leave 0 files differing.
