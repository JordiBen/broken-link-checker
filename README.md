# Broken Link Checker: Find 404s, Dead Links, Broken Images & Redirects

[![Run on Apify](https://img.shields.io/badge/Run%20on-Apify-1f6feb?logo=apify)](https://apify.com/manageable_gully/broken-link-checker) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Run it in the cloud with no setup:** [Broken Link Checker & SEO Crawler: 404s, Images, Redirects on the Apify Store](https://apify.com/manageable_gully/broken-link-checker).  
> Pay only per result, export to JSON/CSV/Excel, schedule runs and call it from the API.
<!-- AFFILIATE_LINK_PLACEHOLDER: replace the Apify links above with the affiliate link when available -->

Crawls your website and lists every **broken link, missing image, dead script or stylesheet and dead external link**, each with **the pages it appears on** and its anchor text, so you know exactly what to fix.

**Priced per page crawled, not per link.** A typical page has 50–150 links, so this costs far less than per-link checkers.

## What you can use it for
- **SEO cleanup:** find every internal 404 and dead external link before Google does, with the exact page and anchor text to fix.
- **Website migrations:** crawl the new site after a redesign or CMS move and catch links that still point to old URLs.
- **Agencies:** run a link audit for every client site on a monthly schedule and send the CSV to the content team.
- **Content teams and blogs:** find outbound links that rotted over the years (404, DNS errors, timeouts).
- **QA before launch:** check that images, scripts, stylesheets and iframes all load.

## How to use it
1. Add your site under **Start URLs** (you can add several sites; each is crawled separately).
2. Set **Max pages per site** to cap the crawl and the cost.
3. Click **Start**.
4. Open the results: one row per broken or blocked URL, with `foundOn` pages. Export to CSV or Excel.

## Features
- Stays on your domain (optionally includes subdomains) and follows internal links up to a depth limit.
- Checks `<a>` links, `<img>`, `<script>`, stylesheets, icons, `<iframe>`, `<video>`/`<audio>` sources, and external links.
- Verdicts: **broken** (4xx/5xx, DNS error, timeout), **blocked** (401/403/429: the server refused the checker, so the link may still work in a browser) and **ok**.
- Sends a HEAD request first and confirms with GET, which avoids false 404s from servers that mishandle HEAD. Each URL is checked only once per run.
- **Polite by design:** always respects robots.txt, allows at most 2 parallel requests per external host, and backs off on 429.
- Writes a summary record to the key-value store (`SUMMARY`): pages crawled, links checked, broken, blocked.

## Input
```json
{ "startUrls": [{"url": "https://example.com"}], "maxPagesPerSite": 200, "checkExternalLinks": true, "checkResources": true }
```
| Field | Default | Meaning |
|---|---|---|
| `startUrls` | – | One or more sites (each is crawled separately) |
| `maxPagesPerSite` | 200 | Upper limit on pages crawled, and so on cost |
| `checkExternalLinks` | true | Verify links to other domains |
| `checkResources` | true | Verify images, scripts, CSS, iframes and media |
| `includeWorkingLinks` | false | Also output working links |
| `includeSubdomains` | false | Treat `blog.example.com` as internal |
| `maxDepth` / `maxConcurrency` / `timeoutSecs` | 10 / 5 / 15 | Advanced |

## Output (one item per broken or blocked URL)
```json
{
  "verdict": "broken", "status": 404, "url": "https://example.com/old-pricing",
  "resourceType": "link", "internal": true,
  "foundOn": ["https://example.com/", "https://example.com/blog/launch"],
  "anchorTexts": ["See pricing"], "error": null, "site": "https://example.com/"
}
```
Export as CSV or Excel and hand it to whoever edits the site, or schedule a weekly run and get notified only when `broken > 0`.

## Pricing
Pay per event, no monthly rent: **$0.002 per page crawled** (**$2.00 per 1,000**).

| Example | Cost |
|---|---|
| 200 pages (a small site) | $0.40 |
| 1,000 pages | $2.00 |
| 10,000 pages | $20.00 |

You can set a **maximum cost per run** in the run options; the Actor stops cleanly when it is reached. New to Apify? The free plan includes $5 of platform credit every month, so you can try this Actor at no cost.

## API, integrations and AI agents (MCP)
Run it from your own code with the [Apify API](https://docs.apify.com/api/v2) and get the results in one call:
```bash
curl -X POST "https://api.apify.com/v2/acts/manageable_gully~broken-link-checker/run-sync-get-dataset-items?token=<YOUR_APIFY_TOKEN>" \
  -H "Content-Type: application/json" -d @input.json
```
```python
from apify_client import ApifyClient
run = ApifyClient("<YOUR_APIFY_TOKEN>").actor("manageable_gully/broken-link-checker").call(run_input={...})
```
- **No-code:** use the Apify app in **n8n, Make or Zapier** ("Run Actor", then "Get dataset items"), or send results to Google Sheets, Slack or a webhook.
- **AI agents (MCP):** add `https://mcp.apify.com?tools=manageable_gully/broken-link-checker` to Claude, Cursor, VS Code or any MCP client and the agent can call this Actor as a tool.
- **Schedules:** run it hourly, daily or weekly from Apify Console.

## FAQ
**Is it priced per link?** No. You pay per page crawled ($0.002). All links and resources on that page are checked at no extra cost, so a page with 150 links still costs $0.002.

**Can it check a list of URLs without crawling?** Set `maxDepth` to 0 to check only the links found on your start pages.

**Why "blocked" instead of "broken"?** Sites such as LinkedIn, Amazon and GitHub often refuse automated checkers (403/429). Those links usually work for people, so they are listed separately to avoid false alarms.

**Does it run JavaScript?** No. It reads server-rendered HTML, which is fast and cheap. Links that only appear after client-side JS runs are not discovered.

**Can I check someone else's site?** Only public pages, and only what robots.txt allows. The Actor never logs in or submits forms.

**Can AI agents use it?** Yes. It is available as a tool through the Apify MCP server (`https://mcp.apify.com?tools=manageable_gully/broken-link-checker`) and the Apify API, and it returns structured JSON that agents can read directly.

## More tools from WebIntel Tools
- [SEO Audit & Domain Checker](https://apify.com/manageable_gully/website-health-audit): SEO, DNS, SSL and security-header audit for lists of domains
- [Lighthouse & PageSpeed Bulk Audit](https://apify.com/manageable_gully/lighthouse-bulk-audit): Lighthouse scores and Core Web Vitals for hundreds of URLs
- [Web Page to Markdown](https://apify.com/manageable_gully/page-to-markdown): clean Markdown and RAG chunks from any URL, for LLMs
- [Website Tech Stack Detector](https://apify.com/manageable_gully/website-tech-detector): BuiltWith/Wappalyzer-style tech stack lookup in bulk

See [all WebIntel Tools Actors](https://apify.com/manageable_gully).

*Made by WebIntel Tools. This Actor was built and is maintained with AI assistance. Report issues on the Issues tab; they are monitored daily.*

## Run from source
This repository is the full source of the [Broken Link Checker & SEO Crawler: 404s, Images, Redirects](https://apify.com/manageable_gully/broken-link-checker) Actor.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest
# run locally with the Apify CLI (https://docs.apify.com/cli):
apify run --input '{...}'
```

Deploy your own copy with `apify push`. The easiest way to use it is the hosted version on the [Apify Store](https://apify.com/manageable_gully/broken-link-checker).

<!-- AFFILIATE_LINK_PLACEHOLDER: "New to Apify? Sign up here" link goes here -->

## License
MIT, see [LICENSE](LICENSE).
