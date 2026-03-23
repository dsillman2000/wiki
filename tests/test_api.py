"""Unit tests for wiki_client.api."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from wiki_client import api

SAMPLE_SUMMARY = {
    "title": "Unix shell",
    "description": "Type of command-line interface",
    "extract": (
        "A Unix shell is a command-line interpreter that provides a user interface."
    ),
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Unix_shell"}},
}

SAMPLE_SEARCH_RESPONSE = {
    "query": {
        "search": [
            {
                "title": "Unix shell",
                "snippet": "A <span>Unix shell</span> is a command-line interpreter",
            },
            {
                "title": "Bash (Unix shell)",
                "snippet": "<span>Bash</span> is a Unix shell and command language",
            },
        ]
    }
}

# Minimal Wikipedia-like HTML with lead section + two sections (h2 + h3)
SAMPLE_HTML = """
<html><body>
<section data-mw-section-id="0">
  <p>The Unix shell is a command-line interface.</p>
</section>
<section data-mw-section-id="1">
  <h2 id="History">History</h2>
  <p>The Unix shell was developed in the 1970s.</p>
</section>
<section data-mw-section-id="2">
  <h3 id="Early_shells">Early shells</h3>
  <p>The Thompson shell was one of the first Unix shells.</p>
</section>
</body></html>
"""

SAMPLE_HTML_WITH_TABLE = """
<html><body>
<p>Lead paragraph.</p>
<h2 id="History">History</h2>
<p>History content.</p>
<h2 id="Filmography">Filmography</h2>
<table class="wikitable sortable">
  <caption>Film appearances</caption>
  <tr><th>Year</th><th>Title</th><th>Role</th></tr>
  <tr><td>1997</td><td>Who's the Caboose?</td><td>Max</td></tr>
  <tr><td>1998</td><td>Next Stop Wonderland</td><td>Kevin</td></tr>
</table>
<p>See also the TV work.</p>
</body></html>
"""

SAMPLE_TABLE_HTML = """
<h2 id="Filmography">Filmography</h2>
<table class="wikitable sortable">
  <caption>Film appearances</caption>
  <tr><th>Year</th><th>Title</th><th>Role</th></tr>
  <tr><td>1997</td><td><i>Who's the Caboose?</i></td><td>Max</td></tr>
  <tr><td>1998</td><td><i>Next Stop Wonderland</i></td><td>Kevin</td></tr>
</table>
<p>Some additional text.</p>
"""

NON_WIKITABLE_HTML = """
<table class="infobox">
  <tr><td>Name</td><td>Sam Seder</td></tr>
</table>
"""


# ---------------------------------------------------------------------------
# get_summary
# ---------------------------------------------------------------------------


class TestGetSummary:
    def test_returns_parsed_json(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        result = api.get_summary("Unix%20shell")
        assert result["title"] == "Unix shell"
        assert "extract" in result

    def test_raises_on_http_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/NoSuchArticle",
            status_code=404,
            json={"type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found"},
        )
        with pytest.raises(httpx.HTTPStatusError):
            api.get_summary("NoSuchArticle")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_returns_list_of_results(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=httpx.URL(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": "Unix shell",
                    "srlimit": "10",
                    "format": "json",
                    "srprop": "snippet",
                },
            ),
            json=SAMPLE_SEARCH_RESPONSE,
        )
        results = api.search("Unix shell")
        assert len(results) == 2
        assert results[0]["title"] == "Unix shell"
        assert results[0]["url"] == "https://en.wikipedia.org/wiki/Unix_shell"

    def test_strips_html_from_snippet(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=httpx.URL(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": "Bash",
                    "srlimit": "10",
                    "format": "json",
                    "srprop": "snippet",
                },
            ),
            json={
                "query": {
                    "search": [
                        {
                            "title": "Bash",
                            "snippet": "<span class='hi'>Bash</span> shell",
                        }
                    ]
                }
            },
        )
        results = api.search("Bash")
        assert "<span" not in results[0]["snippet"]
        assert "Bash" in results[0]["snippet"]

    def test_returns_empty_list_when_no_results(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=httpx.URL(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": "xyzzy_no_such_article_ever",
                    "srlimit": "10",
                    "format": "json",
                    "srprop": "snippet",
                },
            ),
            json={"query": {"search": []}},
        )
        assert api.search("xyzzy_no_such_article_ever") == []


# ---------------------------------------------------------------------------
# fetch_article
# ---------------------------------------------------------------------------


class TestFetchArticle:
    def test_direct_title_lookup_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        result = api.fetch_article("Unix%20shell")
        assert result["title"] == "Unix shell"
        assert isinstance(result["sections"], list)

    def test_sections_are_hierarchical(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        result = api.fetch_article("Unix%20shell")
        history = next(s for s in result["sections"] if s["title"] == "History")
        assert any(s["title"] == "Early shells" for s in history["subsections"])

    def test_empty_sections_on_html_failure(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            status_code=503,
            json={},
        )
        result = api.fetch_article("Unix%20shell")
        assert result["title"] == "Unix shell"
        assert result["sections"] == []


# ---------------------------------------------------------------------------
# _build_section_tree
# ---------------------------------------------------------------------------

_FLAT_SECTIONS = [
    {"id": "", "title": "", "level": 0, "content": "Lead.", "tables": []},
    {
        "id": "History",
        "title": "History",
        "level": 2,
        "content": "History.",
        "tables": [],
    },
    {
        "id": "Early_shells",
        "title": "Early shells",
        "level": 3,
        "content": "Early.",
        "tables": [],
    },
    {
        "id": "Later_shells",
        "title": "Later shells",
        "level": 3,
        "content": "Later.",
        "tables": [],
    },
    {
        "id": "Career",
        "title": "Career",
        "level": 2,
        "content": "Career.",
        "tables": [],
    },
]


class TestBuildSectionTree:
    def test_structure(self) -> None:
        tree = api._build_section_tree(_FLAT_SECTIONS)
        titles = [s["title"] for s in tree]
        assert "" in titles  # lead included
        assert "History" in titles
        assert "Career" in titles
        history = next(s for s in tree if s["title"] == "History")
        sub_titles = [s["title"] for s in history["subsections"]]
        assert "Early shells" in sub_titles
        assert "Later shells" in sub_titles
        assert not any(s["title"] == "Career" for s in history["subsections"])
        assert history["id"] == "History"

    def test_empty_input_returns_empty(self) -> None:
        assert api._build_section_tree([]) == []

    def test_lead_only_returns_lead(self) -> None:
        flat = [{"id": "", "title": "", "level": 0, "content": "Lead.", "tables": []}]
        tree = api._build_section_tree(flat)
        assert len(tree) == 1
        assert tree[0]["title"] == ""
        assert tree[0]["content"] == "Lead."


# ---------------------------------------------------------------------------
# flatten_sections
# ---------------------------------------------------------------------------

_TREE = [
    {
        "id": "History",
        "title": "History",
        "level": 2,
        "content": "History.",
        "tables": [],
        "subsections": [
            {
                "id": "Early",
                "title": "Early shells",
                "level": 3,
                "content": "Early.",
                "tables": [],
                "subsections": [],
            }
        ],
    },
    {
        "id": "Career",
        "title": "Career",
        "level": 2,
        "content": "Career.",
        "tables": [],
        "subsections": [],
    },
]


class TestFlattenSections:
    def test_document_order(self) -> None:
        flat = api.flatten_sections(_TREE)
        assert [s["title"] for s in flat] == ["History", "Early shells", "Career"]

    def test_no_subsections_key_in_output(self) -> None:
        assert all("subsections" not in s for s in api.flatten_sections(_TREE))

    def test_empty_input(self) -> None:
        assert api.flatten_sections([]) == []


# ---------------------------------------------------------------------------
# _parse_sections
# ---------------------------------------------------------------------------


class TestParseSections:
    def test_structure(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML)
        by_title = {s["title"]: s for s in sections}
        assert "" in by_title  # lead
        assert by_title[""]["level"] == 0
        assert by_title["History"]["level"] == 2
        assert by_title["Early shells"]["level"] == 3
        assert by_title["History"]["id"] == "History"
        assert by_title["Early shells"]["id"] == "Early_shells"

    def test_content_extracted(self) -> None:
        by_title = {s["title"]: s for s in api._parse_sections(SAMPLE_HTML)}
        assert "1970s" in by_title["History"]["content"]
        assert "Thompson" in by_title["Early shells"]["content"]

    def test_html_entities_decoded(self) -> None:
        html = "<h2>Bourne &amp; C shells</h2><p>Text here.</p>"
        sections = api._parse_sections(html)
        assert sections[0]["title"] == "Bourne & C shells"

    def test_sup_tags_stripped(self) -> None:
        html = "<h2>History</h2><p>Text<sup>[1]</sup> here.</p>"
        sections = api._parse_sections(html)
        assert "[1]" not in sections[0]["content"]

    def test_empty_html_returns_empty_list(self) -> None:
        assert api._parse_sections("") == []

    def test_no_headings_returns_lead_only(self) -> None:
        sections = api._parse_sections("<p>Just a paragraph.</p>")
        assert len(sections) == 1
        assert sections[0]["title"] == ""
        assert "paragraph" in sections[0]["content"]


# ---------------------------------------------------------------------------
# get_sections
# ---------------------------------------------------------------------------


class TestGetSections:
    def test_returns_sections_list(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        sections = api.get_sections("Unix%20shell")
        assert any(s["title"] == "History" for s in sections)

    def test_falls_back_to_search_on_404(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/unix+shell",
            status_code=404,
            json={},
        )
        httpx_mock.add_response(
            url=httpx.URL(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": "unix+shell",
                    "srlimit": "1",
                    "format": "json",
                    "srprop": "snippet",
                },
            ),
            json={"query": {"search": [{"title": "Unix shell", "snippet": ""}]}},
        )
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        assert any(s["title"] == "History" for s in api.get_sections("unix+shell"))

    def test_raises_value_error_when_no_match(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/xyzzy_nothing",
            status_code=404,
            json={},
        )
        httpx_mock.add_response(
            url=httpx.URL(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": "xyzzy_nothing",
                    "srlimit": "1",
                    "format": "json",
                    "srprop": "snippet",
                },
            ),
            json={"query": {"search": []}},
        )
        with pytest.raises(ValueError, match="No Wikipedia article found"):
            api.get_sections("xyzzy_nothing")


# ---------------------------------------------------------------------------
# filter_sections
# ---------------------------------------------------------------------------

_FILTER_SECTIONS = [
    {"id": "", "title": "", "level": 0, "content": "Lead text."},
    {"id": "History", "title": "History", "level": 2, "content": "History."},
    {"id": "Early", "title": "Early History", "level": 3, "content": "Early history."},
    {"id": "Tech", "title": "Technical details", "level": 2, "content": "Technical."},
]


class TestFilterSections:
    @pytest.mark.parametrize(
        "query,expected_title",
        [
            ("History", "History"),  # exact match
            ("history", "History"),  # case-insensitive
            ("hist", "History"),  # fuzzy substring
        ],
    )
    def test_matching(self, query: str, expected_title: str) -> None:
        result = api.filter_sections(_FILTER_SECTIONS, (query,))
        assert any(s["title"] == expected_title for s in result)

    def test_fuzzy_matches_multiple_sections(self) -> None:
        result = api.filter_sections(_FILTER_SECTIONS, ("hist",))
        titles = [s["title"] for s in result]
        assert "History" in titles
        assert "Early History" in titles

    def test_matched_section_includes_subsections(self) -> None:
        sections = [
            {"id": "", "title": "", "level": 0, "content": "Lead."},
            {"id": "Hist", "title": "History", "level": 2, "content": "History."},
            {"id": "Early", "title": "Early shells", "level": 3, "content": "Early."},
            {"id": "Other", "title": "Other section", "level": 2, "content": "Other."},
        ]
        result = api.filter_sections(sections, ("History",))
        titles = [s["title"] for s in result]
        assert "Early shells" in titles
        assert "Other section" not in titles

    def test_multiple_queries(self) -> None:
        result = api.filter_sections(_FILTER_SECTIONS, ("History", "Technical"))
        titles = [s["title"] for s in result]
        assert "History" in titles
        assert "Technical details" in titles

    def test_lead_section_excluded(self) -> None:
        result = api.filter_sections(_FILTER_SECTIONS, ("History",))
        assert all(s["title"] != "" for s in result)

    def test_no_match_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="No sections found matching"):
            api.filter_sections(_FILTER_SECTIONS, ("xyzzy_nope",))


# ---------------------------------------------------------------------------
# _strip_html
# ---------------------------------------------------------------------------


class TestStripHtml:
    @pytest.mark.parametrize(
        "html_input,expected",
        [
            ("<span>hello</span>", "hello"),
            ("<b><i>text</i></b>", "text"),
            ("plain text", "plain text"),
        ],
    )
    def test_strips_html(self, html_input: str, expected: str) -> None:
        assert api._strip_html(html_input) == expected


# ---------------------------------------------------------------------------
# _parse_tables
# ---------------------------------------------------------------------------


class TestParseTables:
    def test_basic_wikitable(self) -> None:
        tables = api._parse_tables(SAMPLE_TABLE_HTML)
        assert len(tables) == 1
        t = tables[0]
        assert t["headers"] == ["Year", "Title", "Role"]
        assert t["caption"] == "Film appearances"
        assert len(t["rows"]) == 2
        assert t["rows"][0][0] == "1997"
        assert "Caboose" in t["rows"][0][1]

    def test_non_wikitable_ignored(self) -> None:
        assert api._parse_tables(NON_WIKITABLE_HTML) == []

    @pytest.mark.parametrize(
        "html_input",
        ["", "<p>Plain text.</p>"],
        ids=["empty_html", "no_table_element"],
    )
    def test_no_table_returns_empty(self, html_input: str) -> None:
        assert api._parse_tables(html_input) == []

    def test_html_stripped_from_cells(self) -> None:
        html = """
        <table class="wikitable">
          <tr><th>Title</th></tr>
          <tr><td><a href="/wiki/Foo">Foo article</a></td></tr>
        </table>
        """
        assert api._parse_tables(html)[0]["rows"][0][0] == "Foo article"

    def test_table_without_caption(self) -> None:
        html = """
        <table class="wikitable">
          <tr><th>A</th><th>B</th></tr>
          <tr><td>1</td><td>2</td></tr>
        </table>
        """
        assert api._parse_tables(html)[0]["caption"] == ""

    def test_table_without_headers(self) -> None:
        html = """
        <table class="wikitable">
          <tr><td>a</td><td>b</td></tr>
          <tr><td>c</td><td>d</td></tr>
        </table>
        """
        t = api._parse_tables(html)[0]
        assert t["headers"] == []
        assert len(t["rows"]) == 2

    def test_multiple_tables(self) -> None:
        html = """
        <table class="wikitable"><tr><th>A</th></tr><tr><td>1</td></tr></table>
        <table class="wikitable"><tr><th>B</th></tr><tr><td>2</td></tr></table>
        """
        tables = api._parse_tables(html)
        assert len(tables) == 2
        assert tables[0]["headers"] == ["A"]
        assert tables[1]["headers"] == ["B"]


# ---------------------------------------------------------------------------
# _parse_sections with tables + _build_section_tree with tables
# ---------------------------------------------------------------------------


class TestParseSectionsWithTables:
    def test_tables_extracted_and_text_clean(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        by_title = {s["title"]: s for s in sections}
        assert all("tables" in s for s in sections)
        film_tables = by_title["Filmography"]["tables"]
        assert len(film_tables) == 1
        assert film_tables[0]["headers"] == ["Year", "Title", "Role"]
        assert "Year" not in by_title["Filmography"]["content"]
        assert "1997" not in by_title["Filmography"]["content"]

    def test_section_without_table_has_empty_tables(self) -> None:
        by_title = {s["title"]: s for s in api._parse_sections(SAMPLE_HTML_WITH_TABLE)}
        assert by_title["History"]["tables"] == []

    def test_non_table_content_still_extracted(self) -> None:
        by_title = {s["title"]: s for s in api._parse_sections(SAMPLE_HTML_WITH_TABLE)}
        assert "TV work" in by_title["Filmography"]["content"]


# ---------------------------------------------------------------------------
# _url_to_title
# ---------------------------------------------------------------------------


class TestUrlToTitle:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://en.wikipedia.org/wiki/Unix_shell", "Unix shell"),
            ("https://en.wikipedia.org/wiki/Sam%20Seder", "Sam Seder"),
            ("https://en.wikipedia.org/wiki/Bash_(Unix_shell)", "Bash (Unix shell)"),
            (
                "http://en.wikipedia.org/wiki/Python_(programming_language)",
                "Python (programming language)",
            ),
            ("https://fr.wikipedia.org/wiki/Unix", "Unix"),
        ],
    )
    def test_valid_url_returns_title(self, url: str, expected: str) -> None:
        assert api._url_to_title(url) == expected

    @pytest.mark.parametrize(
        "url",
        [
            "https://en.wikipedia.org/w/index.php?title=Unix",
            "https://example.com/wiki/Unix_shell",
            "Unix shell",
            "",
            "https://en.wikipedia.org/wiki/",
        ],
    )
    def test_invalid_input_returns_none(self, url: str) -> None:
        assert api._url_to_title(url) is None


# ---------------------------------------------------------------------------
# fetch_article with URL input
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Content formatting: code blocks, inline code, blockquotes, links
# ---------------------------------------------------------------------------


class TestCodeBlockExtraction:
    def test_code_block_extracted_as_fence(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>Here is some code:</p>
            <div class="mw-highlight mw-highlight-lang-python"
                 data-mw='{"name":"syntaxhighlight",
                 "attrs":{"lang":"python"},
                 "body":{"extsrc":"def hello():\\n    print(\\"H\\")"}}'>
                <pre><span>code</span></pre>
            </div>
        </section>
        """
        sections = api._parse_sections(html)
        assert "```python" in sections[0]["content"]
        assert "def hello():" in sections[0]["content"]
        assert "print" in sections[0]["content"]

    def test_code_block_preserves_newlines(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <pre>line1
line2
line3</pre>
        </section>
        """
        sections = api._parse_sections(html)
        assert "line1" in sections[0]["content"]
        assert "line2" in sections[0]["content"]

    def test_multiple_code_blocks(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Examples</h2>
            <pre>code1</pre>
            <p>Some text</p>
            <pre>code2</pre>
        </section>
        """
        sections = api._parse_sections(html)
        content = sections[0]["content"]
        assert "code1" in content
        assert "code2" in content


class TestInlineCode:
    def test_inline_code_wrapped_in_backticks(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>Use <code>print()</code> to output text.</p>
        </section>
        """
        sections = api._parse_sections(html)
        assert "`print()`" in sections[0]["content"]

    def test_inline_code_preserves_text(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>The <code>main</code> function.</p>
        </section>
        """
        sections = api._parse_sections(html)
        assert "`main`" in sections[0]["content"]
        assert "function" in sections[0]["content"]


class TestBlockquoteRendering:
    def test_blockquote_converted_to_markdown(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <blockquote>
                <p>This is a quote.</p>
            </blockquote>
        </section>
        """
        sections = api._parse_sections(html)
        assert "> This is a quote" in sections[0]["content"]

    def test_nested_blockquote(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <blockquote>
                <p>Outer quote.</p>
                <blockquote>
                    <p>Inner quote.</p>
                </blockquote>
            </blockquote>
        </section>
        """
        sections = api._parse_sections(html)
        content = sections[0]["content"]
        assert "> Outer quote" in content
        assert "> Inner quote" in content


class TestWikipediaLinks:
    def test_internal_wiki_link_converted(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p><a rel="mw:WikiLink" href="./OOP">object-oriented</a> programming.</p>
        </section>
        """
        sections = api._parse_sections(html)
        assert (
            "[object-oriented](https://en.wikipedia.org/OOP)" in sections[0]["content"]
        )

    def test_external_link_converted(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>Visit <a rel="mw:ExtLink" href="https://python.org">python.org</a>.</p>
        </section>
        """
        sections = api._parse_sections(html)
        assert "[python.org](https://python.org)" in sections[0]["content"]

    def test_link_with_display_text(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>See <a rel="mw:WikiLink" href="./Author">Guido</a>.</p>
        </section>
        """
        sections = api._parse_sections(html)
        assert "[Guido]" in sections[0]["content"]


class TestMixedContent:
    def test_code_and_text_mixed(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>Define a function:</p>
            <pre>def foo(): pass</pre>
            <p>Then call it.</p>
        </section>
        """
        sections = api._parse_sections(html)
        content = sections[0]["content"]
        assert "Define a function:" in content
        assert "Then call it." in content
        assert "```" in content  # code fence present

    def test_code_inline_and_block(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <p>Use <code>x</code> variable.</p>
            <pre>def f(): pass</pre>
        </section>
        """
        sections = api._parse_sections(html)
        content = sections[0]["content"]
        assert "`x`" in content
        assert "```" in content

    def test_quote_and_link(self) -> None:
        html = """
        <section data-mw-section-id="1">
            <h2>Example</h2>
            <blockquote>
                <p>See <a rel="mw:WikiLink" href="./API">the API</a>.</p>
            </blockquote>
        </section>
        """
        sections = api._parse_sections(html)
        content = sections[0]["content"]
        assert "> See [the API]" in content


# ---------------------------------------------------------------------------
# fetch_featured_article
# ---------------------------------------------------------------------------


SAMPLE_FEATURED_RESPONSE = {
    "tfa": {
        "type": "standard",
        "title": "Michael_Tritter",
        "displaytitle": '<span class="mw-page-title-main">Michael Tritter</span>',
        "normalizedtitle": "Michael Tritter",
        "namespace": {"id": 0, "text": ""},
        "wikibase_item": "Q3856283",
        "titles": {
            "canonical": "Michael_Tritter",
            "normalized": "Michael Tritter",
            "display": '<span class="mw-page-title-main">Michael Tritter</span>',
        },
        "pageid": 19612185,
        "lang": "en",
        "dir": "ltr",
        "revision": "1333889563",
        "tid": "9bdbc708-f5db-11f0-b44a-0d205c4be687",
        "timestamp": "2026-01-20T08:40:01Z",
        "description": "Fictional detective on the TV series House",
        "description_source": "local",
        "content_urls": {
            "desktop": {
                "page": "https://en.wikipedia.org/wiki/Michael_Tritter",
                "revisions": "https://en.wikipedia.org/wiki/Michael_Tritter?action=history",
                "edit": "https://en.wikipedia.org/wiki/Michael_Tritter?action=edit",
                "talk": "https://en.wikipedia.org/wiki/Talk:Michael_Tritter",
            },
            "mobile": {
                "page": "https://en.m.wikipedia.org/wiki/Michael_Tritter",
                "revisions": "https://en.m.wikipedia.org/wiki/Special:History/Michael_Tritter",
                "edit": "https://en.m.wikipedia.org/wiki/Michael_Tritter?action=edit",
                "talk": "https://en.m.wikipedia.org/wiki/Talk:Michael_Tritter",
            },
        },
        "extract": (
            "Michael Tritter is a fictional detective on the television series House. "
            "He is portrayed by actor David Morse. Tritter appears in the third season "
            "of the series, in which he investigates Dr. Gregory House for drug abuse."
        ),
        "extract_html": (
            "<p><b>Michael Tritter</b> is a fictional detective on the "
            "television series <i>House</i>. He is portrayed by actor "
            '<a href="/wiki/David_Morse" title="David Morse">David Morse</a>. '
            "Tritter appears in the third season of the series, in which "
            "he investigates Dr. Gregory House for drug abuse.</p>"
        ),
    }
}

SAMPLE_FEATURED_HTML = """
<html><body>
<section data-mw-section-id="0">
  <p>Michael Tritter is a fictional detective on the television series House.</p>
</section>
<section data-mw-section-id="1">
  <h2 id="Character">Character</h2>
  <p>Tritter is portrayed by actor David Morse.</p>
</section>
<section data-mw-section-id="2">
  <h2 id="Plot">Plot</h2>
  <p>In the third season, Tritter investigates Dr. Gregory House for drug abuse.</p>
</section>
</body></html>
"""


class TestFetchFeaturedArticle:
    def test_fetches_todays_featured_article(self, httpx_mock: HTTPXMock) -> None:
        # Mock datetime to return a fixed date
        mock_date = datetime(2025, 3, 23)
        with patch("wiki_client.api.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_date
            httpx_mock.add_response(
                url="https://en.wikipedia.org/api/rest_v1/feed/featured/2025/03/23",
                json=SAMPLE_FEATURED_RESPONSE,
            )
            # Mock HTML response for the article
            httpx_mock.add_response(
                url="https://en.wikipedia.org/api/rest_v1/page/html/Michael_Tritter",
                text=SAMPLE_FEATURED_HTML,
            )

            result = api.fetch_featured_article()

        assert result["title"] == "Michael_Tritter"
        assert result["description"] == "Fictional detective on the TV series House"
        assert "extract" in result
        assert "content_urls" in result
        assert "sections" in result
        assert len(result["sections"]) == 3
        assert result["sections"][0]["title"] == ""
        assert result["sections"][1]["title"] == "Character"
        assert result["sections"][2]["title"] == "Plot"

    def test_fetches_featured_article_for_specific_date(
        self, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/feed/featured/2025/03/23",
            json=SAMPLE_FEATURED_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Michael_Tritter",
            text=SAMPLE_FEATURED_HTML,
        )

        result = api.fetch_featured_article("2025-03-23")

        assert result["title"] == "Michael_Tritter"
        assert len(result["sections"]) == 3

    def test_handles_missing_tfa_key(self, httpx_mock: HTTPXMock) -> None:
        # Mock datetime to return a fixed date
        mock_date = datetime(2025, 3, 23)
        with patch("wiki_client.api.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_date

            httpx_mock.add_response(
                url="https://en.wikipedia.org/api/rest_v1/feed/featured/2025/03/23",
                json={},  # Empty response without tfa key
            )

            with pytest.raises(ValueError, match="No featured article found"):
                api.fetch_featured_article()

    def test_handles_http_errors_on_featured_api(self, httpx_mock: HTTPXMock) -> None:
        # Mock datetime to return a fixed date
        mock_date = datetime(2025, 3, 23)
        with patch("wiki_client.api.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_date

            httpx_mock.add_response(
                url="https://en.wikipedia.org/api/rest_v1/feed/featured/2025/03/23",
                status_code=404,
            )

            with pytest.raises(httpx.HTTPStatusError):
                api.fetch_featured_article()

    def test_handles_http_errors_on_html_fetch(self, httpx_mock: HTTPXMock) -> None:
        # Mock datetime to return a fixed date
        mock_date = datetime(2025, 3, 23)
        with patch("wiki_client.api.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_date

            httpx_mock.add_response(
                url="https://en.wikipedia.org/api/rest_v1/feed/featured/2025/03/23",
                json=SAMPLE_FEATURED_RESPONSE,
            )
            httpx_mock.add_response(
                url="https://en.wikipedia.org/api/rest_v1/page/html/Michael_Tritter",
                status_code=500,
            )

            result = api.fetch_featured_article()

        # Should still return summary data even if HTML fetch fails
        assert result["title"] == "Michael_Tritter"
        assert result["description"] == "Fictional detective on the TV series House"
        assert result["sections"] == []  # Empty sections when HTML fetch fails

    @pytest.mark.parametrize(
        "bad_date",
        [
            "",  # empty string
            "   ",  # whitespace-only
            "2025/03/23",  # wrong separator
            "03-23-2025",  # wrong order (MM-DD-YYYY)
            "not-a-date",  # not a date at all
            "2025-02-30",  # impossible date
            "2025-13-01",  # invalid month
        ],
    )
    def test_rejects_invalid_date_formats(self, bad_date: str) -> None:
        with pytest.raises(ValueError, match="Invalid date format"):
            api.fetch_featured_article(bad_date)
