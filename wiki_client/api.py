"""Wikipedia REST API client using HTTPX."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

USER_AGENT = "wiki-client/1.0 (+https://github.com/dsillman2000/wiki-cli)"

_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_HTML_URL = "https://en.wikipedia.org/api/rest_v1/page/html/{title}"
_SEARCH_URL = "https://en.wikipedia.org/w/api.php"

# Heading tag names used for BeautifulSoup tree searches
_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
_HEADING_TAG_RE = re.compile(r"^h[1-6]$", re.IGNORECASE)


def _url_to_title(query: str) -> str | None:
    """Extract an article title from a Wikipedia URL.

    Supports URLs of the form
    ``https://en.wikipedia.org/wiki/Article_Title``.

    Args:
        query: Arbitrary string that may or may not be a Wikipedia URL.

    Returns:
        The decoded article title (underscores replaced with spaces), or
        *None* if *query* is not a recognisable Wikipedia wiki URL.
    """
    try:
        parsed = urlparse(query)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    if "wikipedia.org" not in (parsed.netloc or ""):
        return None
    path = parsed.path or ""
    if not path.startswith("/wiki/"):
        return None
    raw_title = path.removeprefix("/wiki/")
    if not raw_title:
        return None
    return unquote(raw_title).replace("_", " ")


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
    # Resolve Wikipedia URLs to article titles transparently
    title_from_url = _url_to_title(query)
    if title_from_url:
        query = title_from_url

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
            "tables": s.get("tables", []),
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
    """Remove HTML tags from a snippet string using BeautifulSoup."""
    return BeautifulSoup(text, "html.parser").get_text()


def _direct_rows(table: Tag) -> list[Tag]:
    """Return direct ``<tr>`` children of *table*, accounting for wrappers.

    Handles tables with or without ``<tbody>``/``<thead>``/``<tfoot>`` wrappers
    so that rows from nested tables inside cells are never included.

    Args:
        table: A BS4 ``<table>`` Tag.

    Returns:
        Ordered list of direct ``<tr>`` Tags belonging to *table* itself.
    """
    rows: list[Tag] = []
    for child in table.children:
        if not isinstance(child, Tag):
            continue
        if child.name == "tr":
            rows.append(child)
        elif child.name in ("tbody", "thead", "tfoot"):
            rows.extend(child.find_all("tr", recursive=False))
    return rows


def _parse_tables(html_or_tag: str | Tag) -> list[dict]:
    """Parse ``<table class="wikitable">`` elements using BeautifulSoup.

    Replaces the previous regex-based approach with proper HTML tree
    traversal, correctly handling nested tags, malformed markup, and
    tables-within-cells.

    Each returned dict contains:
        - ``caption``: table caption text (empty string if absent)
        - ``headers``: list of header cell strings (empty if no ``<th>`` row)
        - ``rows``: list of data rows, each a list of cell strings

    Cells are plain text — all HTML tags are stripped and entities decoded.
    Nested tables inside cells are removed before text extraction.

    Args:
        html_or_tag: Raw HTML string or BS4 Tag to search for wikitables.

    Returns:
        List of table dicts in document order.
    """
    if isinstance(html_or_tag, Tag):
        root: BeautifulSoup | Tag = html_or_tag
    else:
        root = BeautifulSoup(html_or_tag, "html.parser")

    def _cell_text(cell: Tag) -> str:
        # Remove nested tables so their text does not bleed into the cell
        for nested in cell.find_all("table"):
            nested.decompose()
        return re.sub(r"\s+", " ", cell.get_text(separator=" ")).strip()

    tables: list[dict] = []
    for table in root.select("table.wikitable"):
        cap_tag = table.find("caption")
        caption = _cell_text(cap_tag) if cap_tag else ""

        headers: list[str] = []
        rows: list[list[str]] = []

        for tr in _direct_rows(table):
            th_cells = tr.find_all("th", recursive=False)
            td_cells = tr.find_all("td", recursive=False)

            if th_cells and not td_cells:
                # Pure header row — use the first such row as column headers
                if not headers:
                    headers = [_cell_text(th) for th in th_cells]
            elif td_cells:
                rows.append([_cell_text(td) for td in td_cells])

        if headers or rows:
            tables.append({"caption": caption, "headers": headers, "rows": rows})

    return tables


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

    Uses BeautifulSoup for reliable parsing of headings, tables, and content,
    replacing the previous fragile regex-based approach.  Handles both
    Wikipedia REST-API HTML (``<section data-mw-section-id="N">`` elements)
    and plain heading-based HTML via a fallback path.

    Each dict contains:
        - ``id``: anchor id from the heading element (empty for lead section)
        - ``title``: section heading text (empty string for the lead section)
        - ``level``: heading level (0 for lead, 2–6 for h2–h6)
        - ``content``: plain-text content of the section (tables excluded)
        - ``tables``: list of table dicts parsed by :func:`_parse_tables`

    Args:
        html_content: Raw HTML string from the Wikipedia REST API.

    Returns:
        List of section dicts in document order, lead section first.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove noisy elements: footnote markers, scripts, styles, edit links
    for tag in soup.find_all(["script", "style", "sup"]):
        tag.decompose()
    for span in soup.find_all("span", class_="mw-editsection"):
        span.decompose()

    def _make_entry(section_id: str, title: str, level: int, html: str) -> dict:
        """Build a section entry dict from raw HTML content."""
        # Parse once; _parse_tables decomposes nested tables inside cells but
        # leaves the wikitables themselves intact, so we can still remove them
        # afterward for plain-text extraction.
        entry_soup = BeautifulSoup(html, "html.parser")
        tables = _parse_tables(entry_soup)
        for tbl in entry_soup.find_all("table"):
            tbl.decompose()
        content = re.sub(r"\s+", " ", entry_soup.get_text(separator=" ")).strip()
        return {
            "id": section_id,
            "title": title,
            "level": level,
            "content": content,
            "tables": tables,
        }

    sections: list[dict] = []

    # Primary path: Wikipedia REST API wraps each section in
    # <section data-mw-section-id="N"> elements.
    section_els = soup.find_all("section", attrs={"data-mw-section-id": True})
    if section_els:
        for section_el in section_els:
            heading = section_el.find(_HEADING_TAG_RE)
            if heading:
                level = int(heading.name[1])
                title = heading.get_text(strip=True)
                section_id = heading.get("id", "")
                heading.decompose()
            else:
                level = 0
                title = ""
                section_id = ""
            entry = _make_entry(section_id, title, level, str(section_el))
            if entry["content"] or entry["tables"]:
                sections.append(entry)
        return sections

    # Fallback: flat HTML where headings and content are sibling elements
    # (e.g. plain Wikipedia article HTML without <section> wrappers).
    root = soup.find("body") or soup
    current_heading: Tag | None = None
    current_content: list[str] = []
    groups: list[tuple[Tag | None, list[str]]] = []

    for child in root.children:
        if isinstance(child, Tag) and child.name in _HEADING_TAGS:
            groups.append((current_heading, current_content))
            current_heading = child
            current_content = []
        else:
            current_content.append(str(child))
    groups.append((current_heading, current_content))

    for heading, content_parts in groups:
        content_html = "".join(content_parts)
        if heading is not None:
            level = int(heading.name[1])
            title = heading.get_text(strip=True)
            section_id = heading.get("id", "")
        else:
            level = 0
            title = ""
            section_id = ""
        entry = _make_entry(section_id, title, level, content_html)
        if entry["content"] or entry["tables"]:
            sections.append(entry)

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
    # Resolve Wikipedia URLs to article titles transparently
    title_from_url = _url_to_title(query)
    if title_from_url:
        query = title_from_url

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
