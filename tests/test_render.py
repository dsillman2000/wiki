"""Unit tests for wiki_client.render."""

from __future__ import annotations

import io

from rich.console import Console

from wiki_client import render


def _capture(func, *args, **kwargs) -> str:
    """Run *func* with a fresh in-memory Console and return its output."""
    buf = io.StringIO()
    original_console = render.console
    render.console = Console(file=buf, highlight=False, markup=False)
    try:
        func(*args, **kwargs)
    finally:
        render.console = original_console
    return buf.getvalue()


SAMPLE_DATA = {
    "title": "Unix shell",
    "description": "Type of command-line interface",
    "extract": "A Unix shell is a command-line interpreter.",
    "sections": [
        {
            "id": "History",
            "title": "History",
            "level": 2,
            "content": "The shell was developed in the 1970s.",
            "tables": [],
            "subsections": [
                {
                    "id": "Early_shells",
                    "title": "Early shells",
                    "level": 3,
                    "content": "The Thompson shell came first.",
                    "tables": [],
                    "subsections": [],
                }
            ],
        }
    ],
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Unix_shell"}},
}

SAMPLE_SECTIONS = [
    {
        "title": "History",
        "level": 2,
        "content": "The shell was developed in the 1970s.",
        "tables": [],
    },
    {
        "title": "Early shells",
        "level": 3,
        "content": "The Thompson shell came first.",
        "tables": [],
    },
]

SAMPLE_TABLE = {
    "caption": "Film appearances",
    "headers": ["Year", "Title", "Role"],
    "rows": [
        ["1997", "Who's the Caboose?", "Max"],
        ["1998", "Next Stop Wonderland", "Kevin"],
    ],
}

SAMPLE_TABLE_NO_HEADERS = {
    "caption": "",
    "headers": [],
    "rows": [["a", "b"], ["c", "d"]],
}

SECTION_WITH_TABLE = {
    "title": "Filmography",
    "level": 2,
    "content": "See also the TV work.",
    "tables": [SAMPLE_TABLE],
}

ARTICLE_WITH_TABLE = {
    "title": "Sam Seder",
    "description": "American comedian",
    "extract": "Sam Seder is an American comedian.",
    "sections": [
        {
            "id": "Filmography",
            "title": "Filmography",
            "level": 2,
            "content": "See also the TV work.",
            "tables": [SAMPLE_TABLE],
            "subsections": [],
        }
    ],
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Sam_Seder"}},
}


# ---------------------------------------------------------------------------
# render_article
# ---------------------------------------------------------------------------


class TestRenderArticle:
    def test_raw_output(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        out = capsys.readouterr().out
        assert "# Unix shell" in out
        assert "1970s" in out
        assert "Thompson" in out
        assert "en.wikipedia.org/wiki/Unix_shell" in out

    def test_rich_output(self) -> None:
        out = _capture(render.render_article, SAMPLE_DATA)
        assert "Unix shell" in out
        assert "1970s" in out
        assert "Thompson" in out
        assert "en.wikipedia.org/wiki/Unix_shell" in out

    def test_raw_falls_back_to_extract_when_no_sections(self, capsys) -> None:
        data = {
            "title": "Unix shell",
            "extract": "A Unix shell is a command-line interpreter.",
            "sections": [],
            "content_urls": {
                "desktop": {"page": "https://en.wikipedia.org/wiki/Unix_shell"}
            },
        }
        render.render_article(data, raw=True)
        assert "command-line interpreter" in capsys.readouterr().out

    def test_missing_fields_raw_does_not_raise(self, capsys) -> None:
        render.render_article({}, raw=True)
        assert capsys.readouterr().out == ""

    def test_missing_fields_rich_does_not_raise(self) -> None:
        _capture(render.render_article, {})


# ---------------------------------------------------------------------------
# render_search_results
# ---------------------------------------------------------------------------


class TestRenderSearchResults:
    RESULTS = [
        {
            "title": "Unix shell",
            "snippet": "A Unix shell is a command-line interpreter.",
            "url": "https://en.wikipedia.org/wiki/Unix_shell",
        },
        {
            "title": "Bash (Unix shell)",
            "snippet": "Bash is a Unix shell and command language.",
            "url": "https://en.wikipedia.org/wiki/Bash_(Unix_shell)",
        },
    ]

    def test_shows_results_and_query(self) -> None:
        out = _capture(render.render_search_results, self.RESULTS, query="my query")
        assert "Unix shell" in out
        assert "wikipedia" in out
        assert "my query" in out

    def test_empty_results_shows_no_results_message(self) -> None:
        out = _capture(render.render_search_results, [], query="xyzzy")
        assert "xyzzy" in out


# ---------------------------------------------------------------------------
# render_section_list
# ---------------------------------------------------------------------------


class TestRenderSectionList:
    def test_shows_titles_and_indentation(self) -> None:
        out = _capture(render.render_section_list, SAMPLE_SECTIONS)
        assert "History" in out
        assert "Early shells" in out
        lines = out.splitlines()
        h_line = next(ln for ln in lines if "History" in ln)
        e_line = next(ln for ln in lines if "Early shells" in ln)
        assert len(e_line) - len(e_line.lstrip()) > len(h_line) - len(h_line.lstrip())

    def test_empty_sections_shows_message(self) -> None:
        assert "No sections" in _capture(render.render_section_list, [])

    def test_lead_section_excluded(self) -> None:
        sections = [
            {"title": "", "level": 0, "content": "Lead text."},
            {"title": "History", "level": 2, "content": "Content."},
        ]
        out = _capture(render.render_section_list, sections)
        assert "History" in out

    def test_shows_source_url_when_provided(self) -> None:
        out = _capture(
            render.render_section_list,
            SAMPLE_SECTIONS,
            page_url="https://en.wikipedia.org/wiki/Unix_shell",
        )
        assert "en.wikipedia.org/wiki/Unix_shell" in out

    def test_no_source_url_by_default(self) -> None:
        assert "Source" not in _capture(render.render_section_list, SAMPLE_SECTIONS)


# ---------------------------------------------------------------------------
# render_sections
# ---------------------------------------------------------------------------


class TestRenderSections:
    def test_raw_output(self, capsys) -> None:
        render.render_sections(
            SAMPLE_SECTIONS[:1],
            raw=True,
            page_url="https://en.wikipedia.org/wiki/Unix_shell",
        )
        out = capsys.readouterr().out
        assert "History" in out
        assert "1970s" in out
        assert "## History" in out
        assert "en.wikipedia.org/wiki/Unix_shell" in out

    def test_rich_output(self) -> None:
        out = _capture(
            render.render_sections,
            SAMPLE_SECTIONS,
            page_url="https://en.wikipedia.org/wiki/Unix_shell",
        )
        assert "History" in out
        assert "1970s" in out
        assert "en.wikipedia.org/wiki/Unix_shell" in out

    def test_no_source_url_by_default(self, capsys) -> None:
        render.render_sections(SAMPLE_SECTIONS[:1], raw=True)
        assert "Source" not in capsys.readouterr().out

    def test_empty_sections_shows_message(self) -> None:
        assert "No sections" in _capture(render.render_sections, [])

    def test_missing_fields_raw_does_not_raise(self, capsys) -> None:
        render.render_sections([{}], raw=True)
        capsys.readouterr()

    def test_missing_fields_rich_does_not_raise(self) -> None:
        _capture(render.render_sections, [{}])


# ---------------------------------------------------------------------------
# _table_to_markdown
# ---------------------------------------------------------------------------


class TestTableToMarkdown:
    def test_basic_structure(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE)
        assert "Year" in md
        assert "Title" in md
        assert "Role" in md
        assert "1997" in md
        assert "Caboose" in md
        assert "---" in md
        assert any(line.startswith("|") for line in md.splitlines())

    def test_caption_shown_italic(self) -> None:
        assert "*Film appearances*" in render._table_to_markdown(SAMPLE_TABLE)

    def test_no_headers_uses_data_rows(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE_NO_HEADERS)
        assert "a" in md and "b" in md

    def test_empty_table_returns_empty_string(self) -> None:
        empty = {"caption": "", "headers": [], "rows": []}
        assert render._table_to_markdown(empty) == ""


# ---------------------------------------------------------------------------
# _table_to_rich
# ---------------------------------------------------------------------------


class TestTableToRich:
    def test_basic_structure(self) -> None:
        from rich.table import Table as RichTable

        t = render._table_to_rich(SAMPLE_TABLE)
        assert isinstance(t, RichTable)
        assert len(t.columns) == 3
        assert t.row_count == 2
        assert t.title == "Film appearances"

    def test_no_headers_still_creates_columns(self) -> None:
        assert len(render._table_to_rich(SAMPLE_TABLE_NO_HEADERS).columns) == 2

    def test_empty_table_creates_no_columns(self) -> None:
        empty = {"caption": "", "headers": [], "rows": []}
        assert len(render._table_to_rich(empty).columns) == 0


# ---------------------------------------------------------------------------
# render_sections with tables
# ---------------------------------------------------------------------------


class TestRenderSectionsWithTables:
    def test_raw_renders_markdown_table(self, capsys) -> None:
        render.render_sections([SECTION_WITH_TABLE], raw=True)
        out = capsys.readouterr().out
        assert "Year" in out
        assert "1997" in out
        assert "|" in out
        assert "TV work" in out
        assert "## Filmography" in out

    def test_rich_renders_table(self) -> None:
        out = _capture(render.render_sections, [SECTION_WITH_TABLE])
        assert "Year" in out
        assert "1997" in out

    def test_section_no_table_still_renders(self, capsys) -> None:
        section = {
            "title": "History",
            "level": 2,
            "content": "Some history.",
            "tables": [],
        }
        render.render_sections([section], raw=True)
        assert "Some history." in capsys.readouterr().out

    def test_render_article_with_table(self) -> None:
        out = _capture(render.render_article, ARTICLE_WITH_TABLE)
        assert "Year" in out
        assert "1997" in out
