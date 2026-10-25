"""Collect credited RSS headlines and US Google Trends without scraping full articles."""
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json, pathlib, re, html, hashlib, os
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
def excerpt(node):
    # RSS descriptions are used as concise attributed previews, never full articles.
    value = node.findtext("description") or node.findtext("{http://www.w3.org/2005/Atom}summary") or ""
    if not value:
        return ""
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"\\s+", " ", html.unescape(value)).strip()
    # No wholesale RSS republication.
    return value[:320].rsplit(" ", 1)[0] if len(value) > 320 else value

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
                items.append({"id":hashlib.sha256(link.encode("utf-8")).hexdigest()[:16],
                 "title":title,"url":link,"category":category,"summary":excerpt(node),
                 "source":urlparse(link).netloc.replace("www.",""),"date":published(val("pubDate") or val("published") or val("updated"))})
            successes+=1
        except Exception as exc: print("Feed unavailable",category,url,str(exc)[:100])
oldfile=BASE/"news.json"
if not items and oldfile.exists():
    old=json.loads(oldfile.read_text())
    items=old.get("items",[]); print("Using last saved feed snapshot")
items.sort(key=lambda x:x["date"] or "",reverse=True)
# Retain previously verified, generated brief text on reruns.
prior = {}
previous = {}
if oldfile.exists():
    try:
        previous = json.loads(oldfile.read_text(encoding="utf-8"))
        prior = {x.get("url"): x for x in previous.get("items", [])}
    except (ValueError, OSError):
        pass
for article in items:
    cached = prior.get(article["url"], {})
    if isinstance(cached.get("brief"), list):
        article["brief"] = cached["brief"]

# Optional original-summary generator. Requires a separate paid API secret.
# Limited to 3 successful briefs per UTC day to avoid accidental excessive costs.
today = datetime.now(timezone.utc).date().isoformat()
count = int(previous.get("ai_generation_count", 0)) if previous.get("ai_generation_date") == today else 0
api_key = os.environ.get("OPENAI_API_KEY", "").strip()
if api_key and count < 3:
    import urllib.request
    # Favor low-risk entertainment/gaming/technology content for automated briefs.
    eligible = [x for x in items if x["category"] in ("Gaming", "Technology", "Entertainment", "Science")
                and len(x.get("summary", "")) >= 125 and not x.get("brief")]
    for article in eligible[:3 - count]:
        payload = {
            "model": os.environ.get("NEWS_AI_MODEL", "gpt-4.1-mini"),
            "instructions": (
                "Write concise, original, factual EN-US news briefs from the provided RSS metadata. "
                "You are a transparent news digest editor, not a reporter. Return ONLY a JSON "
                "object with paragraphs as an array of 1-3 short strings. Use ONLY facts explicitly "
                "present in the title and publisher excerpt. Never invent claims, quotations, context, "
                "release dates, statistics, or quotes. Avoid paraphrasing the source sentence-by-sentence; "
                "add clarity through structure, not through unsupported claims. If material is insufficient, "
                "return {\\\"paragraphs\\\":[]}. Do not use copyright-protected wording or reproduce excerpts."
            ),
            "input": json.dumps({"headline":article["title"],"publisher":article["source"],
                                 "date":article["date"],"feed_excerpt":article["summary"]}),
            "text": {"format": {"type": "json_object"}},
            "max_output_tokens": 300,
        }
        try:
            req=urllib.request.Request("https://api.openai.com/v1/responses",
                   data=json.dumps(payload).encode("utf-8"),
                   headers={"Authorization":"Bearer "+api_key,"Content-Type":"application/json"},
                   method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                result=json.load(response)
            raw="".join(p.get("text","") for x in result.get("output",[])
                        for p in x.get("content",[]) if p.get("type")=="output_text")
            candidate=json.loads(raw).get("paragraphs", [])
            candidate=[p.strip()[:600] for p in candidate if isinstance(p,str) and len(p.strip()) >= 35][:3]
            if candidate:
                article["brief"]=candidate
                count+=1
        except Exception as exc:
            print("Optional AI summary unavailable:", str(exc)[:180])
            break

trends=[]
try:
    root=ET.fromstring(get("https://trends.google.com/trending/rss?geo=US"))
    for n in root.findall(".//item")[:20]:
        title=clean(n.findtext("title"))
        if title: trends.append({"title":title,"url":"https://trends.google.com/trending?geo=US"})
except Exception as exc:
    print("US Trends unavailable:",exc)
    if (BASE/"news.json").exists(): trends=json.loads((BASE/"news.json").read_text()).get("trends",[])
(BASE/"news.json").write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(),"feeds_ok":successes,"items":items[:200],"trends":trends,"ai_generation_date":today,"ai_generation_count":count},ensure_ascii=False),encoding="utf-8")
print("Headlines:",len(items),"Trends:",len(trends),"Feeds working:",successes)
