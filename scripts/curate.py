"""NewsTrendus editorial-style automatic shortlist (free; no API keys).

Publish exactly 45 current headlines when enough quality stories exist.
Google Trends US related coverage and permitted long articles are featured;
source credibility, freshness, variety and US relevance shape the shortlist.
These are automated relevance heuristics, NOT verification of factual accuracy
and NOT real Google search-volume measurements.
"""
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"news.json"
TARGET=45
MIN_TARGET=40
CAP={
    "Trending":10, "US":11, "Gaming":7, "Sports":6,
    "Technology":6,"Business":5,"Health":8,"Science":5,
    "Entertainment":5,"World":4
}
# These are desired variety targets, not requirements to invent a story.
CATEGORY_FLOOR={
    "US":7,"Gaming":5,"Sports":4,"Technology":3,
    "Business":2,"Health":3,"Science":2,
    "Entertainment":2,"World":2
}
SOURCE_CAP=10
KEYWORDS={
    "Gaming":("gta 6","gta vi","grand theft auto","rockstar","playstation","xbox","nintendo","game release","trailer"),
    "Technology":("ai","artificial intelligence","apple","google","microsoft","chip","cyber","security","iphone","openai","robot"),
    "US":("united states","american","congress","white house","supreme court","california","new york","texas","federal","us election"),
    "Business":("stocks","earnings","market","inflation","federal reserve","interest rate","economy","jobs report","retail"),
    "Sports":("nba","nfl","world series","mlb","grand prix","formula 1","f1","championship","final","record"),
    "Health":("medicaid","medicare","health insurance","affordable care","vaccine","hospital","health cost"),
    "Science":("nasa","moon","space","mars","rocket","astronaut","research","mission"),
}
STRIPWORDS={"the","a","an","to","of","for","in","and","with","as","at","by","on","is","are","from","after","this","that","its","new"}
NOISY_WORDS=("newsletter","daily briefing","weekly roundup","liveblog","advertisement","sponsored by","daily puzzle")

def age_hours(item, now):
    try:
        dt=datetime.fromisoformat(item.get("date") or "")
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return max(0,(now-dt.astimezone(timezone.utc)).total_seconds()/3600)
    except (ValueError,TypeError,OverflowError):
        return 999

def tokens(title):
    text=re.sub(r"\s*[-|–]\s*(bbc|the athletic|npr|ap news|reuters|cbs sports).*$","",title.casefold())
    return {w for w in re.findall(r"[a-z0-9]+",text) if len(w)>2 and w not in STRIPWORDS}

def good(item, now):
    name=item.get("title") or ""
    url=item.get("url") or ""
    if len(name)<23 or len(name)>250 or len(name.split())<5:return False
    if any(x in name.casefold() for x in NOISY_WORDS):return False
    parsed=urlparse(url)
    if parsed.scheme!="https" or not parsed.netloc:return False
    old=age_hours(item,now)
    # Licensable long pieces may remain useful for several days.
    if old>24*9 and not item.get("full_html"):return False
    if old>24*20:return False
    return True

def quality_score(item, now):
    age=age_hours(item,now)
    section=item.get("category","")
    title=(item.get("title") or "").casefold()
    summary=item.get("summary") or ""
    # A connected trend is a real US trend-feed association, not a made-up traffic claim.
    trend=bool(item.get("trend_seed") or item.get("trend_matches"))
    score=110 if item.get("trend_seed") else (65 if trend else 0)
    score+=32 if item.get("full_html") else 0
    score+=min(18,len(summary)//18)
    score+=max(0,40-math.sqrt(age)*5)
    score+=12 if section=="US" else 0
    score+=10 if section in ("Gaming","Sports") else 0
    score+=8 if section in ("Health","Technology","Science") else 0
    score+=5 if section in ("Business","Entertainment") else 0
    for word in KEYWORDS.get(section,()):
        if word=="ai":
            if re.search(r"\bai\b",title):score+=8
        elif word in title:score+=8
    score-=12 if age>96 else 0
    score-=15 if not summary and not item.get("full_html") else 0
    return round(score,2)

def main():
    data=json.loads(DATA.read_text(encoding="utf-8"))
    now=datetime.now(timezone.utc)
    source=data.get("items",[])
    candidates=sorted((x for x in source if good(x,now)),
                      key=lambda x:(-quality_score(x,now),x.get("id","")))
    selected=[]
    selected_urls=set()
    selected_tokens=[]
    sources=Counter()
    categories=Counter()
    def take(article,relax=False):
        if len(selected)>=TARGET:return False
        url=article["url"].split("?")[0].rstrip("/")
        category=article.get("category","World")
        domain=article.get("source","")
        if url in selected_urls:return False
        if not relax and (categories[category]>=CAP.get(category,4) or sources[domain]>=SOURCE_CAP):
            return False
        words=tokens(article.get("title",""))
        if words and any(len(words&other)>=4 and
                         len(words&other)/len(words|other)>.67 for other in selected_tokens if other):
            return False
        selected.append(article);selected_urls.add(url)
        selected_tokens.append(words);sources[domain]+=1;categories[category]+=1
        article["selection_score"]=quality_score(article,now)
        return True
    def choose(pool,limit):
        n=0
        for item in pool:
            if take(item):
                n+=1
                if n>=limit or len(selected)>=TARGET:break
        return n

    # First secure a restrained set of real US Google Trends-linked reports.
    choose((x for x in candidates if x.get("category")=="Trending"
            and x.get("trend_seed")),9)
    # Long-format pieces provide extra reading value, with verified rights restrictions.
    choose((x for x in candidates if x.get("full_html")
            and x.get("license_type") in ("NASA government release",
                "KFF Health News licensed republication")),7)
    # Don't let one fast-paced topic crowd out major sections.
    for section,minimum in CATEGORY_FLOOR.items():
        deficit=max(0,minimum-categories[section])
        choose((x for x in candidates if x.get("category")==section),deficit)
    # Remainder is selected entirely by signal score under category and publisher caps.
    choose(candidates,TARGET-len(selected))
    # If source/category caps over-constrain the available pool, aim for 40-45
    # credible distinct headlines without fabricating or backdating anything.
    if len(selected)<MIN_TARGET:
        for item in candidates:
            if take(item,relax=True) and len(selected)>=TARGET:break

    selected.sort(key=lambda x:(-x.get("selection_score",0),x.get("id","")))
    # Only the actively selected 40-45 stories appear in homepage searches/cards.
    # Preserve real trend sidebar links only if the linked brief remains selected.
    ids={x["id"] for x in selected}
    for t in data.get("trends",[]):
        if t.get("related_id") not in ids:
            t.pop("related_id",None)
            t.pop("related_title",None)
            t.pop("related_source",None)
    data["items"]=selected
    data["curation"]={
        "target":TARGET,
        "count":len(selected),
        "algorithm":"Editorial signals: actual US search-trend linkage, source freshness, licensed full-text, category balance, headline specificity; not popularity or fact-checking",
        "category_counts":dict(categories),
        "full_text_count":sum(bool(x.get("full_html")) for x in selected),
        "trend_linked_count":sum(bool(x.get("trend_matches")) for x in selected),
        "candidate_count":len(source),
        "updated":now.isoformat(),
    }
    DATA.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("CURATED_USA_NEWS",json.dumps(data["curation"],ensure_ascii=False))
    if len(selected)<MIN_TARGET:
        print("WARNING: fewer than 40 usable headlines available; no filler articles invented")

if __name__=="__main__":main()
