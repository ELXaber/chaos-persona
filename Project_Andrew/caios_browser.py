#V03232026
def fetch_structured(url: str) -> Dict:
    """
    Agent-optimized page fetcher.
    Returns semantic structure not visual layout.
    No screenshots. No coordinates. No tooltips.
    """
    raw = requests.get(url, headers=agent_headers)

    return {
        'title': extract_title(raw),
        'main_content': extract_body(raw),
        'links': extract_links(raw),
        'forms': extract_forms(raw),
        'metadata': extract_meta(raw),
        'structured_data': extract_json_ld(raw)
    }