#!/usr/bin/env python3
"""check_tokens.py — CI guard: tokens.css <-> tokens.ts parity + WCAG contrast assertions.
Usage: python3 -I design/check_tokens.py   (exit 1 on failure)"""
import re, sys, pathlib
here = pathlib.Path(__file__).parent
css = (here / "tokens.css").read_text()
ts = (here / "tokens.ts").read_text()

def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def L(h):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
def cr(a, b):
    la, lb = sorted((L(a), L(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def ts_obj(name):
    m = re.search(r"export const %s = \{(.*?)\} as const;" % name, ts, re.S)
    return dict(re.findall(r"(\w+):\s*'(#[0-9a-fA-F]{6})'", m.group(1)))

dark, light = ts_obj("dark"), ts_obj("light")
camel = lambda k: re.sub(r'-(\w)', lambda m: m.group(1).upper(), k)

def css_vars(block):
    return {camel(k): v.lower() for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", block)}
root = css[css.index(":root {"): css.index(':root[data-theme="light"]')]
lt = css[css.index(':root[data-theme="light"]'): css.index("@media (prefers-color-scheme: light)")]
cd, cl = css_vars(root), css_vars(lt)

fail = []
for name, tsv, cssv in (("dark", dark, cd), ("light", light, cl)):
    for k, v in tsv.items():
        key = {'text1':'text1','text2':'text2','text3':'text3'}.get(k, k)
        if key in cssv and cssv[key] != v.lower():
            fail.append(f"parity {name}.{k}: ts {v} != css {cssv[key]}")
checks = []  # (theme, fg, bg, min, label)
def add(theme, fg, bg, mn, label): checks.append((theme, fg, bg, mn, label))
for theme, t in (("dark", dark), ("light", light)):
    for s in ("bg", "surfaceLow", "surface", "surfaceHigh", "surfaceHigher", "surfaceHighest"):
        for fg in ("text1", "text2", "text3", "accent", "onSurface", "onSurfaceVariant", "outline", "ok", "warn", "info", "error", "pending", "neutral"):
            if theme == "light" and fg == "outline" and s in ("surfaceHigh", "surfaceHigher", "surfaceHighest"):
                add(theme, t[fg], t[s], 3.0, f"{fg} on {s} (non-text 3:1)"); continue
            add(theme, t[fg], t[s], 3.0 if fg == "outline" else 4.5, f"{fg} on {s}")
    add(theme, t["onAccent"], t["accent"], 4.5, "onAccent on accent")
    add(theme, t["onAccentContainer"], t["accentContainer"], 4.5, "onAccentContainer on accentContainer")
    add(theme, t["onVioletContainer"], t["violetContainer"], 4.5, "onVioletContainer on violetContainer")
for theme, fg, bg, mn, label in checks:
    r = cr(fg, bg)
    if r < mn: fail.append(f"contrast {theme} {label}: {r:.2f} < {mn}")
# Brand rule: violet must NOT be used as text/icon colour on base
if cr(dark["violetContainer"], dark["bg"]) >= 3: fail.append("violet unexpectedly passes — recheck rule text")
print(f"{len(checks)} contrast checks; violet-on-base = {cr(dark['violetContainer'], dark['bg']):.2f}:1 (fill/tint only)")
if fail:
    print("\n".join(fail)); sys.exit(1)
print("tokens OK")
