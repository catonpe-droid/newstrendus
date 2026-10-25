#!/usr/bin/env python3
"""Install the NewsTrendus GA4 tag once per HTML page.

Runs as part of the existing GitHub Actions news build; includes new calculator,
city, guide, elections, story and dynamically generated social HTML.
Measurement IDs are public identifiers, not secrets.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MEASUREMENT_ID="G-10SMK0DD8L"

TAG=f"""<!-- Google Analytics 4 - NewsTrendus -->
<script async src="https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{MEASUREMENT_ID}');
</script>
"""
PRIVACY_HEADING="<h2>Google Analytics 4</h2>"
PRIVACY_NOTICE=(
    '<h2>Google Analytics 4</h2><p>We use Google Analytics 4 (GA4) to understand '
    'visits, approximate geographic regions, page views, engagement and which '
    'news sections and free calculators readers use. Google Analytics may use '
    'cookies and similar technologies and process browser, device and '
    'interaction information under Google&#39;s privacy terms. This helps us '
    'measure and improve the site; it is not a visitor account or a sale of '
    'personal information. You can use available browser privacy controls, '
    'and where applicable we provide or configure consent choices. Read '
    '<a href="https://policies.google.com/privacy" target="_blank" '
    'rel="noopener noreferrer">Google&#39;s Privacy Policy</a> and '
    '<a href="https://tools.google.com/dlpage/gaoptout" target="_blank" '
    'rel="noopener noreferrer">Google Analytics Opt-out</a>.</p>'
)

def main():
    added,kept,ignored=0,0,0
    for file in sorted(ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in file.relative_to(ROOT).parts):
            continue
        text=file.read_text(encoding="utf-8")
        # Do not add a second GA4 tag to a page already carrying this ID.
        if MEASUREMENT_ID in text:
            kept+=1
        else:
            if not re.search(r"</head\s*>",text,re.IGNORECASE):
                ignored+=1
                print("GA4: no <head> closing tag:",file.relative_to(ROOT))
                continue
            text=re.sub(r"</head\s*>",lambda m:TAG+m.group(0),text,count=1,flags=re.IGNORECASE)
            added+=1
        if file==ROOT/"privacy.html" and PRIVACY_HEADING not in text:
            anchor="<h2>Google AdSense, cookies and preferences</h2>"
            if anchor not in text:
                raise RuntimeError("GA4 privacy disclosure anchor missing")
            text=text.replace(anchor,PRIVACY_NOTICE+anchor,1)
        file.write_text(text,encoding="utf-8")
    print(f"GA4 TAG AUDIT: ID={MEASUREMENT_ID} newly_added={added} already_tagged={kept} skipped={ignored}")
    if added+kept<32:
        raise RuntimeError("Unexpectedly few site HTML pages received analytics")

if __name__=="__main__":
    main()
