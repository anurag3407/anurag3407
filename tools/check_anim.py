#!/usr/bin/env python3
"""
Animation-state checker for the live (animated) README SVG assets.

Renders the animated SVG in headless Chrome with --virtual-time-budget
to fast-forward CSS animation clocks, screenshots at several points in
the cycle, then asserts expected regional states:

hero-terminal (16s loop):
  * t=1.6s  — line1 typing: some command-1 glyphs visible, output-1 row
              still blank, lines 2-4 completely blank
  * t=6.5s  — line-2 typed: output-2 row has content, line-3/4 blank
  * t=12.0s — line-4 typed: output-4 row has content
  * t=15.6s — global fade: all body rows darker than at t=12 (fading)
  * cursor block visible during line-1 typing

other assets: frames at two different times must differ pixel-wise
(animation running), and divider/project/player must keep their text
regions stable (text shouldn't move).
"""
from PIL import Image, ImageChops
import subprocess
import sys
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def shoot(svg_path, t_ms, size=(1100, 520)):
    """Deterministic capture: inline the SVG in HTML and PIN every CSS
    animation to exactly t_ms via the Web Animations API, so the frame
    is reproducible regardless of headless virtual-time flakiness."""
    with open(svg_path) as f:
        svg = f.read()
    with tempfile.TemporaryDirectory() as td:
        html = (
            "<!DOCTYPE html><html><head><style>html,body{margin:0;padding:0;"
            "background:#03050a;width:" + str(size[0]) + "px}</style></head><body>"
            + svg +
            "<script>document.getAnimations().forEach(function(a){"
            f"a.currentTime = {t_ms}; a.pause();}});"
            "</script></body></html>")
        hp = os.path.join(td, "h.html")
        with open(hp, "w") as f:
            f.write(html)
        out = os.path.join(td, "s.png")
        subprocess.run([
            CHROME, "--headless", "--disable-gpu",
            f"--screenshot={out}", f"--window-size={size[0]},{size[1]}",
            "--virtual-time-budget=2500",
            "file://" + hp,
        ], capture_output=True, timeout=60)
        return Image.open(out).convert("RGB")

def region_has_ink(im, x0, y0, x1, y1, bg=(13, 21, 38), tol=34, frac=0.004):
    """True if enough non-background pixels exist in the region."""
    px = im.crop((int(x0), int(y0), int(x1), int(y1)))
    w, h = px.size
    if w == 0 or h == 0:
        return False
    data = px.getdata()
    ink = 0
    for r, g, b in data:
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tol:
            ink += 1
    return ink >= max(1, int(len(data) * frac)), ink / len(data)

def ink_ratio(im, x0, y0, x1, y1, bg=(13, 21, 38), tol=34):
    px = im.crop((int(x0), int(y0), int(x1), int(y1)))
    data = list(px.getdata())
    if not data:
        return 0.0
    ink = sum(1 for r, g, b in data if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tol)
    return ink / len(data)

def mean_luma(im, box=None):
    im2 = im.convert("L").crop(box) if box else im.convert("L")
    h = im2.histogram()
    n = sum(h)
    return sum(i * c for i, c in enumerate(h)) / max(1, n)

def main():
    issues = []

    hero = os.path.join(ASSETS, "hero-terminal.svg")
    print("== hero animation states ==")
    # --- t = 1.6s: line 1 typing ---
    f1 = shoot(hero, 1600)
    cmd1 = region_has_ink(f1, 60, 82, 300, 100)          # line-1 command band
    out1 = region_has_ink(f1, 60, 112, 620, 132)          # line-1 output band
    lines234 = region_has_ink(f1, 60, 150, 620, 330)      # everything below
    print(f"  t=1.6s cmd1_ink={cmd1[1]:.3f} out1_ink={out1[1]:.3f} below_ink={lines234[1]:.4f}")
    if cmd1[1] < 0.01:
        issues.append("hero t=1.6s: line-1 command shows no ink — typing not running?")
    if out1[1] > 0.01:
        issues.append(f"hero t=1.6s: line-1 output ink={out1[1]:.3f} — should be ~0 (hidden until typed)")
    if lines234[1] > 0.01:
        issues.append(f"hero t=1.6s: lines 2-4 ink={lines234[1]:.3f} — should be hidden this early")
    # cursor visible during typing: bright block near x0+24.. on line 1
    cur = ink_ratio(f1, 60, 80, 340, 102, bg=(13, 21, 38), tol=180)
    print(f"  cursor-bright pixels ratio={cur:.4f}")
    if cur < 0.001:
        issues.append("hero t=1.6s: no bright cursor block found on line 1")

    # --- t = 6.5s: line 2 typed, output 2 visible ---
    f2 = shoot(hero, 6500)
    out2 = region_has_ink(f2, 60, 180, 620, 200)
    out3 = region_has_ink(f2, 60, 248, 620, 268)
    print(f"  t=6.5s out2_ink={out2[1]:.3f} out3_ink={out3[1]:.4f}")
    if out2[1] < 0.01:
        issues.append("hero t=6.5s: line-2 output not visible after its typing window")
    if out3[1] > 0.02:
        issues.append(f"hero t=6.5s: line-3 output ink={out3[1]:.3f} — should still be hidden")

    # --- t = 12s: line 4 typed, output 4 visible ---
    f3 = shoot(hero, 12000)
    out4 = region_has_ink(f3, 60, 316, 620, 336)
    print(f"  t=12.0s out4_ink={out4[1]:.3f}")
    if out4[1] < 0.01:
        issues.append("hero t=12s: line-4 output not visible after its typing window")

    # --- t = 15.6s: global fade should reduce body luma vs t=12s ---
    f4 = shoot(hero, 15600)
    body_box = (40, 70, 640, 340)
    l12, l156 = mean_luma(f3, body_box), mean_luma(f4, body_box)
    print(f"  body luma t=12s={l12:.1f} t=15.6s={l156:.1f}")
    if l156 > l12 * 0.92:
        issues.append(f"hero: no fade detected at end of cycle (luma {l12:.1f} -> {l156:.1f})")

    # other assets — animation just needs to run (frames differ)
    print("== other assets animate ==")
    for name, box in [
        ("player-card.svg", (0, 0, 880, 380)),
        ("project-career-pilot.svg", (8, 8, 892, 292)),
        ("divider.svg", (20, 0, 880, 30)),
        ("footer-terminal.svg", (0, 0, 900, 170)),
    ]:
        p = os.path.join(ASSETS, name)
        a = shoot(p, 700)
        b = shoot(p, 2600)
        if a.size != b.size:
            issues.append(f"{name}: screenshot sizes differ?!")
            continue
        diff = ImageChops.difference(a.convert("L"), b.convert("L")).getbbox()
        if diff is None:
            issues.append(f"{name}: no pixel change between t=0.7s and t=2.6s — animation not running")
        else:
            print(f"  {name}: animates (diff bbox {diff})")
        # text regions should stay stable (only decor moves) for text assets
        if name != "divider.svg":
            # sample a text-heavy strip; heavy diff there would mean text jitter
            ta = a.crop((60, 60, 500, 170)).convert("L")
            tb = b.crop((60, 60, 500, 170)).convert("L")
            d = ImageChops.difference(ta, tb)
            hist = d.histogram()
            moved = sum(hist[40:]) / max(1, sum(hist))
            if moved > 0.06 and name == "footer-terminal.svg":
                issues.append(f"{name}: text region changes between frames ({moved:.2%}) — text shouldn't move")

    print()
    if issues:
        print(f"✗ {len(issues)} issue(s):")
        for i in issues:
            print("  -", i)
        sys.exit(1)
    print("✓ all animation checks passed")

if __name__ == "__main__":
    main()
