#!/usr/bin/env python3
"""Daily self-check of NewsTrendus.com production signals.

Reads local published artifacts, validates critical SEO and tracking, and
optionally checks public URL reachability. Does not invent traffic, access
unconnected GA4/Search Console accounts, auto-generate filler content or alter
publisher copyright rules. Runs read-only in daily-health.yml.
"""
from __future__ import annotations
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from collections import Counter
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET
import json
import os
import sys
import re

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"daily-health.json"
TODAY=datetime.now(timezone.utc)
BASE="https://newstrendus.com"
ID="G-10SMK0DD8L"
FULL_RIGHTS={"NASA government release","KFF Health News licensed republication"}
issues=[]

def check(ok,category,message,critical=False):
    if not ok:
        issues.append({"severity":"error" if critical else "warning","category":category,"message":message})
    return ok

def age_hours(value):
    if not value:return None
    try:
        d=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return round((TODAY-d.astimezone(timezone.utc)).total_seconds()/3600,1)
    except (TypeError,ValueError,OverflowError):
        return None

def read_json(file):
    try:return json.loads((ROOT/file).read_text(encoding="utf-8"))
    except Exception as exc:
        check(False,file,"JSON missing or invalid: "+str(exc)[:150],True)
        return {}

def probe(url):
    try:
        req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; NewsTrendusDailyAudit/1.0)",
                                 "Accept":"text/html,text/plain,application/xml,*/*"})
        with urlopen(req,timeout=9) as response:
            return {"url":url,"http_status":response.status,"bytes_sampled":len(response.read(6000)),"redirect":response.url}
    except (HTTPError,URLError,TimeoutError,ValueError,OSError) as err:
        check(False,"public_url",f"Could not verify {url}: {str(err)[:150]} (may be network or bot protection)")
        return {"url":url,"error":str(err)[:180]}

def main():
    report={"checked_at_utc":TODAY.isoformat(),"site":BASE,"checks":{},"issues":[]}
    news=read_json("news.json")
    items=news.get("items",[])
    if not isinstance(items,list):items=[]
    count=len(items)
    fresh=age_hours(news.get("updated"))
    # news.json is a legacy, read-only RSS discovery snapshot. RSS autoblogging is disabled.
    # Do not fail health checks because the retired feed has stopped refreshing.
    unique=len({x.get("url") for x in items if isinstance(x,dict)})
    check(unique==count,"news",f"Only {unique} unique story URLs among {count} items")
    full=[x for x in items if isinstance(x,dict) and x.get("full_html")]
    invalid=[x.get("title","?")[:75] for x in full if x.get("license_type") not in FULL_RIGHTS]
    check(not invalid,"copyright","Full-text articles have unapproved source rights: "+str(invalid),True)
    trending=sum(bool(x.get("trend_seed")) for x in items if isinstance(x,dict))
    source_counts=Counter(x.get("source","unknown") for x in items if isinstance(x,dict))
    category_counts=Counter(x.get("category","unknown") for x in items if isinstance(x,dict))
    report["checks"]["news"]={"curated_count":count,"age_hours":fresh,"full_articles":len(full),
        "trend_linked_count":trending,"categories":dict(category_counts),
        "top_sources":source_counts.most_common(6)}

    elections=read_json("elections.json")
    election_age=age_hours(elections.get("updated"))
    # Elections feed is not an active scheduled publisher; report its age, not an SLA.
    jurisdiction_count=len(elections.get("jurisdictions",[]))
    check(jurisdiction_count==51,"elections",f"Expected 50 states + DC; found {jurisdiction_count}")
    report["checks"]["elections"]={"count":len(elections.get("items",[])),
       "feed_age_hours":election_age,"jurisdictions":jurisdiction_count}

    try:
        xml=(ROOT/"sitemap.xml").read_text(encoding="utf-8")
        tree=ET.fromstring(xml)
        sitemap_urls=[x.text for x in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        check(len(sitemap_urls)>=25,"seo",f"Sitemap has {len(sitemap_urls)} URLs; expected >=25",True)
        check(len(set(sitemap_urls))==len(sitemap_urls),"seo","Duplicate URLs in sitemap",True)
        check(all(u.startswith(BASE+"/") for u in sitemap_urls),"seo","External/incorrect domain URLs in sitemap",True)
    except Exception as err:
        sitemap_urls=[]
        check(False,"seo","Sitemap invalid: "+str(err),True)
    robots=(ROOT/"robots.txt").read_text(encoding="utf-8")
    check("Sitemap: "+BASE+"/sitemap.xml" in robots,"seo","Robots sitemap declaration missing",True)
    check("Disallow: /" not in robots,"seo","Site-wide robots blocking Google",True)
    # Four-hour Google Trends publisher creates original static articles, not RSS posts.
    catalog=read_json("editorial-news.json")
    editorial=catalog.get("items",[])
    if not isinstance(editorial,list):
        editorial=[]
    article_urls=[x.get("url","") for x in editorial if isinstance(x,dict)]
    categories=Counter(x.get("category","unknown") for x in editorial if isinstance(x,dict))
    check(bool(editorial),"editorial","No published editorial article catalogue entries",True)
    check(len(article_urls)==len(set(article_urls)),"editorial","Duplicate article URLs in editorial catalogue",True)
    missing=[url for url in article_urls if url not in sitemap_urls]
    check(not missing,"seo","Editorial article URLs missing from sitemap: "+", ".join(missing[:5]),True)
    bad_categories=[x.get("page_url","?") for x in editorial if isinstance(x,dict)
                    and x.get("category") not in {"US","World","Technology","Gaming","Business","Sports","Health","Trending","Science","Entertainment"}]
    check(not bad_categories,"editorial","Unknown editorial categories: "+", ".join(bad_categories[:5]),True)
    newest=max((x.get("date","") for x in editorial if isinstance(x,dict)),default="")
    latest_age=age_hours(newest)
    check(latest_age is not None and -1<=latest_age<=12,"editorial",
          f"Latest original article is {latest_age}h old; verify four-hour Trends publisher")
    css=(ROOT/"site.css").read_text(encoding="utf-8")
    check("aspect-ratio:16/9" in css and "object-fit:cover" in css,
          "editorial","16:9 cropped photo CSS missing",True)
    try:
        image_gate=subprocess.run([sys.executable,"scripts/validate_editorial_images.py"],
                cwd=ROOT,capture_output=True,text=True,timeout=35,check=False)
        image_gate_ok=image_gate.returncode==0
        image_gate_detail=(image_gate.stdout+"\n"+image_gate.stderr).strip()[-900:]
    except (OSError,subprocess.TimeoutExpired) as exc:
        image_gate_ok=False
        image_gate_detail=str(exc)
    check(image_gate_ok,"editorial","External-photo / credit validation failed: "+image_gate_detail,True)
    report["checks"]["editorial"]={"published_articles":len(editorial),
        "latest_article_age_hours":latest_age,"categories":dict(categories),
        "articles_missing_from_sitemap":len(missing),"photo_policy_pass":image_gate_ok}

    html_paths=[p for p in ROOT.rglob("*.html") if ".git" not in p.parts]
    untracked=[]
    duplicates=[]
    for p in html_paths:
        body=p.read_text(encoding="utf-8")
        hits=body.count("https://www.googletagmanager.com/gtag/js?id="+ID)
        if hits==0:untracked.append(p.relative_to(ROOT).as_posix())
        elif hits>1:duplicates.append(p.relative_to(ROOT).as_posix())
    check(not untracked,"analytics","GA4 missing on pages: "+", ".join(untracked[:10]),True)
    check(not duplicates,"analytics","Duplicate GA4 tags on pages: "+", ".join(duplicates[:10]),True)
    adstxt=(ROOT/"ads.txt").read_text(encoding="utf-8").strip()
    check("pub-2124953371207111" in adstxt,"adsense","Publisher entry missing in ads.txt",True)
    homepage=(ROOT/"index.html").read_text(encoding="utf-8")
    check('<link rel="canonical" href="'+BASE+'/"' in homepage,
          "seo","Homepage canonical missing/incorrect",True)
    check("noindex" not in re.sub(r"<script\b[^>]*>.*?</script>","",homepage,flags=re.I|re.S).lower(),
          "seo","Homepage has unexpected noindex",True)
    report["checks"]["seo"]={"sitemap_urls":len(sitemap_urls),"html_pages":len(html_paths),
            "untracked_pages":len(untracked),"duplicate_tracking":len(duplicates),
            "ads_txt_present":True}

    report["checks"]["public_urls"]=[probe(BASE+suffix) for suffix in
        ("/","/robots.txt","/sitemap.xml","/ads.txt")]
    report["issues"]=issues
    report["status"]="ALERT" if any(x["severity"]=="error" for x in issues) else ("WARNING" if issues else "OK")
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("DAILY HEALTH SUMMARY",json.dumps({
        "status":report["status"],"legacy_news":count,"legacy_news_age_hours":fresh,
        "editorial_articles":len(editorial),"photo_policy_pass":image_gate_ok,"sitemap_urls":len(sitemap_urls),
        "html_pages":len(html_paths),"issues":len(issues)},ensure_ascii=False))
    for x in issues:print(f"{x['severity'].upper()}: [{x['category']}] {x['message']}")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as out:
            out.write("# NewsTrendus — Daily Site Health\n\n")
            out.write(f"**Status:** {report['status']} · **Checked UTC:** {TODAY.isoformat()}\n\n")
            out.write(f"Original articles: **{len(editorial)}**, latest age: **{latest_age}h**, photo gate: **{image_gate_ok}**, sitemap URLs: **{len(sitemap_urls)}**, GA4 HTML pages: **{len(html_paths)}**. Legacy RSS snapshot: **{count}** items (not auto-published).\n\n")
            if issues:
                out.write("## Issues\n\n")
                for x in issues:out.write(f"- **{x['severity']} / {x['category']}**: {x['message']}\n")
            else:out.write("No issues detected by these automated checks.\n")
            out.write("\nTraffic, search impressions, earnings, AdSense approval and ranking are **not measured** by this script.\n")
    if report["status"]=="ALERT":
        # Fail daily-only audit to surface alerts in GitHub Actions notifications.
        sys.exit(1)

if __name__=="__main__":main()
