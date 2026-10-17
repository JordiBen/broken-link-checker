"""Apify entrypoint: crawl a website and report broken links, images, scripts and stylesheets."""
from __future__ import annotations

import os

import httpx
from apify import Actor

from .crawler import USER_AGENT, CrawlOptions, build_report, crawl, normalize_url

EVENT = 'page-crawled'


def parse_input(inp: dict) -> tuple[list[str], CrawlOptions, bool]:
    urls = [s.get('url') if isinstance(s, dict) else s for s in (inp.get('startUrls') or [])]
    urls = [u.strip() if '://' in u.strip() else 'https://' + u.strip() for u in urls if u and u.strip()]
    starts = []
    for u in urls:
        n = normalize_url(u, u)
        if n and n not in starts:
            starts.append(n)
    if not starts:
        raise ValueError('Provide at least one website URL in "startUrls".')
    opts = CrawlOptions(
        max_pages=int(min(max(inp.get('maxPagesPerSite', 200), 1), 20_000)),
        max_depth=int(min(max(inp.get('maxDepth', 10), 0), 50)),
        check_external=bool(inp.get('checkExternalLinks', True)),
        check_resources=bool(inp.get('checkResources', True)),
        respect_robots=True,  # always on: we only crawl what the site allows
        concurrency=int(min(max(inp.get('maxConcurrency', 5), 1), 20)),
        timeout_s=float(min(max(inp.get('timeoutSecs', 15), 3), 60)),
        include_subdomains=bool(inp.get('includeSubdomains', False)),
    )
    return starts, opts, bool(inp.get('includeWorkingLinks', False))


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        try:
            starts, opts, include_ok = parse_input(inp)
        except ValueError as e:
            await Actor.fail(status_message=str(e))
            return
        if os.environ.get('ALLOW_PRIVATE_NETWORK_FOR_LOCAL_DEV') == '1' and not Actor.is_at_home():
            opts.allow_private = True

        budget_hit = False
        summaries = []
        async with httpx.AsyncClient(timeout=opts.timeout_s, headers={'User-Agent': USER_AGENT},
                                     limits=httpx.Limits(max_connections=opts.concurrency * 4)) as client:
            for start in starts:
                if budget_hit:
                    break
                pages_done = 0

                async def on_page(url: str) -> bool:
                    nonlocal budget_hit, pages_done
                    res = await Actor.charge(EVENT)
                    if res.charged_count == 0 and res.event_charge_limit_reached:
                        budget_hit = True
                        return False
                    pages_done += 1
                    if pages_done % 20 == 0:
                        await Actor.set_status_message(f'{start}: {pages_done} pages crawled')
                    if res.event_charge_limit_reached:
                        budget_hit = True
                        return False
                    return True

                Actor.log.info(f'Crawling {start} (max {opts.max_pages} pages)')
                try:
                    result = await crawl(start, opts, client, on_page=on_page)
                except Exception as e:  # noqa: BLE001
                    Actor.log.warning(f'{start}: {type(e).__name__}: {e}')
                    summaries.append({'startUrl': start, 'error': f'{type(e).__name__}: {e}'[:300]})
                    continue
                rows, summary = build_report(result, include_ok=include_ok)
                for r in rows:
                    r['site'] = start
                if rows:
                    await Actor.push_data(rows)
                summary['startUrl'] = start
                summaries.append(summary)
                Actor.log.info(f'{start}: {summary}')

        await Actor.set_value('SUMMARY', summaries)
        total_broken = sum(s.get('broken', 0) for s in summaries)
        msg = f'Done: {len(summaries)} site(s), {total_broken} broken link(s) found'
        if budget_hit:
            msg += ' (stopped: max charge reached)'
        await Actor.set_status_message(msg, is_terminal=True)
