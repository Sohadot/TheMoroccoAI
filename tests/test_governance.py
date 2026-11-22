"""TMA-DEC-008 approval governance, end to end on the real /registry/ page.

Each test breaks one property of a human approval and checks that the localized page is not generated, is absent
from hreflang and the switcher, and that the English page is unaffected. All localized text, reviewers and
approvals are SYNTHETIC, created in temporary directories, never committed and never real approvals.
Run: python3 -m unittest discover -s tests
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import i18n  # noqa: E402
from i18n_fixtures import approval  # noqa: E402
from test_extraction import REGISTRY, TODAY, ExtractedRegistryFixture  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
UNIT = "page.registry.legend.note"  # a qualifier: approval failures on it must block the page


class ApprovalGovernsPublication(ExtractedRegistryFixture):
    def set_approval(self, lang="fr", uid=UNIT, **over):
        src, text = self.source(uid), self.text(uid, lang)
        self.edit_unit(lang, uid, approval=approval(src, text, uid, lang, **over))

    def assertWithheld(self, fragment, lang="fr"):
        files, clusters, report = self.localize()
        self.assertNotIn(f"{lang}/registry/index.html", files)
        self.assertNotIn(lang, clusters.get("/registry/", []))
        self.assertTrue(any(fragment in r for r in report), report[:3])
        for html in files.values():
            self.assertNotIn(f'hreflang="{lang}"', html)
        with build.rendering(build.RenderContext("en", self.root, today=TODAY)):
            self.assertEqual(REGISTRY.render(self.model), (REPO / "registry" / "index.html").read_text(encoding="utf-8"))

    def test_baseline_fixture_publishes(self):
        files, clusters, report = self.localize()
        self.assertEqual(report, [])
        self.assertIn("fr/registry/index.html", files)
        self.assertIn("shell.translation_policy", build.LOCALIZATION_ONLY_MESSAGES)
        policy = build.escape(self.text("shell.translation_policy", "fr"), quote=False)
        self.assertIn(policy, files["fr/registry/index.html"])  # the public translation-policy disclosure

    # 14 (stale) and 18 (approval for a different source fingerprint)
    def test_stale_or_foreign_source_approval(self):
        self.edit_unit("fr", UNIT, source="an English text that has since changed")
        self.assertWithheld(UNIT)
        self.set_approval(source_sha256=i18n.fingerprint("another English text"))
        self.assertWithheld(UNIT)

    # 15
    def test_missing_human_approval(self):
        self.edit_unit("fr", UNIT, approval=None)
        self.assertWithheld(UNIT)
        for status in ("DRAFT", "NEEDS_REVISION", "REJECTED"):
            self.edit_unit("fr", UNIT, status=status)
            self.assertWithheld(UNIT)

    # 16
    def test_ai_self_approval_attempt(self):
        for reviewer in ("claude-code-01", "ai-translator-01", "synthetic-drafter-01"):
            self.set_approval(reviewer=reviewer)
            self.assertWithheld(UNIT)
        reg = json.loads((self.root / "i18n" / "reviewers.json").read_text(encoding="utf-8"))
        reg["reviewers"].append({"id": "claude-reviewer-01", "kind": "human", "languages": ["fr"]})
        (self.root / "i18n" / "reviewers.json").write_text(json.dumps(reg), encoding="utf-8")
        errors, _ = i18n.validate(self.root, today=TODAY)
        self.assertTrue(any("cannot be registered as a reviewer" in e for e in errors), errors)

    # 17
    def test_approval_for_a_different_translation(self):
        self.set_approval(translation_sha256=i18n.fingerprint("an earlier draft that was approved"))
        self.assertWithheld(UNIT)
        errors, report = i18n.validate(self.root, today=TODAY)
        self.assertIn(f"fr:{UNIT}", report["stale"])

    def test_editing_an_approved_translation_withdraws_it(self):
        self.edit_unit("fr", UNIT, text=self.text(UNIT, "fr") + " edited",
                       approval=approval(self.source(UNIT), self.text(UNIT, "fr"), UNIT, "fr"))
        self.assertWithheld(UNIT)

    # 19
    def test_approval_under_an_invalid_policy_version(self):
        for policy in ("TMA-DEC-007", "TMA-DEC-009", "two-reviewer"):
            self.set_approval(policy=policy)
            self.assertWithheld(UNIT)

    # 20
    def test_unresolved_specialist_escalation(self):
        self.set_approval(escalation={"criteria": ["specialist-term"], "status": "open"})
        self.assertWithheld(UNIT)
        self.set_approval(escalation={"criteria": ["specialist-term"], "status": "resolved", "resolved_by": "synthetic-reviewer-02",
                                      "resolved_at": "2026-11-21T08:00:00Z"})
        self.assertIn("fr/registry/index.html", self.localize()[0])

    def test_unregistered_reviewer(self):
        self.set_approval(reviewer="reviewer-fr-77")
        self.assertWithheld(UNIT)

    def test_reviewer_without_the_language(self):
        reg = json.loads((self.root / "i18n" / "reviewers.json").read_text(encoding="utf-8"))
        reg["reviewers"][0]["languages"] = ["ar"]
        (self.root / "i18n" / "reviewers.json").write_text(json.dumps(reg), encoding="utf-8")
        self.assertWithheld("has no approved, current translation")  # every French unit loses its approval
        self.assertEqual(i18n.renderable_texts("fr", self.root, today=TODAY), {})

    # 25
    def test_unauthorized_localized_publication(self):
        # Nothing is registered for localization, the repository registers no reviewer, and its catalogs hold no
        # unit: the real build cannot publish a localized page.
        self.assertEqual(build.LOCALIZABLE_PAGES, ())
        self.assertEqual(json.loads((REPO / "i18n" / "reviewers.json").read_text(encoding="utf-8"))["reviewers"], [])
        for lang in ("ar", "fr"):
            for kind in ("messages", "content"):
                self.assertEqual(json.loads((REPO / "i18n" / lang / f"{kind}.json").read_text(encoding="utf-8"))["units"], [])
        self.assertEqual(i18n.renderable_texts("fr", REPO), {})

    def test_validation_and_build_never_write_approvals(self):
        before = {p: p.read_bytes() for p in sorted((self.root / "i18n").rglob("*.json"))}
        i18n.validate(self.root, today=TODAY)
        self.localize()
        after = {p: p.read_bytes() for p in sorted((self.root / "i18n").rglob("*.json"))}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
