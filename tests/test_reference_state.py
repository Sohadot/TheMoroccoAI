"""Sprint 10 Tier 1: /registry/reference-state.json. Projections of the canonical data by published rules, recomputed by
the example consumer; no score, aggregate state, conflict, progress, sum, computed rank, first-party class or domain role."""
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "examples"))
import build  # noqa: E402
import registry  # noqa: E402
import registry_consumer as consumer  # noqa: E402

SNAPSHOT = REPO / "registry" / "reference-state.json"
# Consumers published with earlier versions: v0.6.0 (unchanged since 2803167), v0.7.0, v0.8.0 and v0.9.0.
OLD_CONSUMERS = {"v0.6.0": "2803167", "v0.7.0": "0d0fa8f", "v0.8.0": "59c4221", "v0.9.0": "8ffc6d0"}
FORBIDDEN_TEXT = re.compile(r"(?i)\b(score|confidence|completeness|conflicts?|progress|achieved|evidence[_ ]state|documented|"
                            r"partially|rank|ranking|total|cumulative|first[_ -]party|indicators?|role|funder|regulator)\b")


def snapshot_text():
    evidence, ontology = registry.load_all()
    gaps = registry.load(registry.ROOT / "data" / "gaps.json")
    canonical = {p: (REPO / p).read_bytes() for p in build.REFERENCE_INPUTS}
    return build._json(build.reference_state(build.Model(evidence, ontology), gaps, canonical))


def values(node):
    """Every string value outside the derivation block (which explains, in words, what the file does not hold)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k != "derivation":
                yield from values(v)
    elif isinstance(node, list):
        for v in node:
            yield from values(v)
    elif isinstance(node, str):
        yield node


def keys(node, skip=("derivation",)):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in skip:
                continue
            yield k
            yield from keys(v, skip)
    elif isinstance(node, list):
        for v in node:
            yield from keys(v, skip)


class ReferenceState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SNAPSHOT.read_text(encoding="utf-8")
        cls.s = json.loads(cls.raw)
        cls.evidence, cls.ontology = registry.load_all()
        cls.gaps = registry.load(registry.ROOT / "data" / "gaps.json")
        cls.records = {r["evidence_id"]: r for r in cls.evidence["records"]}
        cls.entities = {e["id"]: e for e in cls.ontology["entities"]}
        cls.manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))

    # ─── Generation and provenance ─────────────────────────────────────────

    def test_generation_is_deterministic_and_byte_identical(self):
        first, second = snapshot_text(), snapshot_text()
        self.assertEqual(first, second)
        self.assertEqual(first, self.raw)

    def test_derived_from_hashes_the_canonical_inputs_directly(self):
        self.assertEqual([x["path"] for x in self.s["derived_from"]], ["/data/evidence.json", "/data/ontology.json", "/data/gaps.json"])
        for x in self.s["derived_from"]:
            self.assertEqual(x["sha256"], hashlib.sha256((REPO / x["path"].lstrip("/")).read_bytes()).hexdigest(), x["path"])

    def test_no_manifest_snapshot_cycle(self):
        paths = [x["path"] for x in self.s["derived_from"]]
        self.assertNotIn("/data/manifest.json", paths)
        self.assertNotIn("/registry/reference-state.json", paths)
        self.assertNotIn("manifest", " ".join(p for p in build.REFERENCE_INPUTS))
        listed = {r["path"]: r for r in self.manifest["resources"]}
        self.assertEqual(listed["/registry/reference-state.json"]["role"], "derived")
        self.assertEqual(listed["/registry/reference-state.json"]["sha256"], hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest())
        # The snapshot does not change when the manifest does: it never reads it.
        evidence, ontology = registry.load_all()
        canonical = {p: (REPO / p).read_bytes() for p in build.REFERENCE_INPUTS}
        model = build.Model(evidence, ontology)
        a = build.reference_state(model, self.gaps, canonical)
        self.assertNotIn("manifest", json.dumps(a["derived_from"]))

    def test_every_field_has_a_reproducible_rule(self):
        d = self.s["derivation"]
        self.assertEqual(set(self.s), set(registry.REFERENCE_FIELDS))
        for k in registry.REFERENCE_FIELDS:
            if k in registry.REFERENCE_UNDERIVED:
                continue
            for path in ([f"{k}.{x}" for x in registry.REFERENCE_SUBFIELDS[k]] if k in registry.REFERENCE_SUBFIELDS else [k]):
                self.assertEqual(d[path]["provenance"], "reproducible", path)
                self.assertTrue(d[path]["rule"].strip(), path)
        self.assertEqual(registry.validate_reference_state(self.s, self.evidence, self.ontology), [])

    def test_version_and_counts(self):
        c = self.s["counts"]
        self.assertEqual((self.s["registry_version"], self.s["as_of"]), (self.evidence["version"], self.evidence["as_of"]))
        self.assertEqual((c["records"], c["entities"], c["relationships"]), (63, 65, 78))
        self.assertEqual(c["records_by_classification"], {"VERIFIED FACT": 46, "OFFICIAL TARGET": 10, "ANNOUNCED PLAN": 4,
                                                          "INDEPENDENT ANALYSIS": 0, "UNVERIFIED CLAIM": 3})
        self.assertEqual(c["relationships_by_classification"]["INDEPENDENT ANALYSIS"], 4)
        self.assertEqual(c["records_by_verification_status"], {"verified": 62, "partial": 1})
        self.assertEqual(sum(c["entities_by_type"].values()), 65)

    # ─── Consumer parity and compatibility ─────────────────────────────────

    def test_consumer_recomputes_every_field(self):
        reg = consumer.Registry(str(REPO))
        mine = reg.reference_state()
        self.assertEqual(set(mine) | set(registry.REFERENCE_UNDERIVED), set(self.s))
        for k, v in mine.items():
            self.assertEqual(self.s[k], v, k)
        self.assertEqual(reg.verify(), [])

    def test_consumer_rejects_a_snapshot_that_does_not_follow(self):
        reg = consumer.Registry(str(REPO))
        for mutate, expected in (
                (lambda s: s["operational_or_pilot"][0].update(counts_as_ai_deployment=False), "operational_or_pilot does not follow"),
                (lambda s: s.update(confidence=0.9), "field 'confidence' is not one this consumer can recompute"),
                (lambda s: s["derived_from"][0].update(sha256="0" * 64), "derived_from does not follow"),
                (lambda s: s["derivation"]["open_gaps"].update(provenance="recorded-not-derivable"), "open_gaps is not marked reproducible")):
            reg.reference = copy.deepcopy(self.s)
            mutate(reg.reference)
            self.assertTrue(any(expected in p for p in reg._check_reference()), expected)

    def test_consumers_of_earlier_versions_still_verify(self):
        for name, ref in OLD_CONSUMERS.items():
            old = subprocess.run(["git", "show", f"{ref}:examples/registry_consumer.py"], cwd=REPO, capture_output=True, text=True)
            if old.returncode:
                self.skipTest("repository history not available")
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "consumer_old.py"
                path.write_text(old.stdout, encoding="utf-8")
                p = subprocess.run([sys.executable, "-I", str(path), "--source", str(REPO), "verify"], capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 0, f"{name}: {p.stderr}")
            self.assertIn(f"registry {self.evidence['version']}", p.stdout, name)

    # ─── Semantic boundaries ───────────────────────────────────────────────

    def test_lifecycle_and_status_basis_integrity(self):
        for x in self.s["lifecycle"]["entities"]:
            e = self.entities[x["id"]]
            self.assertIn(e["type"], registry.LIFECYCLE_TYPES)
            self.assertEqual((x["lifecycle"], x["lifecycle_evidence"], x["project_kind"]), (e["lifecycle"], e["lifecycle_evidence"], e.get("project_kind")))
        for x in self.s["operational_or_pilot"]:
            for r in x["status_evidence_records"]:
                rec = self.records[r]
                self.assertEqual((rec["classification"], rec["status_evidence"]), ("VERIFIED FACT", x["lifecycle"]), r)
                self.assertIn(rec["status_basis"], x["status_bases"])
        self.assertEqual(self.s["operational_or_pilot_by_status_basis"],
                         {"public-availability-observed": ["idarati-ai", "sovereign-ai-marketplace"], "independent-listing": ["toubkal-supercomputer"]})

    def test_status_bases_come_only_from_records_declaring_the_stage(self):
        # A lifecycle_evidence record that declares another stage (here a pilot report) must not lend its basis to the
        # current stage. In the current data every status record declares the entity's stage, so this uses a variant.
        evidence, ontology = copy.deepcopy(self.evidence), copy.deepcopy(self.ontology)
        extra = {**copy.deepcopy(self.records["MAI-EV-0035"]), "evidence_id": "MAI-EV-9999", "status_evidence": "pilot",
                 "status_basis": "operator-report-of-use"}
        evidence["records"].append(extra)
        idarati = next(e for e in ontology["entities"] if e["id"] == "idarati-ai")
        idarati["evidence"].append("MAI-EV-9999")
        idarati["lifecycle_evidence"].append("MAI-EV-9999")
        canonical = {p: (REPO / p).read_bytes() for p in build.REFERENCE_INPUTS}
        s = build.reference_state(build.Model(evidence, ontology), self.gaps, canonical)
        entry = next(x for x in s["operational_or_pilot"] if x["id"] == "idarati-ai")
        self.assertEqual(entry["status_bases"], ["public-availability-observed"])
        self.assertNotIn("MAI-EV-9999", entry["status_evidence_records"])
        self.assertNotIn("operator-report-of-use", s["operational_or_pilot_by_status_basis"])

    def test_no_initiative_has_a_lifecycle_projection(self):
        listed = {x["id"] for k in ("operational_or_pilot", "unresolved_lifecycle") for x in self.s[k]}
        listed |= {x["id"] for x in self.s["lifecycle"]["entities"]}
        listed |= {i for ids in self.s["announced_projects_by_kind"].values() for i in ids}
        self.assertFalse({i for i in listed if self.entities[i]["type"] == "initiative"})

    def test_platforms_and_compute_are_not_ai_deployments(self):
        flags = {x["id"]: x["counts_as_ai_deployment"] for x in self.s["operational_or_pilot"]}
        self.assertEqual(flags, {"idarati-ai": True, "sovereign-ai-marketplace": False, "toubkal-supercomputer": False})
        for x in self.s["operational_or_pilot"]:
            self.assertEqual(x["counts_as_ai_deployment"], x["project_kind"] == "ai-application")

    def test_targets_map_to_their_covering_gap_exactly(self):
        targets = {r["evidence_id"]: r for r in self.evidence["records"] if r["classification"] == "OFFICIAL TARGET"}
        self.assertEqual([t["evidence_id"] for t in self.s["official_targets"]], sorted(targets))
        for t in self.s["official_targets"]:
            r = targets[t["evidence_id"]]
            self.assertEqual(t["target_year"], r["target_year"])
            self.assertEqual([i["id"] for i in t["initiatives"]], [e for e in r["related_entities"] if self.entities[e]["type"] == "initiative"])
            for i in t["initiatives"]:
                gap = next(g for g in self.gaps["gaps"] if i["id"] in g["entities"])
                self.assertEqual((i["covering_gap"], i["gap_state"]), (gap["id"], gap["state"]))
            self.assertEqual(set(t), {"evidence_id", "target_year", "initiatives"})
        self.assertEqual(len(self.s["official_targets"]), 10)

    def test_gap07_assessments_are_verbatim(self):
        g7 = next(g for g in self.gaps["gaps"] if g["id"] == "GAP-07")
        self.assertEqual(self.s["entity_assessments"], [{"gap": "GAP-07", "assessments": g7["entity_assessments"]}])
        published = next(g for g in json.loads((REPO / "registry" / "gaps" / "gaps.json").read_text(encoding="utf-8"))["gaps"] if g["id"] == "GAP-07")
        self.assertEqual(self.s["entity_assessments"][0]["assessments"], published["entity_assessments"])

    def test_gap05_list_parity(self):
        published = next(g for g in json.loads((REPO / "registry" / "gaps" / "gaps.json").read_text(encoding="utf-8"))["gaps"] if g["id"] == "GAP-05")
        expected = [{k: r[k] for k in ("id", "subject", "relationship", "object", "classification", "evidence")} for r in published["relationships"]]
        self.assertEqual(self.s["announcement_only_relationships"], expected)
        self.assertEqual(len(expected), 11)

    def test_open_gap_coverage_and_separate_unresolved_concepts(self):
        self.assertEqual([g["id"] for g in self.s["open_gaps"]], [g["id"] for g in self.gaps["gaps"] if g["state"] == "open"])
        self.assertEqual(len(self.s["entities_in_open_gaps"]), 12)
        self.assertEqual([x["id"] for x in self.s["unresolved_lifecycle"]], ["deepecho-ultrasound-software"])
        self.assertEqual([x["id"] for x in self.s["unresolved_origin"]], ["um6p-ventures"])
        self.assertEqual(self.s["superseded_records"], [{"evidence_id": "MAI-EV-0029", "superseded_by": ["MAI-EV-0032", "MAI-EV-0039"]}])
        self.assertEqual(self.s["records_unverified_claim"], ["MAI-EV-0003", "MAI-EV-0055", "MAI-EV-0056"])
        self.assertEqual(len(self.s["independent_analysis_relationships"]), 4)

    # ─── Forbidden content ─────────────────────────────────────────────────

    def test_no_forbidden_field_names(self):
        for k in keys(self.s):
            self.assertNotRegex(k, r"(?i)conflict|progress|score|confiden|complete|evidence_state|state_label|rank|sum\b|total|cumulative|"
                                   r"domain|role|first_party|indicator|achiev", k)

    def test_no_judgment_words_in_values(self):
        # Outside derivation, the file holds identifiers, vocabulary keys, dates, digests and its scope sentence only.
        scope = self.s["scope"]
        for v in values(self.s):
            if v == scope:
                continue
            self.assertNotRegex(v, FORBIDDEN_TEXT, v)
        for x in self.s["entity_assessments"]:
            for a in x["assessments"]:
                self.assertEqual(set(a) - {"entity", "state", "dimensions", "note"}, set())

    def test_no_aggregate_evidence_state_per_entity(self):
        for k in ("operational_or_pilot", "unresolved_lifecycle", "unresolved_origin"):
            for x in self.s[k]:
                self.assertFalse({"state", "evidence_state", "status", "label"} & set(x), (k, x))
        for x in self.s["lifecycle"]["entities"]:
            self.assertEqual(set(x), {"id", "type", "project_kind", "lifecycle", "lifecycle_evidence", "status_bases"})

    def test_no_domain_or_role_and_no_numbers_beyond_counts(self):
        self.assertNotIn('"domain"', self.raw)
        numbers = []

        def walk(node, path):
            if isinstance(node, bool):
                return
            if isinstance(node, (int, float)):
                numbers.append(path)
            elif isinstance(node, dict):
                for k, v in node.items():
                    if k != "derivation":
                        walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for v in node:
                    walk(v, path)
        walk(self.s, "")
        # Counts, target years and lifecycle tallies only: no amount, no rank, no percentage.
        allowed = re.compile(r"^\.counts\.|^\.official_targets\.target_year$|^\.lifecycle\.by_type_and_kind\.count$")
        self.assertEqual([p for p in numbers if not allowed.search(p)], [])

    def test_no_derived_osi_ordinal_or_summed_appropriation(self):
        self.assertIsNone(re.search(r"\b\d+(?:st|nd|rd|th)\b", self.raw))
        self.assertNotRegex(self.raw, r"3,000,000,000|3000000000|1,500,000,000|1500000000")

    # ─── The validator refuses what the contract excludes ──────────────────

    def test_validator_refuses_out_of_contract_snapshots(self):
        cases = {
            "conflicts": lambda s: s.update(conflicts=[]),
            "progress": lambda s: s["official_targets"][0].update(progress="none"),
            "confidence": lambda s: s["operational_or_pilot"][0].update(confidence_score=1),
            "evidence_state": lambda s: s["unresolved_lifecycle"][0].update(evidence_state="CONFLICTED"),
            "domain role": lambda s: s["lifecycle"]["entities"][0].update(domain_role="funder"),
            "rule removed": lambda s: s["derivation"].pop("official_targets"),
            "initiative operational": lambda s: s["operational_or_pilot"].append(
                {**s["operational_or_pilot"][0], "id": "digital-morocco-2030"}),
            "platform as AI": lambda s: next(x for x in s["operational_or_pilot"] if x["id"] == "sovereign-ai-marketplace").update(counts_as_ai_deployment=True),
            "status record not declaring": lambda s: s["operational_or_pilot"][0]["status_evidence_records"].append("MAI-EV-0013"),
        }
        for name, change in cases.items():
            s = copy.deepcopy(self.s)
            change(s)
            self.assertTrue(registry.validate_reference_state(s, self.evidence, self.ontology), name)


if __name__ == "__main__":
    unittest.main()
