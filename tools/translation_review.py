"""Owner review workflow for Arabic and French translation drafts (Sprint 19B-5; policy TMA-DEC-008).

    python3 tools/translation_review.py check   DRAFTS.json [DRAFTS.json ...]
    python3 tools/translation_review.py package DRAFTS.json [DRAFTS.json ...] --out REVIEW.html
    python3 tools/translation_review.py record  DECISIONS.json --drafts DRAFTS.json [...] --reviewer ID
    python3 tools/translation_review.py provenance   (advisory: the commit behind each committed approval)

Six separate events, never merged into one:
  1. AI draft preparation       a draft workspace file, outside the repository (status DRAFT)
  2. automated verification     `check`: text, parity and semantic-risk findings; nothing is approved
  3. human editorial review     the owner reads the `package` page, corrects or rejects
  4. final approval             the owner's exported decisions, turned into approval records by `record`
  5. GitHub merge               a merge control, never an approval
  6. public publication         only when every unit of a page is approved and the language is published

Drafts and review packages carry a workspace marker and must stay outside the repository: every file on main is
publicly served, and tools/check_site.py fails if the marker appears in the repository. Opening, downloading or
building a package approves nothing; the package preselects nothing and submits nothing.

`record` cannot tell who runs it. It refuses to run in CI, refuses unregistered reviewers and decisions for any
text other than the exact text shown, and writes only what the decisions file says. The decisions file and
the commit that adds the approvals are the owner's own acts: see docs/TRANSLATION_APPROVAL_SECURITY.md.
Standard library only.
"""
import datetime
import html
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n  # noqa: E402
import semantic  # noqa: E402

ROOT = i18n.ROOT
DECISIONS = ("approve", "revise", "reject", "escalate")
DRAFT_UNIT_FIELDS = {"id", "kind", "page", "section", "text", "source_sha256", "draft", "status", "name_basis", "note"}


class ReviewError(Exception):
    pass


# ─── Draft workspace ──────────────────────────────────────────────────────

def load_drafts(path, root=ROOT):
    """A draft workspace file. It must live outside the repository and carry the workspace marker."""
    path = Path(path).resolve()
    if Path(root).resolve() in path.parents:
        raise ReviewError(f"{path}: draft workspaces must stay outside the repository (every file on main is public)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("workspace") != i18n.DRAFT_MARKER or data.get("language") not in ("ar", "fr"):
        raise ReviewError(f"{path}: not a translation draft workspace (needs workspace marker and language ar or fr)")
    return data


def _source(sources, uid):
    return sources.message(uid) if ":" not in uid else sources.content(uid)[0]


def check(drafts, root=ROOT):
    """[(unit, problems, findings, source)] for one workspace. problems block approval; findings are the
    semantic-risk errors and warnings the reviewer is shown."""
    lang, sources = drafts["language"], i18n.Sources(root)
    terms = i18n.term_forms(lang, root)
    out, seen = [], set()
    for u in drafts.get("units", []):
        uid = u.get("id")
        problems = []
        if uid in seen:
            problems.append("duplicate unit id")
        seen.add(uid)
        if set(u) - DRAFT_UNIT_FIELDS:
            problems.append(f"unexpected fields {sorted(set(u) - DRAFT_UNIT_FIELDS)}")
        source = _source(sources, uid) if isinstance(uid, str) else None
        if source is None:
            out.append((u, problems + ["unknown unit: no English source"], [], None))
            continue
        if u.get("source_sha256") != i18n.fingerprint(source):
            problems.append("the English source changed since this draft was prepared (stale draft)")
        if u.get("status") not in ("DRAFT", "NEEDS_REVISION", "REJECTED"):
            problems.append(f"status {u.get('status')!r}: a workspace holds drafts only, never approvals")
        if u.get("kind") not in i18n.KINDS:
            problems.append(f"unknown kind {u.get('kind')!r}")
        if u.get("kind") == "name" and u.get("name_basis") not in i18n.NAME_BASES:
            problems.append("a name needs name_basis")
        problems += i18n._draft_problems(u, "")
        problems += [p.lstrip(": ") for p in i18n._text_problems(u.get("text"), "") + i18n._parity_problems(u.get("text") or "", source, "")]
        findings = semantic.findings(source, u.get("text") or "", lang, terms, i18n.linked_forms(sources, uid))
        out.append((u, problems, findings, source))
    return out


# ─── Review package ───────────────────────────────────────────────────────

def _reference(sources, uid):
    """(label, href) of the source reference behind a unit, for the reviewer."""
    kind, _, rest = uid.partition(":")
    if kind == "evidence":
        rid = rest.split(":")[0]
        rec = sources.records.get(rid, {})
        return f"{rid} · {rec.get('source_organization', '')}", rec.get("source_url")
    if kind == "ontology":
        eid = rest.split(":")[0]
        return f"entity {eid}", f"https://themoroccoai.com/registry/{eid}/"
    if kind in ("changelog", "attribute", "classification", "domain", "predicate", "gaps"):
        return f"canonical {kind}: {rest.rsplit(':', 1)[0]}", None
    return "English interface catalog (i18n/en/messages.json)", None


def _glossary_terms(source, root):
    concepts = i18n.concept_forms(i18n._load(Path(root) / "i18n" / "glossary.json"))
    found = []
    for cid, form in concepts.items():
        if form.lower() in source.lower():
            found.append(f"concept:{cid} ({form})")
    return found


PACKAGE_CSS = """
:root { --bg:#f6f3ec; --ink:#1a2333; --muted:#5b6474; --line:#d8d2c4; --card:#fffdf8; --accent:#1a2e4a; --err:#a1260d; --warn:#8a5a00; --ok:#2d6a3e; }
@media (prefers-color-scheme: dark) { :root { --bg:#14181f; --ink:#e8e4da; --muted:#a7adb8; --line:#333a46; --card:#1c212a; --accent:#9fb7d9; --err:#ff8a73; --warn:#f2c25b; --ok:#7fcf93; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 96px; }
h1 { font-size: 1.6rem; margin: 0 0 8px; } h2 { margin-top: 40px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
h3 { font-size: 1.05rem; margin: 28px 0 8px; color: var(--muted); }
.banner { border:2px solid var(--err); border-radius:8px; padding:12px 16px; background:var(--card); }
.unit { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px; margin:14px 0; }
.unit header { display:flex; flex-wrap:wrap; gap:8px 16px; font-size:.85rem; color:var(--muted); }
.unit code { font-size:.85rem; word-break: break-all; }
.texts { display:grid; grid-template-columns: 1fr; gap:10px; margin:12px 0; }
@media (min-width: 760px) { .texts { grid-template-columns: repeat(3, 1fr); } }
.texts div { border:1px solid var(--line); border-radius:6px; padding:10px; white-space: pre-wrap; }
.texts h4 { margin:0 0 4px; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
[lang="ar"] { font-family: "Noto Naskh Arabic", "Noto Kufi Arabic", "Geeza Pro", serif; font-size: 1.1rem; }
.findings { margin:8px 0; padding-left: 20px; } .error { color:var(--err); } .warning { color:var(--warn); } .clean { color:var(--ok); }
fieldset { border:1px solid var(--line); border-radius:6px; margin:10px 0 0; min-width:0; } legend { font-weight:600; padding:0 4px; }
label { display:inline-flex; align-items:center; gap:6px; margin:4px 14px 4px 0; }
textarea { width:100%; min-height:4.5em; font:inherit; color:inherit; background:transparent; border:1px solid var(--line); border-radius:6px; padding:8px; }
select { font:inherit; max-width:100%; }
.scroll { overflow-x:auto; }
.bar { position:sticky; bottom:0; background:var(--card); border-top:1px solid var(--line); padding:12px 16px; display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between; }
button { font:inherit; padding:8px 14px; border-radius:6px; border:1px solid var(--accent); background:var(--accent); color:var(--bg); cursor:pointer; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
details summary { cursor:pointer; color: var(--muted); }
table { border-collapse: collapse; width: 100%; background: var(--card); } th, td { border: 1px solid var(--line); padding: 6px 8px; text-align: start; vertical-align: top; }
"""

PACKAGE_JS = r"""
(function () {
  var KEY = 'review-' + document.querySelector('meta[name="package-id"]').content;
  function store() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function save(state) { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
  var state = store();
  document.querySelectorAll('.unit').forEach(function (card) {
    var k = card.dataset.key, s = state[k] || {};
    card.querySelectorAll('input[type=radio]').forEach(function (r) { r.checked = s.decision === r.value; });
    if (s.text !== undefined) card.querySelector('.final').value = s.text;
    if (s.comment) card.querySelector('.comment').value = s.comment;
    if (s.criterion) card.querySelector('.criterion').value = s.criterion;
    card.addEventListener('input', function () {
      var chosen = card.querySelector('input[type=radio]:checked');
      state[k] = { decision: chosen ? chosen.value : null, text: card.querySelector('.final').value,
                   comment: card.querySelector('.comment').value, criterion: card.querySelector('.criterion').value };
      save(state); count();
    });
  });
  function count() {
    var n = document.querySelectorAll('.unit input[type=radio]:checked').length;
    document.getElementById('count').textContent = n + ' of ' + document.querySelectorAll('.unit').length + ' units decided';
  }
  count();
  document.getElementById('export').addEventListener('click', function () {
    var out = [];
    document.querySelectorAll('.unit').forEach(function (card) {
      var chosen = card.querySelector('input[type=radio]:checked');
      if (!chosen) return;  // undecided units are not exported: nothing is decided by default
      out.push({ unit: card.dataset.unit, language: card.dataset.lang, decision: chosen.value,
                 draft_sha256: card.dataset.draftSha, source_sha256: card.dataset.sourceSha,
                 shown_warnings: JSON.parse(card.dataset.warnings), text: card.querySelector('.final').value.normalize('NFC'),
                 comment: card.querySelector('.comment').value, criterion: card.querySelector('.criterion').value || null,
                 decided_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z') });
    });
    if (!out.length) { alert('No decision has been made.'); return; }
    var blob = new Blob([JSON.stringify({ kind: 'translation-review-decisions', package: KEY, decisions: out }, null, 1)],
                        { type: 'application/json' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'review-decisions.json'; a.click();
  });
})();
"""


def build_package(workspaces, root=ROOT, generated=None):
    """One HTML page for the owner: every draft unit with its English source, reference, glossary terms,
    findings, fingerprints and status, organised by page and section. Decisions start empty."""
    sources = i18n.Sources(root)
    generated = generated or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for ws in workspaces:
        for u, problems, findings, source in check(ws, root):
            rows.append((u.get("page", "?"), u.get("section", "?"), ws["language"], u, problems, findings, source))
    package_id = i18n.fingerprint(json.dumps([(r[2], r[3].get("id"), r[3].get("text")) for r in rows], ensure_ascii=False))[:16]
    e = lambda x: html.escape(str(x), quote=True)
    body, current = [], None
    order = {}
    for r in rows:  # pages and sections keep the order in which the drafts list them
        order.setdefault(r[0], len(order))
        order.setdefault((r[0], r[1]), len(order))
    for page, section, lang, u, problems, findings, source in sorted(
            rows, key=lambda r: (order[r[0]], order[(r[0], r[1])], r[3].get("id", ""), r[2])):
        if page != current:
            body.append(f"<h2>Page {e(page)}</h2>")
            current, current_section = page, None
        if section != current_section:
            body.append(f"<h3>{e(section)}</h3>")
            current_section = section
        uid, text = u.get("id", ""), u.get("text") or ""
        ref, href = _reference(sources, uid)
        ref_html = f'<a href="{e(href)}" rel="noopener">{e(ref)}</a>' if href else e(ref)
        terms = ", ".join(_glossary_terms(source or "", root)) or "none"
        items = [f'<li class="error">Blocking: {e(p)}</li>' for p in problems]
        items += [f'<li class="{f.severity}">{"Error" if f.severity == "error" else "Warning"} {e(f.code)}: {e(f.message)}</li>' for f in findings]
        status = "blocked by automated checks" if problems or semantic.error_messages(findings) else "passes automated checks"
        findings_html = f'<ul class="findings">{"".join(items)}</ul>' if items else '<p class="clean">No automated finding.</p>'
        key = f"{lang}:{uid}"
        dir_ = "rtl" if lang == "ar" else "ltr"
        criteria = "".join(f'<option value="{c}">{c}</option>' for c in i18n.ESCALATION_CRITERIA)
        body.append(f"""<article class="unit" data-key="{e(key)}" data-unit="{e(uid)}" data-lang="{lang}" data-draft-sha="{i18n.fingerprint(text)}"
  data-source-sha="{e(u.get('source_sha256', ''))}" data-warnings='{e(json.dumps(semantic.warning_codes(findings)))}'>
 <header><code>{e(uid)}</code><span>Language: {lang}</span><span>Kind: {e(u.get('kind', ''))}</span><span>Status: {e(u.get('status', ''))} (not approved)</span></header>
 <div class="texts">
  <div><h4>English source</h4><span lang="en">{e(source or '(missing)')}</span></div>
  <div><h4>{'Arabic' if lang == 'ar' else 'French'} draft (AI-assisted, {e((u.get('draft') or {}).get('by', ''))})</h4><span lang="{lang}" dir="{dir_}">{e(text)}</span></div>
  <div><h4>Checks</h4><p>{status}</p>{findings_html}</div>
 </div>
 <p>Source reference: {ref_html}. Glossary concepts: {e(terms)}.{(' Note: ' + e(u['note'])) if u.get('note') else ''}</p>
 <details><summary>Fingerprints</summary><p>Source SHA-256 <code>{e(u.get('source_sha256', ''))}</code><br>Draft SHA-256 <code>{i18n.fingerprint(text)}</code></p></details>
 <fieldset><legend>Your decision for {e(uid)} ({lang})</legend>
  <label><input type="radio" name="d-{e(key)}" value="approve"> Approve the final text below</label>
  <label><input type="radio" name="d-{e(key)}" value="revise"> Request revision</label>
  <label><input type="radio" name="d-{e(key)}" value="reject"> Reject</label>
  <label><input type="radio" name="d-{e(key)}" value="escalate"> Specialist question</label>
  <label>Criterion <select class="criterion"><option value="">(only for a specialist question)</option>{criteria}</select></label>
  <label for="t-{e(key)}">Final text (edit to correct; an edited text is re-checked before it can be recorded)</label>
  <textarea id="t-{e(key)}" class="final" lang="{lang}" dir="{dir_}">{e(text)}</textarea>
  <label for="c-{e(key)}">Comment</label>
  <textarea id="c-{e(key)}" class="comment"></textarea>
 </fieldset>
</article>""")
    terms = [(ws["language"], t) for ws in workspaces for t in ws.get("term_candidates", [])]
    if terms:
        trs = "".join(f'<tr><td><code>{e(t.get("id", ""))}</code></td><td>{lang}</td>'
                      f'<td lang="{lang}" dir="{"rtl" if lang == "ar" else "ltr"}">{e(t.get("label", ""))}</td><td>{e(t.get("basis", ""))}</td></tr>'
                      for lang, t in sorted(terms, key=lambda x: (x[1].get("id", ""), x[0])))
        body.append('<h2>Terminology candidates</h2><p>For information. Glossary labels are approved separately, through '
                    'the same human approval; they are not part of the decisions exported from this page.</p>'
                    '<div class="scroll"><table><thead><tr><th scope="col">Term</th><th scope="col">Language</th><th scope="col">Candidate label</th>'
                    f'<th scope="col">Basis</th></tr></thead><tbody>{trs}</tbody></table></div>')
    n = len(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="workspace" content="{i18n.DRAFT_MARKER}">
<meta name="package-id" content="{package_id}">
<title>Translation review package</title>
<style>{PACKAGE_CSS}</style>
</head>
<body>
<main>
<h1>Translation review package</h1>
<div class="banner" role="note">
<p><strong>Unpublished drafts. Not approved.</strong> These Arabic and French texts were prepared with AI assistance for your
review under TMA-DEC-008. Opening, reading or downloading this page approves nothing, and no decision is preselected.</p>
<p>For each unit: read the English source and the draft, check the findings, then choose a decision. You may correct the
final text. Export your decisions when you are done. Approvals exist only once your exported decisions are recorded in an
approval commit you make; publication is a further, separate step.</p>
<p>Automated findings are review aids: a warning is a possible change of meaning, not a verdict, and a clean result is not
proof that the translation is right.</p>
</div>
<p>{n} draft units · generated {e(generated)} · package {package_id} · policy {i18n.GOVERNANCE_POLICY}.
Keep this file private: it must not be committed to the repository or published.</p>
{''.join(body)}
</main>
<div class="bar"><span id="count" aria-live="polite"></span><button type="button" id="export">Export my decisions (JSON)</button></div>
<script>{PACKAGE_JS}</script>
</body>
</html>
"""


# ─── Recording the owner's decisions ──────────────────────────────────────

def record(decisions, workspaces, reviewer, root=ROOT, today=None):
    """Write approved units into i18n/<lang>/*.json and the other decisions back into the draft workspaces.
    Returns (approved unit ids, other decision ids). Raises ReviewError, changing nothing, on any problem."""
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        raise ReviewError("refusing to record approvals in CI: an approval is a human act, never an automated one")
    today = today or datetime.date.today()
    root = Path(root)
    errors, _ = i18n.validate(root, today=today)
    if errors:
        raise ReviewError("the translation layer does not validate; fix it first:\n  " + "\n  ".join(errors[:5]))
    reviewers = i18n.load_reviewers(root)
    if reviewer not in reviewers:
        raise ReviewError(f"{reviewer!r} is not a registered reviewer (i18n/reviewers.json); registration is a separate owner decision")
    if decisions.get("kind") != "translation-review-decisions":
        raise ReviewError("not a decisions file exported from a review package")
    by_key = {(ws["language"], u["id"]): (ws, u) for ws in workspaces for u in ws.get("units", [])}
    glossary_version = i18n._load(root / "i18n" / "glossary.json")["version"]
    sources = i18n.Sources(root)
    catalogs, approved, others, problems = {}, [], [], []
    for d in decisions.get("decisions", []):
        lang, uid = d.get("language"), d.get("unit")
        if (lang, uid) not in by_key:
            problems.append(f"{lang}:{uid}: not in the draft workspaces given")
            continue
        ws, u = by_key[(lang, uid)]
        if d.get("decision") not in DECISIONS:
            problems.append(f"{lang}:{uid}: unknown decision {d.get('decision')!r}")
            continue
        if lang not in reviewers[reviewer].get("languages", []):
            problems.append(f"{lang}:{uid}: {reviewer} is not registered for {lang}")
            continue
        source = _source(sources, uid)
        if source is None or d.get("source_sha256") != i18n.fingerprint(source) or u.get("source_sha256") != i18n.fingerprint(source):
            problems.append(f"{lang}:{uid}: the English source changed after the package was built; rebuild it")
            continue
        if d.get("draft_sha256") != i18n.fingerprint(u.get("text") or ""):
            problems.append(f"{lang}:{uid}: the draft changed after the package was built; rebuild it")
            continue
        if d["decision"] != "approve":
            u["status"] = {"revise": "NEEDS_REVISION", "reject": "REJECTED", "escalate": "DRAFT"}[d["decision"]]
            u["note"] = (f"{d['decision']} by {reviewer} on {d.get('decided_at')}"
                         + (f" [{d['criterion']}]" if d.get("criterion") else "") + (f": {d['comment']}" if d.get("comment") else ""))
            if d["decision"] == "revise" and d.get("text") and d["text"] != u.get("text"):
                u["text"] = i18n.nfc(d["text"])  # the reviewer's suggested wording, still a draft
            others.append(f"{lang}:{uid}")
            continue
        text = i18n.nfc(d.get("text") or "")
        terms = i18n.term_forms(lang, root, today)
        found = semantic.findings(source, text, lang, terms, i18n.linked_forms(sources, uid))
        if semantic.error_messages(found):
            problems.append(f"{lang}:{uid}: {semantic.error_messages(found)[0]}")
            continue
        if semantic.warning_codes(found) != sorted(d.get("shown_warnings") or []):
            problems.append(f"{lang}:{uid}: the warnings for this text were not the ones shown; rebuild the package "
                            "to review the corrected text")
            continue
        unit = {"id": uid, "kind": u["kind"], "status": "APPROVED", "text": text, "source_sha256": i18n.fingerprint(source),
                "draft": dict(u["draft"]),
                "approval": {"unit": uid, "language": lang, "reviewer": reviewer, "decision": "approved",
                             "reviewed_at": d.get("decided_at"), "policy": i18n.GOVERNANCE_POLICY,
                             "source_sha256": i18n.fingerprint(source), "translation_sha256": i18n.fingerprint(text),
                             "glossary_version": glossary_version, "acknowledged_warnings": semantic.warning_codes(found)}}
        if text != u.get("text"):
            unit["approval"]["revised"] = True  # the reviewer corrected the draft before approving it
        if u.get("name_basis"):
            unit["name_basis"] = u["name_basis"]
        kind = "messages" if ":" not in uid else "content"
        path = root / "i18n" / lang / f"{kind}.json"
        catalog = catalogs.setdefault(path, i18n._load(path))
        catalog["units"] = [x for x in catalog["units"] if x.get("id") != uid] + [unit]
        u["status"], u["note"] = "DRAFT", f"approved by {reviewer} on {d.get('decided_at')}; recorded in i18n/{lang}/{kind}.json"
        approved.append(f"{lang}:{uid}")
    if problems:
        raise ReviewError("nothing was recorded:\n  " + "\n  ".join(problems))
    backups = {p: p.read_bytes() for p in catalogs}
    for path, catalog in catalogs.items():
        catalog["units"].sort(key=lambda x: x["id"])
        path.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    errors, _ = i18n.validate(root, today=today)
    if errors:
        for path, data in backups.items():
            path.write_bytes(data)
        raise ReviewError("the recorded approvals do not validate; nothing was recorded:\n  " + "\n  ".join(errors[:5]))
    return approved, others


def provenance(root=ROOT):
    """[(lang:unit, reviewer, commit, author, date, signature status)] for every committed approval: the commit
    that introduced its translation fingerprint, and git's signature status (G good, U good but untrusted key,
    N none, E cannot check, B bad). Advisory: a repository cannot prove who a pseudonymous reviewer is; a
    signature by a key only the owner holds is the strongest evidence available. See
    docs/TRANSLATION_APPROVAL_SECURITY.md."""
    out = []
    for path in sorted(Path(root).glob("i18n/*/*.json")):
        if path.parent.name == "en" or path.name not in ("messages.json", "content.json"):
            continue
        for u in i18n._load(path).get("units", []):
            a = u.get("approval") or {}
            sha = a.get("translation_sha256")
            if not sha:
                continue
            log = subprocess.run(["git", "log", "--reverse", "-S", sha, "--format=%h|%an|%cI|%G?", "--", str(path.relative_to(root))],
                                 cwd=root, capture_output=True, text=True).stdout.splitlines()
            commit, author, date, sig = (log[0].split("|") + ["", "", "", ""])[:4] if log else ("uncommitted", "", "", "")
            out.append((f"{path.parent.name}:{u['id']}", a.get("reviewer"), commit, author, date, sig))
    return out


def main(argv):
    if argv[:1] == ["provenance"]:
        rows = provenance()
        for row in rows:
            print(" | ".join(map(str, row)))
        print(f"{len(rows)} committed approval(s). Advisory: signature status is evidence, not proof of identity.")
        return 0
    if len(argv) < 2 or argv[0] not in ("check", "package", "record"):
        print(__doc__)
        return 2
    try:
        if argv[0] == "check":
            bad = 0
            for path in argv[1:]:
                ws = load_drafts(path)
                for u, problems, findings, _ in check(ws):
                    for p in problems:
                        print("BLOCK", ws["language"], u.get("id"), p)
                    for f in findings:
                        print(f.severity.upper(), ws["language"], u.get("id"), f.code, f.message)
                    bad += bool(problems or semantic.error_messages(findings))
            print(f"{bad} unit(s) blocked; warnings are for the reviewer. Nothing is approved by this check.")
            return 1 if bad else 0
        if argv[0] == "package":
            out = Path(argv[argv.index("--out") + 1])
            paths = [a for a in argv[1:argv.index("--out")]]
            if ROOT.resolve() in out.resolve().parents:
                raise ReviewError("the review package must be written outside the repository")
            out.write_text(build_package([load_drafts(p) for p in paths]), encoding="utf-8")
            print(f"wrote {out} (private; not an approval)")
            return 0
        decisions = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        paths = argv[argv.index("--drafts") + 1:argv.index("--reviewer")]
        workspaces = [load_drafts(p) for p in paths]
        approved, others = record(decisions, workspaces, argv[argv.index("--reviewer") + 1])
        for path, ws in zip(paths, workspaces):
            Path(path).write_text(json.dumps(ws, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"recorded {len(approved)} approval(s) and {len(others)} other decision(s). Review the diff and commit it yourself.")
        return 0
    except (ReviewError, ValueError, OSError) as exc:
        print("ERROR", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
