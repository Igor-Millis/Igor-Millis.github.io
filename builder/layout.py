"""HTML shell: <head> with SEO, header, footer/status bar and command palette."""
from __future__ import annotations

import json

from .core import NOTES, ROUTES, Site, attr, esc

FONTS = (
    "https://fonts.googleapis.com/css2?family=Geist:wght@400;500&family=Geist+Mono:wght@400;500"
    "&family=Newsreader:ital,opsz,wght@1,6..72,400&display=swap"
)

THEME_ICON = (
    '<svg class="theme-ico" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="none" '
    'stroke="currentColor"/><path d="M8 1.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg>'
)


def _section_of(key: str) -> str:
    if key in ("work", "edudata", "credit", "recommender", "readmission"):
        return "work"
    if key == "research" or key.startswith("note:"):
        return "research"
    return key


def _nav(site: Site, lang: str, key: str, cls: str = "nav") -> str:
    ui = site.content[lang]["ui"]
    cur = _section_of(key)
    items = [("work", ui["nav_work"]), ("research", ui["nav_research"]), ("about", ui["nav_about"])]
    links = "".join(
        f'<a href="{site.url(lang, k)}"{" aria-current=\"page\"" if cur == k else ""}>{esc(label)}</a>'
        for k, label in items
    )
    return f'<nav class="{cls}" aria-label="primary">{links}</nav>'


def _lang_switch(site: Site, lang: str, key: str) -> str:
    ui = site.content[lang]["ui"]
    parts = []
    for code in site.langs:
        cur = ' aria-current="true"' if code == lang else ""
        hl = site.lang(code)["html"]
        parts.append(f'<a href="{site.url(code, key)}" hreflang="{hl}" lang="{hl}"{cur} data-lang="{code}">{code.upper()}</a>')
    return f'<span class="btn-ghost lang" role="group" aria-label="{esc(ui["lang_label"])}">{"<span class=sep>/</span>".join(parts)}</span>'


def _cmdk_data(site: Site, lang: str, key: str) -> str:
    ui = site.content[lang]["ui"]
    c = site.content[lang]
    a = site.config["author"]
    items = [
        {"label": ui["nav_home"], "hint": "/", "href": site.url(lang, "home")},
        {"label": ui["nav_work"], "hint": "02", "href": site.url(lang, "work")},
        {"label": c["work"]["readmission"]["name"], "hint": ui["nav_work"], "href": site.url(lang, "readmission")},
        {"label": "EduData", "hint": ui["nav_work"], "href": site.url(lang, "edudata")},
        {"label": "Credit Default API", "hint": ui["nav_work"], "href": site.url(lang, "credit")},
        {"label": "Adaptive Recommender", "hint": ui["nav_work"], "href": site.url(lang, "recommender")},
        {"label": ui["nav_research"], "hint": "03", "href": site.url(lang, "research")},
        *({"label": c["research"]["notes"][s]["title"], "hint": ui["nav_research"],
           "href": site.url(lang, f"note:{s}")} for s in NOTES),
        {"label": ui["nav_about"], "hint": "01", "href": site.url(lang, "about")},
        {"label": ui["copy_email"], "hint": a["email"], "action": "copy", "value": a["email"]},
        {"label": "GitHub", "hint": a["github_handle"], "href": a["github"], "ext": True},
        {"label": "LinkedIn", "hint": a["linkedin_handle"], "href": a["linkedin"], "ext": True},
        {"label": ui["theme"], "hint": "t", "action": "theme"},
        {"label": f'{ui["lang_label"]}: {site.other(lang).upper()}', "hint": "l",
         "href": site.url(site.other(lang), key)},
    ]
    return json.dumps({"items": items, "copied": ui["copied"]}, ensure_ascii=False).replace("</", "<\\/")


def _jsonld(obj: dict | list | None) -> str:
    if not obj:
        return ""
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def page(
    site: Site,
    lang: str,
    key: str,
    *,
    title: str,
    description: str,
    body: str,
    scripts: tuple[str, ...] = (),
    head_extra: str = "",
    jsonld: dict | list | None = None,
    og_type: str = "website",
) -> str:
    L = site.lang(lang)
    ui = site.content[lang]["ui"]
    a = site.config["author"]
    canonical = site.abs_url(lang, key)
    alternates = "".join(
        f'<link rel="alternate" hreflang="{site.lang(code)["hreflang"]}" href="{site.abs_url(code, key)}">'
        for code in site.langs
    )
    alternates += f'<link rel="alternate" hreflang="x-default" href="{site.abs_url(site.config["site"]["default_lang"], key)}">'
    og_img = site.config["site"]["base_url"] + site.asset("og.png")
    scripts_html = "".join(f'<script src="{site.asset_v(s)}" defer></script>' for s in ("js/main.js", *scripts))
    t, d = attr(title), attr(description)

    return f"""<!doctype html>
<html lang="{L['html']}" data-palette="chroma">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="author" content="{esc(a['name'])}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:locale" content="{L['locale']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b0e11">
<link rel="icon" href="{site.asset_v('favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{site.asset_v('css/main.css')}">
<script>(function(d){{try{{var t=localStorage.getItem('theme');if(t)d.dataset.theme=t;localStorage.removeItem('palette')}}catch(e){{}}d.classList.add('js')}})(document.documentElement)</script>
{head_extra}
{_jsonld(jsonld)}
{scripts_html}
</head>
<body>
<a class="skip" href="#main">{esc(ui['skip'])}</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="{site.url(lang, 'home')}"><svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="6"/><path d="M10 7.5h12M10 24.5h12M16 7.5v17"/></svg>igor-millis<span class="path">{esc(ROUTES[key].rstrip('/') and '~' + ROUTES[key].rstrip('/') or '~/')}</span></a>
    {_nav(site, lang, key)}
    <div class="tools">
      <button class="btn-ghost" type="button" data-cmdk aria-label="{esc(ui['cmdk_open'])}"><kbd>⌘K</kbd></button>
      <button class="btn-ghost" type="button" data-theme-toggle aria-label="{esc(ui['theme'])}" title="{esc(ui['theme'])}">{THEME_ICON}</button>
      {_lang_switch(site, lang, key)}
    </div>
  </div>
  {_nav(site, lang, key, "wrap mob-nav")}
</header>
<main id="main">
{body}
</main>
{footer(site, lang, key)}
<div class="cmdk" role="dialog" aria-modal="true" aria-label="{esc(ui['cmdk_hint'])}" hidden>
  <div class="cmdk-box">
    <input type="text" placeholder="{esc(ui['cmdk_hint'])}" aria-label="{esc(ui['cmdk_hint'])}" autocomplete="off" spellcheck="false">
    <ul role="listbox"></ul>
    <div class="cmdk-foot"><span><kbd>↑</kbd> <kbd>↓</kbd> {esc(ui['cmdk_nav'])}</span><span><kbd>↵</kbd> {esc(ui['cmdk_go'])}</span><span><kbd>esc</kbd> {esc(ui['cmdk_close'])}</span></div>
  </div>
</div>
<div class="toast" role="status" aria-live="polite"></div>
<script type="application/json" id="cmdk-data">{_cmdk_data(site, lang, key)}</script>
</body>
</html>
"""


def footer(site: Site, lang: str, key: str) -> str:
    ui = site.content[lang]["ui"]
    a = site.config["author"]
    s = site.config["site"]
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-main">
      <h2>{ui['footer_title']}</h2>
      <div>
        <p class="label">{esc(ui['footer_elsewhere'])}</p>
        <ul>
          <li><a href="mailto:{a['email']}">{esc(a['email'])}</a></li>
          <li><a href="{a['github']}" rel="me noopener">github ↗</a></li>
          <li><a href="{a['linkedin']}" rel="me noopener">linkedin ↗</a></li>
        </ul>
      </div>
      <div>
        <p class="label">{esc(ui['footer_site'])}</p>
        <ul>
          <li><a href="{site.url(lang, 'work')}">{esc(ui['nav_work'])}</a></li>
          <li><a href="{site.url(lang, 'research')}">{esc(ui['nav_research'])}</a></li>
          <li><a href="{site.url(lang, 'about')}">{esc(ui['nav_about'])}</a></li>
        </ul>
      </div>
    </div>
    <div class="status">
      <span><span class="accent">●</span> {esc(a['name'].lower())} · {esc(a['coords'])} · {esc(a['university'])}</span>
      <span>{esc(ui['status_stack'])}</span>
      <span>{esc(ui['status_built'])} {esc(s['updated'])} · © {s['updated'][:4]}</span>
    </div>
  </div>
</footer>"""


def section(label: str, title: str, inner: str, *, id: str | None = None) -> str:
    """Two-column editorial section: sticky mono label on the left, content on the right."""
    sid = f' id="{id}"' if id else ""
    head = f"<h2>{title}</h2>" if title else ""
    return f"""<section class="sec"{sid}>
  <div class="wrap sec-grid">
    <div class="side"><span class="label">{label}</span></div>
    <div class="rv">{head}{inner}</div>
  </div>
</section>"""
