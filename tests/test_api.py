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
