#!/usr/bin/env python3
"""NewsTrendus RSS -> Buffer Free -> X (Twitter).

The user's Buffer API token belongs only in GitHub Actions secret BUFFER_API_KEY.
This script shares no passwords, makes at most one X post per invocation,
and records successful submissions to avoid re-sharing the same news brief.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "x-feed.xml"
STATE = ROOT / "social" / "buffer-history.json"
BUFFER_API = "https://api.buffer.com"
AGE_LIMIT = timedelta(hours=18)
ALLOWED_HOST = "newstrendus.com"
STORY_PATTERN = re.compile(r"^/social/stories/[a-f0-9]{16}\.html$")


def load_candidate(now: datetime) -> dict | None:
    if not FEED.exists():
        print("No RSS feed yet; nothing to share.")
        return None
    root = ET.parse(FEED).getroot()
    item = root.find("channel/item")
    if item is None:
        print("RSS feed has no stories yet.")
        return None
    guid = (item.findtext("guid") or "").strip()
    title = " ".join((item.findtext("title") or "").split())
    url = (item.findtext("link") or "").strip()
    pub = (item.findtext("pubDate") or "").strip()
    if not guid.startswith("newstrendus:") or not title or not pub:
        print("RSS item is missing its stable ID, title or publish date.")
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != ALLOWED_HOST or not STORY_PATTERN.fullmatch(parsed.path):
        raise ValueError("Refusing to share an external or invalid NewsTrendus article URL.")
    date = parsedate_to_datetime(pub).astimezone(timezone.utc)
    age = now - date
    if age < timedelta(minutes=-15) or age > AGE_LIMIT:
        print("No fresh eligible article (RSS item's age is outside the 18-hour window).")
        return None
    if len(title) > 250:
        raise ValueError("RSS title is too long; check the hashtag generator.")
    return {"guid": guid, "title": title, "url": url, "published": date.isoformat()}


def load_history() -> list[dict]:
    if not STATE.exists():
        return []
    data = json.loads(STATE.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("submissions"), list):
        raise ValueError("Unrecognized Buffer submission history; refusing duplicate posting.")
    return data["submissions"]


def save_history(history: list[dict], entry: dict) -> None:
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(
        json.dumps({"submissions": (history + [entry])[-300:]}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def gql(token: str, query: str) -> dict:
    request = Request(
        BUFFER_API,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "NewsTrendus-BufferPublisher/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        result = json.load(response)
    if result.get("errors"):
        detail = "; ".join(str(x.get("message", "GraphQL error")) for x in result["errors"])
        raise RuntimeError("Buffer API error: " + detail[:280])
    if not isinstance(result.get("data"), dict):
        raise RuntimeError("Buffer API sent a response without data.")
    return result["data"]


def find_x_channel(token: str, preferred_id: str = "") -> tuple[str, str]:
    organizations = gql(token, "query { account { organizations { id name } } }")
    orgs = (organizations.get("account") or {}).get("organizations") or []
    matches = []
    for org in orgs:
        org_id = str(org["id"])
        q = 'query { channels(input: { organizationId: ' + json.dumps(org_id) + ' }) { id name service } }'
        channels = gql(token, q).get("channels") or []
        for channel in channels:
            if str(channel.get("service", "")).lower() in {"twitter", "x"}:
                if not preferred_id or str(channel.get("id")) == preferred_id:
                    matches.append((org_id, str(channel["id"])))
    if len(matches) != 1:
        raise RuntimeError(
            "Connect exactly one X account in Buffer. If you have multiple X channels, "
            "set the BUFFER_CHANNEL_ID repository variable to select one."
        )
    return matches[0]


def already_in_buffer(token: str, org_id: str, channel_id: str, candidate: dict) -> bool:
    # Double-check Buffer itself, in case a successful post was followed by a Git push error.
    query = (
        "query { posts(first: 50, input: {organizationId: " + json.dumps(org_id) +
        ", filter: {status: [sent, scheduled], channelIds: [" + json.dumps(channel_id) +
        "]}}) { edges { node { text } } } }"
    )
    edges = ((gql(token, query).get("posts") or {}).get("edges") or [])
    article_path = urlparse(candidate["url"]).path
    return any(
        article_path in str((e.get("node") or {}).get("text") or "")
        for e in edges
    )


def is_public(url: str) -> bool:
    # Only direct, non-redirecting NewsTrendus pages can be shared.
    request = Request(url, method="HEAD", headers={"User-Agent": "NewsTrendusBot/1.0"})
    try:
        with urlopen(request, timeout=15) as resp:
            return resp.status == 200 and urlparse(resp.geturl()).netloc == ALLOWED_HOST
    except Exception as exc:
        print("Landing page not available publicly yet:", type(exc).__name__)
        return False


def main() -> int:
    token = os.getenv("BUFFER_API_KEY", "").strip()
    if not token:
        print("Setup pending: add BUFFER_API_KEY to GitHub Actions repository secrets.")
        return 0

    now = datetime.now(timezone.utc)
    candidate = load_candidate(now)
    if not candidate:
        return 0
    history = load_history()
    if any(x.get("guid") == candidate["guid"] for x in history):
        print("Already submitted this article. Nothing to do.")
        return 0
    if not is_public(candidate["url"]):
        print("Skipping; article landing page is not deployed yet.")
        return 0

    preferred_id = os.getenv("BUFFER_CHANNEL_ID", "").strip()
    org_id, channel_id = find_x_channel(token, preferred_id)
    if already_in_buffer(token, org_id, channel_id, candidate):
        print("Already found this article in Buffer. Recording without reposting.")
        save_history(history, {
            "guid": candidate["guid"],
            "url": candidate["url"],
            "submitted_at": now.isoformat(),
            "status": "previously_in_buffer",
        })
        return 0

    text = candidate["title"] + "\n" + candidate["url"]
    # X weights ordinary URLs as 23 characters; keep non-URL text comfortably below 257.
    if len(candidate["title"]) > 250:
        raise ValueError("The post's headline exceeds the safe X size.")
    mutation = (
        "mutation { createPost(input: {text: " + json.dumps(text) +
        ", channelId: " + json.dumps(channel_id) +
        ", schedulingType: automatic, mode: shareNow}) {"
        " ... on PostActionSuccess { post { id dueAt } }"
        " ... on MutationError { message }"
        " } }"
    )
    result = gql(token, mutation).get("createPost") or {}
    post = result.get("post")
    if not post or not post.get("id"):
        raise RuntimeError("Buffer declined the post: " + str(result.get("message") or result)[:220])

    save_history(history, {
        "guid": candidate["guid"],
        "url": candidate["url"],
        "buffer_post_id": str(post["id"]),
        "submitted_at": now.isoformat(),
        "status": "submitted_to_buffer",
    })
    print("Successfully submitted one NewsTrendus article to the linked Buffer X channel.")
    print("Buffer post ID:", str(post["id"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, ET.ParseError) as exc:
        print("Buffer auto-posting stopped safely:", str(exc), file=sys.stderr)
        sys.exit(1)
