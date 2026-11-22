"""SYNTHETIC approval fixtures for the translation-layer tests (TMA-DEC-008 approval contract).

Everything built here is written only into temporary directories created by the tests. The reviewer ids are
synthetic, the approvals are fabricated to exercise the gates, and none of it is a real reviewer, a real review
or a real translation. The committed registry i18n/reviewers.json is empty, so none of these records would be
accepted in the repository.
"""
import json
from pathlib import Path

import i18n

SYNTHETIC_DECISION = "TMA-DEC-900"  # exists only in the temporary decision log written below
REGISTERED_ON = "2026-11-01"
SYNTHETIC_REVIEWERS = [
    {"id": rid, "kind": kind, "languages": ["ar", "fr"], "authorized_by": SYNTHETIC_DECISION, "registered_on": REGISTERED_ON}
    for rid, kind in (("synthetic-reviewer-01", "human"), ("synthetic-reviewer-02", "human"),
                      ("synthetic-certified-01", "certified-translator"))
]
DRAFT = {"method": "machine-assisted", "by": "synthetic-drafter-01"}
REVIEWED_AT = "2026-11-20T10:00:00Z"
GLOSSARY_VERSION = "2026-11-22"


def register_reviewers(root, reviewers=None):
    """SYNTHETIC registry and a SYNTHETIC decision log in the temporary root only."""
    reviewers = reviewers or SYNTHETIC_REVIEWERS
    path = Path(root) / "i18n" / "reviewers.json"
    path.write_text(json.dumps({"note": "SYNTHETIC test reviewers", "reviewers": reviewers}), encoding="utf-8")
    docs = Path(root) / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "DECISION_LOG.md").write_text(
        f"# SYNTHETIC TEST DECISION LOG\n\n## {SYNTHETIC_DECISION} — SYNTHETIC test fixture, not a real decision\n"
        f"- Decision status: Accepted (SYNTHETIC TEST FIXTURE)\n- Decision: registers "
        + ", ".join(r["id"] for r in reviewers) + " for tests only.\n", encoding="utf-8")


def approval(source_text, text, unit=None, language=None, **over):
    a = {"unit": unit, "language": language, "reviewer": "synthetic-reviewer-01", "decision": "approved", "reviewed_at": REVIEWED_AT,
         "policy": i18n.GOVERNANCE_POLICY, "source_sha256": i18n.fingerprint(source_text),
         "translation_sha256": i18n.fingerprint(text), "glossary_version": GLOSSARY_VERSION}
    a.update(over)
    return a


def approved_unit(uid, kind, text, source_text, lang="ar", **over):
    """An APPROVED unit whose approval covers exactly `source_text` and `text`, for unit `uid` in `lang`. Keyword
    overrides replace fields of the unit; pass approval=... (or approval=None) to replace the approval record."""
    unit = {"id": uid, "kind": kind, "status": "APPROVED", "text": text, "source_sha256": i18n.fingerprint(source_text),
            "draft": dict(DRAFT), "approval": approval(source_text, text, uid, lang)}
    unit.update(over)
    if unit.get("approval") is None:
        unit.pop("approval")
    return unit


def approved_label(term_id, label, forbidden=(), lang="ar", **over):
    """A glossary label approved like a unit: its source is the canonical term value."""
    value = term_id.partition(":")[2]
    entry = {"label": label, "status": "APPROVED", "forbidden": list(forbidden), "draft": dict(DRAFT),
             "approval": approval(value, label, term_id, lang)}
    entry.update(over)
    return entry
