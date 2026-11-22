"""Stable identity of changelog texts and entity attributes (i18n/changelog-identity.json,
i18n/attribute-identity.json; Sprint 19B-4).

Canonical data is never modified: every mutation below is applied to an in-memory or temporary copy, and a
test checks that data/ is byte-identical afterwards.
Run: python3 -m unittest discover -s tests
"""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import i18n  # noqa: E402
import registry  # noqa: E402
from i18n_fixtures import approved_unit, register_reviewers  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TODAY = __import__("datetime").date(2026, 11, 22)


def load(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


class Identity(unittest.TestCase):
    def setUp(self):
        self.changelog = load("data/changelog.json")
        self.identity = load("i18n/changelog-identity.json")

    def bind(self, changelog=None, identity=None):
        return i18n.bind_identity("changelog", i18n.changelog_entries(changelog or self.changelog), identity or self.identity)

    def ids_to_text(self, changelog=None, identity=None):
        bindings, texts, errors = self.bind(changelog, identity)
        self.assertEqual(errors, [])
        return texts

    def item(self, iid, identity=None):
        for e in (identity or self.identity)["entries"]:
            for it in e["items"]:
                if it["id"] == iid:
                    return it
        raise KeyError(iid)

    def assertFails(self, fragment, changelog=None, identity=None):
        errors = self.bind(changelog, identity)[2]
        self.assertTrue(any(fragment in e for e in errors), errors)


class Registration(Identity):
    def test_every_translatable_changelog_text_is_registered_and_bound(self):
        bindings, texts, errors = self.bind()
        self.assertEqual(errors, [])
        expected = 1 + sum(1 + sum(len(e.get(k, [])) for k in ("changes", "corrections", "review_fixes", "breaking_changes"))
                           for e in self.changelog["entries"])
        self.assertEqual(len(bindings), expected)
        self.assertEqual(len(texts), expected)
        self.assertEqual(len(set(bindings.values())), expected)

    def test_every_attribute_text_is_registered_and_bound(self):
        ontology = load("data/ontology.json")
        bindings, texts, errors = i18n.load_identity("attribute")
        self.assertEqual(errors, [])
        self.assertEqual(len(bindings), 2 * sum(len(e.get("attributes") or []) for e in ontology["entities"]))

    def test_identity_is_not_positional(self):
        # The NN suffix is a registration label: binding uses the recorded fingerprint, so the same id keeps
        # its text when the list is reversed.
        texts = self.ids_to_text()
        c = copy.deepcopy(self.changelog)
        for e in c["entries"]:
            for k in ("changes", "corrections", "review_fixes"):
                if k in e:
                    e[k].reverse()
        self.assertEqual(self.ids_to_text(c), texts)


class Mutations(Identity):
    # 7
    def test_reordered_items_and_entries_keep_their_identity(self):
        texts = self.ids_to_text()
        c = copy.deepcopy(self.changelog)
        c["entries"].reverse()
        c["entries"][0]["changes"].insert(0, c["entries"][0]["changes"].pop())
        self.assertEqual(self.ids_to_text(c), texts)

    # 8
    def test_edited_item_keeps_its_id_and_invalidates_its_translation(self):
        c = copy.deepcopy(self.changelog)
        target = "changelog.v0-10-1.changes.01"
        old = self.ids_to_text()[target]
        pos = c["entries"][0]["changes"].index(old)
        c["entries"][0]["changes"][pos] = old + " (corrected wording)"
        self.assertFails("has no active identity", c)
        self.assertFails(f"active identity '{target}' matches no canonical text", c)
        proposals = i18n.identity_proposals("changelog", i18n.changelog_entries(c), self.identity)
        self.assertIn(f"{target}: if the text was edited, set source_sha256 to {i18n.fingerprint(old + ' (corrected wording)')}", proposals)
        ident = copy.deepcopy(self.identity)
        self.item(target, ident)["source_sha256"] = i18n.fingerprint(old + " (corrected wording)")
        self.assertEqual(self.ids_to_text(c, ident)[target], old + " (corrected wording)")

    # 9
    def test_inserted_item_needs_a_new_identity(self):
        c = copy.deepcopy(self.changelog)
        c["entries"][0]["changes"].insert(1, "A newly recorded change.")
        self.assertFails("has no active identity", c)
        proposals = i18n.identity_proposals("changelog", i18n.changelog_entries(c), self.identity)
        new_id = next(__import__("re").search(r"register (\S+) with", p).group(1) for p in proposals if p.startswith("new text"))
        self.assertNotIn(new_id, {it["id"] for e in self.identity["entries"] for it in e["items"]})
        ident = copy.deepcopy(self.identity)
        ident["entries"][1]["items"].append({"id": new_id, "field": "changes", "status": "active",
                                              "source_sha256": i18n.fingerprint("A newly recorded change.")})
        self.assertEqual(self.ids_to_text(c, ident)[new_id], "A newly recorded change.")

    # 10
    def test_deleted_item_must_be_retired(self):
        c = copy.deepcopy(self.changelog)
        target = "changelog.v0-10-1.changes.02"
        c["entries"][0]["changes"].remove(self.ids_to_text()[target])
        self.assertFails(f"active identity '{target}' matches no canonical text", c)
        ident = copy.deepcopy(self.identity)
        self.item(target, ident)["status"] = "retired"
        self.assertNotIn(target, self.ids_to_text(c, ident))

    # 11
    def test_retired_identity_is_never_reused(self):
        ident = copy.deepcopy(self.identity)
        target = "changelog.v0-10-1.changes.02"
        self.item(target, ident)["status"] = "retired"
        ident["entries"][1]["items"].append({"id": target, "field": "changes", "status": "active",
                                              "source_sha256": i18n.fingerprint("Some other text.")})
        self.assertFails(f"duplicate identity '{target}' (ids are never reused, retired ones included)", identity=ident)
        # A retired id does not silently take over a matching text either.
        c = copy.deepcopy(self.changelog)
        ident2 = copy.deepcopy(self.identity)
        self.item(target, ident2)["status"] = "retired"
        self.assertFails("has no active identity", c, ident2)

    # 6
    def test_duplicate_identity(self):
        ident = copy.deepcopy(self.identity)
        ident["entries"][1]["items"][1]["id"] = ident["entries"][1]["items"][0]["id"]
        self.assertFails("duplicate identity", identity=ident)

    # 12
    def test_ambiguous_duplicate_text_fails_closed_until_occurrences_are_explicit(self):
        c = copy.deepcopy(self.changelog)
        text = c["entries"][0]["changes"][0]
        c["entries"][0]["changes"].append(text)
        ident = copy.deepcopy(self.identity)
        first = self.item("changelog.v0-10-1.changes.01", ident)
        ident["entries"][1]["items"].append({"id": "changelog.v0-10-1.changes.99", "field": "changes", "status": "active",
                                              "source_sha256": first["source_sha256"]})
        self.assertFails("identical texts need occurrence numbers", c, ident)
        first["occurrence"] = 1
        ident["entries"][1]["items"][-1]["occurrence"] = 2
        texts = self.ids_to_text(c, ident)
        self.assertEqual(texts["changelog.v0-10-1.changes.01"], text)
        self.assertEqual(texts["changelog.v0-10-1.changes.99"], text)

    def test_two_identities_claiming_one_text_fail_closed(self):
        # Even with explicit occurrence numbers, two active ids for a single text are ambiguous.
        ident = copy.deepcopy(self.identity)
        first = self.item("changelog.v0-10-1.changes.01", ident)
        first["occurrence"] = 1
        ident["entries"][1]["items"].append({"id": "changelog.v0-10-1.changes.99", "field": "changes", "status": "active",
                                              "source_sha256": first["source_sha256"], "occurrence": 2})
        self.assertFails("1 identical text(s) but 2 active id(s); ambiguous", identity=ident)

    def test_the_build_stops_on_an_identity_error(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        shutil.copytree(REPO / "i18n", root / "i18n")
        ident = copy.deepcopy(self.identity)
        ident["entries"][1]["items"] = [it for it in ident["entries"][1]["items"] if it["id"] != "changelog.v0-10-1.title"]
        (root / "i18n" / "changelog-identity.json").write_text(json.dumps(ident), encoding="utf-8")
        evidence, ontology = registry.load_all()
        with build.rendering(build.RenderContext("en", root, today=TODAY)):
            with self.assertRaises(SystemExit) as cm:
                build.render_methodology(build.Model(evidence, ontology), self.changelog)
        self.assertIn("identity map is out of date", str(cm.exception))

    def test_ambiguous_entry_key_fails_closed(self):
        c = copy.deepcopy(self.changelog)
        c["entries"][1]["version"] = c["entries"][0]["version"]
        self.assertFails("canonical entries share the key", c)

    # 13
    def test_invalid_source_fingerprint(self):
        ident = copy.deepcopy(self.identity)
        self.item("changelog.v0-10-1.title", ident)["source_sha256"] = "not-a-fingerprint"
        self.assertFails("needs the source_sha256", identity=ident)
        ident = copy.deepcopy(self.identity)
        self.item("changelog.v0-10-1.title", ident)["source_sha256"] = i18n.fingerprint("a different title")
        self.assertFails("matches no canonical text", identity=ident)

    def test_unregistered_entry(self):
        c = copy.deepcopy(self.changelog)
        c["entries"].insert(0, dict(c["entries"][0], version="9.9.9"))
        self.assertFails("canonical entry {'version': '9.9.9'} has no registered identity", c)

    def test_attribute_identity_uses_the_same_rules(self):
        ontology = load("data/ontology.json")
        ident = load("i18n/attribute-identity.json")
        o = copy.deepcopy(ontology)
        toubkal = next(e for e in o["entities"] if e["id"] == "toubkal-supercomputer")
        toubkal["attributes"].reverse()
        before = i18n.bind_identity("attribute", i18n.attribute_entries(ontology), ident)[1]
        self.assertEqual(i18n.bind_identity("attribute", i18n.attribute_entries(o), ident)[1], before)
        toubkal["attributes"][0]["value"] += " (revised)"
        self.assertTrue(i18n.bind_identity("attribute", i18n.attribute_entries(o), ident)[2])


class TranslationsFollowIdentity(unittest.TestCase):
    """A translation is keyed by the stable id: a reorder keeps it valid; an edit makes it stale."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(REPO / "i18n", self.root / "i18n")
        shutil.copytree(REPO / "data", self.root / "data")
        register_reviewers(self.root)
        self.uid = "changelog:changelog.v0-10-1.changes.01:text"
        self.source = i18n.Sources(self.root).content(self.uid)[0]
        cat = {"language": "fr", "units": [approved_unit(self.uid, "prose", "texte (fr)", self.source, lang="fr")]}
        (self.root / "i18n" / "fr" / "content.json").write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")

    def rewrite_changelog(self, change):
        path = self.root / "data" / "changelog.json"
        c = json.loads(path.read_text(encoding="utf-8"))
        change(c)
        path.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")

    def test_reorder_keeps_the_translation_valid(self):
        self.rewrite_changelog(lambda c: c["entries"][0]["changes"].reverse())
        self.assertEqual(i18n.validate(self.root, today=TODAY), ([], {"stale": [], "orphaned": []}))
        self.assertIn(self.uid, i18n.renderable_units("fr", self.root, today=TODAY))

    def test_edit_with_rebinding_makes_the_translation_stale(self):
        def edit(c):
            i = c["entries"][0]["changes"].index(self.source)
            c["entries"][0]["changes"][i] = self.source + " (edited)"
        self.rewrite_changelog(edit)
        ident_path = self.root / "i18n" / "changelog-identity.json"
        ident = json.loads(ident_path.read_text(encoding="utf-8"))
        for e in ident["entries"]:
            for it in e["items"]:
                if it["id"] == "changelog.v0-10-1.changes.01":
                    it["source_sha256"] = i18n.fingerprint(self.source + " (edited)")
        ident_path.write_text(json.dumps(ident), encoding="utf-8")
        errors, report = i18n.validate(self.root, today=TODAY)
        self.assertEqual(errors, [])
        self.assertEqual(report["stale"], [f"fr:{self.uid}"])
        self.assertNotIn(self.uid, i18n.renderable_units("fr", self.root, today=TODAY))

    def test_unrebound_edit_fails_validation(self):
        self.rewrite_changelog(lambda c: c["entries"][0]["changes"].__setitem__(0, c["entries"][0]["changes"][0] + " x"))
        errors, _ = i18n.validate(self.root, today=TODAY)
        self.assertTrue(any("changelog-identity.json" in e for e in errors), errors)


class CanonicalDataUntouched(unittest.TestCase):
    def test_identity_work_never_modifies_canonical_data(self):
        files = ("data/changelog.json", "data/ontology.json", "data/evidence.json", "data/gaps.json")
        before = {f: hashlib.sha256((REPO / f).read_bytes()).hexdigest() for f in files}
        i18n.load_identity("changelog")
        i18n.load_identity("attribute")
        i18n.validate(today=TODAY)
        evidence, ontology = registry.load_all()
        build.render_methodology(build.Model(evidence, ontology), registry.load(REPO / "data" / "changelog.json"))
        self.assertEqual({f: hashlib.sha256((REPO / f).read_bytes()).hexdigest() for f in files}, before)


if __name__ == "__main__":
    unittest.main()
