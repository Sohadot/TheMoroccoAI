#!/usr/bin/env python3
"""Read and check TheMoroccoAI registry from its published JSON alone.

    python3 registry_consumer.py verify
    python3 registry_consumer.py relationship cndp lists_in_framework law-09-08
    python3 registry_consumer.py gap GAP-03
    python3 registry_consumer.py q8
    python3 registry_consumer.py q9
    python3 registry_consumer.py q8 --json

    --source URL or directory   where the site is published (default https://themoroccoai.com);
                                a directory is read as a local copy of the site

It starts from /data/manifest.json, fetches each file listed there and checks its SHA-256, then checks every
reference and recomputes what the derived files claim, using only the rules published in matrix.json,
gaps.json and reference-state.json ("derivation") and documented at /data/. It does not import the site's code. Every command runs these
checks first and stops if the data is inconsistent.

Exit status: 0 when the data is consistent; 1 when it is not (each problem is printed); 2 when a file cannot be
fetched, an argument is wrong or what was asked for is not in the data.

Python 3.10 or later, standard library only.
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

DEFAULT_SOURCE = "https://themoroccoai.com"
MANIFEST = "/data/manifest.json"


class FetchError(Exception):
    pass


class Registry:
    """The published files, loaded and checked against the manifest."""

    def __init__(self, source):
        self.source = source.rstrip("/")
        self.problems = []
        self.manifest = json.loads(self._fetch(MANIFEST))
        self.files = {}
        self.raw = {}
        for res in self.manifest["resources"]:
            raw = self._fetch(res["path"])
            self.raw[res["path"]] = raw
            if hashlib.sha256(raw).hexdigest() != res["sha256"]:
                self.problems.append(f"{res['path']}: SHA-256 differs from the manifest; the file comes from another build or was altered")
            self.files[res["path"]] = json.loads(raw)
        need = ("/data/evidence.json", "/data/ontology.json", "/data/gaps.json", "/registry/matrix/matrix.json", "/registry/gaps/gaps.json",
                "/registry/reference-state.json")
        missing = [p for p in need if p not in self.files]
        if missing:
            raise FetchError(f"the manifest does not list {', '.join(missing)}")
        self.evidence = self.files["/data/evidence.json"]
        self.ontology = self.files["/data/ontology.json"]
        self.gaps = self.files["/data/gaps.json"]
        self.matrix = self.files["/registry/matrix/matrix.json"]
        self.gap_register = self.files["/registry/gaps/gaps.json"]
        self.reference = self.files["/registry/reference-state.json"]
        self.records = {r["evidence_id"]: r for r in self.evidence["records"]}
        self.entities = {e["id"]: e for e in self.ontology["entities"]}
        self.relationships = self.ontology["relationships"]

    def _fetch(self, path):
        if "://" not in self.source:
            target = Path(self.source) / path.lstrip("/")
            try:
                return target.read_bytes()
            except OSError as exc:
                raise FetchError(f"cannot read {target}: {exc}") from exc
        url = self.source + path
        req = urllib.request.Request(url, headers={"User-Agent": "TheMoroccoAI-registry-consumer-example"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except OSError as exc:
            raise FetchError(f"cannot fetch {url}: {exc}") from exc

    # ─── Checks ─────────────────────────────────────────────────────────────

    def verify(self):
        """Every problem found in the published data; an empty list means it is consistent."""
        p = list(self.problems)
        p += self._check_versions()
        p += self._check_definitions()
        p += self._check_references()
        if not p:  # recomputing derived data needs sound references
            p += self._check_support()
            p += self._check_matrix()
            p += self._check_gaps()
            p += self._check_reference()
        return p

    def _check_versions(self):
        v, a = self.manifest["registry_version"], self.manifest["as_of"]
        found = [("evidence.json", self.evidence.get("version"), self.evidence.get("as_of")),
                 ("ontology.json", self.ontology.get("version"), self.ontology.get("as_of")),
                 ("matrix.json", self.matrix.get("registry_version"), self.matrix.get("as_of")),
                 ("registry/gaps/gaps.json", self.gap_register.get("registry_version"), self.gap_register.get("as_of")),
                 ("reference-state.json", self.reference.get("registry_version"), self.reference.get("as_of"))]
        return [f"{name}: version {fv} as of {fa}, but the manifest is version {v} as of {a}" for name, fv, fa in found if (fv, fa) != (v, a)]

    def _check_definitions(self):
        """Each defined value must be defined in its own file, or for record types and bases in the manifest's
        vocabularies; an undefined one is not guessed at."""
        p = []
        ev, on = self.evidence, self.ontology

        def defined(value, table, what, where):
            if value is not None and value not in table:
                p.append(f"{where}: {what} {value!r} is not defined in the published data")

        vocab = self.manifest["vocabularies"]
        for r in ev["records"]:
            defined(r.get("source_type"), vocab["source_type"], "source type", r["evidence_id"])
            defined(r.get("evidence_type"), vocab["evidence_type"], "evidence type", r["evidence_id"])
            defined(r.get("status_basis"), vocab["status_basis"], "status basis", r["evidence_id"])
            defined(r.get("classification"), ev["classifications"], "classification", r["evidence_id"])
            defined(r.get("verification_status"), ev["verification_statuses"], "verification status", r["evidence_id"])
            defined(r.get("status_evidence"), on["lifecycle_stages"], "declared stage", r["evidence_id"])
        for e in on["entities"]:
            defined(e.get("type"), on["entity_types"], "entity type", e["id"])
            defined(e.get("lifecycle"), on["lifecycle_stages"], "lifecycle stage", e["id"])
            defined(e.get("project_kind"), on["project_kinds"], "project kind", e["id"])
            defined(e.get("origin"), on["origins"], "origin", e["id"])
            defined(e.get("domain"), on["domains"], "domain", e["id"])
        for r in self.relationships:
            where = f"relationship {r['subject']}|{r['predicate']}|{r['object']}"
            defined(r.get("predicate"), on["predicates"], "predicate", where)
            defined(r.get("classification"), ev["classifications"], "classification", where)
        for g in self.gaps["gaps"]:
            defined(g.get("state"), self.gaps["states"], "state", g["id"])
        return p

    def _check_references(self):
        p = []
        recs, ents = self.records, self.entities

        def records_exist(ids, where, field):
            for x in ids or []:
                if x not in recs:
                    p.append(f"{where}: {field} cites {x}, which is not in evidence.json")

        def entities_exist(ids, where, field):
            for x in ids or []:
                if x not in ents:
                    p.append(f"{where}: {field} names {x}, which is not in ontology.json")

        if len(recs) != len(self.evidence["records"]):
            p.append("evidence.json: an evidence_id is used twice")
        if len(ents) != len(self.ontology["entities"]):
            p.append("ontology.json: an entity id is used twice")
        for r in self.evidence["records"]:
            rid = r["evidence_id"]
            entities_exist(r.get("related_entities"), rid, "related_entities")
            entities_exist(r.get("associated_entities"), rid, "associated_entities")
            entities_exist([r["source_entity"]] if r.get("source_entity") else [], rid, "source_entity")
            records_exist(r.get("superseded_by"), rid, "superseded_by")
            if not r.get("retrieval_date"):
                p.append(f"{rid}: no retrieval_date")
        for e in self.ontology["entities"]:
            records_exist(e.get("evidence"), e["id"], "evidence")
            records_exist(e.get("lifecycle_evidence"), e["id"], "lifecycle_evidence")
            records_exist(e.get("origin_evidence"), e["id"], "origin_evidence")
            for a in e.get("attributes") or []:
                records_exist([a["evidence"]] if isinstance(a.get("evidence"), str) else a.get("evidence"), e["id"], f"attribute {a.get('name')!r}")
        seen = set()
        preds = self.ontology["predicates"]
        for r in self.relationships:
            key = (r["subject"], r["predicate"], r["object"])
            where = "relationship " + "|".join(key)
            if key in seen:
                p.append(f"{where}: appears twice")
            seen.add(key)
            entities_exist([r["subject"], r["object"]], where, "subject or object")
            if not r.get("evidence"):
                p.append(f"{where}: cites no evidence")
            records_exist(r.get("evidence"), where, "evidence")
            spec = preds.get(r["predicate"])
            if spec and r["subject"] in ents and r["object"] in ents:
                if ents[r["subject"]]["type"] not in spec["subject"] or ents[r["object"]]["type"] not in spec["object"]:
                    p.append(f"{where}: {ents[r['subject']]['type']} → {ents[r['object']]['type']} is not allowed for {r['predicate']}")
        for g in self.gaps["gaps"]:
            entities_exist(g.get("entities"), g["id"], "entities")
            for item in g.get("established") or []:
                records_exist(item.get("evidence"), g["id"], "established")
            records_exist(g.get("assessed_records"), g["id"], "assessed_records")
            records_exist(g.get("resolved_by"), g["id"], "resolved_by")
        return p

    def _check_support(self):
        """The two validator rules published in the manifest (classification_support)."""
        p, rules = [], self.manifest["classification_support"]
        for r in self.relationships:
            allowed = rules["relationship"].get(r["classification"])
            cited = {self.records[x]["classification"] for x in r["evidence"]}
            where = f"relationship {r['subject']}|{r['predicate']}|{r['object']}"
            if r["classification"] == "INDEPENDENT ANALYSIS":
                if len(r["evidence"]) < 2 or not str(r.get("note", "")).strip():
                    p.append(f"{where}: INDEPENDENT ANALYSIS needs at least two records and a note")
            elif isinstance(allowed, list) and not cited & set(allowed):
                p.append(f"{where}: classified {r['classification']} but cites no {' or '.join(allowed)} record")
        for e in self.ontology["entities"]:
            stage = e.get("lifecycle")
            if stage not in rules["lifecycle"]:
                continue
            cited = [self.records[x] for x in e.get("lifecycle_evidence") or []]
            if not any(r["classification"] in rules["lifecycle"][stage] for r in cited):
                p.append(f"{e['id']}: stage {stage} is not supported by a {' or '.join(rules['lifecycle'][stage])} record")
            if stage in rules["status_stages"] and not any(r.get("status_evidence") == stage for r in cited):
                p.append(f"{e['id']}: stage {stage} is not declared by any of its lifecycle_evidence records")
        return p

    def stage_label(self, eid):
        """object.stage, as defined in matrix.json (derivation["object.stage"])."""
        spec, e = self.matrix["derivation"]["object.stage"], self.entities[eid]
        if not e.get("lifecycle"):
            return None
        label = spec["labels"][e["lifecycle"]]
        if e["lifecycle"] in ("operational", "pilot"):
            bases = {self.records[x].get("status_basis") for x in e.get("lifecycle_evidence") or []
                     if self.records[x].get("status_evidence") == e["lifecycle"]}
            if bases == {"public-availability-observed"}:
                label += spec["availability_suffix"]
        return label

    # ─── Derived data, recomputed from the canonical files ──────────────────

    def matrix_rows(self):
        """The matrix recomputed from ontology.json and evidence.json with the rules published in matrix.json."""
        d = self.matrix["derivation"]
        sel, doc, basis = d["row_selection"], d["documented_as"], d["documentation_basis"]
        rows = []
        for r in self.relationships:
            subj, obj = self.entities[r["subject"]], self.entities[r["object"]]
            if subj["type"] not in sel["subject_types"] or obj["type"] not in sel["object_types"]:
                continue
            if r["classification"] == "VERIFIED FACT":
                level = doc["verified_fact_by_relationship"].get(r["predicate"], doc["verified_fact_otherwise"])
            else:
                level = doc["by_classification"][r["classification"]]
            names = basis["assignment"]
            if r["predicate"] not in basis["formal_act_relationships"]:
                how = names["not_a_formal_act"]
            elif all(self.records[x]["evidence_type"] in basis["announcement_evidence_types"] for x in r["evidence"]):
                how = names["every_record_an_announcement"]
            else:
                how = names["otherwise"]
            rows.append({"id": f"{r['subject']}|{r['predicate']}|{r['object']}", "subject": r["subject"], "relationship": r["predicate"],
                         "object": r["object"], "object_lifecycle": obj.get("lifecycle"), "object_stage": self.stage_label(r["object"]),
                         "classification": r["classification"],
                         "documented_as": level, "documentation_basis": how, "evidence": list(r["evidence"])})
        return sorted(rows, key=lambda x: (x["subject"], x["relationship"], x["object"]))

    def _check_matrix(self):
        p = []
        mine = {r["id"]: r for r in self.matrix_rows()}
        published = {r["id"]: r for r in self.matrix["rows"]}
        for rid in sorted(set(mine) - set(published)):
            p.append(f"matrix.json: missing row {rid}")
        for rid in sorted(set(published) - set(mine)):
            p.append(f"matrix.json: row {rid} does not follow from ontology.json")
        for rid in sorted(set(mine) & set(published)):
            a, b = mine[rid], published[rid]
            got = {"subject": b["subject"]["id"], "relationship": b["relationship"], "object": b["object"]["id"],
                   "object_lifecycle": b["object"]["lifecycle"], "object_stage": b["object"]["stage"], "classification": b["classification"],
                   "documented_as": b["documented_as"], "documentation_basis": b["documentation_basis"],
                   "evidence": [e["id"] for e in b["evidence"]]}
            for k, v in got.items():
                if a[k] != v:
                    p.append(f"matrix.json: row {rid} has {k} {v!r}; the published data gives {a[k]!r}")
            for e in b["evidence"]:
                rec = self.records.get(e["id"])
                if rec and any(e[k] != rec[k] for k in ("source_url", "source_type", "evidence_type", "publication_date", "retrieval_date")):
                    p.append(f"matrix.json: row {rid} describes {e['id']} differently from evidence.json")
        return p

    def _formal_act_rows(self):
        acts = self.matrix["derivation"]["documentation_basis"]["formal_act_relationships"]
        return [r for r in self.matrix_rows() if r["relationship"] in acts]

    def announcement_only(self):
        only = self.matrix["derivation"]["documentation_basis"]["assignment"]["every_record_an_announcement"]
        return [r for r in self.matrix_rows() if r["documentation_basis"] == only]

    def fingerprint(self, gap):
        """A gap's digest, computed as published in gaps.json (derivation.assessed_fingerprint)."""
        spec = self.gap_register["derivation"]["assessed_fingerprint"]
        ents = set(gap.get("entities") or [])
        if not ents:
            return None
        data = {
            "records": sorted(([r["evidence_id"]] + [r.get(f) for f in spec["record_fields"]]
                               for r in self.evidence["records"] if ents & set(r.get("related_entities") or [])), key=lambda x: x[0]),
            "entities": sorted(([e["id"]] + [e.get(f) for f in spec["entity_fields"]]
                                for e in self.ontology["entities"] if e["id"] in ents), key=lambda x: x[0]),
            "relationships": sorted([r["subject"], r["predicate"], r["object"], r["classification"], r["evidence"], r.get("note")]
                                    for r in self.relationships if ents & {r["subject"], r["object"]}),
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]

    def run_checks(self, gap):
        """(description, triggered) for each of the gap's data checks, as defined in gaps.json (derivation.checks)."""
        out = []
        for c in gap.get("checks") or []:
            t = c["type"]
            if t == "no_status_basis":
                hit = [x for x in self.entities[c["entity"]].get("lifecycle_evidence") or [] if self.records[x].get("status_basis") in c["bases"]]
                out.append((f"no status record for {c['entity']} with basis {' or '.join(c['bases'])}", bool(hit)))
            elif t == "lifecycle_in":
                moved = [e for e in c["entities"] if self.entities[e].get("lifecycle") not in c["stages"]]
                out.append((f"{', '.join(c['entities'])} still {' or '.join(c['stages'])}", bool(moved)))
            elif t == "no_ai_application_link":
                linked = [r for r in self.relationships if c["entity"] in (r["subject"], r["object"]) and
                          self.entities[r["object"] if r["subject"] == c["entity"] else r["subject"]].get("project_kind") == "ai-application"]
                out.append((f"no AI application linked to {c['entity']}", bool(linked)))
            elif t == "computed_relationships" and c.get("list") == "announcement_only":
                out.append(("at least one relationship documented only by announcements", not self.announcement_only()))
            else:
                raise ValueError(f"{gap['id']}: check {t!r} is not defined in gaps.json; this consumer does not interpret it")
        return out

    def _check_gaps(self):
        p = []
        derived = {g["id"]: g for g in self.gap_register["gaps"]}
        for g in self.gaps["gaps"]:
            gid = g["id"]
            if gid not in derived:
                p.append(f"registry/gaps/gaps.json: {gid} is missing")
                continue
            d = derived[gid]
            for k in ("question", "state", "unestablished", "evidence_needed", "established", "assessed"):
                if d.get(k) != g.get(k):
                    p.append(f"registry/gaps/gaps.json: {gid} {k} differs from data/gaps.json")
            if [e["id"] for e in d["entities"]] != g["entities"]:
                p.append(f"registry/gaps/gaps.json: {gid} entities differ from data/gaps.json")
            computed = any(c["type"] == "computed_relationships" for c in g.get("checks") or [])
            if computed:
                listed = [r["id"] for r in d.get("relationships") or []]
                mine = [r["id"] for r in self.announcement_only()]
                if listed != mine:
                    p.append(f"registry/gaps/gaps.json: {gid} lists {len(listed)} relationships; the published data gives {len(mine)}")
                formal = self._formal_act_rows()
                if d.get("formal_act_relationships") != len(formal):
                    p.append(f"registry/gaps/gaps.json: {gid} states {d.get('formal_act_relationships')} formal-act relationships; the published data gives {len(formal)}")
            ents = set(g["entities"])
            for item in g.get("established") or []:
                for x in item["evidence"]:
                    if ents and not ents & set(self.records[x]["related_entities"]):
                        p.append(f"{gid}: {x} is cited as established but does not concern the gap's entities")
            if ents:
                about = {r["evidence_id"] for r in self.evidence["records"] if ents & set(r["related_entities"])}
                new = sorted(about - set(g.get("assessed_records") or []))
                if new:
                    p.append(f"{gid}: {', '.join(new)} concern this gap but postdate its assessment")
                if self.fingerprint(g) != g.get("assessed_fingerprint"):
                    p.append(f"{gid}: the data it rests on has changed since it was assessed (digest {g.get('assessed_fingerprint')}, now {self.fingerprint(g)})")
            try:
                triggered = [desc for desc, hit in self.run_checks(g) if hit]
            except ValueError as exc:
                p.append(str(exc))
                continue
            if triggered and g["state"] == "open":
                p.append(f"{gid}: open, but the data no longer satisfies: {'; '.join(triggered)}")
            if "entity_assessments" in g or d.get("entity_assessments"):
                if d.get("entity_assessments") != g.get("entity_assessments"):
                    p.append(f"registry/gaps/gaps.json: {gid} entity_assessments differ from data/gaps.json")
                p += self._check_entity_assessments(g)
        for gid in sorted(set(derived) - {g["id"] for g in self.gaps["gaps"]}):
            p.append(f"registry/gaps/gaps.json: {gid} is not in data/gaps.json")
        return p

    def resolution_path(self, assessment):
        """The resolution path an entity's assessment meets, as published in gaps.json (entity_assessment.resolution);
        None means its operational status is unknown in the registry."""
        d, stage = assessment["dimensions"], self.entities[assessment["entity"]].get("lifecycle")
        if d["operational_activity"] and d["outputs"] and (d["staffing"] or d["premises"]) and stage in ("pilot", "operational"):
            return "operating"
        if d["documented_non_commencement"] and not d["operational_activity"] and not d["outputs"] \
                and stage not in ("pilot", "operational", "discontinued"):
            return "not_commenced"
        if d["documented_discontinuation"] and d["operational_activity"] and stage == "discontinued":
            return "discontinued"
        return None

    def _check_entity_assessments(self, g):
        spec, p = self.gap_register["entity_assessment"], []
        gid = g["id"]
        if [a["entity"] for a in g["entity_assessments"]] != g["entities"]:
            p.append(f"{gid}: entity_assessments do not list the gap's entities in order")
        for a in g["entity_assessments"]:
            at = f"{gid}: {a['entity']}"
            if a["state"] not in spec["states"]:
                p.append(f"{at} has undefined state {a['state']!r}")
            if set(a["dimensions"]) != set(spec["dimension_order"]) or set(spec["dimensions"]) != set(spec["dimension_order"]):
                p.append(f"{at} does not list exactly the defined dimensions")
            cited = {x for xs in a["dimensions"].values() for x in xs}
            for x in sorted(cited):
                r = self.records.get(x)
                if r is None or a["entity"] not in r["related_entities"] or r["classification"] != "VERIFIED FACT":
                    p.append(f"{at} cites {x}, which is not a VERIFIED FACT record about it")
            if a["dimensions"]["documented_non_commencement"] and (a["dimensions"]["operational_activity"] or a["dimensions"]["outputs"]):
                p.append(f"{at} records both non-commencement and activity or outputs")
            path = self.resolution_path(a)
            if a["state"] == "resolved" and (not path or not a.get("resolved_by") or not set(a["resolved_by"]) <= cited):
                p.append(f"{at} is resolved but does not meet a resolution path with the records it cites")
            if a["state"] == "open" and path:
                p.append(f"{at} is open but meets the {path} resolution path")
        if g["state"] == "resolved" and any(a["state"] != "resolved" for a in g["entity_assessments"]):
            p.append(f"{gid}: resolved while an entity it assesses is open")
        return p

    # ─── Reference answers ───────────────────────────────────────────────────

    def reference_state(self):
        """Every reproducible field of reference-state.json, recomputed from evidence.json, ontology.json and gaps.json by the
        rules published in its derivation. The manifest is not used."""
        ev, on, gaps = self.evidence, self.ontology, self.gaps
        recs = ev["records"]

        def declaring(e):
            return [x for x in e.get("lifecycle_evidence") or [] if self.records[x].get("status_evidence") == e["lifecycle"]]

        def bases(ids):
            return sorted({self.records[x]["status_basis"] for x in ids if self.records[x].get("status_basis")})

        lifecycle = [{"id": e["id"], "type": e["type"], "project_kind": e.get("project_kind"), "lifecycle": e["lifecycle"],
                      "lifecycle_evidence": list(e.get("lifecycle_evidence") or []), "status_bases": bases(declaring(e))}
                     for e in sorted(on["entities"], key=lambda e: e["id"]) if e["type"] in ("project", "model", "dataset")]
        combos = {}
        for x in lifecycle:
            k = (x["type"], x["project_kind"], x["lifecycle"])
            combos[k] = combos.get(k, 0) + 1
        operating = [{**x, "status_evidence_records": declaring(self.entities[x["id"]]), "counts_as_ai_deployment": x["project_kind"] == "ai-application"}
                     for x in lifecycle if x["lifecycle"] in ("operational", "pilot")]
        by_basis = {}
        for x in operating:
            for b in bases(x["status_evidence_records"]):
                by_basis.setdefault(b, []).append(x["id"])
        open_gaps = [g for g in gaps["gaps"] if g["state"] == "open"]
        in_gaps = {}
        for g in open_gaps:
            for e in g["entities"]:
                in_gaps.setdefault(e, []).append(g["id"])
        targets = []
        for r in sorted((r for r in recs if r["classification"] == "OFFICIAL TARGET"), key=lambda r: r["evidence_id"]):
            inits = []
            for i in (e for e in r["related_entities"] if self.entities[e]["type"] == "initiative"):
                gap = next((g for g in gaps["gaps"] if i in g["entities"]), None)
                inits.append({"id": i, "covering_gap": gap["id"] if gap else None, "gap_state": gap["state"] if gap else None})
            targets.append({"evidence_id": r["evidence_id"], "target_year": r["target_year"], "initiatives": inits})

        def triple(r):
            return f"{r['subject']}|{r['predicate']}|{r['object']}"

        return {
            "registry_version": ev["version"], "as_of": ev["as_of"],
            "derived_from": [{"path": path, "sha256": hashlib.sha256(self.raw[path]).hexdigest()}
                             for path in ("/data/evidence.json", "/data/ontology.json", "/data/gaps.json")],
            "counts": {
                "records": len(recs), "entities": len(on["entities"]), "relationships": len(self.relationships),
                "records_by_classification": {c: sum(1 for r in recs if r["classification"] == c) for c in ev["classifications"]},
                "records_by_verification_status": {s: sum(1 for r in recs if r["verification_status"] == s) for s in ev["verification_statuses"]},
                "relationships_by_classification": {c: sum(1 for r in self.relationships if r["classification"] == c) for c in ev["classifications"]},
                "entities_by_type": {t: sum(1 for e in on["entities"] if e["type"] == t) for t in on["entity_types"]},
            },
            "superseded_records": [{"evidence_id": r["evidence_id"], "superseded_by": list(r["superseded_by"])}
                                   for r in sorted(recs, key=lambda r: r["evidence_id"]) if r.get("superseded_by")],
            "lifecycle": {"entities": lifecycle,
                          "by_type_and_kind": [{"type": t, "project_kind": k, "lifecycle": s, "count": n}
                                               for (t, k, s), n in sorted(combos.items(), key=lambda kv: (kv[0][0], kv[0][1] or "", kv[0][2]))]},
            "operational_or_pilot": operating,
            "operational_or_pilot_by_status_basis": by_basis,
            "announced_projects_by_kind": {k: sorted(e["id"] for e in on["entities"] if e["type"] == "project" and e.get("project_kind") == k
                                                     and e.get("lifecycle") == "announced") for k in on["project_kinds"]},
            "unresolved_lifecycle": [{"id": x["id"], "type": x["type"], "project_kind": x["project_kind"], "lifecycle_evidence": x["lifecycle_evidence"]}
                                     for x in lifecycle if x["lifecycle"] == "unresolved"],
            "unresolved_origin": [{"id": e["id"], "origin_evidence": list(e.get("origin_evidence") or [])}
                                  for e in sorted(on["entities"], key=lambda e: e["id"]) if e["type"] == "company" and e.get("origin") == "unresolved"],
            "official_targets": targets,
            "open_gaps": [{"id": g["id"], "entities": list(g["entities"]), "assessed": g["assessed"], "assessed_fingerprint": g.get("assessed_fingerprint"),
                           "has_entity_assessments": bool(g.get("entity_assessments"))} for g in open_gaps],
            "entities_in_open_gaps": in_gaps,
            "entity_assessments": [{"gap": g["id"], "assessments": g["entity_assessments"]} for g in gaps["gaps"] if g.get("entity_assessments")],
            "announcement_only_relationships": [{"id": r["id"], "subject": r["subject"], "relationship": r["relationship"], "object": r["object"],
                                                 "classification": r["classification"], "evidence": r["evidence"]} for r in self.announcement_only()],
            "independent_analysis_relationships": [{"id": triple(r), "subject": r["subject"], "relationship": r["predicate"], "object": r["object"],
                                                    "evidence": list(r["evidence"])}
                                                   for r in sorted((r for r in self.relationships if r["classification"] == "INDEPENDENT ANALYSIS"),
                                                                   key=lambda r: (r["subject"], r["predicate"], r["object"]))],
            "records_unverified_claim": sorted(r["evidence_id"] for r in recs if r["classification"] == "UNVERIFIED CLAIM"),
            "records_announced_plan": sorted(r["evidence_id"] for r in recs if r["classification"] == "ANNOUNCED PLAN"),
            "records_partially_verified": sorted(r["evidence_id"] for r in recs if r["verification_status"] == "partial"),
        }

    def _check_reference(self):
        """reference-state.json must hold exactly the fields this consumer recomputes (plus its scope, documentation and
        derivation), each with a published rule, and each equal to its recomputed value."""
        p = []
        pub, mine = self.reference, self.reference_state()
        meta = {"scope", "documentation", "derivation"}
        for k in sorted(set(pub) - set(mine) - meta):
            p.append(f"reference-state.json: field {k!r} is not one this consumer can recompute; it is not interpreted")
        for k in sorted(set(mine) - set(pub)):
            p.append(f"reference-state.json: field {k!r} is missing")
        rules = pub.get("derivation") or {}
        allowed = set(rules.get("provenance_values") or {})
        for k in sorted(set(mine)):
            paths = [f"{k}.{s}" for s in mine[k]] if k in ("counts", "lifecycle") else [k]
            for path in paths:
                r = rules.get(path)
                if not isinstance(r, dict) or not r.get("rule") or r.get("provenance") not in allowed:
                    p.append(f"reference-state.json: {path} has no published rule with a defined provenance")
                elif r["provenance"] != "reproducible":
                    p.append(f"reference-state.json: {path} is not marked reproducible, but this consumer recomputes it")
        for k in sorted(set(mine) & set(pub)):
            if pub[k] != mine[k]:
                p.append(f"reference-state.json: {k} does not follow from the canonical files by its published rule")
        return p

    def stage(self, eid):
        """An entity's lifecycle stage with the basis its status records declare, e.g. 'operational (public-availability-observed)'."""
        e = self.entities[eid]
        if not e.get("lifecycle"):
            return None
        bases = sorted({self.records[x]["status_basis"] for x in e.get("lifecycle_evidence") or [] if self.records[x].get("status_basis")})
        return e["lifecycle"] + (f" ({', '.join(bases)})" if bases else "")

    def q8(self):
        """Organisations connected to projects: the reproducible part of Q8."""
        org_types = ("institution", "company")
        rows = [r for r in self.matrix_rows() if self.entities[r["object"]]["type"] == "project" and self.entities[r["subject"]]["type"] in org_types]
        orgs = []
        for sid in sorted({r["subject"] for r in rows}, key=lambda i: self.entities[i]["name"].lower()):
            mine = [r for r in rows if r["subject"] == sid]
            orgs.append({"organisation": sid, "name": self.entities[sid]["name"],
                         "projects": [{"project": r["object"], "relationship": r["relationship"], "documented_as": r["documented_as"],
                                       "lifecycle": r["object_lifecycle"], "stage": self.stage(r["object"]), "classification": r["classification"],
                                       "documentation_basis": r["documentation_basis"]} for r in mine],
                         "evidence": sorted({x for r in mine for x in r["evidence"]})})
        tally = {}
        for r in rows:
            tally[r["documented_as"]] = tally.get(r["documented_as"], 0) + 1
        return {"organisations": len(orgs), "projects": len({r["object"] for r in rows}), "relationships": len(rows),
                "documented_as": dict(sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))),
                "announcement_only": sum(1 for r in rows if r["documentation_basis"] == self.matrix["derivation"]["documentation_basis"]["assignment"]["every_record_an_announcement"]),
                "rows": orgs,
                "not_derivable": ["Each relationship's classification and cited records (editorial, recorded in ontology.json)",
                                  "Each project's lifecycle stage (editorial admission of a record declaring it)"]}

    def q9(self):
        """Official targets, the projects recorded as included, and the gap covering each strategy: the reproducible part of Q9."""
        rows = []
        for r in sorted((r for r in self.evidence["records"] if r["classification"] == "OFFICIAL TARGET"), key=lambda r: r["evidence_id"]):
            for i in (e for e in r["related_entities"] if self.entities[e]["type"] == "initiative"):
                included = [x["object"] for x in self.relationships
                            if x["subject"] == i and x["predicate"] == "includes" and self.entities[x["object"]].get("lifecycle")]
                gap = next((g for g in self.gaps["gaps"] if i in g["entities"]), None)
                rows.append({"strategy": i, "target_record": r["evidence_id"], "target": r["claim"], "target_year": r.get("target_year"),
                             "included": [{"project": x, "lifecycle": self.entities[x]["lifecycle"], "stage": self.stage(x)} for x in included],
                             "gap": gap["id"] if gap else None, "gap_state": gap["state"] if gap else None,
                             "progress": (self.gaps["open_wording"] if gap and gap["state"] == "open"
                                          else "See the gap's resolving records." if gap else "Not yet assessed in the gap register."),
                             "progress_basis": ("not assessed" if not gap else
                                                "editorial assessment; the data checks confirm it" if gap.get("checks") else
                                                "editorial assessment only; no data check backs it, and its digest shows only that the data it rests on is unchanged")})
        return {"rows": rows}


# ─── Output ───────────────────────────────────────────────────────────────

def _date(r):
    pub = r.get("publication_date")
    return (f"published {pub}" if pub else "undated (publication_date is null)") + f"; retrieved {r['retrieval_date']}"


def show_relationship(reg, subject, predicate, obj):
    rel = next((r for r in reg.relationships if (r["subject"], r["predicate"], r["object"]) == (subject, predicate, obj)), None)
    if rel is None:
        raise LookupError(f"no relationship {subject}|{predicate}|{obj} in ontology.json")
    s, o = reg.entities[subject], reg.entities[obj]
    row = next((r for r in reg.matrix["rows"] if r["id"] == f"{subject}|{predicate}|{obj}"), None)
    pred = reg.ontology["predicates"][predicate]
    out = [f"Relationship {subject}|{predicate}|{obj}",
           f"  {s['name']} ({s['type']}) {pred['label']} {o['name']} ({o['type']})",
           "", "DOCUMENTED",
           f"  Classification: {rel['classification']}: {reg.evidence['classifications'][rel['classification']]}"]
    if row:
        out.append(f"  Matrix: documented as \"{row['documented_as']}\"; basis {row['documentation_basis']}: "
                   f"{reg.matrix['derivation']['documentation_basis']['values'][row['documentation_basis']]}")
    if o.get("lifecycle"):
        out.append(f"  {o['name']} stage: {reg.stage(obj)}, on {', '.join(o['lifecycle_evidence'])}: {reg.ontology['lifecycle_stages'][o['lifecycle']]}")
    for x in rel["evidence"]:
        r = reg.records[x]
        out += [f"  {x}: {r['title']}",
                f"    Source: {r['source_organization']} ({r['source_type']}, {r['evidence_type']})",
                f"    URL: {r['source_url']}",
                f"    Dates: {_date(r)}",
                f"    Verification: {r['verification_status']}: {reg.evidence['verification_statuses'][r['verification_status']]}",
                f"    Claim (the registry's summary): {r['claim']}"]
        out += [f"    Excerpt ({r['source_language']}, the source's words): “{q}”" for q in r["source_excerpts"]]
    out += ["", "LIMITATIONS"]
    if rel.get("note"):
        out.append(f"  Relationship note: {rel['note']}")
    for q in (row or {}).get("qualifications") or []:
        if q != rel.get("note"):
            out.append(f"  {q}")
    for x in rel["evidence"]:
        r = reg.records[x]
        out.append(f"  {x}: {r['verification_note']}")
        if r.get("superseded_by"):
            out.append(f"  {x} is superseded by {', '.join(r['superseded_by'])}: its claim is no longer current.")
        if r.get("associated_entities"):
            out.append(f"  {x} links {', '.join(r['associated_entities'])} by name only, not as the same legal entity.")
    if o.get("lifecycle") in ("operational", "pilot"):
        out.append(f"  {o['name']}: a stage rests on its latest status record; it is not evidence of use, scale or outcomes, nor of operation after that record.")
    out.append("  The registry records this relationship and its evidence; it is not a complete account of either party.")
    return "\n".join(out)


def show_gap(reg, gid):
    g = next((g for g in reg.gaps["gaps"] if g["id"] == gid), None)
    if g is None:
        raise LookupError(f"no gap {gid} in gaps.json")
    out = [f"{gid} [{g['state']}] {g['question']}", f"  State: {reg.gaps['states'][g['state']]}"]
    if g["entities"]:
        out.append("  Concerns: " + ", ".join(f"{e} ({reg.entities[e]['name']})" for e in g["entities"]))
    out += ["", "ESTABLISHED (each statement with its records)"]
    for item in g["established"]:
        out.append(f"  - {item['text']}")
        for x in item["evidence"]:
            out.append(f"      {x}: {reg.records[x]['classification']}; {reg.records[x]['source_url']}; {_date(reg.records[x])}")
    if not g["established"]:
        out.append("  - (computed list below)")
    out += ["", "NOT ESTABLISHED", f"  {g['unestablished']}"]
    if g["state"] == "open":
        out.append(f"  {reg.gaps['open_wording']}")
    if g.get("entity_assessments"):
        out += ["", "BY ENTITY (records per dimension; none recorded = '-')"]
        for a in g["entity_assessments"]:
            order = reg.gap_register["entity_assessment"]["dimension_order"]
            out.append(f"  {a['entity']} [{a['state']}]: " + "; ".join(f"{k} {', '.join(a['dimensions'][k]) or '-'}" for k in order))
            if a.get("note"):
                out.append(f"      {a['note']}")
    out += ["", "EVIDENCE THAT WOULD RESOLVE IT"] + [f"  - {x}" for x in g["evidence_needed"]]
    out += ["", "WHAT THE DATA CAN CONFIRM"]
    fp = reg.fingerprint(g)
    if fp:
        out.append(f"  Assessed {g['assessed']} against {', '.join(g['assessed_records'])}; digest {g['assessed_fingerprint']}, "
                   f"recomputed {fp}: {'unchanged since assessment' if fp == g['assessed_fingerprint'] else 'CHANGED since assessment'}")
    checks = reg.run_checks(g)
    for desc, hit in checks:
        out.append(f"  Check: {desc}: {'NO LONGER HOLDS' if hit else 'holds'}")
    if not checks:
        out.append("  No data check is defined: the state rests on the editor's assessment alone.")
    if any(c["type"] == "computed_relationships" for c in g.get("checks") or []):
        rows = reg.announcement_only()
        formal = reg._formal_act_rows()
        out.append(f"  Recomputed: {len(rows)} of {len(formal)} formal-act relationships rest only on announcements, news reports or descriptions:")
        out += [f"    {r['id']} ({', '.join(r['evidence'])})" for r in rows]
    out.append("  The established and not-established statements are the editor's assessment; the lines above are what the data confirms.")
    return "\n".join(out)


def show_q8(a):
    out = [f"Q8: {a['organisations']} organisations are documented as connected to {a['projects']} projects through {a['relationships']} relationships: "
           + ", ".join(f"{k.lower()} {v}" for k, v in a["documented_as"].items())
           + f". {a['announcement_only']} rest only on announcements or news reports in this registry.", ""]
    for o in a["rows"]:
        out.append(f"{o['organisation']} ({o['name']})")
        out += [f"  {p['relationship']} {p['project']}: {p['documented_as']}; project {p['stage']}" for p in o["projects"]]
        out.append(f"  evidence: {' '.join(o['evidence'])}")
    out += ["", "Recorded, not derivable from the data:"] + [f"  - {x}" for x in a["not_derivable"]]
    return "\n".join(out)


def show_q9(a):
    out = []
    for r in a["rows"]:
        out += [f"{r['strategy']}: {r['target']} [{r['target_record']}, target year {r['target_year']}]",
                "  Included: " + ("; ".join(f"{p['project']} ({p['stage']})" for p in r["included"]) or "none recorded"),
                f"  Measured progress: {r['progress']}" + (f" ({r['gap']}, {r['gap_state']})" if r["gap"] else ""),
                f"  Basis: {r['progress_basis']}", ""]
    out.append("A target is never an outcome, and a project's stage is not progress towards a target.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="site address or local directory (default %(default)s)")
    ap.add_argument("--json", action="store_true", help="print q8 or q9 as JSON")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    rp = sub.add_parser("relationship")
    rp.add_argument("subject")
    rp.add_argument("predicate")
    rp.add_argument("object")
    gp = sub.add_parser("gap")
    gp.add_argument("gap_id")
    sub.add_parser("q8")
    sub.add_parser("q9")
    args = ap.parse_args(argv)
    try:
        reg = Registry(args.source)
    except (FetchError, ValueError, KeyError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    try:
        problems = reg.verify()
    except (KeyError, TypeError, AttributeError) as exc:
        problems = [f"unexpected structure: {type(exc).__name__} {exc} (a field this consumer relies on is missing or of the wrong type)"]
    if problems:
        print(f"INCONSISTENT DATA ({len(problems)} problem{'s' if len(problems) != 1 else ''})", file=sys.stderr)
        for x in problems:
            print(f"  {x}", file=sys.stderr)
        return 1
    try:
        if args.command == "verify":
            print(f"OK: registry {reg.manifest['registry_version']} as of {reg.manifest['as_of']}: {len(reg.records)} records, "
                  f"{len(reg.entities)} entities, {len(reg.relationships)} relationships, {len(reg.matrix['rows'])} matrix rows and "
                  f"{len(reg.gaps['gaps'])} gaps checked against the manifest, their references and the published rules.")
            print("This shows the files are consistent with each other and with the manifest. It does not show who published them "
                  "(the hashes are not a signature) or that the records are accurate: the sources were not re-fetched.")
        elif args.command == "relationship":
            print(show_relationship(reg, args.subject, args.predicate, args.object))
        elif args.command == "gap":
            print(show_gap(reg, args.gap_id))
        else:
            answer = reg.q8() if args.command == "q8" else reg.q9()
            print(json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) if args.json
                  else show_q8(answer) if args.command == "q8" else show_q9(answer))
    except LookupError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
