#!/usr/bin/env python3
"""Sitewide, idempotent Google AdSense Auto Ads installation for NewsTrendus.

The AdSense dashboard owns ad format, load, exclusions and revenue settings.
This script only ensures a single authorized tag on eligible content pages.
It intentionally does not create fake ad placements or promise earnings.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER_ID = "ca-pub-2124953371207111"
ADS_TXT_ENTRY = "google.com, pub-2124953371207111, DIRECT, f08c47fec0942fa0"
AUTO_AD_TAG = (
    '<script async src="https://pagead2.googlesyndication.com/pagead/js/'
    'adsbygoogle.js?client=' + PUBLISHER_ID +
    '" crossorigin="anonymous"></script>'
)
ACCOUNT_META = '<meta name="google-adsense-account" content="' + PUBLISHER_ID + '">'
SCRIPT_RE = re.compile(
    r'<script\b[^>]*\bsrc\s*=\s*["\'][^"\']*pagead2\.googlesyndication\.com/'
    r'pagead/js/adsbygoogle\.js[^"\']*["\'][^>]*>',
    re.IGNORECASE,
)
HEAD_END_RE = re.compile(r'</head\s*>', re.IGNORECASE)
ROBOT_META_RE = re.compile(r'<meta\b[^>]*name=["\']robots["\'][^>]*>', re.IGNORECASE)


def is_eligible(path: Path, html: str) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    content_path = relative == "index.html" or relative.startswith(
        ("articles/", "calculators/", "cities/", "guides/", "politics/")
    )
    if not content_path or relative.endswith("/404.html"):
        return False
    robots = ROBOT_META_RE.search(html)
    if robots and "noindex" in robots.group(0).lower():
        return False
    return True


def audit() -> None:
    ads_path = ROOT / "ads.txt"
    if not ads_path.exists() or ADS_TXT_ENTRY not in ads_path.read_text(encoding="utf-8"):
        raise SystemExit("ADSENSE ERROR: ads.txt publisher record is missing or incorrect")

    check = "--check" in sys.argv[1:]
    inserted = 0
    existing = 0
    excluded = 0
    errors = []

    for path in sorted(ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        html = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        if not is_eligible(path, html):
            excluded += 1
            continue

        if not HEAD_END_RE.search(html):
            errors.append(relative + ": missing closing head")
            continue

        current_script = SCRIPT_RE.search(html)
        if current_script:
            if PUBLISHER_ID not in current_script.group(0):
                errors.append(relative + ": another AdSense account's script is present")
                continue
            existing += 1
        else:
            if check:
                errors.append(relative + ": Auto Ads tag missing")
                continue
            injection = ""
            if "google-adsense-account" not in html:
                injection += ACCOUNT_META + "\n"
            injection += AUTO_AD_TAG + "\n"
            html = HEAD_END_RE.sub(lambda match: injection + match.group(0), html, count=1)
            path.write_text(html, encoding="utf-8")
            inserted += 1

    print(
        "ADSENSE AUTO ADS: publisher=" + PUBLISHER_ID +
        " newly_tagged=" + str(inserted) +
        " already_tagged=" + str(existing) +
        " excluded_noncontent_pages=" + str(excluded) +
        " errors=" + str(len(errors)) +
        " check_mode=" + str(check)
    )
    for error in errors[:25]:
        print("ADSENSE ERROR:", error)
    if errors:
        raise SystemExit("ADSENSE ERROR: Fix the untagged/mismatched pages above")
    if inserted + existing < 180:
        raise SystemExit("ADSENSE ERROR: Unexpectedly few eligible pages found")


if __name__ == "__main__":
    audit()
