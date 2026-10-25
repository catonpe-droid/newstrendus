#!/usr/bin/env python3
"""Synchronize static homepage and article-index cards from verified article catalogue.

Only external Pexels CDN URL references are stored; no image file is fetched,
downloaded, uploaded or committed. Existing header, menu and footer stay intact.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "editorial-news.json"
CDN = "https://images.pexels.com/photos/"
FALLBACK = CDN + "33535231/pexels-photo-33535231.jpeg?auto=compress&cs=tinysrgb&w=1200"


def card(item, article_index=False):
    page = item["page_url"]
    link = page.removeprefix("articles/") if article_index else page
    img = item["image"]
    if not img.startswith(CDN) or ".svg" in img.lower():
        raise ValueError(f"Article has non-CDN/SVG image: {page}")
    title = escape(item["title"])
    desc = escape(item.get("summary", ""))
    category = escape(item["category"])
    date = datetime.fromisoformat(item["date"].replace("Z", "+00:00")).strftime("%B %d, %Y").upper()
    alt = escape(item.get("image_alt", "Representative editorial photograph"))
    artist = escape(item["photo_artist"])
    credit = escape(item["photo_credit_url"], quote=True)
    return (
        f'<article class="card"><a href="{escape(link, quote=True)}" aria-label="Read article: {title}">'
        f'<img loading="lazy" decoding="async" src="{escape(img, quote=True)}" '
        f'alt="{alt}" width="1600" height="900" '
        f'onerror="this.onerror=null;this.src=\'{escape(FALLBACK, quote=True)}\'"></a>'
        f'<div class="in"><span class="photo-attribution">Representative photo (not of this event): '
        f'<a href="{credit}" target="_blank" rel="noopener noreferrer">{artist} / Pexels</a></span>'
        f'<span class="kicker">{category} · {date}</span>'
        f'<h3><a href="{escape(link, quote=True)}">{title}</a></h3>'
        f'<p class="excerpt">{desc}</p>'
        f'<div class="byline">NewsTrendus Editorial Desk · Source-verified coverage</div></div></article>'
    )


def update(path, pattern, items, article_index=False):
    text = path.read_text(encoding="utf-8")
    replacement = "\n" + "\n".join(card(x, article_index) for x in items) + "\n"
    updated, n = pattern.subn(lambda m: m.group("open") + replacement + m.group("close"), text, count=1)
    if n != 1:
        raise SystemExit(f"Unable to locate article grid in {path.relative_to(ROOT)}; unchanged")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
    print(f"Updated {path.relative_to(ROOT)} with {len(items)} external-photo cards")


def main():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    items = [x for x in data.get("items", []) if x.get("is_editorial")]
    if not items:
        raise SystemExit("No verified editorial articles in catalogue")
    items.sort(key=lambda x: x["date"], reverse=True)
    home = re.compile(
        r'(?P<open><section\b[^>]*\bid="latest-news-articles"[^>]*>[\s\S]*?<div class="feedgrid">)'
        r'[\s\S]*?(?P<close></div>\s*</section>)', re.I
    )
    articles = re.compile(
        r'(?P<open><main class="container nt-list">[\s\S]*?<div class="feedgrid">)'
        r'[\s\S]*?(?P<close></div></main>)', re.I
    )
    update(ROOT / "index.html", home, items[:24])
    update(ROOT / "articles" / "index.html", articles, items[:120], article_index=True)


if __name__ == "__main__":
    main()
