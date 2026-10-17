# Broken Link Checker: 404s, Broken Images & Redirects

[![Run on Apify](https://img.shields.io/badge/Run%20on-Apify-1f6feb?logo=apify)](https://apify.com/manageable_gully/broken-link-checker) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Run it in the cloud with no setup:** [Broken Link Checker: 404s, Broken Images & Redirects on the Apify Store](https://apify.com/manageable_gully/broken-link-checker).  
> Pay only per result, export to JSON/CSV/Excel, schedule runs and call it from the API.
<!-- Note: the Apify Store page goes live once the Actor is published. -->
<!-- AFFILIATE_LINK_PLACEHOLDER: replace the Apify links above with the affiliate link when available -->

Crawls your website and lists every **broken link, missing image, dead script or stylesheet and dead external link**, each with **the pages it appears on** and its anchor text, so you know exactly what to fix.

**Priced per page crawled, not per link.** A typical page has 50–150 links, so this costs far less than per-link checkers.

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
Pay per event: **$0.002 per page crawled**. The link checks on that page are included. For example, a 200-page site costs about $0.40. Set "max cost per run" and the crawl stops cleanly at your budget.

## FAQ
**Why "blocked" instead of "broken"?** Sites such as LinkedIn, Amazon and GitHub often refuse automated checkers (403/429). Those links usually work for people, so they are listed separately to avoid false alarms.
**Does it run JavaScript?** No. It reads server-rendered HTML, which is fast and cheap. Links that only appear after client-side JS runs are not discovered.
**Can I check someone else's site?** Only public pages, and only what robots.txt allows. The Actor never logs in or submits forms.

*This Actor was built and is maintained with AI assistance. Report issues on the Issues tab; they are monitored daily.*

## Run from source
This repository is the full source of the [Broken Link Checker: 404s, Broken Images & Redirects](https://apify.com/manageable_gully/broken-link-checker) Actor.

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
