# igor-millis · portfolio

Static, bilingual (EN at `/`, PT at `/pt/`) portfolio built with a small Python generator —
**standard library only**, no Node, no frameworks. Deployed to GitHub Pages by GitHub Actions.

## Run locally

```bash
python build.py --serve      # builds into dist/ and serves http://127.0.0.1:8000
```

## Where things live

| Path | What |
|---|---|
| `config.toml` | URL, base path, author links, languages |
| `content/en.toml`, `content/pt.toml` | All text, per language (inline HTML allowed in `'''` strings) |
| `content/notes/<slug>.<lang>.html` | Research note bodies (KaTeX: `\( … \)` and `\[ … \]`) |
| `data/*.json` | Project numbers, copied from the source repositories (each file names its sources) |
| `builder/` | Generator: `core.py` (routes, URLs, formatting), `layout.py` (head/SEO, header, footer, ⌘K), `pages.py`, `charts.py` (SVG) |
| `static/` | CSS, JS, images, favicon, `og.png` — copied as-is |
| `tools/make_og.py` | Regenerates `static/og.png` (local, needs Pillow) |

## Common edits

- **Change text:** edit `content/<lang>.toml` in both languages, then rebuild.
- **Add a research note:** write `content/notes/<slug>.en.html` and `.pt.html`, add metadata under
  `[research.<key>]` in both TOML files, register the slug in `NOTES` and `ROUTES` (`builder/core.py`),
  and list it in `pages.research` and `pages.note`.
- **Add a project:** add a `[work.<key>]` table in both TOML files, a route in `ROUTES`, a renderer in
  `builder/pages.py`, and a row in `project_rows`.

## Deploy (GitHub Pages)

1. Create the repository **`Igor-Millis.github.io`** and push this folder to `main`.
2. In the repository: *Settings → Pages → Build and deployment → Source: GitHub Actions*.
3. Every push to `main` runs `.github/workflows/deploy.yml` and publishes `dist/`.

Using a different repository name (e.g. `portfolio`)? Set `base_path = "/portfolio"` in `config.toml`.

## Principles

Every number on the site comes from the linked repositories (README, notebooks, decision logs or test
files). Interactive demos are replays of real data — nothing runs on a server.
