"""Components for the research note on the non-parametric vs parametric bootstrap (data from data/bootstrap.json)."""
from __future__ import annotations

import json
import math

from .core import Site, esc, integer, num


def _pct(x: float, lang: str, d: int = 1) -> str:
    return num(100 * x, lang, d) + "%"


def _iv(a: list[float], lang: str, d: int = 2) -> str:
    return f"[{num(a[0], lang, d)}; {num(a[1], lang, d)}]" if lang == "pt" else f"[{num(a[0], lang, d)}, {num(a[1], lang, d)}]"


def _tbl(cols: list[str], rows: list[list[str]], hl: set[int] = frozenset()) -> str:
    head = "".join(f"<th scope=col>{c}</th>" for c in cols)
    body = "".join(f'<tr{" class=hl" if i in hl else ""}>' + "".join(f"<td>{v}</td>" for v in r) + "</tr>"
                   for i, r in enumerate(rows))
    return f'<div class="tbl-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _cap(text: str) -> str:
    return f'<p class="cap">{text}</p>'


def _panel(head: str, right: str, inner: str, cap: str, legend: str = "") -> str:
    return f"""<figure class="panel">
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(head)}</span><span>{esc(right)}</span></div>
  <div class="panel-b chart">{legend}{inner}</div>
  <figcaption style="padding:0 18px 16px">{cap}</figcaption>
</figure>"""


def _legend(items: list[tuple[str, str, str]]) -> str:
    """items = [(label, color, style)] with style 'solid' | 'dash' | 'block'."""
    out = []
    for label, color, style in items:
        if style == "block":
            sw = f'style="background:{color};height:8px;opacity:.55"'
        elif style == "dash":
            sw = f'style="background:repeating-linear-gradient(90deg,{color} 0 4px,transparent 4px 7px)"'
        else:
            sw = f'style="background:{color}"'
        out.append(f"<span><i {sw}></i>{label}</span>")
    return f'<div class="legend">{"".join(out)}</div>'


# ------------------------------------------------------------------ diagram: real world vs bootstrap world
def worlds(site: Site, lang: str) -> str:
    pt = lang == "pt"
    M = lambda tex: "\\(" + tex + "\\)"       # noqa: E731
    t = {
        "real": "mundo real" if pt else "real world",
        "boot": "mundo bootstrap" if pt else "bootstrap world",
        "draw": "sorteio" if pt else "draw",
        "calc": "cálculo" if pt else "compute",
    }
    real = [M("F") + (" — desconhecida" if pt else " — unknown"),
            M(r"\mathbf x = (x_1, \dots, x_n)") + (" — uma amostra" if pt else " — one sample"),
            M(r"\hat\theta = s(\mathbf x)") + (" — um número" if pt else " — one number")]
    boot = [M(r"\hat F") + (" — estimada a partir de " if pt else " — estimated from ") + M(r"\mathbf x"),
            M(r"\mathbf x^{*1}, \dots, \mathbf x^{*B}") + (" — B amostras" if pt else " — B samples"),
            M(r"\hat\theta^{*1}, \dots, \hat\theta^{*B}") + (" — uma distribuição" if pt else " — a distribution")]

    def col(title: str, boxes: list[str], cls: str) -> str:
        inner = ""
        for i, b in enumerate(boxes):
            inner += f'<div class="box">{b}</div>'
            if i < 2:
                inner += f'<div class="step">↓ {t["draw"] if i == 0 else t["calc"]}</div>'
        return f'<div class="{cls}"><p class="wt">{title}</p>{inner}</div>'

    foot = ("<p>▸ <b>não paramétrico:</b> " + M(r"\hat F = F_n") + ", a distribuição empírica (a própria amostra)</p>"
            "<p>▸ <b>paramétrico:</b> " + M(r"\hat F = F_{\hat\eta}") + ", um modelo com parâmetros estimados</p>" if pt else
            "<p>▸ <b>non-parametric:</b> " + M(r"\hat F = F_n") + ", the empirical distribution (the sample itself)</p>"
            "<p>▸ <b>parametric:</b> " + M(r"\hat F = F_{\hat\eta}") + ", a model with estimated parameters</p>")
    inner = (f'<div class="worlds">{col(t["real"], real, "real")}{col(t["boot"], boot, "boot")}</div>'
             f'<div class="worlds-foot">{foot}</div>')
    head = "o princípio do bootstrap" if pt else "the bootstrap principle"
    cap = ("A pergunta é sempre a mesma: como " + M(r"\hat\theta") + " varia de amostra para amostra? No mundo real só vemos "
           "uma amostra. No mundo bootstrap, " + M(r"\hat F") + " faz o papel de " + M("F") + " e podemos sortear quantas "
           "amostras quisermos. A única diferença entre os dois bootstraps é a escolha de " + M(r"\hat F") + "." if pt else
           "The question is always the same: how does " + M(r"\hat\theta") + " vary from sample to sample? In the real world "
           "we see one sample. In the bootstrap world " + M(r"\hat F") + " plays the role of " + M("F") + " and we can draw as "
           "many samples as we like. The only difference between the two bootstraps is the choice of " + M(r"\hat F") + ".")
    return _panel(head, "plug-in", inner, cap)


# ------------------------------------------------------------------ toy example table
def toy(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["toy"]
    pt = lang == "pt"
    f1 = lambda v: num(v, lang, 1)        # noqa: E731
    rows = [["<b>" + ("original" if pt else "original") + "</b>", "1, 2, 3, 4, 5", ", ".join(f1(v) for v in d["x"]),
             f"<b>{num(d['mean'], lang, 2)}</b>", f"<b>{f1(d['median'])}</b>"]]
    for i, r in enumerate(d["np"], 1):
        rows.append([f"NP {i}", ", ".join(str(j) for j in r["idx"]), ", ".join(f1(v) for v in r["x"]),
                     num(r["mean"], lang, 2), f1(r["median"])])
    for i, r in enumerate(d["p"], 1):
        rows.append([f"P {i}", "—", ", ".join(f1(v) for v in r["x"]), num(r["mean"], lang, 2), f1(r["median"])])
    cols = (["amostra", "índices sorteados", "valores", "média", "mediana"] if pt else
            ["sample", "drawn indices", "values", "mean", "median"])
    cap = ("NP = não paramétrico: sorteio com reposição dos índices 1–5. P = paramétrico: sorteio de uma Exponencial com média "
           f"{num(d['mean'], lang, 1)} (a média da amostra), arredondado a uma casa. Note que NP só repete valores observados; "
           "P gera valores novos (11,1 nunca foi observado)." if pt else
           "NP = non-parametric: indices 1–5 drawn with replacement. P = parametric: draws from an Exponential with mean "
           f"{num(d['mean'], lang, 1)} (the sample mean), rounded to one decimal. NP only repeats observed values; "
           "P produces new ones (11.1 was never observed).")
    return _tbl(cols, rows, hl={0}) + _cap(cap)


# ------------------------------------------------------------------ ECDF vs fitted exponential
def cdf(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["worked"]
    pt = lang == "pt"
    c = d["cdf"]
    w, h, l, r, t, b = 640, 300, 40, 16, 12, 44
    xmax = 14.0
    X = lambda v: l + v / xmax * (w - l - r)          # noqa: E731
    Y = lambda v: t + (1 - v) * (h - t - b)           # noqa: E731
    out = []
    for v in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>')
    for v in range(0, 15, 2):
        out.append(f'<text x="{X(v):.1f}" y="{h - b + 18}" text-anchor="middle">{v}</text>')
    out.append(f'<text x="{w - r}" y="{h - 6}" text-anchor="end">{"minutos" if pt else "minutes"}</text>')
    for key, cls in (("true", "ln-b"), ("fit", "ln-c")):
        pts = " ".join(f"{X(g):.1f},{Y(v):.1f}" for g, v in zip(c["grid"], c[key]) if g <= xmax)
        out.append(f'<polyline class="{cls}" points="{pts}"/>')
    xs = sorted(c["data"])
    n = len(xs)
    path = f"M{X(0):.1f},{Y(0):.1f}"
    for i, v in enumerate(xs):
        path += f" H{X(v):.1f} V{Y((i + 1) / n):.1f}"
    path += f" H{X(xmax):.1f}"
    out.append(f'<path class="ln-a" d="{path}"/>')
    for v in xs:
        out.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{h - b + 2}" y2="{h - b + 8}" stroke="var(--accent)" stroke-width="1.5"/>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="empirical CDF and fitted exponential">{"".join(out)}</svg>'
    lg = _legend([("\\(F_n\\) — ECDF (bootstrap NP)" if pt else "\\(F_n\\) — ECDF (NP bootstrap)", "var(--accent)", "solid"),
                  (f"Exp(média {num(d['mean'], lang, 1)}) — ajustada (bootstrap P)" if pt else
                   f"Exp(mean {num(d['mean'], lang, 1)}) — fitted (P bootstrap)", "var(--signal)", "solid"),
                  ("Exp(média 4) — verdadeira" if pt else "Exp(mean 4) — true", "var(--text-2)", "dash")])
    head = "as duas estimativas de F" if pt else "the two estimates of F"
    cap = (f"\\(F_n\\) dá peso 1/{n} a cada observação (os tracinhos no eixo) e é uma escada; a exponencial ajustada é suave e "
           f"usa só um número, \\(\\bar x\\) = {num(d['mean'], lang, 1)}. Distância máxima entre as duas (Kolmogorov–Smirnov): "
           f"{num(d['ks_fit'], lang, 3)}." if pt else
           f"\\(F_n\\) puts weight 1/{n} on each observation (the ticks on the axis) and is a staircase; the fitted exponential is smooth "
           f"and uses one number, \\(\\bar x\\) = {num(d['mean'], lang, 1)}. Maximum distance between them (Kolmogorov–Smirnov): "
           f"{num(d['ks_fit'], lang, 3)}.")
    return _panel(head, "n = " + str(n), svg, cap, lg)


# ------------------------------------------------------------------ bootstrap distributions (small multiples)
def _hist_rows(rows: list[tuple[str, list[float], str]], true: list[float], lo: float, hi: float,
               marks: list[tuple[float, str, str]], lang: str, ymax: float | None = None, xlabel: str = "",
               ticks: tuple[list[float], int] | None = None) -> str:
    w, l, r, rowh, gap, b = 640, 120, 16, 92, 14, 30
    bins = len(true)
    h = len(rows) * (rowh + gap) + b
    X = lambda v: l + (v - lo) / (hi - lo) * (w - l - r)        # noqa: E731
    bw = (w - l - r) / bins
    ymax = ymax or max(max(rr[1]) for rr in rows) * 1.05
    out = []
    for i, (label, dens, color) in enumerate(rows):
        y0 = i * (rowh + gap)
        base = y0 + rowh
        Y = lambda v: base - min(v, ymax) / ymax * (rowh - 6)   # noqa: E731,B023
        out.append(f'<text x="{l - 12}" y="{y0 + rowh / 2 + 4:.0f}" text-anchor="end" class="t-strong">{esc(label)}</text>')
        out.append(f'<line class="ax" x1="{l}" x2="{w - r}" y1="{base}" y2="{base}"/>')
        for j, v in enumerate(dens):
            if v > 0:
                out.append(f'<rect x="{X(lo) + j * bw + 0.5:.1f}" y="{Y(v):.1f}" width="{bw - 1:.1f}" height="{base - Y(v):.1f}" '
                           f'fill="{color}" opacity=".55"/>')
        step = f"M{X(lo):.1f},{base}"
        for j, v in enumerate(true):
            step += f" V{Y(v):.1f} H{X(lo) + (j + 1) * bw:.1f}"
        step += f" V{base}"
        out.append(f'<path d="{step}" fill="none" stroke="var(--text-2)" stroke-width="1" stroke-dasharray="3 2"/>')
        for v, color2, lab in marks:
            out.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{y0 + 2}" y2="{base}" stroke="{color2}" stroke-width="1.25"/>')
            if i == 0 and lab:
                out.append(f'<text x="{X(v) + 4:.1f}" y="{y0 + 10}" style="fill:{color2}">{esc(lab)}</text>')
    yb = len(rows) * (rowh + gap) - gap
    vals, dig = ticks or (list(range(int(math.ceil(lo)), int(hi) + 1)), 0)
    for v in vals:
        out.append(f'<text x="{X(v):.1f}" y="{yb + 18}" text-anchor="middle">{num(v, lang, dig)}</text>')
    if xlabel:
        out.append(f'<text x="{w - r}" y="{yb + 18}" text-anchor="end">{esc(xlabel)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="bootstrap distributions">{"".join(out)}</svg>'


def _dist_fig(site: Site, lang: str, stat: str) -> str:
    d = site.data["bootstrap"]["worked"]
    s = d["stats"][stat]
    pt = lang == "pt"
    H = s["hist"]
    lo, hi = H["lo"], H["hi"]
    rows = [("NP · ECDF", H["np"], "var(--accent)"), ("P · Exp(" + num(d["mean"], lang, 1) + ")", H["p"], "var(--signal)")]
    true_v = d["mu_true"] if stat == "mean" else s["true_value"]
    marks = [(s["est"], "var(--text)", ("observado " if pt else "observed ") + num(s["est"], lang, 1)),
             (true_v, "var(--text-3)", "")]
    svg = _hist_rows(rows, H["true"], lo, hi, marks, lang)
    name = ("média" if pt else "mean") if stat == "mean" else ("mediana" if pt else "median")
    lg = _legend([("bootstrap NP", "var(--accent)", "block"), ("bootstrap P", "var(--signal)", "block"),
                  ("distribuição amostral verdadeira" if pt else "true sampling distribution", "var(--text-2)", "dash")])
    head = (f"distribuição bootstrap da {name} · B = {integer(d['B'], lang)}" if pt else
            f"bootstrap distribution of the {name} · B = {integer(d['B'], lang)}")
    if stat == "mean":
        cap = ("A linha tracejada é a distribuição verdadeira de \\(\\bar x\\) quando os dados vêm de Exp(média 4) — algo que só conhecemos "
               "porque a simulação foi nossa. Linha cinza: o valor verdadeiro \\(\\mu = 4\\)." if pt else
               "The dashed outline is the true distribution of \\(\\bar x\\) when the data come from Exp(mean 4) — known only because we "
               "ran the simulation. Grey line: the true value \\(\\mu = 4\\).")
    else:
        cap = (f"O bootstrap NP da mediana só assume {s['distinct_np']} valores diferentes (os dados do meio da amostra), daí as "
               f"barras isoladas. O P é suave, mas centrado em \\(\\bar x \\ln 2\\) = {num(s['mle_plugin'], lang, 2)}, não na mediana "
               f"observada. Linha cinza: a mediana verdadeira \\(4 \\ln 2\\) = {num(s['true_value'], lang, 2)}." if pt else
               f"The NP bootstrap of the median takes only {s['distinct_np']} distinct values (the middle data points), hence the "
               f"isolated bars. The P one is smooth but centred at \\(\\bar x \\ln 2\\) = {num(s['mle_plugin'], lang, 2)}, not at the observed "
               f"median. Grey line: the true median \\(4 \\ln 2\\) = {num(s['true_value'], lang, 2)}.")
    return _panel(head, "x: min", svg, cap, lg)


def dist_mean(site: Site, lang: str) -> str:
    return _dist_fig(site, lang, "mean")


def dist_median(site: Site, lang: str) -> str:
    return _dist_fig(site, lang, "median")


def worked_table(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["worked"]
    pt = lang == "pt"
    rows = []
    for stat in ("mean", "median"):
        s = d["stats"][stat]
        name = ("média" if pt else "mean") if stat == "mean" else ("mediana" if pt else "median")
        rows.append([f"<b>{name}</b>", f"<b>{num(s['est'], lang, 2)}</b>", "", ""])
        rows.append(["&nbsp;&nbsp;" + ("erro-padrão" if pt else "standard error"),
                     num(s["se_true"], lang, 2), num(s["se_np"], lang, 2), num(s["se_p"], lang, 2)])
        rows.append(["&nbsp;&nbsp;" + ("viés" if pt else "bias"),
                     *(num(round(v, 2) + 0.0, lang, 2) for v in (s["bias_true"], s["bias_np"], s["bias_p"]))])
        rows.append(["&nbsp;&nbsp;" + ("IC 95% percentil" if pt else "95% CI percentile"), "—",
                     _iv(s["pct_np"], lang), _iv(s["pct_p"], lang)])
        rows.append(["&nbsp;&nbsp;" + ("IC 95% básico" if pt else "95% CI basic"), "—",
                     _iv(s["basic_np"], lang), _iv(s["basic_p"], lang)])
    cols = (["", "verdade (simulada)", "bootstrap NP", "bootstrap P"] if pt else
            ["", "truth (simulated)", "NP bootstrap", "P bootstrap"])
    m = d["stats"]["mean"]
    cap = (f"Dados: os 15 tempos acima. Verdade = 100.000 amostras novas de Exp(média 4). Para comparar: \\(s/\\sqrt n\\) = "
           f"{num(m['se_formula'], lang, 3)}; o valor exato do NP com \\(B \\to \\infty\\) é \\(\\sqrt{{(n-1)/n}}\\; s/\\sqrt n\\) = {num(m['se_np_ideal'], lang, 3)}; "
           f"o do P é \\(\\bar x/\\sqrt n\\) = {num(m['se_p_ideal'], lang, 3)}; o verdadeiro é \\(4/\\sqrt{{15}}\\) = {num(m['se_true_exact'], lang, 3)}. "
           f"IC t de Student: {_iv(m['t_interval'], lang)}. IC exato do modelo exponencial (pivô \\(\\bar x/\\mu \\sim \\text{{Gama}}(n,1)/n\\)): "
           f"{_iv(m['exact_pivot'], lang)}." if pt else
           f"Data: the 15 times above. Truth = 100,000 fresh samples from Exp(mean 4). For comparison: \\(s/\\sqrt n\\) = "
           f"{num(m['se_formula'], lang, 3)}; the exact NP value as \\(B \\to \\infty\\) is \\(\\sqrt{{(n-1)/n}}\\; s/\\sqrt n\\) = {num(m['se_np_ideal'], lang, 3)}; "
           f"the P value is \\(\\bar x/\\sqrt n\\) = {num(m['se_p_ideal'], lang, 3)}; the true one is \\(4/\\sqrt{{15}}\\) = {num(m['se_true_exact'], lang, 3)}. "
           f"Student t CI: {_iv(m['t_interval'], lang)}. Exact CI under the exponential model (pivot \\(\\bar x/\\mu \\sim \\text{{Gamma}}(n,1)/n\\)): "
           f"{_iv(m['exact_pivot'], lang)}.")
    return _tbl(cols, rows, hl={0, 5}) + _cap(cap)


# ------------------------------------------------------------------ choosing B
def b_table(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["b_choice"]
    pt = lang == "pt"
    rows = [[integer(r["B"], lang), num(r["se_mean"], lang, 3), num(r["se_sd"], lang, 3), _pct(r["se_cv"], lang),
             num(r["lo_sd"], lang, 3)] for r in d["rows"]]
    cols = (["B", "média de \\(\\widehat{\\mathrm{se}}_B\\)", "desvio de \\(\\widehat{\\mathrm{se}}_B\\)", "erro relativo", "desvio do limite 2,5%"] if pt else
            ["B", "mean of \\(\\widehat{\\mathrm{se}}_B\\)", "sd of \\(\\widehat{\\mathrm{se}}_B\\)", "relative error", "sd of the 2.5% endpoint"])
    hl = {i for i, r in enumerate(d["rows"]) if r["B"] == 2000}
    cap = (f"Bootstrap NP da média dos 15 tempos, repetido {d['reps']} vezes para cada B. O alvo (B → ∞) é "
           f"{num(d['ideal_se'], lang, 3)}. O erro de Monte Carlo cai como \\(1/\\sqrt B\\); o dos quantis cai bem mais devagar que o do "
           "erro-padrão, porque um quantil de 2,5% depende de poucas reamostras na cauda." if pt else
           f"NP bootstrap of the mean of the 15 times, repeated {d['reps']} times for each B. The target (B → ∞) is "
           f"{num(d['ideal_se'], lang, 3)}. Monte Carlo error falls like \\(1/\\sqrt B\\); for quantiles it falls much more slowly than for "
           "the standard error, because a 2.5% quantile depends on the few resamples in the tail.")
    return _tbl(cols, rows, hl=hl) + _cap(cap)


# ------------------------------------------------------------------ coverage study
LABELS = {
    "pt": {"np_pct": "NP percentil", "np_basic": "NP básico", "np_t": "NP bootstrap-t", "np_bca": "NP BCa",
           "p_pct": "P percentil", "p_basic": "P básico", "classic_t": "t de Student"},
    "en": {"np_pct": "NP percentile", "np_basic": "NP basic", "np_t": "NP bootstrap-t", "np_bca": "NP BCa",
           "p_pct": "P percentile", "p_basic": "P basic", "classic_t": "Student t"},
}


def coverage_chart(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["coverage"]
    pt = lang == "pt"
    lab = LABELS[lang]
    series = [("np_pct", "var(--accent)", ""), ("np_t", "var(--accent)", "4 3"),
              ("p_pct", "var(--signal)", ""), ("classic_t", "var(--text-3)", "2 3")]
    w, h, t, b = 640, 300, 26, 34
    pw, gap, l0 = 270, 50, 44
    y0, y1 = 0.75, 1.0
    ns = [r["n"] for r in d["right"]]
    lmin, lmax = math.log(ns[0]), math.log(ns[-1])
    Y = lambda v: t + (y1 - v) / (y1 - y0) * (h - t - b)        # noqa: E731
    out = []
    for k, (key, title) in enumerate((("right", "modelo certo · dados Exp" if pt else "model right · Exp data"),
                                      ("wrong", "modelo errado · dados lognormais" if pt else "model wrong · lognormal data"))):
        l = l0 + k * (pw + gap)
        X = lambda n, l=l: l + (math.log(n) - lmin) / (lmax - lmin) * (pw - 10)   # noqa: E731
        out.append(f'<text x="{l}" y="12" class="t-strong">{esc(title)}</text>')
        for v in (0.75, 0.8, 0.85, 0.9, 0.95, 1.0):
            out.append(f'<line class="gl" x1="{l}" x2="{l + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>')
            out.append(f'<text x="{l - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{_pct(v, lang, 0)}</text>')
        se2 = 2 * d["mc_se"]
        out.append(f'<rect x="{l}" y="{Y(0.95 + se2):.1f}" width="{pw}" height="{Y(0.95 - se2) - Y(0.95 + se2):.1f}" '
                   f'fill="var(--text-3)" opacity=".12"/>')
        out.append(f'<line x1="{l}" x2="{l + pw}" y1="{Y(0.95):.1f}" y2="{Y(0.95):.1f}" stroke="var(--text-2)" stroke-width="1"/>')
        for n in ns:
            out.append(f'<text x="{X(n):.1f}" y="{h - b + 18}" text-anchor="middle">{n}</text>')
        for m, color, dash in series:
            pts = " ".join(f"{X(r['n']):.1f},{Y(max(r[m], y0)):.1f}" for r in d[key])
            da = f' stroke-dasharray="{dash}"' if dash else ""
            out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.75"{da}/>')
            for r in d[key]:
                out.append(f'<circle cx="{X(r["n"]):.1f}" cy="{Y(max(r[m], y0)):.1f}" r="2.6" fill="{color}">'
                           f'<title>{esc(lab[m])} · n = {r["n"]} · {_pct(r[m], lang)}</title></circle>')
        if key == "wrong":
            a = d["asymptotic_p_cov_wrong"]
            out.append(f'<line x1="{l}" x2="{l + pw}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" stroke="var(--signal)" stroke-width="1" opacity=".5" stroke-dasharray="1 3"/>'
                       f'<text x="{l + pw}" y="{Y(a) + 14:.1f}" text-anchor="end" style="fill:var(--signal)">{"limite P" if pt else "P limit"} {_pct(a, lang)}</text>')
    out.append(f'<text x="{w - 16}" y="{h - 4}" text-anchor="end">n (log)</text>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="coverage of 95% intervals versus sample size">{"".join(out)}</svg>'
    lg = _legend([(lab["np_pct"], "var(--accent)", "solid"), (lab["np_t"], "var(--accent)", "dash"),
                  (lab["p_pct"], "var(--signal)", "solid"), (lab["classic_t"], "var(--text-3)", "dash")])
    head = "cobertura real de ICs de 95% para a média" if pt else "actual coverage of 95% intervals for the mean"
    cap = (f"{integer(d['M'], lang)} amostras por ponto, B = {d['B']} reamostras cada. A faixa cinza é 95% ± 2 erros de "
           f"Monte Carlo (± {num(200 * d['mc_se'], lang, 1)} p.p.). Modelo paramétrico usado nos dois painéis: exponencial." if pt else
           f"{integer(d['M'], lang)} samples per point, B = {d['B']} resamples each. The grey band is 95% ± 2 Monte Carlo errors "
           f"(± {num(200 * d['mc_se'], lang, 1)} pp). Parametric model used in both panels: exponential.")
    return _panel(head, "y: " + ("cobertura" if pt else "coverage"), svg, cap, lg)


def coverage_table(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["coverage"]
    pt = lang == "pt"
    lab = LABELS[lang]
    ns = [r["n"] for r in d["right"]]
    out = ""
    for key, title in (("right", "Modelo certo (dados exponenciais)" if pt else "Model right (exponential data)"),
                       ("wrong", "Modelo errado (dados lognormais, modelo exponencial)" if pt else
                        "Model wrong (lognormal data, exponential model)")):
        rows = []
        for m in d["methods"]:
            rows.append([lab[m]] + [f"{_pct(r[m], lang)} <span class=muted>· {num(r['w_' + m], lang, 2)}</span>" for r in d[key]])
        cols = [esc(title)] + [f"n = {n}" for n in ns]
        out += _tbl(cols, rows)
    cap = ("Cada célula: cobertura · largura média do intervalo (em unidades da média verdadeira). Um intervalo só é bom se "
           "cobrir perto de 95% — largura menor com cobertura baixa não é virtude." if pt else
           "Each cell: coverage · mean interval width (in units of the true mean). An interval is only good if it covers close "
           "to 95% — a narrower interval with low coverage is not a virtue.")
    return out + _cap(cap)


# ------------------------------------------------------------------ maximum of a uniform
def max_fig(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["maximum"]
    s = d["single"]
    pt = lang == "pt"
    rows = [("NP · ECDF", s["np"], "var(--accent)"), ("P · U(0, máx)" if pt else "P · U(0, max)", s["p"], "var(--signal)")]
    marks = [(s["max"], "var(--text)", ("máx = " if pt else "max = ") + num(s["max"], lang, 3)), (1.0, "var(--text-3)", "")]
    svg = _hist_rows(rows, s["true"], s["lo"], s["hi"], marks, lang, ymax=60,
                     ticks=([0.80, 0.85, 0.90, 0.95, 1.0], 2))
    lg = _legend([("bootstrap NP", "var(--accent)", "block"), ("bootstrap P", "var(--signal)", "block"),
                  ("distribuição amostral verdadeira" if pt else "true sampling distribution", "var(--text-2)", "dash")])
    head = ("máximo de uma Uniforme(0, 1), n = 30" if pt else "maximum of a Uniform(0, 1), n = 30")
    cap = (f"No NP, {_pct(s['p_tie_np'], lang)} das reamostras devolvem exatamente o máximo observado (teoria: \\(1 - (1 - 1/n)^n\\) = "
           f"{_pct(s['p_tie_theory'], lang)}); a barra está cortada. O resto cai nos outros pontos observados. O P é contínuo e "
           "tem a forma certa — só que deslocado para a esquerda, porque \\(\\hat\\theta \\lt \\theta\\) sempre." if pt else
           f"In the NP bootstrap, {_pct(s['p_tie_np'], lang)} of resamples return exactly the observed maximum (theory: "
           f"\\(1 - (1 - 1/n)^n\\) = {_pct(s['p_tie_theory'], lang)}); the bar is clipped. The rest fall on other observed points. "
           "The P one is continuous and has the right shape — just shifted left, because \\(\\hat\\theta \\lt \\theta\\) always.")
    return _panel(head, "θ = 1", svg, cap, lg)


def max_table(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["maximum"]
    pt = lang == "pt"
    c = d["coverage"]
    names = {
        "np_pct": ("NP percentil", "NP percentile"), "np_basic": ("NP básico", "NP basic"),
        "p_pct": ("P percentil", "P percentile"), "p_basic": ("P básico", "P basic"),
        "p_pivot": ("P pivô \\(\\hat\\theta^*/\\hat\\theta\\)", "P pivot \\(\\hat\\theta^*/\\hat\\theta\\)"),
    }
    why = {
        "np_pct": ("todo \\(\\hat\\theta^* \\le \\hat\\theta \\lt \\theta\\): o intervalo nunca alcança \\(\\theta\\)", "every \\(\\hat\\theta^* \\le \\hat\\theta \\lt \\theta\\): the interval never reaches \\(\\theta\\)"),
        "np_basic": ("reflete a cauda, mas a distribuição NP é degenerada", "reflects the tail, but the NP distribution is degenerate"),
        "p_pct": ("mesmo defeito do percentil NP", "same flaw as the NP percentile"),
        "p_basic": ("usa \\(\\hat\\theta^* - \\hat\\theta \\approx \\hat\\theta - \\theta\\): quase certo", "uses \\(\\hat\\theta^* - \\hat\\theta \\approx \\hat\\theta - \\theta\\): nearly right"),
        "p_pivot": ("\\(\\hat\\theta/\\theta \\sim \\text{Beta}(n, 1)\\) nos dois mundos: exato", "\\(\\hat\\theta/\\theta \\sim \\text{Beta}(n, 1)\\) in both worlds: exact"),
    }
    i = 0 if pt else 1
    rows = [[names[k][i], _pct(c[k], lang), why[k][i]] for k in names]
    cols = ["método" if pt else "method", "cobertura" if pt else "coverage", "por quê" if pt else "why"]
    cap = (f"{integer(d['M'], lang)} amostras de U(0, 1) com n = {d['n']}, B = {d['B']}." if pt else
           f"{integer(d['M'], lang)} samples from U(0, 1) with n = {d['n']}, B = {d['B']}.")
    return _tbl(cols, rows, hl={4}) + _cap(cap)


# ------------------------------------------------------------------ interactive: resample by hand
def demo(site: Site, lang: str) -> str:
    d = site.data["bootstrap"]["worked"]
    pt = lang == "pt"
    L = {
        "head": "faça você mesmo · os 15 tempos de espera" if pt else "do it yourself · the 15 waiting times",
        "stat": "estatística" if pt else "statistic",
        "mean": "média" if pt else "mean", "median": "mediana" if pt else "median",
        "one": "+1 reamostra" if pt else "+1 resample", "hundred": "+100", "thousand": "+1.000" if pt else "+1,000",
        "reset": "zerar" if pt else "reset",
        "keys": (["reamostras B", "erro-padrão NP", "erro-padrão P", "IC 95% NP (percentil)"] if pt else
                 ["resamples B", "NP std. error", "P std. error", "NP 95% CI (percentile)"]),
        "cap": ("Cada clique sorteia uma reamostra NP (com reposição dos 15 valores; o número sobre o ponto é quantas vezes ele "
                "saiu) e uma P (15 valores novos de Exp(\\(\\bar x\\))). Os histogramas acumulam \\(\\hat\\theta^*\\) de cada lado. Roda no seu navegador." if pt else
                "Each click draws one NP resample (the 15 values with replacement; the number over a point is how many times it was "
                "drawn) and one P resample (15 fresh values from Exp(\\(\\bar x\\))). The histograms accumulate \\(\\hat\\theta^*\\) on each side. Runs in your browser."),
    }
    reads = "".join(f'<div><div class="v" data-o="{i}">—</div><div class="k">{esc(k)}</div></div>' for i, k in enumerate(L["keys"]))
    cfg = json.dumps({"lang": lang, "x": d["x"]})
    return f"""<figure class="panel" data-boot='{cfg}'>
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(L['head'])}</span>
    <span class="boot-btns"><button type="button" class="btn-ghost" data-add="1">{esc(L['one'])}</button><button type="button" class="btn-ghost" data-add="100">{esc(L['hundred'])}</button><button type="button" class="btn-ghost" data-add="1000">{esc(L['thousand'])}</button><button type="button" class="btn-ghost" data-reset>↺ {esc(L['reset'])}</button></span></div>
  <div class="panel-b">
    <div class="th-ctrl"><span class="label">{esc(L['stat'])}</span>
      <label><input type="radio" name="bs-{lang}" value="mean" checked data-stat> {esc(L['mean'])}</label>
      <label><input type="radio" name="bs-{lang}" value="median" data-stat> {esc(L['median'])}</label></div>
    <div class="chart"><svg viewBox="0 0 640 380" role="img" aria-label="resampling demonstration" data-svg></svg></div>
    <div class="th-read" style="grid-template-columns:repeat(4,minmax(0,1fr))">{reads}</div>
  </div>
  <figcaption style="padding:0 18px 16px">{esc(L['cap'])}</figcaption>
</figure>"""


COMPONENTS = {
    "boot-worlds": worlds, "boot-toy": toy, "boot-cdf": cdf, "boot-dist-mean": dist_mean,
    "boot-dist-median": dist_median, "boot-worked": worked_table, "boot-b": b_table,
    "boot-coverage": coverage_chart, "boot-coverage-table": coverage_table, "boot-max": max_fig,
    "boot-max-table": max_table, "boot-demo": demo,
}
