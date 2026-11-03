"""Animated profile banner: a dot grid that a soft wave of light ripples across (after opencode's
pattern ripple) and a light sweep over the name (after its wordmark shimmer).

Text is converted to outlines so the SVG renders the same everywhere; GitHub serves README images
without web fonts or scripts, so all motion is SMIL inside the SVG.

Fonts: tools/fonts/SourceSans3.ttf (Google Fonts, variable) and Noto Sans JP (Windows: C:/Windows/Fonts/NotoSansJP-VF.ttf).
Usage: python -I -B tools/build_banner.py .
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

HERE = Path(__file__).parent
OUT = Path(sys.argv[1])
W, H = 1280, 300

THEMES = {
    "light": dict(bg="#ffffff", ink="#000000", sub="#555555", accent="#0076df", dot="#000000", dot_op=0.10, glow="#0076df", shimmer=0.55),
    "dark": dict(bg="#0d1117", ink="#f0f6fc", sub="#9198a1", accent="#4ea1ff", dot="#ffffff", dot_op=0.09, glow="#7cc0ff", shimmer=0.35),
}


def font(path, **axes):
    f = TTFont(path)
    return instantiateVariableFont(f, axes) if "fvar" in f else f


SANS_B = font(HERE / "fonts/SourceSans3.ttf", wght=700)
SANS_R = font(HERE / "fonts/SourceSans3.ttf", wght=400)
SANS_S = font(HERE / "fonts/SourceSans3.ttf", wght=600)
CJK = font("C:/Windows/Fonts/NotoSansJP-VF.ttf", wght=600)


def text_path(f, text, x, y, size, tracking=0.0):
    """Outline of `text` with its baseline at (x, y); returns (path d, advance width)."""
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    scale = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs)
    cx = x
    for ch in text:
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, y)))
        cx += hmtx[g][0] * scale + tracking * size
    return pen.getCommands(), cx - x


def banner(t):
    name_d, name_w = text_path(SANS_B, "Dengzhe Hou", 96, 150, 76, -0.01)
    cjk_d, _ = text_path(CJK, "侯登哲", 96 + name_w + 26, 150, 46)
    role_d, _ = text_path(SANS_R, "Assistant Professor · Graduate School of Information Sciences, Tohoku University", 98, 200, 25)
    dirs = ["AI4Cog", "Cog4AI", "AI4Brain", "Brain4AI"]
    x, parts = 98, []
    for i, word in enumerate(dirs):
        d, w = text_path(SANS_S, word, x, 246, 25, 0.01)
        parts.append(d)
        x += w
        if i < len(dirs) - 1:
            dot_d, dw = text_path(SANS_R, "  ·  ", x, 246, 25)
            parts.append(("sep", dot_d))
            x += dw
    dirs_d = "".join(p for p in parts if isinstance(p, str))
    seps_d = "".join(p[1] for p in parts if isinstance(p, tuple))

    # ripples: origin, start (s) within a 12 s loop, reach (px)
    ripples = [(1090, 140, 0.0, 560), (940, 240, 4.0, 520), (1200, 50, 8.0, 540)]
    loop = 12.0
    grads, masks, layers = [], [], []
    for i, (cx, cy, start, reach) in enumerate(ripples):
        a, b = start / loop, (start + 4.4) / loop
        kt = f"0;{a:.4f};{b:.4f};1"
        grads.append(
            f'<radialGradient id="rg{i}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="1">'
            '<stop offset="0" stop-color="#000"/><stop offset="0.62" stop-color="#000"/>'
            '<stop offset="0.86" stop-color="#fff"/><stop offset="0.93" stop-color="#fff"/>'
            '<stop offset="1" stop-color="#000"/>'
            f'<animate attributeName="r" dur="{loop}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="{kt}" values="1;1;{reach};{reach}" keySplines="0 0 1 1;0.25 0.45 0.45 1;0 0 1 1"/>'
            "</radialGradient>"
        )
        masks.append(f'<mask id="m{i}"><rect width="{W}" height="{H}" fill="url(#rg{i})"/></mask>')
        layers.append(
            f'<g mask="url(#m{i})" opacity="0"><rect width="{W}" height="{H}" fill="url(#glowdots)"/>'
            f'<animate attributeName="opacity" dur="{loop}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="0;{a:.4f};{a + 0.01:.4f};{b:.4f};1" values="0;0;1;0;0" '
            'keySplines="0 0 1 1;0 0 1 1;0.4 0 0.8 1;0 0 1 1"/></g>'
        )

    shimmer_mask = (
        '<linearGradient id="sweep" gradientUnits="userSpaceOnUse" x1="-400" y1="0" x2="-100" y2="0">'
        '<stop offset="0" stop-color="#000"/><stop offset="0.5" stop-color="#fff"/><stop offset="1" stop-color="#000"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" dur="{loop}s" repeatCount="indefinite" '
        'keyTimes="0;0.02;0.14;1" values="0 0;0 0;1250 0;1250 0"/></linearGradient>'
        f'<mask id="ms"><rect width="{W}" height="{H}" fill="url(#sweep)"/></mask>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Dengzhe Hou 侯登哲. Assistant Professor, Graduate School of Information Sciences, Tohoku University. AI4Cog, Cog4AI, AI4Brain, Brain4AI.">
<defs>
<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="8" cy="8" r="1.5" fill="{t['dot']}"/></pattern>
<pattern id="glowdots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="8" cy="8" r="1.9" fill="{t['glow']}"/></pattern>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset="0.3" stop-color="#000"/><stop offset="0.62" stop-color="#fff"/></linearGradient>
<mask id="field"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
{"".join(grads)}
{"".join(masks)}
{shimmer_mask}
</defs>
<rect width="{W}" height="{H}" rx="12" fill="{t['bg']}"/>
<g mask="url(#field)">
<rect width="{W}" height="{H}" fill="url(#dots)" opacity="{t['dot_op']}"/>
{"".join(layers)}
</g>
<path d="{name_d}" fill="{t['ink']}"/>
<path d="{cjk_d}" fill="{t['ink']}"/>
<g mask="url(#ms)" opacity="{t['shimmer']}"><path d="{name_d}" fill="{t['accent']}"/><path d="{cjk_d}" fill="{t['accent']}"/></g>
<path d="{role_d}" fill="{t['sub']}"/>
<path d="{dirs_d}" fill="{t['accent']}"/>
<path d="{seps_d}" fill="{t['sub']}"/>
</svg>
'''


OUT.mkdir(parents=True, exist_ok=True)
for name, t in THEMES.items():
    p = OUT / f"banner-{name}.svg"
    p.write_text(banner(t), encoding="utf-8")
    print(p, p.stat().st_size // 1024, "KB")
