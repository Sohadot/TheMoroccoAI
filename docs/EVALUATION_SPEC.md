# Independent Research Evaluation — implementation specification v1.0

Status: First implementation in PR #14; deployment, accessibility review and external validation pending.
Language: English (authoritative).
Public route: `/evaluation/`.
Scope: research usability and evidence interpretation, not factual certification of Morocco's AI ecosystem.

## Architecture
Initial implementation reuses the existing generated-page shell but keeps `/evaluation/index.html` hand-maintained, outside the registry generator. The HTML is committed for GitHub Pages; consider integrating into `tools/build.py` after release validation. Add a quiet homepage link. If lightweight client-side JS is needed for optional response drafting/copying, serve it locally, without external requests or analytics. Update README to disclose this scoped exception to the present no-runtime-JavaScript design.

## Introductory evaluation (~5 minutes)
Prompt: “Find one AI-related initiative in the registry. Identify a supporting source and explain what the source establishes and what it does not establish.”
After the task, ask separately: (1) What did you find? (2) Which evidence identifier or source URL did you use? (3) What was difficult, unclear, or missing? (4) How easy or difficult was the task? Use a balanced five-point scale plus “Prefer not to answer”.
No suggested entity, source, answer, deep link or preselected rating.

## Specialist evaluation (~15–20 minutes)
Three sequential tasks, with neutral entry via registry navigation:
1. Trace a claim to its supporting evidence, describe the source and classification.
2. Find an official target and investigate whether the available evidence establishes achievement; report uncertainty without pressure to infer an outcome.
3. Find an open evidence gap and explain what evidence would resolve it.
For each: finding, evidence identifier/source, unresolved limitation, navigation difficulty, optional free-text feedback. Do not use fixed example records or reveal expected conclusions.

## Response handling and consent
No account, tracking cookies, screen recording, fingerprinting, background submission, localStorage or third-party forms. Draft responses in memory only. “Prepare report” creates selectable plain text after a direct user action; no clipboard permission or automatic copying is required. Explicitly say copying does not submit the response. Optional email to `agent@sohadot.com` must be initiated by the participant and disclose that email may expose sender identity; no automatic email sending. Do not request names, employer, contact details or sensitive information in evaluation prompts. Provide an obvious clear/reset control.
No claim of anonymity if a participant elects to email a report. Define a retention/deletion process before collecting responses.

## Neutrality and integrity
Keep answer keys and internal scoring guidance outside the public repository and published assets. Do not show correct/incorrect messages, score, hints, selected record suggestions, answer-prefilled links or source-specific prompts. Neutral task language must not imply that a target was achieved or that a gap proves absence. Completion counts are not validation; published claims require explicit methodology and independently reviewable evidence.

## SEO and accessibility
Use a canonical URL, OG metadata, `<meta name="robots" content="noindex, follow">`, and a sitemap exclusion supported by explicit tests. Do not block the page in robots.txt. One H1; labelled controls, keyboard operability, focus visibility, accessible status messages, responsive layouts, no mandatory timer. Preserve the current independence disclaimer and avoid official-status implication.

## Quality gates
- `python3 tools/build.py` and `python3 tools/build.py --check`
- `python3 tools/check_site.py`
- `python3 -m unittest discover -s tests`
- Verify navigation, canonical/OG consistency, noindex and sitemap exclusion.
- Negative tests for third-party requests, unconsented storage, leaked answer keys and accidental auto-submission.
- Manual mobile, keyboard and screen-reader checks.
- No changes to canonical evidence, ontology, gaps, reference-state contract or research classifications.
- PR review and passing CI before merge.
