"""Social-sharing image and Open Graph / X metadata.

The image is a committed PNG (assets/social/themoroccoai-og.png) rendered from tools/social/og_image.py. These
tests use the standard library only: the PNG is parsed and its chunk checksums verified without an image library.
Run: python3 -m unittest discover -s tests
"""
import html
import re
import subprocess
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402
import check_site  # noqa: E402
import registry  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "assets" / "social" / "themoroccoai-og.png"
URL = "https://themoroccoai.com/assets/social/themoroccoai-og.png"
HOMEPAGE_TARGET = {
    ("property", "og:type"): "website",
    ("property", "og:site_name"): "TheMoroccoAI",
    ("property", "og:title"): "TheMoroccoAI — Mapping Morocco's AI Landscape",
    ("property", "og:description"): "Independent research infrastructure documenting Morocco's evolving AI ecosystem through "
                                     "structured evidence and transparent methodology.",
    ("property", "og:url"): "https://themoroccoai.com/",
    ("property", "og:image"): URL,
    ("property", "og:image:secure_url"): URL,
    ("property", "og:image:type"): "image/png",
    ("property", "og:image:width"): "1200",
    ("property", "og:image:height"): "630",
    ("property", "og:image:alt"): "TheMoroccoAI — independent research infrastructure mapping Morocco's AI landscape.",
    ("name", "twitter:card"): "summary_large_image",
    ("name", "twitter:title"): "TheMoroccoAI — Mapping Morocco's AI Landscape",
    ("name", "twitter:description"): "Structured evidence and independent research on Morocco's evolving AI ecosystem.",
    ("name", "twitter:image"): URL,
    ("name", "twitter:image:alt"): "TheMoroccoAI — mapping Morocco's AI landscape.",
}


def png_chunks(data):
    """[(type, payload)] after verifying the signature and every chunk's CRC."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG signature"
    pos, chunks = 8, []
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind, payload = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        crc = int.from_bytes(data[pos + 8 + length:pos + 12 + length], "big")
        assert zlib.crc32(kind + payload) == crc, f"bad CRC in {kind!r}"
        chunks.append((kind, payload))
        pos += 12 + length
    return chunks


def metas(page_html):
    """[(attribute, key, content)] for every <meta name|property>, duplicates kept."""
    return [(m.group(1), m.group(2), html.unescape(m.group(3)))
            for m in re.finditer(r'<meta (name|property)="([^"]+)" content="([^"]*)">', page_html)]


def public_pages():
    return [p for p in check_site.site_pages()]


class TheImage(unittest.TestCase):
    def test_is_a_valid_1200_by_630_png_of_reasonable_size(self):
        data = IMAGE.read_bytes()
        chunks = png_chunks(data)
        kinds = [k for k, _ in chunks]
        self.assertEqual(kinds[0], b"IHDR")
        self.assertEqual(kinds[-1], b"IEND")
        self.assertIn(b"IDAT", kinds)
        ihdr = chunks[0][1]
        width, height = int.from_bytes(ihdr[0:4], "big"), int.from_bytes(ihdr[4:8], "big")
        self.assertEqual((width, height), (1200, 630))
        self.assertEqual(ihdr[8], 8)          # 8 bits per channel
        self.assertIn(ihdr[9], (2, 6))        # truecolour, with or without alpha
        raw = zlib.decompress(b"".join(p for k, p in chunks if k == b"IDAT"))
        self.assertEqual(len(raw), height * (1 + width * (3 if ihdr[9] == 2 else 4)))  # complete image data
        self.assertLess(len(data), 1_000_000)
        self.assertEqual(check_site.png_size(IMAGE), (1200, 630))
        self.assertEqual(build.SOCIAL_IMAGE_SIZE, (1200, 630))

    def test_is_committed_and_published_with_the_site(self):
        # GitHub Pages serves the repository as committed: a tracked, non-ignored file is published at its path.
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(IMAGE.relative_to(REPO))], cwd=REPO,
                                 capture_output=True)
        self.assertEqual(tracked.returncode, 0, "the social image must be committed")
        ignored = subprocess.run(["git", "check-ignore", "-q", str(IMAGE.relative_to(REPO))], cwd=REPO)
        self.assertNotEqual(ignored.returncode, 0, "the social image must not be git-ignored")
        self.assertEqual(build.SOCIAL_IMAGE, "https://themoroccoai.com/" + IMAGE.relative_to(REPO).as_posix())
        robots = (REPO / "robots.txt").read_text(encoding="utf-8")
        self.assertNotRegex(robots, r"(?mi)^Disallow:\s*/(?:assets)?/?\s*$")

    def test_the_build_never_writes_or_removes_the_image(self):
        evidence, ontology = registry.load_all()
        files, _ = build.build_outputs(build.Model(evidence, ontology))
        self.assertFalse([p for p in files if p.startswith("assets/")])
        self.assertTrue(IMAGE.exists())
        self.assertFalse([p for p in build.withdrawn_files(REPO, files) if str(p).startswith("assets")])


class HomepageMetadata(unittest.TestCase):
    def setUp(self):
        self.html = (REPO / "index.html").read_text(encoding="utf-8")

    def test_homepage_carries_exactly_the_target_social_metadata(self):
        found = metas(self.html)
        for (attr, key), value in HOMEPAGE_TARGET.items():
            matches = [c for a, k, c in found if k == key]
            self.assertEqual(matches, [value], key)
            self.assertTrue(any(a == attr for a, k, _ in found if k == key), f"{key} should use {attr}=")

    def test_canonical_title_and_description_are_preserved(self):
        self.assertIn('<link rel="canonical" href="https://themoroccoai.com/">', self.html)
        self.assertIn("<title>TheMoroccoAI — Independent Evidence Registry for Morocco’s AI Ecosystem</title>", self.html)
        self.assertEqual([c for a, k, c in metas(self.html) if k == "description"],
                         ["An independent, evidence-backed registry of institutions, initiatives, projects, models and datasets "
                          "in Morocco's AI ecosystem, with sources, classifications and open JSON data. Not a government platform."])

    def test_social_text_comes_from_the_catalog(self):
        tmpl = build.HOMEPAGE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('content="{{a:page.home.og_title}}"', tmpl)
        self.assertIn("{{og_image}}{{twitter}}", tmpl)
        self.assertNotIn("twitter:card", tmpl)  # rendered by build.social_image_meta, not hard-coded


class SiteWide(unittest.TestCase):
    def test_every_public_page_has_one_coherent_social_set(self):
        pages = public_pages()
        self.assertGreaterEqual(len(pages), 70)
        for path in pages:
            page_html = path.read_text(encoding="utf-8")
            p = check_site.Page()
            p.feed(page_html)
            where = path.relative_to(REPO).as_posix()
            self.assertEqual(check_site.social_meta_errors(where, p), [], where)
            keys = [k for _, k, _ in metas(page_html)]
            dups = {k for k in keys if keys.count(k) > 1} - check_site.REPEATABLE_META
            self.assertEqual(dups, set(), where)
            self.assertEqual(p.meta["og:url"], p.canonical, where)

    def test_key_pages_are_covered(self):
        for rel in ("index.html", "methodology/index.html", "registry/index.html", "registry/evidence/index.html",
                    "evaluation/index.html", "acquisition/index.html", "registry/um6p/index.html", "data/index.html"):
            page_html = (REPO / rel).read_text(encoding="utf-8")
            self.assertIn(f'<meta property="og:image" content="{URL}">', page_html, rel)
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', page_html, rel)

    def test_evaluation_page_matches_the_generated_social_set(self):
        evaluation = (REPO / "evaluation" / "index.html").read_text(encoding="utf-8")
        og, tw = build.social_image_meta(build.escape(build.i18n.t("shell.og_image_alt"), quote=False).replace('"', "&quot;"))
        self.assertIn(og + tw, evaluation)


class GateNegatives(unittest.TestCase):
    def check(self, page_html):
        p = check_site.Page()
        p.feed(page_html)
        return check_site.social_meta_errors("page.html", p)

    def setUp(self):
        self.good = (REPO / "registry" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(self.check(self.good), [])

    def assertFlags(self, page_html, fragment):
        errors = self.check(page_html)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_duplicate_or_conflicting_tags(self):
        line = f'<meta property="og:image" content="{URL}">'
        self.assertFlags(self.good.replace(line, line + "\n" + line), "duplicate <meta> 'og:image'")
        self.assertFlags(self.good.replace('<meta name="twitter:card" content="summary_large_image">',
                                           '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:card" content="summary">'),
                         "duplicate <meta> 'twitter:card'")

    def test_missing_wrong_or_relative_image(self):
        self.assertFlags(self.good.replace(f'<meta name="twitter:image" content="{URL}">\n', ""), "missing social metadata")
        self.assertFlags(self.good.replace(f'<meta property="og:image" content="{URL}">', '<meta property="og:image" content="/assets/social/themoroccoai-og.png">'),
                         "must all be")
        self.assertFlags(self.good.replace('content="summary_large_image"', 'content="summary"'), "summary_large_image")

    def test_declared_type_or_size_differing_from_the_file(self):
        self.assertFlags(self.good.replace('content="image/png"', 'content="image/jpeg"'), "does not match the PNG file")
        self.assertFlags(self.good.replace('<meta property="og:image:height" content="630">', '<meta property="og:image:height" content="600">'),
                         "differ from the file's 1200x630")

    def test_png_size_rejects_a_non_png(self):
        self.assertIsNone(check_site.png_size(REPO / "favicon.svg"))


if __name__ == "__main__":
    unittest.main()
