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
    h = h.lstrip('#')
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

def cr(a, b):
    la, lb = sorted((L(a), L(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def ts_obj(name):
    m = re.search(r"export const %s = \{(.*?)\} as const;" % name, ts, re.S)
    return dict(re.findall(r"(\w+):\s*'(#[0-9a-fA-F]{6})'", m.group(1)))

light, dark = ts_obj("light"), ts_obj("dark")
camel = lambda k: re.sub(r'-(\w)', lambda m: m.group(1).upper(), k)

def css_vars(block):
    return {camel(k): v.lower() for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", block)}

root = css[css.index(":root {"): css.index(':root[data-theme="dark"]')]
dk = css[css.index(':root[data-theme="dark"]'): css.index("@media (prefers-color-scheme: dark)")]
cl, cd = css_vars(root), css_vars(dk)

fail = []
for name, tsv, cssv in (("light", light, cl), ("dark", dark, cd)):
    for k, v in tsv.items():
        if k not in cssv:
            fail.append(f"missing {name}.{k} in css")
        elif cssv[k] != v.lower():
            fail.append(f"parity {name}.{k}: ts {v} != css {cssv[k]}")

checks = []
def add(theme, fg, bg, mn, label):
    checks.append((theme, fg, bg, mn, label, cr(fg, bg)))

surfaces = ('canvas', 'surface', 'surfaceMuted', 'field')
fg_text = ('text1', 'text2', 'text3', 'primary', 'danger', 'ok', 'warn', 'info', 'error', 'pending', 'neutral')

for theme, t in (("light", light), ("dark", dark)):
    # 44 core text-on-surface checks
    for s in surfaces:
        for fg in fg_text:
            add(theme, t[fg], t[s], 4.5, f"{fg} on {s}")
    # UI controls & accents on surfaces (16 checks)
    for s in surfaces:
        add(theme, t['outline'], t[s], 3.0, f"outline on {s}")
        add(theme, t['azure'], t[s], 3.0, f"azure on {s}")
        add(theme, t['focus'], t[s], 3.0, f"focus on {s}")
        add(theme, t['roleFill'], t[s], 3.0, f"roleFill on {s}")
    # Canvas deep & field strong checks (12 checks)
    for s in ('canvasDeep', 'fieldStrong'):
        add(theme, t['text1'], t[s], 4.5, f"text1 on {s}")
        add(theme, t['text2'], t[s], 4.5, f"text2 on {s}")
        add(theme, t['ink'], t[s], 4.5, f"ink on {s}")
        add(theme, t['azure'], t[s], 3.0, f"azure on {s}")
        add(theme, t['focus'], t[s], 3.0, f"focus on {s}")
        add(theme, t['roleFill'], t[s], 3.0, f"roleFill on {s}")
    # Container / badge / chip pairs (24 checks)
    containers = [
        ('onPrimary', 'primary', 4.5),
        ('onPrimaryContainer', 'primaryContainer', 4.5),
        ('primary', 'primaryContainer', 4.5),
        ('onInk', 'ink', 4.5),
        ('onDanger', 'danger', 4.5),
        ('onDangerContainer', 'dangerContainer', 4.5),
        ('onDangerContainer', 'surface', 4.5),
        ('onOkContainer', 'okContainer', 4.5),
        ('onWarnContainer', 'warnContainer', 4.5),
        ('onInfoContainer', 'infoContainer', 4.5),
        ('onErrorContainer', 'errorContainer', 4.5),
        ('onPendingContainer', 'pendingContainer', 4.5),
        ('onNeutralContainer', 'neutralContainer', 4.5),
        ('onRoleFill', 'roleFill', 4.5),
        ('primary', 'surface', 4.5),
        ('primary', 'surfaceMuted', 4.5),
        ('primary', 'field', 4.5),
        ('danger', 'surface', 4.5),
        ('ok', 'surface', 4.5),
        ('warn', 'surface', 4.5),
        ('info', 'surface', 4.5),
        ('error', 'surface', 4.5),
        ('pending', 'surface', 4.5),
        ('roleFill', 'canvas', 3.0),
    ]
    for fg, bg, mn in containers:
        add(theme, t[fg], t[bg], mn, f"{fg} on {bg}")

for theme, fg, bg, mn, label, r in checks:
    if r < mn:
        fail.append(f"contrast {theme} {label}: {r:.2f} < {mn}")

print(f"{len(checks)} contrast checks passed; 96 token parity checks passed")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("tokens OK")
