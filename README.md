# NewsTrendus.com

USA-focused trending news discovery site: RSS sources, Google Trends US, GTA 6/gaming and SEO-friendly category pages. Published via GitHub Actions to GitHub Pages.

This repository is maintained with ChatGPT assistance. The site credits original publishers and does not reproduce full news articles. Automated publishing does not guarantee Google rankings or AdSense eligibility.

## Setup

Once `.github/workflows/publish.yml` is present, open **Settings > Pages**, select **GitHub Actions** as the source, then run the workflow in **Actions**. Add `newstrendus.com` as a custom domain only after you control it and have set GitHub Pages DNS records.

## X (Twitter) completely free automatic sharing

NewsTrendus has an RSS generator and GitHub Actions automation that can publish selected news to X through **Buffer Free**, with no paid IFTTT, no paid X developer API, and no server hosting cost. Personal setup of the connected social account is still required.

### One-time account-owner setup (never paste an API key into chat or a GitHub file)

1. Create/login to a **Buffer Free** account at https://buffer.com/ and connect only the intended NewsTrendus **X (Twitter)** account at https://publish.buffer.com/settings/channels. Do not start a paid trial or enter billing details.
2. Open https://publish.buffer.com/settings/api → **Personal Access** → **New Key**; give it a name such as `NewsTrendus GitHub`. Grant the minimum required scopes for organization/channel read, post read and post creation. Copy the generated key privately.
3. Open https://github.com/catonpe-droid/newstrendus/settings/secrets/actions and create a **repository secret** named `BUFFER_API_KEY`. Paste the Buffer key as its value. Never add the key to a source file, commit, issue, or chat.
4. If Buffer holds **more than one X channel**, set GitHub **Settings → Secrets and variables → Actions → Variables** `BUFFER_CHANNEL_ID` to the intended X channel ID. For exactly one X channel this is unnecessary.
5. Open https://github.com/catonpe-droid/newstrendus/actions/workflows/post-x-free.yml and click **Run workflow** once. Inspect its logs and then verify the post directly on your X profile. The workflow also runs hourly, but only shares a *new eligible* article queued by the RSS generator.

### What is automated

- The existing publishing workflow refreshes `https://newstrendus.com/x-feed.xml` and prepares a NewsTrendus article landing page with publisher attribution.
- `scripts/build_x_feed.py` chooses **at most one fresh source-attributed brief every four hours** using US-topic relevance, headline freshness, source/category variety and near-duplicate-topic checks. US/world/business/sports stories need a clear US connection. It adds up to two topic-relevant hashtags from the headline.
- **Important X policy:** automated harvesting/posting about *X's trending topics* or attaching unrelated trending hashtags to drive traffic is prohibited. This is editorial RSS cross-posting, not X trend-jacking.
- `scripts/post_buffer_x.py` runs using `BUFFER_API_KEY` from GitHub Actions secrets; it verifies that the page exists publicly, picks the connected X channel, checks for duplicates, and submits **one** item to Buffer with `mode: shareNow`.
- The URL includes `utm_source=x&utm_medium=social&utm_campaign=auto_news` so visitors from X can be counted in Google Analytics 4.
- `social/buffer-history.json` tracks successful submissions (not credentials). If Buffer rejects a post or setup is missing, no post is reported as successful.

The workflow intentionally **does not** post while the Buffer API key or X authorization is missing. The initial setup cannot be done remotely without the X account owner's permission. The Buffer Free plan currently supports X and an API key, with a maximum of 10 queued posts per channel at a time; this workflow uses immediate posting and checks Buffer's actual response. Free plans, feature availability and API quotas are controlled by Buffer and can change.

References:
- https://buffer.com/pricing
- https://developers.buffer.com/guides/your-first-post.html
- https://developers.buffer.com/guides/rest-migration.html
- https://support.buffer.com/en-us/articles/how-to-create-your-buffer-api-key-ShIgYVwM6j
