"""Components for the research note on quasi-likelihood GLMs (data from data/quasi.json)."""
from __future__ import annotations

from .bootstrap import _cap, _panel, _pct, _tbl
from .core import Site, num


def _iv(a: list[float], lang: str, d: int = 3) -> str:
    sep = "; " if lang == "pt" else ", "
    return f"[{num(a[0], lang, d)}{sep}{num(a[1], lang, d)}]"


def _p(p: float, lang: str) -> str:
    if p < 1e-4:
        exp = 0
        while p < 10 ** -(exp + 1):
            exp += 1
        return f"\\(&lt; 10^{{-{exp}}}\\)"
    return num(p, lang, 4)


# ------------------------------------------------------------------ quasi-Poisson: mean and variance by spray
def qp_groups(site: Site, lang: str) -> str:
    d = site.data["quasi"]["qpois"]
    pt = lang == "pt"
    rows = [[g["spray"], num(g["true"], lang, 0), num(g["mean"], lang, 2), num(g["var"], lang, 2),
             f"<b>{num(g['var'] / g['mean'], lang, 2)}</b>"] for g in d["groups"]]
    cols = (["inseticida", "média verdadeira", "média amostral", "variância amostral", "variância/média"] if pt else
            ["spray", "true mean", "sample mean", "sample variance", "variance/mean"])
    cap = (f"{d['k']} parcelas por inseticida. Os dados foram gerados com \\(\\operatorname{{Var}}(Y) = 3\\mu\\). Sob Poisson, a última "
           "coluna ficaria perto de 1; aqui ela fica entre 2 e 6, sem tendência clara com a média — o padrão que a quasi-Poisson supõe." if pt else
           f"{d['k']} plots per spray. Data generated with \\(\\operatorname{{Var}}(Y) = 3\\mu\\). Under Poisson the last column would be "
           "close to 1; here it ranges from 2 to 6 with no clear trend in the mean — the pattern quasi-Poisson assumes.")
    return _tbl(cols, rows) + _cap(cap)


# ------------------------------------------------------------------ quasi-Poisson: fit table
def qp_fit(site: Site, lang: str) -> str:
    d = site.data["quasi"]["qpois"]
    pt = lang == "pt"
    f = lambda v, k=3: num(v, lang, k)                  # noqa: E731
    names = ["\\(\\beta_0\\) (A)", "\\(\\beta_1\\) (B − A)", "\\(\\beta_2\\) (C − A)", "\\(\\beta_3\\) (D − A)"]
    rows = [[names[j], f(d["beta"][j]), f(d["se_pois"][j]), f"<b>{f(d['se_quasi'][j])}</b>", f(d["se_sand"][j])] for j in range(4)]
    rows.append([("IC 95% para \\(\\beta_1\\)" if pt else "95% CI for \\(\\beta_1\\)"), "—", _iv(d["b1_ci_pois"], lang),
                 _iv(d["b1_ci_quasi"], lang), "—"])
    rows.append([("teste do efeito do inseticida" if pt else "test of the spray effect"), "—",
                 f"\\(\\chi^2_3\\) = {f(d['lr'], 1)}, p {_p(d['lr_p'], lang)}",
                 f"\\(F_{{3,{d['df']}}}\\) = {f(d['F'], 2)}, p = {f(d['F_p'], 4)}", "—"])
    cols = ["", ("estimativa" if pt else "estimate"), ("e.p. Poisson" if pt else "SE Poisson"),
            ("e.p. quasi-Poisson" if pt else "SE quasi-Poisson"), ("e.p. sanduíche" if pt else "SE sandwich")]
    cap = (f"n = {d['n']}, \\(\\hat\\phi = X^2/(n-p) = {f(d['X2'], 1)}/{d['df']} = {f(d['phi'], 2)}\\) (verdadeiro: 3). "
           f"A estimativa é a mesma nas três colunas; só muda o erro-padrão. Quasi-Poisson = Poisson × \\(\\sqrt{{\\hat\\phi}} = {f(d['phi'] ** 0.5, 2)}\\). "
           f"O intervalo quasi usa o quantil \\(t_{{{d['df']}}}\\) = {f(d['t975'])}." if pt else
           f"n = {d['n']}, \\(\\hat\\phi = X^2/(n-p) = {f(d['X2'], 1)}/{d['df']} = {f(d['phi'], 2)}\\) (true: 3). "
           f"The estimate is the same in all three columns; only the standard error changes. Quasi-Poisson = Poisson × \\(\\sqrt{{\\hat\\phi}} = {f(d['phi'] ** 0.5, 2)}\\). "
           f"The quasi interval uses the \\(t_{{{d['df']}}}\\) quantile = {f(d['t975'])}.")
    return _tbl(cols, rows, hl={5}) + _cap(cap)


# ------------------------------------------------------------------ quasi-Poisson: IRLS trace
def qp_trace(site: Site, lang: str) -> str:
    d = site.data["quasi"]["qpois"]
    pt = lang == "pt"
    f = lambda v, k=6: num(v, lang, k)                  # noqa: E731
    rows = [[str(s["it"])] + [f(b) for b in s["beta"]] + [f(s["dev"], 4)] for s in d["trace"]]
    cols = [("iteração" if pt else "iteration"), "\\(\\beta_0\\)", "\\(\\beta_1\\)", "\\(\\beta_2\\)", "\\(\\beta_3\\)",
            ("quasi-deviance" if pt else "quasi-deviance")]
    cap = ("Ponto de partida: \\(\\mu_i^{(0)} = (y_i + \\bar y)/2 + 0{,}1\\). Na terceira iteração os coeficientes já estão certos até a 5ª casa; "
           "as duas últimas só confirmam a convergência. Nenhuma linha depende de \\(\\phi\\)." if pt else
           "Starting point: \\(\\mu_i^{(0)} = (y_i + \\bar y)/2 + 0.1\\). By the third iteration the coefficients are right to the 5th decimal; "
           "the last two only confirm convergence. No row depends on \\(\\phi\\).")
    return _tbl(cols, rows) + _cap(cap)


# ------------------------------------------------------------------ quasi-binomial: germination
def qb_fit(site: Site, lang: str) -> str:
    d = site.data["quasi"]["qbin"]
    pt = lang == "pt"
    f = lambda v, k=3: num(v, lang, k)                  # noqa: E731
    lab = {(0, 0): ("tipo 1 · água" if pt else "type 1 · water"), (0, 1): ("tipo 1 · extrato" if pt else "type 1 · extract"),
           (1, 0): ("tipo 2 · água" if pt else "type 2 · water"), (1, 1): ("tipo 2 · extrato" if pt else "type 2 · extract")}
    rows = [[lab[(c["seed"], c["extract"])], f(c["true"]), f(c["prop"]), f"{c['min']}–{c['max']}"] for c in d["cells"]]
    cols = (["semente · tratamento", "probabilidade verdadeira", "proporção observada", "germinadas por placa (mín–máx)"] if pt else
            ["seed · treatment", "true probability", "observed proportion", "germinated per plate (min–max)"])
    t1 = _tbl(cols, rows)
    rows2 = [
        [("interação \\(\\hat\\beta_3\\)" if pt else "interaction \\(\\hat\\beta_3\\)"), f"{f(d['beta'][3])} ({f(d['se_bin'][3])})",
         f"{f(d['beta'][3])} ({f(d['se_quasi'][3])})"],
        [("estatística" if pt else "statistic"), f"\\(\\chi^2_1\\) = {f(d['lr'], 2)}", f"\\(F_{{1,{d['df']}}}\\) = {f(d['F'], 2)}"],
        [("p-valor" if pt else "p-value"), _p(d["lr_p"], lang), f(d["F_p"], 4)],
        [("dispersão" if pt else "dispersion"), ("\\(\\phi = 1\\) (fixo)" if pt else "\\(\\phi = 1\\) (fixed)"),
         f"\\(\\hat\\phi = {f(d['phi'], 2)}\\)"],
    ]
    t2 = _tbl(["", ("binomial" if pt else "binomial"), "quasi-binomial"], rows2, hl={2})
    cap = (f"{d['plates']} placas de {d['m']} sementes por combinação; probabilidades de placa sorteadas de uma Beta com correlação "
           f"intraplaca \\(\\rho = {f(d['rho'], 2)}\\), o que dá \\(\\phi = 1 + (m-1)\\rho = {f(d['phi_true'], 2)}\\). A interação verdadeira é zero. "
           "Entre parênteses, erros-padrão." if pt else
           f"{d['plates']} plates of {d['m']} seeds per combination; plate probabilities drawn from a Beta with intra-plate correlation "
           f"\\(\\rho = {f(d['rho'], 2)}\\), so \\(\\phi = 1 + (m-1)\\rho = {f(d['phi_true'], 2)}\\). The true interaction is zero. "
           "Standard errors in brackets.")
    return t1 + t2 + _cap(cap)


# ------------------------------------------------------------------ Wedderburn: residuals against fitted values
def wd_fig(site: Site, lang: str) -> str:
    d = site.data["quasi"]["wedd"]
    pt = lang == "pt"
    W, H, pw, gap, l, t, b = 660, 290, 290, 40, 40, 26, 40
    xlo, xhi, ylim = -7.0, 4.5, 3.2
    out = []
    for k, (key, title) in enumerate((("binom", "V(μ) = μ(1 − μ)"), ("wedd", "V(μ) = μ²(1 − μ)²"))):
        x0 = l + k * (pw + gap)
        X = lambda v: x0 + (v - xlo) / (xhi - xlo) * pw                      # noqa: E731
        Y = lambda v: t + (1 - (max(-ylim, min(ylim, v)) + ylim) / (2 * ylim)) * (H - t - b)   # noqa: E731
        out.append(f'<text x="{x0}" y="{t - 10}" font-weight="600">{title}</text>')
        for v in (-3, -2, -1, 0, 1, 2, 3):
            cls = "gl" if v else "gl"
            out.append(f'<line class="{cls}" x1="{x0}" x2="{x0 + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"'
                       + (' stroke-dasharray="3 2"' if v else "") + "/>")
            if k == 0:
                out.append(f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
        for v in (-6, -4, -2, 0, 2, 4):
            out.append(f'<text x="{X(v):.1f}" y="{H - b + 16}" text-anchor="middle">{v}</text>')
        for e, rr in d[key]["points"]:
            out.append(f'<circle cx="{X(e):.1f}" cy="{Y(rr):.1f}" r="3" fill="var(--accent)" opacity=".7"/>')
        out.append(f'<text x="{x0 + pw}" y="{H - 6}" text-anchor="end">logit(μ̂)</text>')
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="standardised Pearson residuals against fitted logit, two variance functions">'
           f'{"".join(out)}</svg>')
    head = "resíduos contra valores ajustados" if pt else "residuals against fitted values"
    cap = ("Resíduos de Pearson padronizados, \\(r_i/\\sqrt{\\hat\\phi(1-h_i)}\\), das 90 proporções. À esquerda, com a variância binomial, "
           "a nuvem é mais estreita nas proporções pequenas e mais larga no meio: a variância suposta não acompanha a dos dados. "
           "À direita, com \\(V(\\mu) = \\mu^2(1-\\mu)^2\\), a largura é parecida em toda a faixa." if pt else
           "Standardised Pearson residuals, \\(r_i/\\sqrt{\\hat\\phi(1-h_i)}\\), for the 90 proportions. Left, with the binomial variance, the "
           "cloud is narrower for small proportions and wider in the middle: the assumed variance does not follow the data. "
           "Right, with \\(V(\\mu) = \\mu^2(1-\\mu)^2\\), the spread is similar across the whole range.")
    return _panel(head, f"n = {d['n']}", svg, cap)


def wd_table(site: Site, lang: str) -> str:
    d = site.data["quasi"]["wedd"]
    pt = lang == "pt"
    f = lambda v, k=3: num(v, lang, k)                  # noqa: E731
    B, Wd = d["binom"], d["wedd"]
    rows = []
    for i in range(5):
        lo, hi = B["bins"][i]["lo"], B["bins"][i]["hi"]
        lo2, hi2 = Wd["bins"][i]["lo"], Wd["bins"][i]["hi"]
        rows.append([f"{i + 1}º " + ("quinto" if pt else "fifth"),
                     f"{f(B['bins'][i]['rvar'], 2)} <span class=muted>(μ̂ {f(lo, 3)}–{f(hi, 3)})</span>",
                     f"{f(Wd['bins'][i]['rvar'], 2)} <span class=muted>(μ̂ {f(lo2, 3)}–{f(hi2, 3)})</span>"])
    rows.append([("\\(\\hat\\phi\\)"), f(B["phi"]), f(Wd["phi"])])
    rows.append([("quasi-verossimilhança estendida \\(Q^+\\)" if pt else "extended quasi-likelihood \\(Q^+\\)"), f(B["eql"], 1),
                 f"<b>{f(Wd['eql'], 1)}</b>"])
    rows.append([("variedade 10 − variedade 1 (verdadeiro 3,5)" if pt else "variety 10 − variety 1 (true 3.5)"),
                 f"{f(B['b_v10'], 2)} ({f(B['se_v10'], 2)})", f"<b>{f(Wd['b_v10'], 2)} ({f(Wd['se_v10'], 2)})</b>"])
    rows.append([("e.p. sanduíche do mesmo contraste" if pt else "sandwich SE of the same contrast"), f(B["sand_v10"], 2), f(Wd["sand_v10"], 2)])
    cols = ["", "\\(V = \\mu(1-\\mu)\\)", "\\(V = \\mu^2(1-\\mu)^2\\)"]
    cap = ("As cinco primeiras linhas: média do resíduo padronizado ao quadrado em cada quinto das observações, ordenadas pelo valor ajustado. "
           "Se a função de variância estiver certa, todas ficam perto de 1. \\(Q^+\\) maior = melhor; ela pode comparar funções de variância "
           "diferentes, coisa que a quasi-deviance não pode." if pt else
           "First five rows: mean squared standardised residual in each fifth of the observations, sorted by fitted value. If the variance "
           "function is right, all are close to 1. Larger \\(Q^+\\) = better; unlike the quasi-deviance it can compare different variance functions.")
    return _tbl(cols, rows, hl={6}) + _cap(cap)


# ------------------------------------------------------------------ simulations
def sim_table(site: Site, lang: str) -> str:
    s = site.data["quasi"]["sim"]
    pt = lang == "pt"
    P = lambda v: _pct(v, lang)                         # noqa: E731
    s1, s3, s2 = s["s1"], s["s3"], s["s2"]
    rows = [
        [("S1 · contagens, \\(\\operatorname{Var} = 3\\mu\\), n = 50" if pt else "S1 · counts, \\(\\operatorname{Var} = 3\\mu\\), n = 50"),
         P(s1["pois"]), P(s1["quasi_z"]), f"<b>{P(s1['quasi_t'])}</b>", P(s1["sand"])],
        [("S3 · as mesmas contagens, n = 12" if pt else "S3 · same counts, n = 12"),
         P(s3["pois"]), P(s3["quasi_z"]), f"<b>{P(s3['quasi_t'])}</b>", P(s3["sand"])],
    ]
    cols = (["cenário", "Poisson", "quasi-Poisson (normal)", "quasi-Poisson (t)", "sanduíche"] if pt else
            ["scenario", "Poisson", "quasi-Poisson (normal)", "quasi-Poisson (t)", "sandwich"])
    t1 = _tbl(cols, rows)
    rows2 = [
        [("cobertura do IC de 95%" if pt else "coverage of the 95% CI"), P(s2["v_mu"]), P(s2["v_mu_sand"]), f"<b>{P(s2['v_mu2'])}</b>"],
        [("desvio-padrão real de \\(\\hat\\beta_1\\)" if pt else "actual sd of \\(\\hat\\beta_1\\)"), num(s2["sd_mu"], lang, 3), num(s2["sd_mu"], lang, 3),
         f"<b>{num(s2['sd_mu2'], lang, 3)}</b>"],
        [("erro-padrão médio reportado" if pt else "mean reported SE"), num(s2["mse_mu"], lang, 3), "—", num(s2["mse_mu2"], lang, 3)],
    ]
    cols2 = (["S2 · contínuos, \\(\\operatorname{Var} = 0{,}25\\,\\mu^2\\), n = 50", "\\(V = \\mu\\)", "\\(V = \\mu\\) + sanduíche", "\\(V = \\mu^2\\)"] if pt else
             ["S2 · continuous, \\(\\operatorname{Var} = 0.25\\,\\mu^2\\), n = 50", "\\(V = \\mu\\)", "\\(V = \\mu\\) + sandwich", "\\(V = \\mu^2\\)"])
    t2 = _tbl(cols2, rows2)
    cap = (f"{s['M']} conjuntos de dados por cenário; \\(\\log\\mu = 1 + 0{{,}}5x\\) (S1, S3) ou \\(1 + 1{{,}}5x\\) (S2), \\(x \\sim U(0, 2)\\). "
           f"Cada célula da primeira tabela: proporção de intervalos de 95% para \\(\\beta_1\\) que contêm o valor verdadeiro. "
           f"Erro de Monte Carlo: ± {num(100 * s['mc_se'], lang, 1)} p.p." if pt else
           f"{s['M']} datasets per scenario; \\(\\log\\mu = 1 + 0.5x\\) (S1, S3) or \\(1 + 1.5x\\) (S2), \\(x \\sim U(0, 2)\\). "
           f"Each cell of the first table: share of 95% intervals for \\(\\beta_1\\) that contain the true value. "
           f"Monte Carlo error: ± {num(100 * s['mc_se'], lang, 1)} pp.")
    return t1 + t2 + _cap(cap)


COMPONENTS = {
    "qp-groups": qp_groups, "qp-fit": qp_fit, "qp-trace": qp_trace, "qb-fit": qb_fit,
    "wd-fig": wd_fig, "wd-table": wd_table, "q-sim": sim_table,
}
