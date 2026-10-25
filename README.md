# NewsTrendus.com

USA-focused trending news discovery site: RSS sources, Google Trends US, GTA 6/gaming and SEO-friendly category pages. Published via GitHub Actions to GitHub Pages.

This repository is maintained with ChatGPT assistance. The site credits original publishers and does not reproduce full news articles. Automated publishing does not guarantee Google rankings or AdSense eligibility.

## Setup

Once `.github/workflows/publish.yml` is present, open **Settings > Pages**, select **GitHub Actions** as the source, then run the workflow in **Actions**. Add `newstrendus.com` as a custom domain only after you control it and have set GitHub Pages DNS records.

## X (Twitter) automatic sharing

**Site-side feed is ready; posting to an X account requires the owner's one-time authorization.**

The GitHub Pages workflow creates `https://newstrendus.com/x-feed.xml` with:
- At most **one new, credited news brief every four hours**, avoiding posting all headlines indiscriminately.
- A NewsTrendus article landing URL (not a misleading redirect) with `utm_source=x&utm_medium=social&utm_campaign=auto_news` for GA4 attribution.
- Up to two relevant headline-based hashtags, already included in the feed item's **title**.
- Stable RSS GUIDs to avoid repeatedly surfacing the same news item.

### Connect an account (one-time, account-owner action)

1. Open https://ifttt.com/applets/xxME6t3P-tweet-new-rss-feed-items-automatically-with-x-twitter or create an RSS Feed → X (Twitter) Applet on IFTTT. IFTTT may require a paid plan for the X posting action.
2. Sign in to IFTTT, connect your own X account, and explicitly authorize posting.
3. Set the RSS feed URL to `https://newstrendus.com/x-feed.xml`.
4. In the X action text, insert the **EntryTitle** ingredient, a space, then **EntryUrl**. Example: `{{EntryTitle}} {{EntryUrl}}`. Do **not** paste a fixed headline or append extra generic hashtags: topic hashtags are included in EntryTitle already.
5. Turn the Applet on, use its check/test features, and inspect the first published post for an accurate title, relevant hashtags, an accessible NewsTrendus brief and publisher attribution.

IFTTT schedules polling rather than instant posting. New feed items are only queued when fresh eligible source briefs are available. This feed does not directly post to X; there are no X account credentials stored in this GitHub repository.

### Important policy notes

- Follow X automation and anti-spam policies: no automated mass replies/mentions, no unrelated trending hashtags, no duplicate promotion.
- Source news is attributed on the NewsTrendus page; do not imply NewsTrendus reported the original article firsthand.
- If sharing is no longer desired, disconnect or disable the IFTTT Applet. Revoking third-party access in X settings also stops authorized posting.
