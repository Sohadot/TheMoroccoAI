# Source intelligence: watchlist, change detection and controlled admission (Sprint 30)

| | |
|---|---|
| Tool | `tools/observatory.py` (standard library). It reuses `tools/check_sources.py` for retrieval, block and error classification and excerpt matching |
| Public definition | `sources/watchlist.json` (schema 1.0): sources the registry already cites |
| Staging store | **Outside the repository**: `$THEMOROCCOAI_OBSERVATORY`, by default `~/.themoroccoai-observatory` |
| Tests | `tests/test_observatory.py` (offline, synthetic fixtures) |
| Public site | **Unchanged.** No dashboard, no candidate content and no new page |

## 1. Three things kept apart

```
Watched source ──observe──► Observation ──compare──► Change ──detect──► Candidate ──human review──► Accepted for admission
 (watchlist)                 (staging)                (staging)          (staging)                       │
                                                                                                         ▼ propose (draft only)
Published reference change ◄── tools/changes.py ◄── data/ commit in a reviewed PR ◄── Draft evidence record (staging)
```

1. **A source page changed:** an observation and a comparison.
2. **A claim about the world may have changed:** a candidate, reviewed by a person.
3. **The registry admitted verified knowledge:** a person commits a record to `data/` in a reviewed pull request. Sprint 29's `/registry/changes/` then shows it as `evidence.added`, and the record's `source_url` and `retrieval_date` link back to the observation.

No stage writes to the next stage's store. Nothing is promoted automatically.

## 2. The watchlist

`sources/watchlist.json` holds **only sources the registry already cites**. The validator requires each entry to list the evidence records whose `source_url` it is.
- **Not a target list:** it is a list of the registry's own sources, and inclusion implies no relationship with the publisher. Any other field is rejected, so nothing like a priority or contact field can be added.
- **Entry fields:** id, name, URL, category (a registry source type), language, research relevance, records, entities, method, frequency, access rules, status (`active`, `paused` or `retired`, with a reason) and optional `ignore_patterns` for known counters.
- **Last observation:** the time of the last successful observation is reported from the staging store and is not written back into the watchlist, so observing does not churn the repository.

**Pilot (15 sources, 12 active).** These are living pages whose changes can affect existing records:
- the ministry's AI Marketplace;
- the Idarati portal and assistant;
- four Hugging Face model and dataset cards;
- AtlasIA, DeepEcho, AIOX Labs and INSEA;
- the CNDP's Law 09-08 page;
- three paused sources: TOP500 and UN DESA, whose robots.txt disallows this observer, and the FDA database, which answers automated requests with HTTP 400.

Frozen sources (news articles, PDFs) are re-checked by `tools/check_sources.py`, not watched here.

## 3. Observation and change detection

- **Retrieval:**
  - robots.txt is checked before every request, and a disallowed source is never requested;
  - at most one request per host every 2 seconds;
  - 30-second timeout and size cap (from `check_sources`);
  - no login, paywall or challenge is bypassed.
- **Outcomes:** `retrieved`, `blocked`, `http-error`, `unreachable`, `robots-disallowed`, `unreadable-format` (PDF or non-HTML).
  - A failure is never a change and never a disappearance; the comparison is `not-comparable`.
  - Three consecutive failures make a source `unreliable`.
- **What is kept:**
  - normalised visible text blocks in document order (scripts, styles and repeats removed; times, timestamps, long tokens and copyright years masked);
  - SHA-256 of the raw body and of the text;
  - redirects and encoding problems;
  - where each excerpt of the citing records was found.

  The raw page is not kept.
- **Comparison results:** `first-observation`, `unchanged`, `formatting-only` (raw changed, text did not), `reordered`, `substantive` (lists of added and removed text), `not-comparable`.
- **Reassessment signal:** an excerpt of a citing record that is found neither in the visible text, the raw source nor the page's own same-host scripts. This uses the same rule as `check_sources`. It is a signal for a person, not a finding.

## 4. Candidates (staging only)

**What becomes a candidate.** A substantive addition becomes a candidate only if it mentions a registry entity (by name or alternative name) or AI.

**Candidate fields:**
- a deterministic id (`CAND-` plus a hash of the source and the text): the same text from the same source is one candidate, however often it is seen;
- source, URL and observation time;
- the excerpt in its original language, and that language (ar, fr, en or und);
- related entities and significance;
- the records whose excerpts it repeats (`duplicate_of_evidence`);
- `duplicate_of_candidate` and `supersedes`;
- notes and the full decision history.

**States.** States describe the review, never the truth of the claim.

| From | To |
|---|---|
| detected | awaiting_review, duplicate (automated triage only) |
| awaiting_review | under_verification, rejected, duplicate, deferred |
| under_verification | needs_additional_evidence, accepted_for_admission, rejected, duplicate, deferred |
| needs_additional_evidence | under_verification, rejected, deferred |
| deferred | awaiting_review |
| accepted_for_admission, rejected, duplicate | (final) |

**Who may move a candidate.** Automated triage only queues candidates or marks exact repeats. Every other move needs a pseudonymous human reviewer and a note. Automated identities (`ai`, `bot`, `claude`, `observatory`…) are refused.

## 5. Verification and admission

The reviewer checks ten points:
1. provenance and accessibility;
2. relevance to Moroccan AI;
3. claim accuracy and wording;
4. publication and observation dates;
5. entity identification;
6. overlap with existing evidence;
7. contradicting or superseding evidence;
8. classification and uncertainty;
9. ontology or gap updates;
10. validation.

Then `propose` prepares a **draft** record. It does so only:
- for a candidate `accepted_for_admission`;
- for a human reviewer;
- with excerpts quoted **verbatim** from the observed page, in their original language (an AI summary is refused);
- with every decision field set by the reviewer.

It assigns the next `MAI-EV` id and takes `retrieval_date` from the observation. It then runs the registry validator on a copy with the draft added and returns the problems still to resolve. It writes the draft to the staging store, **never to `data/`**.

Admission itself is a reviewed pull request: add the record, link it from entities or gaps, bump the version and add a changelog entry.

## 6. Running it

```
export THEMOROCCOAI_OBSERVATORY=~/.themoroccoai-observatory   # outside the repository (enforced)
python3 tools/observatory.py validate            # also run by the test suite in CI
python3 tools/observatory.py observe             # all active sources; --source SRC-001 for one
python3 tools/observatory.py report              # changed, unreliable, reassessment signals, candidates by state
python3 tools/observatory.py candidates
python3 tools/observatory.py review CAND-… --to under_verification --by reviewer-owner-01 --note "Checking the ministry release."
python3 tools/observatory.py propose CAND-… --decision decision.json   # decision.json includes "reviewer"
```

**Failures:**
- an `unreachable` or `http-error` result is retried at the next observation;
- `unreliable` after three failures means checking by hand (moved, renamed, or blocking automated clients);
- `robots-disallowed` sources are paused, with the reason.

**Cost:** one pass over the 12 active sources takes about 40 seconds and a few hundred KB of staging data. No paid service is used.

## 7. Confidentiality

- **The repository is public.** Only the watchlist is committed.
- **Staging stays outside the repository.** Observations, candidates, review notes and proposals stay there.
  - Each staging file carries a marker that `tools/check_site.py` rejects anywhere in the repository.
  - `store_dir` refuses a path inside it.
- **No GitHub staging.** GitHub Issues, Actions logs and artifacts are **not** used for staging. In a public repository, issues are public and workflow artifacts can be downloaded by any signed-in GitHub user.
- **Activation stays manual.** A scheduled GitHub Action is therefore not recommended for observation. Run it on the owner's own machine, or on private infrastructure the owner controls.

## 8. Pilot results (2026-11-23, two passes)

| Result | Sources |
|---|---|
| Retrieved, text unchanged | ai.mmsp.gov.ma, idarati.ma, chatbot.idarati.ma, atlasia.ma, deepecho.io, aiox-labs.com, insea.ac.ma |
| Retrieved, formatting-only (raw HTML changed, text not) | the four Hugging Face cards |
| Unreachable from this environment (not treated as removed) | cndp.ma |
| Paused by policy | TOP500, UN DESA (robots.txt), FDA (HTTP 400 to automated clients) |

- **Candidates: none.** No source changed between passes, so there was no candidate and no admission.
- **One reassessment signal (left for review, data unchanged):** one of the four excerpts of **MAI-EV-0038** (chatbot.idarati.ma) is no longer found in the page or its scripts. `tools/check_sources.py` reports the same.

## 9. Issue #29

| Item | Status |
|---|---|
| 2. Source watchlist schema, 5–10 justified sources | Done: 15 cited sources, 12 active |
| 3. Candidate records distinct from verified evidence | Done: staging only, states and history |
| 4. Offline, fixture-tested change detection | Done (formatting vs substance, failures, duplicates) |
| 5. Review workflow; public change log only for admitted evidence | Done: workflow here; public log is Sprint 29 |
| 6. Tests | Done: 23 tests |
| External outreach | Not done: no question here needs it |

## 10. Deferred

- Scheduled observation (needs private infrastructure, per §7).
- PDF watching.
- Rendering JavaScript-only pages.
- A reviewer interface beyond the CLI.
- Publishing candidates.
- Multilingual presentation of observations.

Excerpts keep their original language, and nothing is translated.
