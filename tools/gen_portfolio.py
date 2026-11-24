#!/usr/bin/env python3
"""
Scrapbook portfolio panels for the anurag3407 profile README.

Every panel is hand-composed SVG: paper, tape, taped photos, sticker chips,
ruler doodles, and display type converted to outlines so the layout is
pixel-identical on every platform. Only metric-safe fonts stay live text
(Courier New, Arial Narrow / Helvetica).

    python3 tools/gen_portfolio.py            # regenerate assets/
    python3 tools/gen_portfolio.py --preview  # + PNG renders via Chrome
"""
import argparse
import base64
import io
import os
import random
import subprocess
from functools import lru_cache

from PIL import Image, ImageFont
from fontTools.ttLib import TTFont, TTCollection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets")
PREVIEW = os.path.join(OUT, "preview")
PORTRAIT_SRC = os.path.join(OUT, "portrait.webp")
PORTRAIT_BOX = (0.1274, 0.0, 0.8070, 0.6589)
HEAD_BOX = (0.22, 0.0, 0.80, 0.40)

# ------------------------------------------------------------------ palette --
PAPER = "#F8F5EC"
PAPER_WARM = "#FBF7EA"
PAPER_COOL = "#F4F3EC"
INK = "#17150F"
INK_SOFT = "#3D3930"
MUTED = "#7A7465"
RULE = "#D9E2E7"
GRID = "#E2DED1"
TAPE = "#D8CDB2"
YELLOW = "#F4C842"
YELLOW_PALE = "#FBE7A2"
GREEN = "#3FA45B"
PINK = "#F49CB4"
BLUE = "#3E68DC"
RED = "#E1523D"
NAVY = "#141B2E"
CREAM = "#EFE8D6"

F_DISPLAY = ("supp/Rockwell.ttc", 2)          # Rockwell Bold
F_SERIF = ("supp/Didot.ttc", 2)               # Didot Bold
F_HAND = ("supp/Bradley Hand Bold.ttf", 0)
F_LABEL = "supp/Arial Narrow Bold.ttf"

SUPP = "/System/Library/Fonts/Supplemental/"

BODY = "'Courier New',Courier,monospace"
LABEL = "'Arial Narrow','Helvetica Neue',Arial,sans-serif"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# -------------------------------------------------------------------- fonts --
@lru_cache(maxsize=None)
def ttf(spec):
    name, idx = spec
    path = SUPP + name.split("/", 1)[1]
    return TTFont(path, fontNumber=idx)


@lru_cache(maxsize=None)
def pil_font(name, size):
    return ImageFont.truetype(SUPP + name, size)


@lru_cache(maxsize=None)
def glyphs(spec):
    font = ttf(spec)
    return font, font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm


def path_width(text, spec, size, tracking=0.0, sx=1.0):
    _, gs, cmap, upm = glyphs(spec)
    s = size / upm
    w = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        w += gs[gname].width * s + tracking
    if text:
        w -= tracking
    return w * sx


def path_text(text, spec, size, x, y, anchor="start", tracking=0.0,
              fill=INK, rot=0.0, sx=1.0, opacity=1.0, cls="", extra=""):
    """Display type as outlines: font-independent, kerning-free by design."""
    _, gs, cmap, upm = glyphs(spec)
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
    xunits = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        glyph = gs[gname]
        glyph.draw(TransformPen(pen, (1, 0, 0, 1, xunits, 0)))
        xunits += glyph.width + tracking / (size / upm)
    d = pen.getCommands()
    w = path_width(text, spec, size, tracking, sx)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    s = size / upm
    transform = f"translate({x:.1f} {y:.1f}) scale({s * sx:.4f} {-s:.4f})"
    if rot:
        cx, cy = x + w / 2, y - size * 0.35
        transform = f"rotate({rot} {cx:.1f} {cy:.1f}) " + transform
    cls_attr = f' class="{cls}"' if cls else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<path d="{d}" fill="{fill}" transform="{transform}"'
            f'{cls_attr}{op}{extra}/>')


def live(text, x, y, size=12, family=BODY, fill=INK, weight="normal",
         anchor="start", spacing=0.0, opacity=1.0, extra=""):
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}"{op}{extra}>'
            f'{esc(text)}</text>')


def label_width(text, size, spacing=0.0):
    f = pil_font("Arial Narrow Bold.ttf", round(size * 4))
    return f.getlength(text) / 4 + spacing * max(0, len(text) - 1)


def mono_width(text, size):
    return len(text) * size * 0.6


def sans_width(text, size, bold=False, spacing=0.0):
    f = pil_font("Arial Bold.ttf" if bold else "Arial.ttf", round(size * 4))
    return f.getlength(text) / 4 + spacing * max(0, len(text) - 1)


# -------------------------------------------------------------- svg surfaces --
def paper(w, h, kind="grid", tint=PAPER):
    defs = []
    body = [f'<rect width="{w}" height="{h}" fill="{tint}"/>']
    if kind == "grid":
        defs.append(
            '<pattern id="grid" width="16" height="16" patternUnits="userSpaceOnUse">'
            f'<path d="M16 0H0V16" fill="none" stroke="{GRID}" stroke-width=".7"/>'
            '</pattern>')
        body.append(f'<rect width="{w}" height="{h}" fill="url(#grid)" opacity=".85"/>')
    elif kind == "rule":
        defs.append(
            '<pattern id="rule" width="8" height="27" patternUnits="userSpaceOnUse">'
            f'<line x1="0" y1="26.5" x2="8" y2="26.5" stroke="{RULE}" stroke-width="1"/>'
            '</pattern>')
        body.append(f'<rect width="{w}" height="{h}" fill="url(#rule)"/>')
        body.append(f'<line x1="58" y1="0" x2="58" y2="{h}" stroke="#E7BDB4" stroke-width="1"/>')
    body.append(
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" fill="none" '
        'stroke="#DED8C8" stroke-width="1"/>')
    body.append(
        f'<rect width="{w}" height="{h}" fill="url(#vignette)" pointer-events="none"/>')
    return "".join(defs), "".join(body)


BASE_DEFS = f'''
<linearGradient id="vignette" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#B7A98A" stop-opacity=".10"/>
  <stop offset=".10" stop-color="#B7A98A" stop-opacity="0"/>
  <stop offset=".92" stop-color="#B7A98A" stop-opacity="0"/>
  <stop offset="1" stop-color="#B7A98A" stop-opacity=".14"/>
</linearGradient>
<filter id="sh" x="-30%" y="-30%" width="170%" height="170%">
  <feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#3B2E17" flood-opacity=".20"/>
</filter>
<filter id="sh-soft" x="-30%" y="-30%" width="170%" height="170%">
  <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#3B2E17" flood-opacity=".14"/>
</filter>
<filter id="rough" x="-8%" y="-8%" width="116%" height="116%">
  <feTurbulence type="fractalNoise" baseFrequency="0.052" numOctaves="2" seed="9" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="2.1" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="rough-hard" x="-10%" y="-10%" width="120%" height="120%">
  <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" seed="4" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="3.4" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="grain">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3"/>
  <feColorMatrix type="saturate" values="0"/>
  <feComponentTransfer><feFuncA type="linear" slope=".06"/></feComponentTransfer>
</filter>
'''

NAV_CSS = '''
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
'''


def svg_doc(w, h, body, defs="", css=""):
    style = f"<style>{css}</style>" if css else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">'
            f'{style}<defs>{BASE_DEFS}{defs}</defs>{body}</svg>')


def grain(w, h):
    return f'<rect width="{w}" height="{h}" filter="url(#grain)" opacity=".55"/>'


# ------------------------------------------------------------------- images --
def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def portrait_crop(box, size):
    """Crop the alpha cutout and lay it on the palette red like a studio backdrop."""
    im = Image.open(PORTRAIT_SRC).convert("RGBA")
    w, h = im.size
    px = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
    crop = im.crop(px)
    bg = Image.new("RGBA", crop.size, hex_rgb(RED) + (255,))
    return Image.alpha_composite(bg, crop).convert("RGB").resize(size, Image.LANCZOS)


@lru_cache(maxsize=None)
def photo_uri(kind):
    if kind == "portrait":
        im = portrait_crop(PORTRAIT_BOX, (400, 540))
        q = 86
    else:  # head
        im = portrait_crop(HEAD_BOX, (500, 480))
        q = 88
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- components --
def tape(cx, cy, w, h, rot=0, opacity=0.8, tint=TAPE):
    seed = int(cx + cy + w) % 97
    rnd = random.Random(seed)
    jitter = [rnd.uniform(-1.2, 1.2) for _ in range(4)]
    d = (f"M{3+jitter[0]:.1f},0.5 L{w-4+jitter[1]:.1f},1 "
         f"L{w-1},{h*0.35:.1f} L{w-2.5+jitter[2]:.1f},{h-0.5} "
         f"L{4+jitter[3]:.1f},{h-1:.1f} L0.5,{h*0.6:.1f} Z")
    return (f'<g transform="rotate({rot} {cx} {cy})" opacity="{opacity}">'
            f'<path d="{d}" transform="translate({cx-w/2} {cy-h/2})" fill="{tint}"/>'
            f'<path d="M{cx-w/2+6},{cy-h/2+h*0.28} H{cx+w/2-7}" stroke="#FFFDF4" '
            'stroke-width="1.6" opacity=".38"/></g>')


def chip(x, y, text, fill, fg=INK, rot=0, dot=None, size=10.5, pad=11, border=None):
    w = label_width(text, size, 0.9) + pad * 2 + (10 if dot else 0)
    h = 22
    cx, cy = x + w / 2, y + h / 2
    b = f'stroke="{border}" stroke-width="1"' if border else ""
    inner = ""
    if dot:
        inner += f'<circle cx="{x+pad+2.5}" cy="{cy}" r="3" fill="{fg}"/>'
    tx = x + pad + (9 if dot else 0)
    return (f'<g transform="rotate({rot} {cx} {cy})">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="{fill}" {b}/>'
            f'{inner}'
            f'{live(text, tx, cy + 3.6, size, LABEL, fg, "bold", spacing=0.9)}'
            f'</g>')


def sticky(x, y, w, h, rot=0, fill=YELLOW_PALE, ruled=False, fold=True):
    cx, cy = x + w / 2, y + h / 2
    lines = ""
    if ruled:
        step = 24
        yy = y + 30
        while yy < y + h - 12:
            lines += (f'<line x1="{x+10}" y1="{yy}" x2="{x+w-10}" y2="{yy}" '
                      'stroke="#C9B98A" stroke-width=".6" opacity=".55"/>')
            yy += step
    corner = ""
    if fold:
        corner = (f'<path d="M{x+w-26},{y+h} L{x+w},{y+h-26} L{x+w},{y+h} Z" '
                  f'fill="#000" opacity=".12"/>'
                  f'<path d="M{x+w-26},{y+h} L{x+w},{y+h-26} L{x+w-24},{y+h-24} Z" '
                  f'fill="#fff" opacity=".35"/>')
    shadow = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" filter="url(#sh)"/>'
    body = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
            f'{lines}{corner}'
            f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" fill="none" '
            'stroke="#000" stroke-opacity=".07"/>')
    return f'<g transform="rotate({rot} {cx} {cy})">{shadow}{body}</g>'


def photo_frame(x, y, w, h, rot=0, uri=None, border=10, caption=None,
                tape_corners=(-16, 8)):
    cx, cy = x + w / 2, y + h / 2
    uri = uri or photo_uri("portrait")
    cap = ""
    if caption:
        cap = (f'{path_text(caption, F_HAND, 15, x + w / 2, y + h + 22, "middle", fill=INK_SOFT)}')
    t1 = tape(x + 18, y + 4, 62, 17, tape_corners[0], 0.72)
    t2 = tape(x + w - 20, y + h - 10, 58, 16, tape_corners[1], 0.72)
    return (f'<g transform="rotate({rot} {cx} {cy})">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFDF6" filter="url(#sh)"/>'
            f'<image href="{uri}" x="{x+border}" y="{y+border}" '
            f'width="{w-border*2}" height="{h-border*2}" preserveAspectRatio="xMidYMid slice"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" '
            'stroke-opacity=".10"/>'
            f'{t1}{t2}{cap}</g>')


def avatar(cx, cy, r, rot=-4, uri=None):
    uri = uri or photo_uri("head")
    t = tape(cx - 6, cy - r + 2, 48, 14, -8, 0.7)
    return (f'<g transform="rotate({rot} {cx} {cy})">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFDF6" filter="url(#sh)"/>'
            f'<clipPath id="av{int(cx)}_{int(cy)}"><circle cx="{cx}" cy="{cy}" r="{r-6}"/></clipPath>'
            f'<image href="{uri}" x="{cx-r+6}" y="{cy-r+6}" width="{(r-6)*2}" '
            f'height="{(r-6)*2}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#av{int(cx)}_{int(cy)})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#FFFDF6" stroke-width="5"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#000" stroke-opacity=".22" stroke-width="1"/>'
            f'{t}</g>')


def arrowhead(x, y, ang, color=INK, size=8, width=2.0):
    import math
    a1 = math.radians(ang + 150)
    a2 = math.radians(ang - 150)
    return (f'<path d="M{x:.1f},{y:.1f} L{x+size*math.cos(a1):.1f},{y+size*math.sin(a1):.1f} '
            f'M{x:.1f},{y:.1f} L{x+size*math.cos(a2):.1f},{y+size*math.sin(a2):.1f}" '
            f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')


def curved_arrow(d, color=INK, width=1.9, head_ang=0, head_at=None, dash=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    g = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
         f'stroke-linecap="round"{dash_attr}/>')
    if head_at:
        g += arrowhead(head_at[0], head_at[1], head_ang, color, 8, width)
    return g


def star(cx, cy, r, color=INK, rot=0, width=1.6):
    import math
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.24
        a = math.radians(rot - 90 + i * 45)
        pts.append(f"{cx+rr*math.cos(a):.1f},{cy+rr*math.sin(a):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linejoin="round"/>')


def scribble(x1, y1, x2, y2, color=RED, width=2.4, amp=2.2):
    n = max(3, int(abs(x2 - x1) / 26))
    import math
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t + math.sin(i * 2.1) * amp
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round"/>')


def sidebar_dots(x, y, gap=13):
    return (f'<circle cx="{x}" cy="{y}" r="4.6" fill="{YELLOW}" stroke="#000" stroke-opacity=".25"/>'
            f'<circle cx="{x+gap}" cy="{y}" r="4.6" fill="{GREEN}" stroke="#000" stroke-opacity=".25"/>'
            f'<circle cx="{x+gap*2}" cy="{y}" r="4.6" fill="{RED}" stroke="#000" stroke-opacity=".25"/>')


def nav_bar(y=22, x=22, w=836, active="home"):
    items = [("home", "HOME"), ("about", "ABOUT"), ("work", "WORK"), ("play", "PLAYGROUND")]
    right = "CONTACT"
    svg = [f'<rect x="{x}" y="{y}" width="{w}" height="40" rx="3" fill="{PAPER_WARM}" '
           'stroke="#1B1810" stroke-width="1.4" filter="url(#sh-soft)"/>',
           sidebar_dots(x + 18, y + 20)]
    ix = x + 92
    for key, text in items:
        wdt = label_width(text, 10.5, 1.5)
        col = INK if key == active else MUTED
        svg.append(f'<circle cx="{ix+3}" cy="{y+20}" r="2.6" fill="{RED if key==active else "#B4AD9C"}"/>')
        svg.append(live(text, ix + 12, y + 23.6, 10.5, LABEL, col, "bold", spacing=1.5))
        if key == active:
            svg.append(f'<line x1="{ix+12}" y1="{y+29}" x2="{ix+12+wdt}" y2="{y+29}" '
                       f'stroke="{RED}" stroke-width="1.4"/>')
        ix += 12 + wdt + 30
    rx = x + w - 26
    svg.append(f'<circle cx="{rx-24}" cy="{y+20}" r="2.6" fill="{BLUE}"/>'
               f'<circle cx="{rx-12}" cy="{y+20}" r="2.6" fill="{GREEN}"/>'
               f'<circle cx="{rx}" cy="{y+20}" r="2.6" fill="{YELLOW}"/>')
    svg.append(live(right, rx - 36, y + 23.6, 10.5, LABEL, INK, "bold",
                    anchor="end", spacing=1.5))
    return "".join(svg)


def section_tag(x, y, num, text, rot=-2, fill=INK, fg=CREAM):
    w = label_width(f"{num} — {text}", 10.5, 1.4) + 26
    return (f'<g transform="rotate({rot} {x+w/2} {y+11})">'
            f'{tape(x+w/2, y+10, w+22, 26, 0.6, 0.55)}'
            f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="2" fill="{fill}"/>'
            f'{live(f"{num} — {text}", x + 13, y + 14.6, 10.5, LABEL, fg, "bold", spacing=1.4)}'
            f'</g>')


def folio(n, total, w=880, h=640, x=None):
    return (f'{path_text(f"— {n:02d} / {total:02d}", F_HAND, 14, x if x is not None else w - 34, h - 22, "end", fill="#9A927F")}')


def browser(x, y, w, h, body_svg, title="career-pilot — app", chrome_fill="#EDE9DD"):
    bar = 26
    cid = f"bc{int(x)}_{int(y)}_{int(w)}_{int(h)}"
    return (f'<g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFDF6" filter="url(#sh)"/>'
            f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
            f'<g clip-path="url(#{cid})">'
            f'<g transform="translate({x} {y+bar})">{body_svg}</g>'
            f'</g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{bar}" fill="{chrome_fill}"/>'
            f'{sidebar_dots(x + 12, y + bar / 2, 10)}'
            f'<rect x="{x+58}" y="{y+7}" width="{w-120}" height="12" rx="6" fill="#FFFDF6" '
            'stroke="#000" stroke-opacity=".12"/>'
            f'{live(title, x + 64, y + 16.5, 8, BODY, MUTED, spacing=0.4)}'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" '
            'stroke-opacity=".16"/>'
            f'</g>')


def torn_button(x, y, text, fill=INK, fg=CREAM, w=None, h=38):
    w = w or label_width(text, 12, 1.8) + 34
    return (f'<g transform="rotate(-.6 {x+w/2} {y+h/2})">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{fill}" filter="url(#sh-soft)"/>'
            f'<rect x="{x+4}" y="{y+4}" width="{w-8}" height="{h-8}" fill="none" '
            'stroke="#FFFDF6" stroke-opacity=".18"/>'
            f'{live(text, x + w / 2, y + h / 2 + 4, 11.5, LABEL, fg, "bold", "middle", spacing=1.8)}'
            f'</g>')


# =================================================================== 01 HERO ==
def hero():
    W, H = 880, 640
    defs, bg = paper(W, H, "grid", PAPER)
    body = [bg, grain(W, H)]

    # top strip: identity + availability, no fake navigation
    body.append(f'<g transform="rotate(-1.8 130 52)">'
                f'{tape(130, 52, 214, 28, -1, .6)}'
                f'{live("ANU.3407 — PORTFOLIO ’26", 130, 56, 9.2, LABEL, INK, "bold", "middle", spacing=1.4)}'
                f'</g>')
    body.append(f'<g transform="rotate(2.4 742 54)">'
                f'{tape(742, 54, 202, 28, 1, .7, YELLOW_PALE)}'
                f'{live("open to 2027 internships", 742, 58, 10.5, LABEL, INK, "bold", "middle", spacing=.7)}'
                f'</g>')

    # name plate
    name = "ANURAG"
    size = 104
    nw = path_width(name, F_DISPLAY, size, tracking=-2.5, sx=0.95)
    plate_w = nw + 96
    plate_x = 440 - plate_w / 2
    plate_y = 116
    plate_h = 122
    body.append(
        f'<g transform="rotate(-2.1 440 177)">'
        f'<rect x="{plate_x}" y="{plate_y}" width="{plate_w}" height="{plate_h}" '
        'fill="#FFFDF4" filter="url(#sh-soft)"/>'
        f'<rect x="{plate_x+5}" y="{plate_y+5}" width="{plate_w-10}" height="{plate_h-10}" '
        'fill="none" stroke="#000" stroke-opacity=".10" stroke-dasharray="3 3"/>'
        f'{path_text(name, F_DISPLAY, size, 440, plate_y + 94, "middle", tracking=-2.5, sx=0.95, extra=" filter=\'url(#rough)\'")}'
        f'</g>')
    body.append(tape(plate_x + 6, plate_y + 6, 84, 26, -19, 0.75))
    body.append(tape(plate_x + plate_w - 8, plate_y + plate_h - 8, 88, 25, 14, 0.75))

    # name label + the name tag
    tw = label_width("name label", 9, 1.6) + 20
    body.append(f'<g transform="rotate(-7 320 96)">'
                f'<rect x="{320-tw/2}" y="86" width="{tw}" height="20" rx="10" fill="{INK}"/>'
                f'{live("name label", 320, 99.5, 9, LABEL, CREAM, "bold", "middle", spacing=1.6)}'
                f'</g>')
    tw2 = label_width("the name", 9, 1.4) + 18
    body.append(f'<g transform="rotate(6 632 250)">'
                f'<rect x="{632-tw2/2}" y="240" width="{tw2}" height="19" rx="2" fill="{RED}"/>'
                f'{live("the name", 632, 253, 9, LABEL, "#FFF6EC", "bold", "middle", spacing=1.4)}'
                f'</g>')

    # sticker chips
    body.append(chip(56, 128, "OPEN SOURCE", GREEN, "#FFFDF4", -5.5, dot="#FFFDF4"))
    body.append(chip(46, 186, "full-stack dev", CREAM, INK, 3.5, border="#00000022"))
    body.append(chip(716, 116, "what the hell?", YELLOW, INK, 4.5))
    body.append(chip(722, 170, "my work is", PAPER_WARM, INK, -3, border="#00000026"))
    body.append(chip(708, 224, "ships weekly", BLUE, "#FFFDF4", 6, dot="#FFFDF4"))

    # headline
    hl1 = "I build tools that do the work"
    hl2 = "so you don't have to."
    w2 = sans_width(hl2, 36, bold=True, spacing=-0.4)
    body.append(f'<rect x="{440-w2/2-9:.1f}" y="340" width="{w2+18:.1f}" '
                f'height="39" fill="{YELLOW}" opacity=".42" transform="rotate(-.8 440 360)"/>')
    body.append(live(hl1, 440, 324, 33, SANS, INK, "normal", "middle", spacing=-0.2))
    body.append(live(hl2, 440, 372, 36, SANS, INK, "bold", "middle", spacing=-0.4))
    body.append(star(728, 332, 13, RED, 12, 2.0))
    body.append(star(744, 360, 7, INK, 0, 1.4))

    body.append(live("A SPACE TO SHOW WHAT I SHIP & HOW I THINK", 440, 405,
                     11, LABEL, MUTED, "bold", "middle", spacing=3.0))


    # avatar + sticky
    body.append(avatar(122, 516, 52, -4))
    body.append(path_text("hi, that's me", F_HAND, 16, 122, 594, "middle", fill=INK_SOFT, rot=-3))

    body.append(sticky(652, 448, 188, 124, 3.2, YELLOW_PALE, ruled=True))
    body.append(path_text("currently:", F_HAND, 17, 668, 476, fill=INK))
    body.append(path_text("DSA in Java", F_HAND, 15, 668, 500, fill=INK_SOFT))
    body.append(path_text("OSS reviews", F_HAND, 15, 668, 523, fill=INK_SOFT))
    body.append(path_text("shipping side quests", F_HAND, 15, 668, 546, fill=INK_SOFT))

    # doodles
    body.append(curved_arrow("M528,443 C 560,470 470,492 300,498 C 240,500 200,485 180,470",
                             INK, 1.7, 205, (181, 471), dash="5 6"))
    body.append(path_text("scroll for the good stuff", F_HAND, 14, 300, 476, fill=INK_SOFT, rot=-2))

    body.append(folio(1, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ================================================================= 02 WHATSUP ==
def whatsup():
    W, H = 880, 560
    defs, bg = paper(W, H, "rule", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 30, "02", "WHAT'S UP"))

    # sticky note with the bio
    body.append(sticky(62, 96, 468, 268, -1.4, "#FCF3D0"))
    body.append(path_text("what's up", F_HAND, 24, 86, 128, fill=INK, rot=-1))
    bio = [
        "Full-stack dev, third-year CSE at NIT Patna.",
        "I like taking messy problems apart and",
        "rebuilding them into something obvious —",
        "the edge cases everyone forgets, the 40ms",
        "that shouldn't be there, the deploy that",
        "finally goes green. Break first, build",
        "second, ship until it feels easy.",
    ]
    y = 164
    for line in bio:
        body.append(live(line, 86, y, 14.2, BODY, INK_SOFT, spacing=0.1))
        y += 25.5
    body.append(scribble(86, 323, 370, 322, RED, 1.6, 1.2))

    # chips
    chips = [
        ("FULL-STACK", YELLOW, INK, -3),
        ("AI TOOLS", GREEN, "#FFFDF4", 2),
        ("OPEN SOURCE", BLUE, "#FFFDF4", -1.5),
        ("EDGE CASES", PINK, INK, 3),
        ("SHIPS WEEKLY", CREAM, INK, -2),
    ]
    cx = 66
    for text, fill, fg, rot in chips:
        body.append(chip(cx, 392, text, fill, fg, rot, size=10))
        cx += label_width(text, 10, 0.9) + 34

    # portrait + info card
    body.append(photo_frame(612, 84, 208, 274, 3.6, caption=None, tape_corners=(-12, 10)))
    body.append(path_text("me, allegedly", F_HAND, 16, 716, 388, "middle", fill=INK_SOFT, rot=3))

    body.append(f'<g transform="rotate(-1 715 451)">'
                f'<rect x="590" y="420" width="250" height="62" fill="#FFFDF6" filter="url(#sh-soft)"/>'
                f'<rect x="590" y="420" width="250" height="62" fill="none" stroke="#000" stroke-opacity=".10"/>'
                f'<rect x="590" y="420" width="4" height="62" fill="{RED}"/>'
                f'{tape(600, 421, 54, 15, -7, .62)}'
                f'{live("BASED  Patna, IN  ·  B.Tech CSE ’28", 608, 442, 10.2, LABEL, INK, "bold", spacing=.2)}'
                f'{live("NOW  DSA + OSS  ·  OPEN internships", 608, 462, 10.2, LABEL, MUTED, "bold", spacing=.2)}'
                f'</g>')
    body.append(path_text("patna · 2026", F_HAND, 13, 66, 486, fill="#8E8674", rot=-1))
    body.append(path_text("— anurag", F_HAND, 26, 66, 522, fill=INK_SOFT, rot=-2))
    body.append(star(214, 498, 9, RED, 10, 1.6))
    body.append(folio(2, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ==================================================================== 03 ABOUT ==
def about():
    W, H = 880, 640
    defs, bg = paper(W, H, "rule", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 28, "03", "ABOUT"))

    body.append(path_text("ABOUT", F_DISPLAY, 78, 40, 136, tracking=-1.0, sx=.9,
                          extra=" filter='url(#rough)'"))
    body.append(scribble(44, 150, 244, 148, RED, 2.4, 2.0))

    # story card
    body.append(sticky(44, 166, 520, 314, -0.7, "#FCF3D0"))
    body.append(path_text("hello, i'm anurag.", F_HAND, 20, 66, 204, fill=INK, rot=-.5))

    paras = [
        ["I build software because I keep finding",
         "small, annoying edges — and I like",
         "smoothing them out. That turned into",
         "full-stack products, open source, and a",
         "habit of shipping sooner than is safe."],
        ["Third-year CSE at NIT Patna. Most of my",
         "work sits where AI meets real workflows:",
         "resumes, repo reviews, documents, search."],
        ["Break first, build second. The edge cases",
         "are the fun part."],
    ]
    y = 236
    for para in paras:
        for line in para:
            body.append(live(line, 66, y, 13.0, BODY, INK_SOFT, spacing=.1))
            y += 21
        y += 11
    body.append(scribble(66, 433, 66 + mono_width("Break first, build second.", 13), 432, RED, 1.5, 1.1))
    body.append(star(524, 452, 8, RED, 9, 1.5))

    # portrait
    body.append(photo_frame(636, 108, 208, 274, 3.4, caption=None, tape_corners=(-13, 9)))
    body.append(path_text("the face behind the commits", F_HAND, 15, 740, 410, "middle",
                          fill=INK_SOFT, rot=2.5))
    body.append(star(612, 126, 7, INK, 0, 1.3))

    # quick answers
    body.append(live("QUICK ANSWERS", 44, 502, 8.4, LABEL, MUTED, "bold", spacing=1.6))
    qa = [
        ("WHAT'S THE GOAL?", ["tools people keep."], -1.4),
        ("CURRENT OBSESSION?", ["the 40ms that", "shouldn't be there."], 1.2),
        ("WHAT'S NEXT?", ["2027 internship,", "more open source."], -1.0),
    ]
    for i, (q, ans, rot) in enumerate(qa):
        x = 44 + i * 272
        y0 = 514
        body.append(f'<g transform="rotate({rot} {x+122} {y0+42})">'
                    f'<rect x="{x}" y="{y0}" width="244" height="86" fill="#FFFDF6" filter="url(#sh-soft)"/>'
                    f'<rect x="{x}" y="{y0}" width="244" height="86" fill="none" stroke="#000" stroke-opacity=".10"/>'
                    f'{tape(x + 24, y0 + 2, 58, 15, -6, .55)}'
                    f'{live(q, x + 14, y0 + 24, 7.6, LABEL, RED, "bold", spacing=1.2)}'
                    + "".join(path_text(line, F_HAND, 17, x + 14, y0 + 50 + j * 21, fill=INK)
                              for j, line in enumerate(ans)) +
                    f'</g>')
    body.append(folio(3, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ==================================================================== MOCKS ==
def mock_careerpilot(x, y, w, h):
    b = ['<rect width="792" height="286" fill="#0D1422"/>',
         '<rect width="148" height="286" fill="#0A101C"/>',
         f'<rect x="16" y="16" width="11" height="11" rx="2" fill="{YELLOW}"/>',
         live("career.pilot", 33, 26, 10.5, BODY, "#EDE7D6", "bold", spacing=-.3)]
    nav = ["Overview", "Resume", "Interviews", "Applications", "Portfolio"]
    for i, item in enumerate(nav):
        yy = 62 + i * 24
        if i == 0:
            b.append(f'<rect x="10" y="{yy-12}" width="128" height="20" rx="3" fill="#18233A"/>')
            b.append(f'<rect x="16" y="{yy-6}" width="4" height="8" rx="1" fill="{YELLOW}"/>')
        b.append(live(item, 28, yy, 7.5, BODY, "#F0EAD9" if i == 0 else "#7C879C"))
    b += ['<circle cx="24" cy="256" r="8" fill="#2A3550"/>',
          live("Anurag", 38, 254, 7, BODY, "#D8D2C2"),
          live("free plan", 38, 264, 5.6, BODY, "#69748A")]
    b += [live("Good evening, Anurag", 176, 44, 16, BODY, "#F2ECDC", "bold", spacing=-.4),
          live("3 applications need a nudge today — one interview at 4pm.", 176, 60, 7.2, BODY, "#7F8AA0"),
          '<circle cx="742" cy="42" r="10" fill="#27314A"/>',
          live("Oct 26", 724, 30, 5.6, BODY, "#7F8AA0", anchor="end")]
    # resume score card
    b += [f'<rect x="176" y="78" width="360" height="126" rx="5" fill="#16203A"/>',
          live("RESUME SCORE", 194, 98, 6.4, BODY, "#7FCFA0", "bold", spacing=1.2),
          live("92", 194, 158, 44, BODY, "#F6F0DF", "bold", spacing=-2),
          live("/100", 262, 158, 9, BODY, "#7F8AA0"),
          live("+8 this week", 194, 178, 6.4, BODY, "#7FCFA0"),
          '<circle cx="470" cy="140" r="35" fill="none" stroke="#27324C" stroke-width="8"/>',
          f'<circle cx="470" cy="140" r="35" fill="none" stroke="{GREEN}" stroke-width="8" '
          'stroke-dasharray="202 220" stroke-linecap="round" transform="rotate(-90 470 140)"/>',
          live("top 4%", 470, 144, 7, BODY, "#F2ECDC", anchor="middle"),
          live("ATS keywords", 320, 122, 6.2, BODY, "#7F8AA0"),
          '<rect x="320" y="128" width="96" height="4" rx="2" fill="#27324C"/>',
          f'<rect x="320" y="128" width="90" height="4" rx="2" fill="{YELLOW}"/>',
          live("impact verbs", 320, 150, 6.2, BODY, "#7F8AA0"),
          '<rect x="320" y="156" width="96" height="4" rx="2" fill="#27324C"/>',
          f'<rect x="320" y="156" width="80" height="4" rx="2" fill="{BLUE}"/>']
    # next up
    b += [f'<rect x="552" y="78" width="216" height="126" rx="5" fill="#16203A"/>',
          live("NEXT UP", 568, 98, 6.4, BODY, "#E8C64B", "bold", spacing=1.2),
          live("Mock interview", 568, 120, 10.5, BODY, "#F2ECDC", "bold"),
          live("System design · 20 min", 568, 136, 6.6, BODY, "#7F8AA0"),
          f'<rect x="568" y="154" width="184" height="24" rx="3" fill="#E8C64B"/>',
          live("Start session  →", 576, 169, 7, BODY, "#16130C", "bold")]
    # pipeline
    b += [live("APPLICATIONS", 176, 228, 6.4, BODY, "#7F8AA0", "bold", spacing=1.2)]
    cols = [("APPLIED", "12", YELLOW), ("INTERVIEW", "3", BLUE), ("OFFER", "1", GREEN)]
    for i, (name, n, col) in enumerate(cols):
        xx = 176 + i * 200
        b += [f'<rect x="{xx}" y="238" width="186" height="32" rx="3" fill="#16203A"/>',
              f'<rect x="{xx+10}" y="248" width="4" height="12" fill="{col}"/>',
              live(name, xx + 22, 252, 5.6, BODY, "#7F8AA0", "bold", spacing=.8),
              live(n, xx + 170, 258, 10, BODY, "#F2ECDC", "bold", anchor="end")]
    return (f'<g transform="translate({x} {y}) scale({w/792:.4f} {h/286:.4f})">'
            + "".join(b) + '</g>')


def mock_ghostfounder(x, y, w, h):
    card, line = "#141A26", "#232C3D"
    b = ['<rect width="396" height="216" fill="#0A0E15"/>',
         '<rect width="396" height="24" fill="#0C1119"/>',
         '<rect y="23" width="396" height="1" fill="#1B2434"/>',
         '<rect x="12" y="8" width="8" height="8" rx="1.5" fill="#E8C64B"/>',
         live("ghostfounder", 24, 15, 6.2, BODY, "#F0EAD9", "bold", spacing=-.2),
         '<rect x="108" y="6" width="174" height="12" rx="6" fill="#141A26" stroke="#232C3D"/>',
         live("Ask your data, or jump to...", 116, 14, 4.4, BODY, "#65708A"),
         '<rect x="292" y="6" width="92" height="12" rx="2" fill="#E8C64B"/>',
         live("NEW DECK", 338, 14, 4.2, BODY, "#07120B", "bold", anchor="middle", spacing=.6),
         # sidebar
         '<rect x="0" y="24" width="92" height="192" fill="#0A101C"/>',
         live("WORKSPACE", 12, 38, 4.0, BODY, "#4B566B", "bold", spacing=.8),
         '<rect x="6" y="46" width="80" height="15" rx="2" fill="#18233A"/>',
         '<rect x="8" y="51" width="2.5" height="5" fill="#E8C64B"/>',
         live("Overview", 16, 56, 5.2, BODY, "#F0EAD9"),
         live("Code Police", 16, 72, 5.2, BODY, "#8B96AC"),
         f'<circle cx="76" cy="69" r="4" fill="{RED}"/>',
         live("3", 76, 70.4, 4.2, BODY, "#FFFDF4", "bold", "middle"),
         live("Pitch Deck", 16, 88, 5.2, BODY, "#8B96AC"),
         live("Equity", 16, 104, 5.2, BODY, "#8B96AC"),
         live("Database", 16, 120, 5.2, BODY, "#8B96AC"),
         live("REPO", 12, 150, 4.0, BODY, "#4B566B", "bold", spacing=.8),
         '<rect x="8" y="156" width="76" height="22" fill="#101724" stroke="#1B2434"/>',
         live("ghosthunter", 14, 166, 4.6, BODY, "#D8D2C2"),
         '<circle cx="15" cy="173" r="1.6" fill="#6FD3A0"/>',
         live("connected", 20, 174, 3.8, BODY, "#6FD3A0"),
         live("86 commits · 3 weeks", 12, 200, 4.0, BODY, "#4B566B"),
         # heading
         live("Good evening, Anurag", 104, 44, 9.6, BODY, "#F2ECDC", "bold", spacing=-.3),
         live("Your startup, in one place.", 104, 55, 4.8, BODY, "#7F8AA0"),
         # code police
         f'<rect x="104" y="64" width="170" height="100" rx="3" fill="{card}" stroke="{line}"/>',
         live("CODE POLICE", 114, 78, 4.6, BODY, "#6FD3A0", "bold", spacing=1.0),
         live("3 issues", 114, 96, 12, BODY, "#F2ECDC", "bold", spacing=-.4),
         live("flagged on main", 114, 106, 4.4, BODY, "#7F8AA0"),
         f'<circle cx="244" cy="96" r="18" fill="none" stroke="{line}" stroke-width="3.4"/>',
         f'<circle cx="244" cy="96" r="18" fill="none" stroke="#6FD3A0" stroke-width="3.4" '
         'stroke-dasharray="93 20" stroke-linecap="round" transform="rotate(-90 244 96)"/>',
         live("82", 244, 98, 8, BODY, "#F2ECDC", "bold", "middle"),
         live("score", 244, 106, 3.4, BODY, "#65708A", "middle"),
         '<rect x="114" y="118" width="32" height="11" rx="2" fill="#3A1A1E"/>',
         live("2 HIGH", 130, 125.4, 3.8, BODY, "#F08A7E", "bold", "middle", spacing=.4),
         '<rect x="150" y="118" width="30" height="11" rx="2" fill="#3A3218"/>',
         live("1 MED", 165, 125.4, 3.8, BODY, "#E8C64B", "bold", "middle", spacing=.4),
         f'<circle cx="117" cy="141" r="2" fill="{RED}"/>',
         live("auth/session.ts", 123, 143, 4.4, BODY, "#AEB8C9"),
         f'<circle cx="117" cy="153" r="2" fill="#E8C64B"/>',
         live("api/upload.ts", 123, 155, 4.4, BODY, "#AEB8C9"),
         # pitch deck
         f'<rect x="282" y="64" width="102" height="46" rx="3" fill="{card}" stroke="{line}"/>',
         live("PITCH DECK", 292, 77, 4.4, BODY, "#E8C64B", "bold", spacing=.8),
         live("10 / 12", 292, 92, 9.2, BODY, "#F2ECDC", "bold", spacing=-.3),
         live("seed deck", 292, 102, 4.0, BODY, "#7F8AA0"),
         f'<rect x="338" y="88" width="36" height="3.4" rx="1.7" fill="{line}"/>',
         '<rect x="338" y="88" width="30" height="3.4" rx="1.7" fill="#E8C64B"/>',
         # equity
         f'<rect x="282" y="116" width="102" height="48" rx="3" fill="{card}" stroke="{line}"/>',
         live("EQUITY", 292, 129, 4.4, BODY, "#4C7DF0", "bold", spacing=.8),
         f'<circle cx="304" cy="146" r="11" fill="none" stroke="{line}" stroke-width="4"/>',
         '<circle cx="304" cy="146" r="11" fill="none" stroke="#E8C64B" stroke-width="4" '
         'stroke-dasharray="31 38" transform="rotate(-90 304 146)"/>',
         '<circle cx="304" cy="146" r="11" fill="none" stroke="#6FD3A0" stroke-width="4" '
         'stroke-dasharray="17 52" stroke-dashoffset="-31" transform="rotate(-90 304 146)"/>',
         '<circle cx="304" cy="146" r="11" fill="none" stroke="#4C7DF0" stroke-width="4" '
         'stroke-dasharray="9 60" stroke-dashoffset="-48" transform="rotate(-90 304 146)"/>',
         live("3 holders", 322, 142, 4.6, BODY, "#DCE2EE"),
         live("on-chain", 322, 152, 4.0, BODY, "#E8C64B"),
         # database agent
         f'<rect x="104" y="170" width="280" height="36" rx="3" fill="{card}" stroke="{line}"/>',
         live("DATABASE AGENT", 114, 182, 4.4, BODY, "#4C7DF0", "bold", spacing=.9),
         live("read-only", 374, 182, 3.8, BODY, "#6FD3A0", anchor="end"),
         live("> which users signed up this week?", 114, 196, 4.4, BODY, "#A8E6A1")]
    return (f'<g transform="translate({x} {y}) scale({w/396:.4f} {h/216:.4f})">'
            + "".join(b) + '</g>')


def mock_codepolice(x, y, w, h):
    b = ['<rect width="360" height="200" fill="#F6F0E0"/>',
         '<rect width="360" height="20" fill="#EBE3CE"/>',
         sidebar_dots(10, 10, 8),
         live("PR #42 · fix/auth-guard", 46, 13, 5.6, BODY, "#5E584A"),
         live("diff", 10, 36, 5, BODY, "#8A8372", spacing=.6)]
    diff = [("+", "if (!session.verify(token)) {", "#DFF0DA"),
            ("-", "  return next();", "#F6D9D2"),
            ("+", "  throw new AuthError(401);", "#DFF0DA"),
            ("+", "}", "#DFF0DA"),
            (" ", "", "#F0EBDD"),
            ("+", "// rate limit: 60 req / min", "#DFF0DA"),
            ("+", "await limiter.enforce(req.ip);", "#DFF0DA"),
            (" ", "", "#F0EBDD"),
            (" ", "// TODO: rotate refresh tokens", "#F0EBDD")]
    for i, (sign, txt, bg) in enumerate(diff):
        yy = 44 + i * 13
        b += [f'<rect x="8" y="{yy-8}" width="228" height="12" fill="{bg}"/>',
              live(sign, 12, yy + 1, 5, BODY, "#7A7364"),
              live(txt, 20, yy + 1, 5, BODY, "#3A352B")]
    b += ['<rect x="244" y="38" width="106" height="118" rx="3" fill="#FFFDF6" stroke="#D8CFB6"/>',
          f'<circle cx="256" cy="50" r="5" fill="{RED}"/>',
          live("code_police", 266, 52, 5.6, BODY, "#2B261C", "bold"),
          live("2 blocking issues", 254, 70, 5.2, BODY, "#C23B2B", "bold"),
          live("· missing auth test", 254, 82, 4.8, BODY, "#6B6455"),
          live("· token never expires", 254, 92, 4.8, BODY, "#6B6455"),
          live("14 checks passed", 254, 106, 4.8, BODY, "#4F7C4A"),
          live("1 suggestion", 254, 116, 4.8, BODY, "#6B6455"),
          f'<rect x="254" y="128" width="86" height="16" rx="2" fill="{INK}"/>',
          live("view patch  →", 262, 139, 5, BODY, "#F6F0E0", "bold"),
          live("guard: on", 254, 174, 5, BODY, "#8A8372", spacing=.6)]
    return (f'<g transform="translate({x} {y}) scale({w/360:.4f} {h/200:.4f})">'
            + "".join(b) + '</g>')


def mock_rag(x, y, w, h):
    b = ['<rect width="360" height="190" fill="#FFFDF6"/>',
         '<rect width="360" height="20" fill="#F2ECDD"/>',
         '<circle cx="14" cy="10" r="4" fill="#4C7DF0"/>',
         live("chat-with-pdf", 22, 13, 5.6, BODY, "#2E2A20", "bold"),
         '<rect x="120" y="5" width="100" height="10" rx="5" fill="#E7DFCB"/>',
         live("paper.pdf · 34 pages", 170, 13, 4.4, BODY, "#6B6455", anchor="middle")]
    b += ['<rect x="196" y="28" width="150" height="20" rx="4" fill="#E4E9F8"/>',
          live("summarise section 4", 206, 41, 5, BODY, "#2E3A55"),
          '<rect x="12" y="56" width="198" height="76" rx="4" fill="#F4EFE2"/>',
          live("Section 4 argues the retrieval", 20, 70, 4.8, BODY, "#4A4437"),
          live("budget, not model size, is what", 20, 80, 4.8, BODY, "#4A4437"),
          live("caps latency at 200ms. [1][2]", 20, 90, 4.8, BODY, "#4A4437"),
          live("[1] §4.2   [2] fig. 7   [3] p.12", 20, 104, 4.4, BODY, "#4C7DF0"),
          live("grounded in 3 sources", 20, 120, 4.4, BODY, "#8A8372"),
          '<rect x="12" y="140" width="100" height="18" rx="3" fill="#E7DFCB"/>',
          live("paper.pdf", 20, 152, 4.4, BODY, "#5E584A"),
          '<rect x="118" y="140" width="80" height="18" rx="3" fill="#E7DFCB"/>',
          live("figures.pdf", 126, 152, 4.4, BODY, "#5E584A"),
          '<rect x="12" y="166" width="336" height="14" rx="7" fill="#F1EADB"/>',
          live("ask anything about the doc", 22, 176, 4.6, BODY, "#8A8372"),
          f'<circle cx="338" cy="173" r="5" fill="{INK}"/>']
    return (f'<g transform="translate({x} {y}) scale({w/360:.4f} {h/190:.4f})">'
            + "".join(b) + '</g>')


def badge(cx, cy, r, big, small, fill=YELLOW, rot=-7, fg=INK):
    return (f'<g transform="rotate({rot} {cx} {cy})">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFDF6" filter="url(#sh-soft)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r-3}" fill="{fill}"/>'
            f'{live(big, cx, cy + 3, 12, LABEL, fg, "bold", "middle", spacing=.6)}'
            f'{live(small, cx, cy + 12, 5.8, LABEL, fg, "bold", "middle", spacing=1)}'
            f'</g>')


def work_card(x, y, w, h, rot, date, title, desc, tags, mock, index,
              mock_h=190, sticker=None, fill="#FFFDF6"):
    pad = 16
    mh = mock_h
    b = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" filter="url(#sh)"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" stroke-opacity=".10"/>',
         tape(x + w * .1, y + 2, 72, 17, -8, .62),
         f'<rect x="{x+pad}" y="{y+22}" width="5" height="5" fill="{RED}"/>',
         live(date, x + pad + 11, y + 27, 8.2, LABEL, MUTED, "bold", spacing=1.1),
         live(index, x + w - pad, y + 31, 12, LABEL, "#B9B19D", "bold", anchor="end", spacing=1)]
    b.append(f'<rect x="{x+pad}" y="{y+40}" width="{w-2*pad}" height="{mh}" fill="#0E1420"/>')
    b.append(mock(x + pad, y + 40, w - 2 * pad, mh))
    b.append(f'<rect x="{x+pad}" y="{y+40}" width="{w-2*pad}" height="{mh}" fill="none" stroke="#000" stroke-opacity=".2"/>')
    ty = y + 40 + mh + 42
    b.append(path_text(title, F_SERIF, 31, x + pad, ty, fill=INK, sx=.97))
    b.append(live(desc[0], x + pad, ty + 18, 9.4, BODY, "#4F4A3D"))
    b.append(live(desc[1], x + pad, ty + 31, 9.4, BODY, "#4F4A3D"))
    b.append(live(tags, x + pad, y + h - 14, 8, LABEL, MUTED, "bold", spacing=1.3))
    b.append(live("↗", x + w - pad, y + h - 12, 15, SANS, INK, anchor="end"))
    if sticker:
        b.append(badge(x + w - 44, y + 64, 27, sticker[0], sticker[1], sticker[2]))
    return f'<g transform="rotate({rot} {x+w/2} {y+h/2})">' + "".join(b) + '</g>'


# ================================================================== 03 WORKS ==
def feature_card(x, y, w, h, rot, date, title, desc, tags, art, index, fill,
                 ink, soft, tape_tint=TAPE, sticker=None):
    b = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" filter="url(#sh)"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" stroke-opacity=".18"/>',
         tape(x + 46, y + 2, 76, 17, -7, .6, tape_tint),
         f'<rect x="{x+18}" y="{y+22}" width="5" height="5" fill="{RED}"/>',
         live(date, x + 30, y + 27, 8.2, LABEL, soft, "bold", spacing=1.1),
         path_text(index, F_DISPLAY, 40, x + w - 18, y + 52, "end", fill=soft, extra=" opacity='.32'"),
         path_text(title, F_SERIF, 35, x + 18, y + 98, fill=ink, sx=.98),
         live(desc[0], x + 18, y + 118, 9.6, BODY, soft),
         live(desc[1], x + 18, y + 132, 9.6, BODY, soft),
         f'<rect x="{x+18}" y="{y+150}" width="{w-36}" height="218" fill="#FFFDF6" filter="url(#sh-soft)"/>',
         art(x + 18, y + 150, w - 36, 218),
         f'<rect x="{x+18}" y="{y+150}" width="{w-36}" height="218" fill="none" stroke="#000" stroke-opacity=".14"/>',
         live(tags, x + 18, y + h - 20, 8, LABEL, soft, "bold", spacing=1.3)]
    if sticker:
        b.append(badge(x + w - 38, y + 176, 29, sticker[0], sticker[1], sticker[2],
                       sticker[3] if len(sticker) > 3 else -8,
                       sticker[4] if len(sticker) > 4 else INK))
    return f'<g transform="rotate({rot} {x+w/2} {y+h/2})">' + "".join(b) + '</g>'


def works():
    W, H = 880, 680
    defs, bg = paper(W, H, "grid", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 30, "04", "FEATURED WORKS"))
    body.append(path_text("FEATURED", F_DISPLAY, 66, 42, 121, tracking=-1.2, sx=.9,
                          extra=" filter='url(#rough)'"))
    body.append(path_text("WORKS", F_DISPLAY, 66, 42, 185, tracking=-1.2, sx=.9,
                          extra=" filter='url(#rough)'"))
    body.append(scribble(44, 199, 292, 197, RED, 2.2, 2.0))
    body.append(path_text("the two I'd show first", F_HAND, 18, 646, 106, fill=INK_SOFT, rot=-3))
    body.append(curved_arrow("M632,122 C 600,140 540,178 494,206", INK, 1.5, 55, (496, 207), dash="5 6"))
    body.append(tape(646, 132, 128, 24, 3, .6))
    body.append(live("BUILT IN PUBLIC", 710, 148, 8.6, LABEL, INK, "bold", "middle", spacing=1.6))

    def career_art(ax, ay, aw, ah):
        return (f'{browser(ax + 10, ay + 10, aw - 20, ah - 20, mock_careerpilot(0, 0, aw - 20, ah - 46), "career-pilot — dashboard", "#1A2233")}'
                f'{tape(ax + 34, ay + 6, 58, 14, -6, .55)}')

    def ghost_art(ax, ay, aw, ah):
        return (f'<rect x="{ax+10}" y="{ay+10}" width="{aw-20}" height="{ah-20}" fill="#0F141D"/>'
                f'{mock_ghostfounder(ax + 10, ay + 10, aw - 20, ah - 20)}'
                f'{tape(ax + aw - 84, ay + 6, 58, 14, 7, .55)}')

    body.append(feature_card(40, 216, 396, 418, -1.1, "APR 2026 — ONGOING", "career-pilot",
                             ["Open-source AI career platform.", "Resume · interviews · job tracking."],
                             "AI  ·  REACT  ·  NODE  ·  MONGO", career_art, "01",
                             NAVY, CREAM, "#93A0BA", "#C9BFA6", ("136 ★", "STARS", YELLOW, -8)))
    body.append(feature_card(448, 228, 392, 406, 1.2, "DEC 2025 — JAN 2026", "GhostFounder",
                             ["An AI startup OS — code,", "decks, equity and data."],
                             "NEXT.JS  ·  FIREBASE  ·  LANGCHAIN  ·  WEB3", ghost_art, "02",
                             YELLOW, INK, "#4B3E12", TAPE, ("4", "TOOLS", BLUE, 8, "#FFFDF4")))
    body.append(path_text("hand-built · no template", F_HAND, 14, 44, 654, fill="#9A927F", rot=-1))
    body.append(folio(4, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ============================================================== 04 CASE STUDY ==
def case_study():
    W, H = 880, 704
    defs, bg = paper(W, H, "rule", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 28, "04", "CASE STUDY"))

    body.append(f'<rect x="70" y="82" width="6" height="6" fill="{RED}"/>')
    body.append(live("APR 2026 → NOW", 84, 89, 9, LABEL, MUTED, "bold", spacing=1.4))
    body.append(path_text("career-pilot", F_SERIF, 54, 68, 148, sx=.98))
    body.append(live("The AI co-pilot your career wish it had.", 70, 174, 13, BODY, INK_SOFT))

    # meta card
    body.append(sticky(596, 74, 238, 112, 1.2, "#FFFDF6"))
    body.append(path_text("THE FILE", F_DISPLAY, 8.5, 612, 96, tracking=1.6, fill=RED))
    meta = [("ROLE", "creator + maintainer"),
            ("STACK", "React · Node/Express · Mongo"),
            ("STATUS", "300+ contributors, shipping")]
    yy = 114
    for k, v in meta:
        body.append(live(k, 612, yy, 6.4, LABEL, MUTED, "bold", spacing=1.1))
        body.append(live(v, 660, yy, 8.4, BODY, INK))
        yy += 21

    # product shot
    body.append(browser(70, 206, 766, 286,
                        mock_careerpilot(0, 0, 766, 260),
                        "career-pilot — dashboard", "#1A2233"))
    body.append(tape(130, 202, 84, 20, -5, .55))

    # metric tiles
    tiles = [("136", "STARS ON GITHUB", "#CFE0FF", BLUE, -1.5),
             ("752", "FORKS (YES, REALLY)", YELLOW_PALE, INK, 1.0),
             ("300+", "CONTRIBUTORS", "#F9CFDC", INK, -1.0)]
    for i, (num, label, fill, fg, rot) in enumerate(tiles):
        x = 70 + i * 260
        body.append(f'<g transform="rotate({rot} {x+126} 560)">'
                    f'<rect x="{x}" y="518" width="252" height="84" fill="{fill}" filter="url(#sh-soft)"/>'
                    f'<rect x="{x}" y="518" width="252" height="84" fill="none" stroke="#000" stroke-opacity=".08"/>'
                    f'{live(num, x + 16, 566, 34, SANS, fg, "bold", spacing=-1.2)}'
                    f'{live(label, x + 16, 586, 8, LABEL, INK_SOFT, "bold", spacing=1.3)}'
                    f'</g>')
    # feature chips + cta
    features = ["RESUME OPTIMIZER", "MOCK INTERVIEWS", "JOB TRACKER", "PORTFOLIO BUILDER",
                "DISCORD COMMUNITY"]
    fxx = 70
    for text in features:
        body.append(chip(fxx, 635, text, CREAM, INK, -1.2, size=8.6, pad=9, border="#00000022"))
        fxx += label_width(text, 8.6, .9) + 18 + 14
    body.append(torn_button(654, 632, "VIEW ON GITHUB  ↗", INK, CREAM, w=182, h=36))
    body.append(folio(4, 8, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ============================================================= 05 PROJECT 01 ==
def project_career():
    W, H = 880, 760
    defs = ('<pattern id="navdots" width="18" height="18" patternUnits="userSpaceOnUse">'
            '<circle cx="1.1" cy="1.1" r=".9" fill="#28334C"/></pattern>'
            '<radialGradient id="pglow" cx=".76" cy=".14" r=".66">'
            '<stop offset="0" stop-color="#24365C"/><stop offset="1" stop-color="#24365C" stop-opacity="0"/>'
            '</radialGradient>')
    body = [f'<rect width="{W}" height="{H}" fill="{NAVY}"/>',
            f'<rect width="{W}" height="{H}" fill="url(#pglow)"/>',
            f'<rect width="{W}" height="{H}" fill="url(#navdots)" opacity=".85"/>']

    body.append(section_tag(40, 24, "05", "PROJECT 01", fill=CREAM, fg=INK))
    body.append(live("CASE FILE — 3407", 836, 42, 8.2, LABEL, "#8FA0BE", "bold", "end", spacing=1.5))
    body.append(f'<rect x="842" y="36" width="5" height="5" fill="{YELLOW}"/>')

    body.append(f'<rect x="42" y="80" width="5" height="5" fill="{RED}"/>')
    body.append(live("APR 2026 — NOW", 54, 86, 9, LABEL, "#B9C4D8", "bold", spacing=1.4))
    body.append(path_text("career-pilot", F_SERIF, 72, 38, 172, fill=CREAM, sx=.98))
    body.append(scribble(46, 190, 420, 187, YELLOW, 3.0, 2.4))
    body.append(live("An AI career OS, built in public.", 42, 210, 13.2, BODY, "#AEB9CE"))

    # meta card
    meta_rows = [("ROLE", "creator + maintainer"),
                 ("STACK", "React · Node · Mongo"),
                 ("STATE", "open source, MIT")]
    body.append(f'<g transform="rotate(-1 182 284)">'
                f'<rect x="40" y="232" width="288" height="104" fill="{CREAM}" filter="url(#sh)"/>'
                f'<rect x="40" y="232" width="288" height="104" fill="none" stroke="#000" stroke-opacity=".22"/>'
                f'<rect x="40" y="232" width="4" height="104" fill="{RED}"/>'
                f'{tape(122, 230, 62, 15, -7, .55)}'
                f'{path_text("THE FILE", F_DISPLAY, 8.2, 58, 256, tracking=1.5, fill=RED)}')
    yy = 278
    for k, v in meta_rows:
        body.append(live(k, 58, yy, 6.6, LABEL, MUTED, "bold", spacing=1.1))
        body.append(live(v, 114, yy, 8.4, BODY, INK))
        yy += 21
    body.append('</g>')

    # product shot: cream offset print, bleeding off the right
    body.append(f'<g transform="rotate(2.0 660 260)">'
                f'<rect x="460" y="104" width="472" height="330" fill="{YELLOW}"/>'
                f'<rect x="448" y="92" width="472" height="330" fill="{CREAM}" filter="url(#sh)"/>'
                f'{browser(460, 104, 448, 306, mock_careerpilot(0, 0, 448, 280), "career-pilot — dashboard", "#F3EAD0")}'
                f'{tape(482, 98, 72, 17, -7, .6)}'
                f'</g>')
    body.append(badge(792, 112, 36, "136", "STARS", YELLOW, -8))
    body.append(star(330, 120, 9, YELLOW, 10, 1.7))
    body.append(star(812, 438, 8, CREAM, 0, 1.4))

    # floating status note
    body.append(f'<g transform="rotate(-4 330 424)">'
                f'<rect x="250" y="390" width="158" height="66" fill="#FFFDF6" filter="url(#sh-soft)"/>'
                f'{tape(268, 392, 44, 13, -6, .6)}'
                f'{path_text("still shipping", F_HAND, 17, 264, 422, fill=INK)}'
                f'{live("apr → now  ·  public", 264, 442, 7.6, BODY, MUTED)}'
                f'</g>')

    # paper receipts band
    body.append(f'<g transform="rotate(-.6 440 600)">'
                f'<rect x="34" y="474" width="812" height="248" fill="{PAPER_WARM}" filter="url(#sh)"/>'
                f'<rect x="34" y="474" width="812" height="248" fill="none" stroke="#000" stroke-opacity=".12"/>'
                f'{tape(74, 470, 88, 18, -6, .5)}'
                f'{tape(788, 470, 80, 18, 7, .5)}'
                f'{live("THE RECEIPTS", 58, 506, 8.4, LABEL, RED, "bold", spacing=1.7)}'
                f'{live("OCT 2026", 836, 506, 7.6, LABEL, MUTED, "bold", "end", spacing=1.4)}')
    stats = [("136", "STARS ON GITHUB", BLUE, 58),
             ("752", "FORKS — YES, REALLY", INK, 322),
             ("300+", "CONTRIBUTORS", RED, 586)]
    for num, label, col, x in stats:
        body.append(live(num, x, 566, 44, SANS, col, "bold", spacing=-1.6))
        body.append(live(label, x + 2, 586, 8, LABEL, MUTED, "bold", spacing=1.3))
    body.append(f'<line x1="58" y1="606" x2="824" y2="605" stroke="#000" stroke-opacity=".14" stroke-dasharray="4 5"/>')
    body.append(live("INSIDE", 58, 636, 7.8, LABEL, MUTED, "bold", spacing=1.5))
    features = ["RESUME OPTIMIZER", "MOCK INTERVIEWS", "JOB TRACKER", "PORTFOLIO BUILDER",
                "DISCORD COMMUNITY"]
    fxx = 112
    for text in features:
        body.append(chip(fxx, 620, text, CREAM, INK, -1.0, size=8.4, pad=9, border="#00000022"))
        fxx += label_width(text, 8.4, .9) + 18 + 13
    body.append(path_text("300+ people, one repo. still shipping.", F_HAND, 18, 58, 690,
                          fill=INK_SOFT, rot=-.6))
    body.append(star(782, 668, 9, RED, 10, 1.6))
    body.append('</g>')

    body.append(f'<path d="M40,748 H840" stroke="#3A455C" stroke-width="1"/>')
    body.append(path_text("— 05 / 09", F_HAND, 14, 838, 744, "end", fill="#8FA0BE"))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ============================================================= 06 PROJECT 02 ==
def project_ghost():
    W, H = 880, 700
    defs, bg = paper(W, H, "grid", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 26, "06", "PROJECT 02"))
    body.append(f'<rect x="42" y="84" width="5" height="5" fill="{RED}"/>')
    body.append(live("DEC 2025 — JAN 2026", 54, 90, 9, LABEL, MUTED, "bold", spacing=1.4))
    body.append(path_text("GhostFounder", F_SERIF, 64, 38, 168, sx=.98))
    body.append(scribble(44, 182, 438, 180, RED, 2.4, 2.0))
    body.append(live("Code, decks, equity and data — one tab.", 42, 204, 13.2, BODY, INK_SOFT))

    # founder dashboard
    body.append(f'<g transform="rotate(-1 300 390)">'
                f'<rect x="32" y="226" width="540" height="336" fill="#FFFDF6" filter="url(#sh)"/>'
                f'{browser(44, 238, 516, 312, mock_ghostfounder(0, 0, 516, 286), "ghostfounder — dashboard", "#151B26")}'
                f'{tape(74, 232, 70, 16, -7, .58)}'
                f'</g>')
    body.append(badge(786, 168, 38, "4", "TOOLS", BLUE, 8, "#FFFDF4"))

    # pitch deck card
    body.append(f'<g transform="rotate(1.2 718 310)">'
                f'<rect x="598" y="228" width="238" height="164" fill="#FFFDF6" filter="url(#sh-soft)"/>'
                f'<rect x="598" y="228" width="238" height="164" fill="none" stroke="#000" stroke-opacity=".12"/>'
                f'<rect x="598" y="228" width="4" height="164" fill="{RED}"/>'
                f'{path_text("PITCH DECK STUDIO", F_DISPLAY, 8.6, 614, 252, tracking=1.2, fill=RED)}'
                f'{live("SOURCE", 614, 276, 6.2, LABEL, MUTED, "bold", spacing=1.2)}'
                f'{live("README.md", 682, 276, 8.2, BODY, INK)}'
                f'{live("TEMPLATE", 614, 296, 6.2, LABEL, MUTED, "bold", spacing=1.2)}'
                f'{live("Seed · 12 slides", 682, 296, 8.2, BODY, INK)}'
                f'{live("STATUS", 614, 316, 6.2, LABEL, MUTED, "bold", spacing=1.2)}'
                f'{live("draft · 10 / 12", 682, 316, 8.2, BODY, INK)}'
                f'<rect x="614" y="326" width="208" height="5" fill="#E9E3D3"/>'
                f'<rect x="614" y="326" width="173" height="5" fill="{YELLOW}"/>'
                f'{live("GAP ANALYSIS", 614, 352, 6.2, LABEL, MUTED, "bold", spacing=1.2)}'
                f'{live("2 slides missing", 682, 352, 8.2, BODY, "#B4462E")}'
                f'{live("PDF / PNG export ready", 614, 376, 7.4, BODY, MUTED)}'
                f'</g>')

    # code police log
    body.append(f'<g transform="rotate(-1 718 480)">'
                f'<rect x="598" y="414" width="238" height="132" rx="2" fill="#141A24" filter="url(#sh)"/>'
                f'{sidebar_dots(612, 428, 9)}'
                f'{live("code police · webhook", 660, 431, 5.2, BODY, "#65708A")}'
                f'{live("> push · main · 3 commits", 612, 456, 8.2, BODY, "#A8E6A1")}'
                f'{live("✓ scan complete · 1.2s", 612, 474, 8.2, BODY, "#8FA0BE")}'
                f'{live("! 2 high · 1 medium", 612, 492, 8.2, BODY, "#F08A7E")}'
                f'{live("-> report emailed", 612, 510, 8.2, BODY, "#8FA0BE")}'
                f'{live("_", 612, 530, 9, BODY, "#A8E6A1")}'
                f'</g>')

    # notes and process
    body.append(path_text("86 commits. three weeks.", F_HAND, 18, 404, 594, fill=INK_SOFT, rot=-2))
    body.append(star(374, 612, 8, RED, 8, 1.5))

    body.append(live("01  REVIEW", 42, 632, 8.4, LABEL, RED, "bold", spacing=1.4))
    body.append(live("CODE POLICE", 116, 632, 8.4, LABEL, INK, "bold", spacing=1.0))
    body.append(live("02  PITCH", 356, 632, 8.4, LABEL, RED, "bold", spacing=1.4))
    body.append(live("README → DECK", 416, 632, 8.4, LABEL, INK, "bold", spacing=1.0))
    body.append(live("03  SPLIT", 682, 632, 8.4, LABEL, RED, "bold", spacing=1.4))
    body.append(live("ON-CHAIN EQUITY", 742, 632, 8.4, LABEL, INK, "bold", spacing=1.0))
    body.append(f'<line x1="40" y1="648" x2="840" y2="647" stroke="#000" stroke-opacity=".16" stroke-dasharray="4 5"/>')
    body.append(path_text("next.js · firebase · langchain · solidity.", F_HAND, 16, 42, 678,
                          fill=INK_SOFT, rot=-1))
    body.append(folio(6, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# =============================================================== 05 MORE WORK ==
def more_work():
    W, H = 880, 560
    defs, bg = paper(W, H, "grid", "#F4F1E6")
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 30, "05", "ALSO SHIPPED"))

    # navy card
    x, y, w, h = 40, 92, 392, 368
    body.append(f'<g transform="rotate(-1.2 {x+w/2} {y+h/2})">'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NAVY}" filter="url(#sh)"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" stroke-opacity=".3"/>'
                f'{tape(x+50, y+2, 70, 17, -7, .5, "#C9BFA6")}'
                f'{live("PROJECT 06", x+18, y+30, 8, LABEL, "#8C97AD", "bold", spacing=1.5)}'
                f'{path_text("code_police", F_SERIF, 37, x+18, y+74, fill="#F3EDDD")}'
                f'{live("An AI agent that guards your repos", x+18, y+96, 9.4, BODY, "#AEB8CC")}'
                f'{live("and flags bad pushes before they land.", x+18, y+110, 9.4, BODY, "#AEB8CC")}'
                f'{mock_codepolice(x+16, y+128, w-32, 200)}'
                f'{live("AI  ·  TYPESCRIPT  ·  CI", x+18, y+h-16, 8, LABEL, "#8C97AD", "bold", spacing=1.3)}'
                f'{live("↗", x+w-18, y+h-14, 15, SANS, "#F3EDDD", anchor="end")}'
                f'</g>')

    # yellow card
    x, y, w, h = 448, 106, 392, 356
    body.append(f'<g transform="rotate(1.1 {x+w/2} {y+h/2})">'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#F6C945" filter="url(#sh)"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#000" stroke-opacity=".12"/>'
                f'{tape(x+w-120, y+2, 74, 17, 8, .55)}'
                f'{live("PROJECT 07", x+18, y+30, 8, LABEL, "#6B5512", "bold", spacing=1.5)}'
                f'{path_text("chat-with-pdf", F_SERIF, 37, x+18, y+74, fill=INK)}'
                f'{live("Interrogate any document in plain", x+18, y+96, 9.4, BODY, "#4A3D14")}'
                f'{live("language. Answers with receipts.", x+18, y+110, 9.4, BODY, "#4A3D14")}'
                f'{mock_rag(x+16, y+128, w-32, 190)}'
                f'{live("RAG  ·  NEXT.JS  ·  LLM", x+18, y+h-16, 8, LABEL, "#6B5512", "bold", spacing=1.3)}'
                f'{live("↗", x+w-18, y+h-14, 15, SANS, INK, anchor="end")}'
                f'</g>')

    body.append(path_text("the rest live in the repos →", F_HAND, 18, 300, 502, fill=INK_SOFT, rot=-2))
    body.append(star(264, 486, 10, RED, 8, 1.8))
    body.append(folio(5, 8, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ================================================================ 06 PLAYGROUND ==
def macintosh(cx, cy, rot=-2):
    """A little beige Mac, drawn from scratch."""
    x, y, w, h = cx - 92, cy - 113, 184, 210
    b = [f'<rect x="{x}" y="{y}" width="{w}" height="{h-26}" rx="8" fill="#E7DFC9" stroke="#2A261C" stroke-width="1.6" filter="url(#sh-soft)"/>',
         f'<rect x="{x+14}" y="{y+16}" width="{w-28}" height="112" rx="3" fill="#BFD8CE" stroke="#2A261C" stroke-width="1.4"/>',
         f'<rect x="{x+18}" y="{y+20}" width="{w-36}" height="104" fill="#D6E8DE"/>']
    # screen smiley + text
    b += [f'<circle cx="{x+92}" cy="{y+58}" r="17" fill="none" stroke="{INK}" stroke-width="1.6"/>',
          f'<circle cx="{x+86}" cy="{y+54}" r="1.8" fill="{INK}"/>',
          f'<circle cx="{x+98}" cy="{y+54}" r="1.8" fill="{INK}"/>',
          f'<path d="M{x+84},{y+64} Q{x+92},{y+71} {x+100},{y+64}" fill="none" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>',
          live("hello, world", x + 92, y + 93, 7.4, BODY, "#3D4A42", anchor="middle", spacing=.6),
          live("side quests since 2024", x + 92, y + 105, 5.2, BODY, "#5D6A62", anchor="middle", spacing=.4),
          # floppy slot + badge + chin
          f'<rect x="{x+18}" y="{y+138}" width="70" height="7" rx="2" fill="#CFC6AE" stroke="#2A261C" stroke-width="1"/>',
          f'<rect x="{x+106}" y="{y+136}" width="58" height="26" rx="2" fill="none" stroke="#2A261C" stroke-width="1"/>',
          live("anurag", x + 135, y + 148, 5.2, BODY, "#5A5342", anchor="middle"),
          live("’28", x + 135, y + 157, 5.2, BODY, "#5A5342", anchor="middle")]
    for i, col in enumerate([GREEN, YELLOW, RED, BLUE]):
        b.append(f'<rect x="{x+18+i*9}" y="{y+165}" width="6" height="4" fill="{col}"/>')
    # stand
    b += [f'<path d="M{x+58},{y+h-26} L{x+50},{y+h} L{x+134},{y+h} L{x+126},{y+h-26} Z" fill="#DCD3BC" stroke="#2A261C" stroke-width="1.4"/>',
          f'<rect x="{x+38}" y="{y+h-4}" width="108" height="7" rx="3" fill="#D8CFB8" stroke="#2A261C" stroke-width="1.4"/>']
    return (f'<g transform="rotate({rot} {cx} {cy})">' + "".join(b) + '</g>')


def cassette(cx, cy, rot=-7):
    x, y, w, h = cx - 105, cy - 64, 210, 128
    b = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#2B2A25" stroke="#15140F" stroke-width="1.6" filter="url(#sh-soft)"/>',
         f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="{h-20}" rx="2" fill="#E9E2CE"/>',
         f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="34" fill="#F2C842"/>',
         path_text("DSA MIX", F_HAND, 20, x + 16, y + 36, fill=INK, rot=-2),
         live("vol. 3 · 90 min", x + w - 16, y + 33, 7, BODY, "#5D5332", anchor="end"),
         f'<circle cx="{x+58}" cy="{y+76}" r="23" fill="#FFFDF6" stroke="#2B2A25" stroke-width="1.4"/>',
         f'<circle cx="{x+152}" cy="{y+76}" r="23" fill="#FFFDF6" stroke="#2B2A25" stroke-width="1.4"/>']
    for ccx in (x + 58, x + 152):
        b.append(f'<circle cx="{ccx}" cy="{y+76}" r="14" fill="#2B2A25"/>')
        for k in range(6):
            import math
            a = math.radians(k * 60)
            b.append(f'<line x1="{ccx}" y1="{y+76}" x2="{ccx+12*math.cos(a):.1f}" y2="{y+76+12*math.sin(a):.1f}" stroke="#D8CFB8" stroke-width="1.4"/>')
        b.append(f'<circle cx="{ccx}" cy="{y+76}" r="4" fill="#E9E2CE"/>')
    return f'<g transform="rotate({rot} {cx} {cy})">' + "".join(b) + '</g>'


def polaroid(cx, cy, w, h, rot, uri, caption):
    x, y = cx - w / 2, cy - h / 2
    b = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFDF6" filter="url(#sh)"/>',
         f'<image href="{uri}" x="{x+11}" y="{y+11}" width="{w-22}" height="{h-56}" preserveAspectRatio="xMidYMid slice"/>',
         path_text(caption, F_HAND, 13, cx, y + h - 16, "middle", fill=INK_SOFT)]
    return (f'<g transform="rotate({rot} {cx} {cy})">' + "".join(b)
            + tape(x + w - 28, y - 2, 52, 14, 12, .6) + '</g>')


def playground():
    W, H = 880, 580
    defs, bg = paper(W, H, "grid", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 26, "07", "PLAYGROUND"))
    body.append(f'<rect x="226" y="70" width="270" height="42" fill="{YELLOW}" opacity=".35" transform="rotate(-2 360 91)"/>')
    body.append(path_text("just for fun", F_HAND, 42, 250, 104, fill=INK, rot=-2))
    body.append(chip(620, 58, "NO AGENDA", INK, CREAM, 5, size=9))

    body.append(cassette(190, 220, -7))
    body.append(macintosh(445, 240, -2))
    body.append(polaroid(732, 236, 196, 250, 5, photo_uri("head"), "3am, still shipping"))

    body.append(sticky(74, 392, 204, 130, 2.5, YELLOW_PALE, ruled=True))
    body.append(path_text("fixed a bug", F_HAND, 16, 90, 428, fill=INK))
    body.append(path_text("no idea why", F_HAND, 16, 90, 452, fill=INK_SOFT))
    body.append(path_text("moving on", F_HAND, 16, 90, 476, fill=INK_SOFT))
    body.append(f'<circle cx="252" cy="410" r="4" fill="{RED}"/>')

    body.append(sticky(604, 402, 204, 116, -4, "#F7F1E1"))
    body.append(live("git commit -m", 622, 436, 10, BODY, "#4C4639"))
    body.append(live("\"hope\"", 622, 456, 10, BODY, INK, "bold"))
    body.append(live("(again)", 622, 476, 10, BODY, "#4C4639"))
    body.append(scribble(620, 488, 742, 486, RED, 1.4, 1.0))

    # ticket
    body.append(f'<g transform="rotate(7 786 92)">'
                f'<rect x="712" y="62" width="148" height="60" fill="{PAPER_WARM}" stroke="#2A261C" stroke-width="1.2" stroke-dasharray="5 3"/>'
                f'{path_text("NIT PATNA", F_DISPLAY, 12, 722, 84, tracking=.8, fill=INK)}'
                f'{live("CSE ’28 · ADMIT ONE", 722, 99, 6.6, LABEL, MUTED, "bold", spacing=.9)}'
                f'{live("NO. 3407", 852, 113, 6.4, BODY, RED, anchor="end")}'
                f'</g>')

    body.append(star(322, 380, 11, RED, 8, 1.8))
    body.append(star(560, 132, 7, INK, 0, 1.4))
    body.append(curved_arrow("M282,448 C 318,432 352,402 384,370", INK, 1.5, -43, (385, 369)))
    body.append(path_text("side quests: DSA · OSS · breaking prod (locally)", F_HAND, 16, 440, 552,
                          "middle", fill=INK_SOFT, rot=-1))
    body.append(folio(7, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# ================================================================= 07 STACK ==
def tech_mark(x, y, color, kind):
    if kind == "dot":
        return f'<circle cx="{x+5}" cy="{y+5}" r="5" fill="{color}"/>'
    if kind == "ring":
        return f'<circle cx="{x+5}" cy="{y+5}" r="4.2" fill="none" stroke="{color}" stroke-width="2"/>'
    if kind == "bars":
        return (f'<rect x="{x}" y="{y+1}" width="10" height="2.4" fill="{color}"/>'
                f'<rect x="{x}" y="{y+4.2}" width="10" height="2.4" fill="{color}"/>'
                f'<rect x="{x}" y="{y+7.4}" width="10" height="2.4" fill="{color}"/>')
    if kind == "diamond":
        return (f'<rect x="{x+2}" y="{y+2}" width="7" height="7" fill="{color}" '
                f'transform="rotate(45 {x+5.5} {y+5.5})"/>')
    if kind == "hex":
        return (f'<path d="M{x+5},{y} L{x+9.7},{y+2.6} V{y+7.4} L{x+5},{y+10} '
                f'L{x+0.3},{y+7.4} V{y+2.6} Z" fill="{color}"/>')
    return f'<rect x="{x}" y="{y}" width="10" height="10" rx="1.5" fill="{color}"/>'


def letstalk():
    W, H = 880, 600
    defs, bg = paper(W, H, "rule", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 26, "08", "LET'S TALK"))

    body.append(live("SHIPPED WITH", 44, 96, 8.4, LABEL, MUTED, "bold", spacing=1.7))
    body.append(path_text("the daily drivers", F_HAND, 16, 836, 94, "end", fill=INK_SOFT, rot=-1.5))

    body.append(f'<g transform="rotate(-.5 440 137)">'
                f'<rect x="40" y="110" width="800" height="54" fill="#FFFDF6" filter="url(#sh-soft)"/>'
                f'<rect x="40" y="110" width="800" height="54" fill="none" stroke="#000" stroke-opacity=".10"/>'
                f'{tape(84, 108, 72, 16, -6, .55)}'
                f'{tape(796, 108, 72, 16, 7, .55)}')
    tech = [("TypeScript", BLUE, "square"), ("React", "#2E7FB8", "dot"),
            ("Next.js", INK, "ring"), ("Node", GREEN, "hex"),
            ("MongoDB", "#2F8F4E", "diamond"), ("PostgreSQL", "#2E64A8", "square"),
            ("Docker", "#2E7FB8", "bars"), ("Git", RED, "diamond")]
    for i, (name, col, kind) in enumerate(tech):
        cx = 96 + i * 94
        tw = sans_width(name, 11.6, bold=True)
        body.append(tech_mark(cx - tw / 2 - 15, 132, col, kind))
        body.append(live(name, cx + 2, 143, 11.6, SANS, INK_SOFT, "bold", "middle"))
    body.append('</g>')
    body.append(live("plus Python · Django · Java · C++ · Linux", 44, 190, 8, BODY, MUTED))

    body.append(smiley(440, 254, 46))
    body.append(star(354, 240, 9, RED, 10, 1.7))
    body.append(star(534, 286, 7, INK, 0, 1.3))

    tt = "LET'S TALK"
    tw = path_width(tt, F_DISPLAY, 74, tracking=-1.8, sx=.93)
    body.append(f'<rect x="{440-tw/2-10:.1f}" y="342" width="{tw+20:.1f}" height="48" '
                f'fill="{YELLOW}" opacity=".38" transform="rotate(-.9 440 366)"/>')
    body.append(path_text(tt, F_DISPLAY, 74, 440, 386, "middle", tracking=-1.8, sx=.93,
                          extra=" filter='url(#rough-hard)'"))
    body.append(scribble(440 - tw / 2 + 6, 404, 440 + tw / 2 - 6, 402, RED, 2.4, 2.2))
    body.append(live("Got a project, a role, or a bug you can't kill?", 440, 436, 13.2, BODY,
                     INK_SOFT, anchor="middle"))
    body.append(live("My inbox is open, and I reply embarrassingly fast.", 440, 456, 13.2, BODY,
                     INK_SOFT, anchor="middle"))

    email = "anuragmishra3407@gmail.com"
    ew = mono_width(email, 16.4)
    body.append(f'<rect x="{440-ew/2-8:.1f}" y="476" width="{ew+16:.1f}" height="25" '
                f'fill="{YELLOW}" opacity=".5" transform="rotate(-.5 440 488)"/>')
    body.append(live(email, 440, 494, 16.4, BODY, INK, "bold", "middle", spacing=-.3))
    body.append(scribble(440 - ew / 2, 501, 440 + ew / 2, 500, INK, 1.4, .8))
    body.append(path_text("no forms. just email.", F_HAND, 16, 440, 534, "middle",
                          fill=INK_SOFT, rot=-1.2))

    body.append(folio(8, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, CONTACT_CSS)


# ================================================================= 08 CONTACT ==
CONTACT_CSS = NAV_CSS + '''
@keyframes smileblink{0%,92%,100%{transform:scaleY(1)}95%,98%{transform:scaleY(.12)}}
.eye{transform-box:fill-box;transform-origin:center;animation:smileblink 5.6s infinite}
'''

def smiley(cx, cy, r):
    return (f'<g transform="rotate(-3 {cx} {cy})">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{YELLOW}" stroke="{INK}" '
            'stroke-width="2.6" filter="url(#rough)"/>'
            f'<ellipse class="eye" cx="{cx-r*0.33}" cy="{cy-r*0.18}" rx="{r*0.075}" ry="{r*0.15}" fill="{INK}"/>'
            f'<ellipse class="eye" cx="{cx+r*0.33}" cy="{cy-r*0.18}" rx="{r*0.075}" ry="{r*0.15}" fill="{INK}"/>'
            f'<path d="M{cx-r*0.42},{cy+r*0.18} Q{cx},{cy+r*0.62} {cx+r*0.42},{cy+r*0.18}" '
            f'fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
            f'</g>')


def contact():
    W, H = 880, 600
    defs, bg = paper(W, H, "rule", PAPER)
    body = [bg, grain(W, H)]
    body.append(section_tag(40, 26, "09", "CONTACT"))

    body.append(path_text("CONTACT", F_DISPLAY, 68, 42, 126, tracking=-.9, sx=.9,
                          extra=" filter='url(#rough)'"))
    body.append(scribble(46, 140, 330, 138, RED, 2.4, 2.0))
    body.append(path_text("no forms, no funnels.", F_HAND, 17, 438, 116, fill=INK_SOFT, rot=-2))

    body.append(photo_frame(58, 176, 200, 264, -3.2, caption=None, tape_corners=(-12, 10)))
    body.append(path_text("hello from patna", F_HAND, 14, 158, 462, "middle", fill=INK_SOFT, rot=-1))

    # contact card
    body.append(f'<g transform="rotate(.8 526 310)">'
                f'<rect x="306" y="160" width="440" height="300" fill="#FFFDF6" filter="url(#sh)"/>'
                f'<rect x="306" y="160" width="440" height="300" fill="none" stroke="#000" stroke-opacity=".12"/>'
                f'{tape(500, 158, 78, 17, -6, .55)}'
                f'<circle cx="330" cy="192" r="4" fill="{GREEN}"/>'
                f'{live("OPEN TO", 342, 196, 7.2, LABEL, MUTED, "bold", spacing=1.3)}'
                f'{path_text("internships · collabs · good questions", F_HAND, 19, 324, 228, fill=INK)}'
                f'<line x1="326" y1="250" x2="726" y2="249" stroke="#000" stroke-opacity=".14" stroke-dasharray="4 4"/>')
    rows = [("EMAIL", "anuragmishra3407@gmail.com"),
            ("BASED", "Patna, IN · IST (UTC+5:30)"),
            ("REPLY", "usually within a day"),
            ("ELSEWHERE", "github / linkedin / x")]
    yy = 282
    for k, v in rows:
        body.append(live(k, 326, yy, 6.6, LABEL, MUTED, "bold", spacing=1.2))
        body.append(live(v, 398, yy, 8.8, BODY, INK))
        yy += 30
    body.append(f'<line x1="326" y1="396" x2="726" y2="395" stroke="#000" stroke-opacity=".14" stroke-dasharray="4 4"/>'
                f'{path_text("or just star a repo — I’ll notice", F_HAND, 17, 326, 432, fill=INK_SOFT, rot=-.6)}'
                f'</g>')

    # second, smaller print
    body.append(f'<g transform="rotate(7 792 438)">'
                f'<rect x="738" y="364" width="108" height="126" fill="#FFFDF6" filter="url(#sh)"/>'
                f'<image href="{photo_uri("head")}" x="744" y="370" width="96" height="114" '
                f'preserveAspectRatio="xMidYMid slice"/>'
                f'{tape(786, 360, 52, 14, 6, .6)}'
                f'</g>')
    body.append(star(734, 182, 10, RED, 9, 1.7))

    body.append(live("© 2026 Anurag Mishra — hand-built, SVG by SVG.", 44, 584, 9.6, BODY, MUTED))
    body.append(folio(9, 9, W, H))
    return svg_doc(W, H, "".join(body), defs, NAV_CSS)


# =================================================================== ROUTINES ==
PANELS = {
    "pf-hero": (hero, 880, 640),
    "pf-whatsup": (whatsup, 880, 560),
    "pf-about": (about, 880, 640),
    "pf-works": (works, 880, 680),
    "pf-project-career": (project_career, 880, 760),
    "pf-project-ghost": (project_ghost, 880, 700),
    "pf-playground": (playground, 880, 580),
    "pf-letstalk": (letstalk, 880, 600),
    "pf-contact": (contact, 880, 600),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("only", nargs="*", help="panel slugs to build")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    for slug, (fn, w, h) in PANELS.items():
        if args.only and slug not in args.only:
            continue
        svg = fn()
        path = os.path.join(OUT, slug + ".svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"{slug}.svg  {len(svg)/1024:.1f} KB")
        if args.preview:
            png = os.path.join(PREVIEW, slug + ".png")
            chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=2", f"--window-size={w},{h}",
                            f"--screenshot={png}", f"file://{path}"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            print(f"  → {png}")


if __name__ == "__main__":
    main()
