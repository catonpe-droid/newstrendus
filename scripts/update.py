"""Collect credited RSS headlines and US Google Trends without scraping full articles."""
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json, pathlib, re, html
BASE = pathlib.Path(__file__).resolve().parents[1]
FEEDS = {
    "US": ["https://feeds.npr.org/1001/rss.xml","https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"],
    "Technology": ["https://feeds.arstechnica.com/arstechnica/index","https://www.theverge.com/rss/index.xml"],
    "Gaming": ["https://www.ign.com/articles/feed","https://www.gamespot.com/feeds/mashup/"],
    "Business": ["https://feeds.bbci.co.uk/news/business/rss.xml"],
    "Science": ["https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"],
    "Entertainment": ["https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml"],
    "World": ["https://feeds.bbci.co.uk/news/world/rss.xml"],
}
def get(url):
    r=Request(url,headers={"User-Agent":"NewsTrendusBot/1.0 (attributed feed aggregator)","Accept":"application/rss+xml, application/xml, text/xml"})
    with urlopen(r,timeout=17) as response:
        return response.read(2_000_000)
def clean(x):
    return re.sub(r"<[^>]+>","",html.unescape(x or "")).strip()[:250]
def published(x):
    try: return parsedate_to_datetime(x).astimezone(timezone.utc).isoformat()
    except Exception: return None
items=[]; seen=set(); successes=0
for category, urls in FEEDS.items():
    for url in urls:
        try:
            root=ET.fromstring(get(url)); entries=root.findall(".//item")
            if not entries: entries=root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for node in entries[:35]:
                def val(key): return node.findtext(key) or node.findtext("{http://www.w3.org/2005/Atom}"+key) or ""
                link=val("link")
                if not link:
                    el=node.find("{http://www.w3.org/2005/Atom}link")
                    link=el.attrib.get("href","") if el is not None else ""
                title=clean(val("title"))
                if not title or not link.startswith("https://") or link in seen: continue
                seen.add(link)
                items.append({"title":title,"url":link,"category":category,
                 "source":urlparse(link).netloc.replace("www.",""),"date":published(val("pubDate") or val("published") or val("updated"))})
            successes+=1
        except Exception as exc: print("Feed unavailable",category,url,str(exc)[:100])
oldfile=BASE/"news.json"
if not items and oldfile.exists():
    old=json.loads(oldfile.read_text())
    items=old.get("items",[]); print("Using last saved feed snapshot")
items.sort(key=lambda x:x["date"] or "",reverse=True)
trends=[]
try:
    root=ET.fromstring(get("https://trends.google.com/trending/rss?geo=US"))
    for n in root.findall(".//item")[:20]:
        title=clean(n.findtext("title"))
        if title: trends.append({"title":title,"url":"https://trends.google.com/trending?geo=US"})
except Exception as exc:
    print("US Trends unavailable:",exc)
    if (BASE/"news.json").exists(): trends=json.loads((BASE/"news.json").read_text()).get("trends",[])
(BASE/"news.json").write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(),"feeds_ok":successes,"items":items[:200],"trends":trends},ensure_ascii=False),encoding="utf-8")
print("Headlines:",len(items),"Trends:",len(trends),"Feeds working:",successes)
