"""Cover pictures for blog posts, drawn from the post's own data (no text, so one picture fits both languages).

tree_cover(): root -> lineages -> branches as a dendrogram on the left, one dot per item on a year axis.
png(): 1200 x 630 PNG of an SVG for link previews (og:image), with headless Chrome if it is installed.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#8C7B00", "#7E57C2", "#5D7087"]  # same order as assets/blog.js
THEMES = {"light": {"bg": "#ffffff", "grid": "#e6e6e6", "text": "#828282", "root": "#1c1c1d"},  # stylesheet.css light / dark surfaces
          "dark": {"bg": "#212529", "grid": "#3a3a3e", "text": "#828282", "root": "#e8e8e8"}}
W, H = 1200, 630


def curve(x1, y1, x2, y2):
    xm = (x1 + x2) / 2
    return f"M{x1:.1f} {y1:.1f}C{xm:.1f} {y1:.1f} {xm:.1f} {y2:.1f} {x2:.1f} {y2:.1f}"


def tree_cover(nodes, items, field, out_light, out_dark, cols=4, step=8.6, r=3.5):
    top = [n for n in nodes if not n["parent"]]
    kids = {t["id"]: [n for n in nodes if n["parent"] == t["id"]] for t in top}
    rows = [k for t in top for k in kids[t["id"]]]
    y0s = [i["year"] for i in items]
    Y0, Y1 = min(y0s), max(y0s)
    X0, X1, T0, T1, gap = 330, 1140, 46, 548, 12
    rh = (T1 - T0 - gap * (len(top) - 1)) / len(rows)
    ys, y = {}, T0
    for t in top:
        for k in kids[t["id"]]:
            ys[k["id"]] = y + rh / 2
            y += rh
        y += gap
    cw = (X1 - X0) / (Y1 - Y0 + 1)
    xof = lambda yr: X0 + (yr - Y0 + 0.5) * cw
    for theme, out in (("light", out_light), ("dark", out_dark)):
        c = THEMES[theme]
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
             f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>']
        for yr in range(Y0, Y1 + 1):
            s.append(f'<line x1="{xof(yr):.1f}" y1="{T0 - 14}" x2="{xof(yr):.1f}" y2="{T1 + 6}" stroke="{c["grid"]}" stroke-width="1"/>')
            if (yr - Y0) % 3 == 0 or yr == Y1:
                s.append(f'<text x="{xof(yr):.1f}" y="{T1 + 40}" fill="{c["text"]}" font-family="system-ui, Segoe UI, Roboto, Arial, sans-serif" '
                         f'font-size="19" font-weight="600" text-anchor="middle">{yr}</text>')
        rx, ry, lx, bx = 62, (T0 + T1) / 2, 160, 262
        for i, t in enumerate(top):
            col = COLORS[i % len(COLORS)]
            ly = sum(ys[k["id"]] for k in kids[t["id"]]) / len(kids[t["id"]])
            s.append(f'<path d="{curve(rx, ry, lx, ly)}" fill="none" stroke="{col}" stroke-width="3" opacity="0.8"/>')
            for k in kids[t["id"]]:
                mine = sorted((it for it in items if it[field] == k["id"]), key=lambda it: it["year"])
                by = {}
                for it in mine:
                    by.setdefault(it["year"], []).append(it)
                by_ = ys[k["id"]]
                s.append(f'<path d="{curve(lx, ly, bx, by_)}" fill="none" stroke="{col}" stroke-width="2" opacity="0.7"/>')
                if mine:
                    s.append(f'<line x1="{bx}" y1="{by_:.1f}" x2="{xof(mine[-1]["year"]):.1f}" y2="{by_:.1f}" stroke="{col}" stroke-width="1.6" opacity="0.35"/>')
                for yr, cell in by.items():
                    nrow = (len(cell) + cols - 1) // cols
                    for j, _ in enumerate(cell):
                        cx = xof(yr) + (j % cols - (min(cols, len(cell)) - 1) / 2) * step
                        cy = by_ + (j // cols - (nrow - 1) / 2) * step
                        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{col}"/>')
                s.append(f'<circle cx="{bx}" cy="{by_:.1f}" r="4.5" fill="{c["bg"]}" stroke="{col}" stroke-width="2.4"/>')
            s.append(f'<circle cx="{lx}" cy="{ly:.1f}" r="8" fill="{col}"/>')
        s.append(f'<circle cx="{rx}" cy="{ry:.1f}" r="12" fill="{c["root"]}"/>')
        s.append("</svg>")
        Path(out).write_text("\n".join(s) + "\n", encoding="utf-8")


def png(svg, out):
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        print("note: no Chrome found; skipped", out)
        return False
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "cover.html"
        page.write_text(f'<!doctype html><html><body style="margin:0"><img src="{Path(svg).resolve().as_uri()}" width="{W}" height="{H}" style="display:block"></body></html>',
                        encoding="utf-8")
        subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp}/profile",
                        f"--window-size={W},{H}", f"--screenshot={Path(out).resolve()}", page.as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    return True


def smooth(points):
    """Path through points with horizontal tangents at each point: smooth, no overshoot, and two layers that share
    points share the exact same edge (so stacked areas never leave gaps)."""
    d = f"{points[0][0]:.1f} {points[0][1]:.1f}"
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        xm = (x1 + x2) / 2
        d += f"C{xm:.1f} {y1:.1f} {xm:.1f} {y2:.1f} {x2:.1f} {y2:.1f}"
    return d


def stack_cover(nodes, items, field, out_light, out_dark):
    """Share of each top-level group per year as stacked areas (for posts with too many items for one dot each)."""
    top = [n for n in nodes if not n["parent"]]
    parent = {n["id"]: n["parent"] or n["id"] for n in nodes}
    years = sorted({i["year"] for i in items})
    X0, X1, T0, T1 = 70, 1130, 46, 540
    xs = [X0 + (X1 - X0) * k / (len(years) - 1) for k in range(len(years))]
    total = {y: sum(1 for i in items if i["year"] == y) for y in years}
    cum, layers = [0.0] * len(years), []
    for idx, t in enumerate(top):
        part = [sum(1 for i in items if i["year"] == y and parent[i[field]] == t["id"]) / total[y] for y in years]
        upper = [c + p for c, p in zip(cum, part)]
        layers.append((t.get("color") or COLORS[idx % len(COLORS)], cum, upper))
        cum = upper
    ypos = lambda f: T1 - f * (T1 - T0)
    for theme, out in (("light", out_light), ("dark", out_dark)):
        c = THEMES[theme]
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">', f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>']
        for col, lower, upper in layers:
            up = list(zip(xs, map(ypos, upper)))
            lo = list(zip(xs, map(ypos, lower)))[::-1]
            s.append(f'<path d="M{smooth(up)}L{smooth(lo)}Z" fill="{col}" stroke="{c["bg"]}" stroke-width="2" stroke-linejoin="round"/>')
        for x, y in zip(xs, years):
            s.append(f'<text x="{x:.1f}" y="{T1 + 44}" fill="{c["text"]}" font-family="system-ui, Segoe UI, Roboto, Arial, sans-serif" '
                     f'font-size="19" font-weight="600" text-anchor="middle">{y}</text>')
        s.append("</svg>")
        Path(out).write_text("\n".join(s) + "\n", encoding="utf-8")
