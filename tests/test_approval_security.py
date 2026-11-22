"""Approval security (Sprint 19B-5; threat model in docs/TRANSLATION_APPROVAL_SECURITY.md).

Every reviewer, decision and approval below is SYNTHETIC and lives in a temporary directory. The tests check
that each threat the repository can control fails closed: replayed approvals, registry entries without an owner
decision, approvals before registration, CI with write access, drafts committed to the publicly served tree.
Run: python3 -m unittest discover -s tests
"""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_site  # noqa: E402
import i18n  # noqa: E402
from i18n_fixtures import SYNTHETIC_REVIEWERS, approval, register_reviewers  # noqa: E402
from test_i18n import TODAY, Fixture  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


class Replay(Fixture):
    def test_baseline_unit_is_valid(self):
        self.with_units([self.message_unit()])
        self.assertEqual(self.validate()[0], [])

    def test_approval_copied_to_another_unit_is_rejected(self):
        # Same English text and same translation, so both fingerprints match: only the unit binding differs.
        source = self.en["footer.as_of"]
        replayed = approval(source, "بتاريخ {date}", "footer.as_of", "ar")
        self.with_units([self.message_unit(), self.message_unit(uid="footer.as_of", approval=replayed)])
        unit = self.message_unit(approval=dict(replayed, unit="footer.registry_version"))
        self.with_units([unit])
        self.assertRejected("an approval cannot be reused")

    def test_approval_copied_to_another_language_is_rejected(self):
        self.with_units([self.message_unit(approval=approval(self.en["footer.as_of"], "بتاريخ {date}", "footer.as_of", "fr"))])
        self.assertRejected("names language 'fr', not 'ar'")

    def test_approval_without_binding_is_rejected(self):
        self.with_units([self.message_unit(approval=approval(self.en["footer.as_of"], "بتاريخ {date}"))])
        self.assertRejected("an approval cannot be reused")

    def test_replayed_approval_is_never_renderable(self):
        self.with_units([self.message_unit(approval=approval(self.en["footer.as_of"], "بتاريخ {date}", "footer.time", "ar"))])
        self.assertEqual(i18n.renderable_texts("ar", self.root, self.evidence, self.ontology, self.gaps, today=TODAY), {})


class RegistryAuthorization(Fixture):
    def registry(self, **over):
        entry = dict(SYNTHETIC_REVIEWERS[0], **over)
        for k in [k for k, v in over.items() if v is None]:
            entry.pop(k)
        register_reviewers(self.root, [entry] + SYNTHETIC_REVIEWERS[1:])
        if "id" in over:  # keep the synthetic decision naming the original ids only
            log = self.root / "docs" / "DECISION_LOG.md"
            log.write_text(log.read_text(encoding="utf-8").replace(over["id"], SYNTHETIC_REVIEWERS[0]["id"]), encoding="utf-8")

    def test_synthetic_registry_is_valid(self):
        self.assertEqual(self.validate()[0], [])

    def test_registration_needs_an_owner_decision(self):
        self.registry(authorized_by=None)
        self.assertRejected("authorized_by must name the owner decision")

    def test_registration_cannot_cite_an_unknown_decision(self):
        self.registry(authorized_by="TMA-DEC-999")
        self.assertRejected("is not an accepted decision")

    def test_registration_cannot_cite_a_decision_that_does_not_name_the_reviewer(self):
        self.registry(id="reviewer-fr-09")
        self.assertRejected("does not name this reviewer id")

    def test_a_real_decision_cannot_be_reused_to_register_someone(self):
        # TMA-DEC-008 is accepted but registers nobody: citing it for a reviewer fails.
        (self.root / "docs" / "DECISION_LOG.md").unlink()  # fall back to the repository's real decision log
        register_reviewers(self.root)
        (self.root / "docs" / "DECISION_LOG.md").unlink()
        reg = json.loads((self.root / "i18n" / "reviewers.json").read_text(encoding="utf-8"))
        for r in reg["reviewers"]:
            r["authorized_by"] = "TMA-DEC-008"
        (self.root / "i18n" / "reviewers.json").write_text(json.dumps(reg), encoding="utf-8")
        self.assertRejected("decision TMA-DEC-008 does not name this reviewer id")

    def test_unaccepted_decision_is_not_an_authorization(self):
        log = self.root / "docs" / "DECISION_LOG.md"
        log.write_text(log.read_text(encoding="utf-8").replace("Decision status: Accepted", "Decision status: Proposed"), encoding="utf-8")
        self.assertRejected("is not an accepted decision")

    def test_registration_date_is_required_and_not_in_the_future(self):
        self.registry(registered_on=None)
        self.assertRejected("registered_on must be a date")
        self.registry(registered_on="2027-01-01")
        self.assertRejected("registered_on is in the future")

    def test_approval_before_registration_is_rejected(self):
        self.registry(registered_on="2026-11-21")  # the synthetic approval is dated 2026-11-20
        self.with_units([self.message_unit()])
        self.assertRejected("precedes the reviewer's registration")

    def test_personal_data_and_automated_identities_stay_rejected(self):
        self.registry(email="someone@example.com")
        self.assertRejected("unexpected fields")
        self.registry(id="claude-reviewer-01")
        self.assertRejected("cannot be registered as a reviewer")


class RepositoryState(unittest.TestCase):
    def test_no_reviewer_is_registered_and_no_decision_registers_one(self):
        self.assertEqual(json.loads((REPO / "i18n" / "reviewers.json").read_text(encoding="utf-8"))["reviewers"], [])
        for dec, body in i18n.accepted_decisions(REPO).items():
            self.assertNotRegex(body, r"\breviewer-[a-z]{2}-\d+\b", dec)

    def test_no_committed_catalog_holds_an_approval(self):
        for path in sorted((REPO / "i18n").glob("*/content.json")) + sorted((REPO / "i18n").glob("*/messages.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(any("approval" in u for u in data.get("units", [])), path)
        glossary = json.loads((REPO / "i18n" / "glossary.json").read_text(encoding="utf-8"))
        self.assertFalse(any(t.get("translations") for t in glossary["terms"]))


class CiCannotApprove(unittest.TestCase):
    def test_workflows_have_read_only_contents_permission(self):
        for wf in sorted((REPO / ".github" / "workflows").glob("*.y*ml")):
            text = wf.read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$", wf.name)
            self.assertNotRegex(text, r":\s*write\b", wf.name)
            self.assertNotIn("pull_request_target", text, wf.name)
            self.assertNotRegex(text, r"git (?:commit|push)", wf.name)

    def test_codeowners_cover_the_approval_metadata(self):
        owners = (REPO / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        rules = dict(line.split(None, 1) for line in owners.splitlines() if line.strip() and not line.startswith("#"))
        for path in ("/i18n/", "/tools/i18n.py", "/docs/DECISION_LOG.md", "/docs/TRANSLATION_REVIEW_POLICY.md", "/.github/"):
            self.assertEqual(rules.get(path, "").strip(), "@Sohadot", path)


class DraftIsolation(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(REPO / "i18n", self.root / "i18n")
        shutil.copytree(REPO / "data", self.root / "data")  # read-only sources for fingerprints

    def test_unexpected_files_in_i18n_are_rejected(self):
        for rel in ("ar/drafts.json", "fr/review.html", "drafts/fr.json"):
            path = self.root / "i18n" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
        errors, _ = i18n.validate(self.root, today=TODAY)
        for rel in ("ar/drafts.json", "fr/review.html", "drafts/fr.json"):
            self.assertTrue(any(e.startswith(f"i18n/{rel}: unexpected file") for e in errors), (rel, errors))

    def test_draft_status_cannot_be_committed(self):
        cat = {"language": "fr", "units": [{"id": "footer.as_of", "kind": "interface", "status": "DRAFT", "text": "au {date}",
                                            "source_sha256": i18n.fingerprint(i18n.english_messages()["footer.as_of"]),
                                            "draft": {"method": "machine-assisted", "by": "ai-draft-01"}}]}
        (self.root / "i18n" / "fr" / "messages.json").write_text(json.dumps(cat), encoding="utf-8")
        errors, _ = i18n.validate(self.root, today=TODAY)
        self.assertTrue(any("drafts stay off main" in e for e in errors), errors)

    def test_draft_marker_anywhere_in_the_site_fails_the_site_gate(self):
        self.assertEqual(i18n.DRAFT_MARKER, "themoroccoai-" + "translation-draft")
        original = check_site.ROOT
        site = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, site)
        (site / "drafts").mkdir()
        (site / "drafts" / "review.html").write_text(f'<meta name="workspace" content="{i18n.DRAFT_MARKER}">', encoding="utf-8")
        (site / "notes.md").write_text("nothing to see", encoding="utf-8")
        check_site.ROOT = site
        self.addCleanup(setattr, check_site, "ROOT", original)
        errors = check_site.check_draft_leaks()
        self.assertEqual(len(errors), 1)
        self.assertIn("drafts/review.html", errors[0])

    def test_repository_carries_no_draft(self):
        self.assertEqual(check_site.check_draft_leaks(), [])
        self.assertFalse([p for p in REPO.rglob("*.json") if ".git" not in p.parts and "tests" not in p.parts
                          and re.search(r'"status":\s*"(DRAFT|NEEDS_REVISION|REJECTED)"', p.read_text(encoding="utf-8", errors="ignore"))])


if __name__ == "__main__":
    unittest.main()
