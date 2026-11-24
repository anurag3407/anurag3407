#!/usr/bin/env python3
"""
Obsidian Studio README SVG generator for anurag3407.

Design language:
- Pitch-black / obsidian canvas (#050507) with carbon surfaces (#0A0A0E, #111117)
- Hairline 1px borders (#1D1D26) & specular top-edge highlights (#343442)
- Display typography converted to <path> outlines via fontTools (pixel-exact)
- Real official SVG brand paths loaded from tools/icon_paths.json
- Pure CSS @keyframes animations (100% compatible with GitHub's <img> SVG sandbox)

Usage:
    tools/.venv/bin/python tools/gen_obsidian.py
    tools/.venv/bin/python tools/gen_obsidian.py --preview
"""

import argparse
import base64
import io
import json
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
ICONS_SRC = os.path.join(HERE, "icon_paths.json")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

with open(ICONS_SRC) as _f:
    ICONS = json.load(_f)

# ------------------------------------------------------------------ palette --
VOID = "#050507"
CARD = "#0A0A0E"
CARD_HI = "#101016"
WELL = "#13131B"
BORDER = "#1D1D26"
BORDER_HI = "#2E2E3C"
GRID = "#111118"

INK = "#F4F4F6"
INK_2 = "#A2A2B0"
INK_3 = "#646473"

EMERALD = "#10B981"
SAYA_ORANGE = "#FF7A45"
EMBER = "#FF5C35"
ICE = "#60A5FA"
INDIGO = "#818CF8"
AMBER = "#F59E0B"

MONO = "'SF Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Helvetica Neue','Segoe UI',Arial,sans-serif"

# -------------------------------------------------------------------- fonts --
FONT_HELV_BOLD = ("/System/Library/Fonts/HelveticaNeue.ttc", 1)
FONT_HELV_MED = ("/System/Library/Fonts/HelveticaNeue.ttc", 10)
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


def brand_icon(slug, x, y, size=14, fill_override=None):
    """Render an official Simple Icons 24x24 vector path at (x, y)."""
    meta = ICONS[slug]
    color = fill_override or meta["color"]
    scale = size / 24.0
    return f'<path d="{meta["d"]}" fill="{color}" transform="translate({x:.1f} {y:.1f}) scale({scale:.4f})"/>'


def icon_pill(x, y, slug, label=None, h=24, size=10.2, icon_sz=12, px=10,
              bg=WELL, border=BORDER_HI, fg=INK):
    """Pill chip with an exact real brand SVG logo inside."""
    lbl = label or ICONS[slug]["label"]
    text_w = len(lbl) * size * 0.59
    gap = 6
    w = round(px + icon_sz + gap + text_w + px)
    iy = y + (h - icon_sz) / 2
    tx = x + px + icon_sz + gap
    ty = y + h / 2 + size * 0.34
    svg = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{h/2:.1f}" '
        f'fill="{bg}" stroke="{border}" stroke-width="1"/>'
        + brand_icon(slug, x + px, iy, size=icon_sz)
        + txt(lbl, tx, ty, size, MONO, fg, "500")
    )
    return svg, w


def plain_pill(x, y, label, bg=WELL, border=BORDER, fg=INK_2, size=10, h=23, px=10):
    w = round(len(label) * size * 0.60 + px * 2)
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{h/2:.1f}" '
        f'fill="{bg}" stroke="{border}" stroke-width="1"/>'
        + txt(label, x + w / 2, y + h / 2 + size * 0.34, size, MONO, fg, "500", anchor="middle")
    ), w


# ----------------------------------------------------------------- portrait --
@lru_cache(maxsize=None)
def obsidian_portrait_uri():
    im = Image.open(PORTRAIT_SRC).convert("RGBA")
    w, h = im.size
    crop_box = (int(0.14 * w), int(0.02 * h), int(0.84 * w), int(0.68 * h))
    crop = im.crop(crop_box)
    alpha = crop.split()[3]
    gray = ImageOps.grayscale(crop)
    gray = ImageEnhance.Contrast(gray).enhance(1.22)
    gray = ImageEnhance.Brightness(gray).enhance(0.96)
    r = gray.point(lambda p: int(p * 0.96))
    g = gray.point(lambda p: int(p * 0.97))
    b = gray
    fg = Image.merge("RGBA", (r, g, b, alpha))
    bg = Image.new("RGBA", crop.size, (10, 10, 14, 255))
    comp = Image.alpha_composite(bg, fg).convert("RGB").resize((360, 440), Image.LANCZOS)
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


def card_shell(w, h, inner, defs="", css="", rx=18, clip_id="cClip", label="card"):
    all_defs = COMMON_DEFS + defs + f'<clipPath id="{clip_id}"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{rx}"/></clipPath>'
    body = (
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="{VOID}"/>'
        f'<g clip-path="url(#{clip_id})">'
        f'<rect width="{w}" height="{h}" fill="url(#cardBg)"/>'
        f'{inner}'
        f'</g>'
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<line x1="{rx}" y1="0.75" x2="{w-rx}" y2="0.75" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg_shell(w, h, body, defs=all_defs, css=css, label=label)


# =============================================================================
# 1. HERO — Obsidian Identity (900 x 440) — NO "open to internship" copy
# =============================================================================
def gen_hero(preview=False):
    W, H = 900, 440
    uri = obsidian_portrait_uri()
    marquee_items = (
        "TYPESCRIPT  ·  NEXT.JS  ·  REACT  ·  NODE.JS  ·  PYTHON  ·  DJANGO  ·  "
        "POSTGRESQL  ·  MONGODB  ·  REDIS  ·  DOCKER  ·  CLOUDFLARE  ·  AI AGENTS  ·  "
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
    defs = f"""
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
<clipPath id="photoClip"><rect x="598" y="66" width="262" height="304" rx="14"/></clipPath>
<clipPath id="mqClip"><rect x="2" y="392" width="{W-4}" height="46"/></clipPath>
"""
    top_bar = (
        f'<circle cx="44" cy="36" r="4" fill="{EMERALD}"/>'
        f'<circle class="pr" cx="44" cy="36" r="4" fill="none" stroke="{EMERALD}" stroke-width="1.4"/>'
        + txt("SYSTEMS ONLINE · BUILDING OPEN SOURCE", 58, 39.5, 10.5, MONO, INK_2, "600", spacing=1.3)
        + f'<rect class="b1" x="720" y="29" width="2.2" height="11" rx="1" fill="{EMERALD}"/>'
        + f'<rect class="b2" x="725" y="29" width="2.2" height="11" rx="1" fill="{INK_2}"/>'
        + f'<rect class="b3" x="730" y="29" width="2.2" height="11" rx="1" fill="{INK_3}"/>'
        + txt("NIT PATNA · CSE", 860, 39.5, 10.5, MONO, INK_3, "500", anchor="end", spacing=1.3)
        + f'<line x1="36" y1="56" x2="{W-36}" y2="56" stroke="{BORDER}" stroke-width="1"/>'
    )
    eyebrow = txt("INDEX 00 / FULL-STACK & AI SYSTEMS", 40, 100, 10.5, MONO, INK_3, "600", spacing=1.8)
    title_1 = path_text("Anurag", FONT_HELV_BOLD, 74, 38, 174, tracking=-2.2, fill="url(#nameGrad)")
    title_2 = path_text("Mishra", FONT_HELV_BOLD, 74, 38, 246, tracking=-2.2, fill="url(#nameGrad)")
    accent_dot = f'<circle cx="276" cy="240" r="5.5" fill="{EMERALD}"/>'
    tagline = (
        txt("I engineer tools that take work off someone's hands —", 40, 286, 15.5, SANS, INK_2, "400")
        + txt("multi-agent workspaces, developer tooling, and cloud infra.", 40, 309, 15.5, SANS, INK_2, "400")
    )
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
        + f'<path d="M608 76h10M613 71v10" stroke="{INK_3}" stroke-width="1"/>'
        + f'<path d="M840 76h10M845 71v10" stroke="{INK_3}" stroke-width="1"/>'
        + txt("@anurag3407", 614, 342, 11.5, MONO, INK, "600", spacing=0.5)
        + txt("25.59°N · IN", 844, 342, 10, MONO, INK_3, "500", anchor="end", spacing=0.6)
        + txt("FULL-STACK · AI", 614, 357, 9.5, MONO, EMERALD, "600", spacing=1.1)
    )
    marquee = (
        f'<line x1="1" y1="392" x2="{W-1}" y2="392" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect x="1" y="393" width="{W-2}" height="46" fill="#08080C"/>'
        f'<g clip-path="url(#mqClip)"><g class="mq">'
        + txt(marquee_items + marquee_items, 20, 419, 10.5, MONO, INK_3, "600", spacing=1.8)
        + f'</g><rect x="1" y="393" width="90" height="46" fill="url(#mqFadeL)"/>'
        f'<rect x="{W-91}" y="393" width="90" height="46" fill="url(#mqFadeR)"/></g>'
    )
    inner = (
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.8"/>'
        f'<rect width="{W}" height="{H}" fill="url(#topGlow)"/>'
        + ("" if preview else f'<rect class="sh" x="0" y="0" width="220" height="{H}" fill="url(#sheenGrad)"/>')
        + reticle + top_bar + eyebrow + title_1 + title_2 + accent_dot
        + tagline + motto_box + stat_pill + portrait_frame + marquee
    )
    return card_shell(W, H, inner, defs=defs, css=css, rx=20, clip_id="heroClip", label="Anurag Mishra Hero")


# =============================================================================
# 2. DIVIDER (900 x 24)
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
# 3. PROJECT 01 — SAYABOT (900 x 430) — Exact 3 Bot Mascots + Room Specs
# =============================================================================
def mascot_pocket_saya(x, y, scale=0.22, color=SAYA_ORANGE, cls=""):
    """Exact Pocket Saya (bot-a / avatar.svg) mascot from anurag3407/sayabot."""
    return (
        f'<g class="{cls}" transform="translate({x:.1f} {y:.1f}) scale({scale:.4f})">'
        f'<g fill="{color}">'
        f'<circle cx="128" cy="26" r="14"/>'
        f'<circle cx="125" cy="22" r="4.5" fill="#FFC4AD"/>'
        f'<rect x="124" y="36" width="8" height="22" rx="4"/>'
        f'<rect x="22" y="98" width="22" height="48" rx="11"/>'
        f'<rect x="212" y="98" width="22" height="48" rx="11"/>'
        f'<rect x="36" y="54" width="184" height="152" rx="60"/>'
        f'</g>'
        f'<rect x="52" y="70" width="152" height="120" rx="44" fill="#0B0E0C"/>'
        f'<ellipse cx="74" cy="142" rx="8" ry="4" fill="{color}" opacity="0.45"/>'
        f'<ellipse cx="182" cy="142" rx="8" ry="4" fill="{color}" opacity="0.45"/>'
        f'<ellipse cx="94" cy="122" rx="16" ry="22" fill="#FFFFFF"/>'
        f'<ellipse cx="162" cy="122" rx="16" ry="22" fill="#FFFFFF"/>'
        f'<path d="M 118 144 Q 128 156 138 144" fill="none" stroke="#FFFFFF" stroke-width="5.5" stroke-linecap="round"/>'
        f'<circle cx="99" cy="115" r="6.5" fill="#0B0E0C" opacity="0.18"/>'
        f'<circle cx="167" cy="115" r="6.5" fill="#0B0E0C" opacity="0.18"/>'
        f'</g>'
    )


def mascot_monitor_roomie(x, y, scale=0.22, color=INDIGO, cls=""):
    """Exact Monitor Roomie (bot-b.svg) mascot from anurag3407/sayabot."""
    return (
        f'<g class="{cls}" transform="translate({x:.1f} {y:.1f}) scale({scale:.4f})">'
        f'<g fill="{color}">'
        f'<path d="M 78 48 L 56 18 C 53 14 56 8 62 8 C 65 8 68 10 71 14 L 96 46 Z"/>'
        f'<path d="M 178 48 L 200 18 C 203 14 200 8 194 8 C 191 8 188 10 185 14 L 160 46 Z"/>'
        f'<rect x="36" y="44" width="184" height="168" rx="52"/>'
        f'<rect x="74" y="212" width="36" height="18" rx="9"/>'
        f'<rect x="146" y="212" width="36" height="18" rx="9"/>'
        f'</g>'
        f'<rect x="52" y="60" width="152" height="136" rx="38" fill="#0B0E0C"/>'
        f'<g fill="#FFFFFF">'
        f'<path d="M 76 128 C 76 108 92 98 106 104 C 114 108 116 118 110 126 C 104 134 94 134 88 132 L 86 138 C 82 140 76 136 76 128 Z"/>'
        f'<path d="M 180 128 C 180 108 164 98 150 104 C 142 108 140 118 146 126 C 152 134 162 134 168 132 L 170 138 C 174 140 180 136 180 128 Z"/>'
        f'<circle cx="128" cy="136" r="6" fill="{color}"/>'
        f'<path d="M 118 154 Q 128 164 138 154" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>'
        f'</g></g>'
    )


def mascot_astro_bot(x, y, scale=0.22, color=EMERALD, cls=""):
    """Exact Astro Bot (bot-c.svg) mascot from anurag3407/sayabot."""
    return (
        f'<g class="{cls}" transform="translate({x:.1f} {y:.1f}) scale({scale:.4f})">'
        f'<g fill="{color}">'
        f'<ellipse cx="128" cy="24" rx="24" ry="8"/>'
        f'<rect x="124" y="26" width="8" height="18"/>'
        f'<rect x="22" y="98" width="24" height="52" rx="12"/>'
        f'<rect x="210" y="98" width="24" height="52" rx="12"/>'
        f'<circle cx="128" cy="124" r="86"/>'
        f'<circle cx="56" cy="208" r="18"/>'
        f'<circle cx="200" cy="208" r="18"/>'
        f'</g>'
        f'<path d="M 64 124 C 64 92 92 78 128 78 C 164 78 192 92 192 124 C 192 154 164 164 128 164 C 92 164 64 154 64 124 Z" fill="#0B0E0C"/>'
        f'<rect x="90" y="102" width="22" height="34" rx="11" fill="#FFFFFF"/>'
        f'<rect x="144" y="102" width="22" height="34" rx="11" fill="#FFFFFF"/>'
        f'<path d="M 120 144 Q 128 152 136 144" fill="none" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round"/>'
        f'</g>'
    )


def gen_sayabot(preview=False):
    W, H = 900, 430
    css = "" if preview else """
@keyframes bobA{0%,100%{transform:translateY(0)}50%{transform:translateY(-3.5px)}}
@keyframes bobB{0%,100%{transform:translateY(0)}50%{transform:translateY(-3.5px)}}
@keyframes bobC{0%,100%{transform:translateY(0)}50%{transform:translateY(-3.5px)}}
@keyframes busFlow{0%{transform:translateY(0);opacity:0}15%{opacity:1}85%{opacity:1}100%{transform:translateY(176px);opacity:0}}
@keyframes gatePulse{0%,100%{opacity:1}50%{opacity:.4}}
.mbA{animation:bobA 2.8s ease-in-out infinite}
.mbB{animation:bobB 3.2s ease-in-out infinite .6s}
.mbC{animation:bobC 2.6s ease-in-out infinite 1.2s}
.bsf{animation:busFlow 3s cubic-bezier(.4,0,.2,1) infinite}
.gp{animation:gatePulse 1.8s ease-in-out infinite}
"""
    defs = f"""
<radialGradient id="sayaGlow" cx="0.80" cy="0.35" r="0.58">
  <stop offset="0" stop-color="{SAYA_ORANGE}" stop-opacity="0.075"/>
  <stop offset="0.55" stop-color="{INDIGO}" stop-opacity="0.035"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</radialGradient>
"""
    # Left column
    eyebrow = (
        f'<rect x="38" y="30" width="248" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}"/>'
        f'<circle class="gp" cx="52" cy="42" r="3.2" fill="{SAYA_ORANGE}"/>'
        + txt("01 / MULTI-AGENT ROOM · FEATURED", 62, 45.5, 9.5, MONO, INK, "600", spacing=0.9)
    )
    title = path_text("Sayabot", FONT_HELV_BOLD, 44, 38, 108, tracking=-1.4, fill=INK)
    title_dot = f'<circle cx="212" cy="104" r="4.5" fill="{SAYA_ORANGE}"/>'
    subtitle = txt("The shared room where your team and coding agents work together.", 40, 134, 14.5, SANS, INK_2, "400")

    features = [
        ("MCP INVITE", SAYA_ORANGE, "Claude Code, Codex, Cursor, Hermes & ChatGPT via MCP."),
        ("HUMAN GATE", EMBER, "Deploys & shell pause on a 5-min card. AES-256-GCM."),
        ("SANDBOX", INDIGO, "Isolated /home/bot Linux Docker box + egress proxy."),
        ("LIVE CANVAS", EMERALD, "Shared Markdown/SVG/HTML + Mac, Win & Android."),
    ]
    fy = 160
    feat_svg = []
    for tag, col, desc in features:
        feat_svg.append(
            f'<rect x="40" y="{fy}" width="98" height="22" rx="6" fill="{WELL}" stroke="{BORDER}"/>'
            f'<circle cx="51" cy="{fy+11}" r="2.5" fill="{col}"/>'
            + txt(tag, 59, fy + 14.5, 8.5, MONO, INK, "700", spacing=0.3)
            + txt(desc, 147, fy + 14.5, 11.4, SANS, INK_2, "400")
        )
        fy += 33

    # Tech stack pills with real brand icons
    pills_data = [
        ("nextdotjs", "Next.js 16"),
        ("react", "React 19"),
        ("typescript", "TypeScript"),
        ("postgresql", "Postgres"),
        ("docker", "Docker"),
        ("anthropic", "MCP"),
    ]
    px = 40
    pills_svg = []
    for slug, lbl in pills_data:
        ps, pw = icon_pill(px, 314, slug, lbl, h=24, size=9.2, icon_sz=10.5, px=7)
        pills_svg.append(ps)
        px += pw + 5

    cta = (
        txt("EXPLORE WORKSPACE", 40, 386, 10.5, MONO, INK, "700", spacing=1.1)
        + txt("↗", 190, 386, 13, SANS, SAYA_ORANGE, "700")
        + txt("github.com/anurag3407/sayabot  ·  Mac / Win / Android", 212, 386, 10.5, MONO, INK_3, "400")
    )

    # Right column: Live Bot Room + All 3 Mascots
    rx, ry, rw, rh = 556, 26, 314, 378
    room_hdr = (
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" rx="16" fill="#07070B" stroke="{BORDER_HI}"/>'
        f'<circle cx="{rx+18}" cy="{ry+22}" r="3" fill="{EMERALD}"/>'
        + txt("ROOM: #LAUNCH-WEEK", rx + 29, ry + 25.5, 9.8, MONO, INK, "700", spacing=0.8)
        + txt("3 BOTS ONLINE", rx + rw - 16, ry + 25.5, 9.2, MONO, SAYA_ORANGE, "700", anchor="end", spacing=0.7)
        + f'<line x1="{rx+14}" y1="{ry+40}" x2="{rx+rw-14}" y2="{ry+40}" stroke="{BORDER}"/>'
        # Vertical agent bus trace
        + f'<line x1="{rx+43}" y1="{ry+78}" x2="{rx+43}" y2="{ry+272}" stroke="{BORDER_HI}" stroke-width="1.4" stroke-dasharray="3 3"/>'
        + ("" if preview else f'<circle class="bsf" cx="{rx+43}" cy="{ry+78}" r="3" fill="{SAYA_ORANGE}"/>')
    )

    bots = [
        ("POCKET SAYA", "Claude Code · Room Lead", "Claimed task #12 · editing canvas", SAYA_ORANGE, mascot_pocket_saya, "mbA"),
        ("MONITOR ROOMIE", "Codex · Sandbox Runner", "Running Playwright in /home/bot", INDIGO, mascot_monitor_roomie, "mbB"),
        ("ASTRO BOT", "Hermes · Guarded Deploy", "Waiting: deploy.sh --env prod", EMERALD, mascot_astro_bot, "mbC"),
    ]
    bots_svg = []
    for i, (bname, brole, bstat, bcol, mfn, mcls) in enumerate(bots):
        by = ry + 52 + i * 82
        bots_svg.append(
            f'<rect x="{rx+14}" y="{by}" width="{rw-28}" height="70" rx="11" fill="{CARD_HI}" stroke="{BORDER}" stroke-width="1"/>'
            + mfn(rx + 20, by + 10, scale=0.195, color=bcol, cls="" if preview else mcls)
            + txt(bname, rx + 80, by + 23, 10.2, MONO, INK, "700", spacing=0.7)
            + txt(brole, rx + 80, by + 39, 10.2, SANS, bcol, "600")
            + txt(bstat, rx + 80, by + 55, 10.2, SANS, INK_3, "400")
        )

    # Approval Gate Card at bottom of room
    ay = ry + 306
    approval_card = (
        f'<rect x="{rx+14}" y="{ay}" width="{rw-28}" height="56" rx="10" fill="#120E0D" stroke="{SAYA_ORANGE}" stroke-opacity="0.45"/>'
        f'<circle class="gp" cx="{rx+28}" cy="{ay+20}" r="3" fill="{SAYA_ORANGE}"/>'
        + txt("APPROVAL GATE · 04:58", rx + 39, ay + 23.5, 9.2, MONO, SAYA_ORANGE, "700", spacing=0.8)
        + txt("deploy.sh --env production", rx + 28, ay + 41, 10.2, MONO, INK_2, "400")
        + f'<rect x="{rx+220}" y="{ay+14}" width="66" height="26" rx="6" fill="{EMERALD}" fill-opacity="0.16" stroke="{EMERALD}" stroke-opacity="0.6"/>'
        + txt("APPROVE", rx + 253, ay + 30.5, 8.8, MONO, EMERALD, "700", anchor="middle", spacing=0.6)
    )

    inner = (
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.55"/>'
        f'<rect width="{W}" height="{H}" fill="url(#sayaGlow)"/>'
        + eyebrow + title + title_dot + subtitle
        + "".join(feat_svg) + "".join(pills_svg) + cta
        + room_hdr + "".join(bots_svg) + approval_card
    )
    return card_shell(W, H, inner, defs=defs, css=css, rx=18, clip_id="sayaClip", label="Sayabot project card")


# =============================================================================
# 4. PROJECT 02 — CAREER-PILOT (900 x 390) — Popular (135★ · 750 Forks) + 6 Pillars
# =============================================================================
def gen_careerpilot(preview=False):
    W, H = 900, 390
    css = "" if preview else """
@keyframes cpFlow{0%{transform:translateY(0);opacity:0}14%{opacity:1}86%{opacity:1}100%{transform:translateY(150px);opacity:0}}
@keyframes starPulse{0%,100%{opacity:1}50%{opacity:.45}}
@keyframes swp{0%{transform:translateX(-300px) skewX(-18deg);opacity:0}18%{opacity:1}55%{transform:translateX(960px) skewX(-18deg);opacity:0}100%{transform:translateX(960px) skewX(-18deg);opacity:0}}
.cpf{animation:cpFlow 2.9s cubic-bezier(.4,0,.2,1) infinite}
.stp{animation:starPulse 2.2s ease-in-out infinite}
.swp{animation:swp 8.5s ease-in-out infinite}
"""
    defs = f"""
<radialGradient id="cpGlow" cx="0.82" cy="0.30" r="0.55">
  <stop offset="0" stop-color="{AMBER}" stop-opacity="0.065"/>
  <stop offset="0.6" stop-color="{EMERALD}" stop-opacity="0.03"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="swpG" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.03"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
"""
    eyebrow = (
        f'<rect x="38" y="28" width="242" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}"/>'
        f'<circle class="stp" cx="52" cy="40" r="3.2" fill="{AMBER}"/>'
        + txt("02 / MOST POPULAR · OPEN SOURCE", 62, 43.5, 9.0, MONO, INK, "600", spacing=0.6)
    )
    # Popularity telemetry pills next to eyebrow
    pop_badges = (
        f'<rect x="288" y="28" width="102" height="24" rx="12" fill="#17130B" stroke="{AMBER}" stroke-opacity="0.45"/>'
        + txt("★ 135 STARS", 339, 43.5, 9.2, MONO, AMBER, "700", anchor="middle", spacing=0.5)
        + f'<rect x="398" y="28" width="100" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}"/>'
        + txt("⑂ 750 FORKS", 448, 43.5, 9.2, MONO, INK, "700", anchor="middle", spacing=0.5)
    )

    title = path_text("career-pilot", FONT_HELV_BOLD, 42, 38, 102, tracking=-1.2, fill=INK)
    subtitle = txt("Full-stack AI career OS — resumes, mocks, jobs & portfolios in one app.", 40, 128, 13.5, SANS, INK_2, "400")

    # 6 Feature Pillars (2 columns x 3 rows)
    pillars = [
        ("01 RESUME STUDIO", "60+ templates, ATS scorer, AI tailoring"),
        ("02 INTERVIEW SIM", "Avatar A/V mocks + Monaco coding"),
        ("03 JOBS & TRACKER", "JSearch board, Kanban & outreach"),
        ("04 PORTFOLIO GEN", "29 themes, Netlify / CF deploy"),
        ("05 AI TOOLS", "Cover letters, skill-gap & trajectory"),
        ("06 GITHUB INTEL", "Repo analyzer, fellowships & payouts"),
    ]
    p_svg = []
    for idx, (ptitle, pdesc) in enumerate(pillars):
        col = idx % 2
        row = idx // 2
        px = 40 + col * 246
        py = 148 + row * 48
        p_svg.append(
            f'<rect x="{px}" y="{py}" width="236" height="40" rx="8" fill="{CARD_HI}" stroke="{BORDER}"/>'
            + txt(ptitle, px + 11, py + 15.5, 9.2, MONO, EMERALD if idx % 2 == 0 else INK, "700", spacing=0.7)
            + txt(pdesc, px + 11, py + 31, 10.6, SANS, INK_2, "400")
        )

    # Tech stack pills with real brand logos
    cp_tech = [
        ("react", "React 19"),
        ("express", "Express"),
        ("mongodb", "MongoDB"),
        ("redis", "Redis"),
        ("openai", "Multi-AI"),
        ("tailwindcss", "Tailwind"),
    ]
    tx = 40
    tpills = []
    for slug, lbl in cp_tech:
        ps, pw = icon_pill(tx, 304, slug, lbl, h=24, size=9.6, icon_sz=11, px=9)
        tpills.append(ps)
        tx += pw + 6

    cta = (
        txt("EXPLORE REPOSITORY", 40, 360, 10.5, MONO, INK, "700", spacing=1.1)
        + txt("↗", 190, 360, 13, SANS, AMBER, "700")
        + txt("github.com/anurag3407/career-pilot  ·  120+ contributors", 212, 360, 10.2, MONO, INK_3, "400")
    )

    # Right Column: Popularity + Multi-AI Pipeline Card
    rx, ry, rw, rh = 560, 28, 310, 334
    right_panel = [
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" rx="16" fill="#07070B" stroke="{BORDER_HI}"/>',
        # Big hero stats row
        f'<rect x="{rx+14}" y="{ry+14}" width="136" height="72" rx="10" fill="{CARD_HI}" stroke="{AMBER}" stroke-opacity="0.35"/>',
        path_text("135", FONT_HELV_BOLD, 30, rx + 26, ry + 54, tracking=-1.0, fill=INK),
        txt("★ GITHUB STARS", rx + 26, ry + 73, 8.8, MONO, AMBER, "700", spacing=0.6),
        f'<rect x="{rx+160}" y="{ry+14}" width="136" height="72" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>',
        path_text("750", FONT_HELV_BOLD, 30, rx + 172, ry + 54, tracking=-1.0, fill=INK),
        txt("⑂ COMMUNITY FORKS", rx + 172, ry + 73, 8.8, MONO, INK_2, "700", spacing=0.4),
        # Multi-AI header
        txt("MULTI-AI ENGINE · BYOK ROUTER", rx + 16, ry + 110, 9.2, MONO, INK_3, "700", spacing=0.9),
        f'<line x1="{rx+34}" y1="{ry+134}" x2="{rx+34}" y2="{ry+294}" stroke="{BORDER_HI}" stroke-width="1.4" stroke-dasharray="3 3"/>',
        ("" if preview else f'<circle class="cpf" cx="{rx+34}" cy="{ry+134}" r="3.2" fill="{EMERALD}"/>'),
    ]
    stages = [
        ("OPENAI · CLAUDE · GROQ", "provider pool", EMERALD),
        ("ATS SCORE · 94/100", "resume diff", AMBER),
        ("MOCK AVATAR · 14 LANGS", "monaco sandbox", ICE),
        ("PORTFOLIO · NETLIFY / CF", "1-click ship", INK),
    ]
    for i, (st_lbl, st_sub, scol) in enumerate(stages):
        sy = ry + 134 + i * 50
        right_panel.append(
            f'<circle cx="{rx+34}" cy="{sy}" r="4.5" fill="#0D0D13" stroke="{scol}" stroke-width="1.5"/>'
            f'<rect x="{rx+52}" y="{sy-16}" width="242" height="32" rx="8" fill="{CARD_HI}" stroke="{BORDER}"/>'
            + txt(st_lbl, rx + 64, sy + 3.5, 9.4, MONO, INK, "700", spacing=0.4)
            + txt(st_sub, rx + 282, sy + 3.5, 9.2, SANS, INK_3, "400", anchor="end")
        )

    inner = (
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.5"/>'
        f'<rect width="{W}" height="{H}" fill="url(#cpGlow)"/>'
        + ("" if preview else f'<rect class="swp" x="0" y="0" width="180" height="{H}" fill="url(#swpG)"/>')
        + eyebrow + pop_badges + title + subtitle
        + "".join(p_svg) + "".join(tpills) + cta + "".join(right_panel)
    )
    return card_shell(W, H, inner, defs=defs, css=css, rx=18, clip_id="cpClip", label="career-pilot project card")


# =============================================================================
# 5. PROJECT 03 — STORINARY (900 x 340) — Animated Media Pipeline & Features
# =============================================================================
def gen_storinary(preview=False):
    W, H = 900, 340
    css = "" if preview else """
@keyframes stPkt1{0%{transform:translateX(0);opacity:0}12%{opacity:1}88%{opacity:1}100%{transform:translateX(218px);opacity:0}}
@keyframes stPkt2{0%{transform:translateX(0);opacity:0}12%{opacity:1}88%{opacity:1}100%{transform:translateX(218px);opacity:0}}
@keyframes ringRot{to{transform:rotate(360deg)}}
@keyframes meterGlow{0%,100%{opacity:.95}50%{opacity:.55}}
.sp1{animation:stPkt1 2.4s cubic-bezier(.4,0,.2,1) infinite}
.sp2{animation:stPkt2 2.4s cubic-bezier(.4,0,.2,1) infinite 1.2s}
.rrot{transform-box:fill-box;transform-origin:center;animation:ringRot 9s linear infinite}
.mg{animation:meterGlow 2s ease-in-out infinite}
"""
    defs = f"""
<radialGradient id="stGlow" cx="0.80" cy="0.50" r="0.55">
  <stop offset="0" stop-color="{EMERALD}" stop-opacity="0.07"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</radialGradient>
"""
    eyebrow = (
        f'<rect x="38" y="28" width="268" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}"/>'
        f'<circle cx="52" cy="40" r="3" fill="{EMERALD}"/>'
        + txt("03 / SELF-HOSTED CLOUDINARY ALTERNATIVE", 62, 43.5, 9.0, MONO, INK, "600", spacing=0.7)
    )
    title = path_text("Storinary", FONT_HELV_BOLD, 42, 38, 102, tracking=-1.2, fill=INK)
    subtitle = txt("Own your images & video — upload, transform, and serve from your own bucket.", 40, 128, 13.5, SANS, INK_2, "400")

    features = [
        ("WASM AI", EMERALD, "Client-side background removal & WebP pre-compression ($0 server cost)."),
        ("TRANSFORMS", ICE, "On-the-fly resize, gravity crop, f_auto, q_auto & HMAC signed delivery."),
        ("VIDEO ENGINE", AMBER, "MP4/WebM streaming, FFmpeg auto-posters & 360p/720p renditions."),
        ("YOUR BUCKET", INK, "Backblaze B2, Supabase or Appwrite Storage · 646 tests passing."),
    ]
    fy = 148
    fsvg = []
    for tag, col, desc in features:
        fsvg.append(
            f'<rect x="40" y="{fy}" width="98" height="22" rx="6" fill="{WELL}" stroke="{BORDER}"/>'
            f'<circle cx="51" cy="{fy+11}" r="2.5" fill="{col}"/>'
            + txt(tag, 59, fy + 14.5, 8.6, MONO, INK, "700", spacing=0.3)
            + txt(desc, 146, fy + 14.5, 11.4, SANS, INK_2, "400")
        )
        fy += 31

    techs = [("nextdotjs", "Next.js 15"), ("typescript", "TypeScript"), ("prisma", "Prisma"), ("postgresql", "Postgres"), ("cloudflare", "Cloudflare")]
    tx = 40
    tpills = []
    for slug, lbl in techs:
        ps, pw = icon_pill(tx, 282, slug, lbl, h=23, size=9.4, icon_sz=11, px=8)
        tpills.append(ps)
        tx += pw + 6

    cta = (
        txt("VIEW STORINARY", 40, 323, 10.2, MONO, INK, "700", spacing=1.0)
        + txt("↗", 156, 323, 12.5, SANS, EMERALD, "700")
        + txt("github.com/anurag3407/storinary", 176, 323, 10.2, MONO, INK_3, "400")
    )

    # Right Column: Animated Media Transform Pipeline
    rx, ry, rw, rh = 560, 28, 310, 284
    pipe = [
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" rx="16" fill="#07070B" stroke="{BORDER_HI}"/>',
        f'<circle cx="{rx+18}" cy="{ry+22}" r="3" fill="{EMERALD}"/>',
        txt("EDGE TRANSFORM PIPELINE", rx + 29, ry + 25.5, 9.5, MONO, INK, "700", spacing=0.7),
        txt("646 TESTS OK", rx + rw - 16, ry + 25.5, 8.8, MONO, EMERALD, "700", anchor="end"),
        f'<line x1="{rx+14}" y1="{ry+40}" x2="{rx+rw-14}" y2="{ry+40}" stroke="{BORDER}"/>',

        # Horizontal trace line
        f'<line x1="{rx+48}" y1="{ry+104}" x2="{rx+264}" y2="{ry+104}" stroke="{BORDER_HI}" stroke-width="1.5" stroke-dasharray="3 3"/>',
        ("" if preview else f'<circle class="sp1" cx="{rx+48}" cy="{ry+104}" r="3.5" fill="{INK}"/>'),
        ("" if preview else f'<circle class="sp2" cx="{rx+48}" cy="{ry+104}" r="3.5" fill="{EMERALD}"/>'),

        # Node 1: Bucket
        f'<rect x="{rx+18}" y="{ry+74}" width="64" height="60" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>',
        txt("RAW", rx + 50, ry + 100, 10.5, MONO, INK, "700", anchor="middle"),
        txt("2.4 MB", rx + 50, ry + 118, 8.8, MONO, INK_3, "500", anchor="middle"),

        # Node 2: Spinning WASM / Sharp core
        f'<circle class="rrot" cx="{rx+155}" cy="{ry+104}" r="36" fill="none" stroke="{EMERALD}" stroke-width="1.5" stroke-dasharray="10 6"/>',
        f'<circle cx="{rx+155}" cy="{ry+104}" r="28" fill="{WELL}" stroke="{BORDER_HI}"/>',
        txt("WASM", rx + 155, ry + 101, 9.5, MONO, EMERALD, "700", anchor="middle"),
        txt("+ SHARP", rx + 155, ry + 114, 8.2, MONO, INK_2, "600", anchor="middle"),

        # Node 3: Edge CDN
        f'<rect x="{rx+228}" y="{ry+74}" width="64" height="60" rx="10" fill="{CARD_HI}" stroke="{EMERALD}" stroke-opacity="0.5"/>',
        txt("WEBP", rx + 260, ry + 100, 10.5, MONO, EMERALD, "700", anchor="middle"),
        txt("184 KB", rx + 260, ry + 118, 8.8, MONO, INK, "600", anchor="middle"),

        # Bottom live metrics box
        f'<rect x="{rx+18}" y="{ry+158}" width="{rw-36}" height="106" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>',
        txt("TRANSFORM TELEMETRY", rx + 30, ry + 178, 8.8, MONO, INK_3, "700", spacing=0.8),
        txt("-92% PAYLOAD", rx + rw - 30, ry + 178, 9.2, MONO, EMERALD, "700", anchor="end"),
        f'<rect x="{rx+30}" y="{ry+190}" width="{rw-60}" height="8" rx="4" fill="{WELL}"/>',
        f'<rect class="mg" x="{rx+30}" y="{ry+190}" width="212" height="8" rx="4" fill="{EMERALD}"/>',
        txt("✓  f_auto · q_auto · bg_remove (WASM)", rx + 30, ry + 219, 9.6, MONO, INK_2, "500"),
        txt("✓  HMAC signed · Immutable CDN cache", rx + 30, ry + 237, 9.6, MONO, INK_2, "500"),
        txt("✓  B2 / Supabase / Appwrite buckets", rx + 30, ry + 255, 9.6, MONO, INK_3, "500"),
    ]

    inner = (
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.5"/>'
        f'<rect width="{W}" height="{H}" fill="url(#stGlow)"/>'
        + eyebrow + title + subtitle + "".join(fsvg) + "".join(tpills) + cta + "".join(pipe)
    )
    return card_shell(W, H, inner, defs=defs, css=css, rx=18, clip_id="stClip", label="Storinary project card")


# =============================================================================
# 6. PROJECT 04 — GHOSTFOUNDER (900 x 340) — Animated 4-Module Hub & Features
# =============================================================================
def gen_ghostfounder(preview=False):
    W, H = 900, 340
    css = "" if preview else """
@keyframes gfScan{0%,100%{transform:translateX(0)}50%{transform:translateX(96px)}}
@keyframes gfWave1{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}
@keyframes gfWave2{0%,100%{transform:scaleY(.9)}50%{transform:scaleY(.3)}}
@keyframes gfPulse{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes gfSlide{0%{transform:translateX(0)}50%{transform:translateX(44px)}100%{transform:translateX(0)}}
.gfs{animation:gfScan 2.8s ease-in-out infinite}
.gfw1{transform-box:fill-box;transform-origin:bottom;animation:gfWave1 1.2s ease-in-out infinite}
.gfw2{transform-box:fill-box;transform-origin:bottom;animation:gfWave2 1.5s ease-in-out infinite}
.gfp{animation:gfPulse 1.9s ease-in-out infinite}
.gfsl{animation:gfSlide 3.2s ease-in-out infinite}
"""
    defs = f"""
<radialGradient id="gfGlow" cx="0.80" cy="0.50" r="0.55">
  <stop offset="0" stop-color="{INDIGO}" stop-opacity="0.08"/>
  <stop offset="1" stop-color="{VOID}" stop-opacity="0"/>
</radialGradient>
"""
    eyebrow = (
        f'<rect x="38" y="28" width="224" height="24" rx="12" fill="{WELL}" stroke="{BORDER_HI}"/>'
        f'<circle class="gfp" cx="52" cy="40" r="3" fill="{INDIGO}"/>'
        + txt("04 / AI + WEB3 STARTUP TOOLKIT", 62, 43.5, 9.0, MONO, INK, "600", spacing=0.8)
    )
    title = path_text("GhostFounder", FONT_HELV_BOLD, 42, 38, 102, tracking=-1.2, fill=INK)
    subtitle = txt("Build startups at warp speed — AI automation paired with on-chain equity.", 40, 128, 13.5, SANS, INK_2, "400")

    features = [
        ("CODE POLICE", EMERALD, "Automated webhook PR & commit reviews with severity reports."),
        ("PITCH STUDIO", INDIGO, "README-to-investor deck generator + visual slide canvas."),
        ("EQUITY CHAIN", AMBER, "Ethereum Sepolia ERC-20 cap table & MetaMask transfers."),
        ("DB AGENT", ICE, "AES-256 encrypted NL queries for Postgres, MySQL & Mongo."),
    ]
    fy = 148
    fsvg = []
    for tag, col, desc in features:
        fsvg.append(
            f'<rect x="40" y="{fy}" width="102" height="22" rx="6" fill="{WELL}" stroke="{BORDER}"/>'
            f'<circle cx="51" cy="{fy+11}" r="2.5" fill="{col}"/>'
            + txt(tag, 59, fy + 14.5, 8.6, MONO, INK, "700", spacing=0.3)
            + txt(desc, 150, fy + 14.5, 11.4, SANS, INK_2, "400")
        )
        fy += 31

    techs = [("nextdotjs", "Next.js 16"), ("langchain", "LangChain"), ("googlegemini", "Gemini"), ("solidity", "Solidity"), ("firebase", "Firebase")]
    tx = 40
    tpills = []
    for slug, lbl in techs:
        ps, pw = icon_pill(tx, 282, slug, lbl, h=23, size=9.4, icon_sz=11, px=8)
        tpills.append(ps)
        tx += pw + 6

    cta = (
        txt("VIEW GHOSTFOUNDER", 40, 323, 10.2, MONO, INK, "700", spacing=1.0)
        + txt("↗", 174, 323, 12.5, SANS, INDIGO, "700")
        + txt("github.com/anurag3407/ghosthunter", 194, 323, 10.2, MONO, INK_3, "400")
    )

    # Right Column: 4-Module Animated Command Hub
    rx, ry, rw, rh = 560, 28, 310, 284
    hub = [
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" rx="16" fill="#07070B" stroke="{BORDER_HI}"/>',
        f'<circle class="gfp" cx="{rx+18}" cy="{ry+22}" r="3" fill="{INDIGO}"/>',
        txt("FOUNDER COMMAND SUITE", rx + 29, ry + 25.5, 9.5, MONO, INK, "700", spacing=0.7),
        txt("4 MODULES", rx + rw - 16, ry + 25.5, 8.8, MONO, INDIGO, "700", anchor="end"),
        f'<line x1="{rx+14}" y1="{ry+40}" x2="{rx+rw-14}" y2="{ry+40}" stroke="{BORDER}"/>',
    ]

    # 2x2 animated sub-cards
    mx1, mx2 = rx + 16, rx + 160
    my1, my2 = ry + 54, ry + 166
    mw, mh = 134, 98

    # Q1: Code Police (diff laser scan)
    hub.append(
        f'<rect x="{mx1}" y="{my1}" width="{mw}" height="{mh}" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>'
        + txt("CODE POLICE", mx1 + 12, my1 + 20, 8.8, MONO, EMERALD, "700", spacing=0.6)
        + txt("PR diff scan", mx1 + 12, my1 + 35, 9.8, SANS, INK_3, "400")
        + f'<rect x="{mx1+12}" y="{my1+48}" width="84" height="5" rx="2.5" fill="{EMERALD}" opacity="0.75"/>'
        + f'<rect x="{mx1+12}" y="{my1+59}" width="58" height="5" rx="2.5" fill="{EMBER}" opacity="0.75"/>'
        + f'<rect x="{mx1+12}" y="{my1+70}" width="98" height="5" rx="2.5" fill="{BORDER_HI}"/>'
        + ("" if preview else f'<rect class="gfs" x="{mx1+12}" y="{my1+44}" width="2" height="36" rx="1" fill="{INK}" opacity="0.7"/>')
    )

    # Q2: Pitch Studio (animated deck progress)
    hub.append(
        f'<rect x="{mx2}" y="{my1}" width="{mw}" height="{mh}" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>'
        + txt("PITCH STUDIO", mx2 + 12, my1 + 20, 8.8, MONO, INDIGO, "700", spacing=0.6)
        + txt("README → Deck", mx2 + 12, my1 + 35, 9.8, SANS, INK_3, "400")
        + f'<rect x="{mx2+12}" y="{my1+48}" width="110" height="34" rx="5" fill="{WELL}" stroke="{BORDER_HI}"/>'
        + f'<rect x="{mx2+20}" y="{my1+56}" width="44" height="4" rx="2" fill="{INDIGO}"/>'
        + f'<rect class="gfsl" x="{mx2+20}" y="{my1+66}" width="38" height="4" rx="2" fill="{INK_2}" opacity="0.7"/>'
    )

    # Q3: Equity Chain (pulsing ERC-20 blocks)
    hub.append(
        f'<rect x="{mx1}" y="{my2}" width="{mw}" height="{mh}" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>'
        + txt("EQUITY CHAIN", mx1 + 12, my2 + 20, 8.8, MONO, AMBER, "700", spacing=0.6)
        + txt("Sepolia ERC-20", mx1 + 12, my2 + 35, 9.8, SANS, INK_3, "400")
        + f'<line x1="{mx1+30}" y1="{my2+64}" x2="{mx1+104}" y2="{my2+64}" stroke="{BORDER_HI}" stroke-width="1.2" stroke-dasharray="2 2"/>'
        + f'<rect x="{mx1+14}" y="{my2+52}" width="24" height="24" rx="5" fill="{WELL}" stroke="{AMBER}" stroke-opacity="0.6"/>'
        + f'<rect class="gfp" x="{mx1+55}" y="{my2+52}" width="24" height="24" rx="5" fill="{WELL}" stroke="{EMERALD}"/>'
        + f'<rect x="{mx1+96}" y="{my2+52}" width="24" height="24" rx="5" fill="{WELL}" stroke="{BORDER_HI}"/>'
    )

    # Q4: NL2SQL Agent (animated bars)
    bars_q4 = []
    for i, (bh, c, cl) in enumerate([(14, ICE, "gfw1"), (22, EMERALD, "gfw2"), (10, ICE, "gfw1"), (24, INK_2, "gfw2"), (16, ICE, "gfw1"), (20, EMERALD, "gfw2"), (12, ICE, "gfw1"), (18, INK_2, "gfw2")]):
        bx = mx2 + 16 + i * 13
        bars_q4.append(f'<rect class="{cl}" x="{bx}" y="{my2 + 80 - bh}" width="5" height="{bh}" rx="2.5" fill="{c}" opacity="0.85"/>')
    hub.append(
        f'<rect x="{mx2}" y="{my2}" width="{mw}" height="{mh}" rx="10" fill="{CARD_HI}" stroke="{BORDER}"/>'
        + txt("DB AGENT", mx2 + 12, my2 + 20, 8.8, MONO, ICE, "700", spacing=0.6)
        + txt("NL → SQL / NoSQL", mx2 + 12, my2 + 35, 9.8, SANS, INK_3, "400")
        + "".join(bars_q4)
    )

    inner = (
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.5"/>'
        f'<rect width="{W}" height="{H}" fill="url(#gfGlow)"/>'
        + eyebrow + title + subtitle + "".join(fsvg) + "".join(tpills) + cta + "".join(hub)
    )
    return card_shell(W, H, inner, defs=defs, css=css, rx=18, clip_id="gfClip", label="GhostFounder project card")


# =============================================================================
# 7. STACK & TELEMETRY (900 x 470) — ALL 36 Real Technologies with Exact Logos!
# =============================================================================
def gen_stack(preview=False):
    W, H = 900, 405
    css = "" if preview else """
@keyframes barSweep{0%{transform:translateX(-220px);opacity:0}20%{opacity:1}80%{opacity:1}100%{transform:translateX(860px);opacity:0}}
.bsw{animation:barSweep 4.8s ease-in-out infinite}
"""
    defs = f"""
<linearGradient id="bswGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.32"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<clipPath id="barClip"><rect x="38" y="394" width="824" height="14" rx="7"/></clipPath>
"""

    categories = [
        ("01 / LANGUAGES", [
            ("typescript", "TypeScript"), ("javascript", "JavaScript"), ("python", "Python"),
            ("openjdk", "Java"), ("cplusplus", "C++"), ("solidity", "Solidity"),
        ]),
        ("02 / FRONTEND & UI", [
            ("react", "React 19"), ("nextdotjs", "Next.js 16"), ("tailwindcss", "Tailwind CSS"),
            ("vite", "Vite"), ("framer", "Framer Motion"), ("playwright", "Playwright"),
        ]),
        ("03 / BACKEND & REAL-TIME", [
            ("nodedotjs", "Node.js"), ("express", "Express"), ("django", "Django"),
            ("socketdotio", "Socket.IO"), ("turborepo", "Turborepo"), ("pnpm", "pnpm"),
        ]),
        ("04 / DATA & STORAGE", [
            ("postgresql", "PostgreSQL"), ("mongodb", "MongoDB"), ("redis", "Redis"),
            ("prisma", "Prisma"), ("drizzle", "Drizzle ORM"), ("supabase", "Supabase"),
            ("firebase", "Firebase"), ("appwrite", "Appwrite"), ("mysql", "MySQL"),
        ]),
        ("05 / AI, AGENTS & WEB3", [
            ("anthropic", "Claude / MCP"), ("openai", "OpenAI"), ("googlegemini", "Gemini"),
            ("langchain", "LangChain"), ("ethereum", "Ethereum"),
        ]),
        ("06 / CLOUD, AUTH & INFRA", [
            ("docker", "Docker"), ("linux", "Linux"), ("git", "Git"),
            ("githubactions", "Actions"), ("cloudflare", "Cloudflare"),
            ("vercel", "Vercel"), ("railway", "Railway"), ("clerk", "Clerk"),
        ]),
    ]

    rows_svg = []
    ry = 30
    for cat_title, items in categories:
        rows_svg.append(txt(cat_title, 38, ry + 17, 9.5, MONO, INK_3, "700", spacing=1.1))
        ix = 212
        cy = ry
        for slug, lbl in items:
            ps, pw = icon_pill(ix, cy, slug, lbl, h=25, size=9.6, icon_sz=12, px=9)
            if ix + pw > W - 36:
                ix = 212
                cy += 31
                ps, pw = icon_pill(ix, cy, slug, lbl, h=25, size=9.6, icon_sz=12, px=9)
            rows_svg.append(ps)
            ix += pw + 7
        ry = cy + 36
        rows_svg.append(f'<line x1="38" y1="{ry-6}" x2="{W-38}" y2="{ry-6}" stroke="{BORDER}" stroke-width="0.8"/>')

    # Wait: compute exact total height or fit cleanly above y=370!
    # Let's check: 6 categories, only cat 4 (9 items) and cat 6 (8 items) wrap to 2 lines -> 8 lines * 31 + gaps.
    # Let's adjust spacing so it fits cleanly inside 900x470! Let's check exact bottom ry below.
    # Actually let's use exact dynamic layout calculation and return W, H cleanly, OR tighten padding slightly so ry ends around 358!
    rows_svg = []
    ry = 26
    for cat_title, items in categories:
        rows_svg.append(txt(cat_title, 38, ry + 16, 9.2, MONO, INK_3, "700", spacing=1.0))
        ix = 216
        cy = ry
        for slug, lbl in items:
            ps, pw = icon_pill(ix, cy, slug, lbl, h=24, size=9.4, icon_sz=11.5, px=8)
            if ix + pw > W - 36:
                ix = 216
                cy += 29
                ps, pw = icon_pill(ix, cy, slug, lbl, h=24, size=9.4, icon_sz=11.5, px=8)
            rows_svg.append(ps)
            ix += pw + 6
        ry = cy + 34
        rows_svg.append(f'<line x1="38" y1="{ry-5}" x2="{W-38}" y2="{ry-5}" stroke="{BORDER}" stroke-width="0.8"/>')

    # Language telemetry bar (anchored cleanly below last row)
    bar_y = ry + 16
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
        segs.append(f'<rect x="{cur_x:.1f}" y="{bar_y+14}" width="{sw:.1f}" height="14" fill="{color}"/>')
        cur_x += sw

    legend = []
    lx = 38
    for name, pct, color in langs:
        lbl = f"{name} {round(pct)}%"
        legend.append(
            f'<circle cx="{lx+4}" cy="{bar_y+46}" r="3.5" fill="{color}"/>'
            + txt(lbl, lx + 13, bar_y + 49.5, 10.2, MONO, INK_2, "500")
        )
        lx += len(lbl) * 6.3 + 34

    defs = f"""
<linearGradient id="bswGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.32"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<clipPath id="barClip"><rect x="38" y="{bar_y+14}" width="824" height="14" rx="7"/></clipPath>
"""

    bar_section = (
        txt("LANGUAGE DISTRIBUTION · 121 ORIGINAL REPOS", 38, bar_y, 9.8, MONO, INK_3, "700", spacing=1.1)
        + txt("GITHUB API TELEMETRY · 162 TOTAL", W - 38, bar_y, 9.2, MONO, EMERALD, "700", anchor="end", spacing=0.9)
        + f'<g clip-path="url(#barClip)">{"".join(segs)}'
        + ("" if preview else f'<rect class="bsw" x="38" y="{bar_y+14}" width="140" height="14" fill="url(#bswGrad)"/>')
        + f'</g>'
        + f'<rect x="38" y="{bar_y+14}" width="824" height="14" rx="7" fill="none" stroke="{BORDER_HI}" stroke-width="1"/>'
        + "".join(legend)
        + txt("typed > untyped", W - 38, bar_y + 49.5, 9.8, MONO, INK_3, "500", anchor="end")
    )

    inner = "".join(rows_svg) + bar_section
    return card_shell(W, H, inner, defs=defs, css=css, rx=18, clip_id="stClip", label="Full technology stack and telemetry")


# =============================================================================
# 8. REDESIGNED CONNECT SECTION (NO "open to internship")
# =============================================================================
def gen_connect_header(preview=False):
    W, H = 900, 146
    css = "" if preview else """
@keyframes orbFoot{to{transform:rotate(360deg)}}
@keyframes dotLive{0%,100%{opacity:1}50%{opacity:.35}}
.obf{transform-box:fill-box;transform-origin:center;animation:orbFoot 26s linear infinite}
.dlv{animation:dotLive 2.2s ease-in-out infinite}
"""
    inner = (
        f'<rect width="{W}" height="{H}" fill="url(#microGrid)" opacity="0.45"/>'
        + txt("04 / CONNECT", 40, 38, 9.8, MONO, INK_3, "700", spacing=1.3)
        + path_text("Let's build something sharp.", FONT_HELV_BOLD, 32, 38, 78, tracking=-0.9, fill=INK)
        + txt("Always down to talk multi-agent tooling, developer infrastructure, or open-source systems.", 40, 108, 13.5, SANS, INK_2, "400")
        + f'<g transform="translate(816,73)">'
        f'<circle class="obf" cx="0" cy="0" r="44" fill="none" stroke="{BORDER_HI}" stroke-width="1" stroke-dasharray="3 8"/>'
        f'<circle cx="0" cy="0" r="30" fill="{WELL}" stroke="{BORDER}"/>'
        + path_text("AM", FONT_SERIF_ITALIC, 22, 0, 8, anchor="middle", fill=INK)
        + f'</g>'
        + f'<circle class="dlv" cx="44" cy="127" r="2.8" fill="{EMERALD}"/>'
        + txt("NIT PATNA · CSE  ·  ANURAG3407", 54, 130.5, 9.5, MONO, INK_3, "600", spacing=0.9)
    )
    return card_shell(W, H, inner, css=css, rx=18, clip_id="cnClip", label="Connect with Anurag Mishra")


def gen_link_card(slug, title, handle, accent, is_mail=False):
    def _fn(preview=False):
        W, H = 216, 76
        css = "" if preview else """
@keyframes lkPulse{0%,100%{opacity:1}50%{opacity:.3}}
.lkp{animation:lkPulse 2.4s ease-in-out infinite}
"""
        if is_mail:
            icon_svg = (
                f'<g transform="translate(18 27)">'
                f'<rect x="0" y="2" width="18" height="14" rx="3" fill="none" stroke="{accent}" stroke-width="1.6"/>'
                f'<path d="M1 4l8 6 8-6" fill="none" stroke="{accent}" stroke-width="1.6" stroke-linecap="round"/>'
                f'</g>'
            )
        else:
            icon_svg = brand_icon(slug, 18, 27, size=18, fill_override=accent)

        inner = (
            f'<rect x="14" y="18" width="26" height="36" rx="8" fill="{WELL}" stroke="{BORDER}" opacity="0"/>'
            + icon_svg
            + txt(title, 48, 34, 10.5, MONO, INK, "700", spacing=0.8)
            + txt(handle, 48, 51, 9.8, MONO, INK_3, "500")
            + f'<circle class="lkp" cx="{W-20}" cy="22" r="2.5" fill="{accent}"/>'
            + txt("↗", W - 16, 54, 13, SANS, INK_2, "700", anchor="end")
        )
        return card_shell(W, H, inner, css=css, rx=14, clip_id=f"lk_{slug}", label=f"{title} link card")
    return _fn


def render_preview_png(svg_path, png_path, w, h):
    with open(svg_path) as f:
        svg = f.read()
    html_path = svg_path + ".tmp.html"
    with open(html_path, "w") as f:
        f.write(f"<!DOCTYPE html><html><body style='margin:0;padding:0;background:#010409'>{svg}</body></html>")
    try:
        subprocess.run([
            CHROME, "--headless", "--disable-gpu",
            f"--screenshot={png_path}", f"--window-size={w},{h}",
            "--virtual-time-budget=1200", "file://" + html_path,
        ], capture_output=True, check=True, timeout=30)
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    jobs = {
        "obsidian-hero.svg": (gen_hero, 900, 440),
        "obsidian-divider.svg": (gen_divider, 900, 24),
        "obsidian-project-sayabot.svg": (gen_sayabot, 900, 430),
        "obsidian-project-careerpilot.svg": (gen_careerpilot, 900, 390),
        "obsidian-project-storinary.svg": (gen_storinary, 900, 340),
        "obsidian-project-ghostfounder.svg": (gen_ghostfounder, 900, 340),
        "obsidian-stack.svg": (gen_stack, 900, 405),
        "obsidian-connect.svg": (gen_connect_header, 900, 146),
        "obsidian-link-github.svg": (gen_link_card("github", "GITHUB", "@anurag3407", INK), 216, 76),
        "obsidian-link-linkedin.svg": (gen_link_card("linkedin", "LINKEDIN", "/in/anurag3407", ICE), 216, 76),
        "obsidian-link-x.svg": (gen_link_card("x", "X / TWITTER", "@anurag3407", INK_2), 216, 76),
        "obsidian-link-email.svg": (gen_link_card("mail", "EMAIL", "anuragmishra3407", EMERALD, is_mail=True), 216, 76),
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
