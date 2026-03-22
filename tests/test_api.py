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
        httpx_mock.add_response(
            url="https://en.wikipedia.org/api/rest_v1/page/summary/Unix%20shell",
            json=SAMPLE_SUMMARY,
        )
        result = api.fetch_article("Unix%20shell")
        assert result["title"] == "Unix shell"

    def test_falls_back_to_search_on_404(self, httpx_mock: HTTPXMock) -> None:
        # First call: 404 on direct lookup
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
        result = api.fetch_article("unix+shell")
        assert result["title"] == "Unix shell"

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


class TestStripHtml:
    def test_removes_span_tags(self) -> None:
        assert api._strip_html("<span>hello</span>") == "hello"

    def test_removes_nested_tags(self) -> None:
        assert api._strip_html("<b><i>text</i></b>") == "text"

    def test_plain_text_unchanged(self) -> None:
        assert api._strip_html("plain text") == "plain text"
