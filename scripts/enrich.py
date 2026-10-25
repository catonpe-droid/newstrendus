"""Free, rights-aware article enrichment for NewsTrendus.

Only automatic full-text rights paths:
  1. NASA agency-authored news releases: public U.S. government text.
  2. KFF Health News original articles: their explicitly allowed republication,
     only when the RSS entry contains a complete body and an author.
Never copy CNN/BBC/AP/Reuters/The Conversation or VOA third-party text.
Original images are never pulled from publishers.
"""
from __future__ import annotations
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
import html as htmlmod
import json, re
from bs4 import BeautifulSoup, Tag
import bleach

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"news.json"
ALLOWED=["p","h2","h3","h4","ul","ol","li","strong","b","i","em","a","blockquote","br"]
KFF_TAGLINE=("KFF Health News is a national newsroom that produces in-depth journalism "
             "about health issues and is one of the core operating programs at KFF "
             "— the independent source for health policy research, polling, and journalism.")
TIMEOUT=15

def fetch(url):
    parsed=urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in (
         "www.nasa.gov","nasa.gov","kffhealthnews.org","www.kffhealthnews.org"):
        raise ValueError("Unapproved origin")
    req=Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; NewsTrendus/1.0; licensed RSS news syndication)",
                              "Accept":"text/html,application/rss+xml,text/xml"})
    with urlopen(req,timeout=TIMEOUT) as response:
        if urlparse(response.url).hostname not in (
            "www.nasa.gov","nasa.gov","kffhealthnews.org","www.kffhealthnews.org"):
            raise ValueError("Unexpected redirect")
        return response.read(1_750_000).decode("utf-8","replace")

def words(s):
    return len(re.findall(r"\b[\w'-]+\b",BeautifulSoup(s,"html.parser").get_text(" ",strip=True)))

def sanitize(fragment):
    soup=BeautifulSoup(fragment,"html.parser")
    # No third-party publisher photos, advertisements, embedded scripts or embeds.
    for el in soup.select("script,style,iframe,figure,img,video,audio,form,svg,aside,nav,.sharedaddy,.ad,.advertisement"):
        el.decompose()
    # Apply safe formatting, keep every non-image hyperlink.
    safe=bleach.clean(str(soup),tags=ALLOWED,attributes={"a":["href","title"]},
                      protocols=["http","https"],strip=True)
    return safe.strip()

def nasa_body(article):
    page=BeautifulSoup(fetch(article["url"]),"html.parser")
    candidates=page.select(".entry-content, .wp-block-post-content, .article-content, article, main")
    choices=[]
    for node in candidates:
        for extra in node.select("header,footer,nav,aside,.related-posts,.article-footer,.social-share,.related-content"):
            extra.decompose()
        tags=node.find_all(["p","h2","h3","ul","ol","blockquote"])
        # Avoid duplicating list element nested inside another selected tag
        selected=[]
        for tag in tags:
            if tag.find_parent(["ul","ol","blockquote"]) and tag.name=="p": continue
            txt=tag.get_text(" ",strip=True)
            if len(txt)>=25 or tag.name in ("h2","h3"):
                selected.append(str(tag))
        body=sanitize("\n".join(selected))
        cnt=words(body)
        if cnt>=260 and cnt<=9000:
            choices.append((cnt,body))
    if not choices: return ""
    # Most complete plausible article body; avoid entire site chrome >9K words.
    body=max(choices,key=lambda v:v[0])[1]
    return body

def get_kff_encoded():
    root=ET.fromstring(fetch("https://kffhealthnews.org/feed/"))
    out={}
    for item in root.findall(".//item")[:25]:
        link=(item.findtext("link") or "").strip()
        creator=(item.findtext("{http://purl.org/dc/elements/1.1/}creator") or "").strip()
        text=item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or ""
        if link and text:out[link.split("?")[0].rstrip("/")]=(creator,text)
    return out

def kff_body(article,encoded):
    creator,raw=encoded
    if len(raw)<2600 or not creator: return ""
    soup=BeautifulSoup(raw,"html.parser")
    plain=soup.get_text(" ",strip=True)
    if re.search(r"all\s+rights\s+reserved",plain,re.I):
        return ""
    # Avoid automatic cartoons/partner stories, third-party syndicated writing.
    if article["url"].find("/multimedia/")>=0: return ""
    if re.search(r"\b(?:The Associated Press|AP News|Reuters|AFP)\b",creator,re.I):return ""
    body=sanitize(raw)
    if not 500<=words(body)<=6500:return ""
    # Exclude malformed content. Preserve all publisher links inside remaining copy.
    link_count=len(BeautifulSoup(raw,"html.parser").find_all("a",href=True))
    safe_links=len(BeautifulSoup(body,"html.parser").find_all("a",href=True))
    if safe_links<link_count:return ""
    return body

def kff_attribution(article):
    author=article.get("author","").strip()
    return "By "+author+" — KFF Health News" if author else "KFF Health News"

def article_score(article,trends):
    blob=((article.get("title") or "")+" "+(article.get("summary") or "")).lower()
    if not blob.strip():return 0
    matches=[]
    for t in trends:
        phrase=(t.get("title") or "").lower().strip()
        if len(phrase)>2 and phrase in blob:matches.append(t.get("title"))
    article["trend_matches"]=matches[:3]
    return 20*len(matches)

def main():
    d=json.loads(DATA.read_text(encoding="utf-8"))
    items=d.get("items",[])
    nasa=[x for x in items if urlparse(x.get("url","")).hostname in ("nasa.gov","www.nasa.gov")
          and x.get("url","").find("/news-release/")>=0]
    kff=[x for x in items if urlparse(x.get("url","")).hostname in ("kffhealthnews.org","www.kffhealthnews.org")]
    # Enrichment is deliberately limited rather than bulk mirroring: at most
    # 3 NASA and 2 KFF complete new stories per refresh (cache is retained).
    result={"nasa_candidates":len(nasa),"kff_candidates":len(kff),"nasa_added":0,"kff_added":0}
    for item in nasa:
        if item.get("full_html"):continue
        if result["nasa_added"]>=3:break
        try:
            body=nasa_body(item)
            if not body:continue
            item.update(full_html=body,license_type="NASA government release",
                        full_source="NASA",rights_notice="NASA original release; NASA credited. External images excluded.")
            result["nasa_added"]+=1
        except Exception as e:print("NASA enrichment skipped:",str(e)[:120])
    try:encoded=get_kff_encoded()
    except Exception as e:
        encoded={}
        print("KFF RSS full body not available:",str(e)[:130])
    for item in kff:
        if item.get("full_html"):continue
        if result["kff_added"]>=2:break
        try:
            key=item["url"].split("?")[0].rstrip("/")
            pair=encoded.get(key)
            if not pair:continue
            if not item.get("author"):item["author"]=pair[0]
            body=kff_body(item,pair)
            if not body:continue
            item.update(full_html=body,license_type="KFF Health News licensed republication",
                        full_source="KFF Health News",
                        rights_notice="Original KFF Health News article republished intact with byline, original links and attribution. Photos excluded.")
            result["kff_added"]+=1
        except Exception as e:print("KFF item skipped:",str(e)[:120])
    for x in items:
        x["trend_score"]=article_score(x,d.get("trends",[]))
    # Use topical relevance and freshness, not made-up search-volume claims.
    def rank(x):
        try:
            dt=datetime.fromisoformat(x.get("date","") or "")
            hours=max(0,(datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()/3600)
        except Exception:hours=240
        relevance=min(20,x.get("trend_score",0))
        licensed=3 if x.get("full_html") else 0
        us=1 if x.get("category") in ("US","Gaming","Health","Science","Sports") else 0
        return relevance+licensed+us+max(0,10-hours/12)
    d["items"]=sorted(items,key=rank,reverse=True)
    d["enrichment_updated"]=datetime.now(timezone.utc).isoformat()
    d["enrichment_summary"]=result
    DATA.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
    print("LICENSED_FULL_TEXT_SUMMARY",json.dumps(result),
          "total_full",sum(bool(x.get("full_html")) for x in items),
          "exact_us_trend_matches",sum(bool(x.get("trend_matches")) for x in items))

if __name__=="__main__":main()
