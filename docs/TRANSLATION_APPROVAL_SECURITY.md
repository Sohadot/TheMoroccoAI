# Translation approval security

| | |
|---|---|
| Policy | [TMA-DEC-008](TRANSLATION_REVIEW_POLICY.md): one documented human approval, escalated to a second registered reviewer when a criterion applies |
| Scope | Who may approve, how an approval is recorded, and what the repository can and cannot prove about it (Sprint 19B-5) |
| Current state | **No reviewer is registered. No approval exists. No localized page is published.** |

Status words in this document:
- **Implemented and tested:** enforced by code in this repository, with a test that fails if the control is removed.
- **Requires a GitHub setting:** enforced only when the owner configures it on GitHub. Not verifiable from this repository.
- **Procedure:** a documented practice that no code enforces.

## 1. The finding that shapes everything else

Commits and pull requests made by the AI coding agent on this repository appear under the owner's GitHub account. (For example, PR #23 was opened by the agent and shows the owner as its author.) Consequences:
- **GitHub cannot tell an AI commit from an owner commit.** The repository alone cannot prove that a human approved a translation.
- **Code-owner review is weak here.** The owner cannot approve a pull request opened in their own name, so required code-owner review either blocks every such pull request or is bypassed by the owner.
- **The `reviewer` field proves nothing.** It is an attestation that anyone with write access could type.

The design therefore does not rely on account identity. It relies on four things:
1. **Exact binding.** An approval names the unit, language, English source fingerprint, translation fingerprint and the warnings shown. A copied, edited or replayed approval is rejected.
2. **Owner-only steps the agent never performs:**
   - registering a reviewer, through a new accepted decision in [DECISION_LOG.md](DECISION_LOG.md);
   - exporting decisions from the review package;
   - making the approval commit.
3. **Evidence of who made the approval commit.** The strongest evidence is a signature by a key only the owner holds (Section 4).
4. **Fail-closed publication.** Anything that does not validate is not rendered.

## 2. Threat model

| Threat | Preconditions | Mechanism | Existing control | Residual risk | Mitigation | Verification | GitHub-dependent |
|---|---|---|---|---|---|---|---|
| **A. Fabricated approval** | Write access, as the agent has | An agent writes an approval record claiming the owner reviewed a translation | The reviewer must be registered by an accepted owner decision; a replayed record is rejected (unit, language, fingerprints, warnings); validation, the build and CI never write approvals; `record` refuses CI; the agent's instructions forbid it | An actor with write access can still write a complete, valid-looking record for a registered reviewer | The owner makes approval commits personally, signed with an owner-held key; the PR states it; `provenance` shows the commit and signature status for every approval | `test_approval_security`, `test_governance`, `test_review_workflow.test_a_successful_ci_run_cannot_record_an_approval` | Partly: signature requirement |
| **B. Reviewer impersonation** | A registered reviewer id exists | Someone uses that id without the reviewer's authorization | Ids are pseudonymous and registered only by an owner decision; no personal data | The id is not a credential: nothing in the file proves who typed it | One reviewer id per real person, used only in approval commits that person signs | `test_approval_security.RegistryAuthorization` | Yes: commit signature |
| **C. Unauthorized registry change** | Write access | A PR adds a reviewer to make its own translations look approved | `authorized_by` must cite an **accepted** decision that **names the id**; no existing decision names a reviewer; registration date required; approvals before registration rejected; automated identities and personal fields rejected | A PR could also add a fabricated decision entry | `CODEOWNERS` covers `i18n/` and `docs/DECISION_LOG.md`; the owner reads every decision-log change; branch protection | `RegistryAuthorization`, `RepositoryState`, `test_codeowners_cover_the_approval_metadata` | Yes: CODEOWNERS only with branch protection |
| **D. Approval replay** | A valid approval exists | The approval is copied to another unit, language, source version or text | The approval names `unit` and `language`, and both fingerprints must match | None known within the repository | — | `test_approval_security.Replay`, `test_governance` (foreign source, different translation) | No |
| **E. Approval laundering** | CI, a merge or an automation | A passing check, a commit or a merged PR is treated as approval | Approval exists only as a complete record; CI has `contents: read` only, no push step and no `pull_request_target`; `record` refuses to run when `CI` or `GITHUB_ACTIONS` is set; merging does not change any approval field | A future workflow could be given write access | Tests fail if any workflow gains write permission or a push step; `.github/` is code-owned | `CiCannotApprove`, `test_validation_and_build_never_write_approvals` | Partly |
| **F. Stale approval** | An approved unit | The English source or the approved text changes after approval | Both fingerprints are checked at validation and at render time; a stale unit is withdrawn with no grace period; changed semantic warnings make the unit unacknowledged and withdrawn | None known | — | `test_review_workflow.test_complete_lifecycle`, `test_governance`, `test_semantic.Eligibility` | No |
| **G. Branch-protection bypass** | Admin or direct push rights | Review metadata is changed on `main` without the owner's review | Direct pushes are a GitHub setting; the repository cannot block them | Without branch protection, anyone with push rights can change `main` | Configure the rules in Section 4 | Not verifiable from the repository: the owner checks the settings | **Yes** |
| **H. Public exposure** | Drafts or review notes exist | A draft, review package, reviewer identity or note is committed; every file on `main` is publicly served | Drafts and packages carry a workspace marker and `check_site` fails if it appears in the repository; `i18n/` accepts only its known files; catalogs accept only `APPROVED` units; `load_drafts` and `package` refuse paths inside the repository; reviewer entries reject personal fields | A draft pasted into an unmarked file elsewhere would not be detected; a hidden folder is still served | Keep drafts in the owner's private storage; the package says so on its first screen | `test_approval_security.DraftIsolation`, `test_review_workflow.Package` | No |

Not claimed:
- No repository file proves human identity cryptographically.
- No code here can enforce GitHub account permissions.
- Commit signature status is evidence of which key signed. It is not proof of who reviewed.

## 3. Owner approval workflow

There are six separate events, and none implies the next:

| # | Event | Who | Artifact | Where it lives |
|---|---|---|---|---|
| 1 | AI draft preparation | AI tool (`ai-draft-01`) | Draft workspace JSON (`status: DRAFT`, `draft.method: machine-assisted`) | Owner's private storage, never the repository |
| 2 | Automated verification | `tools/translation_review.py check` | Problems (blocking) and semantic findings (errors block; warnings inform) | Terminal output |
| 3 | Human editorial review | Owner | Review package HTML: English source, draft, source reference, glossary concepts, findings, fingerprints, status; nothing preselected | Owner's private storage |
| 4 | Final approval | Owner | Exported decisions JSON, then `record`, which writes approval records bound to the exact text; the owner commits them, signed | The decisions stay private; the approval commit goes to a PR |
| 5 | GitHub merge | Integration reviewer | Merge of the approval PR: a merge control, not an approval | `main` |
| 6 | Public publication | Owner decision | Language `published` in `i18n/languages.json` and the page added to `LOCALIZABLE_PAGES`, in its own PR | `main` |

Steps for the owner:
1. Open the review package in a browser. For each unit, read the English source and the draft, check the source reference and the findings, then choose a decision:
   - **approve:** approves the final text shown, which you may edit;
   - **request revision:** the unit stays a draft;
   - **reject;**
   - **specialist question:** choose an escalation criterion.
2. Export your decisions (`review-decisions.json`). Only decided units are exported.
3. On your own computer, run:

   ```
   python3 tools/translation_review.py record review-decisions.json --drafts pilot-ar.json pilot-fr.json --reviewer <your reviewer id>
   ```

   `record` refuses anything that does not match what you were shown:
   - a changed draft or source;
   - a semantic error;
   - a corrected text whose warnings you were not shown (rebuild the package and review again).

   It writes only approved units into `i18n/<lang>/*.json` and changes nothing if any decision fails.
4. Review the diff and commit it yourself with a signed commit (`git commit -S`). Open the PR and say in it that you made the approval.
5. Run `python3 tools/translation_review.py provenance` to list each approval with its commit and signature status.

A unit you corrected is recorded with `approval.revised: true`, and the AI drafter stays recorded as the drafter. That is review, not self-approval of your own draft.

## 4. GitHub settings that require the owner

These settings could not be inspected or changed with the tools available to the agent. Configure them under **Settings → Rules → Rulesets** (or **Branches → Branch protection rules**) for `main`:

1. **Require a pull request before merging.** Block direct pushes to `main`, including for administrators if possible.
2. **Require status checks to pass:** the `checks` job of `.github/workflows/quality.yml`.
3. **Require signed commits.** Add your own SSH or GPG signing key under **Settings → SSH and GPG keys** and enable *Vigilant mode*, so that unsigned commits under your name show as *Unverified*. Do not give the agent your signing key.
4. **Code owners:**
   - `.github/CODEOWNERS` assigns `i18n/`, `tools/i18n.py`, `docs/DECISION_LOG.md`, the translation policies and `.github/` to `@Sohadot`.
   - *Require review from Code Owners* is useful only if pull requests are opened under a different account from yours. Under the current setup, the agent acts under your account, so treat CODEOWNERS as a reminder rather than a gate.
   - If you want it to be a real gate, give the agent its own GitHub account or app identity. Your code-owner review then becomes a distinct, attributable act.
5. **Restrict workflow permissions.** Under **Settings → Actions → General**, set *Workflow permissions* to *Read repository contents*. The tests already fail if a workflow in the repository requests write access.

## 5. Registering a reviewer (owner only)

The registry `i18n/reviewers.json` is empty and stays empty until the owner decides otherwise. Registering yourself as the pseudonymous Arabic and French reviewer:

1. **Choose a pseudonymous id,** for example `reviewer-owner-01`. It must not contain your name, an e-mail address, or words that denote an automated identity (`ai`, `bot`, `ci`, `claude`, `gpt`, `model`, …).
2. **Record the decision.** Add a new entry to [DECISION_LOG.md](DECISION_LOG.md):

   ```
   ## TMA-DEC-009 — Registration of reviewer-owner-01
   - Date: <today>
   - Domain: Translation review governance
   - Decision status: Accepted (project owner)
   - Decision: Registers reviewer-owner-01, the project owner, as a human reviewer for ar and fr under TMA-DEC-008.
   ```

3. **Add the registry entry** to `i18n/reviewers.json`:

   ```json
   {"id": "reviewer-owner-01", "kind": "human", "languages": ["ar", "fr"], "authorized_by": "TMA-DEC-009", "registered_on": "<today>"}
   ```

4. **Commit both changes yourself, signed,** in a PR that does nothing else. Validation fails if the decision is not accepted, does not name the id, or is missing.

Rules:
- Registration says who **may** approve. It is not a review, and it approves nothing.
- History is preserved. Remove a reviewer by a later decision and a registry change; past approvals then fail validation and are withdrawn until they are re-approved.
- The agent does not perform this registration.

## 6. What is implemented, tested, designed or external

| Item | State |
|---|---|
| Approval binding to unit, language, fingerprints and acknowledged warnings | Implemented and tested |
| Reviewer registration tied to an accepted, naming decision and a registration date | Implemented and tested |
| `record`: refusal in CI, exact-text binding, roll-back | Implemented and tested |
| Draft isolation (workspace marker, `i18n/` file allow-list, path refusal) | Implemented and tested |
| Read-only CI, no push step | Implemented and tested (repository side) |
| `CODEOWNERS` | Implemented; **effective only with GitHub settings** |
| Branch protection, signed commits, workflow permission setting | **Owner action on GitHub** (Section 4) |
| Approval commit signature | **Procedure**; `provenance` reports it, advisory |
| Human identity of a reviewer | **Not provable** by this repository |
