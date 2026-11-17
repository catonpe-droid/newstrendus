#!/usr/bin/env python3
"""NewsTrendus worldwide sports fixtures: source-attributed, cached, static, SEO-safe.
TheSportsDB V1 free results are partial (limited rows/request), NOT a complete world calendar.
Never invent fixtures, results, broadcasts, or assert live-score coverage.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json, os, re, time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sports"
OUT.mkdir(exist_ok=True)
SITE = "https://newstrendus.com"
API = "https://www.thesportsdb.com/api/v1/json/123/eventsday.php"
SPORTS = [
 ("soccer","Football / Soccer","Soccer","Club leagues, international football and major tournaments","https://www.fifa.com/"),
 ("basketball","Basketball / NBA","Basketball","NBA, WNBA and international basketball competition","https://www.nba.com/schedule"),
 ("american-football","American Football / NFL","American Football","NFL and other American football fixtures","https://www.nfl.com/schedules/"),
 ("ice-hockey","Ice Hockey / NHL","Ice Hockey","NHL and international ice hockey events","https://www.nhl.com/"),
 ("baseball","Baseball / MLB","Baseball","MLB and international baseball games","https://www.mlb.com/schedule"),
 ("cricket","Cricket","Cricket","International cricket and leading domestic competitions","https://www.icc-cricket.com/"),
 ("tennis","Tennis / ATP / WTA","Tennis","Men's and women's professional tennis tournaments","https://www.atptour.com/"),
 ("motorsport","Formula 1 / Motorsport","Motorsport","Formula 1 and other professional motorsport events","https://www.formula1.com/"),
 ("golf","Golf","Golf","Professional golf tours and championship dates","https://www.pgatour.com/"),
 ("rugby","Rugby","Rugby","Rugby union, rugby league and international fixtures","https://www.world.rugby/"),
 ("mma","MMA / UFC","MMA","Mixed martial arts and upcoming fight cards","https://www.ufc.com/"),
 ("boxing","Boxing","Boxing","Professional boxing and championship bouts","https://www.wbcboxing.com/"),
 ("badminton","Badminton","Badminton","International badminton fixtures and tournaments","https://bwfbadminton.com/"),
 ("volleyball","Volleyball","Volleyball","International and national volleyball competitions","https://www.fivb.com/"),
 ("cycling","Cycling","Cycling","Road cycling and international race events","https://www.uci.org/"),
 ("athletics","Athletics / Track & Field","Athletics","Track and field meetings and championship calendars","https://worldathletics.org/"),
 ("handball","Handball","Handball","European and international handball competitions","https://www.ihf.info/"),
 ("table-tennis","Table Tennis","Table Tennis","Professional table tennis events","https://www.ittf.com/"),
 ("snooker","Snooker","Snooker","Professional snooker tournament fixtures","https://www.wst.tv/"),
 ("darts","Darts","Darts","Professional darts competitions","https://www.pdc.tv/"),
 ("esports","Esports","Esports","Professional gaming and esports tournaments","https://www.iesf.org/"),
 ("field-hockey","Field Hockey","Field Hockey","International field hockey tournaments","https://www.fih.hockey/"),
 ("australian-football","Australian Rules Football","Australian Football","Australian rules football schedules","https://www.afl.com.au/"),
 ("winter-sports","Winter Sports","Winter Sports","International winter sport events","https://www.olympics.com/"),
]
BY_API={x[2].lower():x[0] for x in SPORTS}
PRIORITY={"soccer","basketball","american-football","ice-hockey","baseball","cricket","tennis","motorsport"}
COUNTRIES=[
 ("usa","United States",("united states","usa","united states of america")),
 ("canada","Canada",("canada",)),
 ("uk","United Kingdom",("united kingdom","england","scotland","wales","northern ireland")),
 ("india","India",("india",)),
 ("australia","Australia",("australia",)),
 ("brazil","Brazil",("brazil",)),
 ("japan","Japan",("japan",)),
 ("germany","Germany",("germany",)),
 ("france","France",("france",)),
 ("spain","Spain",("spain",)),
 ("italy","Italy",("italy",)),
 ("south-africa","South Africa",("south africa",)),
]
CSS_LINK='<link rel="stylesheet" href="../site.css"><link rel="stylesheet" href="sports.css"><link rel="icon" type="image/svg+xml" href="../assets/us-mark.svg">'
def h(x):return escape(str(x or ""),quote=True)
def iso(t):return t.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def stamp(value):
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError,TypeError,AttributeError):return None

def request_day(day,sport):
    query=urlencode({"d":day,"s":sport})
    req=Request(API+"?"+query,headers={"User-Agent":"NewsTrendusSportsCalendar/1.0 (+https://newstrendus.com/contact.html)","Accept":"application/json"})
    with urlopen(req,timeout=13) as res:
        if res.status!=200:raise OSError(f"HTTP {res.status}")
        data=json.load(res)
    if not isinstance(data,dict):raise ValueError("Unexpected API payload")
    return data.get("events") or []

def collect(now):
    byid={}
    success=0
    failed=0
    today=now.date()
    # TheSportsDB shared free tier has 30 requests/minute and small result limits.
    # One date for every supported sport, and next four days for eight priority sports.
    jobs=[(today,s) for s in SPORTS]
    jobs += [(today+timedelta(days=offset),s) for offset in range(1,5) for s in SPORTS if s[0] in PRIORITY]
    for n,(day,sport) in enumerate(jobs):
        slug,name,api_sport,_,_=sport
        try:
            events=request_day(day.isoformat(),api_sport)
            success+=1
            for x in events:
                if not isinstance(x,dict):continue
                name_event=(x.get("strEvent") or "").strip()
                date_event=(x.get("dateEvent") or "").strip()
                sid=str(x.get("idEvent") or "").strip()
                if not name_event or not re.match(r"^\d{4}-\d{2}-\d{2}$",date_event):continue
                if len(name_event)>190:continue
                event_sport=(x.get("strSport") or api_sport).strip().lower()
                if event_sport not in BY_API or BY_API[event_sport]!=slug:continue
                raw_ts=(x.get("strTimestamp") or "").strip()
                dt=stamp(raw_ts)
                # Unspecified timezone is not silently interpreted as UTC.
                exact=bool(re.search(r"(Z|[+-]\d\d:\d\d)$",raw_ts))
                when=iso(dt) if dt and exact else ""
                # Discard dates outside the requested short calendar window.
                if date_event < today.isoformat() or date_event > (today+timedelta(days=5)).isoformat():continue
                key=sid or slug+":"+date_event+":"+name_event
                byid[key]=dict(id=key[:90],sport=slug,name=name_event,league=(x.get("strLeague") or "Competition").strip()[:100],
                    country=(x.get("strCountry") or "").strip()[:70],venue=(x.get("strVenue") or "").strip()[:100],
                    date=date_event,utc=when,source="TheSportsDB")
        except (ValueError,TimeoutError,OSError) as err:
            failed+=1
            print(f"SPORTS SOURCE WARNING {day} {slug}: {str(err)[:120]}")
            if success==0 and failed>=3:
                break
        # Stay under the 30 requests/minute limit including shared-key contention.
        if n+1<len(jobs):time.sleep(2.15)
    return sorted(byid.values(),key=lambda x:(x["utc"] or x["date"],x["sport"],x["name"])),success

def load(now):
    cache=OUT/"fixtures.json"
    previous={}
    if cache.exists():
        try:previous=json.loads(cache.read_text(encoding="utf-8"))
        except (ValueError,OSError):pass
    updated=stamp(previous.get("updated_at",""))
    force=os.environ.get("SPORTS_FORCE_REFRESH")=="1"
    if updated and not force and (now-updated).total_seconds()<18*3600:
        print("SPORTS using recent verified cache")
        return previous
    try:
        events,count=collect(now)
    except Exception as exc:
        print("SPORTS fetch unavailable:",str(exc)[:200])
        events,count=[],0
    if count==0:
        # Do not falsely change 'last checked' or erase valid previously fetched fixtures.
        print("SPORTS WARNING: No successful source calls; retaining prior verified snapshot")
        return previous if previous.get("updated_at") else {"updated_at":"","events":[],"source":"TheSportsDB (limited free feed)"}
    result={"updated_at":iso(now),"events":events,"source":"TheSportsDB (limited free feed)","source_url":"https://www.thesportsdb.com/","source_note":"Selected fixtures, not an exhaustive calendar or live scores; times may change."}
    cache.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SPORTS updated",len(events),"fixtures from",count,"successful daily source calls")
    return result

def frame(title,desc,canonical,body,index=True):
    robots="index,follow,max-image-preview:large" if index else "noindex,follow"
    schema={"@context":"https://schema.org","@type":"CollectionPage","name":title,"url":canonical,
            "description":desc,"inLanguage":"en-US","publisher":{"@type":"Organization","name":"NewsTrendus","url":SITE}}
    schema_html=json.dumps(schema,ensure_ascii=True).replace("<","\\u003c")
    return f'''<!doctype html>
<html lang="en-US"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="{robots}">
<title>{h(title)}</title><meta name="description" content="{h(desc)}">
<link rel="canonical" href="{h(canonical)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="NewsTrendus">
<meta property="og:title" content="{h(title)}"><meta property="og:description" content="{h(desc)}">
<meta property="og:url" content="{h(canonical)}"><meta name="twitter:card" content="summary">
{CSS_LINK}
<script type="application/ld+json">{schema_html}</script>
<script defer src="sports.js"></script></head><body>
<div class="topline"><div class="container">NewsTrendus · Worldwide sports, with a US and Canada focus</div></div>
<header class="masthead"><div class="container masthead-inner"><a class="brand" href="../index.html">News<span>Trendus</span><small>.com</small></a><span class="sport-edition">GLOBAL SPORTS CALENDAR</span></div></header>
<div class="navshell"><nav class="container nav" aria-label="Site navigation">
<a href="../index.html">Home</a><a href="index.html">World Sports Schedule</a><a href="../articles/index.html">Latest News</a>
<a href="../contact.html">Contact</a></nav></div>
{body}
<footer class="sport-footer"><div class="container">
<p>NewsTrendus publishes a curated discovery calendar, not an official schedule, real-time score service or complete database.
Verify times, changes and tickets with the relevant organizer. Source: <a href="https://www.thesportsdb.com/" target="_blank" rel="noopener noreferrer">TheSportsDB</a> (free-tier partial fixtures); official league links are provided for fuller coverage.</p>
<p><a href="../about.html">About</a> · <a href="../editorial.html">Editorial standards</a> · <a href="../privacy.html">Privacy</a> · <a href="../contact.html">Contact</a></p></div></footer>
</body></html>
'''

def nav():
    return '<nav class="sport-pills" aria-label="Browse sports">' + ''.join(
        f'<a href="{h(s)}.html">{h(n)}</a>' for s,n,_,_,_ in SPORTS
    ) + '</nav>'

def regions():
    return '<div class="region-links"><strong>Explore by country:</strong> '+" · ".join(
        f'<a href="{h(slug)}-schedule.html">{h(name)}</a>' for slug,name,_ in COUNTRIES
    )+'</div>'

def toolbar():
    return '''<div class="sport-controls">
<label>Show times in <select id="timeZone">
<option value="America/New_York">USA / Canada · Eastern</option>
<option value="America/Los_Angeles">USA / Canada · Pacific</option>
<option value="America/Chicago">USA / Canada · Central</option>
<option value="America/Toronto">Canada · Toronto</option>
<option value="Europe/London">UK · London</option>
<option value="Europe/Paris">Europe · Paris</option>
<option value="Asia/Kolkata">India · IST</option>
<option value="Australia/Sydney">Australia · Sydney</option>
<option value="Asia/Tokyo">Japan · Tokyo</option>
<option value="America/Sao_Paulo">Brazil · São Paulo</option>
<option value="UTC">UTC</option>
</select></label>
<label>Find team / league <input id="fixtureSearch" type="search" placeholder="Search available fixtures" aria-label="Search fixtures"></label>
</div>'''

def row(e):
    txt=e["name"]+" "+e["league"]+" "+e["country"]
    when=e.get("utc","")
    label=e["date"]+" · time not confirmed" if not when else e["date"]+" · UTC"
    tags=(f'<span class="sport-country">{h(e["country"])}</span>' if e["country"] else "")
    return (f'<article class="fixture" data-filter="{h(txt.lower())}" data-date="{h(e["date"])}">'
            f'<div class="fixture-badge">{h(e["sport"].replace("-"," ").title())}</div>'
            f'<div class="fixture-main"><h3>{h(e["name"])}</h3><p>{h(e["league"])} {tags}</p></div>'
            f'<time class="fixture-time" datetime="{h(when)}" data-fallback="{h(label)}">{h(label)}</time></article>')

def section(items,empty):
    if not items:return '<div class="sport-empty">'+h(empty)+'</div>'
    return '<div class="fixture-list">'+''.join(row(e) for e in items[:180])+'</div><p class="sport-nomatch" hidden>No matches fit your search within the currently listed fixtures.</p>'

def build(data):
    events=data.get("events",[])
    checked=data.get("updated_at","")
    updated=h(checked[:16].replace("T"," ")+" UTC" if checked else "not yet verified")
    today=datetime.now(timezone.utc).date()
    fresh=[e for e in events if e.get("date","")>=today.isoformat()]
    intro=f'''<section class="sport-hero"><div class="container"><div class="sport-kicker">NewsTrendus / WORLD SPORTS</div>
<h1>World Sports Schedule: Today & Upcoming Matches</h1>
<p>Discover selected fixtures across major sports and countries. Built for fans in the USA, Canada, UK, India, Australia and worldwide. Check local match times and open official schedules for full coverage.</p>
<div class="sport-metrics"><span>24 sports covered in navigation</span><span>Selected events · next 5 days</span><span>Last verified: {updated}</span></div>
</div></section>'''
    hub=('<main class="container sport-main">'+nav()+regions()+toolbar()+
      '<section class="sport-panel"><h2>Upcoming sports fixtures and games</h2>'
      '<p class="sport-note">Partial, third-party fixture selection. Not all leagues, matches or dates are listed; this is not a live-score service. Please confirm with official organizers.</p>'+
      section(fresh,"The source has not returned verified upcoming fixtures. Use the official sport and league links below, and check back after the next update.")+
      '</section><section class="sport-panel"><h2>Official sports schedules and competitions</h2><div class="sport-grid">'+
      ''.join(f'<article><h3><a href="{h(slug)}.html">{h(name)}</a></h3><p>{h(context)}.</p><a href="{h(url)}" target="_blank" rel="noopener noreferrer">Official sport website</a></article>' for slug,name,_,context,url in SPORTS)+
      '</div></section><section class="sport-panel sport-faq"><h2>Sports schedule FAQ</h2><h3>Does this include all matches worldwide?</h3><p>No. The free data provider returns a small selection of fixtures per request; the official sport links are the best source for complete schedules.</p><h3>Are scores shown live?</h3><p>No. This page is refreshed periodically, not during every match. Use the official live coverage for real-time scores.</p><h3>Which time zone is used?</h3><p>Times with verified UTC start times can be converted to your chosen zone. A match without a verified UTC start is shown as time not confirmed.</p></section></main>')
    (OUT/"index.html").write_text(frame("World Sports Schedule Today & Upcoming Games | NewsTrendus",
     "World sports schedule with selected football, NFL, NBA, NHL, MLB, cricket, tennis and F1 fixtures. Check local times for USA, Canada, UK and worldwide.",SITE+"/sports/index.html",intro+hub),encoding="utf-8")
    for slug,name,api_sport,context,official in SPORTS:
        matching=[e for e in fresh if e.get("sport")==slug]
        d=f"{name} Schedule: Upcoming Fixtures & Times | NewsTrendus"
        desc=f"Explore selected upcoming {name.lower()} fixtures, match dates, leagues and local start times for fans in the USA, Canada and worldwide. Verify the complete calendar at official sources."
        body=(f'<main class="container sport-main"><div class="breadcrumbs"><a href="index.html">World sports</a> / {h(name)}</div>'
          f'<div class="sport-heading"><span class="sport-kicker">{h(name)} · Fixtures</span><h1>{h(name)} Schedule & Upcoming Events</h1>'
          f'<p>{h(context)}. Times are localized only when a source supplies a verified UTC kickoff or start time.</p>'
          f'<p class="sport-note">Last source check: {updated}. This feed is a selected sample, not a complete fixture list.</p></div>'
          +toolbar()+'<section class="sport-panel"><h2>Selected upcoming events</h2>'+
          section(matching,"No verified upcoming events for this sport were returned by the limited source feed. This does not mean no games are scheduled.")+
          f'<p class="sport-official">For the complete and latest schedule: <a href="{h(official)}" target="_blank" rel="noopener noreferrer">Visit the official {h(name)} competition site</a>.</p></section>'
          '<section class="sport-panel"><h2>Other sports and top countries</h2>'+nav()+regions()+'</section></main>')
        (OUT/(slug+".html")).write_text(frame(d,desc,SITE+"/sports/"+slug+".html",body,index=bool(matching)),encoding="utf-8")
    for slug,name,country_names in COUNTRIES:
        matching=[e for e in fresh if e.get("country","").casefold() in country_names]
        title=f"{name} Sports Schedule Today: Selected Games | NewsTrendus"
        desc=f"Browse selected upcoming sports fixtures in {name}, leagues and match start times. Find official sports calendar resources and convert times to your local zone."
        body=(f'<main class="container sport-main"><div class="breadcrumbs"><a href="index.html">World sports</a> / {h(name)}</div>'
              f'<div class="sport-heading"><span class="sport-kicker">World sports · {h(name)}</span>'
              f'<h1>{h(name)} Sports Schedule and Upcoming Games</h1>'
              f'<p>Browse selected fixtures attributed to leagues based in {h(name)}. International games featuring {h(name)} teams may be hosted elsewhere and may not appear here.</p>'
              f'<p class="sport-note">Limited, source-verified selection; last checked {updated}. For complete coverage, consult individual leagues.</p></div>'
              +toolbar()+'<section class="sport-panel"><h2>Selected fixtures in '+h(name)+'</h2>'+
              section(matching,"No verified fixtures for this country were returned by the limited data source. This is not confirmation that no games are taking place.")+
              '</section><section class="sport-panel"><h2>Browse more sports</h2>'+nav()+regions()+'</section></main>')
        (OUT/(slug+"-schedule.html")).write_text(frame(title,desc,SITE+"/sports/"+slug+"-schedule.html",body,index=bool(matching)),encoding="utf-8")
    print("SPORTS generated",len(SPORTS),"sport pages,",len(COUNTRIES),"country pages, hub; selected",len(fresh),"future fixtures")

def main():
    now=datetime.now(timezone.utc)
    data=load(now)
    build(data)
if __name__=="__main__":main()
