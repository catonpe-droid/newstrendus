# NewsTrendus — Google Search Console setup

**Live property:** `newstrendus.com` (Domain property, no `https://`, no `www`).
**Public homepage:** https://newstrendus.com/
**Sitemap:** https://newstrendus.com/sitemap.xml
**Robots:** https://newstrendus.com/robots.txt
**Repository:** https://github.com/catonpe-droid/newstrendus

## Site owner: one-time Google Search Console steps

1. Open **https://search.google.com/search-console/welcome** while signed into the Google account that should own the site's Search Console property.
2. Choose **Domain**, enter only **newstrendus.com**, and select **Continue**.
3. Google shows a **unique TXT record** such as `google-site-verification=...`. This is an example prefix only: **do not make up or copy an example token**. Copy the entire record shown in your own Search Console.
4. In the domain registrar's DNS manager, add a **TXT** record with host **@** and value **exactly Google's displayed TXT record**, with Auto/default TTL. Do not delete or change the site's existing GitHub Pages A/CNAME, email MX or AdSense-related DNS records.
5. Return to Search Console and select **Verify**. It may take time for DNS TXT changes to propagate. Leave the TXT in DNS for continued ownership verification.
6. Open **Indexing → Sitemaps** in the newly verified Domain property. Under **Add a new sitemap**, enter **https://newstrendus.com/sitemap.xml** if the field accepts absolute URLs, or **sitemap.xml** if the Search Console UI has prefilled the site's URL. Submit.
7. In **URL Inspection**, inspect these important pages:
   - https://newstrendus.com/
   - https://newstrendus.com/calculators/index.html
   - https://newstrendus.com/calculators/mortgage.html
   - https://newstrendus.com/calculators/sales-tax.html
   - https://newstrendus.com/cities/index.html
   - https://newstrendus.com/politics/elections.html
8. Where eligible, select **Request indexing** after a successful live URL test. Do not repeatedly submit hundreds of URLs. Google decides whether/when a page is indexed.
9. Review **Performance → Search results**, **Indexing → Pages**, **Core Web Vitals**, and **Sitemaps** weekly. For US-focused readership, filter Performance by **Country → United States** when data arrives.

## Automated SEO protection in GitHub

Every 30-minute scheduled **Refresh USA news and publish** workflow:
- Fetches and curates approximately **45** source-credited news headlines.
- Updates relevant local politics information when available.
- Runs `python scripts/seo_build.py` to rebuild the sitemap from static, canonical, indexable HTML pages.
- Audits metadata, titles, viewport declarations and local HTML links.
- Leaves thin/temporary JavaScript RSS preview URLs out of Google's static sitemap.
- Writes `robots.txt` with a link to the sitemap.

**Important:** RSS snippets and republished articles do not automatically qualify for Google indexing or AdSense approval. Search results require original, useful information. Source rights and editorial guidelines are still important.

## If Domain DNS verification is unavailable

Create a separate **URL-prefix** property for `https://newstrendus.com/`, choose Google's **HTML tag** method, and add Google's exact provided `google-site-verification` meta tag to the homepage `<head>`. An HTML meta tag **cannot verify the Domain property**; only DNS verification does that.

There is no Google Search Console account authorization inside this GitHub repository. The Google sign-in and ownership verification are account-specific steps and cannot be simulated by committing a fake token.
