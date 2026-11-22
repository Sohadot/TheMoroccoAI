"""Owner review workflow and the complete translation lifecycle, SIMULATED (Sprint 19B-5).

Every draft, decision, reviewer and approval here is a SYNTHETIC TEST FIXTURE in temporary directories: the
'reviewer' is synthetic-reviewer-01, registered by a synthetic decision log, and its decisions are written by
the test. Nothing here is a real review or a real approval, and nothing reaches the repository.

Lifecycle: draft -> automated checks -> human-review record -> exact-text approval -> publication eligibility
-> source change -> staleness -> withdrawal -> correction -> re-approval.
Run: python3 -m unittest discover -s tests
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n  # noqa: E402
import semantic  # noqa: E402
import translation_review as tr  # noqa: E402
from test_extraction import TODAY, ExtractedRegistryFixture  # noqa: E402
from test_multilingual import synthetic  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
UNIT = "page.registry.legend.note"  # a qualifier on /registry/
DECIDED_AT = "2026-11-21T10:00:00Z"


class Lifecycle(ExtractedRegistryFixture):
    """/registry/ fully approved (synthetically) except UNIT in French, which goes through the workflow."""

    def setUp(self):
        super().setUp()
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        for var in ("CI", "GITHUB_ACTIONS"):
            os.environ.pop(var, None)
        cat = self.read("fr/messages.json")
        cat["units"] = [u for u in cat["units"] if u["id"] != UNIT]
        self.write("fr/messages.json", cat)
        self.ws_dir = Path(tempfile.mkdtemp())  # outside the repository
        self.addCleanup(shutil.rmtree, self.ws_dir)

    def draft(self, text=None):
        source = i18n.Sources(self.root).message(UNIT)  # the current English source
        ws = {"workspace": i18n.DRAFT_MARKER, "language": "fr", "note": "SYNTHETIC TEST FIXTURE",
              "units": [{"id": UNIT, "kind": "qualifier", "page": "/registry/", "section": "Legend",
                         "text": text or self.text(UNIT, "fr"), "source_sha256": i18n.fingerprint(source),
                         "draft": {"method": "machine-assisted", "by": "ai-draft-01"}, "status": "DRAFT"}]}
        path = self.ws_dir / "fr.json"
        path.write_text(json.dumps(ws, ensure_ascii=False), encoding="utf-8")
        return tr.load_drafts(path, REPO)

    def decision(self, ws, decision="approve", text=None, **over):
        u = ws["units"][0]
        final = text if text is not None else u["text"]
        shown = semantic.warning_codes(tr.check(ws, self.root)[0][2])  # what the package showed for the draft
        d = {"unit": UNIT, "language": "fr", "decision": decision, "draft_sha256": i18n.fingerprint(u["text"]),
             "source_sha256": u["source_sha256"], "shown_warnings": shown, "text": final, "comment": "",
             "criterion": None, "decided_at": DECIDED_AT}
        d.update(over)
        return {"kind": "translation-review-decisions", "package": "SYNTHETIC", "decisions": [d]}

    def published(self):
        files, clusters, report = self.localize()
        return "fr/registry/index.html" in files, report

    def record(self, decisions, ws, reviewer="synthetic-reviewer-01"):
        return tr.record(decisions, [ws], reviewer, self.root, today=TODAY)

    def test_complete_lifecycle(self):
        # 1-2. Draft and automated checks: no blocking problem; nothing is approved; the page is not generated.
        ws = self.draft()
        [(unit, problems, findings, _)] = tr.check(ws, self.root)
        self.assertEqual(problems, [])
        self.assertFalse(self.published()[0])
        # 3-4. Human review record, bound to the exact text: the unit becomes approved and the page eligible.
        approved, others = self.record(self.decision(ws), ws)
        self.assertEqual(approved, ["fr:" + UNIT])
        recorded = next(u for u in self.read("fr/messages.json")["units"] if u["id"] == UNIT)
        self.assertEqual(recorded["approval"]["translation_sha256"], i18n.fingerprint(ws["units"][0]["text"]))
        self.assertEqual((recorded["approval"]["unit"], recorded["approval"]["language"]), (UNIT, "fr"))
        self.assertEqual(recorded["draft"]["by"], "ai-draft-01")
        self.assertNotIn("revised", recorded["approval"])
        self.assertEqual(i18n.validate(self.root, today=TODAY)[0], [])
        # 5. Publication eligibility.
        self.assertTrue(self.published()[0])
        # 6-8. The English source changes: the translation is stale and the page is withdrawn.
        en = self.read("en/messages.json")
        for m in en["messages"]:
            if m["id"] == UNIT:
                m["text"] = m["text"] + " Revised."
        self.write("en/messages.json", en)
        errors, report = i18n.validate(self.root, today=TODAY)
        self.assertIn(f"fr:{UNIT}", report["stale"])
        live, why = self.published()
        self.assertFalse(live)
        self.assertTrue(any(UNIT in r for r in why), why)
        # 9-10. Correction (a new draft for the new source) and re-approval: the page is eligible again.
        ws = self.draft(synthetic(i18n.Sources(self.root).message(UNIT), "fr") + " " + self.tag(UNIT))
        self.record(self.decision(ws), ws)
        self.assertTrue(self.published()[0])
        # French is current again; Arabic, not re-reviewed, stays stale and its page stays withdrawn.
        self.assertEqual(i18n.validate(self.root, today=TODAY), ([], {"stale": [f"ar:{UNIT}"], "orphaned": [], "unacknowledged": []}))
        files, clusters, report = self.localize()
        self.assertNotIn("ar/registry/index.html", files)

    def test_corrected_text_is_recorded_as_revised_or_refused_if_its_warnings_were_not_shown(self):
        ws = self.draft()
        corrected = ws["units"][0]["text"] + " corrigé"
        self.record(self.decision(ws, text=corrected), ws)
        recorded = next(u for u in self.read("fr/messages.json")["units"] if u["id"] == UNIT)
        self.assertEqual(recorded["text"], corrected)
        self.assertIs(recorded["approval"]["revised"], True)
        # A correction that raises a warning the package did not show must be re-reviewed first.
        ws = self.draft()
        with self.assertRaisesRegex(tr.ReviewError, "were not the ones shown"):
            self.record(self.decision(ws, text=ws["units"][0]["text"] + " n'est pas"), ws)

    def test_other_decisions_update_the_workspace_only(self):
        before = (self.root / "i18n" / "fr" / "messages.json").read_bytes()
        for decision, status in (("revise", "NEEDS_REVISION"), ("reject", "REJECTED"), ("escalate", "DRAFT")):
            ws = self.draft()
            approved, others = self.record(self.decision(ws, decision, criterion="specialist-term" if decision == "escalate" else None), ws)
            self.assertEqual((approved, others), ([], ["fr:" + UNIT]))
            self.assertEqual(ws["units"][0]["status"], status)
            self.assertIn(decision, ws["units"][0]["note"])
        self.assertEqual((self.root / "i18n" / "fr" / "messages.json").read_bytes(), before)
        self.assertFalse(self.published()[0])

    def test_refusals_change_nothing(self):
        ws = self.draft()
        before = {p: p.read_bytes() for p in (self.root / "i18n").rglob("*.json")}
        cases = [
            (dict(reviewer="synthetic-unknown-01"), "not a registered reviewer"),
            (dict(decisions=self.decision(ws, draft_sha256=i18n.fingerprint("another draft"))), "the draft changed"),
            (dict(decisions=self.decision(ws, source_sha256=i18n.fingerprint("another source"))), "English source changed"),
            (dict(decisions=self.decision(ws, decision="looks good")), "unknown decision"),
            (dict(decisions=self.decision(ws, text="Le 32 octobre.")), "DATE_MONTH"),
            (dict(decisions={"decisions": []}), "not a decisions file"),
        ]
        for over, fragment in cases:
            with self.assertRaisesRegex(tr.ReviewError, fragment):
                tr.record(over.get("decisions", self.decision(ws)), [ws], over.get("reviewer", "synthetic-reviewer-01"),
                          self.root, today=TODAY)
        self.assertEqual({p: p.read_bytes() for p in (self.root / "i18n").rglob("*.json")}, before)

    def test_a_successful_ci_run_cannot_record_an_approval(self):
        ws = self.draft()
        for var in ("CI", "GITHUB_ACTIONS"):
            with mock.patch.dict(os.environ, {var: "true"}):
                with self.assertRaisesRegex(tr.ReviewError, "refusing to record approvals in CI"):
                    self.record(self.decision(ws), ws)
        self.assertFalse(self.published()[0])

    def test_check_blocks_stale_unknown_and_approved_drafts(self):
        ws = self.draft()
        ws["units"].append(dict(ws["units"][0], id="page.registry.not_a_message"))
        ws["units"].append(dict(ws["units"][0], status="APPROVED"))
        ws["units"][0]["source_sha256"] = i18n.fingerprint("an older English text")
        problems = [p for _, ps, _, _ in tr.check(ws, self.root) for p in ps]
        self.assertTrue(any("stale draft" in p for p in problems))
        self.assertTrue(any("unknown unit" in p for p in problems))
        self.assertTrue(any("never approvals" in p for p in problems))


class Package(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        source = i18n.english_messages()["footer.disclaimer"]
        self.ws = {"workspace": i18n.DRAFT_MARKER, "language": "ar", "note": "SYNTHETIC TEST FIXTURE",
                   "units": [{"id": "footer.disclaimer", "kind": "disclosure", "page": "/", "section": "Footer",
                              "text": "غير تابع لحكومة المغرب", "source_sha256": i18n.fingerprint(source),
                              "draft": {"method": "machine-assisted", "by": "ai-draft-01"}, "status": "DRAFT"},
                             {"id": "footer.owner_note", "kind": "disclosure", "page": "/", "section": "Footer",
                              "text": "تملكه وتديره سوهادوت", "source_sha256": i18n.fingerprint(i18n.english_messages()["footer.owner_note"]),
                              "draft": {"method": "machine-assisted", "by": "ai-draft-01"}, "status": "DRAFT"}]}

    def test_package_preselects_nothing_and_says_it_is_not_an_approval(self):
        page = tr.build_package([self.ws], generated="2026-11-22T00:00:00Z")
        self.assertNotRegex(page, r"<input[^>]*\bchecked\b")
        self.assertEqual(page.count('type="radio"'), 8)
        self.assertIn(f'<meta name="workspace" content="{i18n.DRAFT_MARKER}">', page)
        self.assertIn('content="noindex, nofollow"', page)
        self.assertIn("Not approved", page)
        self.assertIn("approves nothing", page)
        self.assertIn('lang="ar" dir="rtl"', page)
        self.assertIn("Not affiliated with the Government of Morocco", page)  # the English source is shown
        self.assertNotIn("fetch(", page)  # nothing is submitted anywhere
        self.assertNotRegex(page, r"https?://(?!themoroccoai\.com/registry/|www\.)")  # no external script or endpoint

    def test_drafts_and_packages_stay_outside_the_repository(self):
        inside = REPO / "fr-drafts.json"
        with self.assertRaisesRegex(tr.ReviewError, "outside the repository"):
            tr.load_drafts(inside, REPO)
        path = self.dir / "ws.json"
        path.write_text(json.dumps(dict(self.ws, workspace="something-else")), encoding="utf-8")
        with self.assertRaisesRegex(tr.ReviewError, "not a translation draft workspace"):
            tr.load_drafts(path, REPO)
        self.assertEqual(tr.main(["package", str(path), "--out", str(REPO / "review.html")]), 1)
        self.assertFalse((REPO / "review.html").exists())


if __name__ == "__main__":
    unittest.main()
