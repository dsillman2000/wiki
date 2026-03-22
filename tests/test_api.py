"""Unit tests for wiki_cli.api."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from wiki_cli import api

SAMPLE_SUMMARY = {
    "title": "Unix shell",
    "description": "Type of command-line interface",
    "extract": (
        "A Unix shell is a command-line interpreter that provides a user interface."
    ),
    "content_urls": {
        "desktop": {"page": "https://en.wikipedia.org/wiki/Unix_shell"}
    },
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
        results = api.search("xyzzy_no_such_article_ever")
        assert results == []


class TestFetchArticle:
    def test_direct_title_lookup_success(self, httpx_mock: HTTPXMock) -> None:
        # Summary call uses the query as-is
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        # HTML call uses the canonical title returned by the summary ("Unix shell")
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        result = api.fetch_article("Unix%20shell")
        assert result["title"] == "Unix shell"
        assert "sections" in result
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
        # "History" (h2) should have "Early shells" (h3) as a subsection
        history = next(s for s in result["sections"] if s["title"] == "History")
        assert any(s["title"] == "Early shells" for s in history["subsections"])

    def test_falls_back_to_search_on_404(self, httpx_mock: HTTPXMock) -> None:
        # First call: 404 on direct summary lookup
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/unix+shell",
            status_code=404,
            json={},
        )
        # Second call: search returns "Unix shell"
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
        # Third call: summary for the found title
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        # Fourth call: HTML for the canonical title
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        result = api.fetch_article("unix+shell")
        assert result["title"] == "Unix shell"
        assert "sections" in result

    def test_raises_value_error_when_no_match(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/xyzzy_nothing",
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
            api.fetch_article("xyzzy_nothing")

    def test_empty_sections_on_html_failure(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        # HTML endpoint unavailable
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            status_code=503,
            json={},
        )
        result = api.fetch_article("Unix%20shell")
        assert result["title"] == "Unix shell"
        assert result["sections"] == []


class TestBuildSectionTree:
    FLAT = [
        {"id": "", "title": "", "level": 0, "content": "Lead."},
        {"id": "History", "title": "History", "level": 2, "content": "History."},
        {
            "id": "Early_shells",
            "title": "Early shells",
            "level": 3,
            "content": "Early.",
        },
        {
            "id": "Later_shells",
            "title": "Later shells",
            "level": 3,
            "content": "Later.",
        },
        {"id": "Career", "title": "Career", "level": 2, "content": "Career."},
    ]

    def test_top_level_sections(self) -> None:
        tree = api._build_section_tree(self.FLAT)
        titles = [s["title"] for s in tree]
        assert "History" in titles
        assert "Career" in titles
        assert "" not in titles  # lead excluded

    def test_h3_nested_under_h2(self) -> None:
        tree = api._build_section_tree(self.FLAT)
        history = next(s for s in tree if s["title"] == "History")
        sub_titles = [s["title"] for s in history["subsections"]]
        assert "Early shells" in sub_titles
        assert "Later shells" in sub_titles

    def test_h2_not_nested_under_sibling_h2(self) -> None:
        tree = api._build_section_tree(self.FLAT)
        history = next(s for s in tree if s["title"] == "History")
        assert not any(s["title"] == "Career" for s in history["subsections"])

    def test_empty_input_returns_empty(self) -> None:
        assert api._build_section_tree([]) == []

    def test_lead_only_returns_empty(self) -> None:
        flat = [{"id": "", "title": "", "level": 0, "content": "Lead."}]
        assert api._build_section_tree(flat) == []

    def test_id_preserved(self) -> None:
        tree = api._build_section_tree(self.FLAT)
        history = next(s for s in tree if s["title"] == "History")
        assert history["id"] == "History"


class TestFlattenSections:
    TREE = [
        {
            "id": "History",
            "title": "History",
            "level": 2,
            "content": "History.",
            "subsections": [
                {
                    "id": "Early",
                    "title": "Early shells",
                    "level": 3,
                    "content": "Early.",
                    "subsections": [],
                }
            ],
        },
        {
            "id": "Career",
            "title": "Career",
            "level": 2,
            "content": "Career.",
            "subsections": [],
        },
    ]

    def test_document_order(self) -> None:
        flat = api.flatten_sections(self.TREE)
        titles = [s["title"] for s in flat]
        assert titles == ["History", "Early shells", "Career"]

    def test_no_subsections_key_in_output(self) -> None:
        flat = api.flatten_sections(self.TREE)
        assert all("subsections" not in s for s in flat)

    def test_empty_input(self) -> None:
        assert api.flatten_sections([]) == []


class TestParseSections:
    def test_lead_plus_sections(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML)
        titles = [s["title"] for s in sections]
        assert "" in titles  # lead section
        assert "History" in titles
        assert "Early shells" in titles

    def test_lead_section_has_empty_title(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML)
        assert sections[0]["title"] == ""
        assert sections[0]["level"] == 0

    def test_section_levels_are_correct(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML)
        by_title = {s["title"]: s for s in sections}
        assert by_title["History"]["level"] == 2
        assert by_title["Early shells"]["level"] == 3

    def test_content_extracted(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML)
        by_title = {s["title"]: s for s in sections}
        assert "1970s" in by_title["History"]["content"]
        assert "Thompson" in by_title["Early shells"]["content"]

    def test_id_extracted_from_heading(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML)
        by_title = {s["title"]: s for s in sections}
        assert by_title["History"]["id"] == "History"
        assert by_title["Early shells"]["id"] == "Early_shells"

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
        html = "<p>Just a paragraph.</p>"
        sections = api._parse_sections(html)
        assert len(sections) == 1
        assert sections[0]["title"] == ""
        assert "paragraph" in sections[0]["content"]


class TestGetSections:
    def test_returns_sections_list(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/html/Unix%20shell",
            text=SAMPLE_HTML,
        )
        sections = api.get_sections("Unix%20shell")
        titles = [s["title"] for s in sections]
        assert "History" in titles

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
        sections = api.get_sections("unix+shell")
        assert any(s["title"] == "History" for s in sections)

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


class TestFilterSections:
    SECTIONS = [
        {"id": "", "title": "", "level": 0, "content": "Lead text."},
        {"id": "History", "title": "History", "level": 2, "content": "History."},
        {
            "id": "Early",
            "title": "Early History",
            "level": 3,
            "content": "Early history.",
        },
        {
            "id": "Tech",
            "title": "Technical details",
            "level": 2,
            "content": "Technical.",
        },
    ]

    def test_exact_match(self) -> None:
        result = api.filter_sections(self.SECTIONS, ("History",))
        titles = [s["title"] for s in result]
        assert "History" in titles

    def test_case_insensitive_match(self) -> None:
        result = api.filter_sections(self.SECTIONS, ("history",))
        titles = [s["title"] for s in result]
        assert "History" in titles

    def test_fuzzy_substring_match(self) -> None:
        result = api.filter_sections(self.SECTIONS, ("hist",))
        titles = [s["title"] for s in result]
        assert "History" in titles
        assert "Early History" in titles

    def test_matched_section_includes_subsections(self) -> None:
        # "History" (h2) is directly matched; "Early shells" (h3) should be
        # included automatically as its subsection even without a direct match.
        sections = [
            {"id": "", "title": "", "level": 0, "content": "Lead."},
            {"id": "Hist", "title": "History", "level": 2, "content": "History."},
            {
                "id": "Early",
                "title": "Early shells",
                "level": 3,
                "content": "Early.",
            },
            {
                "id": "Other",
                "title": "Other section",
                "level": 2,
                "content": "Other.",
            },
        ]
        result = api.filter_sections(sections, ("History",))
        titles = [s["title"] for s in result]
        assert "History" in titles
        assert "Early shells" in titles  # subsection pulled in
        assert "Other section" not in titles  # sibling excluded

    def test_multiple_queries(self) -> None:
        result = api.filter_sections(self.SECTIONS, ("History", "Technical"))
        titles = [s["title"] for s in result]
        assert "History" in titles
        assert "Technical details" in titles

    def test_lead_section_excluded(self) -> None:
        result = api.filter_sections(self.SECTIONS, ("History",))
        assert all(s["title"] != "" for s in result)

    def test_no_match_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="No sections found matching"):
            api.filter_sections(self.SECTIONS, ("xyzzy_nope",))


class TestStripHtml:
    def test_removes_span_tags(self) -> None:
        assert api._strip_html("<span>hello</span>") == "hello"

    def test_removes_nested_tags(self) -> None:
        assert api._strip_html("<b><i>text</i></b>") == "text"

    def test_plain_text_unchanged(self) -> None:
        assert api._strip_html("plain text") == "plain text"


# ---------------------------------------------------------------------------
# Wikitable fixture HTML
# ---------------------------------------------------------------------------

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

NON_WIKITABLE_HTML = """
<table class="infobox">
  <tr><td>Name</td><td>Sam Seder</td></tr>
</table>
"""


class TestParseTables:
    def test_basic_wikitable(self) -> None:
        tables = api._parse_tables(SAMPLE_TABLE_HTML)
        assert len(tables) == 1
        t = tables[0]
        assert t["headers"] == ["Year", "Title", "Role"]
        assert len(t["rows"]) == 2

    def test_caption_extracted(self) -> None:
        tables = api._parse_tables(SAMPLE_TABLE_HTML)
        assert tables[0]["caption"] == "Film appearances"

    def test_data_rows_extracted(self) -> None:
        tables = api._parse_tables(SAMPLE_TABLE_HTML)
        assert tables[0]["rows"][0][0] == "1997"
        assert "Caboose" in tables[0]["rows"][0][1]
        assert tables[0]["rows"][0][2] == "Max"

    def test_non_wikitable_ignored(self) -> None:
        tables = api._parse_tables(NON_WIKITABLE_HTML)
        assert tables == []

    def test_empty_html_returns_empty(self) -> None:
        assert api._parse_tables("") == []

    def test_no_table_returns_empty(self) -> None:
        assert api._parse_tables("<p>Plain text.</p>") == []

    def test_html_stripped_from_cells(self) -> None:
        html = """
        <table class="wikitable">
          <tr><th>Title</th></tr>
          <tr><td><a href="/wiki/Foo">Foo article</a></td></tr>
        </table>
        """
        tables = api._parse_tables(html)
        assert tables[0]["rows"][0][0] == "Foo article"

    def test_table_without_caption(self) -> None:
        html = """
        <table class="wikitable">
          <tr><th>A</th><th>B</th></tr>
          <tr><td>1</td><td>2</td></tr>
        </table>
        """
        tables = api._parse_tables(html)
        assert tables[0]["caption"] == ""

    def test_table_without_headers(self) -> None:
        html = """
        <table class="wikitable">
          <tr><td>a</td><td>b</td></tr>
          <tr><td>c</td><td>d</td></tr>
        </table>
        """
        tables = api._parse_tables(html)
        assert tables[0]["headers"] == []
        assert len(tables[0]["rows"]) == 2

    def test_multiple_tables(self) -> None:
        html = """
        <table class="wikitable"><tr><th>A</th></tr><tr><td>1</td></tr></table>
        <table class="wikitable"><tr><th>B</th></tr><tr><td>2</td></tr></table>
        """
        tables = api._parse_tables(html)
        assert len(tables) == 2
        assert tables[0]["headers"] == ["A"]
        assert tables[1]["headers"] == ["B"]


class TestParseSectionsWithTables:
    def test_section_has_tables_key(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        for s in sections:
            assert "tables" in s

    def test_table_extracted_from_section(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        by_title = {s["title"]: s for s in sections}
        film_tables = by_title["Filmography"]["tables"]
        assert len(film_tables) == 1
        assert film_tables[0]["headers"] == ["Year", "Title", "Role"]

    def test_table_text_not_in_content(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        by_title = {s["title"]: s for s in sections}
        # "Year", "Title", "Role" (headers) should not appear in plain-text content
        content = by_title["Filmography"]["content"]
        assert "Year" not in content
        assert "1997" not in content

    def test_section_without_table_has_empty_tables(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        by_title = {s["title"]: s for s in sections}
        assert by_title["History"]["tables"] == []

    def test_non_table_content_still_extracted(self) -> None:
        sections = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        by_title = {s["title"]: s for s in sections}
        assert "TV work" in by_title["Filmography"]["content"]


class TestBuildSectionTreeWithTables:
    def test_tables_preserved_in_tree(self) -> None:
        flat = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        tree = api._build_section_tree(flat)
        by_title = {s["title"]: s for s in tree}
        assert len(by_title["Filmography"]["tables"]) == 1

    def test_tables_preserved_in_flatten(self) -> None:
        flat = api._parse_sections(SAMPLE_HTML_WITH_TABLE)
        tree = api._build_section_tree(flat)
        flattened = api.flatten_sections(tree)
        by_title = {s["title"]: s for s in flattened}
        assert len(by_title["Filmography"]["tables"]) == 1


class TestStripAllTables:
    def test_removes_single_table(self) -> None:
        html = "<p>Before</p><table><tr><td>x</td></tr></table><p>After</p>"
        result = api._strip_all_tables(html)
        assert "<table" not in result
        assert "Before" in result
        assert "After" in result

    def test_removes_nested_tables(self) -> None:
        html = "<table><tr><td><table><tr><td>inner</td></tr></table></td></tr></table>"
        result = api._strip_all_tables(html)
        assert "<table" not in result

    def test_empty_input(self) -> None:
        assert api._strip_all_tables("") == ""

    def test_no_table_unchanged(self) -> None:
        html = "<p>No table here.</p>"
        assert api._strip_all_tables(html) == html
