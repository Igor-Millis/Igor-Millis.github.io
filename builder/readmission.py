"""Project page: 30-day readmission of diabetic inpatients (data from data/readmission.json)."""
from __future__ import annotations

import math

from .bootstrap import _legend
from .charts import ci_bars
from .core import Site, attr, esc, integer, num


def _pct(x: float, lang: str, d: int = 1) -> str:
    return num(100 * x, lang, d) + "%"


def _iv(lo: float, hi: float, lang: str, d: int = 3) -> str:
    return f"[{num(lo, lang, d)}; {num(hi, lang, d)}]" if lang == "pt" else f"[{num(lo, lang, d)}, {num(hi, lang, d)}]"


def _signed(v: float, lang: str, d: int = 3) -> str:
    return ("+" if v >= 0 else "−") + num(abs(v), lang, d)


def panel(head: str, right: str, inner: str, cap: str, legend: str = "") -> str:
    return f"""<figure class="panel">
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(head)}</span><span>{esc(right)}</span></div>
  <div class="panel-b chart">{legend}{inner}</div>
  <figcaption style="padding:0 18px 16px">{cap}</figcaption>
</figure>"""


# ------------------------------------------------------------------ generic xy line chart
def _xy(series: list[dict], lang: str, *, x0: float, x1: float, y0: float, y1: float, xt: list[float], yt: list[float],
        xd: int = 2, yd: int = 2, logx: bool = False, diag: bool = False, zero: bool = False, h: int = 320,
        xfmt=None, label: str = "line chart") -> str:
    """series = [{"pts": [[x, y], ...], "cls": "ln-a" | ..., "dots": bool, "name": str}]"""
    w, l, r, t, b = 640, 52, 16, 12, 34
    tx = (lambda v: math.log10(v)) if logx else (lambda v: v)
    X = lambda v: l + (tx(v) - tx(x0)) / (tx(x1) - tx(x0)) * (w - l - r)  # noqa: E731
    Y = lambda v: t + (1 - (v - y0) / (y1 - y0)) * (h - t - b)              # noqa: E731
    out = []
    for v in yt:
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, yd)}</text>')
    for v in xt:
        lab = xfmt(v) if xfmt else num(v, lang, xd)
        out.append(f'<text x="{X(v):.1f}" y="{h - 12}" text-anchor="middle">{lab}</text>')
    out.append(f'<line class="ax" x1="{l}" x2="{w - r}" y1="{h - b}" y2="{h - b}"/>')
    if zero:
        out.append(f'<line x1="{l}" x2="{w - r}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--text-3)"/>')
    if diag:
        lo, hi = max(x0, y0), min(x1, y1)
        out.append(f'<line x1="{X(lo):.1f}" y1="{Y(lo):.1f}" x2="{X(hi):.1f}" y2="{Y(hi):.1f}" stroke="var(--text-3)" stroke-dasharray="3 4"/>')
    for s in series:
        pts = [(x, y) for x, y in s["pts"] if y0 - 1e-9 <= y <= y1 + 1e-9]
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y) in enumerate(pts))
        out.append(f'<path class="{s["cls"]}" d="{d}"/>')
        if s.get("dots"):
            stroke = {"ln-a": "var(--accent)", "ln-c": "var(--signal)", "ln-b": "var(--text-2)"}[s["cls"]]
            for x, y in pts:
                out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4" fill="var(--bg)" stroke="{stroke}" stroke-width="1.5">'
                           f'<title>{esc(s.get("name", ""))}: x = {xfmt(x) if xfmt else num(x, lang, 3)} · y = {num(y, lang, 3)}</title></circle>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{attr(label)}">{"".join(out)}</svg>'


# ------------------------------------------------------------------ grouped bars (leakage)
def grouped_bars(groups: list[str], series: list[tuple[str, str, list[float]]], lang: str, *, y0: float, y1: float) -> str:
    w, h, l, r, t, b = 640, 280, 44, 10, 12, 44
    Y = lambda v: t + (1 - (v - y0) / (y1 - y0)) * (h - t - b)  # noqa: E731
    gw = (w - l - r) / len(groups)
    bw = min(34, gw / (len(series) + 1.2))
    out = []
    step = 0.02
    ticks = [round(y0 + i * step, 4) for i in range(int(round((y1 - y0) / step)) + 1)]
    for v in ticks:
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>')
    for gi, g in enumerate(groups):
        cx = l + gw * (gi + 0.5)
        x_start = cx - bw * len(series) / 2 - 2 * (len(series) - 1) / 2
        for si, (_, fill, vals) in enumerate(series):
            v = vals[gi]
            x = x_start + si * (bw + 2)
            out.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(y0) - Y(v):.1f}" fill="{fill}" rx="2">'
                       f'<title>{esc(g)} · {esc(series[si][0])}: {num(v, lang, 3)}</title></rect>'
                       f'<text x="{x + bw / 2:.1f}" y="{Y(v) - 5:.1f}" text-anchor="middle" style="font-size:10px">{num(v, lang, 3)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{h - 24}" text-anchor="middle" class="t-strong">{esc(g)}</text>')
    out.append(f'<line class="ax" x1="{l}" x2="{w - r}" y1="{Y(y0):.1f}" y2="{Y(y0):.1f}"/>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="grouped bar chart">{"".join(out)}</svg>'


# ------------------------------------------------------------------ dot + CI on a zoomed axis
def dot_ci(items: list[list], lang: str, *, lo: float, hi: float, step: float, label_w: int = 250,
           accent: str = "", signal: str = "") -> str:
    """items = [[key, label, value, ci_lo, ci_hi], ...]"""
    w, row = 640, 28
    h = len(items) * row + 30
    X = lambda v: label_w + (v - lo) / (hi - lo) * (w - label_w - 56)  # noqa: E731
    out = []
    n = int(round((hi - lo) / step))
    for i in range(n + 1):
        v = lo + i * step
        out.append(f'<line class="gl" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="0" y2="{h - 26}"/>'
                   f'<text x="{X(v):.1f}" y="{h - 8}" text-anchor="middle">{num(v, lang, 2)}</text>')
    for i, (key, label, v, a, b) in enumerate(items):
        y = i * row + row / 2
        col = "var(--accent)" if key == accent else "var(--signal)" if key == signal else "var(--text-3)"
        strong = ' class="t-strong"' if key in (accent, signal) else ""
        out.append(f'<text x="{label_w - 10}" y="{y + 4:.1f}" text-anchor="end"{strong}>{esc(label)}</text>')
        if a is not None:
            out.append(f'<line x1="{X(a):.1f}" x2="{X(b):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="2" stroke-linecap="round"/>')
        out.append(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="5" fill="{col}" stroke="var(--bg)" stroke-width="2">'
                   f'<title>{esc(label)}: {num(v, lang, 3)}{"" if a is None else " " + _iv(a, b, lang)}</title></circle>'
                   f'<text x="{w - 4}" y="{y + 4:.1f}" text-anchor="end">{num(v, lang, 3)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="point estimates with confidence intervals">{"".join(out)}</svg>'


# ------------------------------------------------------------------ forest plot (odds ratios, log scale)
def forest(rows: list[dict], lang: str, *, label_w: int = 300, lo: float = 0.4, hi: float = 2.5) -> str:
    w, row = 640, 22
    h = len(rows) * row + 34
    X = lambda v: label_w + (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)) * (w - label_w - 60)  # noqa: E731
    out = []
    for v in (0.5, 0.75, 1, 1.5, 2):
        if lo <= v <= hi:
            out.append(f'<line class="gl" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="0" y2="{h - 30}"/>'
                       f'<text x="{X(v):.1f}" y="{h - 12}" text-anchor="middle">{num(v, lang, 2)}</text>')
    out.append(f'<line x1="{X(1):.1f}" x2="{X(1):.1f}" y1="0" y2="{h - 30}" stroke="var(--text-3)"/>')
    for i, c in enumerate(rows):
        y = i * row + row / 2
        cls = "var(--accent)" if c["or"] > 1 else "var(--signal)"
        a, bb = max(c["lo"], lo), min(c["hi"], hi)
        out.append(f'<text x="{label_w - 10}" y="{y + 4:.1f}" text-anchor="end">{esc(c["label"])}</text>'
                   f'<line x1="{X(a):.1f}" x2="{X(bb):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{cls}" stroke-width="2" stroke-linecap="round"/>'
                   f'<rect x="{X(c["or"]) - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{cls}">'
                   f'<title>OR {num(c["or"], lang, 2)} {_iv(c["lo"], c["hi"], lang, 2)}</title></rect>'
                   f'<text x="{w - 4}" y="{y + 4:.1f}" text-anchor="end">{num(c["or"], lang, 2)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="odds ratio forest plot">{"".join(out)}</svg>'


# ====================================================================== page
MODEL_ORDER = ["lr_spline", "lr_enet", "lr_linear", "lr_balanced", "lgbm", "rf", "lr_one", "prevalence"]


def _p_value(v: float, lang: str) -> str:
    if v < 0.001:
        return "&lt; 0,001" if lang == "pt" else "&lt; 0.001"
    return num(v, lang, 3)


def render(site: Site, lang: str) -> str:
    from .layout import page, section
    from .pages import _project_head, _software_ld, _tab_group, table

    p = site.content[lang]["work"]["readmission"]
    d = site.data["readmission"]
    R = d["results"]
    repo, hub = d["repo"], d["hub"]
    names = p["model_names"]
    f2 = lambda v: num(v, lang, 2)  # noqa: E731
    f3 = lambda v: num(v, lang, 3)  # noqa: E731
    f4 = lambda v: num(v, lang, 4)  # noqa: E731
    pc = lambda v: _pct(v, lang)    # noqa: E731
    nanf = lambda v, fn=f3: "—" if v is None or v != v else fn(v)  # noqa: E731
    T = R["test"]
    models = [k for k in MODEL_ORDER if k in T]
    fitted = [k for k in models if k != "prevalence"]
    hl_main = {models.index("lr_spline")}

    def sec(i: int, inner: str) -> str:
        return section(esc(p[f"s{i}_label"]), esc(p[f"s{i}_title"]), inner)

    def prose(i: int, key: str = "body") -> str:
        return f'<div class="prose">{p[f"s{i}_{key}"]}</div>'

    def cap(text: str) -> str:
        return f'<p class="cap">{esc(text)}</p>'

    # ---- 1. problem / irregularities
    s1 = prose(1) + table(p["irr_cols"], p["irr_rows"], cls="l2") + cap(p["irr_cap"])

    # ---- 2. leakage
    L = R["leakage"]
    lk = [k for k in ("lr_spline", "lgbm", "rf", "rf_deep") if k in L]
    lab = {**names, "rf_deep": p["rf_deep_name"]}
    ser = [(p["leak_series"][0], "var(--line-strong)", [L[k]["encounter_split"] for k in lk]),
           (p["leak_series"][1], "var(--accent)", [L[k]["patient_split"] for k in lk]),
           (p["leak_series"][2], "var(--signal)", [L[k]["test"] for k in lk])]
    leg = _legend([(esc(n), c, "block") for n, c, _ in ser])
    lo = math.floor(min(min(v) for _, _, v in ser) * 20) / 20 - 0.05
    hi = math.ceil(max(max(v) for _, _, v in ser) * 20) / 20
    chart = grouped_bars([lab[k] for k in lk], ser, lang, y0=lo, y1=hi)
    s2 = prose(2) + panel(p["leak_head"], "ROC AUC", chart, esc(p["leak_cap"]), leg) + prose(2, "after")

    # ---- 3. features & models
    cvi = R["cv"]
    rows = []
    for k in fitted:
        bp = ", ".join(f"{a}={num(v, lang, 3) if isinstance(v, float) else v}" for a, v in cvi[k]["best_params"].items()) or "—"
        rows.append([esc(names[k]), esc(p["model_desc"][k]), f"<code>{esc(bp)}</code>",
                     f4(cvi[k]["cv_logloss"]) if cvi[k]["cv_logloss"] is not None else "—"])
    s3 = prose(3) + table(p["models_cols"], rows, hl={0}, cls="l2") + cap(p["models_cap"]) + prose(3, "after")

    # ---- 4. headline comparison: ranking + probabilistic + paired differences
    ci = R["ci"]
    order = sorted(fitted, key=lambda k: -T[k]["auc"])
    bars = dot_ci([[k, names[k], T[k]["auc"], ci[k]["auc"][0], ci[k]["auc"][1]] for k in order], lang,
                  lo=0.58, hi=0.70, step=0.02, accent="lr_spline", signal="lgbm")
    one = "1,00×" if lang == "pt" else "1.00×"
    rk = [[esc(names[k]), f3(T[k]["auc"]), _iv(*ci[k]["auc"], lang) if k in ci else "—", f3(T[k]["gini"]), f3(T[k]["ks"]),
           f3(T[k]["ap"]), f2(T[k]["ap_lift"]) + "×",
           pc(T[k]["recall@10%"]) if k in ci else "10,0%" if lang == "pt" else "10.0%",
           pc(T[k]["recall@20%"]) if k in ci else "20,0%" if lang == "pt" else "20.0%",
           f2(T[k]["lift@10%"]) + "×" if k in ci else one] for k in models]
    pr = [[esc(names[k]), f4(T[k]["brier"]), _iv(*ci[k]["brier"], lang, 4) if k in ci else "—", pc(T[k]["brier_skill"]),
           f4(T[k]["logloss"]), pc(T[k]["logloss_skill"]), f3(T[k]["discrimination_slope"])] for k in models]
    P = R["paired_vs_lr_spline"]
    prow = []
    for k in [m for m in models if m in P]:
        cells = [esc(names[k])]
        for m, dg in (("auc", 3), ("ap", 3), ("brier", 5), ("logloss", 4)):
            q = P[k][m]
            cells.append(f'{_signed(q["diff"], lang, dg)}<br><span class="muted">{_iv(q["lo"], q["hi"], lang, dg)}</span>')
        qa = P[k]["auc"]
        cells.append(esc(p["verdict_better"] if qa["lo"] > 0 else p["verdict_worse"] if qa["hi"] < 0 else p["verdict_tie"]))
        prow.append(cells)
    s4 = (prose(4) + panel(p["auc_head"], f'n = {integer(R["split"]["test"], lang)}', bars, esc(p["auc_cap"]))
          + f'<h3>{esc(p["rank_title"])}</h3>' + table(p["rank_cols"], rk, hl=hl_main, cls="l2") + cap(p["rank_cap"])
          + f'<h3>{esc(p["prob_title"])}</h3>' + table(p["prob_cols"], pr, hl=hl_main, cls="l2") + cap(p["prob_cap"])
          + f'<h3>{esc(p["paired_title"])}</h3>' + table(p["paired_cols"], prow, cls="l2") + cap(p["paired_cap"])
          + prose(4, "after"))
    G = d["gap"]
    grows = [[esc(names["lr_spline"]), "201", f4(cvi["lr_spline"]["cv_logloss"]), f3(T["lr_spline"]["auc"]), "—",
              _signed(-P["lgbm"]["auc"]["diff"], lang), f3(T["lr_spline"]["ap"]), f4(T["lr_spline"]["brier"]), f2(T["lr_spline"]["cal_slope"])]]
    for k in ("lr_icd3", "lr_inter", "lr_full"):
        t, i, q = G["test"][k], G["info"][k], G["paired"][k]
        grows.append([esc(p["gap_names"][k]), str(i["n_features"]), f4(i["cv_logloss"]), f3(t["auc"]),
                      f'{_signed(q["lr_spline"]["diff"], lang)}<br><span class="muted">{_iv(q["lr_spline"]["lo"], q["lr_spline"]["hi"], lang)}</span>',
                      f'{_signed(q["lgbm"]["diff"], lang)}<br><span class="muted">{_iv(q["lgbm"]["lo"], q["lgbm"]["hi"], lang)}</span>',
                      f3(t["ap"]), f4(t["brier"]), f2(t["cal_slope"])])
    grows.append([esc(names["lgbm"]), "—", f4(cvi["lgbm"]["cv_logloss"]), f3(T["lgbm"]["auc"]), _signed(P["lgbm"]["auc"]["diff"], lang), "—",
                  f3(T["lgbm"]["ap"]), f4(T["lgbm"]["brier"]), f2(T["lgbm"]["cal_slope"])])
    s4 += (f'<h3>{esc(p["gap_title"])}</h3>' + table(p["gap_cols"], grows, hl={3}, cls="l2") + cap(p["gap_cap"])
           + prose(4, "gap_after"))

    # ---- 5. threshold metrics, one tab per policy
    TM = R["at_threshold"]
    tabs = []
    for pol, code in (("f1_opt", "F1*"), ("youden_opt", "J*"), ("top20", "20%"), ("default_0.5", "0.5")):
        rows = []
        for k in [m for m in models if m in TM]:
            m = TM[k][pol]
            rows.append([esc(names[k]), f3(m["threshold"]), pc(m["flag_rate"]), f3(m["accuracy"]), f3(m["balanced_accuracy"]),
                         nanf(m["precision"]), f3(m["recall"]), f3(m["specificity"]), nanf(m["npv"]), f3(m["f1"]),
                         f3(m["f2"]), f3(m["mcc"]), f3(m["kappa"]), nanf(m["lr_pos"], f2), nanf(m["lr_neg"], f2),
                         nanf(m["dor"], f2)])
        tabs.append([code, p["thr_tabs"][pol], table(p["thr_cols"], rows, hl={0}, cls="l2") + cap(p["thr_caps"][pol])])
    s5 = prose(5) + _tab_group("rthr", tabs) + prose(5, "after")

    # ---- 6. calibration
    rel = R["reliability"]
    series = [{"pts": [[q["mean_p"], q["obs"]] for q in rel["lr_balanced"]], "cls": "ln-b", "dots": True, "name": names["lr_balanced"]},
              {"pts": [[q["mean_p"], q["obs"]] for q in rel["lgbm"]], "cls": "ln-c", "dots": True, "name": names["lgbm"]},
              {"pts": [[q["mean_p"], q["obs"]] for q in rel["lr_spline"]], "cls": "ln-a", "dots": True, "name": names["lr_spline"]}]
    xmax = math.ceil(max(q["mean_p"] for q in rel["lr_balanced"]) * 10) / 10
    ymax = math.ceil(max(q["obs"] for k in rel for q in rel[k]) * 10) / 10
    ch = _xy(series, lang, x0=0, x1=xmax, y0=0, y1=ymax, xt=[i / 10 for i in range(int(round(xmax * 10)) + 1)],
             yt=[i / 10 for i in range(int(round(ymax * 10)) + 1)], xd=1, yd=1, diag=True, label="reliability diagram")
    leg = _legend([(esc(names["lr_spline"]), "var(--accent)", "solid"), (esc(names["lgbm"]), "var(--signal)", "solid"),
                   (esc(names["lr_balanced"]), "var(--text-2)", "dash"), (esc(p["perfect"]), "var(--text-3)", "dash")])
    cal = [[esc(names[k]), f3(T[k]["mean_p"]), f2(T[k]["oe_ratio"]), f3(T[k]["cal_intercept"]), f3(T[k]["cal_slope"]),
            f4(T[k]["ece"]), f4(T[k]["mce"]), f2(T[k]["spiegelhalter_z"]), f2(T[k]["hosmer_lemeshow"]),
            _p_value(T[k]["hosmer_lemeshow_p"], lang)] for k in fitted]
    s6 = (prose(6) + panel(p["cal_head"], p["cal_right"], ch, esc(p["cal_cap"]), leg)
          + table(p["cal_cols"], cal, hl={0}, cls="l2") + cap(p["cal_tcap"]) + prose(6, "after"))

    # ---- 7. interpretation
    inf = R["inference"]
    co = [dict(c) for c in inf["coefs"] if abs(c["z"]) > 3.5]
    co.sort(key=lambda c: -c["or"])
    for c in co:
        c["label"] = p["term_labels"].get(c["term"], c["label"])
    fp_ = forest(co, lang, lo=min(0.4, min(c["lo"] for c in co) * 0.95), hi=max(2.5, max(c["hi"] for c in co) * 1.05))
    leg = _legend([(esc(p["or_up"]), "var(--accent)", "solid"), (esc(p["or_down"]), "var(--signal)", "solid")])
    s7 = prose(7) + panel(p["or_head"], f'n = {integer(inf["n"], lang)} · p = {inf["p"]}', fp_, esc(p["or_cap"]), leg) + prose(7, "after")

    # ---- 8. decisions: decision curve, learning curve, subgroups
    dca = R["dca"]
    th = dca["thresholds"]
    mx = max(max(dca["lr_spline"]), max(dca["lgbm"]))
    ytop = math.ceil(mx * 100) / 100 + 0.01
    ys = [round(i / 100, 2) for i in range(0, int(round(ytop * 100)) + 1)]
    dser = [{"pts": list(zip(th, dca["treat_all"])), "cls": "ln-b", "name": p["treat_all"]},
            {"pts": list(zip(th, dca["lgbm"])), "cls": "ln-c", "name": names["lgbm"]},
            {"pts": list(zip(th, dca["lr_spline"])), "cls": "ln-a", "name": names["lr_spline"]}]
    dch = _xy(dser, lang, x0=th[0], x1=th[-1], y0=-0.005, y1=ytop, xt=[0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
              yt=ys, xd=2, yd=2, zero=True, label="decision curve")
    leg = _legend([(esc(names["lr_spline"]), "var(--accent)", "solid"), (esc(names["lgbm"]), "var(--signal)", "solid"),
                   (esc(p["treat_all"]), "var(--text-2)", "dash"), (esc(p["treat_none"]), "var(--text-3)", "solid")])
    lc = R["learning_curve"]
    lmin = math.floor(min(lc["lr_spline"] + lc["lgbm"]) * 50) / 50
    lmax = math.ceil(max(lc["lr_spline"] + lc["lgbm"]) * 50) / 50
    lser = [{"pts": list(zip(lc["n"], lc["lgbm"])), "cls": "ln-c", "dots": True, "name": names["lgbm"]},
            {"pts": list(zip(lc["n"], lc["lr_spline"])), "cls": "ln-a", "dots": True, "name": names["lr_spline"]}]
    lch = _xy(lser, lang, x0=lc["n"][0] * 0.8, x1=lc["n"][-1] * 1.25, y0=lmin, y1=lmax, logx=True, xt=lc["n"],
              yt=[round(lmin + i * (lmax - lmin) / 4, 3) for i in range(5)], yd=3, xfmt=lambda v: integer(int(v), lang),
              label="learning curve", h=280)
    leg2 = _legend([(esc(names["lr_spline"]), "var(--accent)", "solid"), (esc(names["lgbm"]), "var(--signal)", "solid")])
    sub = [[esc(p["sub_vars"][r["var"]]), esc(p["sub_levels"].get(r["level"], r["level"])), integer(r["n"], lang),
            pc(r["prev"]), pc(r["mean_p"]), f3(r["auc"])] for r in R["subgroups"]]
    s8 = (prose(8) + panel(p["dca_head"], p["dca_right"], dch, esc(p["dca_cap"]), leg) + prose(8, "mid")
          + panel(p["lc_head"], "ROC AUC", lch, esc(p["lc_cap"]), leg2)
          + f'<h3>{esc(p["sub_title"])}</h3>' + table(p["sub_cols"], sub, cls="l2") + cap(p["sub_cap"]))

    # ---- 9. reproducibility & limits
    s9 = prose(9).replace("{hub}", hub).replace("{repo}", repo)

    body = _project_head(site, lang, p, repo) + "".join(
        sec(i, s) for i, s in enumerate((s1, s2, s3, s4, s5, s6, s7, s8, s9), start=1))
    return page(site, lang, "readmission", title=p["title"], description=p["description"], body=body,
                scripts=("js/recommender.js",), jsonld=_software_ld(site, lang, "readmission", p, repo, ["Python"]))
