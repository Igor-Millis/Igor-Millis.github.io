"""Server-rendered SVG charts (no client-side charting library)."""
from __future__ import annotations

import json
import math

from .core import esc, integer, num

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


def reliability(rows: list[dict], lang: str, *, min_n: int = 20) -> str:
    """Reliability diagram: observed default rate vs mean predicted probability per bin,
    with the bin counts as a histogram strip underneath."""
    w, h, l, r, t, b = 640, 400, 44, 16, 14, 96
    ph = h - t - b                      # plot height
    X = lambda v: l + v * (w - l - r)    # noqa: E731
    Y = lambda v: t + (1 - v) * ph       # noqa: E731
    out = []
    for v in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>')
        out.append(f'<text x="{X(v):.1f}" y="{t + ph + 18}" text-anchor="middle">{num(v, lang, 2)}</text>')
    out.append(f'<line class="ax" x1="{l}" x2="{w - r}" y1="{t + ph}" y2="{t + ph}"/>')
    out.append(f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(1)}" y2="{Y(1)}" stroke="var(--text-3)" stroke-dasharray="3 4"/>')
    out.append(f'<text x="{X(0.83):.1f}" y="{Y(0.9):.1f}" text-anchor="end">{"calibração perfeita" if lang == "pt" else "perfect calibration"}</text>')
    shown = [q for q in rows if q["n"] >= min_n]
    d = " ".join(f"{'M' if i == 0 else 'L'}{X(q['mean_p']):.1f},{Y(q['obs']):.1f}" for i, q in enumerate(shown))
    out.append(f'<path class="ln-a" d="{d}"/>')
    nmax = max(q["n"] for q in rows)
    for q in shown:
        rad = 3 + 6 * math.sqrt(q["n"] / nmax)
        out.append(f'<circle cx="{X(q["mean_p"]):.1f}" cy="{Y(q["obs"]):.1f}" r="{rad:.1f}" fill="var(--bg)" stroke="var(--accent)" stroke-width="1.5">'
                   f'<title>p̄ = {num(q["mean_p"], lang, 3)} · obs = {num(q["obs"], lang, 3)} · n = {integer(q["n"], lang)}</title></circle>')
    # histogram strip
    hy, hh = t + ph + 36, 44
    out.append(f'<text x="{l - 8}" y="{hy + 10}" text-anchor="end">n</text>')
    for q in rows:
        x0 = X(q["bin"] / 10) + 2
        bh = max(1.0, hh * q["n"] / nmax)
        out.append(f'<rect class="bar" x="{x0:.1f}" y="{hy + hh - bh:.1f}" width="{(w - l - r) / 10 - 4:.1f}" height="{bh:.1f}"/>'
                   f'<text x="{x0 + (w - l - r) / 20 - 2:.1f}" y="{hy + hh + 14}" text-anchor="middle">{integer(q["n"], lang)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="reliability diagram">{"".join(out)}</svg>'
