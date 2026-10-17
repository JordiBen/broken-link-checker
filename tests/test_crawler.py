import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from src.crawler import CrawlOptions, build_report, crawl, extract_links, is_internal, normalize_url, verdict
from src.main import parse_input

EXT = {}


def page(body):
    return f'<html><head><title>t</title><link rel="stylesheet" href="/style.css"></head><body>{body}</body></html>'


def make_handler(pages):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body=b'', ctype='text/html', head=False, extra=None):
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)

        def route(self, head):
            p = self.path
            if p == '/nohead' and head:
                return self._send(405, head=True)
            if p in pages:
                code, body, ctype, extra = pages[p]
                return self._send(code, body.encode() if isinstance(body, str) else body, ctype, head, extra)
            return self._send(404, b'not found', head=head)

        def do_GET(self):
            self.route(False)

        def do_HEAD(self):
            self.route(True)
    return H


def serve(handler):
    srv = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


@pytest.fixture(scope='module')
def site():
    ext = serve(make_handler({'/alive': (200, 'ok', 'text/plain', None)}))
    ext_base = f'http://localhost:{ext.server_address[1]}'
    pages = {
        '/': (200, page(f'''<a href="/a">A</a> <a href="/b#section">B</a> <a href="/missing">Missing page</a>
              <a href="/private/x">P</a> <a href="mailto:x@y.z">mail</a> <a href="#top">top</a>
              <img src="/img.png" alt="ok"> <img src="/broken.png" alt="Broken pic">
              <a href="{ext_base}/alive">ext ok</a> <a href="{ext_base}/dead">ext dead</a>
              <a href="/redirect">R</a> <a href="/nohead">NH</a>'''), 'text/html', None),
        '/a': (200, page('<a href="/">home</a> <a href="/deep1">d1</a>'), 'text/html', None),
        '/b': (200, page('<a href="/a">again A</a> <a href="/missing">Missing again</a>'), 'text/html', None),
        '/deep1': (200, page('<a href="/deep2">d2</a>'), 'text/html', None),
        '/deep2': (200, page('<a href="/gone-deep">gone</a>'), 'text/html', None),
        '/redirect': (301, '', 'text/html', {'Location': '/b'}),
        '/nohead': (200, 'fine', 'text/plain', None),
        '/img.png': (200, b'\x89PNG', 'image/png', None),
        '/style.css': (200, 'body{}', 'text/css', None),
        '/robots.txt': (200, 'User-agent: *\nDisallow: /private/\n', 'text/plain', None),
        '/private/x': (200, page('<a href="/private-leak">secret</a>'), 'text/html', None),
    }
    srv = serve(make_handler(pages))
    yield f'http://127.0.0.1:{srv.server_address[1]}', ext_base
    srv.shutdown(); ext.shutdown()


def run(start, **kw):
    async def go():
        opts = CrawlOptions(allow_private=True, timeout_s=5, **kw)
        async with httpx.AsyncClient(timeout=5) as c:
            return await crawl(start, opts, c)
    return asyncio.run(go())


def test_normalize_and_internal():
    assert normalize_url('/x#frag', 'https://Ex.com/a/') == 'https://ex.com/x'
    assert normalize_url('mailto:a@b.c', 'https://ex.com') is None
    assert normalize_url('javascript:void(0)', 'https://ex.com') is None
    assert normalize_url('https://ex.com:443/p?q=1', 'https://ex.com') == 'https://ex.com/p?q=1'
    assert is_internal('https://www.ex.com/x', 'ex.com', False)
    assert not is_internal('https://blog.ex.com/x', 'ex.com', False)
    assert is_internal('https://blog.ex.com/x', 'ex.com', True)


def test_extract_links_types():
    html = '<base href="https://cdn.x/"><a href="p">P</a><img src="i.png" alt="pic"><script src="s.js"></script><link rel="icon" href="f.ico">'
    got = {(u, t) for u, t, _ in extract_links(html, 'https://x.com/', True)}
    assert ('https://cdn.x/p', 'link') in got and ('https://cdn.x/i.png', 'image') in got
    assert ('https://cdn.x/s.js', 'script') in got and ('https://cdn.x/f.ico', 'icon') in got
    assert {t for _, t, _ in extract_links(html, 'https://x.com/', False)} == {'link'}


def test_verdicts():
    assert verdict(200, None) == 'ok' and verdict(404, None) == 'broken' and verdict(403, None) == 'blocked'
    assert verdict(None, 'timeout') == 'broken'


def test_full_crawl(site):
    base, ext = site
    res = run(base + '/')
    rows, summary = build_report(res)
    broken = {r['url']: r for r in rows if r['verdict'] == 'broken'}
    assert base + '/missing' in broken and broken[base + '/missing']['status'] == 404
    assert sorted(broken[base + '/missing']['foundOn']) == sorted([base + '/', base + '/b'])
    assert 'Missing page' in broken[base + '/missing']['anchorTexts']
    assert base + '/broken.png' in broken and broken[base + '/broken.png']['resourceType'] == 'image'
    assert ext + '/dead' in broken and broken[ext + '/dead']['internal'] is False
    assert base + '/gone-deep' in broken
    assert base + '/nohead' not in broken          # HEAD 405 -> GET fallback succeeds
    assert ext + '/alive' not in broken
    assert base + '/private-leak' not in res['results']  # robots.txt respected, page never fetched
    assert summary['pagesSkippedByRobots'] == 1 and summary['robotsTxtUsed']
    assert summary['broken'] == 4 and summary['pagesCrawled'] == 5  # /, /a, /b, /deep1, /deep2
    assert not any('mailto' in u for u in res['links'])


def test_max_pages_and_depth(site):
    base, _ = site
    res = run(base + '/', max_pages=2)
    assert sum(1 for p in res['pages'] if p.get('status')) == 2
    res = run(base + '/', max_depth=0)
    assert [p['url'] for p in res['pages'] if p.get('status')] == [base + '/']


def test_external_off(site):
    base, ext = site
    res = run(base + '/', check_external=False)
    assert ext + '/dead' not in res['results']


def test_on_page_stop(site):
    base, _ = site
    calls = []

    async def go():
        async def on_page(u):
            calls.append(u)
            return len(calls) < 2
        async with httpx.AsyncClient(timeout=5) as c:
            return await crawl(base + '/', CrawlOptions(allow_private=True, concurrency=1), c, on_page=on_page)
    res = asyncio.run(go())
    assert res['stoppedEarly'] and len(calls) == 2


def test_private_blocked_by_default(site):
    base, _ = site
    async def go():
        async with httpx.AsyncClient(timeout=5) as c:
            return await crawl(base + '/', CrawlOptions(), c)
    with pytest.raises(Exception, match='non-public'):
        asyncio.run(go())


def test_parse_input():
    starts, opts, inc = parse_input({'startUrls': [{'url': 'example.com'}, {'url': 'https://example.com/'}], 'maxConcurrency': 99})
    assert starts == ['https://example.com/'] and opts.concurrency == 20 and opts.respect_robots and not inc
    with pytest.raises(ValueError):
        parse_input({'startUrls': []})
