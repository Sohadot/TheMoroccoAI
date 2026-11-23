"""Evidence change intelligence: what changed in the documented record between published registry versions.

    python3 tools/changes.py            print a summary of every transition between published versions

A *snapshot* is a published version of the canonical files (data/evidence.json, data/ontology.json, data/gaps.json)
on the first-parent history of the current branch: one per registry version (the last commit carrying it), plus the
working tree when it holds a version not yet committed. Snapshots are identified by version, as_of date and the
SHA-256 of their content, never by commit hash, so the output does not change when a branch is merged.

Every change describes the RECORD, not the world:
- a record added in a version was admitted to the registry then; it does not mean the event it documents happened
  then. The dates that exist are kept apart and labelled: the source's publication date, the date the registry
  retrieved the source, and the version's as_of date (when the registry's sources were last checked). No event date
  is recorded unless the data records one; none is inferred.
- a text revision is classed 'editorial' only when the texts differ in whitespace, case or punctuation alone; any
  other revision is 'undetermined': whether it changes the finding is not decided by this tool.
- a snapshot older than a file (gaps.json first appears in v0.4.0) does not 'remove' anything: the register begins.
- a property absent before and present after is 'first recorded', never 'changed': when the lifecycle field was
  introduced, entities received a stage for the first time; nothing moved from one stage to another.

Deterministic and standard-library only; it reads git history with `git show` and fails loudly without it.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "1.0"
CANONICAL = ("evidence.json", "ontology.json", "gaps.json")

# Change classes: (subject kind, class) -> (materiality, plain description). Materiality says what the change is
# about: 'research' (the documented findings changed), 'editorial', 'structural' (format or schema), or
# 'undetermined' (a text revision the tool does not judge).
CLASSES = {
    "evidence.added": ("research", "Evidence record admitted"),
    "evidence.removed": ("research", "Evidence record removed"),
    "evidence.reclassified": ("research", "Claim classification changed"),
    "evidence.verification_changed": ("research", "Verification status changed"),
    "evidence.superseded": ("research", "Record marked as superseded"),
    "evidence.source_changed": ("research", "Source reference changed"),
    "evidence.excerpts_changed": ("research", "Source excerpts changed"),
    "evidence.date_corrected": ("research", "Source publication date changed"),
    "evidence.rechecked": ("structural", "Source retrieval date changed"),
    "evidence.links_changed": ("research", "Entities the record relates to changed"),
    "evidence.text_revised": ("undetermined", "Record wording revised"),
    "evidence.text_editorial": ("editorial", "Record wording reformatted"),
    "evidence.metadata_changed": ("structural", "Record metadata changed"),
    "evidence.field_recorded": ("research", "Property first recorded on an existing record"),
    "entity.added": ("research", "Entity added"),
    "entity.removed": ("research", "Entity removed"),
    "entity.lifecycle_changed": ("research", "Lifecycle stage changed"),
    "entity.lifecycle_recorded": ("research", "Lifecycle stage first recorded"),
    "entity.field_recorded": ("research", "Property first recorded on an existing entity"),
    "entity.classification_changed": ("research", "Type, kind, origin or domain changed"),
    "entity.renamed": ("research", "Name changed"),
    "entity.attributes_changed": ("research", "Documented attributes changed"),
    "entity.evidence_changed": ("research", "Supporting records changed"),
    "entity.dates_changed": ("research", "Documented start or end date changed"),
    "entity.text_revised": ("undetermined", "Description revised"),
    "entity.text_editorial": ("editorial", "Description reformatted"),
    "entity.metadata_changed": ("structural", "Entity metadata changed"),
    "relationship.added": ("research", "Relationship documented"),
    "relationship.removed": ("research", "Relationship removed"),
    "relationship.reclassified": ("research", "Relationship classification changed"),
    "relationship.evidence_changed": ("research", "Relationship evidence changed"),
    "relationship.text_revised": ("undetermined", "Relationship note revised"),
    "relationship.text_editorial": ("editorial", "Relationship note reformatted"),
    "gap.opened": ("research", "Evidence gap opened"),
    "gap.state_changed": ("research", "Evidence gap state changed"),
    "gap.reassessed": ("research", "Evidence gap reassessed"),
    "gap.removed": ("research", "Evidence gap removed"),
    "gap.text_revised": ("undetermined", "Gap wording revised"),
    "gap.register_started": ("structural", "Gap register begins"),
    "schema.field_added": ("structural", "New field in the data contract"),
    "schema.field_removed": ("structural", "Field removed from the data contract"),
}
LIMITATIONS = [
    "Changes describe the registry's record between published versions, not events in the world: a record admitted "
    "in a version documents something that may have happened much earlier.",
    "Dates are kept apart: source_published is the source's own date, retrieved is when the registry retrieved it, "
    "and registry_as_of is when the version's sources were last checked. No event date is inferred.",
    "A text revision is 'editorial' only if it differs in whitespace, case or punctuation; otherwise its effect on "
    "the finding is 'undetermined' and is read from the before and after texts.",
    "Snapshots are the published versions on the repository's main history; changes made between versions are not "
    "seen separately.",
    "Source disappearance or modification is not detected here: tools/check_sources.py re-checks sources, and only "
    "a recorded correction appears as a change.",
]

EVIDENCE_TEXT = ("title", "claim", "verification_note")
EVIDENCE_LINKS = ("related_entities", "associated_entities", "source_entity")
ENTITY_TEXT = ("summary", "status", "note")
ENTITY_CLASS = ("type", "project_kind", "origin", "domain")


# ─── Snapshots ────────────────────────────────────────────────────────────

def _git(*args, root=ROOT):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def _digest(files):
    h = hashlib.sha256()
    for name in CANONICAL:
        h.update(name.encode() + b"\0" + json.dumps(files.get(name), sort_keys=True, ensure_ascii=False).encode() + b"\0")
    return h.hexdigest()


def _snapshot(files):
    ev = files["evidence.json"]
    return {"version": ev["version"], "as_of": ev["as_of"], "content_sha256": _digest(files), "files": files}


def snapshots(root=ROOT):
    """Published snapshots, oldest first. Raises RuntimeError without git history."""
    root = Path(root)
    if _git("rev-parse", "--is-shallow-repository", root=root).stdout.strip() != "false":
        raise RuntimeError("tools/changes.py needs the full git history (git fetch --unshallow)")
    log = _git("log", "--first-parent", "--reverse", "--format=%H", "HEAD", "--",
               *[f"data/{f}" for f in CANONICAL], root=root)
    if log.returncode:
        raise RuntimeError("cannot read git history: " + log.stderr.strip())
    by_version = {}
    for commit in log.stdout.split():
        files = {}
        for name in CANONICAL:
            shown = _git("show", f"{commit}:data/{name}", root=root)
            files[name] = json.loads(shown.stdout) if shown.returncode == 0 else None
        if files["evidence.json"] is None:
            continue
        snap = _snapshot(files)
        by_version.pop(snap["version"], None)  # the last commit carrying a version is its published state
        by_version[snap["version"]] = snap
    current = _snapshot({name: json.loads((root / "data" / name).read_text(encoding="utf-8"))
                         if (root / "data" / name).exists() else None for name in CANONICAL})
    by_version.pop(current["version"], None)
    by_version[current["version"]] = current
    return list(by_version.values())


# ─── Comparison ───────────────────────────────────────────────────────────

def _norm(text):
    return re.sub(r"[\W_]+", "", str(text).lower())


def _text_class(prefix, before, after):
    return f"{prefix}.text_editorial" if _norm(before) == _norm(after) else f"{prefix}.text_revised"


def _change(cls, kind, sid, fields=(), evidence=(), dates=None, note=None):
    materiality, label = CLASSES[cls]
    c = {"class": cls, "materiality": materiality, "label": label, "subject": {"kind": kind, "id": sid}}
    if fields:
        c["fields"] = [{"field": f, "before": b, "after": a} for f, b, a in fields]
    if evidence:
        c["evidence"] = sorted(set(evidence))
    if dates:
        c["dates"] = dates
    if note:
        c["note"] = note
    return c


def _record_dates(r):
    return {"source_published": r.get("publication_date"), "retrieved": r.get("retrieval_date")}


def _diff_evidence(before, after):
    out = []
    a = {r["evidence_id"]: r for r in before["records"]}
    b = {r["evidence_id"]: r for r in after["records"]}
    for rid in sorted(set(b) - set(a)):
        r = b[rid]
        out.append(_change("evidence.added", "evidence", rid, evidence=[rid], dates=_record_dates(r),
                           note=f"{r['classification']}: {r['title']}"))
    for rid in sorted(set(a) - set(b)):
        out.append(_change("evidence.removed", "evidence", rid, evidence=[rid]))
    for rid in sorted(set(a) & set(b)):
        x, y = a[rid], b[rid]
        if x == y:
            continue
        per = {}
        for field in sorted(set(x) | set(y)):
            if x.get(field) == y.get(field):
                continue
            if field not in x and field != "superseded_by":  # being superseded is a finding, never just 'recorded'
                per.setdefault("evidence.field_recorded", []).append((field, None, y.get(field)))
                continue
            cls = {"classification": "evidence.reclassified", "verification_status": "evidence.verification_changed",
                   "superseded_by": "evidence.superseded", "source_url": "evidence.source_changed",
                   "source_excerpts": "evidence.excerpts_changed", "publication_date": "evidence.date_corrected",
                   "retrieval_date": "evidence.rechecked"}.get(field)
            if cls is None and field in EVIDENCE_LINKS:
                cls = "evidence.links_changed"
            if cls is None and field in EVIDENCE_TEXT:
                cls = _text_class("evidence", x.get(field, ""), y.get(field, ""))
            cls = cls or "evidence.metadata_changed"
            if field == "superseded_by" and not y.get(field):
                cls = "evidence.metadata_changed"
            per.setdefault(cls, []).append((field, x.get(field), y.get(field)))
        for cls in sorted(per):
            out.append(_change(cls, "evidence", rid, per[cls], evidence=[rid], dates=_record_dates(y)))
    return out


def _attr_key(attrs):
    return sorted(json.dumps(a, sort_keys=True, ensure_ascii=False) for a in attrs or [])


def _diff_ontology(before, after):
    out = []
    a = {e["id"]: e for e in before["entities"]}
    b = {e["id"]: e for e in after["entities"]}
    for eid in sorted(set(b) - set(a)):
        e = b[eid]
        out.append(_change("entity.added", "entity", eid, evidence=e.get("evidence", []), note=f"{e['type']}: {e['name']}"))
    for eid in sorted(set(a) - set(b)):
        out.append(_change("entity.removed", "entity", eid))
    for eid in sorted(set(a) & set(b)):
        x, y = a[eid], b[eid]
        if x == y:
            continue
        per = {}
        for field in sorted(set(x) | set(y)):
            if x.get(field) == y.get(field):
                continue
            if field in ("lifecycle", "lifecycle_evidence"):
                if x.get("lifecycle") is None:
                    cls = "entity.lifecycle_recorded"
                else:
                    cls = "entity.lifecycle_changed" if x.get("lifecycle") != y.get("lifecycle") else "entity.evidence_changed"
            elif field not in x:
                cls = "entity.field_recorded"
            elif field in ENTITY_CLASS:
                cls = "entity.classification_changed"
            elif field in ("name", "alt_names"):
                cls = "entity.renamed"
            elif field == "attributes":
                if _attr_key(x.get(field)) == _attr_key(y.get(field)):
                    continue  # reordered only
                cls = "entity.attributes_changed"
            elif field in ("evidence", "origin_evidence"):
                if sorted(x.get(field) or []) == sorted(y.get(field) or []):
                    continue
                cls = "entity.evidence_changed"
            elif field in ("start_date", "end_date"):
                cls = "entity.dates_changed"
            elif field in ENTITY_TEXT:
                cls = _text_class("entity", x.get(field, ""), y.get(field, ""))
            else:
                cls = "entity.metadata_changed"
            per.setdefault(cls, []).append((field, x.get(field), y.get(field)))
        for cls in sorted(per):
            ev = set()
            for field, _, after_value in per[cls]:
                if field in ("lifecycle_evidence", "evidence", "origin_evidence") and isinstance(after_value, list):
                    ev |= set(after_value) - set(x.get(field) or [])
            if cls in ("entity.lifecycle_changed", "entity.lifecycle_recorded"):
                ev |= set(y.get("lifecycle_evidence") or [])
            if cls == "entity.attributes_changed":
                ev |= {at.get("evidence") for at in y.get("attributes") or [] if at.get("evidence")} - \
                      {at.get("evidence") for at in x.get("attributes") or [] if at.get("evidence")}
            out.append(_change(cls, "entity", eid, per[cls], evidence=sorted(v for v in ev if v)))
    key = lambda r: f"{r['subject']}|{r['predicate']}|{r['object']}"
    ra = {key(r): r for r in before["relationships"]}
    rb = {key(r): r for r in after["relationships"]}
    for k in sorted(set(rb) - set(ra)):
        r = rb[k]
        out.append(_change("relationship.added", "relationship", k, evidence=r.get("evidence", []), note=r["classification"]))
    for k in sorted(set(ra) - set(rb)):
        out.append(_change("relationship.removed", "relationship", k, evidence=ra[k].get("evidence", [])))
    for k in sorted(set(ra) & set(rb)):
        x, y = ra[k], rb[k]
        if x.get("classification") != y.get("classification"):
            out.append(_change("relationship.reclassified", "relationship", k,
                               [("classification", x.get("classification"), y.get("classification"))], evidence=y.get("evidence", [])))
        if sorted(x.get("evidence", [])) != sorted(y.get("evidence", [])):
            out.append(_change("relationship.evidence_changed", "relationship", k,
                               [("evidence", x.get("evidence"), y.get("evidence"))],
                               evidence=sorted(set(y.get("evidence", [])) - set(x.get("evidence", [])))))
        if x.get("note") != y.get("note"):
            out.append(_change("relationship.text_revised" if _norm(x.get("note", "")) != _norm(y.get("note", ""))
                               else "relationship.text_editorial", "relationship", k, [("note", x.get("note"), y.get("note"))]))
    return out


def _diff_gaps(before, after):
    if after is None:
        return []
    if before is None:
        return [_change("gap.register_started", "gap", "register",
                        note=f"The gap register begins with {len(after['gaps'])} gaps; earlier versions had none.")] + \
               [_change("gap.opened", "gap", g["id"], evidence=g.get("assessed_records", []), note=g.get("question"))
                for g in after["gaps"]]
    out = []
    a = {g["id"]: g for g in before["gaps"]}
    b = {g["id"]: g for g in after["gaps"]}
    for gid in sorted(set(b) - set(a)):
        g = b[gid]
        out.append(_change("gap.opened", "gap", gid, evidence=g.get("assessed_records", []), note=g.get("question")))
    for gid in sorted(set(a) - set(b)):
        out.append(_change("gap.removed", "gap", gid))
    for gid in sorted(set(a) & set(b)):
        x, y = a[gid], b[gid]
        if x.get("state") != y.get("state"):
            out.append(_change("gap.state_changed", "gap", gid, [("state", x.get("state"), y.get("state"))],
                               evidence=y.get("assessed_records", [])))
        if sorted(x.get("assessed_records") or []) != sorted(y.get("assessed_records") or []) or \
                x.get("entity_assessments") != y.get("entity_assessments"):
            out.append(_change("gap.reassessed", "gap", gid, [("assessed_records", x.get("assessed_records"), y.get("assessed_records"))],
                               evidence=sorted(set(y.get("assessed_records") or []) - set(x.get("assessed_records") or []))))
        text = [(f, x.get(f), y.get(f)) for f in ("question", "established", "unestablished", "evidence_needed") if x.get(f) != y.get(f)]
        if text:
            out.append(_change("gap.text_revised", "gap", gid, text))
    return out


def _fields(doc, path):
    if doc is None:
        return set()
    if path == "record":
        return {k for r in doc["records"] for k in r}
    if path == "entity":
        return {k for e in doc["entities"] for k in e}
    if path == "relationship":
        return {k for r in doc["relationships"] for k in r}
    return {k for g in doc["gaps"] for k in g}


def _diff_schema(before, after):
    out = []
    for kind, name in (("record", "evidence.json"), ("entity", "ontology.json"), ("relationship", "ontology.json"), ("gap", "gaps.json")):
        if before["files"][name] is None or after["files"][name] is None:
            continue
        fa, fb = _fields(before["files"][name], kind), _fields(after["files"][name], kind)
        if not fa or not fb:
            continue  # no items on one side: nothing to say about the schema
        for f in sorted(fb - fa):
            out.append(_change("schema.field_added", "schema", f"{kind}.{f}"))
        for f in sorted(fa - fb):
            out.append(_change("schema.field_removed", "schema", f"{kind}.{f}"))
    return out


def transition(before, after):
    changes = (_diff_evidence(before["files"]["evidence.json"], after["files"]["evidence.json"])
               + _diff_ontology(before["files"]["ontology.json"], after["files"]["ontology.json"])
               + _diff_gaps(before["files"]["gaps.json"], after["files"]["gaps.json"])
               + _diff_schema(before, after))
    for c in changes:
        c["id"] = f"{after['version']}:{c['class']}:{c['subject']['id']}"
    ids = [c["id"] for c in changes]
    assert len(ids) == len(set(ids)), "change ids must be unique"
    counts = {}
    for c in changes:
        counts[c["class"]] = counts.get(c["class"], 0) + 1
    by_materiality = {}
    for c in changes:
        by_materiality[c["materiality"]] = by_materiality.get(c["materiality"], 0) + 1
    return {"from": {"version": before["version"], "as_of": before["as_of"], "content_sha256": before["content_sha256"]},
            "to": {"version": after["version"], "as_of": after["as_of"], "content_sha256": after["content_sha256"]},
            "counts": dict(sorted(counts.items())), "materiality": dict(sorted(by_materiality.items())), "changes": changes}


def change_log(snaps):
    """The published change log: every transition between consecutive snapshots, oldest first."""
    return {
        "schema_version": SCHEMA_VERSION,
        "description": "Changes to TheMoroccoAI's documented record between published registry versions, classified by "
                       "what changed. They describe the record, not events in the world.",
        "date_fields": {
            "registry_as_of": "When the registry's sources were last checked for that version.",
            "source_published": "The source's own publication date (null if the source states none).",
            "retrieved": "When the registry retrieved the source.",
        },
        "materiality": {"research": "The documented findings changed.", "editorial": "Formatting only.",
                        "structural": "Format, schema or bookkeeping; no finding changed.",
                        "undetermined": "A wording revision whose effect on the finding is not judged automatically."},
        "classes": {k: {"materiality": m, "label": l} for k, (m, l) in sorted(CLASSES.items())},
        "limitations": LIMITATIONS,
        "snapshots": [{"version": s["version"], "as_of": s["as_of"], "content_sha256": s["content_sha256"]} for s in snaps],
        "transitions": [transition(a, b) for a, b in zip(snaps, snaps[1:])],
    }


if __name__ == "__main__":
    log = change_log(snapshots())
    for t in log["transitions"]:
        print(f"{t['from']['version']} -> {t['to']['version']} ({t['to']['as_of']}): {len(t['changes'])} changes {t['materiality']}")
        for cls, n in t["counts"].items():
            print(f"    {cls}: {n}")
    sys.exit(0)
