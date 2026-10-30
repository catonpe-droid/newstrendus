#!/usr/bin/env python3
"""Idempotently enable sharing + static social image metadata for original articles.

RSS-based story.html is intentionally excluded. New original articles receive
the same enhancement from the GitHub Pages publishing workflow.
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
    # All NewsTrendus generated article metadata use double-quoted attributes.
    expression = r'<meta\b[^>]*\b' + re.escape(attr) + r'="' + re.escape(key) + r'"[^>]*\bcontent="([^"]*)"'
    match = re.search(expression, text, flags=re.I)
    return unescape(match.group(1)) if match else ""


def tag(key: str, value: str, attr: str = "property") -> str:
    return f'<meta {attr}="{key}" content="{escape(value, quote=True)}">'


def enhance(path: Path, check: bool = False) -> tuple[bool, list[str]]:
    html = path.read_text(encoding="utf-8")
    if meta(html, "og:type") != "article":
        return False, []
    problems = []
    additions = []
    def relative(name: str) -> str:
        return os.path.relpath(ROOT / name, path.parent).replace("\\", "/")

    if not re.search(r'<link[^>]+href="[^"]*share\.css', html, flags=re.I):
        additions.append(f'<link rel="stylesheet" href="{relative("share.css")}?v=20261030">')
    if not re.search(r'<script[^>]+src="[^"]*share\.js', html, flags=re.I):
        additions.append(f'<script src="{relative("share.js")}?v=20261030" defer></script>')

    image = meta(html, "og:image")
    if not image:
        hero = re.search(r'<img\b[^>]*class="[^"]*nt-hero[^"]*"[^>]*>', html, flags=re.I)
        if hero:
            src = re.search(r'\bsrc="([^"]+)"', hero.group(0), flags=re.I)
            if src: image = unescape(src.group(1))
        if image.startswith("https://"):
            additions.append(tag("og:image", image))
    title = meta(html, "og:title")
    if not title:
        title_element = re.search(r'<title>(.*?)</title>', html, flags=re.I | re.S)
        if title_element:
            title = unescape(re.sub(r'\s+', ' ', title_element.group(1)).strip()).removesuffix(" | NewsTrendus")
            additions.append(tag("og:title", title))
    description = meta(html, "og:description") or meta(html, "description", attr="name")
    if description and not meta(html, "og:description"):
        additions.append(tag("og:description", description))

    if image.startswith("https://") and urlparse(image).netloc:
        if not meta(html, "og:image:secure_url"):
            additions.append(tag("og:image:secure_url", image))
        if not meta(html, "twitter:image", attr="name"):
            additions.append(tag("twitter:image", image, attr="name"))
    if not meta(html, "twitter:card", attr="name"):
        additions.append(tag("twitter:card", "summary_large_image", attr="name"))
    if title and not meta(html, "twitter:title", attr="name"):
        additions.append(tag("twitter:title", title, attr="name"))
    if description and not meta(html, "twitter:description", attr="name"):
        additions.append(tag("twitter:description", description, attr="name"))

    if not image: problems.append(f"{path.relative_to(ROOT)}: missing article image")
    if not title: problems.append(f"{path.relative_to(ROOT)}: missing title")
    if not re.search(r'</head>', html, flags=re.I): problems.append(f"{path.relative_to(ROOT)}: missing head")
    if check:
        if additions: problems.append(f"{path.relative_to(ROOT)}: missing {len(additions)} share/preview tags")
        return False, problems
    if additions:
        updated, count = re.subn(r'</head>', lambda m: ''.join(additions) + m.group(0), html, count=1, flags=re.I)
        if not count: raise ValueError(f"Missing </head>: {path}")
        path.write_text(updated, encoding="utf-8")
        return True, problems
    return False, problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate without modifying articles")
    args = parser.parse_args()
    if not (ROOT / "share.js").is_file() or not (ROOT / "share.css").is_file():
        raise SystemExit("Sharing JavaScript / CSS assets not found")
    count = 0
    changed = 0
    problems = []
    for file in sorted(ARTICLES.rglob("*.html")):
        if file.name == "index.html": continue
        if meta(file.read_text(encoding="utf-8"), "og:type") != "article": continue
        count += 1
        did_change, warnings = enhance(file, args.check)
        changed += int(did_change)
        problems.extend(warnings)
    print(f"Original article sharing: {count} pages scanned, {changed} updated. RSS briefs excluded.")
    for problem in problems[:25]: print("SHARE WARNING:", problem)
    if problems: raise SystemExit(f"{len(problems)} article preview/sharing issues")


if __name__ == "__main__":
    main()
