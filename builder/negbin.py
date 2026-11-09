"""Components for the research note on Poisson overdispersion and the negative binomial (data from data/negbin.json)."""
from __future__ import annotations

import math

from .bootstrap import _cap, _legend, _panel, _pct, _tbl
from .core import Site, esc, integer, num


def _iv(a: list[float], lang: str, d: int = 3) -> str:
    sep = "; " if lang == "pt" else ", "
    return f"[{num(a[0], lang, d)}{sep}{num(a[1], lang, d)}]"


# ------------------------------------------------------------------ the mixture: simulated vs closed form vs Poisson
def mixture_fig(site: Site, lang: str) -> str:
    d = site.data["negbin"]["mixture"]
    pt = lang == "pt"
    w, h, l, r, t, b = 640, 290, 44, 16, 14, 40
    K = len(d["k"])
    ymax = 0.22
    bw = (w - l - r) / K
    X = lambda k: l + (k + 0.5) * bw                 # noqa: E731
    Y = lambda v: t + (1 - min(v, ymax) / ymax) * (h - t - b)   # noqa: E731
    out = []
    for v in (0, 0.05, 0.10, 0.15, 0.20):
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>')
    for k in d["k"]:
        v = d["emp"][k]
        out.append(f'<rect x="{X(k) - bw / 2 + 2:.1f}" y="{Y(v):.1f}" width="{bw - 4:.1f}" height="{Y(0) - Y(v):.1f}" '
                   f'fill="var(--accent)" opacity=".45"><title>k = {k} · {"simulado" if pt else "simulated"} {num(v, lang, 4)}</title></rect>')
        if k % 2 == 0:
            out.append(f'<text x="{X(k):.1f}" y="{h - b + 16}" text-anchor="middle">{k}</text>')
    out.append(f'<text x="{w - r}" y="{h - 6}" text-anchor="end">y</text>')
    pts = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in zip(d["k"], d["pois"]))
    out.append(f'<polyline points="{pts}" fill="none" stroke="var(--text-2)" stroke-width="1.25" stroke-dasharray="3 2"/>')
    pts = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in zip(d["k"], d["nb"]))
    out.append(f'<polyline points="{pts}" fill="none" stroke="var(--signal)" stroke-width="1.5"/>')
    for k, v in zip(d["k"], d["nb"]):
        out.append(f'<circle cx="{X(k):.1f}" cy="{Y(v):.1f}" r="2.6" fill="var(--signal)"><title>k = {k} · BN {num(v, lang, 4)}</title></circle>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Poisson-Gamma mixture versus negative binomial and Poisson">{"".join(out)}</svg>'
    a, be = d["alpha"], d["beta"]
    lg = _legend([((f"simulado: Z ~ Gama({num(a, lang, 0)}; {num(be, lang, 1)}), depois Y | Z ~ Poisson(Z)" if pt else
                    f"simulated: Z ~ Gamma({num(a, lang, 0)}, {num(be, lang, 1)}), then Y | Z ~ Poisson(Z)"), "var(--accent)", "block"),
                  ((f"binomial negativa(r = {num(a, lang, 0)}, p = 1/3), fórmula fechada" if pt else
                    f"negative binomial(r = {num(a, lang, 0)}, p = 1/3), closed form"), "var(--signal)", "solid"),
                  (("Poisson(4) — mesma média" if pt else "Poisson(4) — same mean"), "var(--text-2)", "dash")])
    head = "a mistura Poisson–Gama, simulada" if pt else "the Poisson–Gamma mixture, simulated"
    cap = (f"{integer(d['N'], lang)} repetições do experimento em duas etapas. A maior diferença entre a frequência simulada e a "
           f"fórmula da binomial negativa em qualquer \\(k\\) é {num(d['max_abs_err'], lang, 4)} — ruído de Monte Carlo. A Poisson com a "
           "mesma média é estreita demais: pouca massa no zero, quase nada na cauda." if pt else
           f"{integer(d['N'], lang)} runs of the two-stage experiment. The largest gap between the simulated frequency and the "
           f"negative binomial formula at any \\(k\\) is {num(d['max_abs_err'], lang, 4)} — Monte Carlo noise. The Poisson with the "
           "same mean is far too narrow: too little mass at zero, almost nothing in the tail.")
    return _panel(head, "E[Y] = 4", svg, cap, lg)


def mixture_table(site: Site, lang: str) -> str:
    d = site.data["negbin"]["mixture"]
    pt = lang == "pt"
    f = lambda v, k=3: num(v, lang, k)                  # noqa: E731
    rows = [
        ["\\(\\mathbb E[Z]\\)", "\\(\\alpha/\\beta\\)", f(4, 0), f(d["ez_sim"]), "—"],
        ["\\(\\operatorname{Var}(Z)\\)", "\\(\\alpha/\\beta^2\\)", f(8, 0), f(d["varz_sim"]), "—"],
        ["\\(\\mathbb E[Y]\\)", "\\(\\mathbb E[\\mathbb E[Y\\mid Z]] = \\mathbb E[Z]\\)", f(d["mean_th"], 0), f(d["mean_sim"]), f(4, 0)],
        ["\\(\\operatorname{Var}(Y)\\)", "\\(\\mathbb E[Z] + \\operatorname{Var}(Z)\\)", f(d["var_th"], 0), f(d["var_sim"]), f(4, 0)],
        ["\\(\\Pr(Y = 0)\\)", "\\(p^{\\alpha} = (1/3)^2\\)", f(d["p0"]["nb"], 4), f(d["p0"]["emp"], 4), f(d["p0"]["pois"], 4)],
        ["\\(\\Pr(Y \\ge 10)\\)", "—", f(d["tail10"]["nb"], 4), f(d["tail10"]["emp"], 4), f(d["tail10"]["pois"], 4)],
    ]
    cols = (["quantidade", "fórmula", "teoria", "simulação", "Poisson(4)"] if pt else
            ["quantity", "formula", "theory", "simulation", "Poisson(4)"])
    cap = ("\\(\\alpha = 2\\), \\(\\beta = 0{,}5\\) (taxa), \\(p = \\beta/(1+\\beta) = 1/3\\). A variância de \\(Y\\) é a da Poisson (4) mais a "
           "variância de \\(Z\\) (8): a heterogeneidade triplica a variância sem mexer na média." if pt else
           "\\(\\alpha = 2\\), \\(\\beta = 0.5\\) (rate), \\(p = \\beta/(1+\\beta) = 1/3\\). The variance of \\(Y\\) is the Poisson part (4) plus "
           "the variance of \\(Z\\) (8): heterogeneity triples the variance without touching the mean.")
    return _tbl(cols, rows, hl={3}) + _cap(cap)


# ------------------------------------------------------------------ worked example: fit table
def fit_table(site: Site, lang: str) -> str:
    d = site.data["negbin"]["worked"]
    pt = lang == "pt"
    P, N = d["pois"], d["nb"]
    f = lambda v, k=3: num(v, lang, k)                  # noqa: E731
    se = lambda v: f'<span class=muted>({f(v)})</span>'  # noqa: E731
    rows = [
        ["\\(\\beta_0\\)" + (" (verdadeiro 1)" if pt else " (true 1)"), f"{f(P['beta'][0])} {se(P['se'][0])}",
         f"{f(P['beta'][0])} {se(P['se_quasi'][0])}", f"{f(N['beta'][0])} {se(N['se'][0])}"],
        ["\\(\\beta_1\\)" + (" (verdadeiro 0,5)" if pt else " (true 0.5)"), f"{f(P['beta'][1])} {se(P['se'][1])}",
         f"{f(P['beta'][1])} {se(P['se_quasi'][1])}", f"{f(N['beta'][1])} {se(N['se'][1])}"],
        [("IC 95% para \\(\\beta_1\\)" if pt else "95% CI for \\(\\beta_1\\)"), _iv(P["ci_b1"], lang), _iv(P["ci_b1_quasi"], lang), _iv(N["ci_b1"], lang)],
        ["\\(\\theta\\)" + (" (verdadeiro 1,5)" if pt else " (true 1.5)"), "\\(\\infty\\) " + ("(fixo)" if pt else "(fixed)"), "—",
         f"{f(N['theta'])} {se(N['theta_se'])}"],
        [("\\(\\hat\\phi\\) = Pearson \\(X^2\\)/g.l." if pt else "\\(\\hat\\phi\\) = Pearson \\(X^2\\)/df"),
         f"{f(P['pearson'], 1)}/{P['df']} = <b>{f(P['phi'], 2)}</b>", f(P["phi"], 2) + (" (estimado)" if pt else " (estimated)"),
         f"{f(N['pearson'], 1)}/{d['n'] - 3} = <b>{f(N['phi'], 2)}</b>"],
        [("deviance/g.l." if pt else "deviance/df"), f"{f(P['deviance'], 1)}/{P['df']} = {f(P['deviance'] / P['df'], 2)}", "—",
         f"{f(N['deviance'], 1)}/{d['n'] - 3} = {f(N['deviance'] / (d['n'] - 3), 2)}"],
        [("log-verossimilhança" if pt else "log-likelihood"), f(P["ll"], 1), ("— (não há)" if pt else "— (none)"), f(N["ll"], 1)],
        ["AIC", f(P["aic"], 1), "—", f"<b>{f(N['aic'], 1)}</b>"],
    ]
    cols = ["", "Poisson", "quasi-Poisson", ("binomial negativa" if pt else "negative binomial")]
    cap = (f"n = {d['n']} contagens simuladas com \\(\\log\\mu_i = 1 + 0{{,}}5\\,x_i\\) e \\(\\theta = 1{{,}}5\\). Entre parênteses, erros-padrão. "
           f"Média amostral de \\(y\\): {f(d['y_mean'], 2)}; variância: {f(d['y_var'], 2)}; zeros: {d['zeros']}. A quasi-Poisson tem as mesmas "
           "estimativas da Poisson, só multiplica os erros-padrão por \\(\\sqrt{\\hat\\phi}\\)." if pt else
           f"n = {d['n']} counts simulated with \\(\\log\\mu_i = 1 + 0.5\\,x_i\\) and \\(\\theta = 1.5\\). Standard errors in brackets. "
           f"Sample mean of \\(y\\): {f(d['y_mean'], 2)}; variance: {f(d['y_var'], 2)}; zeros: {d['zeros']}. Quasi-Poisson has the same "
           "estimates as Poisson and only multiplies the standard errors by \\(\\sqrt{\\hat\\phi}\\).")
    return _tbl(cols, rows, hl={4}) + _cap(cap)


# ------------------------------------------------------------------ worked example: observed vs expected frequencies
def freq_fig(site: Site, lang: str) -> str:
    d = site.data["negbin"]["worked"]["freq"]
    pt = lang == "pt"
    obs, ep, en = d["obs"], d["pois"], d["nb"]
    K = len(obs)
    w, h, l, r, t, b = 640, 290, 44, 16, 14, 40
    ymax = 130
    bw = (w - l - r) / K
    X = lambda k: l + (k + 0.5) * bw                 # noqa: E731
    Y = lambda v: t + (1 - min(v, ymax) / ymax) * (h - t - b)   # noqa: E731
    out = []
    for v in range(0, 121, 20):
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    for k in range(K):
        lab = str(k) if k < K - 1 else f"{k}+"
        out.append(f'<rect x="{X(k) - bw / 2 + 2:.1f}" y="{Y(obs[k]):.1f}" width="{bw - 4:.1f}" height="{Y(0) - Y(obs[k]):.1f}" '
                   f'fill="var(--text-3)" opacity=".35"><title>y = {lab} · {"observado" if pt else "observed"} {obs[k]} · Poisson '
                   f'{num(ep[k], lang, 1)} · {"BN" if pt else "NB"} {num(en[k], lang, 1)}</title></rect>')
        out.append(f'<text x="{X(k):.1f}" y="{h - b + 16}" text-anchor="middle">{lab}</text>')
    for vals, color, dash in ((ep, "var(--text-2)", "3 2"), (en, "var(--signal)", "")):
        pts = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in enumerate(vals))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5"{da}/>')
        for k, v in enumerate(vals):
            out.append(f'<circle cx="{X(k):.1f}" cy="{Y(v):.1f}" r="2.6" fill="{color}"/>')
    out.append(f'<text x="{w - r}" y="{h - 6}" text-anchor="end">y</text>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="observed and expected count frequencies">{"".join(out)}</svg>'
    lg = _legend([("observado" if pt else "observed", "var(--text-3)", "block"),
                  ("esperado · Poisson" if pt else "expected · Poisson", "var(--text-2)", "dash"),
                  ("esperado · binomial negativa" if pt else "expected · negative binomial", "var(--signal)", "solid")])
    head = "frequências observadas × esperadas" if pt else "observed vs expected frequencies"
    cap = (f"Esperado = \\(\\sum_i \\Pr(Y_i = k \\mid \\hat\\mu_i)\\) somado sobre as {site.data['negbin']['worked']['n']} observações. "
           f"A Poisson prevê {num(ep[0], lang, 1)} zeros (houve {obs[0]}) e {num(ep[-1], lang, 2)} valores \\(\\ge {K - 1}\\) (houve {obs[-1]}); "
           f"compensa empilhando massa no meio. A binomial negativa prevê {num(en[0], lang, 1)} zeros e {num(en[-1], lang, 1)} na cauda." if pt else
           f"Expected = \\(\\sum_i \\Pr(Y_i = k \\mid \\hat\\mu_i)\\) summed over the {site.data['negbin']['worked']['n']} observations. "
           f"Poisson predicts {num(ep[0], lang, 1)} zeros (there were {obs[0]}) and {num(ep[-1], lang, 2)} values \\(\\ge {K - 1}\\) (there were {obs[-1]}); "
           f"it makes up for it by piling mass in the middle. The negative binomial predicts {num(en[0], lang, 1)} zeros and {num(en[-1], lang, 1)} in the tail.")
    return _panel(head, "n = " + str(site.data["negbin"]["worked"]["n"]), svg, cap, lg)


# ------------------------------------------------------------------ worked example: mean-variance plot
def mv_fig(site: Site, lang: str) -> str:
    d = site.data["negbin"]["worked"]
    pt = lang == "pt"
    th = d["nb"]["theta"]
    bins = d["mv_bins"]
    w, h, l, r, t, b = 640, 300, 44, 16, 14, 40
    xmax, ymax = 6.5, 32
    X = lambda v: l + v / xmax * (w - l - r)          # noqa: E731
    Y = lambda v: t + (1 - min(v, ymax) / ymax) * (h - t - b)   # noqa: E731
    out = []
    for v in range(0, 31, 5):
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    for v in range(0, 7):
        out.append(f'<text x="{X(v):.1f}" y="{h - b + 16}" text-anchor="middle">{v}</text>')
    grid = [i * xmax / 100 for i in range(101)]
    out.append(f'<polyline points="{" ".join(f"{X(m):.1f},{Y(m):.1f}" for m in grid)}" fill="none" stroke="var(--text-2)" stroke-width="1.25" stroke-dasharray="3 2"/>')
    out.append(f'<polyline points="{" ".join(f"{X(m):.1f},{Y(m + m * m / th):.1f}" for m in grid if m + m * m / th <= ymax)}" fill="none" stroke="var(--signal)" stroke-width="1.5"/>')
    phi = d["pois"]["phi"]
    out.append(f'<polyline points="{" ".join(f"{X(m):.1f},{Y(phi * m):.1f}" for m in grid)}" fill="none" stroke="var(--accent)" stroke-width="1.25" stroke-dasharray="6 3"/>')
    for g in bins:
        out.append(f'<circle cx="{X(g["m"]):.1f}" cy="{Y(g["v"]):.1f}" r="4" fill="var(--text)" opacity=".8">'
                   f'<title>{"média" if pt else "mean"} {num(g["m"], lang, 2)} · {"variância" if pt else "variance"} {num(g["v"], lang, 2)}</title></circle>')
    out.append(f'<text x="{w - r}" y="{h - 6}" text-anchor="end">{"média do grupo" if pt else "group mean"}</text>')
    out.append(f'<text x="{l + 4}" y="{t + 10}">{"variância do grupo" if pt else "group variance"}</text>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="variance against mean by group">{"".join(out)}</svg>'
    lg = _legend([("Poisson: Var = μ", "var(--text-2)", "dash"),
                  (f"quasi-Poisson: Var = {num(phi, lang, 2)} μ", "var(--accent)", "dash"),
                  ((f"BN: Var = μ + μ²/{num(th, lang, 2)}" if pt else f"NB: Var = μ + μ²/{num(th, lang, 2)}"), "var(--signal)", "solid")])
    head = "variância contra média" if pt else "variance against mean"
    cap = ("As 500 observações ordenadas pela média ajustada e cortadas em 10 grupos de 50; cada ponto é a média e a variância "
           "amostral de um grupo. Os pontos estão todos acima da reta Var = μ. Com 50 pontos por grupo a variância é ruidosa; o que "
           "importa é o padrão: a distância até a reta cresce com a média." if pt else
           "The 500 observations sorted by fitted mean and cut into 10 groups of 50; each point is one group's sample mean and "
           "variance. Every point lies above the line Var = μ. With 50 points per group the variance is noisy; what matters is "
           "the pattern: the gap to the line grows with the mean.")
    return _panel(head, "θ̂ = " + num(th, lang, 2), svg, cap, lg)


# ------------------------------------------------------------------ coverage study
def coverage_table(site: Site, lang: str) -> str:
    d = site.data["negbin"]["coverage"]
    pt = lang == "pt"
    rows = []
    for r in d["rows"]:
        th = r["theta"]
        lab = ("\\(\\infty\\) (Poisson)" if th is None else f"\\({num(th, lang, 1 if th < 1 else 0)}\\)")
        cell = lambda k: f"{_pct(r['cov_' + k], lang)} <span class=muted>· {num(r['w_' + k], lang, 3)}</span>"   # noqa: E731
        rows.append([lab, cell("pois"), cell("quasi"), cell("nb"), num(r["sd_b1_pois"], lang, 3) + " / " + num(r["sd_b1_nb"], lang, 3)])
    cols = (["\\(\\theta\\) verdadeiro", "Poisson", "quasi-Poisson", "binomial negativa", "desvio real de \\(\\hat\\beta_1\\) (P / BN)"] if pt else
            ["true \\(\\theta\\)", "Poisson", "quasi-Poisson", "negative binomial", "actual sd of \\(\\hat\\beta_1\\) (P / NB)"])
    cap = (f"{integer(d['M'], lang)} conjuntos de dados por linha, n = {d['n']}, \\(\\log\\mu = 1 + 0{{,}}5x\\). Cada célula: cobertura do IC de Wald de 95% "
           f"para \\(\\beta_1\\) · largura média. Erro de Monte Carlo da cobertura: ± {num(100 * d['mc_se'], lang, 1)} p.p. A última coluna é o "
           "desvio-padrão de \\(\\hat\\beta_1\\) entre os conjuntos: o que um bom erro-padrão deveria estimar." if pt else
           f"{integer(d['M'], lang)} datasets per row, n = {d['n']}, \\(\\log\\mu = 1 + 0.5x\\). Each cell: coverage of the 95% Wald interval "
           f"for \\(\\beta_1\\) · mean width. Monte Carlo error of the coverage: ± {num(100 * d['mc_se'], lang, 1)} pp. The last column is the "
           "standard deviation of \\(\\hat\\beta_1\\) across datasets: what a good standard error should estimate.")
    return _tbl(cols, rows, hl={3}) + _cap(cap)


COMPONENTS = {
    "nb-mixture": mixture_fig, "nb-mixture-table": mixture_table, "nb-fit": fit_table,
    "nb-freq": freq_fig, "nb-mv": mv_fig, "nb-coverage": coverage_table,
}
