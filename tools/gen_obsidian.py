#!/usr/bin/env python3
"""
Obsidian Studio README SVG generator for anurag3407.

Design language:
- Pitch-black / obsidian canvas (#050507) with carbon surfaces (#0A0A0E, #111117)
- Hairline 1px borders (#1D1D25) & specular top-edge highlights (#343442)
- Display typography converted to <path> outlines via fontTools (pixel-exact across OSes)
- Pure CSS @keyframes animations (100% compatible with GitHub's <img> SVG sandbox)

Usage:
    tools/.venv/bin/python tools/gen_obsidian.py
    tools/.venv/bin/python tools/gen_obsidian.py --preview
"""

import argparse
import base64
import io
import math
import os
import subprocess
from functools import lru_cache

from PIL import Image, ImageEnhance, ImageOps
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
PREVIEW = os.path.join(ASSETS, "preview")
PORTRAIT_SRC = os.path.join(ASSETS, "portrait.webp")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ------------------------------------------------------------------ palette --
VOID = "#050507"
CARD = "#0A0A0E"
CARD_HI = "#101016"
WELL = "#13131A"
BORDER = "#1D1D26"
BORDER_HI = "#2E2E3B"
GRID = "#111118"

INK = "#F4F4F6"
INK_2 = "#A0A0AE"
INK_3 = "#626270"

EMERALD = "#10B981"
EMERALD_GLOW = "#34D399"
EMBER = "#FF5C35"
ICE = "#60A5FA"
AMBER = "#F59E0B"

MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Helvetica Neue','Segoe UI',Arial,sans-serif"

# -------------------------------------------------------------------- fonts --
FONT_HELV_REG = ("/System/Library/Fonts/HelveticaNeue.ttc", 0)
FONT_HELV_BOLD = ("/System/Library/Fonts/HelveticaNeue.ttc", 1)
FONT_HELV_MED = ("/System/Library/Fonts/HelveticaNeue.ttc", 10)
FONT_HELV_LIGHT = ("/System/Library/Fonts/HelveticaNeue.ttc", 7)
FONT_SERIF_ITALIC = ("/System/Library/Fonts/Supplemental/Didot.ttc", 1)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@lru_cache(maxsize=None)
def load_font(spec):
    path, idx = spec
    font = TTFont(path, fontNumber=idx)
    return font, font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm


def path_width(text, spec, size, tracking=0.0):
    _, gs, cmap, upm = load_font(spec)
    s = size / upm
    w = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        w += gs[gname].width * s + tracking
    if text:
        w -= tracking
    return w


def path_text(text, spec, size, x, y, anchor="start", tracking=0.0,
              fill=INK, opacity=1.0, cls="", extra=""):
    """Render display typography as exact vector <path> outlines."""
    _, gs, cmap, upm = load_font(spec)
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
    s = size / upm
    xunits = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        glyph = gs[gname]
        glyph.draw(TransformPen(pen, (1, 0, 0, 1, xunits, 0)))
        xunits += glyph.width + tracking / s
    d = pen.getCommands()
    w = path_width(text, spec, size, tracking)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    transform = f"translate({x:.1f} {y:.1f}) scale({s:.5f} {-s:.5f})"
    cls_attr = f' class="{cls}"' if cls else ""
    op_attr = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return f'<path d="{d}" fill="{fill}" transform="{transform}"{cls_attr}{op_attr}{extra}/>'


def txt(s, x, y, size=12, family=SANS, fill=INK_2, weight="400",
        anchor="start", spacing=0, opacity=1.0, cls="", extra=""):
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{op}{c}{extra}>'
            f'{esc(s)}</text>')


def pill(x, y, label, bg=WELL, border=BORDER, fg=INK_2, size=10.5, h=24, px=11):
    w = round(len(label) * size * 0.60 + px * 2)
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{h/2:.1f}" '
        f'fill="{bg}" stroke="{border}" stroke-width="1"/>'
        f'<text x="{x + w/2:.1f}" y="{y + h/2 + size*0.34:.1f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="{size}" fill="{fg}">{esc(label)}</text>'
    ), w


# ----------------------------------------------------------------- portrait --
@lru_cache(maxsize=None)
def obsidian_portrait_uri():
    """Monochrome silver-gelatin editorial crop of Anurag on obsidian black."""
    im = Image.open(PORTRAIT_SRC).convert("RGBA")
    w, h = im.size
    # Frame upper body & face nicely
    crop_box = (int(0.14 * w), int(0.02 * h), int(0.84 * w), int(0.68 * h))
    crop = im.crop(crop_box)
    # Extract alpha & desaturate into editorial darkroom monochrome
    alpha = crop.split()[3]
    gray = ImageOps.grayscale(crop)
    gray = ImageEnhance.Contrast(gray).enhance(1.22)
    gray = ImageEnhance.Brightness(gray).enhance(0.96)
    # Slight cool silver tint
    r = gray.point(lambda p: int(p * 0.96))
    g = gray.point(lambda p: int(p * 0.97))
    b = gray
    fg = Image.merge("RGBA", (r, g, b, alpha))
    bg = Image.new("RGBA", crop.size, (10, 10, 14, 255))
    comp = Image.alpha_composite(bg, fg).convert("RGB")
    comp = comp.resize((360, 440), Image.LANCZOS)
    buf = io.BytesIO()
    comp.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------ shared --
def svg_shell(w, h, body, defs="", css="", label="obsidian card"):
    base_css = (
        "@media(prefers-reduced-motion:reduce){*{animation:none!important}}"
        "text{user-select:none}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">\n'
        f'<defs>\n{defs}\n<style>{base_css}{css}</style>\n</defs>\n'
        f'{body}\n</svg>'
    )


def card_frame(x, y, w, h, rx=18, fill="url(#cardBg)"):
    """Obsidian surface with 1px hairline border + top specular rim."""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{BORDER}" stroke-width="1"/>'
        f'<line x1="{x + rx}" y1="{y + 0.75}" x2="{x + w - rx}" y2="{y + 0.75}" '
        f'stroke="url(#rim)" stroke-width="1"/>'
    )


COMMON_DEFS = f"""
<linearGradient id="cardBg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#0C0C11"/>
  <stop offset="1" stop-color="#07070A"/>
</linearGradient>
<linearGradient id="rim" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{BORDER}" stop-opacity="0"/>
  <stop offset="0.35" stop-color="#383846" stop-opacity="0.9"/>
  <stop offset="0.65" stop-color="#4A4A5C" stop-opacity="0.9"/>
  <stop offset="1" stop-color="{BORDER}" stop-opacity="0"/>
</linearGradient>
<pattern id="microGrid" width="24" height="24" patternUnits="userSpaceOnUse">
  <path d="M24 0H0V24" fill="none" stroke="{GRID}" stroke-width="0.8"/>
</pattern>
"""


# =============================================================================
# 1. HERO — Editorial Obsidian Identity + Portrait + Live Marquee (900 x 440)
# =============================================================================
def gen_hero(preview=False):
    W, H = 900, 440
    uri = obsidian_portrait_uri()

    marquee_items = (
        "TYPESCRIPT  ·  NEXT.JS  ·  REACT  ·  NODE.JS  ·  PYTHON  ·  "
        "DJANGO  ·  POSTGRESQL  ·  DOCKER  ·  AI AGENTS  ·  OPEN SOURCE  ·  "
    )

    css = "" if preview else """
@keyframes pulseRing{0%{transform:scale(1);opacity:.75}70%{transform:scale(2.3);opacity:0}100%{transform:scale(2.3);opacity:0}}
@keyframes sheen{0%{transform:translateX(-460px) skewX(-18deg);opacity:0}15%{opacity:1}50%{transform:translateX(1100px) skewX(-18deg);opacity:0}100%{transform:translateX(1100px) skewX(-18deg);opacity:0}}
@keyframes orbit{to{transform:rotate(360deg)}}
@keyframes orbitRev{to{transform:rotate(-360deg)}}
@keyframes eq1{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}
@keyframes eq2{0%,100%{transform:scaleY(.9)}50%{transform:scaleY(.3)}}
@keyframes eq3{0%,100%{transform:scaleY(.5)}50%{transform:scaleY(.95)}}
@keyframes marquee{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
@keyframes scanline{0%{transform:translateY(0);opacity:0}12%{opacity:.45}88%{opacity:.45}100%{transform:translateY(290px);opacity:0}}
.pr{transform-box:fill-box;transform-origin:center;animation:pulseRing 2.4s cubic-bezier(.2,.8,.3,1) infinite}
.sh{animation:sheen 7.5s ease-in-out infinite}
.orb1{transform-box:fill-box;transform-origin:center;animation:orbit 28s linear infinite}
.orb2{transform-box:fill-box;transform-origin:center;animation:orbitRev 40s linear infinite}
.b1{transform-box:fill-box;transform-origin:bottom;animation:eq1 1.1s ease-in-out infinite}
.b2{transform-box:fill-box;transform-origin:bottom;animation:eq2 1.4s ease-in-out infinite}
.b3{transform-box:fill-box;transform-origin:bottom;animation:eq3 0.9s ease-in-out infinite}
.mq{animation:marquee 24s linear infinite}
.sc{animation:scanline 5.5s ease-in-out infinite}
"""

    defs = COMMON_DEFS + f"""
<radialGradient id="topGlow" cx="0.72" cy="0.18" r="0.6">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.06"/>
  <stop offset="0.5" stop-color="#10B981" stop-opacity="0.025"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="nameGrad" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#FFFFFF"/>
  <stop offset="1" stop-color="#A8A8B6"/>
</linearGradient>
<linearGradient id="sheenGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.045"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<linearGradient id="photoFade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#0A0A0E" stop-opacity="0"/>
  <stop offset="0.54" stop-color="#0A0A0E" stop-opacity="0"/>
  <stop offset="0.82" stop-color="#0A0A0E" stop-opacity="0.78"/>
  <stop offset="1" stop-color="#0A0A0E" stop-opacity="0.98"/>
</linearGradient>
<linearGradient id="mqFadeL" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#09090D"/>
  <stop offset="1" stop-color="#09090D" stop-opacity="0"/>
</linearGradient>
<linearGradient id="mqFadeR" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#09090D" stop-opacity="0"/>
  <stop offset="1" stop-color="#09090D"/>
</linearGradient>
<clipPath id="heroClip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20"/></clipPath>
<clipPath id="photoClip"><rect x="598" y="66" width="262" height="304" rx="14"/></clipPath>
<clipPath id="mqClip"><rect x="2" y="392" width="{W-4}" height="46"/></clipPath>
"""

    # Top bar
    top_bar = (
        f'<circle cx="44" cy="36" r="4" fill="{EMERALD}"/>'
        f'<circle class="pr" cx="44" cy="36" r="4" fill="none" stroke="{EMERALD}" stroke-width="1.4"/>'
        + txt("AVAILABLE FOR 2027 INTERNSHIPS", 58, 39.5, 10.5, MONO, INK_2, "600", spacing=1.4)
        + f'<rect class="b1" x="720" y="29" width="2.2" height="11" rx="1" fill="{EMERALD}"/>'
        + f'<rect class="b2" x="725" y="29" width="2.2" height="11" rx="1" fill="{INK_2}"/>'
        + f'<rect class="b3" x="730" y="29" width="2.2" height="11" rx="1" fill="{INK_3}"/>'
        + txt("NIT PATNA · CSE", 860, 39.5, 10.5, MONO, INK_3, "500", anchor="end", spacing=1.3)
        + f'<line x1="36" y1="56" x2="{W-36}" y2="56" stroke="{BORDER}" stroke-width="1"/>'
    )

    # Left Editorial Column
    eyebrow = txt("INDEX 00 / FULL-STACK & AI SYSTEMS", 40, 100, 10.5, MONO, INK_3, "600", spacing=1.8)
    title_1 = path_text("Anurag", FONT_HELV_BOLD, 74, 38, 174, tracking=-2.2, fill="url(#nameGrad)")
    title_2 = path_text("Mishra", FONT_HELV_BOLD, 74, 38, 246, tracking=-2.2, fill="url(#nameGrad)")
    accent_dot = f'<circle cx="276" cy="240" r="5.5" fill="{EMERALD}"/>'

    tagline = (
        txt("I engineer tools that take work off someone's hands —", 40, 286, 15.5, SANS, INK_2, "400")
        + txt("interview prep, PR review, and developer infrastructure.", 40, 309, 15.5, SANS, INK_2, "400")
    )

    # Manifesto pill + CTA metric strip
    motto_box = (
        f'<rect x="40" y="334" width="320" height="34" rx="8" fill="{WELL}" stroke="{BORDER_HI}" stroke-width="1"/>'
        + f'<rect x="52" y="347" width="6" height="6" rx="1.5" fill="{EMBER}"/>'
        + txt("BREAK THE PROBLEM FIRST. BUILD SECOND.", 68, 355, 10.2, MONO, INK, "600", spacing=0.9)
    )
    stat_pill = (
        f'<rect x="372" y="334" width="156" height="34" rx="8" fill="{CARD}" stroke="{BORDER}" stroke-width="1"/>'
        + txt("135★", 388, 355.5, 12, MONO, INK, "700")
        + txt("· 162 REPOS", 428, 355, 10.5, MONO, INK_3, "500", spacing=0.6)
    )

    # Right Editorial Portrait Frame
    # Subtle rotating orbital arcs behind portrait card
    reticle = (
        f'<g opacity="0.55">'
        f'<circle class="orb1" cx="729" cy="218" r="146" fill="none" stroke="{BORDER_HI}" stroke-width="1" stroke-dasharray="3 9"/>'
        f'<circle class="orb2" cx="729" cy="218" r="132" fill="none" stroke="{EMERALD}" stroke-width="0.8" stroke-dasharray="18 140" opacity="0.55"/>'
        f'</g>'
    )

    portrait_frame = (
        f'<rect x="598" y="66" width="262" height="304" rx="14" fill="#0B0B10" stroke="{BORDER_HI}" stroke-width="1"/>'
        f'<g clip-path="url(#photoClip)">'
        f'<image href="{uri}" x="598" y="66" width="262" height="304" preserveAspectRatio="xMidYMin slice"/>'
        f'<rect x="598" y="66" width="262" height="304" fill="url(#photoFade)"/>'
        + ("" if preview else f'<rect class="sc" x="598" y="66" width="262" height="1.5" fill="{EMERALD}" opacity="0.35"/>')
        + f'</g>'
        # Registration crosshairs + caption
        + f'<path d="M608 76h10M613 71v10" stroke="{INK_3}" stroke-width="1"/>'
        + f'<path d="M840 76h10M845 71v10" stroke="{INK_3}" stroke-width="1"/>'
        + txt("@anurag3407", 614, 342, 11.5, MONO, INK, "600", spacing=0.5)
        + txt("25.59°N · IN", 844, 342, 10, MONO, INK_3, "500", anchor="end", spacing=0.6)
        + txt("FULL-STACK · AI", 614, 357, 9.5, MONO, EMERALD, "600", spacing=1.1)
    )

    # Bottom Marquee Ticker
    marquee_y = 419
    marquee = (
        f'<line x1="1" y1="392" x2="{W-1}" y2="392" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect x="1" y="393" width="{W-2}" height="46" fill="#08080C"/>'
        f'<g clip-path="url(#mqClip)">'
        f'<g class="mq">'
        + txt(marquee_items + marquee_items, 20, marquee_y, 10.5, MONO, INK_3, "600", spacing=1.8)
        + f'</g>'
        f'<rect x="1" y="393" width="90" height="46" fill="url(#mqFadeL)"/>'
        f'<rect x="{W-91}" y="393" width="90" height="46" fill="url(#mqFadeR)"/>'
        f'</g>'
    )

    body = (
        f'<rect width="{W}" height="{H}" rx="20" fill="{VOID}"/>'
        f'<g clip-path="url(#heroClip)">'
        f'<rect width="{W}" height="{H}" fill="url(#cardBg)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.8"/>'
        f'<rect width="{W}" height="{H}" fill="url(#topGlow)"/>'
        + ("" if preview else f'<rect class="sh" x="0" y="0" width="220" height="{H}" fill="url(#sheenGrad)"/>')
        + reticle
        + top_bar
        + eyebrow + title_1 + title_2 + accent_dot
        + tagline + motto_box + stat_pill
        + portrait_frame
        + marquee
        + f'</g>'
        + f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        + f'<line x1="22" y1="0.75" x2="{W-22}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(W, H, body, defs=defs, css=css, label="Anurag Mishra — Obsidian Portfolio Hero")


# =============================================================================
# 2. DIVIDER — Razor Hairline with Counter-Traveling Pulses (900 x 24)
# =============================================================================
def gen_divider(preview=False):
    W, H = 900, 24
    css = "" if preview else """
@keyframes glideR{0%{transform:translateX(0);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateX(840px);opacity:0}}
@keyframes glideL{0%{transform:translateX(0);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateX(-840px);opacity:0}}
.pR{animation:glideR 3.4s cubic-bezier(.4,0,.2,1) infinite}
.pL{animation:glideL 3.4s cubic-bezier(.4,0,.2,1) infinite 1.7s}
"""
    defs = f"""
<linearGradient id="dl" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{BORDER}" stop-opacity="0"/>
  <stop offset="0.2" stop-color="{BORDER}"/>
  <stop offset="0.8" stop-color="{BORDER}"/>
  <stop offset="1" stop-color="{BORDER}" stop-opacity="0"/>
</linearGradient>
"""
    body = (
        f'<rect x="20" y="11.5" width="860" height="1" fill="url(#dl)"/>'
        f'<polygon points="450,7 455,12 450,17 445,12" fill="{CARD}" stroke="{BORDER_HI}" stroke-width="1"/>'
        f'<circle cx="450" cy="12" r="1.5" fill="{EMERALD}"/>'
        f'<g class="pR"><rect x="24" y="11" width="44" height="2" rx="1" fill="{INK}" opacity="0.75"/></g>'
        f'<g class="pL"><rect x="832" y="11" width="44" height="2" rx="1" fill="{EMERALD}" opacity="0.75"/></g>'
    )
    return svg_shell(W, H, body, defs=defs, css=css, label="Section divider")


# =============================================================================
# 3. FLAGSHIP — career-pilot Full-Width Bento Card (900 x 300)
# =============================================================================
def gen_flagship(preview=False):
    W, H = 900, 300
    css = "" if preview else """
@keyframes flowDown{0%{transform:translateY(0);opacity:0}12%{opacity:1}88%{opacity:1}100%{transform:translateY(138px);opacity:0}}
@keyframes beacon{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes sweepCard{0%{transform:translateX(-340px) skewX(-18deg);opacity:0}18%{opacity:1}55%{transform:translateX(980px) skewX(-18deg);opacity:0}100%{transform:translateX(980px) skewX(-18deg);opacity:0}}
.flw{animation:flowDown 2.8s cubic-bezier(.4,0,.2,1) infinite}
.bcn{animation:beacon 2s ease-in-out infinite}
.swc{animation:sweepCard 8s ease-in-out infinite}
"""
    defs = COMMON_DEFS + f"""
<radialGradient id="flagGlow" cx="0.82" cy="0.45" r="0.55">
  <stop offset="0" stop-color="{EMERALD}" stop-opacity="0.06"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="swGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.035"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<clipPath id="fcClip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath>
"""
    # fix closing tag typo in defs above -> make sure radialGradient closes properly
    defs = COMMON_DEFS + f"""
<radialGradient id="flagGlow" cx="0.82" cy="0.45" r="0.55">
  <stop offset="0" stop-color="{EMERALD}" stop-opacity="0.065"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="swGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.035"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<clipPath id="fcClip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath>
"""

    # Left column content
    eyebrow = (
        f'<rect x="38" y="34" width="194" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}" stroke-width="1"/>'
        f'<circle class="bcn" cx="52" cy="46" r="3" fill="{EMERALD}"/>'
        + txt("01 / FLAGSHIP · OPEN SOURCE", 62, 49.5, 9.8, MONO, INK, "600", spacing=0.9)
    )
    title = path_text("career-pilot", FONT_HELV_BOLD, 44, 38, 114, tracking=-1.2, fill=INK)
    desc = (
        txt("An open-source AI career platform unifying resume optimization,", 40, 146, 14.5, SANS, INK_2, "400")
        + txt("mock interviews, application tracking, and portfolio building.", 40, 168, 14.5, SANS, INK_2, "400")
    )

    chips_list = ["Next.js", "React", "Node.js", "AI / LLM", "PostgreSQL"]
    cx = 40
    chips_svg = []
    for c in chips_list:
        p_svg, pw = pill(cx, 196, c)
        chips_svg.append(p_svg)
        cx += pw + 8

    cta = (
        txt("EXPLORE REPOSITORY", 40, 260, 11, MONO, INK, "700", spacing=1.2)
        + txt("↗", 206, 260, 13, SANS, EMERALD, "700")
        + txt("github.com/anurag3407/career-pilot", 230, 260, 11, MONO, INK_3, "400")
    )

    # Right column: Live Pipeline Glass Sub-Card
    rx, ry, rw, rh = 556, 28, 312, 244
    subcard = [
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" rx="14" fill="#07070B" stroke="{BORDER_HI}" stroke-width="1"/>',
        f'<circle cx="{rx+18}" cy="{ry+22}" r="3" fill="{EMERALD}"/>',
        txt("135 STARS  ·  750 FORKS", rx + 30, ry + 25.5, 10, MONO, INK_2, "600", spacing=0.9),
        txt("LIVE", rx + rw - 16, ry + 25.5, 9.5, MONO, EMERALD, "700", anchor="end", spacing=1.1),
        f'<line x1="{rx+14}" y1="{ry+40}" x2="{rx+rw-14}" y2="{ry+40}" stroke="{BORDER}" stroke-width="1"/>',
        # Vertical trace
        f'<line x1="{rx+34}" y1="{ry+64}" x2="{rx+34}" y2="{ry+210}" stroke="{BORDER_HI}" stroke-width="1.5" stroke-dasharray="3 3"/>',
        f'<g class="flw"><circle cx="{rx+34}" cy="{ry+64}" r="3.5" fill="{EMERALD}"/><circle cx="{rx+34}" cy="{ry+64}" r="7" fill="{EMERALD}" opacity="0.25"/></g>',
    ]
    nodes = [
        ("01", "RESUME PARSER", "ATS + keyword diff"),
        ("02", "MOCK INTERVIEW", "adaptive AI rounds"),
        ("03", "JOB PIPELINE", "stage & offer tracking"),
        ("04", "PORTFOLIO GEN", "instant deploy"),
    ]
    for i, (num, ntitle, nsub) in enumerate(nodes):
        ny = ry + 64 + i * 44
        subcard.append(
            f'<circle cx="{rx+34}" cy="{ny}" r="5" fill="#0D0D13" stroke="{EMERALD if i == 0 else BORDER_HI}" stroke-width="1.5"/>'
            f'<rect x="{rx+52}" y="{ny-15}" width="242" height="30" rx="7" fill="{CARD_HI}" stroke="{BORDER}" stroke-width="1"/>'
            + txt(num, rx + 63, ny + 3.5, 9.5, MONO, INK_3, "700")
            + txt(ntitle, rx + 84, ny + 3.5, 10, MONO, INK, "600", spacing=0.6)
            + txt(nsub, rx + 284, ny + 3.5, 9.5, SANS, INK_3, "400", anchor="end")
        )

    body = (
        f'<rect width="{W}" height="{H}" rx="18" fill="{VOID}"/>'
        f'<g clip-path="url(#fcClip)">'
        f'<rect width="{W}" height="{H}" fill="url(#cardBg)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.55"/>'
        f'<rect width="{W}" height="{H}" fill="url(#flagGlow)"/>'
        + ("" if preview else f'<rect class="swc" x="0" y="0" width="180" height="{H}" fill="url(#swGrad)"/>')
        + eyebrow + title + desc + "".join(chips_svg) + cta + "".join(subcard)
        + f'</g>'
        + f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        + f'<line x1="20" y1="0.75" x2="{W-20}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(W, H, body, defs=defs, css=css, label="career-pilot flagship project card")


# =============================================================================
# 4. BENTO PROJECT CARDS (442 x 232 each — 2x2 grid below flagship)
# =============================================================================
def bento_card_base(w, h, num, tag, title, line1, line2, pills_list, visual_svg, css="", defs_extra=""):
    defs = COMMON_DEFS + defs_extra + f"""
<clipPath id="bClip"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16"/></clipPath>
"""
    header = (
        txt(f"{num} / {tag}", 26, 36, 9.8, MONO, INK_3, "600", spacing=1.2)
        + txt("↗", w - 26, 37, 14, SANS, INK_2, "700", anchor="end")
    )
    heading = path_text(title, FONT_HELV_BOLD, 28, 25, 72, tracking=-0.6, fill=INK)
    copy = (
        txt(line1, 26, 100, 12.8, SANS, INK_2, "400")
        + txt(line2, 26, 119, 12.8, SANS, INK_2, "400")
    )
    px = 26
    ps = []
    for p in pills_list:
        p_svg, pw = pill(px, 190, p, size=9.5, h=21, px=9)
        ps.append(p_svg)
        px += pw + 6

    body = (
        f'<rect width="{w}" height="{h}" rx="16" fill="{VOID}"/>'
        f'<g clip-path="url(#bClip)">'
        f'<rect width="{w}" height="{h}" fill="url(#cardBg)"/>'
        + header + heading + copy + visual_svg + "".join(ps)
        + f'</g>'
        + f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="16" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        + f'<line x1="18" y1="0.75" x2="{w-18}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(w, h, body, defs=defs, css=css, label=f"{title} project card")


def gen_card_codepolice(preview=False):
    W, H = 442, 232
    css = "" if preview else """
@keyframes scanX{0%,100%{transform:translateX(0)}50%{transform:translateX(352px)}}
.scn{animation:scanX 3.4s ease-in-out infinite}
"""
    # Miniature diff scanner bar
    vx, vy, vw, vh = 26, 136, 390, 42
    visual = (
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="8" fill="#07070B" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect x="{vx+12}" y="{vy+10}" width="118" height="5" rx="2.5" fill="{EMERALD}" opacity="0.75"/>'
        f'<rect x="{vx+138}" y="{vy+10}" width="64" height="5" rx="2.5" fill="{BORDER_HI}"/>'
        f'<rect x="{vx+12}" y="{vy+20}" width="84" height="5" rx="2.5" fill="{EMBER}" opacity="0.75"/>'
        f'<rect x="{vx+104}" y="{vy+20}" width="142" height="5" rx="2.5" fill="{BORDER_HI}"/>'
        f'<rect x="{vx+12}" y="{vy+30}" width="166" height="5" rx="2.5" fill="{INK_3}" opacity="0.5"/>'
        + txt("DIFF +42 / -18", vx + vw - 12, vy + 24.5, 9.5, MONO, EMERALD, "600", anchor="end")
        + ("" if preview else f'<rect class="scn" x="{vx+10}" y="{vy+4}" width="2" height="{vh-8}" rx="1" fill="{INK}" opacity="0.65"/>')
    )
    return bento_card_base(
        W, H, "02", "PR CO-MAINTAINER", "Code-Police",
        "Reviews pull requests, maps dependency impact,",
        "and catches merge conflicts before they land.",
        ["TypeScript", "AST", "GitHub"], visual, css=css
    )


def gen_card_storinary(preview=False):
    W, H = 442, 232
    css = "" if preview else """
@keyframes packet{0%{transform:translateX(0);opacity:0}12%{opacity:1}88%{opacity:1}100%{transform:translateX(274px);opacity:0}}
.pkt{animation:packet 2.4s cubic-bezier(.4,0,.2,1) infinite}
.pkt2{animation:packet 2.4s cubic-bezier(.4,0,.2,1) infinite 1.2s}
"""
    vx, vy, vw, vh = 26, 136, 390, 42
    visual = (
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="8" fill="#07070B" stroke="{BORDER}" stroke-width="1"/>'
        f'<line x1="{vx+64}" y1="{vy+21}" x2="{vx+338}" y2="{vy+21}" stroke="{BORDER_HI}" stroke-width="1.2" stroke-dasharray="3 3"/>'
        f'<rect x="{vx+12}" y="{vy+10}" width="54" height="22" rx="5" fill="{CARD_HI}" stroke="{BORDER_HI}"/>'
        + txt("BUCKET", vx + 39, vy + 24.5, 8.8, MONO, INK_2, "600", anchor="middle")
        + f'<rect x="{vx+150}" y="{vy+10}" width="90" height="22" rx="5" fill="{CARD_HI}" stroke="{EMERALD}" stroke-opacity="0.5"/>'
        + txt("TRANSFORM", vx + 195, vy + 24.5, 8.8, MONO, EMERALD, "600", anchor="middle")
        + f'<rect x="{vx+324}" y="{vy+10}" width="54" height="22" rx="5" fill="{CARD_HI}" stroke="{BORDER_HI}"/>'
        + txt("EDGE", vx + 351, vy + 24.5, 8.8, MONO, INK, "600", anchor="middle")
        + ("" if preview else
           f'<circle class="pkt" cx="{vx+64}" cy="{vy+21}" r="3" fill="{INK}"/>'
           f'<circle class="pkt2" cx="{vx+64}" cy="{vy+21}" r="3" fill="{EMERALD}"/>')
    )
    return bento_card_base(
        W, H, "03", "MEDIA INFRA", "Storinary",
        "Self-hosted image management and delivery.",
        "Upload, transform, and serve from your own bucket.",
        ["TypeScript", "Storage", "CDN"], visual, css=css
    )


def gen_card_ghostfounder(preview=False):
    W, H = 442, 232
    css = "" if preview else """
@keyframes waveA{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}
@keyframes waveB{0%,100%{transform:scaleY(.9)}50%{transform:scaleY(.28)}}
@keyframes waveC{0%,100%{transform:scaleY(.55)}50%{transform:scaleY(.95)}}
.wA{transform-box:fill-box;transform-origin:bottom;animation:waveA 1.3s ease-in-out infinite}
.wB{transform-box:fill-box;transform-origin:bottom;animation:waveB 1.6s ease-in-out infinite}
.wC{transform-box:fill-box;transform-origin:bottom;animation:waveC 1.1s ease-in-out infinite}
"""
    vx, vy, vw, vh = 26, 136, 390, 42
    bars = []
    classes = ["wA", "wB", "wC", "wA", "wC", "wB", "wA", "wB", "wC", "wA", "wB", "wC"]
    heights = [16, 22, 12, 24, 18, 14, 22, 16, 20, 12, 24, 15]
    for i, (cls_n, bh) in enumerate(zip(classes, heights)):
        bx = vx + 16 + i * 11
        color = EMERALD if i in (3, 7, 10) else INK_2
        bars.append(
            f'<rect class="{cls_n}" x="{bx}" y="{vy + 33 - bh}" width="4" height="{bh}" rx="2" fill="{color}" opacity="0.8"/>'
        )
    visual = (
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="8" fill="#07070B" stroke="{BORDER}" stroke-width="1"/>'
        + "".join(bars)
        + txt("NL2SQL · EQUITY · DECK", vx + vw - 14, vy + 24.5, 9.2, MONO, INK_3, "600", anchor="end", spacing=0.6)
    )
    return bento_card_base(
        W, H, "04", "FOUNDER SUITE", "GhostFounder",
        "Code review, pitch-deck generation, on-chain",
        "equity tools, and natural-language DB queries.",
        ["TypeScript", "AI", "Web3"], visual, css=css
    )


def gen_card_archive(preview=False):
    W, H = 442, 232
    css = "" if preview else """
@keyframes spinSlow{to{transform:rotate(360deg)}}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}
.spS{transform-box:fill-box;transform-origin:center;animation:spinSlow 22s linear infinite}
.ndg{animation:nudge 1.8s ease-in-out infinite}
"""
    defs = COMMON_DEFS + f"""
<clipPath id="aClip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16"/></clipPath>
"""
    rings = (
        f'<g opacity="0.55">'
        f'<circle class="spS" cx="378" cy="64" r="46" fill="none" stroke="{BORDER_HI}" stroke-width="1" stroke-dasharray="3 7"/>'
        f'<circle cx="378" cy="64" r="26" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<circle cx="378" cy="64" r="3" fill="{EMERALD}"/>'
        f'</g>'
    )
    big_num = path_text("162", FONT_HELV_BOLD, 56, 25, 94, tracking=-2.0, fill=INK)
    sub_lbl = (
        txt("PUBLIC", 136, 73, 9.8, MONO, INK_3, "600", spacing=1.1)
        + txt("REPOSITORIES", 136, 88, 9.8, MONO, INK_3, "600", spacing=1.1)
    )
    copy = (
        txt("Including Lexi, JusticeTrack, ChainCrate,", 26, 128, 12.8, SANS, INK_2, "400")
        + txt("chat-with-pdf, and daily systems experiments.", 26, 148, 12.8, SANS, INK_2, "400")
    )
    cta = (
        f'<rect x="26" y="176" width="390" height="34" rx="8" fill="{WELL}" stroke="{BORDER_HI}" stroke-width="1"/>'
        + txt("BROWSE ALL REPOSITORIES", 42, 197, 10.2, MONO, INK, "600", spacing=1.1)
        + f'<g class="ndg">' + txt("→", 394, 197.5, 14, SANS, EMERALD, "700", anchor="end") + f'</g>'
    )
    body = (
        f'<rect width="{W}" height="{H}" rx="16" fill="{VOID}"/>'
        f'<g clip-path="url(#aClip)">'
        f'<rect width="{W}" height="{H}" fill="url(#cardBg)"/>'
        + rings
        + txt("05 / ARCHIVE", 26, 36, 9.8, MONO, INK_3, "600", spacing=1.2)
        + big_num + sub_lbl + copy + cta
        + f'</g>'
        + f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        + f'<line x1="18" y1="0.75" x2="{W-18}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(W, H, body, defs=defs, css=css, label="All 162 repositories archive card")


# =============================================================================
# 5. STACK & LANGUAGE TELEMETRY (900 x 300)
#    Real GitHub API counts across 121 non-fork repos (95 language-tagged):
#    TS 62 (65%), JS 18 (19%), Python 5 (5%), CSS 5 (5%), HTML 4 (4%), Java 1 (1%)
# =============================================================================
def gen_stack(preview=False):
    W, H = 900, 300
    css = "" if preview else """
@keyframes barSweep{0%{transform:translateX(-220px);opacity:0}20%{opacity:1}80%{opacity:1}100%{transform:translateX(860px);opacity:0}}
.bsw{animation:barSweep 4.8s ease-in-out infinite}
"""
    defs = COMMON_DEFS + f"""
<linearGradient id="bswGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.32"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<clipPath id="stClip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath>
<clipPath id="barClip"><rect x="38" y="218" width="824" height="14" rx="7"/></clipPath>
"""

    cols = [
        ("01 / BUILD", 38, [
            ["TypeScript", "JavaScript", "React"],
            ["Next.js", "Node.js", "Python"],
            ["Django", "Tailwind"],
        ]),
        ("02 / DATA", 332, [
            ["PostgreSQL", "MongoDB"],
            ["Firebase", "SQL"],
        ]),
        ("03 / SHIP", 626, [
            ["Docker", "Git", "Linux"],
            ["Java (DSA)", "CI/CD"],
        ]),
    ]
    cols_svg = []
    for heading, cx, rows in cols:
        cols_svg.append(txt(heading, cx, 42, 10, MONO, INK_3, "700", spacing=1.4))
        ry = 58
        for row in rows:
            rx = cx
            for item in row:
                ps, pw = pill(rx, ry, item, bg=WELL, border=BORDER_HI, fg=INK, size=10.5, h=26, px=11)
                cols_svg.append(ps)
                rx += pw + 8
            ry += 34

    # Vertical hairline dividers between columns
    col_divs = (
        f'<line x1="312" y1="32" x2="312" y2="162" stroke="{BORDER}" stroke-width="1"/>'
        f'<line x1="606" y1="32" x2="606" y2="162" stroke="{BORDER}" stroke-width="1"/>'
        f'<line x1="38" y1="180" x2="{W-38}" y2="180" stroke="{BORDER}" stroke-width="1"/>'
    )

    # Real GitHub language telemetry bar
    langs = [
        ("TypeScript", 65.3, "#F4F4F6"),
        ("JavaScript", 18.9, "#8E8E9E"),
        ("Python", 5.3, EMERALD),
        ("CSS", 5.3, ICE),
        ("HTML", 4.2, EMBER),
        ("Java", 1.0, AMBER),
    ]
    bx, bw = 38, 824
    segs = []
    cur_x = bx
    for name, pct, color in langs:
        sw = bw * pct / 100.0
        segs.append(f'<rect x="{cur_x:.1f}" y="218" width="{sw:.1f}" height="14" fill="{color}"/>')
        cur_x += sw

    legend = []
    lx = 38
    for name, pct, color in langs:
        lbl = f"{name} {round(pct)}%"
        legend.append(
            f'<circle cx="{lx+4}" cy="252" r="3.5" fill="{color}"/>'
            + txt(lbl, lx + 13, 255.5, 10.5, MONO, INK_2, "500")
        )
        lx += len(lbl) * 6.5 + 34

    bar_section = (
        txt("LANGUAGE DISTRIBUTION · 121 ORIGINAL REPOS", 38, 204, 10, MONO, INK_3, "600", spacing=1.2)
        + txt("GITHUB API TELEMETRY", W - 38, 204, 9.5, MONO, EMERALD, "600", anchor="end", spacing=1.0)
        + f'<g clip-path="url(#barClip)">{"".join(segs)}'
        + ("" if preview else f'<rect class="bsw" x="38" y="218" width="140" height="14" fill="url(#bswGrad)"/>')
        + f'</g>'
        + f'<rect x="38" y="218" width="824" height="14" rx="7" fill="none" stroke="{BORDER_HI}" stroke-width="1"/>'
        + "".join(legend)
        + txt("typed > untyped", W - 38, 278, 10, MONO, INK_3, "500", anchor="end")
    )

    body = (
        f'<rect width="{W}" height="{H}" rx="18" fill="{VOID}"/>'
        f'<g clip-path="url(#stClip)">'
        f'<rect width="{W}" height="{H}" fill="url(#cardBg)"/>'
        + "".join(cols_svg) + col_divs + bar_section
        + f'</g>'
        + f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        + f'<line x1="20" y1="0.75" x2="{W-20}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(W, H, body, defs=defs, css=css, label="Tech stack and language telemetry")


# =============================================================================
# 6. FOOTER / WHAT'S NEXT — Editorial Closing Card (900 x 190)
# =============================================================================
def gen_footer(preview=False):
    W, H = 900, 190
    css = "" if preview else """
@keyframes pulseDot{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes orbFoot{to{transform:rotate(360deg)}}
.pdt{animation:pulseDot 2s ease-in-out infinite}
.obf{transform-box:fill-box;transform-origin:center;animation:orbFoot 26s linear infinite}
"""
    defs = COMMON_DEFS + f"""
<clipPath id="ftClip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath>
"""
    eyebrow = txt("04 / WHAT'S NEXT", 40, 40, 10, MONO, INK_3, "700", spacing=1.4)
    headline = path_text("Open to 2027 internships.", FONT_HELV_BOLD, 34, 38, 86, tracking=-0.9, fill=INK)
    sub = (
        txt("Contributing to open source, sharpening DSA in Java, and looking to work on", 40, 118, 14, SANS, INK_2, "400")
        + txt("high-leverage systems that matter to real users.", 40, 139, 14, SANS, INK_2, "400")
    )

    # Right colophon badge + orbital emblem
    emblem = (
        f'<g transform="translate(758,84)">'
        f'<circle class="obf" cx="0" cy="0" r="52" fill="none" stroke="{BORDER_HI}" stroke-width="1" stroke-dasharray="3 8"/>'
        f'<circle cx="0" cy="0" r="36" fill="{WELL}" stroke="{BORDER}" stroke-width="1"/>'
        + path_text("AM", FONT_SERIF_ITALIC, 26, 0, 9, anchor="middle", fill=INK)
        + f'</g>'
    )
    status_pill = (
        f'<rect x="652" y="148" width="212" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}" stroke-width="1"/>'
        f'<circle class="pdt" cx="667" cy="160" r="3" fill="{EMERALD}"/>'
        + txt("NIT PATNA · CLASS OF 2028", 677, 163.5, 9.5, MONO, INK_2, "600", spacing=0.7)
    )
    colophon = txt("anuragmishra3407@gmail.com  ·  github.com/anurag3407", 40, 168, 10.5, MONO, INK_3, "500")

    body = (
        f'<rect width="{W}" height="{H}" rx="18" fill="{VOID}"/>'
        f'<g clip-path="url(#ftClip)">'
        f'<rect width="{W}" height="{H}" fill="url(#cardBg)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.5"/>'
        + eyebrow + headline + sub + emblem + status_pill + colophon
        + f'</g>'
        + f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        + f'<line x1="20" y1="0.75" x2="{W-20}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(W, H, body, defs=defs, css=css, label="What's next and contact footer")


def gen_cta(label, sub, accent=EMERALD):
    def _fn(preview=False):
        W, H = 210, 46
        defs = COMMON_DEFS
        body = (
            f'<rect width="{W}" height="{H}" rx="10" fill="{VOID}"/>'
            + card_frame(0.5, 0.5, W - 1, H - 1, rx=10)
            + f'<circle cx="18" cy="23" r="3" fill="{accent}"/>'
            + txt(label, 30, 21, 10.5, MONO, INK, "700", spacing=0.9)
            + txt(sub, 30, 35, 9.5, MONO, INK_3, "500")
            + txt("↗", W - 16, 27, 13, SANS, INK_2, "700", anchor="end")
        )
        return svg_shell(W, H, body, defs=defs, label=label)
    return _fn


def render_preview_png(svg_path, png_path, w, h):
    with open(svg_path) as f:
        svg = f.read()
    html_path = svg_path + ".tmp.html"
    with open(html_path, "w") as f:
        f.write(
            f"<!DOCTYPE html><html><body style='margin:0;padding:0;background:#010409'>{svg}</body></html>"
        )
    try:
        subprocess.run([
            CHROME, "--headless", "--disable-gpu",
            f"--screenshot={png_path}",
            f"--window-size={w},{h}",
            "--virtual-time-budget=1200",
            "file://" + html_path,
        ], capture_output=True, check=True, timeout=30)
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="Also emit static preview SVGs + PNG renders")
    args = ap.parse_args()

    jobs = {
        "obsidian-hero.svg": (gen_hero, 900, 440),
        "obsidian-divider.svg": (gen_divider, 900, 24),
        "obsidian-flagship.svg": (gen_flagship, 900, 300),
        "obsidian-card-codepolice.svg": (gen_card_codepolice, 442, 232),
        "obsidian-card-storinary.svg": (gen_card_storinary, 442, 232),
        "obsidian-card-ghostfounder.svg": (gen_card_ghostfounder, 442, 232),
        "obsidian-card-archive.svg": (gen_card_archive, 442, 232),
        "obsidian-stack.svg": (gen_stack, 900, 300),
        "obsidian-footer.svg": (gen_footer, 900, 190),
        "obsidian-cta-email.svg": (gen_cta("EMAIL", "anuragmishra3407", EMERALD), 210, 46),
        "obsidian-cta-linkedin.svg": (gen_cta("LINKEDIN", "/in/anurag3407", ICE), 210, 46),
        "obsidian-cta-x.svg": (gen_cta("X / TWITTER", "@anurag3407", INK_2), 210, 46),
        "obsidian-cta-github.svg": (gen_cta("GITHUB", "162 repositories", EMBER), 210, 46),
    }

    os.makedirs(ASSETS, exist_ok=True)
    for name, (fn, w, h) in jobs.items():
        out = os.path.join(ASSETS, name)
        with open(out, "w") as f:
            f.write(fn(preview=False))
        print("wrote", out, f"({os.path.getsize(out)} bytes)")

    if args.preview:
        os.makedirs(PREVIEW, exist_ok=True)
        for name, (fn, w, h) in jobs.items():
            p_svg = os.path.join(PREVIEW, name)
            with open(p_svg, "w") as f:
                f.write(fn(preview=True))
            p_png = p_svg + ".png"
            render_preview_png(p_svg, p_png, w, h)
            print("rendered", p_png)


if __name__ == "__main__":
    main()
