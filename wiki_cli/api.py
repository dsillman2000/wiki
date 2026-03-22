"""Wikipedia REST API client using HTTPX."""

from __future__ import annotations

import re

import httpx

USER_AGENT = "wiki-cli/1.0 (+https://github.com/dsillman2000/wiki)"

_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
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
