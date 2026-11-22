"""Source artwork of the social-sharing image (Open Graph / X), 1200 x 630.

    python3 tools/social/og_image.py OUT.html                 write the artwork as a page OUTSIDE the repository
    node tools/social/render.js OUT.html [assets/social/themoroccoai-og.png]
                                                              render it with headless Chromium at 1200 x 630

The intermediate page is not committed: every repository file is publicly served, and it is not a site page.

The composition is computed, not drawn by hand: an eight-fold zellige star (khatam) built from two squares rotated
45 degrees, its interlace rings and evidence pathways joining precise nodes, around the site's nested-hexagon mark.
Colours are the site's (navy #1A2E4A, gold #B8892A, ivory #F4F0E8); type is the site's self-hosted Cormorant
Garamond and DM Mono (SIL OFL 1.1, assets/fonts). No photograph, flag, seal or insignia. Standard library only;
the output is deterministic.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
W, H = 1200, 630
NAVY, NAVY_DEEP, GOLD, IVORY, MUTED = "#1A2E4A", "#0F1D31", "#B8892A", "#F4F0E8", "#8FA3BD"
CX, CY = 962, 315  # centre of the knowledge structure
K = 0.84            # scale of the structure (radii below are at K = 1)


def pt(r, a, cx=CX, cy=CY):
    r *= K
    return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))


def poly(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def star(r, rotate=0.0):
    """Eight-pointed khatam: two squares of circumradius r, one rotated 45 degrees."""
    a = [pt(r, rotate + 45 + 90 * i) for i in range(4)]
    b = [pt(r, rotate + 90 * i) for i in range(4)]
    return a, b


def star_outline(r, rotate=0.0):
    """The sixteen-vertex outline of the khatam: points at radius r, inner corners where the squares cross."""
    inner = r * math.cos(math.radians(45)) / math.cos(math.radians(22.5))
    out = []
    for i in range(8):
        out.append(pt(r, rotate + 45 * i))
        out.append(pt(inner, rotate + 45 * i + 22.5))
    return out


def hexagon(r, rotate=-90.0):
    return [pt(r, rotate + 60 * i) for i in range(6)]


def svg():
    parts = []
    add = parts.append
    # Background: deep navy with a quiet light from the structure's side.
    add(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    add(f'<rect width="{W}" height="{H}" fill="url(#light)"/>')
    # Faint zellige lattice across the field (the site's own background grid, at 40 / 56 px).
    add('<g stroke="#F4F0E8" stroke-width="0.6" opacity="0.035">')
    for x in range(0, W + 1, 40):
        add(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
    for y in range(0, H + 1, 40):
        add(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
    add("</g>")
    add('<g stroke="#B8892A" stroke-width="0.6" opacity="0.05">')
    for k in range(-H, W + H, 56):
        add(f'<line x1="{k}" y1="0" x2="{k + H}" y2="{H}"/>')
        add(f'<line x1="{k}" y1="{H}" x2="{k + H}" y2="0"/>')
    add("</g>")

    # ── Knowledge structure ──
    add('<g fill="none" stroke-linejoin="round">')
    # Outer reference circles, as on an atlas.
    for r, op, dash in ((262, 0.16, "2 6"), (236, 0.28, ""), (150, 0.18, "1 5")):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        add(f'<circle cx="{CX}" cy="{CY}" r="{r * K:.2f}" stroke="#F4F0E8" stroke-width="0.8" opacity="{op}"{d}/>')
    # Graduations on the outer ring: 64 ticks, every eighth longer.
    for i in range(64):
        long_ = i % 8 == 0
        x1, y1 = pt(236, i * 5.625)
        x2, y2 = pt(236 + (12 if long_ else 5), i * 5.625)
        add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#B8892A" stroke-width="{1.1 if long_ else 0.7}" opacity="{0.8 if long_ else 0.45}"/>')
    # Large khatam with interlace: two squares, slightly offset parallels for a woven band.
    for r, sw, op, col in ((214, 1.4, 0.95, GOLD), (204, 0.7, 0.45, GOLD)):
        a, b = star(r)
        add(f'<polygon points="{poly(a)}" stroke="{col}" stroke-width="{sw}" opacity="{op}"/>')
        add(f'<polygon points="{poly(b)}" stroke="{col}" stroke-width="{sw}" opacity="{op}"/>')
    # Inner khatam outline, rotated 22.5 degrees, in ivory: the second layer of depth.
    add(f'<polygon points="{poly(star_outline(128, 22.5))}" stroke="#F4F0E8" stroke-width="1.1" opacity="0.55"/>')
    add(f'<polygon points="{poly(star_outline(128, 22.5))}" fill="#F4F0E8" opacity="0.025" stroke="none"/>')
    # Rosette: eight petals between the two stars.
    for i in range(8):
        a = 22.5 + 45 * i
        p1, p2, p3 = pt(84, a - 22.5), pt(128 * 0.924, a), pt(84, a + 22.5)
        add(f'<path d="M{p1[0]:.2f},{p1[1]:.2f} Q{p2[0]:.2f},{p2[1]:.2f} {p3[0]:.2f},{p3[1]:.2f}" stroke="#B8892A" stroke-width="0.8" opacity="0.55"/>')
    add("</g>")

    # Evidence pathways: chords joining the star's outer points to the inner star's points (the registry's
    # sources -> records -> entities), drawn as fine lines with a soft gold gradient.
    outer = [pt(214, 45 * i) for i in range(8)]
    inner = [pt(128, 22.5 + 45 * i) for i in range(8)]
    mid = [pt(84, 45 * i) for i in range(8)]
    add('<g stroke="url(#path)" stroke-width="0.9" fill="none" opacity="0.9">')
    hexpts = hexagon(46)
    for i in range(8):
        # each source feeds the two records beside it; each record links to the two entities beside it
        for j in (i, (i - 1) % 8):
            add(f'<line x1="{outer[i][0]:.2f}" y1="{outer[i][1]:.2f}" x2="{inner[j][0]:.2f}" y2="{inner[j][1]:.2f}"/>')
        for j in (i, (i + 1) % 8):
            add(f'<line x1="{inner[i][0]:.2f}" y1="{inner[i][1]:.2f}" x2="{mid[j][0]:.2f}" y2="{mid[j][1]:.2f}" opacity="0.7"/>')
        # entities converge on the registry at the centre
        hx, hy = min(hexpts, key=lambda q: (q[0] - mid[i][0]) ** 2 + (q[1] - mid[i][1]) ** 2)
        add(f'<line x1="{mid[i][0]:.2f}" y1="{mid[i][1]:.2f}" x2="{hx:.2f}" y2="{hy:.2f}" opacity="0.45" stroke-dasharray="2 3"/>')
    add("</g>")

    # Nodes: sources (outer, gold), records (inner, ivory), entities (middle, small gold).
    add('<g>')
    for x, y in outer:
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="9" fill="#B8892A" opacity="0.12"/>')
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.2" fill="{NAVY_DEEP}" stroke="#B8892A" stroke-width="1.4"/>')
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.6" fill="#B8892A"/>')
    for x, y in inner:
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" fill="#F4F0E8" opacity="0.9"/>')
    for x, y in mid:
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2" fill="#B8892A"/>')
    add("</g>")

    # The site's mark at the centre: nested hexagons and the gold point.
    add(f'<circle cx="{CX}" cy="{CY}" r="{70 * K:.2f}" fill="url(#core)"/>')
    add(f'<polygon points="{poly(hexagon(46))}" fill="{NAVY_DEEP}" stroke="#F4F0E8" stroke-width="1.6"/>')
    add(f'<polygon points="{poly(hexagon(28))}" fill="none" stroke="#B8892A" stroke-width="1.4"/>')
    add(f'<circle cx="{CX}" cy="{CY}" r="{6 * K:.2f}" fill="#B8892A"/>')

    # ── Typography (left column, 88 px safe margin) ──
    x0 = 88
    add(f'<text x="{x0}" y="150" class="mono label">INDEPENDENT EVIDENCE REGISTRY</text>')
    add(f'<line x1="{x0}" y1="172" x2="{x0 + 46}" y2="172" stroke="#B8892A" stroke-width="1.4"/>')
    add(f'<text x="{x0 - 4}" y="270" class="serif title">TheMoroccoAI<tspan class="dotcom">.com</tspan></text>')
    add(f'<text x="{x0}" y="342" class="serif italic sub">Mapping Morocco’s AI Landscape</text>')
    add(f'<line x1="{x0}" y1="410" x2="{x0 + 520}" y2="410" stroke="#F4F0E8" stroke-width="0.8" opacity="0.22"/>')
    add(f'<text x="{x0}" y="452" class="mono small">Independent Research  ·  Traceable Evidence</text>')

    defs = f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{NAVY_DEEP}"/><stop offset="0.55" stop-color="{NAVY}"/><stop offset="1" stop-color="#16294A"/>
  </linearGradient>
  <radialGradient id="light" cx="{CX / W:.3f}" cy="0.5" r="0.55">
    <stop offset="0" stop-color="#2B4A73" stop-opacity="0.55"/><stop offset="1" stop-color="{NAVY}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="core" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="#B8892A" stop-opacity="0.22"/><stop offset="1" stop-color="#B8892A" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="path" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#D9B46A" stop-opacity="0.75"/><stop offset="1" stop-color="#B8892A" stop-opacity="0.35"/>
  </linearGradient>
</defs>"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="TheMoroccoAI.com — Mapping Morocco’s AI Landscape">\n{defs}\n' + "\n".join(parts) + "\n</svg>")


def html():
    fonts = ROOT / "assets" / "fonts"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>TheMoroccoAI social image</title>
<style>
@font-face {{ font-family: 'Cormorant Garamond'; font-weight: 300 600; src: url('{(fonts / "cormorant-garamond-latin.woff2").as_uri()}') format('woff2'); }}
@font-face {{ font-family: 'Cormorant Garamond'; font-style: italic; font-weight: 300 400; src: url('{(fonts / "cormorant-garamond-italic-latin.woff2").as_uri()}') format('woff2'); }}
@font-face {{ font-family: 'DM Mono'; font-weight: 400; src: url('{(fonts / "dm-mono-400-latin.woff2").as_uri()}') format('woff2'); }}
@font-face {{ font-family: 'DM Mono'; font-weight: 500; src: url('{(fonts / "dm-mono-500-latin.woff2").as_uri()}') format('woff2'); }}
html, body {{ margin: 0; padding: 0; background: {NAVY}; }}
svg {{ display: block; }}
.serif {{ font-family: 'Cormorant Garamond', Georgia, serif; }}
.mono {{ font-family: 'DM Mono', monospace; }}
.title {{ font-size: 86px; font-weight: 500; fill: {IVORY}; letter-spacing: -0.5px; }}
.dotcom {{ fill: {GOLD}; font-weight: 400; }}
.italic {{ font-style: italic; }}
.sub {{ font-size: 44px; font-weight: 400; fill: #E3C98F; }}
.label {{ font-size: 17px; font-weight: 500; fill: {GOLD}; letter-spacing: 3.4px; }}
.small {{ font-size: 21px; font-weight: 400; fill: {MUTED}; letter-spacing: 0.4px; white-space: pre; }}
.tiny {{ font-size: 15px; font-weight: 400; fill: {MUTED}; letter-spacing: 2px; opacity: 0.8; }}
</style></head>
<body>{svg()}</body></html>
"""


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or ROOT.resolve() in Path(sys.argv[1]).resolve().parents:
        sys.exit("usage: og_image.py OUT.html  (a path outside the repository)")
    Path(sys.argv[1]).write_text(html(), encoding="utf-8")
    print(f"wrote {sys.argv[1]}")
