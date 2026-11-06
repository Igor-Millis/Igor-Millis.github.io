"""Components for the research note on the statistics of betting (data from data/bets.json)."""
from __future__ import annotations

import json
import math

from .core import Site, esc, integer, num


def _pct(x: float, lang: str, d: int = 1) -> str:
    return num(100 * x, lang, d) + "%"


def _tbl(cols: list[str], rows: list[list[str]], hl: set[int] = frozenset()) -> str:
    head = "".join(f"<th scope=col>{c}</th>" for c in cols)
    body = "".join(f'<tr{" class=hl" if i in hl else ""}>' + "".join(f"<td>{v}</td>" for v in r) + "</tr>"
                   for i, r in enumerate(rows))
    return f'<div class="tbl-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _panel(head: str, right: str, inner: str, cap: str) -> str:
    return f"""<figure class="panel">
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(head)}</span><span>{esc(right)}</span></div>
  <div class="panel-b chart">{inner}</div>
  <figcaption style="padding:0 18px 16px">{esc(cap)}</figcaption>
</figure>"""


def market(site: Site, lang: str) -> str:
    d = site.data["bets"]["market"]
    pt = lang == "pt"
    names = {"home": "mandante" if pt else "home", "draw": "empate" if pt else "draw", "away": "visitante" if pt else "away"}
    rows = [[names[k], num(d["odds"][k], lang, 2), _pct(d["implied"][k], lang), num(d["fair_odds"][k], lang, 2)] for k in d["odds"]]
    rows.append(["<b>soma</b>" if pt else "<b>sum</b>", "", f"<b>{_pct(d['booksum'], lang)}</b>", ""])
    cols = (["resultado", "odd oferecida", "prob. implícita 1/o", "odd justa"] if pt else
            ["outcome", "offered odds", "implied prob. 1/o", "fair odds"])
    cap = ("Mercado ilustrativo de futebol (1X2), não de uma casa específica. A soma passa de 100%: o excedente é a margem."
           if pt else "Illustrative football 1X2 market, not from a specific bookmaker. The sum exceeds 100%: the excess is the margin.")
    return _tbl(cols, rows, hl={3}) + f'<p class="cap">{esc(cap)}</p>'


def ahead(site: Site, lang: str) -> str:
    d = site.data["bets"]
    pt = lang == "pt"
    rows = []
    for r in d["p_ahead"]:
        ex = r["exact"]
        exs = "&lt; 0,01%" if pt and ex < 1e-4 else ("&lt; 0.01%" if ex < 1e-4 else _pct(ex, lang, 2))
        rows.append([integer(r["n"], lang), exs, num(r["expected_loss"], lang, 1), num(r["two_sd"], lang, 1)])
    cols = (["apostas n", "P(no lucro)", "perda esperada (u)", "±2σ√n (u)"] if pt else
            ["bets n", "P(ahead)", "expected loss (u)", "±2σ√n (u)"])
    hl = {i for i, r in enumerate(d["p_ahead"]) if r["n"] == 2000}
    cap = ("Apostas de 1 unidade a odd 1,91 num evento 50/50. P(no lucro) calculada exatamente pela binomial. "
           "Quando a perda esperada passa de 2σ√n, a sorte já não cobre a margem." if pt else
           "One-unit bets at odds 1.91 on a 50/50 event. P(ahead) computed exactly from the binomial. "
           "Once the expected loss exceeds 2σ√n, luck can no longer cover the margin.")
    return _tbl(cols, rows, hl=hl) + f'<p class="cap">{esc(cap)}</p>'


def parlay(site: Site, lang: str) -> str:
    d = site.data["bets"]
    pt = lang == "pt"
    rows = [[str(r["legs"]), _pct(r["ev"], lang)] for r in d["parlay"]]
    cols = ["seleções k", "valor esperado por real apostado"] if pt else ["legs k", "expected value per unit staked"]
    cap = (f"Cada seleção com a margem do mercado acima ({_pct(d['market']['overround'], lang)}). A margem se multiplica."
           if pt else f"Each leg priced with the margin of the market above ({_pct(d['market']['overround'], lang)}). The margin compounds.")
    return _tbl(cols, rows, hl={3}) + f'<p class="cap">{esc(cap)}</p>'


def ruin(site: Site, lang: str) -> str:
    d = site.data["bets"]
    pt = lang == "pt"
    rows = []
    for r in d["ruin"]:
        pd = r["p_double"]
        pds = ("&lt; 0,01%" if pt else "&lt; 0.01%") if pd < 1e-4 else _pct(pd, lang, 2)
        rows.append([num(r["p"], lang, 3), _pct(r["edge"], lang), pds, _pct(1 - pd, lang, 2) if pd >= 1e-4 else "≈ 100%"])
    cols = (["p de vitória", "vantagem por aposta", "P(dobrar 50 → 100)", "P(quebrar)"] if pt else
            ["win prob. p", "edge per bet", "P(double 50 → 100)", "P(ruin)"])
    cap = ("Apostas de 1 unidade a odd 2,00, começando com 50 unidades e parando em 100 ou em 0 (ruína do jogador)."
           if pt else "One-unit bets at odds 2.00, starting with 50 units, stopping at 100 or at 0 (gambler's ruin).")
    return _tbl(cols, rows, hl={3}) + f'<p class="cap">{esc(cap)}</p>'


def lln(site: Site, lang: str) -> str:
    d = site.data["bets"]
    L = d["lln"]
    pt = lang == "pt"
    w, h, l, r, t, b = 640, 320, 48, 16, 14, 34
    y0, y1 = -0.35, 0.25
    lx = lambda n: l + math.log10(n) / 4 * (w - l - r)          # noqa: E731
    Y = lambda v: t + (y1 - v) / (y1 - y0) * (h - t - b)          # noqa: E731
    out = [f'<defs><clipPath id="clip-lln"><rect x="{l}" y="{t}" width="{w - l - r}" height="{h - t - b}"/></clipPath></defs>']
    for v in (-0.3, -0.2, -0.1, 0, 0.1, 0.2):
        cls = "ax" if v == 0 else "gl"
        out.append(f'<line class="{cls}" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{_pct(v, lang, 0)}</text>')
    for n in (1, 10, 100, 1000, 10000):
        out.append(f'<text x="{lx(n):.1f}" y="{h - 12}" text-anchor="middle">{integer(n, lang)}</text>')
    band = L["band"]
    poly = " ".join(f"{lx(n):.1f},{Y(hi):.1f}" for n, lo, hi in band) + " " + " ".join(
        f"{lx(n):.1f},{Y(lo):.1f}" for n, lo, hi in reversed(band))
    g = [f'<polygon points="{poly}" fill="var(--accent)" opacity=".10"/>']
    for p in L["paths"]:
        pts = " ".join(f"{lx(n):.1f},{Y(v):.1f}" for n, v in zip(L["n"], p))
        g.append(f'<polyline points="{pts}" fill="none" stroke="var(--text-3)" stroke-width="1" opacity=".55"/>')
    mu = d["mu"]
    g.append(f'<line x1="{l}" x2="{w - r}" y1="{Y(mu):.1f}" y2="{Y(mu):.1f}" stroke="var(--accent)" stroke-width="1.75"/>')
    out.append(f'<g clip-path="url(#clip-lln)">{"".join(g)}</g>')
    out.append(f'<text class="t-accent" x="{w - r - 4}" y="{Y(mu) + 16:.1f}" text-anchor="end">μ = {_pct(mu, lang)}</text>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="law of large numbers">{"".join(out)}</svg>'
    head = ("retorno médio por aposta · 24 apostadores simulados" if pt else "average return per bet · 24 simulated bettors")
    right = "x: n (log)"
    cap = (f"Cada linha cinza é um apostador; a faixa é μ ± 2σ/√n. Depois de 10.000 apostas, os 24 estão no prejuízo "
           f"(média {_pct(L['final_mean'], lang)}). Simulação com semente fixa: research/bets/bets.py." if pt else
           f"Each grey line is one bettor; the band is μ ± 2σ/√n. After 10,000 bets all 24 are behind "
           f"(mean {_pct(L['final_mean'], lang)}). Seeded simulation: research/bets/bets.py.")
    return _panel(head, right, svg, cap)


def simulator(site: Site, lang: str) -> str:
    pt = lang == "pt"
    labels = {
        "head": "simulador · 200 apostadores, 1 unidade por aposta" if pt else "simulator · 200 bettors, 1 unit per bet",
        "margin": "margem da casa" if pt else "house margin",
        "n": "apostas por pessoa" if pt else "bets per person",
        "rerun": "sortear de novo" if pt else "re-run",
        "keys": (["no lucro ao final", "resultado médio", "esperado nμ", "pior / melhor"] if pt else
                 ["ahead at the end", "mean result", "expected nμ", "worst / best"]),
        "cap": ("Odd = 2/(1 + margem) num evento 50/50. As linhas são 40 dos 200 apostadores; a faixa é nμ ± 2σ√n. Roda no seu navegador."
                if pt else "Odds = 2/(1 + margin) on a 50/50 event. Lines are 40 of the 200 bettors; the band is nμ ± 2σ√n. Runs in your browser."),
    }
    reads = "".join(f'<div><div class="v" data-o="{i}">—</div><div class="k">{esc(k)}</div></div>'
                    for i, k in enumerate(labels["keys"]))
    cfg = json.dumps({"lang": lang})
    return f"""<figure class="panel" data-bets='{cfg}'>
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(labels['head'])}</span><button type="button" class="btn-ghost" data-rerun>↻ {esc(labels['rerun'])}</button></div>
  <div class="panel-b">
    <div class="th-ctrl"><label class="label" for="bm-{lang}" style="min-width:150px">{esc(labels['margin'])}</label><input id="bm-{lang}" type="range" min="0" max="15" step="0.5" value="4.5" data-m><output data-mo>4,5%</output></div>
    <div class="th-ctrl"><label class="label" for="bn-{lang}" style="min-width:150px">{esc(labels['n'])}</label><input id="bn-{lang}" type="range" min="0" max="100" step="1" value="70" data-n><output data-no>—</output></div>
    <div class="chart"><svg viewBox="0 0 640 300" role="img" aria-label="bankroll simulation" data-svg></svg></div>
    <div class="th-read" style="grid-template-columns:repeat(4,minmax(0,1fr))">{reads}</div>
  </div>
  <figcaption style="padding:0 18px 16px">{esc(labels['cap'])}</figcaption>
</figure>"""


COMPONENTS = {
    "bets-market": market, "bets-ahead": ahead, "bets-parlay": parlay, "bets-ruin": ruin,
    "bets-lln": lln, "bets-sim": simulator,
}
