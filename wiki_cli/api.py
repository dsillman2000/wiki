"""Wikipedia REST API client using HTTPX."""

from __future__ import annotations

import html as _html_module
import re

import httpx

USER_AGENT = "wiki-cli/1.0 (+https://github.com/dsillman2000/wiki)"

_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_HTML_URL = "https://en.wikipedia.org/api/rest_v1/page/html/{title}"
_SEARCH_URL = "https://en.wikipedia.org/w/api.php"


def get_summary(title: str) -> dict:
    """Fetch the summary for a Wikipedia article by exact title.

    Args:
        title: The Wikipedia article title (URL-encoded automatically).

    Returns:
        Parsed JSON response from the REST v1 summary endpoint.

    Raises:
        httpx.HTTPStatusError: On 4xx/5xx responses.
        httpx.RequestError: On network failures.
    """
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        response = client.get(_SUMMARY_URL.format(title=title))
        response.raise_for_status()
        return response.json()


def search(query: str, limit: int = 10) -> list[dict]:
    """Search Wikipedia and return a list of result dicts.

    Each result dict contains at least:
        - ``title``: article title
        - ``snippet``: short text excerpt
        - ``url``: full Wikipedia article URL

    Args:
        query: Search query string.
        limit: Maximum number of results to return (default 10).

    Returns:
        List of search result dicts.

    Raises:
        httpx.HTTPStatusError: On 4xx/5xx responses.
        httpx.RequestError: On network failures.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "srprop": "snippet",
    }
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        response = client.get(_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("query", {}).get("search", []):
        results.append(
            {
                "title": item.get("title", ""),
                "snippet": _strip_html(item.get("snippet", "")),
                "url": (
                    "https://en.wikipedia.org/wiki/"
                    + item.get("title", "").replace(" ", "_")
                ),
            }
        )
    return results


def fetch_article(query: str) -> dict:
    """Resolve a query to a Wikipedia article and return its summary.

    Attempts a direct title lookup first.  Falls back to a search and
    returns the summary for the top result.

    Args:
        query: Article title or search query.

    Returns:
        Summary dict as returned by :func:`get_summary`.

    Raises:
        httpx.HTTPStatusError: On unrecoverable HTTP errors.
        httpx.RequestError: On network failures.
        ValueError: If no articles match the query.
    """
    try:
        return get_summary(query)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise

    # Fall back to search
    results = search(query, limit=1)
    if not results:
        raise ValueError(f"No Wikipedia article found for: {query!r}")
    return get_summary(results[0]["title"])


def _strip_html(text: str) -> str:
    """Remove simple HTML tags from a snippet string."""
    return re.sub(r"<[^>]+>", "", text)


def _fetch_html(title: str) -> str:
    """Fetch the full HTML of a Wikipedia article by exact title.

    Args:
        title: The Wikipedia article title (URL-encoded automatically).

    Returns:
        Raw HTML string from the REST v1 html endpoint.

    Raises:
        httpx.HTTPStatusError: On 4xx/5xx responses.
        httpx.RequestError: On network failures.
    """
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        response = client.get(_HTML_URL.format(title=title))
        response.raise_for_status()
        return response.text


def _parse_sections(html_content: str) -> list[dict]:
    """Parse Wikipedia article HTML into a list of section dicts.

    Each dict contains:
        - ``title``: section heading text (empty string for the lead section)
        - ``level``: heading level (0 for lead, 2–6 for h2–h6)
        - ``content``: plain-text content of the section

    Args:
        html_content: Raw HTML string from the Wikipedia REST API.

    Returns:
        List of section dicts in document order, lead section first.
    """
    # Remove script/style/sup elements (footnote markers, etc.)
    clean = re.sub(
        r"<(script|style|sup)[^>]*>.*?</\1>",
        "",
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Remove edit-section spans inserted by MediaWiki
    clean = re.sub(
        r'<span[^>]*class="mw-editsection"[^>]*>.*?</span>',
        "",
        clean,
        flags=re.DOTALL | re.IGNORECASE,
    )

    heading_re = re.compile(r"<(h[1-6])[^>]*>(.*?)</\1>", re.DOTALL | re.IGNORECASE)
    tag_re = re.compile(r"<[^>]+>")

    def _extract_text(fragment: str) -> str:
        text = tag_re.sub("", fragment)
        text = _html_module.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    headings = list(heading_re.finditer(clean))
    sections: list[dict] = []

    # Lead section (content before the first heading)
    lead_html = clean[: headings[0].start()] if headings else clean
    lead_text = _extract_text(lead_html)
    if lead_text:
        sections.append({"title": "", "level": 0, "content": lead_text})

    for i, match in enumerate(headings):
        level = int(match.group(1)[1])
        heading_text = _extract_text(match.group(2))
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(clean)
        content_text = _extract_text(clean[start:end])
        sections.append(
            {"title": heading_text, "level": level, "content": content_text}
        )

    return sections


def get_sections(query: str) -> list[dict]:
    """Resolve a query to a Wikipedia article and return its sections.

    Attempts a direct title lookup first.  Falls back to a search and
    returns sections for the top result.

    Args:
        query: Article title or search query.

    Returns:
        List of section dicts as returned by :func:`_parse_sections`.

    Raises:
        httpx.HTTPStatusError: On unrecoverable HTTP errors.
        httpx.RequestError: On network failures.
        ValueError: If no articles match the query.
    """
    try:
        html = _fetch_html(query)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        results = search(query, limit=1)
        if not results:
            raise ValueError(f"No Wikipedia article found for: {query!r}")
        html = _fetch_html(results[0]["title"])
    return _parse_sections(html)


def filter_sections(sections: list[dict], queries: tuple[str, ...]) -> list[dict]:
    """Return sections whose titles fuzzy-match any entry in *queries*.

    Matching is case-insensitive substring after normalising to lowercase
    alphanumeric characters (spaces and punctuation are ignored).  The lead
    section (empty title) is always excluded.

    Args:
        sections: List of section dicts as returned by :func:`get_sections`.
        queries:  One or more query strings to match against section titles.

    Returns:
        Filtered list of matching section dicts.

    Raises:
        ValueError: If no sections match any of the given queries.
    """

    def _normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    normalised_queries = [_normalize(q) for q in queries]
    result = [
        s
        for s in sections
        if s["title"]
        and any(nq in _normalize(s["title"]) for nq in normalised_queries)
    ]
    if not result:
        raise ValueError(
            f"No sections found matching: {', '.join(repr(q) for q in queries)}"
        )
    return result
