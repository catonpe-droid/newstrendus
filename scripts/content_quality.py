#!/usr/bin/env python3
"""User-first publishing hygiene for NewsTrendus.

Prevents empty promotional listings from being promoted or indexed; clarifies
authorship/methods on source-linked articles; and labels retired news snapshots.
No claims about AdSense approval or search rankings. No new photos are stored.
Idempotent: safe to run on each GitHub Pages deployment.
"""
from __future__ import annotations

from pathlib import Path
from html import escape
from urllib.parse import urlparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
NAV_RE = re.compile(r"(<nav\b[^>]*>)(.*?)(</nav>)", re.I | re.S)
COMMERCIAL_LINK_RE = re.compile(
    r"<a\b[^>]*\bhref=['\"][^'\"]*(?:business-directory|advertise)\.html"
    r"(?:[?#][^'\"]*)?['\"][^>]*>.*?</a>", re.I | re.S
)
META_RE = re.compile(r"(<div class=['\"]article-meta['\"]>)(.*?)(</div>)", re.I | re.S)
STAMP = "<!-- nt-article-methodology-v1 -->"


def relative_prefix(path: Path) -> str:
    return "../" * (len(path.relative_to(ROOT).parts) - 1)


def content_count() -> int:
    try:
        data = json.loads((ROOT / "businesses.json").read_text(encoding="utf-8"))
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            return len(data.get("items", []))
    except (OSError, ValueError, TypeError):
        pass
    return 0


def prevent_indexing(text: str) -> str:
    # A page made entirely of an unlaunched directory/advertising pitch is not
    # treated as editorial publisher inventory during AdSense site review.
    if re.search(r"<meta\s+name=['\"]robots['\"]", text, re.I):
        return re.sub(
            r"<meta\s+name=['\"]robots['\"][^>]*>",
            '<meta name="robots" content="noindex,follow">',
            text, count=1, flags=re.I
        )
    return text.replace("</head>", '<meta name="robots" content="noindex,follow"></head>', 1)


def revise_elections_page(text: str) -> str:
    text = text.replace(
        "Latest Election Headlines",
        "Election source links (not live results)"
    )
    text = text.replace(
        "Listings update automatically from public news-search RSS and may not cover every race.",
        "This feed is a dated archive, not live election results. For current returns, consult your state election office."
    )
    text = re.sub(
        r"<h2>How often headlines refresh</h2><p>.*?</p>",
        "<h2>How current are these headlines?</h2><p>Our public news-search snapshot may be out of date. "
        "When it is more than 48 hours old, we hide its headlines rather than imply they are current. "
        "This page is not an official vote-counting service. Confirm current results, registration "
        "and ballot information with your state election office.</p>",
        text, count=1, flags=re.I | re.S
    )
    text = text.replace(
        "Coverage searches rotate among states during scheduled refreshes.",
        "Historical links are displayed only when the source snapshot is current."
    )
    return text


def article_disclosure(text: str, prefix: str) -> str:
    # Existing hand-authored methodology notes count as disclosures too.
    # Otherwise the deploy job can append a second notice to the same story.
    if STAMP in text or 'class="nt-method-note"' in text or "class='nt-method-note'" in text:
        return text
    if "class=\"article-meta\"" not in text:
        return text

    def place(match):
        lead, inner, end = match.groups()
        old = "By NewsTrendus Editorial Desk"
        if old in inner:
            inner = inner.replace(
                old,
                f'By <a href="{prefix}editorial.html">NewsTrendus Editorial Desk</a>'
            )
        note = (
            f'{STAMP}<p class="nt-method-note" style="font-size:13px;line-height:1.65;'
            f'color:#526174;margin:12px 0 0">This is a source-linked desk explainer, '
            f'not first-hand reporting. Research and drafting may use AI-assisted tools. '
            f'Follow the cited source links and read our '
            f'<a href="{prefix}editorial.html">editorial and corrections policy</a>.</p>'
        )
        return lead + inner + end + note
    return META_RE.sub(place, text, count=1)


def tidy_site():
    approved = content_count()
    changed = []
    news_articles = 0
    for path in ROOT.rglob("*.html"):
        if any(p in {".git", "node_modules", "__pycache__"} for p in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        before = path.read_text(encoding="utf-8")
        text = before
        prefix = relative_prefix(path)

        if approved == 0 or rel == "advertise.html":
            # Empty directory and advertising-only pages are not central
            # news destinations; keep them reachable via disclosure links.
            if approved == 0:
                text = NAV_RE.sub(
                    lambda m: m.group(1) + COMMERCIAL_LINK_RE.sub("", m.group(2)) + m.group(3),
                    text
                )
            else:
                text = NAV_RE.sub(
                    lambda m: m.group(1) + re.sub(
                        r"<a\b[^>]*\bhref=['\"][^'\"]*advertise\.html(?:[?#][^'\"]*)?['\"][^>]*>.*?</a>",
                        "", m.group(2), flags=re.I | re.S
                    ) + m.group(3), text
                )
        if rel == "business-directory.html" and approved == 0:
            text = prevent_indexing(text)
        if rel == "advertise.html":
            text = prevent_indexing(text)
        if rel == "index.html":
            text = text.replace(
                "Fresh headlines, short on-site briefs and related coverage from credited sources. This is a curated news digest, not independent original reporting.",
                "Read source-linked U.S. explainers with clear dates, cited reporting and practical context. These are desk articles, not eyewitness reports; check the linked primary sources for developing stories."
            )
        if rel == "politics/elections.html":
            text = revise_elections_page(text)
        if re.fullmatch(r"articles/20\d{2}/\d{2}/[^/]+\.html", rel):
            news_articles += 1
            text = article_disclosure(text, prefix)
        # Remove a misleading footer claim about automatic news updates:
        text = text.replace(
            "Stories are automatically updated and may not be independently verified.",
            "Please confirm fast-changing claims with the linked primary sources."
        )
        if text != before:
            path.write_text(text, encoding="utf-8")
            changed.append(rel)

    print(f"QUALITY HYGIENE: updated {len(changed)} page(s); {news_articles} news articles inspected; "
          f"{approved} approved commercial directory listings.")
    print("QUALITY POLICY: no fictional businesses, no false live-results labels, no uploaded news images.")
    return changed


def assess():
    warnings = []
    articles = sorted((ROOT / "articles").glob("20*/*/*.html"))
    for path in articles:
        text = path.read_text(encoding="utf-8")
        content = text.split('class="article-inside nt-story-content"', 1)
        if len(content) < 2:
            warnings.append(f"{path.relative_to(ROOT)}: no standardized article body")
            continue
        body = content[1].split("</article>", 1)[0]
        visible = re.sub(r"<[^>]+>", " ", body)
        visible = re.sub(r"\s+", " ", visible)
        domains = {
            urlparse(m.group(1)).netloc
            for m in re.finditer(r'<a\b[^>]*href="(https?://[^"]+)"', body, re.I)
            if not any(d in m.group(1) for d in ("newstrendus.com", "pexels.com"))
        }
        # A heuristic for editorial review, not a Google minimum word count.
        if len(visible.split()) < 280 or len(domains) < 2:
            warnings.append(f"{path.relative_to(ROOT)}: review depth and independent source diversity")
    print(f"QUALITY AUDIT: {len(articles)} article pages sampled structurally; "
          f"{len(warnings)} editorial-review flag(s).")
    for warning in warnings[:30]:
        print("QUALITY REVIEW:", warning)
    print("This technical check cannot confirm article originality, facts, author expertise or AdSense approval.")


if __name__ == "__main__":
    tidy_site()
    assess()
