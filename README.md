# NewsTrendus.com

NewsTrendus is a US-focused news discovery and attributed editorial website on GitHub Pages. **Google Trends US is the primary subject-discovery signal** for the scheduled editorial assistant; a search trend is never proof that a story is true. Every publishable story requires independent factual checks, source links and meaningful original context.

## Permanent photo policy: link only, no image uploads

For **every news article published now or in the future**:

- Use a real, suitable, lawfully reusable professional **photograph**, not AI event impersonation, an SVG news poster, or a flat category illustration.
- Prefer `https://images.pexels.com/photos/...` **direct external JPEG URLs**. HTML, JSON and NewsArticle schema contain only the URL; **never download or commit a photo, image binary, generated image or editorial SVG** to this repository, ChatGPT Library, Drive or any local image library.
- Record `news:photo_artist` and `news:photo_credit_url` metadata. Show the proper credit and original Pexels photo-page link beside the displayed image. Mark generic imagery **representative**, not an actual photograph of the reported event.
- Use `<img class="nt-hero" width="1600" height="900" src="https://images.pexels.com/...">` for news heroes (the legacy F1 article uses class `nthimg`). Use 16:9, center-cropped `object-fit:cover`, at most about 420 px tall on desktop, responsive on mobile. The same credited image appears in the homepage cards, corresponding category, article directory and its article page.
- Existing identity files (e.g. the site's small logo and icons) are not news photographs and may remain locally hosted; the restriction covers **editorial news images**.

The GitHub Actions deployment gate runs `scripts/editorial_catalog.py` and **`scripts/validate_editorial_images.py`** before SEO/deployment. It blocks pages with missing/wrong external CDN URLs, inappropriate local/SVG hero references, invalid 16:9 sizing or absent photo credits. New article images must always pass this validation. The catalogue `editorial-news.json` ensures every news article is shown among **Top Stories** and in its correct category; retain the familiar sitewide navigation.

### Storage model

**CDN photo server → article HTML/JSON URL → visitor browser**.

Only small HTML/CSS/JavaScript/JSON metadata and publisher-credit links are added to the repo. News-image bytes remain on Pexels or another explicitly authorized third-party photo host, not in the GitHub repo or user Library. This saves repository image storage; actual photo download bandwidth, third-party availability and caching still depend on the CDN and visitor browser.

## Scheduling and deployment

The ChatGPT **NewsTrendus Google Trends Publisher** task runs every four hours, targets 4–5 factual, nonduplicate, US-relevant articles where sufficient sources exist, and must never claim an article published without an actual GitHub commit. RSS previews may still appear as source-linked discovery, but **generic RSS feed-to-article autoblogging is disabled**. The GitHub Actions `publish.yml` workflow is for catalogue regeneration, image policy and SEO checks, GA4 and GitHub Pages deployment.

To configure GitHub Pages, select GitHub Actions under repository Settings → Pages and confirm the custom domain. Every push to `main` requests a deployment. Check **Actions** for policy or build failures; passing commits do not guarantee immediate live visibility, search indexing, AdSense approval or traffic.

## Attribution and content quality

Do not use unlicensed third-party reporting or photographs without permission. Keep original story links, accurate factual publication dates and representative-image disclosure. Avoid keyword stuffing, shallow paraphrases, misleading headlines or artificial click tactics. Strong SEO metadata is a technical baseline, not a guarantee of virality.

## Optional social sharing

An older Buffer/X integration exists in the repository but is not an active automatic hourly publishing source. Do not restore its schedule or collect X trending hashtags for automated promotion without separate authorization and platform-policy review. API keys must stay in GitHub Actions secrets, never source files.
