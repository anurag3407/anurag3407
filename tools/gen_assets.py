#!/usr/bin/env python3
"""
Generate hand-crafted animated SVG assets for the anurag3407 profile README.

Only uses animation techniques that survive GitHub's <img> SVG sandbox
(CSS @keyframes — no scripts, no external refs).

Run with --preview to emit static variants (animations stripped, typing
pre-completed) into assets/preview/ for render checking.
"""
import argparse
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets")

# ---------------------------------------------------------------- palette ---
BG0 = "#070b14"; BG1 = "#0b1120"; PANEL = "#0d1526"
LINE = "#1c2740"; GRID = "#101a30"
RED = "#ff4d4d"; RED_DEEP = "#d32f2f"
BLUE = "#4d8dff"; GREEN = "#3ddc84"; AMBER = "#ffb454"
TXT_HI = "#e8eef7"; TXT_MID = "#9aa8bf"; TXT_DIM = "#5c6b82"

MONO = "'SF Mono','Cascadia Code',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# =========================================================================
# 1. HERO — animated terminal window with typing effect
# =========================================================================
def hero(preview=False):
    W, H = 900, 420
    T = 16.0                      # full loop period (s)
    CH = 9                        # monospace char advance (font-size 15)
    fs = 15
    x0 = 40                       # body left padding
    ytop = 96                     # first text baseline
    lh = 34                       # line height

    lines = [
        ("whoami", "anurag_mishra · full-stack engineer · NIT Patna CSE"),
        ("cat stack.txt", "TypeScript ▸ React ▸ Next.js ▸ Node ▸ Django ▸ PostgreSQL"),
        ("git log --oneline -1", "f1a2c3d ▸ feat: ship career-pilot — 129★ · 758 forks"),
        ("./focus --mode=build", "⚡ building AI tools · open to internships & OSS"),
    ]

    # ---- timeline: per line (cmd, out, type_start, type_dur, out_show) ----
    tl = []
    t = 0.8
    for cmd, out in lines:
        dur = 0.5 + len(cmd) * 0.062
        tl.append((cmd, out, t, dur, t + dur + 0.35))
        t += dur + 1.15
    fade_all = T - 1.1            # everything fades just before wrap

    def pct(sec): return round(sec / T * 100, 3)

    css, body = [], []
    for i, (cmd, out, ts, dur, ofs) in enumerate(tl):
        cmd_w = len(cmd) * CH
        ty_s, ty_e = pct(ts), pct(ts + dur)
        o_s = pct(ofs)
        cur_off = pct(ts + dur + 0.3)
        y = ytop + i * 2 * lh
        # cover slides right, stepping one char at a time, then rests
        css.append(
            f"@keyframes type{i}{{0%,{ty_s}%{{transform:translateX(0);"
            f"animation-timing-function:steps({len(cmd)})}}"
            f"{ty_e}%,100%{{transform:translateX({cmd_w}px)}}}}")
        # output fades in and stays until the global fade
        css.append(
            f"@keyframes show{i}{{0%,{o_s}%{{opacity:0}}"
            f"{pct(ofs + 0.25)}%,{pct(fade_all)}%{{opacity:1}}"
            f"{pct(fade_all + 0.9)}%,100%{{opacity:0}}}}")
        # cursor rides with the typing, only visible while its line types
        css.append(
            f"@keyframes tcur{i}{{0%,{ty_s}%{{transform:translateX(0);"
            f"animation-timing-function:steps({len(cmd)})}}"
            f"{ty_e}%,100%{{transform:translateX({cmd_w}px)}}}}")
        css.append(
            f"@keyframes ocur{i}{{0%,{pct(ts - 0.05)}%{{opacity:0}}"
            f"{pct(ts)}%,{cur_off}%{{opacity:1}}"
            f"{pct(ts + dur + 0.4)}%,100%{{opacity:0}}}}")
        body.append(
            f'<g class="ln{i}">'
            f'<text x="{x0}" y="{y}" font-family="{MONO}" font-size="{fs}" font-weight="700" fill="{RED}">$</text>'
            f'<text x="{x0 + 24}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{TXT_HI}">{esc(cmd)}</text>'
            + ("" if preview else
               f'<g class="cov{i}"><rect x="{x0 + 23}" y="{y - 16}" width="{cmd_w + 16}" height="{fs + 10}" fill="{PANEL}"/></g>'
               f'<g class="cg{i}"><rect class="cur" x="{x0 + 24}" y="{y - fs + 2}" width="8" height="{fs - 2}" fill="{TXT_HI}"/></g>')
            + f'<text class="out{i}" x="{x0 + 24}" y="{y + lh}" font-family="{MONO}" font-size="{fs}" fill="{TXT_MID}"'
            + (' opacity="1"' if preview else '')
            + f'>{esc(out)}</text></g>')
    css.append(
        f"@keyframes cyclefade{{0%,{pct(fade_all)}%{{opacity:1}}"
        f"{pct(fade_all + 0.9)}%,100%{{opacity:0}}}}")

    anim_css = "" if preview else """
@keyframes blink{0%,45%{opacity:1}50%,95%{opacity:0}100%{opacity:1}}
@keyframes sweep{0%{transform:translateY(-6px)}100%{transform:translateY(414px)}}
@keyframes led{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes bar{0%{transform:translateX(-124px)}100%{transform:translateX(124px)}}
@keyframes drift{0%{transform:translate(0,0)}100%{transform:translate(14px,-18px)}}
""" + "\n".join(css)
    cls = "" if preview else "".join(
        f".cov{i}{{animation:type{i} {T}s linear infinite}}\n"
        f".cg{i}{{animation:tcur{i} {T}s steps(1) infinite,ocur{i} {T}s linear infinite}}\n"
        f".out{i}{{animation:show{i} {T}s linear infinite}}\n"
        f".ln{i}{{animation:cyclefade {T}s linear infinite}}\n"
        for i in range(4)) + f""".cur{{animation:blink .9s steps(1) infinite}}
.sweep{{animation:sweep {T}s linear infinite}}
.led{{animation:led 2s ease-in-out infinite}}
.bar{{animation:bar 2.6s linear infinite}}
.p0{{animation:drift 7s ease-in-out infinite alternate}}
.p1{{animation:drift 9s ease-in-out infinite alternate .8s}}
.p2{{animation:drift 11s ease-in-out infinite alternate 2s}}
"""

    # NOTE: .cg uses tcur (transform, stepped) + ocur (opacity) — two
    # animations, disjoint properties. steps(1) on the element applies
    # between keyframes of tcur only where its timing isn't overridden
    # per-keyframe; tcur sets steps(len) inside its own keyframes, which
    # takes precedence for that segment.
    particles = "" if preview else (
        f'<circle class="p0" cx="700" cy="120" r="2.2" fill="{RED}" opacity=".5"/>'
        f'<circle class="p1" cx="820" cy="200" r="1.6" fill="{BLUE}" opacity=".45"/>'
        f'<circle class="p2" cx="640" cy="300" r="1.8" fill="{AMBER}" opacity=".4"/>')
    scan = "" if preview else (
        f'<rect class="sweep" x="10" y="0" width="880" height="3" fill="{BLUE}" opacity=".07"/>')

    status = (
        f'<text x="40" y="392" font-family="{MONO}" font-size="12" fill="{GREEN}">● main</text>'
        f'<text x="110" y="392" font-family="{MONO}" font-size="12" fill="{TXT_DIM}">↑2 ↓0</text>'
        f'<text x="196" y="392" font-family="{MONO}" font-size="12" fill="{TXT_DIM}">deploying portfolio…</text>'
        f'<rect x="360" y="386" width="120" height="4" rx="2" fill="{LINE}"/>'
        f'<g clip-path="url(#pc)"><g class="bar"><rect x="360" y="386" width="56" height="4" fill="url(#pg)"/></g></g>'
        f'<text x="866" y="392" text-anchor="end" font-family="{MONO}" font-size="12" fill="{TXT_DIM}">utf-8 · lf · v2026.09</text>')

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="terminal hero">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
<linearGradient id="tb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111a2e"/><stop offset="1" stop-color="#0d1424"/></linearGradient>
<linearGradient id="pg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{RED_DEEP}"/><stop offset="1" stop-color="{RED}"/></linearGradient>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="{GRID}" stroke-width="1"/></pattern>
<clipPath id="pc"><rect x="360" y="386" width="120" height="4" rx="2"/></clipPath>
<style>{anim_css}{cls}text{{user-select:none}}</style>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>
<!-- terminal window: SOLID interior so typing covers blend invisibly -->
<rect x="10" y="10" width="880" height="400" rx="16" fill="{PANEL}" stroke="{LINE}" stroke-width="1"/>
<path d="M10 26a16 16 0 0 1 16-16h848a16 16 0 0 1 16 16v28H10Z" fill="url(#tb)"/>
<line x1="10" y1="54" x2="890" y2="54" stroke="{LINE}" stroke-width="1"/>
<circle cx="38" cy="32" r="6.5" fill="#ff5f57"/><circle cx="64" cy="32" r="6.5" fill="#febc2e"/>
<circle class="led" cx="90" cy="32" r="6.5" fill="#28c840"/>
<text x="450" y="37" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{TXT_MID}">anurag@dev-os — ~/portfolio</text>
<text x="866" y="37" text-anchor="end" font-family="{MONO}" font-size="11" fill="{TXT_DIM}">zsh · 96×24</text>
{scan}
{"".join(body)}
<line x1="10" y1="374" x2="890" y2="374" stroke="{LINE}" stroke-width="1"/>
{status}
{particles}
<g stroke="{RED_DEEP}" stroke-width="2" fill="none" opacity=".8">
<path d="M2 30V10h20"/><path d="M878 10h20v20"/><path d="M2 390v20h20"/><path d="M878 410h20v-20"/>
</g>
</svg>"""

# =========================================================================
# 2. PLAYER CARD — RPG character sheet
# =========================================================================
def player(preview=False):
    W, H = 880, 380
    anim = "" if preview else """
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{opacity:.55}50%{opacity:.2}}
@keyframes shimmer{0%{transform:translateX(-440px)}100%{transform:translateX(440px)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
.ring{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}
.ring2{transform-box:fill-box;transform-origin:center;animation:spin 22s linear infinite reverse}
.glow{animation:pulse 2.4s ease-in-out infinite}
.shm{animation:shimmer 3.2s linear infinite}
.am{animation:float 5s ease-in-out infinite}
"""

    def vital(y, pid, label, val, color, note):
        x, w = 230, 420
        fill_w = int(w * val / 100)
        return (
            f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="12" font-weight="700" fill="{TXT_MID}">{label}</text>'
            f'<text x="{x + w}" y="{y}" text-anchor="end" font-family="{SANS}" font-size="12" font-weight="800" fill="{color}">{val}<tspan fill="{TXT_DIM}" font-weight="400">/100</tspan></text>'
            f'<rect x="{x}" y="{y + 7}" width="{w}" height="7" rx="3.5" fill="{LINE}"/>'
            f'<clipPath id="c-{pid}"><rect x="{x}" y="{y + 7}" width="{fill_w}" height="7" rx="3.5"/></clipPath>'
            f'<g clip-path="url(#c-{pid})"><rect x="{x}" y="{y + 7}" width="{fill_w}" height="7" fill="{color}"/>'
            + ("" if preview else f'<g class="shm"><rect x="{x}" y="{y + 7}" width="70" height="7" fill="{TXT_HI}" opacity=".18"/></g>')
            + '</g>'
            f'<text x="{x}" y="{y + 31}" font-family="{SANS}" font-size="10.5" fill="{TXT_DIM}">{note}</text>')

    def stat(x, label, val, color):
        w = 180
        return (
            f'<text x="{x}" y="356" font-family="{SANS}" font-size="11" font-weight="700" fill="{TXT_MID}">{label}</text>'
            f'<text x="{x + w}" y="356" text-anchor="end" font-family="{SANS}" font-size="11" font-weight="800" fill="{color}">{val}</text>'
            f'<rect x="{x}" y="361" width="{w}" height="6" rx="3" fill="{LINE}"/>'
            f'<rect x="{x}" y="361" width="{int(w * val / 100)}" height="6" rx="3" fill="{color}"/>')

    hex_pts = " ".join(
        f"{110 + 52 * math.cos(math.radians(a - 90)):.1f},{180 + 52 * math.sin(math.radians(a - 90)):.1f}"
        for a in range(0, 360, 60))

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="player card">
<defs>
<linearGradient id="pbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
<linearGradient id="lv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RED}"/><stop offset="1" stop-color="{RED_DEEP}"/></linearGradient>
<style>{anim}text{{user-select:none}}</style>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="url(#pbg)" stroke="{LINE}" stroke-width="1"/>
<g class="am">
<circle class="glow" cx="110" cy="180" r="74" fill="{RED_DEEP}" opacity=".08"/>
<circle class="ring" cx="110" cy="180" r="70" fill="none" stroke="{RED_DEEP}" stroke-width="1.5" stroke-dasharray="4 10" opacity=".7"/>
<circle class="ring2" cx="110" cy="180" r="62" fill="none" stroke="{BLUE}" stroke-width="1" stroke-dasharray="2 14" opacity=".5"/>
<polygon points="{hex_pts}" fill="#101a30" stroke="{LINE}" stroke-width="1.5"/>
<text x="110" y="176" text-anchor="middle" font-family="{MONO}" font-size="34" font-weight="700" fill="{TXT_HI}">AM</text>
<text x="110" y="200" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{RED}">lvl 02</text>
</g>
<text x="230" y="84" font-family="{SANS}" font-size="30" font-weight="800" fill="{TXT_HI}">Anurag Mishra</text>
<text x="230" y="112" font-family="{SANS}" font-size="15" fill="{RED}">Class: Full-Stack Mage · Guild: NIT Patna (CSE)</text>
<text x="230" y="140" font-family="{MONO}" font-size="12.5" fill="{TXT_MID}">motto: break first, build later — every bug is a duel.</text>
<rect x="230" y="156" width="120" height="24" rx="12" fill="url(#lv)"/>
<text x="290" y="172" text-anchor="middle" font-family="{SANS}" font-size="11" font-weight="700" fill="#fff">▲ MAIN QUEST</text>
<text x="366" y="172" font-family="{SANS}" font-size="11.5" fill="{TXT_MID}">ship career-pilot v2 · grind DSA · land the internship</text>
{vital(222, "hp", "HP · coffee", 88, AMBER, "sustained by espresso and curiosity")}
{vital(262, "mp", "MP · sleep", 41, BLUE, "sacrificed to side-projects and hack nights")}
{vital(302, "xp", "XP · typescript", 76, RED, "47 of 140 repos fluent in the typed arts")}
{stat(60, "STR · backend", 84, RED_DEEP)}
{stat(262, "DEX · frontend", 91, BLUE)}
{stat(464, "INT · ai/agents", 87, GREEN)}
{stat(668, "CHA · shipping", 89, AMBER)}
</svg>"""

# =========================================================================
# 3. PROJECT BANNER — career-pilot flagship
# =========================================================================
def project(preview=False):
    W, H = 900, 300
    anim = "" if preview else """
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes flame{0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.35)}}
@keyframes glow{0%,100%{opacity:.4}50%{opacity:.9}}
@keyframes sweep2{0%{transform:translateX(-900px)}100%{transform:translateX(900px)}}
.rk{animation:float 3.4s ease-in-out infinite}
.fl{transform-box:fill-box;transform-origin:top;animation:flame .5s ease-in-out infinite}
.st{animation:glow 2.2s ease-in-out infinite}
.ed{animation:sweep2 6s linear infinite}
"""
    chips = ["Next.js", "React", "Node.js", "AI/LLM", "PostgreSQL", "Open-Source"]
    cx = 60
    chip_svg = []
    for c in chips:
        w = 20 + len(c) * 7.2
        chip_svg.append(
            f'<rect x="{cx:.0f}" y="196" width="{w:.0f}" height="26" rx="13" fill="#101a30" stroke="{LINE}"/>'
            f'<text x="{cx + w / 2:.0f}" y="213" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="{TXT_MID}">{c}</text>')
        cx += w + 10

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="career-pilot banner">
<defs>
<linearGradient id="jbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
<linearGradient id="redline" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{RED_DEEP}"/><stop offset="1" stop-color="{RED}"/></linearGradient>
<clipPath id="card"><rect x="8" y="8" width="884" height="284" rx="16"/></clipPath>
<style>{anim}text{{user-select:none}}</style>
</defs>
<rect x="8" y="8" width="884" height="284" rx="16" fill="url(#jbg)" stroke="{LINE}" stroke-width="1"/>
<g clip-path="url(#card)"><rect class="ed" x="-900" y="8" width="130" height="284" fill="{RED}" opacity=".05"/></g>
<path d="M8 24a16 16 0 0 1 16-16h180l-22 18 22 18H24A16 16 0 0 1 8 24Z" fill="url(#redline)"/>
<text x="100" y="30" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="700" fill="#fff">◆ FLAGSHIP · OPEN-SOURCE</text>
<text x="60" y="96" font-family="{SANS}" font-size="40" font-weight="800" fill="{TXT_HI}">career-pilot</text>
<text x="60" y="126" font-family="{SANS}" font-size="15" fill="{TXT_MID}">AI co-pilot for your career — resume optimizer, mock interviews,</text>
<text x="60" y="148" font-family="{SANS}" font-size="15" fill="{TXT_MID}">job-tracker &amp; portfolio builder — 120+ contributors aboard.</text>
{"".join(chip_svg)}
<text x="60" y="262" font-family="{MONO}" font-size="12.5" fill="{BLUE}">github.com/anurag3407/career-pilot ↗</text>
<rect x="640" y="60" width="220" height="180" rx="14" fill="#101a30" stroke="{LINE}"/>
<circle class="st" cx="750" cy="112" r="44" fill="{RED_DEEP}" opacity=".5"/>
<g transform="translate(730,92)"><path d="M32 2l8.2 16.6 18.2 2.6-13.2 12.9 3.1 18.1L32 44l-16.3 8.6 3.1-18.1L5.6 21.2l18.2-2.6Z" transform="scale(.62)" fill="{AMBER}"/></g>
<text x="750" y="160" text-anchor="middle" font-family="{SANS}" font-size="34" font-weight="800" fill="{TXT_HI}">129</text>
<text x="750" y="178" text-anchor="middle" font-family="{SANS}" font-size="11" fill="{AMBER}">★ stars · 758 forks</text>
<path d="M660 204h10l6-13 8 26 6-13h11" stroke="{GREEN}" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<text x="716" y="208" font-family="{SANS}" font-size="12.5" fill="{GREEN}">actively maintained</text>
<g class="rk" transform="translate(570,35)">
<path d="M18 44s-14-8-14-24c0-12 8-20 14-24 6 4 14 12 14 24 0 16-14 24-14 24Z" fill="{PANEL}" stroke="{RED}" stroke-width="1.6"/>
<circle cx="18" cy="20" r="5" fill="{BLUE}"/>
<path d="M8 38l-8 8 3-11M28 38l8 8-3-11" fill="{RED_DEEP}"/>
<path class="fl" d="M13 46c1 5 3 8 5 9 2-1 4-4 5-9-3 1.5-7 1.5-10 0Z" fill="{AMBER}"/>
</g>
</svg>"""

# =========================================================================
# 4. DIVIDER — circuit line with traveling pulse
# =========================================================================
def divider(preview=False):
    W, H = 900, 30
    anim = "" if preview else """
@keyframes travel{0%{transform:translateX(0);opacity:0}8%{opacity:1}92%{opacity:1}100%{transform:translateX(840px);opacity:0}}
@keyframes travel2{0%{transform:translateX(0);opacity:0}8%{opacity:1}92%{opacity:1}100%{transform:translateX(-840px);opacity:0}}
.d1{animation:travel 2.8s cubic-bezier(.4,0,.6,1) infinite}
.d2{animation:travel2 2.8s cubic-bezier(.4,0,.6,1) infinite}
"""
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="divider">
<defs><style>{anim}</style>
<linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{LINE}" stop-opacity="0"/><stop offset="1" stop-color="{LINE}"/></linearGradient>
<linearGradient id="fadeR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{LINE}"/><stop offset="1" stop-color="{LINE}" stop-opacity="0"/></linearGradient>
</defs>
<rect x="30" y="14" width="400" height="2" fill="url(#fadeL)"/>
<rect x="470" y="14" width="400" height="2" fill="url(#fadeR)"/>
<rect x="432" y="9" width="36" height="12" rx="6" fill="none" stroke="{RED_DEEP}" stroke-width="1.4"/>
<circle cx="436" cy="15" r="2.2" fill="{RED}"/>
<circle cx="464" cy="15" r="2.2" fill="{RED}"/>
<g class="d1"><circle cx="30" cy="15" r="3" fill="{RED}"/><circle cx="30" cy="15" r="6.5" fill="{RED}" opacity=".3"/></g>
<g class="d2"><circle cx="870" cy="15" r="3" fill="{BLUE}"/><circle cx="870" cy="15" r="6.5" fill="{BLUE}" opacity=".3"/></g>
</svg>"""

# =========================================================================
# 5. FOOTER — closing terminal
# =========================================================================
def footer(preview=False):
    W, H = 900, 170
    anim = "" if preview else """
@keyframes blink2{0%,45%{opacity:1}50%,95%{opacity:0}100%{opacity:1}}
@keyframes rise{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
.cur2{animation:blink2 1s steps(1) infinite}
.who{animation:rise 4s ease-in-out infinite}
"""
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="footer terminal">
<defs><style>{anim}text{{user-select:none}}</style>
<linearGradient id="fbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG1}" stop-opacity="0"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#fbg)" rx="14"/>
<text x="60" y="52" font-family="{MONO}" font-size="15" font-weight="700" fill="{RED}">$</text>
<text x="84" y="52" font-family="{MONO}" font-size="15" fill="{TXT_HI}">exit</text>
<rect class="cur2" x="124" y="38" width="9" height="16" fill="{TXT_HI}"/>
<text x="84" y="84" font-family="{MONO}" font-size="13" fill="{TXT_MID}">session closed · thanks for scrolling — 100% ▓▓▓▓▓▓</text>
<text x="84" y="112" font-family="{MONO}" font-size="13" fill="{GREEN}">◈ crafted by hand with raw SVG — zero templates</text>
<text x="84" y="140" font-family="{MONO}" font-size="13" fill="{TXT_DIM}">reconnect →</text>
<text x="184" y="140" font-family="{MONO}" font-size="13" fill="{BLUE}">linkedin/anurag3407 · x/anurag3407 · anurag3407.dev</text>
<g class="who"><text x="840" y="128" text-anchor="end" font-family="{SANS}" font-size="30" fill="{RED_DEEP}" opacity=".85">⛩️</text></g>
</svg>"""

# =========================================================================
# 6. LANGUAGES — hand-drawn horizontal distribution bar (real repo data)
#    140 public repos (non-fork): TS 47, JS 18, CSS 5, Python 4, HTML 4,
#    Java 1, other/none 61  → shares of the 79 language-tagged repos:
#    TS 59%, JS 23%, CSS 6%, Python 5%, HTML 5%, Java 2%
# =========================================================================
def languages(preview=False):
    W, H = 900, 150
    data = [
        ("TypeScript", 59, "#3178c6", "TS"),
        ("JavaScript", 23, "#f7df1e", "JS"),
        ("CSS", 6, "#663399", "CSS"),
        ("Python", 5, "#ffd343", "PY"),
        ("HTML", 5, "#e34c26", "HTML"),
        ("Java", 2, "#f89820", "JAVA"),
    ]
    x = 40
    bw = 820
    seg = []
    for name, pct, color, short in data:
        w = bw * pct / 100
        seg.append(
            f'<rect x="{x:.1f}" y="42" width="{w:.1f}" height="26" fill="{color}"/>'
            + ("" if w < 46 else
               f'<text x="{x + w / 2:.1f}" y="59" text-anchor="middle" font-family="{SANS}" font-size="11.5" font-weight="700" fill="{BG0}">{short} {pct}%</text>'))
        x += w
    # per-segment width labels for narrow ones, below the bar
    labels = []
    lx = 40
    labeled = 0
    for name, pct, color, short in data:
        w = bw * pct / 100
        if w >= 46:
            labels.append(
                f'<text x="{lx + w / 2:.1f}" y="86" text-anchor="middle" font-family="{SANS}" font-size="10.5" fill="{TXT_DIM}">{short} {pct}%</text>')
            labeled += pct
        lx += w
    labels.append(
        f'<text x="860" y="86" text-anchor="end" font-family="{SANS}" font-size="10.5" fill="{TXT_DIM}">other {100 - labeled}%</text>')
    # title row
    title = (f'<text x="40" y="24" font-family="{MONO}" font-size="13" font-weight="700" fill="{RED}">$</text>'
             f'<text x="60" y="24" font-family="{MONO}" font-size="13" fill="{TXT_HI}">git ls-remote --stats · language distribution across 140 repos</text>')
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="language distribution">
<defs><style>text{{user-select:none}}</style>
<linearGradient id="lbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="url(#lbg)" stroke="{LINE}" stroke-width="1"/>
{title}
{"".join(seg)}
{"".join(labels)}
<text x="860" y="116" text-anchor="end" font-family="{MONO}" font-size="10.5" fill="{TXT_DIM}">sampled 2026.09 · source: GitHub API</text>
<text x="40" y="116" font-family="{MONO}" font-size="10.5" fill="{TXT_DIM}">typed &gt; untyped — the prophecy holds</text>
</svg>"""

# =========================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true",
                    help="static variants for render checking (no animation, typing pre-completed)")
    args = ap.parse_args()
    out = os.path.join(OUT, "preview") if args.preview else OUT
    os.makedirs(out, exist_ok=True)
    jobs = {
        "hero-terminal.svg": hero,
        "player-card.svg": player,
        "project-career-pilot.svg": project,
        "divider.svg": divider,
        "footer-terminal.svg": footer,
        "languages.svg": languages,
    }
    for name, fn in jobs.items():
        path = os.path.join(out, name)
        with open(path, "w") as f:
            f.write(fn(args.preview))
        print("wrote", path, f"({os.path.getsize(path)} bytes)")

if __name__ == "__main__":
    main()
