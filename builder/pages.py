"""Page renderers. Each returns (route_key, html) for one language."""
from __future__ import annotations

import json

from .charts import ci_bars, hbars, threshold_chart
from .charts import reliability as reliability_svg
from .bets import COMPONENTS as BETS_COMPONENTS
from .bootstrap import COMPONENTS as BOOT_COMPONENTS
from .negbin import COMPONENTS as NB_COMPONENTS
from .quasi import COMPONENTS as QL_COMPONENTS
from .readmission import render as _readmission
from .core import NOTES, ROOT, Site, attr, esc, integer, num
from .layout import page, section

KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"


# ---------------------------------------------------------------- components
def page_head(label: str, h1: str, lede: str = "", extra: str = "") -> str:
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    return f"""<header class="page-head">
  <div class="wrap rv">
    <span class="label">{label}</span>
    <h1>{h1}</h1>
    {lede_html}
    {extra}
  </div>
</header>"""


def tags(items: list[str]) -> str:
    return '<div class="tags">' + "".join(f'<span class="tag">{esc(t)}</span>' for t in items) + "</div>"


def project_rows(site: Site, lang: str) -> str:
    c = site.content[lang]["work"]
    rows = []
    for n, key, k in (("01", "readmission", "readmission"), ("02", "edudata", "edudata"), ("03", "credit", "credit"),
                      ("04", "recommender", "recommender")):
        p = c[k]
        rows.append(f"""<a class="row rv" href="{site.url(lang, key)}">
  <span class="n">{n}</span>
  <span><h3>{esc(p['name'])}</h3><p class="desc">{esc(p['summary'])}</p>{tags(p['tags'])}</span>
  <span class="meta">{'<br>'.join(f'<b>{esc(m)}</b>' if i == 0 else esc(m) for i, m in enumerate(p['meta']))}<br>{esc(p['kicker'])}</span>
  <span class="arr" aria-hidden="true">↗</span>
</a>""")
    return '<div class="index">' + "".join(rows) + "</div>"


def stats(items: list[list[str]]) -> str:
    return '<div class="stats">' + "".join(
        f'<div class="stat"><div class="v">{esc(v)}</div><div class="k">{esc(k)}</div></div>' for v, k in items
    ) + "</div>"


def spec(items: list[list[str]], repo: str, ui: dict, demo: str | None = None) -> str:
    rows = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in items)
    if demo:
        rows += f'<div><dt>{esc(ui["demo"])}</dt><dd><a href="{demo}" rel="noopener">{esc(demo.replace("https://", ""))} ↗</a></dd></div>'
    short = repo.replace("https://", "")
    rows += f'<div><dt>{esc(ui["repo"])}</dt><dd><a href="{repo}" rel="noopener">{esc(short)} ↗</a></dd></div>'
    return f'<dl class="spec">{rows}</dl>'


def table(cols: list[str], rows: list[list[str]], hl: set[int] = frozenset(), cls: str = "") -> str:
    head = "".join(f"<th scope=col>{c}</th>" for c in cols)
    body = "".join(
        f'<tr{" class=hl" if i in hl else ""}>' + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for i, r in enumerate(rows)
    )
    return f'<div class="tbl-wrap"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def threshold_explorer(site: Site, lang: str) -> str:
    c = site.content[lang]["work"]["credit"]
    d = site.data["credit"]
    curve = d["threshold_curve"]
    start = next(i for i, r in enumerate(curve) if abs(r[0] - 0.5) < 1e-9)
    payload = json.dumps({"curve": curve, "lang": lang})
    keys = c["th_keys"]
    legend = (
        f'<div class="legend"><span><i style="background:var(--text-2)"></i>{keys[0]}</span>'
        f'<span><i style="background:var(--signal)"></i>{keys[1]}</span>'
        f'<span><i style="background:var(--accent)"></i>{keys[2]}</span></div>'
    )
    reads = "".join(
        f'<div><div class="v" data-out="{i}">—</div><div class="k">{k}</div></div>' for i, k in enumerate(keys)
    )
    return f"""<figure class="panel" data-th='{payload}'>
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(c['th_head'])}</span><span>n = {integer(d['split']['test'], lang)}</span></div>
  <div class="panel-b">
    <div class="th-ctrl">
      <label class="label" for="th-{lang}">{esc(c['th_label'])}</label>
      <input id="th-{lang}" type="range" min="0" max="{len(curve) - 1}" step="1" value="{start}">
      <output for="th-{lang}">{num(curve[start][0], lang, 2)}</output>
    </div>
    {legend}
    <div class="chart">{threshold_chart(curve, d['final']['threshold'], lang)}</div>
    <div class="th-read" style="grid-template-columns:repeat(4,minmax(0,1fr))">{reads}</div>
  </div>
  <figcaption style="padding:0 18px 16px">{esc(c['th_cap'])}</figcaption>
</figure>"""


def reliability_figure(site: Site, lang: str) -> str:
    d = site.data["calibration"]
    pt = lang == "pt"
    head = "modelo salvo · conjunto de teste · 10 bins" if pt else "saved model · test set · 10 bins"
    cap = ("Cada ponto é um bin de probabilidade prevista (área ∝ n); a faixa de baixo mostra quantos clientes caem em cada bin. "
           "O bin 0,9–1,0 (n = 2) não é plotado. Fonte: research/calibration/calibration.py." if pt else
           "Each point is a bin of predicted probability (area ∝ n); the strip below shows how many clients fall in each bin. "
           "The 0.9–1.0 bin (n = 2) is not plotted. Source: research/calibration/calibration.py.")
    xl = "probabilidade prevista média" if pt else "mean predicted probability"
    yl = "taxa de inadimplência observada" if pt else "observed default rate"
    return f"""<figure class="panel">
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(head)}</span><span>n = {integer(sum(q['n'] for q in d['saved']['reliability']), lang)}</span></div>
  <div class="panel-b chart"><span class="label" style="display:block;margin:0 0 8px">y: {esc(yl)} · x: {esc(xl)}</span>{reliability_svg(d['saved']['reliability'], lang)}</div>
  <figcaption style="padding:0 18px 16px">{esc(cap)}</figcaption>
</figure>"""


def calibration_table(site: Site, lang: str) -> str:
    d = site.data["calibration"]
    pt = lang == "pt"
    cols = (["modelo", "Brier", "log loss", "ECE", "ROC AUC", "p̂ médio", "g(0,24)", "c<sub>FN</sub>/c<sub>FP</sub>"] if pt else
            ["model", "Brier", "log loss", "ECE", "ROC AUC", "mean p̂", "g(0.24)", "c<sub>FN</sub>/c<sub>FP</sub>"])
    names = {"saved": "salvo (24k)" if pt else "saved (24k)", "raw": "refit, bruto" if pt else "refit, raw",
             "platt": "refit + Platt", "isotonic": "refit + isotônica" if pt else "refit + isotonic"}
    rows = []
    for k in ("saved", "raw", "platt", "isotonic"):
        r = d[k]
        g = r.get("g_of_024", 0.24)
        rows.append([names[k], num(r["brier"], lang, 4), num(r["logloss"], lang, 4), num(r["ece"], lang, 4),
                     num(r["auc"], lang, 4), num(r["mean_p"], lang, 4), num(g, lang, 3), num((1 - g) / g, lang, 2) + "×"])
    base = num(d["saved"]["base_rate"], lang, 4)
    cap = (f"Conjunto de teste (n = 6.000, taxa real de inadimplência = {base}). Calibradores ajustados na validação (n = 4.800). "
           "g(0,24) = probabilidade calibrada correspondente ao threshold bruto 0,24." if pt else
           f"Test set (n = 6,000, observed default rate = {base}). Calibrators fitted on validation (n = 4,800). "
           "g(0.24) = calibrated probability corresponding to the raw threshold 0.24.")
    return table(cols, rows, hl={0}, cls="l2") + f'<p class="cap">{esc(cap)}</p>'


def person_ld(site: Site, lang: str) -> dict:
    a = site.config["author"]
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": a["name"],
        "url": site.abs_url(lang, "home"),
        "email": f"mailto:{a['email']}",
        "image": site.config["site"]["base_url"] + site.asset("img/igor-millis.webp"),
        "sameAs": [a["github"], a["linkedin"]],
        "affiliation": {"@type": "CollegeOrUniversity", "name": "Universidade Federal do Espírito Santo (UFES)"},
        "knowsAbout": ["Statistics", "Machine Learning", "Data Engineering", "Data Science", "Large Language Models"],
    }


# ---------------------------------------------------------------- pages
def home(site: Site, lang: str) -> str:
    c = site.content[lang]
    h = c["home"]
    ui = c["ui"]
    sub = "".join(f"<span>{esc(s)}</span>" for s in h["sub"])
    doors = "".join(
        f"""<a class="door rv" href="{site.url(lang, key)}">
  <span class="label"><b>{n}</b> / {esc(ui['nav_' + key])}</span>
  <h2>{esc(h[f'door_{key}_title'])}</h2>
  <p>{esc(h[f'door_{key}_text'])}</p>
  <span class="go">cd ~/{key} →</span>
</a>"""
        for n, key in (("01", "about"), ("02", "work"), ("03", "research"))
    )
    body = f"""<section class="hero" aria-label="intro">
  <canvas id="field" aria-hidden="true"></canvas>
  <div class="wrap">
    <div class="prompt">$ <span class="cmd">whoami</span> <span class="flag">{esc(h['prompt_flag'])}</span><span class="caret" aria-hidden="true"></span></div>
    <h1>{h['h1']}</h1>
    <div class="sub">{sub}</div>
  </div>
  <div class="readout" aria-hidden="true">{esc(h['readout'])}<br>step <span id="step">0</span> · mean L = <span id="loss">—</span></div>
</section>
<div class="wrap"><nav class="doors" aria-label="{esc(h['doors_label'])}">{doors}</nav></div>
<section class="sec">
  <div class="wrap">
    <p class="label" style="margin-bottom:18px"><b>02</b> / {esc(h['selected_label'])}</p>
    {project_rows(site, lang)}
  </div>
</section>"""
    return page(site, lang, "home", title=h["title"], description=h["description"], body=body,
                jsonld=person_ld(site, lang))


def about(site: Site, lang: str) -> str:
    c = site.content[lang]
    ab = c["about"]
    a = site.config["author"]
    ui = c["ui"]
    paras = "".join(f"<p>{p}</p>" for p in ab["paragraphs"])
    intro = f"""<section class="sec">
  <div class="wrap about-grid">
    <div class="rv">
      <div class="portrait"><img src="{site.asset('img/igor-millis.webp')}" width="400" height="400" alt="{attr(ab['portrait_alt'])}"><span class="cross" aria-hidden="true"></span></div>
      <div class="portrait-cap"><span>{esc(ab['portrait_cap'][0])}</span><span>{esc(ab['portrait_cap'][1])}</span></div>
    </div>
    <div class="about-text rv">{paras}</div>
  </div>
</section>"""
    def tl(e: dict) -> str:
        title = esc(e["title"])
        if e.get("href"):
            title = f'<a href="{site.url(lang, e["href"])}">{title} <span class="arr" aria-hidden="true">↗</span></a>'
        return (f'<div class="tl{" now" if e.get("now") else ""}"><span class="when">{esc(e["when"])}</span>'
                f'<h3>{title}</h3><p class="place">{esc(e["place"])}</p>'
                + (f'<p>{esc(e["text"])}</p>' if e.get("text") else "") + "</div>")
    edu = f'<p class="prose" style="margin-bottom:28px">{esc(ab["edu_intro"])}</p><div class="timeline">' + "".join(tl(e) for e in ab["edu"]) + "</div>"
    exp = '<div class="exp">' + "".join(
        f'<article class="job{" now" if x.get("now") else ""}"><div class="job-h"><span class="when">{esc(x["when"])}</span>'
        f'<h3>{esc(x["org"])}</h3><p class="roles">{" · ".join(esc(r) for r in x["roles"])}</p></div>'
        f'<ul>{"".join(f"<li>{i}</li>" for i in x["items"])}</ul></article>'
        for x in ab["exp"]) + "</div>"
    focus = '<div class="focus-grid">' + "".join(
        f'<a class="focus" href="{site.url(lang, f["href"])}"><span class="fn">{i + 1:02d}</span>'
        f'<h3>{esc(f["title"])}</h3><p>{esc(f["text"])}</p><span class="proof">→ {esc(f["proof"])}</span></a>'
        for i, f in enumerate(ab["focus"])) + "</div>"
    stack = '<dl class="stack">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in ab["stack"]) + "</dl>"
    stack += f'<p class="cap">{esc(ab["stack_note"])}</p>'
    links = f"""<p class="muted" style="max-width:52ch">{esc(ab['contact_text'])}</p>
<ul class="links-big">
  <li><a href="mailto:{a['email']}" data-copy="{a['email']}"><span class="k">email</span><span class="v">{esc(a['email'])}</span><span class="arr">↗</span></a></li>
  <li><a href="{a['github']}" rel="me noopener"><span class="k">github</span><span class="v">github.com/{esc(a['github_handle'])}</span><span class="arr">↗</span></a></li>
  <li><a href="{a['linkedin']}" rel="me noopener"><span class="k">linkedin</span><span class="v">{esc(a['linkedin_handle'])}</span><span class="arr">↗</span></a></li>
</ul>"""
    body = (
        page_head(ab["label"], ab["h1"])
        + intro
        + section(f"<b>01.1</b> / {esc(ab['edu_label'])}", esc(ab["edu_title"]), edu)
        + section(f"<b>01.2</b> / {esc(ab['exp_label'])}", esc(ab["exp_title"]), exp, id="experience")
        + section(f"<b>01.3</b> / {esc(ab['focus_label'])}", esc(ab["focus_title"]), focus)
        + section(f"<b>01.4</b> / {esc(ab['stack_label'])}", esc(ab["stack_title"]), stack)
        + section(f"<b>01.5</b> / {esc(ab['contact_label'])}", esc(ab["contact_title"]), links, id="contact")
    )
    return page(site, lang, "about", title=ab["title"], description=ab["description"], body=body,
                jsonld=person_ld(site, lang), og_type="profile")


def work(site: Site, lang: str) -> str:
    w = site.content[lang]["work"]
    body = page_head(w["label"], w["h1"], w["lede"]) + f'<section class="sec"><div class="wrap">{project_rows(site, lang)}</div></section>'
    return page(site, lang, "work", title=w["title"], description=w["description"], body=body)


def _project_head(site: Site, lang: str, p: dict, repo: str, demo: str | None = None) -> str:
    ui = site.content[lang]["ui"]
    cta = (f'<p style="margin-top:20px"><a class="btn-ghost" href="{demo}" rel="noopener">{esc(ui["demo_cta"])} ↗</a>'
           f' <span class="cap" style="margin-left:8px">{esc(ui["demo_note"])}</span></p>') if demo else ""
    head = page_head(f'<a href="{site.url(lang, "work")}" style="text-decoration:none">{esc(ui["back_work"])}</a> · {esc(p["kicker"])}',
                     esc(p["name"]), esc(p["summary"]), tags(p["tags"]) + cta)
    overview = f"""<section class="sec overview" style="padding-top:48px">
  <div class="wrap">
    <div class="rv">{stats(p['stats'])}</div>
    <div class="rv" style="margin-top:32px">{spec(p['spec'], repo, ui, demo)}</div>
  </div>
</section>"""
    return head + overview


def _software_ld(site: Site, lang: str, key: str, p: dict, repo: str, langs: list[str]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": p["name"],
        "description": attr(p["description"]),
        "codeRepository": repo,
        "programmingLanguage": langs,
        "url": site.abs_url(lang, key),
        "author": {"@type": "Person", "name": site.config["author"]["name"]},
    }


def edudata(site: Site, lang: str) -> str:
    p = site.content[lang]["work"]["edudata"]
    d = site.data["edudata"]
    repo = d["repo"]

    tabs = "".join(
        f'<button role="tab" id="st-{i}" aria-controls="sp-{i}" aria-selected="{"true" if i == 0 else "false"}"><b>{esc(code)}</b>{esc(name)}</button>'
        for i, (code, name, _) in enumerate(p["stages"])
    )
    panels = "".join(
        f'<div class="pipe-detail" role="tabpanel" id="sp-{i}" aria-labelledby="st-{i}">{text}</div>'
        for i, (_, _, text) in enumerate(p["stages"])
    )
    pipeline = f'<p class="prose">{esc(p["s2_body"])}</p><div class="pipe" role="tablist" data-pipe>{tabs}</div><div data-pipe-panels>{panels}</div>'

    replay_data = {
        "items": d["replay"],
        "ok": p["replay_ok"], "rank": p["replay_rank"],
        "why": {"out_of_range": p["replay_why_out_of_range"], "not_published": p["replay_why_not_published"]},
    }
    qbtns = "".join(
        f'<button type="button" aria-pressed="{"true" if i == 0 else "false"}" data-i="{i}">{esc(r["q"])}</button>'
        for i, r in enumerate(d["replay"])
    )
    cols = p["replay_cols"]
    replay = f"""{p['s3_body']}
<div class="panel" data-replay>
  <div class="panel-h"><span><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{esc(p['replay_head'])}</span><span>motor/consultas.py · motor/seguranca.py</span></div>
  <div class="replay-q" role="group">{qbtns}</div>
  <div class="replay-steps" aria-live="polite">
    <div><span class="label">{esc(cols[0])}</span><pre class="step" data-s="0"></pre></div>
    <div><span class="label">{esc(cols[1])}</span><pre class="step" data-s="1"></pre></div>
    <div><span class="label">{esc(cols[2])}</span><pre class="step" data-s="2"></pre></div>
  </div>
  <div class="verdict" data-verdict></div>
  <script type="application/json">{json.dumps(replay_data, ensure_ascii=False).replace("</", "<\\/")}</script>
</div>
<p class="cap">{esc(p['replay_note'])}</p>"""

    names_pt = {"Rules": "Regras", "LLM 3B alone": "LLM 3B sozinho", "LLM 7B alone": "LLM 7B sozinho",
                "Hybrid (rules + 7B)": "Híbrido (regras + 7B)"}
    rows = []
    for r in d["llm_eval"]:
        name = names_pt.get(r["name"], r["name"]) if lang == "pt" else r["name"]
        pct = r["total"] / 40 * 100
        bar = f'<span style="display:inline-block;width:56px;height:6px;background:var(--line);vertical-align:1px;margin-right:8px"><span style="display:block;height:100%;width:{pct:.0f}%;background:var(--accent)"></span></span>'
        t = r["time"].replace(".", ",") if lang == "pt" else r["time"]
        star = r.get("note", "")
        rows.append([name, f"{r['para']}{star}", str(r["ctrl"]), f"{bar}{r['total']}{star}", t])
    llm = p["s4_body"] + table(p["s4_cols"], rows, hl={2}) + f'<p class="cap">{esc(p["s4_cap"])}</p>' + p["s4_after"]

    figs = '<div class="fig-grid">' + "".join(
        f'<figure><img src="{site.asset("img/" + src)}" width="{w}" height="{h}" loading="lazy" decoding="async" '
        f'alt="{attr(cap)}"><figcaption>fig. {i + 1} — {esc(cap)}</figcaption></figure>'
        for i, (src, cap, w, h) in enumerate(p["figs"])
    ) + "</div>"

    body = (
        _project_head(site, lang, p, repo, d.get("demo"))
        + section(esc(p["s1_label"]), esc(p["s1_title"]), f'<div class="prose">{p["s1_body"]}</div>')
        + section(esc(p["s2_label"]), esc(p["s2_title"]), pipeline)
        + section(esc(p["s3_label"]), esc(p["s3_title"]), replay)
        + section(esc(p["s4_label"]), esc(p["s4_title"]), f'<div class="prose" style="max-width:none">{llm}</div>')
        + section(esc(p["s5_label"]), esc(p["s5_title"]), f'<div class="prose">{p["s5_body"]}</div>')
        + section(esc(p["s6_label"]), esc(p["s6_title"]), f'<p class="prose">{esc(p["s6_body"])}</p>{figs}')
        + section(esc(p["s7_label"]), esc(p["s7_title"]), f'<div class="prose">{p["s7_body"]}</div>')
    )
    return page(site, lang, "edudata", title=p["title"], description=p["description"], body=body,
                scripts=("js/edudata.js",), jsonld=_software_ld(site, lang, "edudata", p, repo, ["Python", "SQL"]))


def credit(site: Site, lang: str) -> str:
    p = site.content[lang]["work"]["credit"]
    d = site.data["credit"]
    repo = d["repo"]
    f = lambda v: num(v, lang, 4) if v is not None else "—"  # noqa: E731

    rows = [[esc(m["name"]), esc(m["variant"]), f(m.get("acc")), f(m.get("prec")), f(m.get("rec")), f(m.get("f1")), f(m.get("auc"))]
            for m in d["models"]]
    hp = "\n".join(f"{k:<18}= {v}" for k, v in d["hyperparams"].items())
    method = (f'<div class="prose">{p["s2_body"]}</div>' + table(p["s2_cols"], rows, hl={6}, cls="l2")
              + f'<p class="cap">{esc(p["s2_cap"])}</p>'
              + f'<p class="label" style="margin-top:28px">{esc(p["best_params"])}</p><pre class="code">{esc(hp)}</pre>')

    fin = d["final"]
    cm = fin["cm"]
    names = p["cm_names"]
    n = lambda x: integer(x, lang)  # noqa: E731
    cm_html = f"""<div class="cm" role="table" aria-label="{attr(p['cm_title'])}">
  <div class="h"></div><div class="h">{esc(p['cm_cols'][0])}</div><div class="h">{esc(p['cm_cols'][1])}</div>
  <div class="h">{esc(p['cm_rows'][0])}</div><div class="c">{n(cm['tn'])}<small>{esc(names[0])}</small></div><div class="c">{n(cm['fp'])}<small>{esc(names[1])}</small></div>
  <div class="h">{esc(p['cm_rows'][1])}</div><div class="c">{n(cm['fn'])}<small>{esc(names[2])}</small></div><div class="c tp">{n(cm['tp'])}<small>{esc(names[3])}</small></div>
</div>"""
    final_tbl = table(p["final_cols"], [[k, f(fin[m])] for k, m in zip(p["final_rows"], ("acc", "prec", "rec", "f1", "auc"))], hl={2})
    thr = (f'<div class="prose">{p["s3_body"]}</div>' + threshold_explorer(site, lang)
           + f'<div class="prose">{p["s3_after"].format(note=site.url(lang, "note:threshold-is-a-decision"))}</div>'
           + f'<h3>{esc(p["cm_title"])}</h3><div class="fig-grid" style="align-items:start">{cm_html}{final_tbl}</div>')

    imp = (f'<p class="prose">{esc(p["s4_body"])}</p><figure class="chart">{hbars(d["importance"], lang, digits=3)}'
           f'<figcaption>{esc(p["s4_cap"])}</figcaption></figure>')

    req = ('POST /predict\n{\n  "LIMIT_BAL": 20000, "SEX": 1, "EDUCATION": 2, "MARRIAGE": 1, "AGE": 24,\n'
           '  "PAY_0": 2, "PAY_2": 2, "PAY_3": 0, "PAY_4": 0, "PAY_5": 0, "PAY_6": 0,\n'
           '  "BILL_AMT1": 3913, ... "PAY_AMT6": 0\n}\n\n→ 200 OK\n{\n  "probability": 0.3297,\n  "threshold": 0.24,\n'
           '  "prediction": 1,\n  "classification": "inadimplente"\n}')
    serving = f'<div class="prose">{p["s5_body"]}</div><pre class="code">{esc(req)}</pre><div class="prose">{p["s5_after"]}</div>'

    body = (
        _project_head(site, lang, p, repo)
        + section(esc(p["s1_label"]), esc(p["s1_title"]), f'<div class="prose">{p["s1_body"]}</div>')
        + section(esc(p["s2_label"]), esc(p["s2_title"]), method)
        + section(esc(p["s3_label"]), esc(p["s3_title"]), thr)
        + section(esc(p["s4_label"]), esc(p["s4_title"]), imp)
        + section(esc(p["s5_label"]), esc(p["s5_title"]), serving)
        + section(esc(p["s6_label"]), esc(p["s6_title"]), f'<div class="prose">{p["s6_body"]}</div>')
    )
    return page(site, lang, "credit", title=p["title"], description=p["description"], body=body,
                scripts=("js/threshold.js",), jsonld=_software_ld(site, lang, "credit", p, repo, ["Python"]))


def _katex(selector: str = "main") -> str:
    return (
        f'<link rel="stylesheet" href="{KATEX}/katex.min.css">'
        f'<script defer src="{KATEX}/katex.min.js"></script>'
        f'<script defer src="{KATEX}/contrib/auto-render.min.js"></script>'
        "<script>document.addEventListener('DOMContentLoaded',function(){if(window.renderMathInElement)"
        f"renderMathInElement(document.querySelector('{selector}')||document.body,{{delimiters:[{{left:'\\\\[',right:'\\\\]',display:true}},"
        "{left:'\\\\(',right:'\\\\)',display:false}],throwOnError:false})})</script>"
    )


def _tab_group(gid: str, items: list[list[str]]) -> str:
    """Accessible tab group reusing the .pipe styles; panels stay visible without JS."""
    tabs = "".join(
        f'<button role="tab" id="{gid}-t{i}" aria-controls="{gid}-p{i}" aria-selected="{"true" if i == 0 else "false"}">'
        f'<b>{esc(code)}</b>{esc(name)}</button>'
        for i, (code, name, _) in enumerate(items)
    )
    panels = "".join(
        f'<div class="pipe-detail" role="tabpanel" id="{gid}-p{i}" aria-labelledby="{gid}-t{i}">{body}</div>'
        for i, (_, _, body) in enumerate(items)
    )
    return (f'<div class="pipe pipe-{len(items)}" role="tablist" data-pipe="{gid}">{tabs}</div>'
            f'<div data-pipe-panels="{gid}">{panels}</div>')


def recommender(site: Site, lang: str) -> str:
    p = site.content[lang]["work"]["recommender"]
    d = site.data["recommender"]
    repo = d["repo"]
    names = p["model_names"]
    f3 = lambda v: num(v, lang, 3)  # noqa: E731
    ci = lambda lo, hi: f"[{num(lo, lang, 3)}; {num(hi, lang, 3)}]" if lang == "pt" else f"[{num(lo, lang, 3)}, {num(hi, lang, 3)}]"  # noqa: E731

    def results_block(key: str, cap: str) -> str:
        res = d[key]["results"]
        chart = ci_bars([[names[r["model"]], r["ndcg"], r["lo"], r["hi"]] for r in res], lang, highlight=2)
        hl = {i for i, r in enumerate(res) if r["model"] in ("hybrid_learned", "hybrid_fixed")}
        rows = [[esc(names[r["model"]]), f3(r["ndcg"]), ci(r["lo"], r["hi"]), f3(r["recall"]), f3(r["precision"]),
                 num(r["coverage"], lang, 2)] for r in res]
        return (f'<figure class="chart" style="margin:8px 0 20px">{chart}<figcaption>{esc(cap)}</figcaption></figure>'
                + table(p["results_cols"], rows, hl=hl, cls="l2"))

    def paired_block(key: str) -> str:
        rows = []
        for q in d[key]["paired"]:
            if q["ci_low"] > 0:
                verdict = p["verdict_better"]
            elif q["ci_high"] < 0:
                verdict = p["verdict_worse"]
            else:
                verdict = p["verdict_tie"]
            sign = lambda v: ("+" if v >= 0 else "−") + num(abs(v), lang, 3)  # noqa: E731
            rows.append([f"{esc(names[q['a']])} − {esc(names[q['b']])}", sign(q["diff"]),
                         f"[{sign(q['ci_low'])}; {sign(q['ci_high'])}]" if lang == "pt" else f"[{sign(q['ci_low'])}, {sign(q['ci_high'])}]",
                         esc(verdict)])
        return table(p["paired_cols"], rows, cls="l2")

    hist = d["synthetic"]["by_history"]
    order = [("histórico extenso", 0), ("histórico moderado", 1), ("pouco histórico", 2), ("sem histórico", 3)]
    hist_rows = [[esc(p["history_names"][i]), str(hist[k]["n"]), f3(hist[k]["popularity"]), f3(hist[k]["supervised"]),
                  f3(hist[k]["hybrid_fixed"]), f3(hist[k]["hybrid_learned"])] for k, i in order]
    hist_tbl = table(p["history_cols"], hist_rows, cls="l2") + f'<p class="cap">{esc(p["history_cap"])}</p>'

    figs = '<div class="fig-grid">' + "".join(
        f'<figure><img src="{site.asset("img/" + src)}" width="1440" height="1000" loading="lazy" decoding="async" '
        f'alt="{attr(cap)}"><figcaption>fig. {i + 1} — {esc(cap)}</figcaption></figure>'
        for i, (src, cap) in enumerate(p["figs"])
    ) + "</div>"

    head = _project_head(site, lang, p, repo)
    weekend = f'<section class="sec" style="padding-top:0"><div class="wrap"><div class="weekend rv">{p["weekend"]}</div></div></section>'
    body = (
        head + weekend
        + section(esc(p["s1_label"]), esc(p["s1_title"]), f'<div class="prose">{p["s1_body"]}</div>')
        + section(esc(p["s2_label"]), esc(p["s2_title"]), f'<div class="prose">{p["s2_intro"]}</div>' + _tab_group("steps", p["steps"]))
        + section(esc(p["s3_label"]), esc(p["s3_title"]), f'<div class="prose">{p["s3_body"]}</div>')
        + section(esc(p["s4_label"]), esc(p["s4_title"]), f'<div class="prose">{p["s4_intro"]}</div>' + _tab_group("methods", p["methods"]))
        + section(esc(p["s5_label"]), esc(p["s5_title"]), f'<div class="prose">{p["s5_body"]}</div>')
        + section(esc(p["s6_label"]), esc(p["s6_title"]), f'<div class="prose">{p["s6_body"]}</div>')
        + section(esc(p["s7_label"]), esc(p["s7_title"]),
                  f'<div class="prose">{p["s7_body"]}</div>' + results_block("synthetic", p["synthetic_cap"])
                  + f'<div class="prose" style="margin-top:28px">{p["s7_paired"]}</div>' + paired_block("synthetic")
                  + f'<div class="prose" style="margin-top:28px">{p["s7_history"]}</div>' + hist_tbl
                  + f'<div class="prose" style="margin-top:20px">{p["s7_after"]}</div>')
        + section(esc(p["s8_label"]), esc(p["s8_title"]),
                  f'<div class="prose">{p["s8_body"]}</div>' + results_block("real", p["real_cap"])
                  + f'<div class="prose" style="margin-top:20px">{p["s8_after"]}</div>')
        + section(esc(p["s9_label"]), esc(p["s9_title"]), f'<p class="prose">{esc(p["s9_intro"])}</p>{figs}')
        + section(esc(p["s10_label"]), esc(p["s10_title"]), f'<div class="prose">{p["s10_body"]}</div>')
    )
    return page(site, lang, "recommender", title=p["title"], description=p["description"], body=body,
                scripts=("js/recommender.js",), head_extra=_katex("main"),
                jsonld=_software_ld(site, lang, "recommender", p, repo, ["Python", "SQL"]))


def research(site: Site, lang: str) -> str:
    c = site.content[lang]
    r = c["research"]
    ui = c["ui"]
    rows = ""
    for slug in NOTES:
        n = r["notes"][slug]
        rows += f"""<a class="note-row rv" href="{site.url(lang, f'note:{slug}')}">
  <time datetime="{n['date']}">{n['date']}</time>
  <span><h3>{esc(n['title'])}</h3><p>{esc(n['abstract'])}</p></span>
  <span class="kind">{esc(n['kind'])}<br><span class="muted">{n['minutes']} {esc(ui['min_read'])}</span></span>
</a>"""
    body = (page_head(r["label"], r["h1"], r["lede"])
            + f"""<section class="sec"><div class="wrap">
  <p class="label" style="margin-bottom:18px"><b>03</b> / {esc(r['list_label'])}</p>
  <div class="notes">{rows}</div>
  <p class="label" style="margin-top:40px"><b>fmt</b> / {esc(r['format_label'])} — {esc(r['format'])}</p>
</div></section>""")
    return page(site, lang, "research", title=r["title"], description=r["description"], body=body)


def note(site: Site, lang: str, slug: str) -> str:
    c = site.content[lang]
    ui = c["ui"]
    n = c["research"]["notes"][slug]
    key = f"note:{slug}"
    html_body = (ROOT / "content" / "notes" / f"{slug}.{lang}.html").read_text(encoding="utf-8")
    # Link placeholders: {credit}, {edudata}, {note:<slug>}
    html_body = html_body.replace("{credit}", site.url(lang, "credit")).replace("{edudata}", site.url(lang, "edudata"))
    for other in NOTES:
        html_body = html_body.replace("{note:%s}" % other, site.url(lang, f"note:{other}"))
    # Component placeholders: <!--name--> in the note body -> rendered component
    components = {"explorer": threshold_explorer, "reliability": reliability_figure,
                  "calibration-table": calibration_table, **BETS_COMPONENTS, **BOOT_COMPONENTS, **NB_COMPONENTS, **QL_COMPONENTS}
    for name, render in components.items():
        if f"<!--{name}-->" in html_body:
            html_body = html_body.replace(f"<!--{name}-->", render(site, lang))
    by = (f'<div class="byline"><span>{esc(site.config["author"]["name"])}</span><time datetime="{n["date"]}">{n["date"]}</time>'
          f'<span>{n["minutes"]} {esc(ui["min_read"])}</span><span class="accent">{esc(n["kind"])}</span></div>')
    if n.get("tags"):
        by += tags(n["tags"])
    head = page_head(f'<a href="{site.url(lang, "research")}" style="text-decoration:none">{esc(ui["back_research"])}</a>',
                     esc(n["title"]), esc(n["abstract"]), by)
    body = head + f'<section class="sec"><div class="wrap"><article class="article rv">{html_body}</article></div></section>'
    katex = (
        f'<link rel="stylesheet" href="{KATEX}/katex.min.css">'
        f'<script defer src="{KATEX}/katex.min.js"></script>'
        f'<script defer src="{KATEX}/contrib/auto-render.min.js"></script>'
        "<script>document.addEventListener('DOMContentLoaded',function(){if(window.renderMathInElement)"
        "renderMathInElement(document.querySelector('.article'),{delimiters:[{left:'\\\\[',right:'\\\\]',display:true},"
        "{left:'\\\\(',right:'\\\\)',display:false}],throwOnError:false})})</script>"
    )
    ld = {
        "@context": "https://schema.org", "@type": "TechArticle", "headline": n["title"],
        "description": n["description"], "datePublished": n["date"], "inLanguage": site.lang(lang)["html"],
        "author": {"@type": "Person", "name": site.config["author"]["name"], "url": site.abs_url(lang, "about")},
        "url": site.abs_url(lang, key),
    }
    if n.get("tags"):
        ld["keywords"] = ", ".join(n["tags"])
    return page(site, lang, key, title=n["seo_title"], description=n["description"], body=body,
                scripts=tuple(n.get("scripts", ())), head_extra=katex, jsonld=ld, og_type="article")


def readmission(site: Site, lang: str) -> str:
    return _readmission(site, lang)


def not_found(site: Site) -> str:
    body = f"""<section class="nf"><div class="wrap">
  <p class="label">error / route not found</p>
  <h1>404</h1>
  <p class="prompt" style="margin-top:28px">$ <span class="cmd">cd</span> <span class="flag">~/this-page</span><br>bash: cd: no such file or directory</p>
  <p style="margin-top:28px"><a href="{site.url('en', 'home')}">← home (EN)</a> &nbsp; <a href="{site.url('pt', 'home')}">← início (PT)</a></p>
</div></section>"""
    return page(site, "en", "home", title="404 — Igor Millis", description="Page not found.", body=body,
                head_extra='<meta name="robots" content="noindex">')
