#!/usr/bin/env python3
"""Create a fresh RSS 2.0 feed of genuine original, canonical on-site articles.

Separate from the legacy Buffer/X feed. RSS shares excerpts and links only,
does not republish third-party articles, and is safe to rerun at each deploy.
"""
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "https://newstrendus.com"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("atom", ATOM)


def stamp(value: str) -> datetime:
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def tag(parent, name, value):
    node = ET.SubElement(parent, name)
    node.text = str(value)
    return node


def main():
    data = json.loads((ROOT / "editorial-news.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    articles = [
        x for x in data.get("items", [])
        if x.get("is_editorial") and
        x.get("url", "").startswith(DOMAIN + "/articles/") and
        x.get("title") and x.get("summary") and x.get("date") and
        stamp(x["date"]) <= now
    ]
    articles.sort(key=lambda x: stamp(x["date"]), reverse=True)
    articles = articles[:40]
    if not articles:
        raise SystemExit("RSS: no real canonical original articles found")
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    tag(channel, "title", "NewsTrendus — Original US News Explainers")
    tag(channel, "link", DOMAIN + "/")
    tag(channel, "description", "Independent US-focused news explainers with attributed original sources and practical reader context.")
    tag(channel, "language", "en-us")
    tag(channel, "lastBuildDate", format_datetime(stamp(articles[0]["date"])))
    ET.SubElement(channel, "{" + ATOM + "}link", {"href": DOMAIN + "/feed.xml", "rel": "self", "type": "application/rss+xml"})
    for article in articles:
        item = ET.SubElement(channel, "item")
        tag(item, "title", article["title"])
        tag(item, "link", article["url"])
        guid = tag(item, "guid", article["url"])
        guid.set("isPermaLink", "true")
        tag(item, "pubDate", format_datetime(stamp(article["date"])))
        tag(item, "description", article["summary"])
        tag(item, "category", article.get("category", "US"))
    ET.indent(rss, space="  ")
    ET.ElementTree(rss).write(ROOT / "feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"Original editorial RSS: {len(articles)} verified article URLs")


if __name__ == "__main__":
    main()
