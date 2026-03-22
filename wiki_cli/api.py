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
    """Resolve a query to a Wikipedia article and return the full article.

    Fetches the summary (for title, description, extract, content_urls) and
    the full HTML (for sections).  Falls back to a search on 404.

    The returned dict contains:
        - ``title``: article title
        - ``description``: short description
        - ``extract``: lead paragraph (from summary, kept as fallback)
        - ``content_urls``: dict with ``desktop.page`` URL
        - ``sections``: hierarchical list of section dicts, each containing
          ``id``, ``title``, ``level``, ``content``, and ``subsections``

    Args:
        query: Article title or search query.

    Returns:
        Full article dict.

    Raises:
        httpx.HTTPStatusError: On unrecoverable HTTP errors.
        httpx.RequestError: On network failures.
        ValueError: If no articles match the query.
    """
    # Step 1: get summary for metadata (title, description, urls)
    try:
        summary = get_summary(query)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        results = search(query, limit=1)
        if not results:
            raise ValueError(f"No Wikipedia article found for: {query!r}")
        summary = get_summary(results[0]["title"])

    # Step 2: fetch full HTML using the canonical title from the summary
    canonical_title = summary.get("title", query)
    try:
        html = _fetch_html(canonical_title)
        flat = _parse_sections(html)
        section_tree = _build_section_tree(flat)
    except (httpx.HTTPStatusError, httpx.RequestError):
        section_tree = []

    return {**summary, "sections": section_tree}


def _build_section_tree(flat_sections: list[dict]) -> list[dict]:
    """Build a hierarchical section tree from a flat section list.

    The lead section (empty title) is excluded.  Each node in the tree
    contains ``id``, ``title``, ``level``, ``content``, and ``subsections``.

    Args:
        flat_sections: Flat list as returned by :func:`_parse_sections`.

    Returns:
        List of top-level section dicts; sub-sections are nested under
        their parent's ``subsections`` key.
    """
    tree: list[dict] = []
    # ancestors tracks the chain of open parent nodes (most recent last)
    ancestors: list[dict] = []

    for s in flat_sections:
        if not s.get("title"):
            continue  # skip lead section

        node: dict = {
            "id": s.get("id", ""),
            "title": s["title"],
            "level": s["level"],
            "content": s["content"],
            "subsections": [],
        }

        # Pop ancestors that are at the same level or deeper (not parents)
        while ancestors and ancestors[-1]["level"] >= node["level"]:
            ancestors.pop()

        if ancestors:
            ancestors[-1]["subsections"].append(node)
        else:
            tree.append(node)

        ancestors.append(node)

    return tree


def flatten_sections(tree: list[dict]) -> list[dict]:
    """Flatten a hierarchical section tree back to a document-ordered list.

    The returned dicts do not include the ``subsections`` key.

    Args:
        tree: Hierarchical section list as returned by :func:`_build_section_tree`.

    Returns:
        Flat list of section dicts in document order.
    """
    result: list[dict] = []
    for section in tree:
        flat = {k: v for k, v in section.items() if k != "subsections"}
        result.append(flat)
        result.extend(flatten_sections(section.get("subsections", [])))
    return result


def _flatten_section_tree(tree: list[dict]) -> list[dict]:
    """Alias for :func:`flatten_sections` kept for internal use."""
    return flatten_sections(tree)


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
    """Parse Wikipedia article HTML into a flat list of section dicts.

    Each dict contains:
        - ``id``: anchor id from the heading element (empty for lead section)
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
    heading_id_re = re.compile(r'\bid="([^"]*)"', re.IGNORECASE)
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
        sections.append({"id": "", "title": "", "level": 0, "content": lead_text})

    for i, match in enumerate(headings):
        level = int(match.group(1)[1])
        heading_text = _extract_text(match.group(2))
        id_match = heading_id_re.search(match.group(0))
        section_id = id_match.group(1) if id_match else ""
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(clean)
        content_text = _extract_text(clean[start:end])
        sections.append(
            {
                "id": section_id,
                "title": heading_text,
                "level": level,
                "content": content_text,
            }
        )

    return sections


def get_sections(query: str) -> list[dict]:
    """Resolve a query to a Wikipedia article and return its flat section list.

    Attempts a direct title lookup first.  Falls back to a search and
    returns sections for the top result.

    Args:
        query: Article title or search query.

    Returns:
        Flat list of section dicts as returned by :func:`_parse_sections`.

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

    Each matched section also includes any immediately following subsections
    (sections with a higher heading level) up to the next sibling or parent.

    Args:
        sections: Flat section list as returned by :func:`get_sections` or
                  :func:`_flatten_section_tree`.
        queries:  One or more query strings to match against section titles.

    Returns:
        Filtered list of matching section dicts (with subsections) in
        document order.

    Raises:
        ValueError: If no sections match any of the given queries.
    """

    def _normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    normalised_queries = [_normalize(q) for q in queries]

    # Find directly-matched section indices (non-lead)
    matched_indices = [
        i
        for i, s in enumerate(sections)
        if s.get("title")
        and any(nq in _normalize(s["title"]) for nq in normalised_queries)
    ]

    if not matched_indices:
        raise ValueError(
            f"No sections found matching: {', '.join(repr(q) for q in queries)}"
        )

    # For each match, also collect immediately following subsections
    seen: set[int] = set()
    ordered: list[int] = []
    for idx in matched_indices:
        if idx not in seen:
            seen.add(idx)
            ordered.append(idx)
        base_level = sections[idx]["level"]
        for j in range(idx + 1, len(sections)):
            if sections[j]["level"] > base_level:
                if j not in seen:
                    seen.add(j)
                    ordered.append(j)
            else:
                break

    return [sections[i] for i in ordered]
