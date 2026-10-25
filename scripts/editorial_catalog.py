#!/usr/bin/env python3
"""Create a source-of-truth catalogue of human-readable, indexable NewsTrendus article pages.

The homepage uses this catalogue alongside, not in place of, credited RSS discovery.
Only real, accessible HTML files are listed; no invented article URLs.
"""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone
import json
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
KNOWN = {"US", "World", "Technology", "Gaming", "Business", "Sports", "Health", "Trending", "Science", "Entertainment"}

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.title = []
        self.in_title = False
        self.jsonld = []
        self.in_ld = False
        self.buf = []
        self.hero = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta":
            key = d.get("property") or d.get("name")
            if key:
                self.meta[key.lower()] = d.get("content", "")
        if tag == "title":
            self.in_title = True
        if tag == "script" and d.get("type") == "application/ld+json":
            self.in_ld = True
            self.buf = []
        if tag == "img" and self.hero is None and ("nt-hero" in d.get("class", "") or "nthimg" in d.get("class", "")):
            self.hero = {"src": d.get("src", ""), "alt": d.get("alt", "")}
    def handle_data(self, data):
        if self.in_title: self.title.append(data)
        if self.in_ld: self.buf.append(data)
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "script" and self.in_ld:
            self.in_ld = False
            try:
                data = json.loads("".join(self.buf))
                self.jsonld.extend(data if isinstance(data, list) else [data])
            except ValueError:
                pass

def catalog():
    items = []
    for p in sorted((ROOT / "articles").rglob("*.html")):
        if p.name == "index.html" or p.name == "404.html": continue
        head = Head()
        try: head.feed(p.read_text(encoding="utf-8"))
        except (UnicodeError, OSError): continue
        if "noindex" in head.meta.get("robots", "").lower(): continue
        rel = p.relative_to(ROOT).as_posix()
        canonical = "https://newstrendus.com/" + rel
        if head.meta.get("og:url") not in ("", canonical): continue
        article = next((v for v in head.jsonld if isinstance(v, dict) and v.get("@type") in ("NewsArticle","Article")), {})
        title = head.meta.get("og:title") or article.get("headline") or "".join(head.title).split(" | NewsTrendus")[0]
        description = head.meta.get("description") or article.get("description") or ""
        category = head.meta.get("article:section") or article.get("articleSection") or "US"
        if category not in KNOWN:
            category = "Sports" if re.search(r"\b(nba|nfl|grand prix|formula 1|football|basketball)\b", title, re.I) else "US"
        date = head.meta.get("article:published_time") or article.get("datePublished")
        if not title or not description or not date: continue
        try:
            parsed = datetime.fromisoformat(str(date).replace("Z", "+00:00"))
            if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)
            published = parsed.astimezone(timezone.utc).isoformat()
        except ValueError: continue
        image = head.meta.get("og:image") or (head.hero or {}).get("src") or ""
        if image.startswith("/"): image = "https://newstrendus.com" + image
        if not image.startswith("https://"): continue
        photographer = head.meta.get("news:photo_artist", "")
        credit_link = head.meta.get("news:photo_credit_url", "")
        items.append({
            "id": "editorial-" + p.stem,
            "title": title,
            "url": canonical,
            "page_url": rel,
            "category": category,
            "summary": description,
            "source": "NewsTrendus",
            "date": published,
            "image": image,
            "image_alt": (head.hero or {}).get("alt") or "Representative photo illustrating the article topic",
            "photo_artist": photographer,
            "photo_credit_url": credit_link,
            "is_editorial": True
        })
    items.sort(key=lambda x: x["date"], reverse=True)
    data = {"generated_at": datetime.now(timezone.utc).isoformat(), "items": items}
    (ROOT / "editorial-news.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Editorial catalogue: {len(items)} source-verified on-site stories")
if __name__ == "__main__":
    catalog()
