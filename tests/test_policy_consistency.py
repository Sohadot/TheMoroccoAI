"""TMA-DEC-008 is the operative translation review policy everywhere (Sprint 19B-5).

TMA-DEC-007 stays in the record: its review provisions may be quoted only in sections that say they are
superseded, amended or kept for the record. Operative code, comments and documentation must not describe two
reviews, two reviewers or reviewer independence from the drafter as current requirements.
Run: python3 -m unittest discover -s tests
"""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import i18n  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OBSOLETE = re.compile(r"two (?:human )?reviews|both (?:human )?reviews|two (?:different |independent )?reviewers|"
                      r"substantive and (?:a )?linguistic|independent of the drafter|review functions|"
                      r"two human approvals", re.I)
HISTORICAL = re.compile(r"supersed|\breplaces\b|replaced (?:in Sprint 19B-4 )?by (?:the )?TMA-DEC-008|amended by TMA-DEC-008|TMA-DEC-007 text|for the record|"
                        r"under TMA-DEC-007", re.I)
OPERATIVE_DOCS = ["README.md", "docs/TRANSLATION_REVIEW_POLICY.md", "docs/MULTILINGUAL_ARCHITECTURE.md",
                  "docs/MULTILINGUAL_IMPLEMENTATION_PLAN.md", "docs/ADR_MULTILINGUAL_REFERENCE.md",
                  "docs/MULTILINGUAL_CONTENT_INVENTORY.md", "docs/TRANSLATION_APPROVAL_SECURITY.md",
                  "docs/TRANSLATION_PILOT.md"]


def sections(text):
    """(heading, body) pairs; a nested heading starts a new section."""
    parts = re.split(r"(?m)^(#{1,6} .*)$", text)
    return [("", parts[0])] + list(zip(parts[1::2], parts[2::2]))


def obsolete_statements(text):
    found = []
    for heading, body in sections(text):
        if HISTORICAL.search(heading + body):
            continue
        found += [f"{heading.strip()}: {m.group(0)}" for m in OBSOLETE.finditer(body)]
    return found


class OperativePolicy(unittest.TestCase):
    def test_code_and_comments_state_the_policy_in_force(self):
        self.assertEqual(i18n.GOVERNANCE_POLICY, "TMA-DEC-008")
        for path in sorted((REPO / "tools").glob("*.py")):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if OBSOLETE.search(line) and not HISTORICAL.search(line):
                    self.fail(f"{path.name}:{n}: obsolete review requirement: {line.strip()}")

    def test_operative_documentation_has_no_obsolete_review_requirement(self):
        for rel in OPERATIVE_DOCS:
            path = REPO / rel
            if path.exists():
                self.assertEqual(obsolete_statements(path.read_text(encoding="utf-8")), [], rel)

    def test_the_check_detects_an_obsolete_statement(self):
        self.assertTrue(obsolete_statements("## Publishing\n\nEach translation needs two human reviews.\n"))
        self.assertEqual(obsolete_statements("## Q3 (superseded by TMA-DEC-008)\n\nTwo human reviews.\n"), [])

    def test_decision_record_is_preserved_and_points_to_the_policy_in_force(self):
        log = (REPO / "docs" / "DECISION_LOG.md").read_text(encoding="utf-8")
        dec7 = log[log.index("TMA-DEC-007"):log.index("TMA-DEC-008")]
        self.assertIn("two review functions", dec7.lower() + log.lower())  # the historical text is kept
        self.assertIn("Superseded in part by: TMA-DEC-008", log)
        dec8 = log[log.index("## TMA-DEC-008") if "## TMA-DEC-008" in log else log.rindex("TMA-DEC-008"):]
        self.assertRegex(dec8, r"(?i)status:\s*accepted")
        policy = (REPO / "docs" / "TRANSLATION_REVIEW_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("**TMA-DEC-008**", policy)

    def test_public_disclosure_describes_one_documented_human_approval(self):
        en = i18n.english_messages()
        text = en["shell.translation_policy"]
        self.assertIn("approved by a documented human reviewer", text)
        self.assertNotRegex(text, OBSOLETE)
        self.assertNotRegex(text, r"(?i)certified|sworn|independent(ly)? review")


if __name__ == "__main__":
    unittest.main()
