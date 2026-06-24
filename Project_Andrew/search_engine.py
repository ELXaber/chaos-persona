#V06232026
# =============================================================================
# CAIOS — Search Engine (DuckDuckGo, stdlib only)
#
# Provides web search capability for epistemic gap resolution.
# Integrates with tool_dispatcher.py via [TOOL:web_search query="..." n="5"]
# and with os_control.py's fetch_url for full-page extraction on results.
#
# Architecture:
#   1. DDG Instant Answer API  — structured JSON, fast, rate-limit friendly
#   2. DDG HTML lite fallback  — scrapes lite.duckduckgo.com if API returns empty
#   3. Results feed into shared_memory['last_search_results'] for orchestrator
#      to pass URLs downstream to os_control.fetch_url / caios_mcp_client.scrape
#
# Zero external dependencies — urllib only.
# =============================================================================

import re
import json
import urllib.request
import urllib.parse
import urllib.error
import html
from typing import List, Dict, Optional, Any

# ── Constants ─────────────────────────────────────────────────
DDG_API_URL  = 'https://api.duckduckgo.com/'
DDG_LITE_URL = 'https://lite.duckduckgo.com/lite/'
TIMEOUT      = 10  # seconds

# Plausible browser UA — DDG blocks obvious bot strings
_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/125.0.0.0 Safari/537.36'
)

# HTML entities we want decoded in snippets
_ENTITY_RE = re.compile(r'&[a-zA-Z]+;|&#\d+;')


# =============================================================================
# Internal helpers
# =============================================================================

def _clean(text: str) -> str:
    """Decode HTML entities and collapse whitespace."""
    return re.sub(r'\s+', ' ', html.unescape(text)).strip()


def _get(url: str, data: Optional[bytes] = None) -> Optional[str]:
    """
    Simple GET/POST with browser UA.
    Returns decoded response body or None on any failure.
    """
    req = urllib.request.Request(
        url, data=data,
        headers={'User-Agent': _UA, 'Accept-Language': 'en-US,en;q=0.9'},
        method='POST' if data else 'GET'
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


# =============================================================================
# Strategy 1 — DDG Instant Answer API (JSON, rate-limit friendly)
# =============================================================================

def _search_api(query: str, max_results: int) -> List[Dict]:
    """
    Queries the DDG Instant Answer API.
    Returns RelatedTopics as structured results.
    Good for factual/definitional queries; thinner on news/current events.
    """
    params = urllib.parse.urlencode({
        'q': query,
        'format': 'json',
        'no_html': '1',
        'skip_disambig': '1'
    })
    body = _get(f'{DDG_API_URL}?{params}')
    if not body:
        return []

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return []

    results = []

    # Abstract (the direct answer block, if DDG has one)
    abstract = _clean(data.get('AbstractText', ''))
    abstract_url = data.get('AbstractURL', '')
    if abstract and abstract_url:
        results.append({
            'title':   _clean(data.get('Heading', query)),
            'url':     abstract_url,
            'snippet': abstract,
            'source':  'ddg_abstract'
        })

    # RelatedTopics — the bulk of results
    for item in data.get('RelatedTopics', []):
        if len(results) >= max_results:
            break
        # Some items are group headers, not results
        if 'Topics' in item:
            for sub in item['Topics']:
                if len(results) >= max_results:
                    break
                url  = sub.get('FirstURL', '')
                text = _clean(sub.get('Text', ''))
                if url and text:
                    results.append({
                        'title':   text[:80],
                        'url':     url,
                        'snippet': text,
                        'source':  'ddg_api'
                    })
        else:
            url  = item.get('FirstURL', '')
            text = _clean(item.get('Text', ''))
            if url and text:
                results.append({
                    'title':   text[:80],
                    'url':     url,
                    'snippet': text,
                    'source':  'ddg_api'
                })

    return results


# =============================================================================
# Strategy 2 — DDG HTML lite fallback
# =============================================================================

# lite.duckduckgo.com is simpler HTML than the main page and more stable to parse
_LITE_RESULT_RE = re.compile(
    r'<a[^>]+class="result-link"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
    r'.*?<td[^>]+class="result-snippet"[^>]*>(.*?)</td>',
    re.DOTALL
)

def _search_lite(query: str, max_results: int) -> List[Dict]:
    """
    Scrapes lite.duckduckgo.com as a fallback when the API returns thin results.
    More likely to have current-events and news results.
    """
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    body = _get(DDG_LITE_URL, data=data)
    if not body:
        return []

    results = []
    for m in _LITE_RESULT_RE.finditer(body):
        if len(results) >= max_results:
            break
        url     = _clean(m.group(1))
        title   = _clean(m.group(2))
        snippet = _clean(re.sub(r'<[^>]+>', '', m.group(3)))
        if url.startswith('http') and title:
            results.append({
                'title':   title,
                'url':     url,
                'snippet': snippet,
                'source':  'ddg_lite'
            })

    return results


# =============================================================================
# Public interface
# =============================================================================

def search(
    query: str,
    max_results: int = 5,
    shared_memory: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point. Tries the DDG API first, falls back to lite scraping
    if results are thin (< 2 items), returns a standardised result dict.

    Result dict:
      {
        'status':  'success' | 'empty' | 'error',
        'query':   str,
        'results': [{'title', 'url', 'snippet', 'source'}, ...],
        'urls':    [str, ...]   # flat list for easy downstream fetch_url use
      }

    Stores results in shared_memory['last_search_results'] if provided,
    so the orchestrator can pass URLs to os_control.fetch_url automatically.
    """
    if not query or not query.strip():
        return {'status': 'error', 'query': query, 'results': [], 'urls': [],
                'error': 'Empty query'}

    results = _search_api(query, max_results)

    # Fall back to lite scraping if API gave us fewer than 2 results
    if len(results) < 2:
        lite = _search_lite(query, max_results)
        # Merge, deduplicate by URL
        seen = {r['url'] for r in results}
        for r in lite:
            if r['url'] not in seen:
                results.append(r)
                seen.add(r['url'])
        results = results[:max_results]

    urls = [r['url'] for r in results]

    payload = {
        'status':  'success' if results else 'empty',
        'query':   query,
        'results': results,
        'urls':    urls,
    }

    if shared_memory is not None:
        shared_memory['last_search_results'] = payload
        # Also push into domain heat so CPOL curiosity engine can see it
        shared_memory.setdefault('domain_heat', {})
        shared_memory['domain_heat']['web_search'] = min(
            1.0,
            shared_memory['domain_heat'].get('web_search', 0.0) + 0.15
        )

    return payload


def format_results_for_llm(search_payload: Dict) -> str:
    """
    Formats search results into a compact string for injection into the
    LLM prompt (fits inside [RECENT_CONTEXT] or the enriched_query block).
    """
    if search_payload.get('status') != 'success':
        return f"[SEARCH] No results found for: {search_payload.get('query', '')}"

    lines = [f"[SEARCH RESULTS for: {search_payload['query']}]"]
    for i, r in enumerate(search_payload['results'], 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        if r['snippet']:
            lines.append(f"   {r['snippet'][:200]}")
    lines.append('[/SEARCH RESULTS]')
    return '\n'.join(lines)


# =============================================================================
# Factory — matches CAIOS module pattern
# =============================================================================

def create_search_engine(shared_memory: Optional[Dict] = None):
    """
    Returns a bound search callable with shared_memory pre-filled.
    Usage in orchestrator:
        searcher = create_search_engine(shared_memory)
        results  = searcher('quantum error correction')
    """
    def _search(query: str, max_results: int = 5) -> Dict:
        return search(query, max_results=max_results, shared_memory=shared_memory)
    return _search


# =============================================================================
# Test suite
# =============================================================================

if __name__ == '__main__':
    print('=' * 60)
    print('  CAIOS Search Engine — Test Suite')
    print('=' * 60)

    mock_memory = {'domain_heat': {}}

    # Test 1: Normal factual query (API likely has an abstract)
    print('\n[TEST 1] Factual query')
    r1 = search('Python programming language', max_results=3,
                shared_memory=mock_memory)
    print(f"  Status:  {r1['status']}")
    print(f"  Results: {len(r1['results'])}")
    for res in r1['results']:
        print(f"  - [{res['source']}] {res['title'][:60]}")
        print(f"    {res['url']}")

    # Test 2: Current-events query (API thin, lite fallback expected)
    print('\n[TEST 2] Current-events query (lite fallback)')
    r2 = search('latest AI research 2026', max_results=5,
                shared_memory=mock_memory)
    print(f"  Status:  {r2['status']}")
    print(f"  Results: {len(r2['results'])}")
    sources = {res['source'] for res in r2['results']}
    print(f"  Sources used: {sources}")

    # Test 3: LLM formatting
    print('\n[TEST 3] LLM prompt formatting')
    formatted = format_results_for_llm(r2)
    print(formatted[:400])

    # Test 4: Empty query guard
    print('\n[TEST 4] Empty query guard')
    r4 = search('', max_results=3)
    print(f"  Status: {r4['status']} (expected: error)")

    # Test 5: shared_memory side-effects
    print('\n[TEST 5] shared_memory update')
    print(f"  last_search_results set: {'last_search_results' in mock_memory}")
    print(f"  domain_heat['web_search']: {mock_memory['domain_heat'].get('web_search', 0):.2f}")

    print('\n' + '=' * 60)
    print('  One is glad to be of service.')
    print('=' * 60)
