"""Components for the research note on hyperparameters (data from data/hyper.json)."""
from __future__ import annotations

from .bootstrap import _cap, _legend, _panel, _pct, _tbl
from .core import Site, esc, num

NAMES = {
    "pt": {"cv10": "validação cruzada 10-fold", "loo": "LOOCV (fórmula fechada)", "gcv": "GCV", "aic": "AIC com gl efetivos",
           "aicc": "AICc", "ml": "verossimilhança marginal", "pe": "λ ótimo (oráculo)",
           "grid": "grade", "random": "busca aleatória", "bo": "otimização bayesiana", "sh": "successive halving"},
    "en": {"cv10": "10-fold cross-validation", "loo": "LOOCV (closed form)", "gcv": "GCV", "aic": "AIC with effective df",
           "aicc": "AICc", "ml": "marginal likelihood", "pe": "optimal λ (oracle)",
           "grid": "grid", "random": "random search", "bo": "Bayesian optimisation", "sh": "successive halving"},
}


# ------------------------------------------------------------------ ridge: error curves for one dataset
def ridge_fig(site: Site, lang: str) -> str:
    r = site.data["hyper"]["ridge"]
    o = r["one"]
    pt = lang == "pt"
    w, h, l, rr, t, b = 640, 300, 44, 16, 18, 38
    xs = o["loglam"]
    x0, x1, y0, y1 = xs[0], xs[-1], 0.0, 5.0
    X = lambda v: l + (v - x0) / (x1 - x0) * (w - l - rr)              # noqa: E731
    Y = lambda v: t + (y1 - min(max(v, y0), y1)) / (y1 - y0) * (h - t - b)   # noqa: E731
    out = []
    for v in (0, 1, 2, 3, 4, 5):
        out.append(f'<line class="gl" x1="{l}" x2="{w - rr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 1)}</text>')
    for v in range(int(x0), int(x1) + 1):
        out.append(f'<text x="{X(v):.1f}" y="{h - b + 16}" text-anchor="middle">10<tspan dy="-5" font-size="9">{v}</tspan></text>')
    sig2 = r["sigma"] ** 2
    out.append(f'<line x1="{l}" x2="{w - rr}" y1="{Y(sig2):.1f}" y2="{Y(sig2):.1f}" stroke="var(--text-3)" stroke-dasharray="1 3"/>'
               f'<text x="{w - rr}" y="{Y(sig2) - 5:.1f}" text-anchor="end">σ² = {num(sig2, lang, 0)}</text>')
    series = [("train", "var(--text-3)", "", "erro de treino" if pt else "training error"),
              ("pe", "var(--text)", "", "erro de previsão verdadeiro" if pt else "true prediction error"),
              ("cv10", "var(--accent)", "", NAMES[lang]["cv10"]),
              ("gcv", "var(--signal)", "4 3", "GCV")]
    for key, color, dash, _ in series:
        pts = " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in zip(xs, o[key]))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.75"{da}/>')
    marks = [("pe", "var(--text)", "ótimo" if pt else "optimum"), ("cv10", "var(--accent)", "CV"),
             ("gcv", "var(--signal)", "GCV"), ("ml", "var(--text-2)", "ML"), ("aic", "var(--text-2)", "AIC")]
    for i, (key, color, lab) in enumerate(marks):
        a = o["pick"][key]
        out.append(f'<line x1="{X(a):.1f}" x2="{X(a):.1f}" y1="{t}" y2="{h - b}" stroke="{color}" stroke-width="1" opacity=".35"/>'
                   f'<text x="{X(a) + 3:.1f}" y="{t + 10 + 12 * i}" style="fill:{color}">{lab}</text>')
    out.append(f'<text x="{w - rr}" y="{h - 4}" text-anchor="end">λ (log)</text>')
    svg = f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="ridge regression error curves against lambda">{"".join(out)}</svg>'
    lg = _legend([(s[3], s[1], "dash" if s[2] else "solid") for s in series])
    head = "regressão ridge: erro em função de λ" if pt else "ridge regression: error as a function of λ"
    f = lambda v: num(v, lang, 2)                       # noqa: E731
    cap = (f"Um conjunto de dados (n = {r['n']}, p = {r['p']}): o da simulação em que a distância entre o λ do 10-fold e o λ ótimo é a "
           f"mediana das {r['M']}. O erro de treino só cai; o erro de previsão verdadeiro, \\(\\sigma^2 + (\\hat{{\\boldsymbol\\beta}}_\\lambda - "
           f"\\boldsymbol\\beta)^\\top\\boldsymbol\\Sigma(\\hat{{\\boldsymbol\\beta}}_\\lambda - \\boldsymbol\\beta)\\), tem um mínimo de {f(o['pe_min'])}. "
           f"Mínimos quadrados (λ = 0) dá {f(o['pe_ols'])}; prever zero (λ → ∞) dá {f(o['pe_null'])}. Neste conjunto as curvas estimadas "
           "ficam acima da verdadeira (o ruído da amostra saiu acima da média), mas o que importa para escolher λ é onde fica o mínimo, não o "
           "nível. As linhas verticais marcam o λ escolhido por cada critério." if pt else
           f"One dataset (n = {r['n']}, p = {r['p']}): the replication whose gap between the 10-fold λ and the optimal λ is the median of the "
           f"{r['M']}. Training error only falls; the true prediction error, \\(\\sigma^2 + (\\hat{{\\boldsymbol\\beta}}_\\lambda - "
           f"\\boldsymbol\\beta)^\\top\\boldsymbol\\Sigma(\\hat{{\\boldsymbol\\beta}}_\\lambda - \\boldsymbol\\beta)\\), has a minimum of {f(o['pe_min'])}. "
           f"Least squares (λ = 0) gives {f(o['pe_ols'])}; predicting zero (λ → ∞) gives {f(o['pe_null'])}. The estimated curves sit above the "
           "true one in this dataset (its noise happened to be above average), but what matters for choosing λ is where the minimum is, not its "
           "level. Vertical lines mark the λ chosen by each criterion.")
    return _panel(head, "y: " + ("erro quadrático médio" if pt else "mean squared error"), svg, cap, lg)


# ------------------------------------------------------------------ ridge: criteria over 1,000 datasets
def ridge_table(site: Site, lang: str) -> str:
    r = site.data["hyper"]["ridge"]
    pt = lang == "pt"
    f = lambda v, k=2: num(v, lang, k)                  # noqa: E731
    rows = []
    for c in ("cv10", "loo", "gcv", "aic", "aicc", "ml", "pe"):
        cells = [NAMES[lang][c]]
        for key in ("summary", "summary_prior"):
            s = r[key][c]
            cells.append(f"{f(s['med'])} <span class=muted>({f(s['q1'])} a {f(s['q3'])})</span>" if pt else
                         f"{f(s['med'])} <span class=muted>({f(s['q1'])} to {f(s['q3'])})</span>")
            cells.append("—" if c == "pe" else f(s["r_med"]))
            cells.append("—" if c == "pe" else _pct(s["p_within10"], lang, 0))
        best = {k: min(("cv10", "loo", "gcv", "aic", "aicc", "ml"), key=lambda c: r[k][c]["r_med"]) for k in ("summary", "summary_prior")}
        if c == best["summary"]:
            cells[2] = f"<b>{cells[2]}</b>"
        if c == best["summary_prior"]:
            cells[5] = f"<b>{cells[5]}</b>"
        rows.append(cells)
    cols = (["critério", "β fixo: log₁₀ λ escolhido", "razão", "≤ 1,1", "β da priori: log₁₀ λ escolhido", "razão", "≤ 1,1"] if pt else
            ["criterion", "fixed β: chosen log₁₀ λ", "ratio", "≤ 1.1", "β from prior: chosen log₁₀ λ", "ratio", "≤ 1.1"])
    cap = (f"{r['M']} conjuntos de dados por cenário, n = {r['n']}, p = {r['p']}, preditores AR(1) com ρ = {f(r['rho'], 1)}, σ = {f(r['sigma'], 0)}. "
           "À esquerda, coeficientes fixos que decaem geometricamente; à direita, coeficientes sorteados de "
           f"\\(N(0, \\tau^2)\\) com \\(\\tau = {f(r['tau'], 3)}\\) — exatamente a priori que a verossimilhança marginal supõe. "
           "<b>log₁₀ λ escolhido</b>: mediana (quartis) do λ escolhido. <b>Razão</b>: mediana de (erro de previsão com o λ escolhido − σ²) / "
           "(erro com o λ ótimo − σ²); 1 é perfeito. <b>≤ 1,1</b>: fração dos conjuntos em que o excesso de erro ficou a menos de 10% do mínimo." if pt else
           f"{r['M']} datasets per scenario, n = {r['n']}, p = {r['p']}, AR(1) predictors with ρ = {f(r['rho'], 1)}, σ = {f(r['sigma'], 0)}. "
           "Left, fixed coefficients that decay geometrically; right, coefficients drawn from "
           f"\\(N(0, \\tau^2)\\) with \\(\\tau = {f(r['tau'], 3)}\\) — exactly the prior the marginal likelihood assumes. "
           "<b>chosen log₁₀ λ</b>: median (quartiles) of the chosen λ. <b>Ratio</b>: median of (prediction error at the chosen λ − σ²) / "
           "(error at the optimal λ − σ²); 1 is perfect. <b>≤ 1.1</b>: share of datasets where the excess error was within 10% of the minimum.")
    return _tbl(cols, rows, hl={6}) + _cap(cap)


# ------------------------------------------------------------------ KRR: validation surface with the points each method tried
def surface_fig(site: Site, lang: str) -> str:
    s = site.data["hyper"]["opt"]["surface"]
    box = site.data["hyper"]["opt"]["box"]
    pt = lang == "pt"
    n, Z = s["n"], s["z"]
    zmin = min(min(r) for r in Z)
    zmax = max(max(r) for r in Z)
    W, H, pw, gap, l, t, b = 660, 262, 190, 25, 34, 24, 34
    out = []
    titles = [("grid", NAMES[lang]["grid"] + " 3×3×3"), ("random", NAMES[lang]["random"]), ("bo", NAMES[lang]["bo"])]
    for k, (key, title) in enumerate(titles):
        x0 = l + k * (pw + gap)
        X = lambda u, x0=x0: x0 + u * pw                         # noqa: E731
        Y = lambda u: t + (1 - u) * pw                            # noqa: E731
        out.append(f'<text x="{x0}" y="{t - 8}" class="t-strong">{esc(title)}</text>')
        c = pw / (n - 1)
        out.append(f'<clipPath id="hp-clip{k}"><rect x="{x0}" y="{t}" width="{pw}" height="{pw}"/></clipPath><g clip-path="url(#hp-clip{k})">')
        for j, row in enumerate(Z):               # row j = gamma index, column i = lambda index
            for i, z in enumerate(row):
                op = 0.04 + 0.88 * (1 - min((z - zmin) / 0.3, 1.0)) ** 1.3
                out.append(f'<rect x="{X(i / (n - 1)) - c / 2:.1f}" y="{Y(j / (n - 1)) - c / 2:.1f}" width="{c + 0.4:.1f}" '
                           f'height="{c + 0.4:.1f}" fill="var(--accent)" fill-opacity="{op:.2f}"/>')
        out.append("</g>")
        out.append(f'<rect x="{x0}" y="{t}" width="{pw}" height="{pw}" fill="none" stroke="var(--line-strong)"/>')
        pts = s[key]
        for u in pts:
            if key == "grid":
                out.append(f'<rect x="{X(u[0]) - 3.5:.1f}" y="{Y(u[1]) - 3.5:.1f}" width="7" height="7" fill="var(--bg)" stroke="var(--text)" stroke-width="1.4"/>')
            else:
                col = "var(--signal)" if key == "bo" else "var(--text)"
                out.append(f'<circle cx="{X(u[0]):.1f}" cy="{Y(u[1]):.1f}" r="3" fill="var(--bg)" stroke="{col}" stroke-width="1.4"/>')
        bu = s["best"][key]
        out.append(f'<circle cx="{X(bu[0]):.1f}" cy="{Y(bu[1]):.1f}" r="7" fill="none" stroke="var(--signal)" stroke-width="1.6"/>')
        for v in range(int(box[0][0]), int(box[0][1]) + 1, 2):
            u = (v - box[0][0]) / (box[0][1] - box[0][0])
            out.append(f'<text x="{X(u):.1f}" y="{t + pw + 14}" text-anchor="middle">{v}</text>')
        out.append(f'<text x="{x0 + pw}" y="{t + pw + 28}" text-anchor="end">log₁₀ λ</text>')
        if k == 0:
            for v in range(int(box[1][0]), int(box[1][1]) + 1):
                u = (v - box[1][0]) / (box[1][1] - box[1][0])
                out.append(f'<text x="{x0 - 5}" y="{Y(u) + 4:.1f}" text-anchor="end">{v}</text>')
            out.append(f'<text x="{x0 - 5}" y="{t - 8}" text-anchor="end">log₁₀ γ</text>')
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="validation error surface over log lambda and log gamma with the points '
           f'evaluated by grid search, random search and Bayesian optimisation">{"".join(out)}</svg>')
    head = "onde cada método gastou suas 27 avaliações" if pt else "where each method spent its 27 evaluations"
    cap = ("Primeira réplica do experimento. Fundo: erro de validação da regressão kernel em função de λ e da largura γ do kernel RBF, com o "
           "terceiro hiperparâmetro (peso a do kernel linear) fixado em 0; quanto mais intensa a cor, menor o erro (regiões quase transparentes erram o dobro do mínimo ou mais). Os pontos são as configurações "
           "avaliadas, projetadas nesse plano — a grade tem 27 pontos, mas como a não importa, eles caem em só 9 posições. O círculo maior marca "
           "a configuração escolhida. O vale diagonal mostra a interação: um γ menor (kernel mais suave) pede um λ menor." if pt else
           "First replication of the experiment. Background: validation error of kernel ridge regression as a function of λ and the RBF width γ, "
           "with the third hyperparameter (linear-kernel weight a) fixed at 0; the more intense the colour, the lower the error (near-transparent regions have twice the minimum error or more). Points are the configurations evaluated, "
           "projected onto this plane — the grid has 27 points, but because a does not matter they land on only 9 spots. The larger circle marks "
           "the configuration chosen. The diagonal valley is the interaction: a smaller γ (smoother kernel) wants a smaller λ.")
    return _panel(head, "R = 1", svg, cap)


# ------------------------------------------------------------------ optimisers: summary table
def opt_table(site: Site, lang: str) -> str:
    o, a = site.data["hyper"]["opt"], site.data["hyper"]["ard"]
    pt = lang == "pt"
    f = lambda v: num(v, lang, 3)                       # noqa: E731
    rows = []
    for block, d, methods in (("3", o, ("grid", "random", "bo", "sh")), ("6", a, ("grid", "random", "bo"))):
        for m in methods:
            s = d["summary"][m]
            lab = NAMES[lang][m] + (f" ({'2⁶' if block == '6' else '3³'})" if m == "grid" else "")
            win = "—" if s["win_vs_random"] is None else _pct(s["win_vs_random"], lang, 0)
            cell = f"{f(s['test_med'])} <span class=muted>({f(s['test_q1'])}–{f(s['test_q3'])})</span>"
            if m == "bo" and block == "6":
                cell = f"<b>{cell}</b>"
            rows.append([f"{block} · {d['budget']}", lab, f(s["val_mean"]), cell, win])
    cols = (["hiperparâmetros · orçamento", "método", "erro de validação do escolhido (média)", "erro de teste (mediana e quartis)",
             "vence a busca aleatória"] if pt else
            ["hyperparameters · budget", "method", "validation error of the winner (mean)", "test error (median and quartiles)",
             "beats random search"])
    nte = num(o["n_test"], lang, 0) if o["n_test"] < 1000 else f"{o['n_test']:,}".replace(",", "." if pt else ",")
    cap = (f"Regressão kernel, n = {o['n_train']} treino, {o['n_val']} validação, {nte} teste"
           f"; o menor erro possível (ruído) é {f(o['bayes'])}. Bloco de 3 hiperparâmetros (λ, γ, a): {o['R']} réplicas, 27 ajustes completos. "
           "O successive halving gasta o mesmo número de pontos de treino que 27 ajustes completos. "
           f"Bloco de 6 hiperparâmetros (λ e uma largura por variável): {a['R']} réplicas, 64 ajustes. "
           "“Vence a busca aleatória”: fração das réplicas em que o erro de teste foi menor que o da busca aleatória na mesma réplica." if pt else
           f"Kernel ridge regression, n = {o['n_train']} training, {o['n_val']} validation, {nte} test"
           f"; the lowest possible error (noise) is {f(o['bayes'])}. Three-hyperparameter block (λ, γ, a): {o['R']} replications, 27 full fits. "
           "Successive halving uses as many training points as 27 full fits. "
           f"Six-hyperparameter block (λ and one width per input): {a['R']} replications, 64 fits. "
           "“Beats random search”: share of replications whose test error was below random search's in the same replication.")
    return _tbl(cols, rows, hl={6}) + _cap(cap)


# ------------------------------------------------------------------ optimisers: best-so-far curves
def curves_fig(site: Site, lang: str) -> str:
    o, a = site.data["hyper"]["opt"], site.data["hyper"]["ard"]
    pt = lang == "pt"
    W, H, pw, gap, l, t, b = 640, 270, 265, 56, 44, 24, 36
    y0, y1 = 0.25, 0.65
    Y = lambda v: t + (y1 - min(max(v, y0), y1)) / (y1 - y0) * (H - t - b)     # noqa: E731
    out = []
    panels = ((o["curves"]["random"]["med"], o["curves"]["bo"]["med"], o["summary"]["grid"]["val_mean"], 27, "3"),
              (a["curves"]["random"], a["curves"]["bo"], a["summary"]["grid"]["val_mean"], 64, "6"))
    for k, (rnd, bo, grid, B, dim) in enumerate(panels):
        x0 = l + k * (pw + gap)
        X = lambda i, x0=x0, B=B: x0 + (i - 1) / (B - 1) * pw            # noqa: E731
        out.append(f'<text x="{x0}" y="{t - 8}" class="t-strong">{dim} {"hiperparâmetros" if pt else "hyperparameters"}</text>')
        for v in (0.25, 0.35, 0.45, 0.55, 0.65):
            out.append(f'<line class="gl" x1="{x0}" x2="{x0 + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                       f'<text x="{x0 - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>')
        for i in ([1, 9, 18, 27] if B == 27 else [1, 16, 32, 48, 64]):
            out.append(f'<text x="{X(i):.1f}" y="{H - b + 16}" text-anchor="middle">{i}</text>')
        for seq, color in ((rnd, "var(--text-2)"), (bo, "var(--signal)")):
            pts = " ".join(f"{X(i + 1):.1f},{Y(v):.1f}" for i, v in enumerate(seq))
            out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.9"/>')
        out.append(f'<circle cx="{X(B):.1f}" cy="{Y(grid):.1f}" r="4.5" fill="var(--bg)" stroke="var(--accent)" stroke-width="1.8"/>')
        out.append(f'<text x="{X(B) - 8:.1f}" y="{Y(grid) - 8:.1f}" text-anchor="end" style="fill:var(--accent)">{NAMES[lang]["grid"]}</text>')
        out.append(f'<text x="{x0 + pw}" y="{H - 4}" text-anchor="end">{"avaliações" if pt else "evaluations"}</text>')
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="best validation error so far against number of evaluations">{"".join(out)}</svg>'
    lg = _legend([(NAMES[lang]["random"], "var(--text-2)", "solid"), (NAMES[lang]["bo"], "var(--signal)", "solid"),
                  (NAMES[lang]["grid"] + (" (média, só no fim)" if pt else " (mean, end only)"), "var(--accent)", "solid")])
    head = "melhor erro de validação até a avaliação k" if pt else "best validation error up to evaluation k"
    cap = ("Mediana entre as réplicas. A otimização bayesiana começa com 5 (à esquerda) ou 8 (à direita) pontos aleatórios e por isso "
           "acompanha a busca aleatória no início; depois disso ela usa o que já viu. A grade só tem resultado quando termina." if pt else
           "Median over replications. Bayesian optimisation starts with 5 (left) or 8 (right) random points, so it tracks random search at first; "
           "after that it uses what it has seen. The grid only has a result once it finishes.")
    return _panel(head, "y: " + ("erro de validação" if pt else "validation error"), svg, cap, lg)


# ------------------------------------------------------------------ winner's curse
def curse_table(site: Site, lang: str) -> str:
    o = site.data["hyper"]["opt"]
    pt = lang == "pt"
    f = lambda v: num(v, lang, 3)                       # noqa: E731
    rows = [[str(c["k"]), f(c["val"]), f(c["test"]), f"<b>{f(c['gap'])}</b> <span class=muted>± {f(c['gap_se'])}</span>"]
            for c in o["curse"]]
    cols = (["configurações testadas", "erro de validação do vencedor", "erro de teste do vencedor", "otimismo (teste − validação)"] if pt else
            ["configurations tried", "validation error of the winner", "test error of the winner", "optimism (test − validation)"])
    cap = (f"Médias sobre {o['R']} réplicas; as k configurações são as k primeiras de uma mesma busca aleatória de 243. "
           "Com k = 1 não há seleção, e o otimismo é zero dentro do erro de Monte Carlo (o “±” é um erro-padrão). Ele cresce com k: "
           "quanto mais configurações competem, mais o vencedor deve parte da vitória ao ruído da validação." if pt else
           f"Means over {o['R']} replications; the k configurations are the first k of one random search of 243. "
           "With k = 1 there is no selection and the optimism is zero within Monte Carlo error (the “±” is one standard error). It grows with k: "
           "the more configurations compete, the more the winner owes its win to noise in the validation set.")
    return _tbl(cols, rows) + _cap(cap)


COMPONENTS = {"hp-ridge-fig": ridge_fig, "hp-ridge-table": ridge_table, "hp-surface": surface_fig,
              "hp-opt-table": opt_table, "hp-curves": curves_fig, "hp-curse": curse_table}
