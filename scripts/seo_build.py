#!/usr/bin/env python3
"""Zero-cost Search Console / technical SEO checks for NewsTrendus.

Generate a canonical-only XML sitemap for all STATIC, indexable, genuine pages.
No RSS previews, javascript query-string story.html, or generated JSON URLs.
Print warnings for metadata quality and broken local HTML links, but never
invent Google indexing or submit to Search Console without authorization.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from html import unescape
from html.parser import HTMLParser
from xml.sax.saxutils import escape
from urllib.parse import urlparse, unquote
import sys, re

ROOT=Path(__file__).resolve().parents[1]
DOMAIN="https://newstrendus.com"
IGNORED_DIRS={".git",".github","__pycache__",".venv","node_modules"}
IGNORE_FILES={"story.html","404.html"}

class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title=[]
        self._in_title=False
        self.meta={}
        self.links=[]
        self.anchors=[]
        self.h1_count=0
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=="title":self._in_title=True
        if tag=="h1":self.h1_count+=1
        if tag=="meta":
            key=(d.get("name") or d.get("property") or "").lower()
            if key:self.meta[key]=d.get("content","")
        if tag=="link":self.links.append(d)
        if tag=="a" and d.get("href"):self.anchors.append(d["href"])
    def handle_endtag(self, tag):
        if tag=="title":self._in_title=False
    def handle_data(self, data):
        if self._in_title:self.title.append(data)

def read(path):
    x=Tags()
    x.feed(path.read_text(encoding="utf-8"))
    return x

def urls(path):
    rel=path.relative_to(ROOT).as_posix()
    return DOMAIN+"/" if rel=="index.html" else DOMAIN+"/"+rel

def main():
    files=sorted(path for path in ROOT.rglob("*.html")
                 if not (set(path.relative_to(ROOT).parts)&IGNORED_DIRS)
                 and path.name not in IGNORE_FILES)
    pages=[];warnings=[];broken=[]
    known=set(files)
    for file in files:
        try:p=read(file)
        except (OSError,UnicodeError) as exc:
            warnings.append(f"Unreadable HTML {file.relative_to(ROOT)}: {exc}")
            continue
        rel=file.relative_to(ROOT).as_posix()
        if "noindex" in p.meta.get("robots","").lower():
            continue
        canonical=next((x.get("href") for x in p.links if x.get("rel")=="canonical"),None)
        expected=urls(file)
        if canonical!=expected:
            warnings.append(f"Bad canonical {rel}: {canonical!r} (expected {expected})")
            continue
        if not "".join(p.title).strip():warnings.append(f"Missing title: {rel}")
        if len(p.meta.get("description","").strip())<65:
            warnings.append(f"Short/missing meta description: {rel}")
        if p.h1_count!=1:warnings.append(f"H1 count {p.h1_count}: {rel}")
        if not p.meta.get("viewport"):warnings.append(f"Missing viewport: {rel}")
        pages.append((rel,canonical))
        for href in p.anchors:
            if href.startswith(("http:","https:","mailto:","tel:","#","javascript:")):continue
            href=unquote(href.split("#")[0].split("?")[0])
            if not href:continue
            target=(file.parent/href).resolve()
            if target.is_dir():target/= "index.html"
            if ROOT.resolve() not in target.parents and target!=ROOT.resolve():
                continue
            if target.suffix==".html" and target not in known and not target.exists():
                broken.append(f"{rel} -> {href}")
    pages.sort(key=lambda x:("" if x[0]=="index.html" else x[0]))
    if not pages or pages[0][0]!="index.html":
        raise SystemExit("SEO ERROR: index.html missing or excluded from sitemap")
    xml='<?xml version="1.0" encoding="UTF-8"?>\n'
    xml+='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for _,u in pages:xml+='  <url><loc>'+escape(u)+'</loc></url>\n'
    xml+='</urlset>\n'
    (ROOT/"sitemap.xml").write_text(xml,encoding="utf-8")
    # Google News sitemap: only genuine, canonical articles published within
    # the previous two days; preserve their ORIGINAL publication timestamps.
    # Do not use "last modified" as publication time or include RSS previews.
    news_rows=[]
    cutoff=datetime.now(timezone.utc)-timedelta(days=2)
    now=datetime.now(timezone.utc)
    for rel, url in pages:
        if not rel.startswith("articles/") or rel=="articles/index.html":
            continue
        meta=read(ROOT/rel).meta
        published=meta.get("article:published_time","")
        title=unescape(meta.get("og:title","").strip())
        if not (published and title):
            continue
        try:
            posted=datetime.fromisoformat(published.replace("Z","+00:00"))
            if posted.tzinfo is None:
                continue
            posted=posted.astimezone(timezone.utc)
        except (ValueError,TypeError,OverflowError):
            continue
        if cutoff <= posted <= now:
            news_rows.append((posted,url,title))
    news_rows.sort(key=lambda row:row[0],reverse=True)
    if len(news_rows)>1000:
        print("NEWS SITEMAP WARNING: over 1000 recent articles; retaining newest 1000")
        news_rows=news_rows[:1000]
    news_xml='<?xml version="1.0" encoding="UTF-8"?>\n'
    news_xml+='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
    for posted,url,title in news_rows:
        news_xml+='  <url><loc>'+escape(url)+'</loc><news:news>\n'
        news_xml+='    <news:publication><news:name>NewsTrendus</news:name><news:language>en</news:language></news:publication>\n'
        news_xml+='    <news:publication_date>'+posted.isoformat(timespec="seconds")+'</news:publication_date>\n'
        news_xml+='    <news:title>'+escape(title)+'</news:title></news:news></url>\n'
    news_xml+='</urlset>\n'
    (ROOT/"news-sitemap.xml").write_text(news_xml,encoding="utf-8")
    print(f"NEWS SITEMAP: {len(news_rows)} recent original articles (last 48 hours)")
    (ROOT/"robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: "+DOMAIN+"/sitemap.xml\nSitemap: "+DOMAIN+"/news-sitemap.xml\n",
        encoding="utf-8")
    print(f"SEO CHECK: {len(pages)} indexable static canonical pages in sitemap.xml")
    print(f"SEO CHECK: {len(warnings)} metadata warnings, {len(broken)} broken HTML links")
    for message in warnings[:30]:print("SEO WARNING:",message)
    for message in broken[:30]:print("SEO BROKEN LINK:",message)
    # This is a site audit, not a guarantee of inclusion in Google Search.
    # Do not halt publishing for noncritical copy quality.
    if broken:
        print("SEO WARNING: Fix broken internal links before asking Google to index.")
    if len(pages)<25:
        raise SystemExit("SEO ERROR: fewer indexable static pages than expected.")

if __name__=="__main__":main()
