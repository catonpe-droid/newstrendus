#!/usr/bin/env python3
"""Idempotently enable sharing + static social image metadata for original articles.

Does not touch RSS-based story.html or homepage feed cards. New articles added
later receive the same treatment during the GitHub Pages publish workflow.
"""
from __future__ import annotations
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlparse
import argparse
import os
import re

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"


def meta(text: str, key: str, attr: str = "property") -> str:
    match = re.search(
        r'<meta\\b(?=[^>]*\\b' + attr + r'=["\\\']' + re.escape(key) +
        r'["\\\'])(?=[^>]*\\bcontent=["\\\'](?P<value>[^"\\\']*)["\\\'])[^>]*>',
        text, flags=re.I)
    return unescape(match.group('value')) if match else ""


def tag(key: str, val: str, attr: str = 'property') -> str:
    return f'<meta {attr}="{key}" content="{escape(val, quote=True)}">'


def enhance(path: Path, check: bool = False) -> tuple[bool, list[str]]:
    html = path.read_text(encoding="utf-8")
    if meta(html, "og:type") != "article":
        return False, []
    missing = []
    additions = []
    rel = lambda name: os.path.relpath(ROOT / name, path.parent).replace("\\\\", "/")
    if not re.search(r'<link[^>]+href=["\\\'][^"\\\']*share\\.css', html, flags=re.I):
        additions.append(f'<link rel="stylesheet" href="{rel("share.css")}?v=20261030">')
    if not re.search(r'<script[^>]+src=["\\\'][^"\\\']*share\\.js', html, flags=re.I):
        additions.append(f'<script src="{rel("share.js")}?v=20261030" defer></script>')
    image = meta(html, 'og:image')
    if not image:
        match = re.search(r'<img\\b[^>]*class=["\\\'][^"\\\']*nt-hero[^"\\\']*["\\\'][^>]*>', html, re.I)
        if match:
            src = re.search(r'\\bsrc=["\\\']([^"\\\']+)["\\\']', match.group(0), re.I)
            if src: image = unescape(src.group(1))
        if image and image.startswith("https://"):
            additions.append(tag('og:image', image))
    title = meta(html, "og:title")
    if not title:
        title_tag = re.search(r'<title>(.*?)</title>', html, re.I | re.S)
        if title_tag:
            title = unescape(re.sub(r'\\s+', ' ', title_tag.group(1)).strip()).removesuffix(' | NewsTrendus')
            additions.append(tag("og:title", title))
    desc = meta(html, "og:description") or meta(html, "description", attr="name")
    if desc and not meta(html, "og:description"):
        additions.append(tag("og:description", desc))
    if image and urlparse(image).scheme == "https":
        if not meta(html, 'og:image:secure_url'):
            additions.append(tag('og:image:secure_url', image))
        if not meta(html, 'twitter:image', attr='name'):
            additions.append(tag('twitter:image', image, attr='name'))
    if not meta(html, 'twitter:card', attr='name'):
        additions.append(tag('twitter:card', 'summary_large_image', attr='name'))
    if title and not meta(html, 'twitter:title', attr='name'):
        additions.append(tag('twitter:title', title, attr='name'))
    if desc and not meta(html, 'twitter:description', attr='name'):
        additions.append(tag('twitter:description', desc, attr='name'))
    if not image: missing.append(f'{path.relative_to(ROOT)}: no Open Graph image / article hero')
    if not title: missing.append(f'{path.relative_to(ROOT)}: no article title')
    if '</head>' not in html.lower(): missing.append(f'{path.relative_to(ROOT)}: missing </head>')
    if check:
        if additions: missing.append(f'{path.relative_to(ROOT)}: missing {len(additions)} share/preview tags')
        return False, missing
    if additions:
        html, count = re.subn(r'</head>', ''.join(additions) + '</head>', html, count=1, flags=re.I)
        if count != 1: raise ValueError(f'Missing head: {path}')
        path.write_text(html, encoding='utf-8')
        return True, missing
    return False, missing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Verify without writing')
    args = parser.parse_args()
    if not (ROOT / 'share.js').is_file() or not (ROOT / 'share.css').is_file():
        raise SystemExit('Required sharing assets not found')
    changed = 0
    errors = []
    article_count = 0
    for path in sorted(ARTICLES.rglob('*.html')):
        if path.name == 'index.html': continue
        is_article = meta(path.read_text(encoding='utf-8'), 'og:type') == 'article'
        if not is_article: continue
        article_count += 1
        did_change, problems = enhance(path, check=args.check)
        changed += int(did_change)
        errors.extend(problems)
    print(f'Article share: {article_count} canonical articles, {changed} enhanced; RSS briefs unchanged')
    for error in errors[:25]: print('SHARE WARNING:', error)
    if errors: raise SystemExit(f'{len(errors)} article-sharing issues found')


if __name__ == '__main__':
    main()
