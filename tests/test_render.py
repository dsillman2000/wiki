"""Unit tests for wiki_cli.render."""

from __future__ import annotations

import io

from rich.console import Console

from wiki_cli import render


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
            "subsections": [
                {
                    "id": "Early_shells",
                    "title": "Early shells",
                    "level": 3,
                    "content": "The Thompson shell came first.",
                    "subsections": [],
                }
            ],
        }
    ],
    "content_urls": {
        "desktop": {"page": "https://en.wikipedia.org/wiki/Unix_shell"}
    },
}

SAMPLE_SECTIONS = [
    {
        "title": "History",
        "level": 2,
        "content": "The shell was developed in the 1970s.",
    },
    {
        "title": "Early shells",
        "level": 3,
        "content": "The Thompson shell came first.",
    },
]


class TestRenderArticle:
    def test_raw_includes_title(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        captured = capsys.readouterr()
        assert "# Unix shell" in captured.out

    def test_raw_includes_section_content(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        captured = capsys.readouterr()
        assert "1970s" in captured.out

    def test_raw_includes_subsection_content(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        captured = capsys.readouterr()
        assert "Thompson" in captured.out

    def test_raw_includes_source_url(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        captured = capsys.readouterr()
        assert "en.wikipedia.org/wiki/Unix_shell" in captured.out

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
        captured = capsys.readouterr()
        assert "command-line interpreter" in captured.out

    def test_rich_includes_title(self) -> None:
        output = _capture(render.render_article, SAMPLE_DATA)
        assert "Unix shell" in output

    def test_rich_includes_section_content(self) -> None:
        output = _capture(render.render_article, SAMPLE_DATA)
        assert "1970s" in output

    def test_rich_includes_subsection_content(self) -> None:
        output = _capture(render.render_article, SAMPLE_DATA)
        assert "Thompson" in output

    def test_rich_includes_source_url(self) -> None:
        output = _capture(render.render_article, SAMPLE_DATA)
        assert "en.wikipedia.org/wiki/Unix_shell" in output

    def test_missing_fields_do_not_raise(self, capsys) -> None:
        render.render_article({}, raw=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_rich_mode_missing_fields_do_not_raise(self) -> None:
        _capture(render.render_article, {})


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

    def test_shows_titles(self) -> None:
        output = _capture(
            render.render_search_results, self.RESULTS, query="Unix shell"
        )
        assert "Unix shell" in output

    def test_shows_urls(self) -> None:
        output = _capture(
            render.render_search_results, self.RESULTS, query="Unix shell"
        )
        assert "wikipedia" in output

    def test_empty_results_shows_no_results_message(self) -> None:
        output = _capture(render.render_search_results, [], query="xyzzy")
        assert "xyzzy" in output

    def test_shows_query_in_heading(self) -> None:
        output = _capture(render.render_search_results, self.RESULTS, query="my query")
        assert "my query" in output


class TestRenderSectionList:
    def test_shows_section_titles(self) -> None:
        output = _capture(render.render_section_list, SAMPLE_SECTIONS)
        assert "History" in output
        assert "Early shells" in output

    def test_empty_sections_shows_message(self) -> None:
        output = _capture(render.render_section_list, [])
        assert "No sections" in output

    def test_lead_section_excluded(self) -> None:
        sections = [
            {"title": "", "level": 0, "content": "Lead text."},
            {"title": "History", "level": 2, "content": "Content."},
        ]
        output = _capture(render.render_section_list, sections)
        assert "History" in output

    def test_sub_section_indented(self) -> None:
        output = _capture(render.render_section_list, SAMPLE_SECTIONS)
        lines = output.splitlines()
        history_line = next(line for line in lines if "History" in line)
        early_line = next(line for line in lines if "Early shells" in line)
        assert len(early_line) - len(early_line.lstrip()) > len(history_line) - len(
            history_line.lstrip()
        )

    def test_shows_source_url_when_provided(self) -> None:
        output = _capture(
            render.render_section_list,
            SAMPLE_SECTIONS,
            page_url="https://en.wikipedia.org/wiki/Unix_shell",
        )
        assert "en.wikipedia.org/wiki/Unix_shell" in output

    def test_no_source_url_by_default(self) -> None:
        output = _capture(render.render_section_list, SAMPLE_SECTIONS)
        assert "Source" not in output


class TestRenderSections:
    def test_raw_includes_title(self, capsys) -> None:
        render.render_sections(SAMPLE_SECTIONS[:1], raw=True)
        captured = capsys.readouterr()
        assert "History" in captured.out

    def test_raw_includes_content(self, capsys) -> None:
        render.render_sections(SAMPLE_SECTIONS[:1], raw=True)
        captured = capsys.readouterr()
        assert "1970s" in captured.out

    def test_raw_heading_level_prefix(self, capsys) -> None:
        render.render_sections(SAMPLE_SECTIONS[:1], raw=True)
        captured = capsys.readouterr()
        assert "## History" in captured.out

    def test_raw_includes_source_url(self, capsys) -> None:
        render.render_sections(
            SAMPLE_SECTIONS[:1],
            raw=True,
            page_url="https://en.wikipedia.org/wiki/Unix_shell",
        )
        captured = capsys.readouterr()
        assert "en.wikipedia.org/wiki/Unix_shell" in captured.out

    def test_rich_mode_includes_title(self) -> None:
        output = _capture(render.render_sections, SAMPLE_SECTIONS)
        assert "History" in output

    def test_rich_mode_includes_content(self) -> None:
        output = _capture(render.render_sections, SAMPLE_SECTIONS)
        assert "1970s" in output

    def test_rich_mode_includes_source_url(self) -> None:
        output = _capture(
            render.render_sections,
            SAMPLE_SECTIONS,
            page_url="https://en.wikipedia.org/wiki/Unix_shell",
        )
        assert "en.wikipedia.org/wiki/Unix_shell" in output

    def test_no_source_url_by_default(self, capsys) -> None:
        render.render_sections(SAMPLE_SECTIONS[:1], raw=True)
        captured = capsys.readouterr()
        assert "Source" not in captured.out

    def test_empty_sections_shows_message(self) -> None:
        output = _capture(render.render_sections, [])
        assert "No sections" in output

    def test_missing_fields_do_not_raise(self, capsys) -> None:
        render.render_sections([{}], raw=True)
        capsys.readouterr()

    def test_rich_missing_fields_do_not_raise(self) -> None:
        _capture(render.render_sections, [{}])


# ---------------------------------------------------------------------------
# Table rendering tests
# ---------------------------------------------------------------------------

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


class TestTableToMarkdown:
    def test_headers_in_output(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE)
        assert "Year" in md
        assert "Title" in md
        assert "Role" in md

    def test_rows_in_output(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE)
        assert "1997" in md
        assert "Caboose" in md

    def test_separator_row_present(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE)
        assert "---" in md

    def test_caption_shown_italic(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE)
        assert "*Film appearances*" in md

    def test_no_headers_uses_empty_header_row(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE_NO_HEADERS)
        assert "a" in md
        assert "b" in md

    def test_empty_table_returns_empty_string(self) -> None:
        t = {"caption": "", "headers": [], "rows": []}
        assert render._table_to_markdown(t) == ""

    def test_pipe_delimited_format(self) -> None:
        md = render._table_to_markdown(SAMPLE_TABLE)
        lines = md.splitlines()
        assert any(line.startswith("|") for line in lines)


class TestTableToRich:
    def test_returns_rich_table_object(self) -> None:
        from rich.table import Table as RichTable

        t = render._table_to_rich(SAMPLE_TABLE)
        assert isinstance(t, RichTable)

    def test_column_count_matches_headers(self) -> None:
        t = render._table_to_rich(SAMPLE_TABLE)
        assert len(t.columns) == 3

    def test_row_count_matches(self) -> None:
        t = render._table_to_rich(SAMPLE_TABLE)
        assert t.row_count == 2

    def test_caption_set(self) -> None:
        t = render._table_to_rich(SAMPLE_TABLE)
        assert t.title == "Film appearances"

    def test_no_headers_still_creates_columns(self) -> None:
        t = render._table_to_rich(SAMPLE_TABLE_NO_HEADERS)
        assert len(t.columns) == 2

    def test_empty_table_creates_no_columns(self) -> None:
        t = render._table_to_rich({"caption": "", "headers": [], "rows": []})
        assert len(t.columns) == 0


class TestRenderSectionsWithTables:
    def test_raw_includes_table_markdown(self, capsys) -> None:
        render.render_sections([SECTION_WITH_TABLE], raw=True)
        captured = capsys.readouterr()
        assert "Year" in captured.out
        assert "1997" in captured.out
        assert "|" in captured.out

    def test_raw_content_still_present(self, capsys) -> None:
        render.render_sections([SECTION_WITH_TABLE], raw=True)
        captured = capsys.readouterr()
        assert "TV work" in captured.out

    def test_rich_includes_table(self) -> None:
        output = _capture(render.render_sections, [SECTION_WITH_TABLE])
        assert "Year" in output
        assert "1997" in output

    def test_no_table_data_in_content_text(self, capsys) -> None:
        # Table headers should appear as table, not as garbled content text
        render.render_sections([SECTION_WITH_TABLE], raw=True)
        captured = capsys.readouterr()
        # "Year" must appear exactly inside the table part (after heading)
        assert "## Filmography" in captured.out

    def test_section_no_table_still_renders(self, capsys) -> None:
        section = {
            "title": "History",
            "level": 2,
            "content": "Some history.",
            "tables": [],
        }
        render.render_sections([section], raw=True)
        captured = capsys.readouterr()
        assert "Some history." in captured.out


class TestRenderArticleWithTables:
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
        "content_urls": {
            "desktop": {"page": "https://en.wikipedia.org/wiki/Sam_Seder"}
        },
    }

    def test_raw_article_includes_table(self, capsys) -> None:
        render.render_article(self.ARTICLE_WITH_TABLE, raw=True)
        captured = capsys.readouterr()
        assert "Year" in captured.out
        assert "|" in captured.out

    def test_rich_article_includes_table(self) -> None:
        output = _capture(render.render_article, self.ARTICLE_WITH_TABLE)
        assert "Year" in output

    def test_raw_table_not_garbled_in_content(self, capsys) -> None:
        render.render_article(self.ARTICLE_WITH_TABLE, raw=True)
        captured = capsys.readouterr()
        # Should not see "Year" mixed into the paragraph content
        lines = captured.out.splitlines()
        content_line_idx = next(
            (i for i, line in enumerate(lines) if "TV work" in line), None
        )
        assert content_line_idx is not None
