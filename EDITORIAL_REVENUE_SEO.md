# NewsTrendus — US search-intent and AdSense-safe editorial playbook

Effective: November 8, 2026. Applies to every newly published or substantively updated news article and to future publishing automation. This document complements existing factual verification, copyright, external Pexels photo credit, image-policy and technical publishing rules. Editorial quality and reader benefit take priority over ad revenue.

## Core rule

Write genuinely useful American news reporting, not keyword-loaded pages made to influence advertising. Identify the real U.S. reader search intent before drafting. Research actual related queries where data is available; do not invent popularity, trend rank, CPC, Google Ads advertiser bids, or Search Console rankings. One natural primary query and two to five genuinely relevant supporting phrases is a planning framework, NOT a quota for repeated use.

Google may target ads using page content and audience, among other signals. Publisher earnings are determined by auctions, traffic, ads delivered, valid clicks and impressions. A topic that seems commercially attractive does NOT promise high CPC, ads or revenue.

## Per-article checklist

1. **Story selection:** Start with current Google Trends USA and separately verified newsworthy sources (federal/state agencies, filings, official company announcements, credible independent reporting). Select a timely, nonduplicate story with authentic reader benefit. Prefer service journalism when the facts justify it.
2. **Keyword brief:** Identify one factual primary US search query and 2–5 close reader-search variants/questions; decide whether the article has honest commercial intent. Examples: eligibility, deadline, premiums, coverage changes, recalls, prices, cost comparisons, lawsuits, contracts, tax steps. If no truthful commercial angle exists, publish the news naturally without it.
3. **Title/H1/URL:** Make one accurate, concise descriptive H1 matching the title/OG headline; incorporate the main search phrase only where it reads naturally. Keep URL stable for substantive updates to previously published news.
4. **Metadata:** Distinct meta description (~150–160 characters where sensible), on-page answer-first summary, accurate canonical and dates, NewsArticle structured data, section and byline. Never use a `meta name="keywords"` tag as a ranking trick.
5. **Article body:** Provide verified who/what/when/where/why/how, source-linked facts, concrete U.S. implications, useful H2 headings, necessary context and careful uncertainties. Include dates, amounts, affected states, official steps and user actions only when backed by evidence.
6. **Links and media:** Include authoritative primary sources and meaningful internal links to EXISTING relevant NewsTrendus URLs. Use one real licensed 16:9 representative image via unmodified external HTTPS CDN URL, with actual photographer and original photo-page attribution. Never upload news image files to GitHub.
7. **Quality control:** Read aloud for natural English, check all links and dates, no repeated keyword blocks, thin AI rewrites, false benefits, misleading sponsored language, fabricated quotes, fake claims, or duplicate new URLs. Ensure all publishing, photo and AdSense validation gates pass.
8. **Run report:** State each story's factual primary query, concise related search-intent focus, whether a real commercial angle existed, verified sources, and deployment outcome. Do not claim Search Console or AdSense statistics without authenticated access.

## Relevant U.S. reporting opportunities (only when newsworthy)

| Topic | Real reader search intent examples | Editorial guardrail |
| --- | --- | --- |
| Insurance and housing | U.S. homeowners insurance rate increase; state auto insurance premiums; mortgage refinance rate change | Cite dated state filings, regulator/company notices and avoid unverified quotes or rate claims |
| Personal finance and consumer issues | credit card APR rule; federal student-loan servicing update; mortgage closing cost changes | Provide who is affected and authoritative update/eligibility sources |
| Taxes, employment and small business | IRS tax deadline; employer payroll rules; small-business financing program | Verify effective date and clear audience; no guaranteed savings language |
| Legal and consumer settlements | federal settlement deadline; consumer class-action eligibility; privacy compensation claims | Explain status, official claims page, deadline and uncertainties; do not impersonate legal advice |
| Cybersecurity and enterprise tech | US data breach notification; cyber insurance requirements; cloud or business-software pricing | Distinguish verified breach/filing from rumor and do not invent financial impact |
| Health coverage | Medicare plan change; health insurance enrollment deadline | Source CMS/state insurance authorities; avoid unsupported medical or financial advice |
| Safety and consumer products | safety recall model numbers, remedy, retailers and repair instructions | Use actual CPSC/FDA/NHTSA notices with precise model and incident data |

These are candidate **topics**, not terms to force into every headline. Sports, science and entertainment pages should keep their truthful subject matter even when that means no commercial keywords.

## AdSense and performance boundaries

- Never insert hidden text, invisible keywords, lists of unrelated high-CPC terms, misleading headings or keyword-stuffed FAQs.
- Do not turn genuine news into an unrelated insurance, credit, legal or medical advertorial.
- Google Search ignores the meta keywords tag; quality and relevant on-page language matter more than repeating phrases.
- Sitewide AdSense Auto Ads script is handled by `scripts/adsense_tag.py`. Do not add duplicate ad loader scripts or place ads to imitate navigation or editorial content.
- If accessible later, compare verified AdSense **Page RPM**, page views and estimated earnings together with real Search Console clicks, impressions and queries over equal windows. Do not guess advertiser CPC and do not promise earnings.

Official guidance:
- https://developers.google.com/search/docs/essentials/spam-policies
- https://developers.google.com/search/docs/essentials
- https://support.google.com/adsense/answer/9713
- https://support.google.com/adsense/answer/112030
