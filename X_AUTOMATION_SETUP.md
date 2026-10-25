# NewsTrendus — RSS-to-X publishing connection

Status: RSS generation is configured in GitHub. **Automatic X posting is not enabled until the owner authorizes the X account with a third-party service.**

## What the website publishes

* RSS feed: https://newstrendus.com/x-feed.xml
* News source: trusted publisher RSS snapshots in `news.json`.
* Public links: durable source-attributed brief pages under `/social/stories/`.
* Schedule: GitHub refreshes the news every 30 minutes and selects at most one new story every 4 hours (maximum about six per day).
* Attribution: the brief links to the original news publisher. The image is clearly identified as a representative Pexels category photo, **not** a documentary image of the news event.
* Posts are not sent directly by GitHub; no X credentials are stored in this repository.

## Connect to X with an RSS automation service

1. Open https://ifttt.com/connect/feed/twitter or https://ifttt.com/applets/tRPiqM4T-post-new-rss-feed-items-to-x-twitter
2. Log in to IFTTT and choose an **RSS Feed → X (Twitter): Post a tweet** automation.
3. Enter `https://newstrendus.com/x-feed.xml` as the RSS feed URL.
4. Authorize your own X account on IFTTT's OAuth screen; never paste a password or access token in chat.
5. Use a template along these lines (replace placeholders through IFTTT's ingredient selector):

   `📰 {{EntryTitle}}\n{{EntryUrl}}\n#USNews`

6. Review any costs displayed by IFTTT before activation. X posting may need a paid IFTTT tier even though the GitHub feed is free.
7. Test with one new feed entry and verify that the resulting tweet links to a NewsTrendus page.

## Alternatives

Metricool's RSS Autolist can automate social publishing, but X connectivity requires a paid Starter-or-higher plan **and** a separate X add-on. It is not a fully free option.

**Important:** This repository cannot turn on third-party services or authorize your X account on your behalf. Site changes alone do not activate tweeting.

## Editorial and safety rules

* Avoid mass-posting every syndicated headline. Only select a few stories to reduce spam and duplicates.
* NewsTrendus is an attributed news discovery site, not the original reporter for these items.
* Source excerpts may be updated; never assert an unverified headline as independently confirmed.
* Pausing the IFTTT applet stops publishing to X without disabling the website's RSS or news refresh.
