"""Shared state: configuration, content, data, routes, URL and number helpers."""
from __future__ import annotations

import hashlib
import html
import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# Route keys → path (without language prefix). Same slugs in every language,
# so the language switch and hreflang only swap the prefix.
ROUTES: dict[str, str] = {
    "home": "/",
    "about": "/about/",
    "work": "/work/",
    "edudata": "/work/edudata/",
    "credit": "/work/credit-default-api/",
    "recommender": "/work/adaptive-recommender/",
    "research": "/research/",
}

# Research notes, newest first. Each slug needs [research.notes.<slug>] in every content/<lang>.toml
# and a body in content/notes/<slug>.<lang>.html.
NOTES = ["claude-skills", "negative-binomial", "bootstrap", "local-llms", "why-the-house-wins", "calibration-check", "threshold-is-a-decision"]
ROUTES.update({f"note:{s}": f"/research/{s}/" for s in NOTES})


def _toml(rel: str) -> dict:
    return tomllib.loads((ROOT / rel).read_text(encoding="utf-8"))


def _json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


@dataclass
class Site:
    config: dict = field(default_factory=lambda: _toml("config.toml"))
    content: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for lang in self.langs:
            self.content[lang] = _toml(f"content/{lang}.toml")
        self.data = {"credit": _json("data/credit_default.json"), "edudata": _json("data/edudata.json"),
                     "calibration": _json("data/calibration.json"),
                     "bets": _json("data/bets.json"), "bootstrap": _json("data/bootstrap.json"), "negbin": _json("data/negbin.json"),
                     "recommender": _json("data/recommender.json")}

    # ---- languages -------------------------------------------------------
    @property
    def langs(self) -> list[str]:
        return list(self.config["langs"])

    def lang(self, code: str) -> dict:
        return self.config["langs"][code]

    def other(self, code: str) -> str:
        return next(l for l in self.langs if l != code)

    # ---- urls ------------------------------------------------------------
    def url(self, lang: str, key: str) -> str:
        return self.config["site"]["base_path"] + self.lang(lang)["prefix"] + ROUTES[key]

    def abs_url(self, lang: str, key: str) -> str:
        return self.config["site"]["base_url"] + self.url(lang, key)

    def asset(self, path: str) -> str:
        return self.config["site"]["base_path"] + "/" + path.lstrip("/")

    def asset_v(self, path: str) -> str:
        """Asset URL with a content hash, so browsers refetch CSS/JS after each change."""
        digest = hashlib.sha1((ROOT / "static" / path).read_bytes()).hexdigest()[:8]
        return f"{self.asset(path)}?v={digest}"

    def out_file(self, lang: str, key: str) -> Path:
        rel = (self.lang(lang)["prefix"] + ROUTES[key]).strip("/")
        return DIST / rel / "index.html"


# ---- text helpers --------------------------------------------------------
def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def attr(s: str) -> str:
    """Plain-text, escaped version of a (possibly HTML) string for attributes and <title>."""
    return esc(strip_tags(s))


def num(x: float, lang: str, digits: int = 4) -> str:
    s = f"{x:,.{digits}f}"
    if lang == "pt":
        s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return s


def integer(n: int, lang: str) -> str:
    s = f"{n:,}"
    return s.replace(",", ".") if lang == "pt" else s
