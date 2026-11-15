"""Project page: logistic regression for dengue cases (numbers from data/dengue.json)."""
from __future__ import annotations

import math

from .bootstrap import _legend
from .core import Site, attr, esc, num
from .readmission import dot_ci, panel


def _p(v: float, lang: str) -> str:
    if v < 0.001:
        return "&lt; 0,001" if lang == "pt" else "&lt; 0.001"
    return num(v, lang, 4 if v < 0.01 else 3)


def _iv(lo: float, hi: float, lang: str, d: int = 2) -> str:
    return f"[{num(lo, lang, d)}; {num(hi, lang, d)}]" if lang == "pt" else f"[{num(lo, lang, d)}, {num(hi, lang, d)}]"


def _band(label: str) -> str:
    """'[10,20)' -> '10–19'; the open last band '[60,90)' -> '60+'."""
    a, b = label.strip("[)").split(",")
    return f"{a}+" if int(b) >= 90 else f"{a}–{int(b) - 1}"


# ------------------------------------------------------------------ odds-ratio forest (log axis, custom ticks)
def forest(rows: list[dict], lang: str, *, lo: float, hi: float, ticks: list[float], label_w: int = 190) -> str:
    w, row = 640, 24
    h = len(rows) * row + 34
    X = lambda v: label_w + (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)) * (w - label_w - 64)  # noqa: E731
    out = []
    for v in ticks:
        out.append(f'<line class="gl" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="0" y2="{h - 30}"/>'
                   f'<text x="{X(v):.1f}" y="{h - 12}" text-anchor="middle">{num(v, lang, 2 if v < 1 else 0)}</text>')
    out.append(f'<line x1="{X(1):.1f}" x2="{X(1):.1f}" y1="0" y2="{h - 30}" stroke="var(--text-3)"/>')
    for i, c in enumerate(rows):
        y = i * row + row / 2
        col = "var(--accent)" if c["or"] > 1 else "var(--signal)"
        a, b = max(c["lo"], lo), min(c["hi"], hi)
        out.append(f'<text x="{label_w - 10}" y="{y + 4:.1f}" text-anchor="end">{esc(c["label"])}</text>'
                   f'<line x1="{X(a):.1f}" x2="{X(b):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="2" stroke-linecap="round"/>'
                   f'<rect x="{X(c["or"]) - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{col}">'
                   f'<title>OR {num(c["or"], lang, 2)} {_iv(c["lo"], c["hi"], lang)}</title></rect>'
                   f'<text x="{w - 4}" y="{y + 4:.1f}" text-anchor="end">{num(c["or"], lang, 2)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="odds ratio forest plot">{"".join(out)}</svg>'


# ------------------------------------------------------------------ fitted probability curves with 95% bands
def curves_svg(cur_a: list[list[float]], cur_b: list[list[float]], obs: list[dict], lang: str, label: str) -> str:
    w, h, l, r, t, b = 640, 330, 52, 16, 12, 34
    X = lambda a: l + a / 90 * (w - l - r)           # noqa: E731
    Y = lambda p: t + (1 - p) * (h - t - b)          # noqa: E731
    out = []
    for v in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>'
                   f'<text x="{l - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{num(v, lang, 2)}</text>')
    for a in (0, 20, 40, 60, 80):
        out.append(f'<text x="{X(a):.1f}" y="{h - 12}" text-anchor="middle">{a}</text>')
    out.append(f'<line class="ax" x1="{l}" x2="{w - r}" y1="{h - b}" y2="{h - b}"/>')

    def band(cur: list[list[float]], color: str) -> str:
        up = " ".join(f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(hi):.1f}" for i, (a, _, _, hi) in enumerate(cur))
        dn = " ".join(f"L{X(a):.1f},{Y(lo):.1f}" for a, _, lo, _ in reversed(cur))
        return f'<path d="{up} {dn} Z" fill="{color}" opacity=".13"/>'

    def line(cur: list[list[float]], cls: str) -> str:
        return f'<path class="{cls}" d="' + " ".join(f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(p):.1f}" for i, (a, p, _, _) in enumerate(cur)) + '"/>'

    out += [band(cur_a, "var(--signal)"), band(cur_b, "var(--accent)"), line(cur_a, "ln-c"), line(cur_b, "ln-a")]
    nmax = max((o["n"] for o in obs), default=1)
    for o in obs:
        rad = 3 + 6 * math.sqrt(o["n"] / nmax)
        out.append(f'<circle cx="{X(o["idade_media"]):.1f}" cy="{Y(o["p"]):.1f}" r="{rad:.1f}" fill="var(--bg)" stroke="var(--text-2)" stroke-width="1.5">'
                   f'<title>{esc(_band(o["faixa"]))} · n = {o["n"]} · {num(100 * o["p"], lang, 0)}%</title></circle>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{attr(label)}">{"".join(out)}</svg>'


# ====================================================================== page
def render(site: Site, lang: str) -> str:
    from .layout import page, section
    from .pages import _project_head, table

    p = site.content[lang]["work"]["dengue"]
    d = site.data["dengue"]
    M, L, C = d["models"], d["lrt"], d["coef"]
    f2 = lambda v: num(v, lang, 2)  # noqa: E731
    f3 = lambda v: num(v, lang, 3)  # noqa: E731
    coef = lambda m, term: next(c for c in C[m] if c["term"] == term)  # noqa: E731

    def prose(key: str, **kw) -> str:
        return f'<div class="prose">{p[key].format(**kw) if kw else p[key]}</div>'

    def cap(text: str) -> str:
        return f'<p class="cap">{esc(text)}</p>'

    def plain(html: str) -> str:
        return f'<aside class="plain" aria-label="{attr(p["plain_label"])}"><span class="label">{esc(p["plain_label"])}</span>{html}</aside>'

    def sec(i: int, inner: str) -> str:
        box = plain(p[f"s{i}_plain"]) if p.get(f"s{i}_plain") else ""
        return section(esc(p[f"s{i}_label"]), esc(p[f"s{i}_title"]), box + inner)

    # ---- 1. data: observed shares
    sh = [[f"s{r['rotulo'].split()[-1]}", p["lbl_setor"].format(r["rotulo"].split()[-1]), r["p"], r["lo"], r["hi"]] for r in d["by_setor"]]
    sh += [[f"n{r['rotulo'].split()[-1]}", p["lbl_nivel"].format(r["rotulo"].split()[-1]), r["p"], r["lo"], r["hi"]] for r in d["by_nivel"]]
    chart_sh = dot_ci(sh, lang, lo=0, hi=0.6, step=0.1, label_w=150, accent="s2")
    ag = [[f"a{i}", f"{_band(r['faixa'])} (n = {r['n']})", r["p"], r["lo"], r["hi"]] for i, r in enumerate(d["by_age10"])]
    chart_ag = dot_ci(ag, lang, lo=0, hi=0.8, step=0.2, label_w=150)
    s1 = (prose("s1_body", n=d["n"], cases=d["cases"], pct=num(100 * d["cases"] / d["n"], lang, 1), n40=d["n_40"])
          + f'<div class="fig-grid" style="margin-top:28px">'
          + panel(p["share_head"], "IC 95% Wilson", chart_sh, esc(p["share_cap"]))
          + panel(p["age_head"], "IC 95% Wilson", chart_ag, esc(p["age_cap"])) + "</div>")

    # ---- 2. initial model + selection tests
    names = p["term_names"]
    rows_f = [{"label": names[c["term"]], "or": c["or"], "lo": c["lo"], "hi": c["hi"]} for c in C["ini"] if c["term"] != "(Intercept)"]
    chart_f = forest(rows_f, lang, lo=0.3, hi=8, ticks=[0.5, 1, 2, 4, 8])
    lrt_rows = [[esc(lbl), f3(L[k]["dev"]), str(L[k]["df"]), _p(L[k]["p"], lang)] for lbl, k in p["lrt_rows"]]
    s2 = (prose("s2_body")
          + panel(p["or_head"], "OR · IC 95%", chart_f, esc(p["or_cap"]))
          + prose("s2_after") + table(p["lrt_cols"], lrt_rows, cls="l2") + cap(p["lrt_cap"]))

    # ---- 3. age is not linear
    A, B = d["curves"]["A"], d["curves"]["B"]
    leg = _legend([(esc(p["name_A"]), "var(--signal)", "solid"), (esc(p["name_B"]), "var(--accent)", "solid")])
    panels = ""
    for s in ("1", "2"):
        obs = [o for o in d["by_age4_setor"] if o["setor"] == s and isinstance(o["p"], (int, float))]
        panels += panel(p["curve_head"].format(s), "P(caso)" if lang == "pt" else "P(case)",
                        curves_svg(A[s], B[s], obs, lang, p["curve_head"].format(s)), "", leg if s == "1" else "")
    v = d["vertex"]
    s3 = (prose("s3_body", p_quad=_p(L["quad"]["p"], lang), dev=num(L["quad"]["dev"], lang, 2), aic_a=f2(M["A"]["aic"]),
                aic_b=f2(M["B"]["aic"]), vx=num(v["est"], lang, 1), vlo=num(v["lo"], lang, 0), vhi=num(v["hi"], lang, 0))
          + f'<div class="fig-grid" style="margin-top:28px">{panels}</div>' + cap(p["curve_cap"]) + prose("s3_after"))

    # ---- 4. odds ratio by age interval
    OI = d["or_interval"]
    fmt_or = lambda t: f"{f2(t[0])} ({f2(t[1])} {'a' if lang == 'pt' else 'to'} {f2(t[2])})"  # noqa: E731
    or_rows = [[f"{o['a1']} → {o['a2']}", fmt_or(o["A"]), fmt_or(o["B"])] for o in OI]
    rows_b = [{"label": f"{o['a1']} → {o['a2']}", "or": o["B"][0], "lo": o["B"][1], "hi": o["B"][2]} for o in OI]
    chart_oi = forest(rows_b, lang, lo=0.3, hi=3, ticks=[0.5, 1, 2], label_w=110)
    s4 = (prose("s4_body", n60=d["n_60"], n40=d["n_40"])
          + table(p["oi_cols"], or_rows, cls="l2")
          + panel(p["oi_head"], "OR · IC 95%", chart_oi, esc(p["oi_cap"])) + prose("s4_after"))

    # ---- 5. link function and diagnostics
    K = d["links"]
    link_rows = [[lk, f2(K["A"][lk]), f2(K["B"][lk])] for lk in ("logit", "probit", "cloglog")]
    DH, CK = d["dharma"], d["cook_max"]
    diag_rows = [[esc(lbl), _p(DH["A"][k], lang), _p(DH["B"][k], lang)] for lbl, k in p["diag_rows"]]
    diag_rows.append([esc(p["cook_label"]), f3(CK["A"]), f3(CK["B"])])
    diag_rows.append(["AUC", f3(M["A"]["auc"]), f3(M["B"]["auc"])])
    s5 = (prose("s5_body", lt_a=_p(K["linktest_A"], lang), lt_b=_p(K["linktest_B"], lang))
          + table(p["link_cols"], link_rows, cls="l2") + cap(p["link_cap"])
          + table(p["diag_cols"], diag_rows, cls="l2") + cap(p["diag_cap"]) + prose("s5_after"))

    # ---- 6. two candidates, decision left open
    sa, sb = coef("A", "setor2"), coef("B", "setor2")
    cmp_rows = [
        [esc(p["cmp_formula"]), "<code>caso ~ idade + setor</code>", "<code>caso ~ idade + idade² + setor</code>"],
        ["AIC", f2(M["A"]["aic"]), f2(M["B"]["aic"])],
        ["BIC", f2(M["A"]["bic"]), f2(M["B"]["bic"])],
        ["AUC", f3(M["A"]["auc"]), f3(M["B"]["auc"])],
        ["R² McFadden", f3(M["A"]["mcfadden"]), f3(M["B"]["mcfadden"])],
        [esc(p["cmp_or_sector"]), f"{f2(sa['or'])} {_iv(sa['lo'], sa['hi'], lang)}", f"{f2(sb['or'])} {_iv(sb['lo'], sb['hi'], lang)}"],
        [esc(p["cmp_age"]), esc(p["cmp_age_a"].format(or_year=num(coef("A", "idade")["or"], lang, 3))), esc(p["cmp_age_b"])],
    ]
    s6 = (prose("s6_body") + table(p["cmp_cols"], cmp_rows, cls="l2")
          + f'<div class="note">{p["s6_note"]}</div>')

    # ---- 7. limits
    s7 = prose("s7_body", n40=d["n_40"])

    body = (_project_head(site, lang, p, "") + sec(1, s1) + sec(2, s2) + sec(3, s3) + sec(4, s4) + sec(5, s5)
            + sec(6, s6) + sec(7, s7))
    ld = {"@context": "https://schema.org", "@type": "CreativeWork", "name": p["name"], "description": attr(p["description"]),
          "url": site.abs_url(lang, "dengue"), "author": {"@type": "Person", "name": site.config["author"]["name"]}}
    return page(site, lang, "dengue", title=p["title"], description=p["description"], body=body, jsonld=ld)
