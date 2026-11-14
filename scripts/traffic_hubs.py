#!/usr/bin/env python3
"""Maintain original, search-friendly topic hubs using only published article URLs.

This is navigation, not an AI-generated news feed. Sources and original article
publication dates stay untouched. Re-running is deterministic and idempotent.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://newstrendus.com"
TOPICS = [
    {
        "slug": "product-recalls",
        "title": "US Product Recalls: How to Check Models and Refund Steps",
        "short": "Product recalls",
        "description": "Learn how to verify US recalls using model numbers, lot codes or VINs. Find official CPSC, FDA and NHTSA alerts plus practical refund and repair guides.",
        "intro": "Check the exact product before acting on a headline: model, SKU, serial number, lot code or vehicle VIN can determine whether your item is affected. Use the official agency and manufacturer notice for the current safety instructions. The linked articles below explain specific recalls, but this page is a guide, not a live recall database.",
        "pattern": r"\brecall(?:s|ed)?\b|\bcpsc\b|\bfda safety\b",
        "category": None,
        "sources": [("CPSC household-product and toy recalls", "https://www.cpsc.gov/Recalls"), ("FDA food, drug and medical-product alerts", "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"), ("NHTSA vehicle and equipment recalls", "https://www.nhtsa.gov/recalls")],
        "steps": [
            ("Identify the exact item.", "Find the brand and model or SKU on the product label; check serial, UPC, lot or batch codes when the notice lists them. For a vehicle, locate its 17-character VIN."),
            ("Search the correct official source.", "Use CPSC for many consumer goods and toys, FDA for regulated food and medical products, and NHTSA for vehicles. Compare all identifiers and dates with the actual agency notice."),
            ("Follow the product-specific safety instruction.", "Some recalls advise stopping use immediately, disconnecting a product, parking a vehicle outdoors, or following food-disposal guidance. Never assume the remedy is the same for every recall."),
            ("Request the stated remedy and retain records.", "Follow the official company's directions for a repair, replacement or refund. Keep the product-code photo, order record and any confirmation; contact the listed recall support channel if needed."),
        ],
    },
    {
        "slug": "irs-taxes",
        "title": "IRS Tax News: Federal Filing Deadlines, Brackets and Rule Changes",
        "short": "IRS and taxes",
        "description": "Understand recent IRS news, filing deadlines, federal tax bracket changes and the practical details that matter to US taxpayers.",
        "intro": "Tax-year dates and filing-season dates are not always the same. Our US tax explainers identify the year and affected filers, explain what official announcements do and do not change, and link to primary IRS material. They are general information, not individual tax advice.",
        "pattern": r"\birs\b|\btax(?:es|ation|payer|payers)?\b|\bfiling deadline\b|\bstandard deduction\b",
        "category": None,
        "sources": [("IRS Newsroom", "https://www.irs.gov/newsroom"), ("IRS Filing information", "https://www.irs.gov/filing")],
    },
    {
        "slug": "social-security-medicare",
        "title": "Social Security and Medicare: Benefit Changes Explained",
        "short": "Benefits and Medicare",
        "description": "Read source-checked explainers on Social Security, Medicare, retirement benefits and federal health program updates.",
        "intro": "Headlines about benefit cuts, trust funds or Medicare rules often describe projections rather than immediate payment changes. Read what the official documents say, which dates matter and who could be affected. Consult SSA or Medicare directly for personal eligibility and benefits.",
        "pattern": r"\bsocial security\b|\bmedicare\b|\bssa\b|\bretirement benefits?\b",
        "category": None,
        "sources": [("Social Security Administration", "https://www.ssa.gov/"), ("Medicare official website", "https://www.medicare.gov/")],
    },
    {
        "slug": "ai-cybersecurity",
        "title": "Artificial Intelligence and Cybersecurity: US News Explained",
        "short": "AI and cybersecurity",
        "description": "Explore US-focused reporting on AI policy, technology, cybersecurity warnings, data centers and verified government actions.",
        "intro": "AI product announcements, cybersecurity advisories and government proposals can have different legal and practical effects. These explainers separate confirmed decisions from early plans and link to underlying documents or credible coverage.",
        "pattern": r"\bai\b|\bartificial intelligence\b|\bcyber(?:security|attack|crime)?\b|\bdata cent(?:er|re)s?\b|\bopenai\b",
        "category": None,
        "sources": [("CISA cybersecurity alerts", "https://www.cisa.gov/news-events/cybersecurity-advisories"), ("NIST AI Risk Management Framework", "https://www.nist.gov/itl/ai-risk-management-framework")],
    },
]
MARK_START = "<!-- nt-topic-hubs:start -->"
MARK_END = "<!-- nt-topic-hubs:end -->"


def match(item: dict, topic: dict) -> bool:
    return bool(re.search(topic["pattern"], item.get("title", ""), re.I)) and (
        topic["category"] is None or item.get("category") == topic["category"]
    )


def hub_page(topic: dict, stories: list[dict]) -> str:
    slug = topic["slug"]
    url = f"{SITE}/topics/{slug}.html"
    title, desc = escape(topic["title"]), escape(topic["description"])
    rows = []
    for item in stories[:20]:
        relative = "../" + item["page_url"]
        published = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
        stamp = published.strftime("%B %d, %Y")
        rows.append(
            '<article class="nt-hub-article">'
            f'<div class="nt-hub-meta">{escape(item["category"])} · '
            f'<time datetime="{escape(item["date"])}">{stamp}</time></div>'
            f'<h2><a href="{escape(relative, quote=True)}">{escape(item["title"])}</a></h2>'
            f'<p>{escape(item["summary"])}</p></article>'
        )
    steps = topic.get("steps", [])
    checklist = (
        '<section class="nt-recall-checklist" aria-label="Practical recall-checking steps">'
        '<h2 style="font-size:24px;margin:0 0 12px">How to check if your product is recalled</h2>'
        '<ol style="padding-left:23px;line-height:1.75">'
        + "".join(
            f'<li style="margin:0 0 11px"><strong>{escape(heading)}</strong> {escape(detail)}</li>'
            for heading, detail in steps
        )
        + '</ol><p style="font-size:14px;color:#58687b;margin-bottom:0">'
        'These steps are general guidance, not a substitute for a current government or manufacturer notice.'
        '</p></section>'
    ) if steps else ""
    sources = "".join(
        f'<li><a href="{escape(url_, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a></li>'
        for label, url_ in topic["sources"]
    )
    others = " · ".join(
        f'<a href="{escape(other["slug"])}.html">{escape(other["short"])}</a>'
        for other in TOPICS if other["slug"] != slug
    )
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": topic["title"],
        "url": url,
        "description": topic["description"],
        "publisher": {"@type": "Organization", "name": "NewsTrendus", "url": SITE},
    }, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="en-US"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index,follow,max-image-preview:large">
<title>{title} | NewsTrendus</title>
<meta name="description" content="{escape(topic["description"], quote=True)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="NewsTrendus">
<meta property="og:title" content="{escape(topic["title"], quote=True)}">
<meta property="og:description" content="{escape(topic["description"], quote=True)}">
<meta property="og:url" content="{url}">
<link rel="stylesheet" href="../site.css"><link rel="icon" type="image/svg+xml" href="../assets/us-mark.svg">
<script type="application/ld+json">{schema}</script>
<style>
.nt-hub-wrap{{max-width:1010px;margin:34px auto 65px}}
.nt-hub-intro{{font-size:18px;line-height:1.7;max-width:820px;color:#46576b}}
.nt-hub-grid{{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:34px;margin-top:30px}}
.nt-hub-article{{padding:20px 0;border-bottom:1px solid #e2e8f0}}
.nt-hub-article h2{{font-size:21px;line-height:1.35;margin:6px 0}}
.nt-hub-article h2 a:hover,.nt-hub-aside a:hover{{color:#b11b37;text-decoration:underline}}
.nt-hub-article p{{color:#58687b;line-height:1.6;margin:5px 0}}
.nt-hub-meta{{color:#64748b;font-size:12px;font-weight:700;text-transform:uppercase}}
.nt-recall-checklist{{margin:24px 0 6px;padding:22px 25px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px}}
.nt-recall-checklist li::marker{{color:#475569;font-weight:700}}
.nt-hub-aside{{border:1px solid #e2e8f0;border-radius:12px;padding:19px;align-self:start;background:white}}
.nt-hub-aside li{{margin:11px 0;line-height:1.5}}
@media(max-width:760px){{.nt-hub-grid{{grid-template-columns:1fr}}.nt-hub-wrap{{margin-top:22px}}}}
</style>
</head><body>
<div class="topline"><div class="container">United States edition · NewsTrendus topic guides</div></div>
<header class="masthead"><div class="container masthead-inner"><a class="brand" href="../index.html">News<span>Trendus</span>.com</a><span>Source-linked US reporting</span></div></header>
<div class="navshell"><nav class="container nav" aria-label="Site navigation"><a href="../index.html">Home</a><a href="../articles/index.html">Latest articles</a><a href="../editorial.html">Editorial standards</a><a href="../contact.html">Contact</a></nav></div>
<main class="container nt-hub-wrap">
<span class="eyebrow">NewsTrendus · Reader topic guide</span>
<h1>{title}</h1>
<p class="nt-hub-intro">{escape(topic["intro"])}</p>
{checklist}
<div class="nt-hub-grid"><section aria-label="Related original articles">
<p class="state">Latest related NewsTrendus articles, newest first. Each report links to its cited factual sources.</p>
{''.join(rows)}
</section><aside class="nt-hub-aside"><h2 style="font-size:18px">Primary resources</h2><ul>{sources}</ul>
<p style="font-size:13px;line-height:1.7">Official agency pages are authoritative for the latest notices. NewsTrendus is independent and does not represent these agencies.</p>
<h2 style="font-size:17px;margin-top:25px">Explore more</h2><p style="line-height:1.9">{others}</p>
</aside></div></main>
<footer class="foot"><div class="container footin"><div><a href="../index.html" class="brand">News<span>Trendus</span></a><p>Independent US-focused news explainers and practical reader guides.</p></div><nav><a href="../about.html">About</a><a href="../privacy.html">Privacy</a><a href="../contact.html">Contact</a></nav></div></footer>
</body></html>
'''


def insert_links(path: Path, prefix: str, anchor: str):
    html = path.read_text(encoding="utf-8")
    links = " · ".join(
        f'<a href="{prefix}topics/{t["slug"]}.html">{escape(t["short"])}</a>'
        for t in TOPICS
    )
    block = (
        f'{MARK_START}<nav class="container" aria-label="News topic guides" '
        'style="padding:18px 20px;margin:18px auto;border:1px solid #e2e8f0;'
        'border-radius:12px;background:#fff;line-height:2">'
        f'<strong style="margin-right:12px">Explore US topics:</strong>{links}'
        f'</nav>{MARK_END}'
    )
    if MARK_START in html and MARK_END in html:
        pattern = re.escape(MARK_START) + r".*?" + re.escape(MARK_END)
        updated, n = re.subn(pattern, lambda _: block, html, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"Failed to refresh topic navigation in {path}")
    elif anchor in html:
        updated = html.replace(anchor, block + "\n" + anchor, 1)
    else:
        raise SystemExit(f"Missing topic navigation anchor: {path}")
    if updated != html:
        path.write_text(updated, encoding="utf-8")


def main():
    source = json.loads((ROOT / "editorial-news.json").read_text(encoding="utf-8"))
    items = [x for x in source.get("items", []) if x.get("is_editorial") and x.get("page_url", "").startswith("articles/")]
    (ROOT / "topics").mkdir(exist_ok=True)
    for topic in TOPICS:
        matching = sorted(
            (i for i in items if match(i, topic)),
            key=lambda i: i["date"], reverse=True
        )
        if not matching:
            raise SystemExit(f"No real articles available for hub: {topic['slug']}")
        path = ROOT / "topics" / (topic["slug"] + ".html")
        body = hub_page(topic, matching)
        if not path.exists() or path.read_text(encoding="utf-8") != body:
            path.write_text(body, encoding="utf-8")
        print(f"TOPIC HUB: {topic['slug']} — {len(matching)} matching original articles")
    insert_links(ROOT / "index.html", "", '<section id="latest-news-articles"')
    insert_links(ROOT / "articles" / "index.html", "../", '<main class="container nt-list">')


if __name__ == "__main__":
    main()
