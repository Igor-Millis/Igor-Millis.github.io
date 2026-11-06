"""Build the static site into dist/.

    python build.py            # build
    python build.py --serve    # build and serve on http://127.0.0.1:8000

Only the Python standard library is required (3.11+).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import sys

from builder import pages
from builder.core import DIST, NOTES, ROOT, ROUTES, Site


def write(path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sitemap(site: Site) -> str:
    updated = site.config["site"]["updated"]
    urls = []
    for key in ROUTES:
        for lang in site.langs:
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{site.lang(c)["hreflang"]}" href="{site.abs_url(c, key)}"/>'
                for c in site.langs
            )
            urls.append(f"<url><loc>{site.abs_url(lang, key)}</loc><lastmod>{updated}</lastmod>{alts}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")


def build() -> int:
    site = Site()
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST)

    count = 0
    for lang in site.langs:
        rendered = {
            "home": pages.home(site, lang),
            "about": pages.about(site, lang),
            "work": pages.work(site, lang),
            "edudata": pages.edudata(site, lang),
            "credit": pages.credit(site, lang),
            "research": pages.research(site, lang),
        }
        for slug in NOTES:
            rendered[f"note:{slug}"] = pages.note(site, lang, slug)
        missing = set(ROUTES) - set(rendered)
        if missing:
            raise SystemExit(f"routes without renderer: {missing}")
        for key, html in rendered.items():
            write(site.out_file(lang, key), html)
            count += 1

    write(DIST / "404.html", pages.not_found(site))
    write(DIST / "sitemap.xml", sitemap(site))
    write(DIST / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {site.config['site']['base_url']}{site.asset('sitemap.xml')}\n")
    write(DIST / ".nojekyll", "")
    print(f"built {count} pages + 404 -> {DIST.relative_to(ROOT)}")
    return 0


def serve(port: int) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"serving http://127.0.0.1:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    rc = build()
    if args.serve:
        serve(args.port)
    sys.exit(rc)
