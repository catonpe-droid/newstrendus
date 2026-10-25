"""Select fresh, US-relevant source-credited news for NewsTrendus X RSS.

Do not automatically target X trending topics, scrape X trends, or use unrelated
viral hashtags. X permits helpful RSS cross-posting, not trend manipulation.
The separately authorized Buffer workflow handles actual publication.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
import re
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "news.json"
STATE = ROOT / "social" / "x-history.json"
FEED = ROOT / "x-feed.xml"
SITE = "https://newstrendus.com"
INTERVAL = timedelta(hours=4)  # Max one new social brief every four hours.
CATEGORIES = {"US", "Technology", "Business", "Science", "Gaming", "Sports", "Entertainment", "Health", "World"}
MAX_STORY_AGE = timedelta(hours=30)
CATEGORY_WEIGHTS = {
    "US": 95, "Technology": 70, "Sports": 66, "Gaming": 64,
    "Business": 63, "Science": 60, "Health": 59,
    "Entertainment": 48, "World": 15,
}
US_SIGNALS = re.compile(
    r"\b(?:U\.?S\.?A?\.?|United States|Americans?|American|"
    r"Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|"
    r"Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|"
    r"Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|"
    r"Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|"
    r"New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|"
    r"Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|"
    r"Virginia|Washington|West Virginia|Wisconsin|Wyoming|"
    r"Chicago|Los Angeles|Milwaukee|Miami|Atlanta|Houston|Dallas|Boston|"
    r"White House|Congress|Federal Reserve|Supreme Court|"
    r"NIH|Medicare|Medicaid|Obamacare|ACA plan|midterms?|"
    r"NASA|NFL|NBA|MLB|NHL|Super Bowl|World Series)\b",
    flags=re.IGNORECASE,
)
US_ANCHOR_CATEGORIES = frozenset({"US", "World", "Business", "Sports"})

UNSUITABLE = re.compile(
    r"\b(?:sponsored by|advertisement|newsletter|weekly roundup|"
    r"daily puzzle|horoscope|rumou?rs?|unconfirmed|spoiler)\b",
    flags=re.IGNORECASE,
)
STOPWORDS = frozenset(
    "a an and are at by for from in into is it of on or the to was were "
    "with how why what when after amid says over under new latest today".split()
)

PHOTOS = {
    "US": ("36077357", "Mark Direen", "https://www.pexels.com/photo/iconic-view-of-the-us-capitol-building-at-dawn-36077357/"),
    "Technology": ("34804003", "Daniil Komov", "https://www.pexels.com/photo/modern-workspace-with-laptop-and-code-display-34804003/"),
    "Business": ("36755611", "Jakub Zerdzicki", "https://www.pexels.com/photo/stock-trader-analyzing-market-data-on-screen-36755611/"),
    "Science": ("4031693", "Edward Jenner", "https://www.pexels.com/photo/two-scientists-working-inside-the-laboratory-4031693/"),
    "Gaming": ("7862378", "Alena Darmel", "https://www.pexels.com/photo/a-person-holding-a-game-controller-7862378/"),
    "Sports": ("33535231", "Axel Sandoval", "https://www.pexels.com/photo/outdoor-sports-stadium-with-spectators-33535231/"),
    "Entertainment": ("7991112", "Tima Miroshnichenko", "https://www.pexels.com/photo/empty-seats-of-a-movie-theater-7991112/"),
    "World": ("7635240", "Marina Leonova", "https://www.pexels.com/photo/a-map-beside-a-globe-7635240/"),
}


# Tags must reflect the subject in the *actual headline*, not unrelated trends.
# X discourages irrelevant/viral hashtags and duplicate promotional posts.
DEFAULT_TAGS = {
    "US": "#USNews", "Technology": "#TechNews", "Business": "#BusinessNews",
    "Science": "#ScienceNews", "Gaming": "#GamingNews",
    "Sports": "#SportsNews", "Entertainment": "#EntertainmentNews",
    "World": "#WorldNews",
}
TOPIC_TAGS = (
    (r"\b(gta\s*(?:6|vi)|grand theft auto)\b", "#GTA6"),
    (r"\b(nfl|super bowl)\b", "#NFL"),
    (r"\b(nba|basketball)\b", "#NBA"),
    (r"\b(mlb|baseball|world series)\b", "#MLB"),
    (r"\b(nasa|artemis)\b", "#NASA"),
    (r"\b(artificial intelligence|ai-powered|openai)\b", "#AI"),
    (r"\b(cybersecurity|data breach|ransomware)\b", "#Cybersecurity"),
    (r"\b(oregon)\b", "#Oregon"),
    (r"\b(texas)\b", "#Texas"),
    (r"\b(california)\b", "#California"),
    (r"\b(new york)\b", "#NewYork"),
    (r"\b(flood|flooding)\b", "#Flooding"),
    (r"\b(drought)\b", "#Drought"),
    (r"\b(rancher|ranchers|farming|farmers|agriculture)\b", "#Agriculture"),
    (r"\b(wildfire|wildfires)\b", "#Wildfires"),
    (r"\b(inflation)\b", "#Inflation"),
    (r"\b(federal reserve|fed rate)\b", "#FederalReserve"),
    (r"\b(earnings)\b", "#Earnings"),
    (r"\b(space|moon|mars|astronaut)\b", "#Space"),
)

def tweet_headline(item: dict) -> str:
    """Headline plus at most two *related* hashtags; safe for 'EntryTitle EntryUrl'."""
    headline = " ".join(str(item.get("title") or "").split())
    tags = []
    for pattern, tag in TOPIC_TAGS:
        if re.search(pattern, headline, flags=re.I) and tag not in tags:
            tags.append(tag)
        if len(tags) == 2:
            break
    if len(tags) < 2:
        generic = DEFAULT_TAGS.get(str(item.get("category") or ""), "#USNews")
        if generic not in tags:
            tags.append(generic)
    suffix = "  " + " ".join(tags[:2])
    # The URL consumes about 23 characters in X's weighted post length.
    # Keep title + tags under 230, leaving breathing room for the article URL.
    limit = max(60, 225 - len(suffix))
    if len(headline) > limit:
        clipped = headline[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
        headline = clipped + "…"
    return headline + suffix

def attributed_share_link(item: dict) -> str:
    """UTM-tagged, same-site article URL, not a publisher's destination."""
    url = str(item["share_url"])
    if not url.startswith(SITE + "/social/stories/"):
        raise ValueError("External or unexpected social link")
    return url + "?utm_source=x&utm_medium=social&utm_campaign=auto_news"

def headline_tokens(title: str) -> set[str]:
    """Normalized tokens to stop several near-identical RSS stories."""
    return {
        token for token in re.findall(r"[a-z0-9]{3,}", title.casefold())
        if token not in STOPWORDS
    }


def is_duplicate_topic(title: str, recent: list[dict]) -> bool:
    incoming = headline_tokens(title)
    if len(incoming) < 4:
        return False
    for old in recent:
        previous = headline_tokens(str(old.get("title") or ""))
        if len(previous) < 4:
            continue
        overlap = len(incoming & previous)
        similarity = overlap / len(incoming | previous)
        if overlap >= 4 and similarity >= 0.62:
            return True
    return False


def editorial_score(item: dict, now: datetime, recent: list[dict]) -> float:
    """US-readership and freshness heuristic; not an X trends/rankings feed."""
    category = str(item.get("category") or "")
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    date = when(item.get("date"))
    age_hours = (now - date).total_seconds() / 3600 if date else 72
    score = CATEGORY_WEIGHTS.get(category, 0)
    score += max(0, 46 - age_hours * 2.3)
    if US_SIGNALS.search(title):
        score += 27
    elif US_SIGNALS.search(summary):
        score += 9
    elif category == "World":
        score -= 38  # Never prioritize unrelated overseas news for US readership.
    if category == "US":
        score += 8
    if len(summary.strip()) >= 70:
        score += 8
    elif not summary.strip():
        score -= 12
    last_categories = [x.get("category") for x in recent[-3:]]
    score -= 24 * last_categories.count(category)
    if recent and recent[-1].get("source") == item.get("source"):
        score -= 12
    return score


def when(value: str | None) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None

def image_for(category: str) -> tuple[str, str, str]:
    number, photographer, credit = PHOTOS.get(category, PHOTOS["US"])
    return f"https://images.pexels.com/photos/{number}/pexels-photo-{number}.jpeg?auto=compress&cs=tinysrgb&w=1200", photographer, credit

def social_html(story: dict) -> str:
    title = escape(str(story["title"]))
    summary = escape(str(story.get("summary") or "A current headline from a credited news source. Visit the original publisher for full details."))
    source = escape(str(story.get("source") or "Original publisher"))
    category = escape(str(story["category"]))
    href = escape(str(story["share_url"]), quote=True)
    original = escape(str(story["url"]), quote=True)
    photograph, photographer, photo_credit = image_for(story["category"])
    photo = escape(photograph, quote=True)
    photographer = escape(photographer)
    photo_credit = escape(photo_credit, quote=True)
    desc = escape((str(story.get("summary") or "Attributed news brief. See the original publisher for details."))[:190], quote=True)
    pub = escape(str(story.get("date") or ""), quote=True)
    return f"""<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | NewsTrendus</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{href}">
<meta property="og:type" content="article"><meta property="og:site_name" content="NewsTrendus">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{href}"><meta property="og:image" content="{photo}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{photo}">
<meta property="article:published_time" content="{pub}">
<link rel="stylesheet" href="../../site.css"><link rel="icon" href="../../assets/us-mark.svg" type="image/svg+xml">
<style>body{{margin:0;background:#f5f7fa;color:#142334;font-family:Arial,sans-serif}}.wrap{{max-width:850px;margin:0 auto;padding:22px}}.panel{{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px #20314a12}}.inside{{padding:clamp(19px,4vw,35px)}}h1{{font-size:clamp(26px,4.4vw,43px);line-height:1.13;letter-spacing:-.03em}}.hero{{width:100%;max-height:440px;object-fit:cover}}.small{{font-size:13px;color:#607086}}.btn{{display:inline-block;padding:13px 18px;background:#b42337;color:white!important;border-radius:7px;font-weight:bold;text-decoration:none}}a{{color:#a82037}}p{{line-height:1.75}}</style>
</head><body><div class="wrap"><p><a href="../../index.html"><strong>🇺🇸 NewsTrendus.com</strong></a> · USA edition</p>
<article class="panel"><div class="inside"><p class="small">{category} / Source-credited news brief</p>
<h1>{title}</h1><p class="small">Publisher: {source} · Publisher date: {escape(str(story.get("date") or "Not stated"))}</p></div>
<img class="hero" src="{photo}" alt="Representative category photograph, not an image of this news event">
<div class="inside"><p class="small">Representative image (not a photograph of the reported event): <a href="{photo_credit}">{photographer} / Pexels</a></p>
<h2>What the source reports</h2><p>{summary}</p>
<p class="small">This excerpt is provided by the credited publisher's RSS feed. NewsTrendus has not independently verified the story. The source may have more recent updates and details.</p>
<p><a class="btn" href="{original}" target="_blank" rel="noopener noreferrer">Read full reporting at {source}</a></p>
<p><a href="../../index.html">Explore more US news and trends</a></p>
</div></article><p class="small">Original reporting remains with its credited publisher. NewsTrendus is an independent source-discovery service.</p></div></body></html>
"""

def build() -> None:
    now = datetime.now(timezone.utc)
    history = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"items": []}
    selected = history.get("items", [])
    if not isinstance(selected, list):
        selected = []
    previous = when(selected[-1].get("shared_at")) if selected else None
    data = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"items": []}
    all_ids = {str(x.get("id")) for x in selected}
    if previous is None or now - previous >= INTERVAL:
        choices = []
        recent = [
            s for s in selected[-30:]
            if (when(s.get("shared_at")) or datetime.min.replace(tzinfo=timezone.utc))
               >= now - timedelta(days=5)
        ]
        for item in data.get("items", []):
            date = when(item.get("date"))
            url = str(item.get("url") or "")
            ident = str(item.get("id") or "")
            title = " ".join(str(item.get("title") or "").split())
            parsed_url = urlparse(url)
            if (
                not re.fullmatch(r"[a-f0-9]{16}", ident) or ident in all_ids
                or item.get("category") not in CATEGORIES
                or len(title) < 25 or not date
                or not (timedelta(0) <= now - date < MAX_STORY_AGE)
                or parsed_url.scheme != "https" or not parsed_url.netloc
                or UNSUITABLE.search(title)
                or (
                    item.get("category") in US_ANCHOR_CATEGORIES
                    and not US_SIGNALS.search(title + " " + str(item.get("summary") or ""))
                )
                or is_duplicate_topic(title, recent)
            ):
                continue
            choices.append(item)
        # Editorial selection only: freshness, US relevance and source diversity.
        # X explicitly disallows automating posts about X trending topics.
        choices.sort(
            key=lambda a: (
                editorial_score(a, now, recent),
                when(a.get("date")) or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )
        if choices:
            a = choices[0]
            story = {k: a.get(k) for k in ("id", "title", "summary", "source", "category", "url", "date")}
            story["shared_at"] = now.isoformat()
            story["share_url"] = f"{SITE}/social/stories/{a['id']}.html"
            selected.append(story)
            out = ROOT / "social" / "stories" / f"{a['id']}.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(social_html(story), encoding="utf-8")
            print("Queued one US-relevant source-credited post:", story["title"], "\\nCategory:", story["category"])
        else:
            print("No eligible fresh source headlines available.")
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({"items": selected}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for k, v in (
        ("title", "NewsTrendus — Source-credited USA news briefs"),
        ("link", SITE + "/"),
        ("description", "Selected source-attributed news briefs; visit NewsTrendus for context and the publisher link. Original reporting is credited."),
        ("language", "en-us"),
    ):
        ET.SubElement(channel, k).text = v
    ET.SubElement(channel, "ttl").text = "60"
    latest = when(selected[-1].get("shared_at")) if selected else now
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(latest)
    for item in reversed(selected[-40:]):
        node = ET.SubElement(channel, "item")
        for k, v in (
            ("title", tweet_headline(item)),
            ("link", attributed_share_link(item)),
            ("description", f"Source: {item.get('source') or 'publisher'}. {str(item.get('summary') or '')[:280]}"),
            ("guid", "newstrendus:" + str(item["id"])),
            ("pubDate", format_datetime(when(item.get("shared_at")) or now)),
        ):
            el = ET.SubElement(node, k)
            el.text = v
            if k == "guid":
                el.set("isPermaLink", "false")
    ET.indent(rss, space="  ")
    ET.ElementTree(rss).write(FEED, encoding="utf-8", xml_declaration=True)
    print("RSS entries:", min(40, len(selected)))

if __name__ == "__main__":
    build()
