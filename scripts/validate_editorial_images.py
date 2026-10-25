#!/usr/bin/env python3
"""NewsTrendus publishing gate: link-only, photo-led article images.

News images live on the photographer/CDN's server. Never commit news photos
to GitHub or upload them to any ChatGPT file library. Existing website logos
and icons are separate from editorial hero images.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PHOTO_HOST = "images.pexels.com"
LICENSE_HOST = "www.pexels.com"
MEDIA_SUFFIXES = {".svg", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp", ".tif", ".tiff", ".heic"}
errors: list[str] = []


def issue(path, message):
    errors.append(f"{path}: {message}")


def is_cdn_photo(value):
    u = urlparse(str(value))
    return (
        u.scheme == "https"
        and u.netloc == PHOTO_HOST
        and bool(re.fullmatch(r"/photos/[0-9]+/pexels-photo-[0-9]+\.jpeg", u.path))
        and u.path.split("/")[2] == re.search(r"pexels-photo-([0-9]+)\.jpeg", u.path).group(1)
    )


def photo_id(url):
    match = re.search(r"/photos/([0-9]+)/pexels-photo-\1\.jpeg", url)
    return match.group(1) if match else None


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metadata = {}
        self.hero = []
        self.ld_items = []
        self._ld = False
        self._buf = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.metadata[key.lower()] = attrs.get("content", "")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._ld = True
            self._buf = []
        if tag == "img" and re.search(r"\b(?:nt-hero|nthimg)\b", attrs.get("class", "")):
            self.hero.append(attrs)

    def handle_data(self, data):
        if self._ld:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._ld:
            self._ld = False
            try:
                obj = json.loads("".join(self._buf))
                self.ld_items.extend(obj if isinstance(obj, list) else [obj])
            except ValueError:
                pass


def verify_article(path):
    relative = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    s = Scan()
    s.feed(text)
    if len(s.hero) != 1:
        issue(relative, f"expected one photo hero, found {len(s.hero)}")
        return
    hero = s.hero[0]
    image = hero.get("src", "")
    if not is_cdn_photo(image):
        issue(relative, "hero src must be HTTPS Pexels CDN JPEG; no SVG, local file or data URL")
    if ".svg" in image.lower() or image.startswith(("assets/", "../", "/assets/")):
        issue(relative, "local/SVG news hero is forbidden")
    alt = hero.get("alt", "")
    if len(alt) < 25 or not re.search(r"representative|illustrative|generic", alt, re.I):
        issue(relative, "write meaningful and honest representative-photo alt text")
    try:
        w, h = int(hero.get("width", "0")), int(hero.get("height", "0"))
        if h == 0 or abs(w / h - 16 / 9) > 0.025:
            issue(relative, "hero image HTML width/height must be 16:9 (e.g., 1600x900)")
    except ValueError:
        issue(relative, "hero width/height must be numeric")

    meta_image = s.metadata.get("og:image", "")
    if not is_cdn_photo(meta_image) or photo_id(meta_image) != photo_id(image):
        issue(relative, "og:image must match the article's external CDN photo")
    for node in s.ld_items:
        if not isinstance(node, dict) or node.get("@type") not in ("NewsArticle", "Article"):
            continue
        candidates = node.get("image", [])
        if isinstance(candidates, str):
            candidates = [candidates]
        if isinstance(candidates, dict):
            candidates = [candidates.get("url", "")]
        for candidate in candidates:
            val = candidate.get("url", "") if isinstance(candidate, dict) else candidate
            if not is_cdn_photo(val) or photo_id(val) != photo_id(image):
                issue(relative, "NewsArticle schema image must match CDN photo")
    artist = s.metadata.get("news:photo_artist", "")
    credit = s.metadata.get("news:photo_credit_url", "")
    parsed = urlparse(credit)
    if not artist or parsed.scheme != "https" or parsed.netloc != LICENSE_HOST or not parsed.path.startswith("/photo/"):
        issue(relative, "photographer credit and original Pexels photo-page URL required")
    if credit not in text or "Pexels" not in text:
        issue(relative, "visible photo credit link required below hero image")
    if not re.search(r"\b(?:not (?:a )?photo|not from|not an image|representative)\b", text, re.I):
        issue(relative, "disclose if photo does not depict the reported event")


def check_local_media():
    # The site logo and legacy calculators/guides remain untouched. The
    # article image directory and article folders MUST be text-only.
    for directory in [ROOT / "assets" / "editorial", ROOT / "articles"]:
        if not directory.exists():
            continue
        for f in directory.rglob("*"):
            if f.is_file() and f.suffix.lower() in MEDIA_SUFFIXES:
                issue(f.relative_to(ROOT), "local media in editorial/article directories forbidden; use CDN URL only")


def check_listing():
    for path in (ROOT / "index.html", ROOT / "articles" / "index.html"):
        text = path.read_text(encoding="utf-8")
        if path.name == "index.html" and path.parent == ROOT:
            match = re.search(r'<section\s+id="latest-news-articles"\b[\s\S]*?</section>', text, re.I)
            if not match:
                issue(path.name, "Latest News Articles section missing")
                continue
            text = match.group(0)
        for tag in re.findall(r"<img\b[^>]*>", text, re.I):
            src_match = re.search(r'\bsrc="([^"]+)"', tag)
            if not src_match:
                continue
            src = src_match.group(1)
            if "assets/us-mark.svg" in src:
                continue  # logo remains unchanged
            if not is_cdn_photo(src):
                issue(path.relative_to(ROOT), "news listing contains a local/SVG or non-CDN image: " + src[:110])


def check_catalog():
    path = ROOT / "editorial-news.json"
    if not path.exists():
        issue(path.name, "catalogue missing")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    listed = set()
    for item in data.get("items", []):
        page = item.get("page_url", "")
        image = item.get("image", "")
        listed.add(page)
        if not is_cdn_photo(image):
            issue(page, "editorial JSON requires external Pexels photograph")
        if not item.get("photo_artist") or urlparse(item.get("photo_credit_url", "")).netloc != LICENSE_HOST:
            issue(page, "editorial JSON requires photographer and Pexels photo-page URL")
        if not (ROOT / page).is_file():
            issue(page, "article missing for catalogue entry")
    for html in (ROOT / "articles").glob("20*/*/*.html"):
        if html.relative_to(ROOT).as_posix() not in listed:
            issue(html.relative_to(ROOT), "article is not listed in automatic catalogue")


def main():
    articles = list((ROOT / "articles").glob("20*/*/*.html"))
    check_local_media()
    for path in articles:
        verify_article(path)
    check_listing()
    check_catalog()
    if errors:
        for message in errors:
            print("EDITORIAL IMAGE POLICY ERROR:", message)
        print(f"Image policy FAILED: {len(errors)} issues")
        sys.exit(1)
    print(f"Image policy PASS: {len(articles)} article pages, no uploaded editorial media, all hero/list photos are external and credited.")


if __name__ == "__main__":
    main()
