"""Server-rendered SVG charts (no client-side charting library)."""
from __future__ import annotations

import json

from .core import esc, num

# Geometry shared with static/js/threshold.js through data attributes.
TH = {"w": 640, "h": 300, "l": 40, "r": 14, "t": 14, "b": 34, "x0": 0.1, "x1": 0.9}


def _x(v: float) -> float:
    g = TH
    return g["l"] + (v - g["x0"]) / (g["x1"] - g["x0"]) * (g["w"] - g["l"] - g["r"])


def _y(v: float) -> float:
    g = TH
    return g["t"] + (1 - v) * (g["h"] - g["t"] - g["b"])


def threshold_chart(curve: list[list[float]], operating: float, lang: str) -> str:
    g = TH
    paths = {}
    for i, cls in ((1, "ln-b"), (2, "ln-c"), (3, "ln-a")):
        d = " ".join(f"{'M' if j == 0 else 'L'}{_x(r[0]):.1f},{_y(r[i]):.1f}" for j, r in enumerate(curve))
        paths[cls] = f'<path class="{cls}" d="{d}"/>'
    grid = ""
    for v in (0, 0.25, 0.5, 0.75, 1):
        y = _y(v)
        grid += f'<line class="gl" x1="{g["l"]}" x2="{g["w"] - g["r"]}" y1="{y:.1f}" y2="{y:.1f}"/>'
        grid += f'<text x="{g["l"] - 8}" y="{y + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>'
    for v in (0.1, 0.3, 0.5, 0.7, 0.9):
        x = _x(v)
        grid += f'<text x="{x:.1f}" y="{g["h"] - 12}" text-anchor="middle">{num(v, lang, 1)}</text>'
    xo = _x(operating)
    op = (
        f'<line x1="{xo:.1f}" x2="{xo:.1f}" y1="{g["t"]}" y2="{g["h"] - g["b"]}" stroke="var(--accent)" '
        f'stroke-width="1" opacity=".45"/>'
        f'<text class="t-accent" x="{xo + 5:.1f}" y="{g["t"] + 10}">τ={num(operating, lang, 2)}</text>'
    )
    base = g["h"] - g["b"]
    axis = f'<line class="ax" x1="{g["l"]}" x2="{g["w"] - g["r"]}" y1="{base}" y2="{base}"/>'
    cursor = (
        f'<g data-cursor><line class="cursor" x1="0" x2="0" y1="{g["t"]}" y2="{base}"/>'
        f'<circle class="pt" r="4" stroke="var(--text-2)" data-p="1"/>'
        f'<circle class="pt" r="4" stroke="var(--signal)" data-p="2"/>'
        f'<circle class="pt" r="4.5" stroke="var(--accent)" data-p="3"/></g>'
    )
    return (
        f'<svg viewBox="0 0 {g["w"]} {g["h"]}" role="img" aria-label="precision, recall and F1 versus threshold" '
        f'data-geom=\'{json.dumps(g)}\'>{grid}{axis}{op}{paths["ln-b"]}{paths["ln-c"]}{paths["ln-a"]}{cursor}</svg>'
    )


def hbars(items: list[list], lang: str, *, digits: int = 3, highlight: int = 1, label_w: int = 110) -> str:
    """Horizontal bar chart. items = [[label, value], ...] sorted desc."""
    w, row, gap = 640, 22, 8
    vmax = max(v for _, v in items)
    plot_w = w - label_w - 70
    h = len(items) * (row + gap)
    out = []
    for i, (label, v) in enumerate(items):
        y = i * (row + gap)
        bw = max(1.0, v / vmax * plot_w)
        cls = "bar hl" if i < highlight else "bar"
        out.append(
            f'<text x="{label_w - 10}" y="{y + 15}" text-anchor="end" class="{"t-strong" if i < highlight else ""}">{esc(label)}</text>'
            f'<rect class="{cls}" x="{label_w}" y="{y + 4}" width="{bw:.1f}" height="{row - 8}"/>'
            f'<text x="{label_w + bw + 8:.1f}" y="{y + 15}">{num(v, lang, digits)}</text>'
        )
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="bar chart">{"".join(out)}</svg>'
