"""SYNTHETIC approval fixtures for the translation-layer tests (TMA-DEC-008 approval contract).

Everything built here is written only into temporary directories created by the tests. The reviewer ids are
synthetic, the approvals are fabricated to exercise the gates, and none of it is a real reviewer, a real review
or a real translation. The committed registry i18n/reviewers.json is empty, so none of these records would be
accepted in the repository.
"""
import json
from pathlib import Path

import i18n

SYNTHETIC_REVIEWERS = [
    {"id": "synthetic-reviewer-01", "kind": "human", "languages": ["ar", "fr"]},
    {"id": "synthetic-reviewer-02", "kind": "human", "languages": ["ar", "fr"]},
    {"id": "synthetic-certified-01", "kind": "certified-translator", "languages": ["ar", "fr"]},
]
DRAFT = {"method": "machine-assisted", "by": "synthetic-drafter-01"}
REVIEWED_AT = "2026-11-20T10:00:00Z"
GLOSSARY_VERSION = "2026-11-22"


def register_reviewers(root, reviewers=None):
    path = Path(root) / "i18n" / "reviewers.json"
    path.write_text(json.dumps({"note": "SYNTHETIC test reviewers", "reviewers": reviewers or SYNTHETIC_REVIEWERS}), encoding="utf-8")


def approval(source_text, text, **over):
    a = {"reviewer": "synthetic-reviewer-01", "decision": "approved", "reviewed_at": REVIEWED_AT,
         "policy": i18n.GOVERNANCE_POLICY, "source_sha256": i18n.fingerprint(source_text),
         "translation_sha256": i18n.fingerprint(text), "glossary_version": GLOSSARY_VERSION}
    a.update(over)
    return a


def approved_unit(uid, kind, text, source_text, **over):
    """An APPROVED unit whose approval covers exactly `source_text` and `text`. Keyword overrides replace fields
    of the unit; pass approval=... (or approval=None) to replace the approval record."""
    unit = {"id": uid, "kind": kind, "status": "APPROVED", "text": text, "source_sha256": i18n.fingerprint(source_text),
            "draft": dict(DRAFT), "approval": approval(source_text, text)}
    unit.update(over)
    if unit.get("approval") is None:
        unit.pop("approval")
    return unit


def approved_label(term_id, label, forbidden=(), **over):
    """A glossary label approved like a unit: its source is the canonical term value."""
    value = term_id.partition(":")[2]
    entry = {"label": label, "status": "APPROVED", "forbidden": list(forbidden), "draft": dict(DRAFT),
             "approval": approval(value, label)}
    entry.update(over)
    return entry
