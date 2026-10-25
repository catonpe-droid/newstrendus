"""Local and state elections headlines for NewsTrendus; all 50 states + DC.
Free Google News RSS search is not an official or guaranteed API.
No predictions, fabricated outcomes, party preference or voter-profiling.
New feed searches rotate across state groups to avoid excessive requests.
"""
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen,Request
from xml.etree import ElementTree as ET
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"elections.json"
STATES=[
("AL","Alabama"),("AK","Alaska"),("AZ","Arizona"),("AR","Arkansas"),("CA","California"),
("CO","Colorado"),("CT","Connecticut"),("DE","Delaware"),("DC","District of Columbia"),
("FL","Florida"),("GA","Georgia"),("HI","Hawaii"),("ID","Idaho"),("IL","Illinois"),
("IN","Indiana"),("IA","Iowa"),("KS","Kansas"),("KY","Kentucky"),("LA","Louisiana"),
("ME","Maine"),("MD","Maryland"),("MA","Massachusetts"),("MI","Michigan"),("MN","Minnesota"),
("MS","Mississippi"),("MO","Missouri"),("MT","Montana"),("NE","Nebraska"),("NV","Nevada"),
("NH","New Hampshire"),("NJ","New Jersey"),("NM","New Mexico"),("NY","New York"),
("NC","North Carolina"),("ND","North Dakota"),("OH","Ohio"),("OK","Oklahoma"),("OR","Oregon"),
("PA","Pennsylvania"),("RI","Rhode Island"),("SC","South Carolina"),("SD","South Dakota"),
("TN","Tennessee"),("TX","Texas"),("UT","Utah"),("VT","Vermont"),("VA","Virginia"),
("WA","Washington"),("WV","West Virginia"),("WI","Wisconsin"),("WY","Wyoming")]
TOPICS=["election","ballot","primary","voter","council","school board","mayor","governor",
        "county commission","district","statehouse","legislature","recall","campaign"]
def rss(query):
    url="https://news.google.com/rss/search?q="+quote(query)+"&hl=en-US&gl=US&ceid=US:en"
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; NewsTrendusLocalPolitics/1.0)"})
    with urlopen(req,timeout=16) as r: return ET.fromstring(r.read(1_200_000))
def valid_title(t):
    return len(t)>26 and len(t)<240 and any(w in t.lower() for w in TOPICS)
def get_items(query,state_name,state_code,limit=5):
    output=[]
    try:
        root=rss(query)
        for item in root.findall(".//item")[:30]:
            title=re.sub(r"\s+"," ",item.findtext("title") or "").strip()
            src=item.find("source")
            publisher=(src.text or "").strip() if src is not None else ""
            link=item.findtext("link") or ""
            if not valid_title(title) or not link.startswith("https://"):continue
            if publisher.lower().endswith((".ca"," canada")) or "countylive.ca" in title.casefold():continue
            if publisher.lower() in ("multistate",):continue
            if "ontario election" in title.casefold() or "canadian election" in title.casefold():continue
            if state_code and not publisher:continue
            date=item.findtext("pubDate")
            try:iso=parsedate_to_datetime(date).astimezone(timezone.utc).isoformat()
            except Exception:continue
            if datetime.now(timezone.utc)-datetime.fromisoformat(iso)>timedelta(days=7):continue
            output.append({"id":hashlib.sha256(link.encode()).hexdigest()[:16],
              "title":title,"source":publisher or "Publisher via Google News",
              "url":link,"date":iso,"state":state_code,"state_name":state_name,
              "type":"Local elections / government","full_text":False})
            if len(output)>=limit:break
    except Exception as exc:print("ELECTION_FEED_UNAVAILABLE",state_name,str(exc)[:110])
    return output
def main():
    try:old=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    except Exception:old={}
    saved=old.get("items",[])
    now=datetime.now(timezone.utc)
    # Change the state subset each scheduled run. Every 3 hours covers 51 jurisdictions.
    rotation=int(now.timestamp()//1800)%6
    group=[p for i,p in enumerate(STATES) if i%6==rotation]
    fresh=[]
    for code,name in group:
        query='"'+name+'" ("local election" OR "school board election" OR "city council" OR "ballot measure" OR "governor race") when:7d'
        fresh.extend(get_items(query,name,code,5))
    # National reporting keeps election section broadly useful between rotations.
    fresh.extend(get_items('"US midterm election" OR "2026 US state elections" OR "US school board elections" when:3d',
                           "United States","US",10))
    combined={a["id"]:a for a in saved if a.get("id") and a.get("url")}
    combined.update({a["id"]:a for a in fresh})
    entries=[a for a in combined.values() if a.get("date")
             and now-datetime.fromisoformat(a["date"])<timedelta(days=7)]
    entries.sort(key=lambda a:a["date"],reverse=True)
    # Preserve a useful cross-section of states, not just one large media market.
    chosen=[];per={}
    for article in entries:
        st=article.get("state","US")
        if per.get(st,0)>=5:continue
        chosen.append(article);per[st]=per.get(st,0)+1
        if len(chosen)>=150:break
    payload={"updated":now.isoformat(),"coverage_note":
      "50 states and Washington, DC are checked in rotating groups over approximately 3 hours. Stories originate from attributed Google News RSS results. Official dates, voter registration and locations must be checked with your state election office.",
      "jurisdictions":[{"code":code,"name":name} for code,name in STATES],
      "states_checked_this_run":[name for code,name in group],
      "items":chosen,"count":len(chosen)}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("USA_ELECTION_COVERAGE",json.dumps({"count":len(chosen),"checked":len(group),
      "states_with_news":len({a["state"] for a in chosen})}))
if __name__=="__main__":main()
