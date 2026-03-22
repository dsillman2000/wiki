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

    def test_raw_includes_extract(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        captured = capsys.readouterr()
        assert "command-line interpreter" in captured.out

    def test_raw_includes_source_url(self, capsys) -> None:
        render.render_article(SAMPLE_DATA, raw=True)
        captured = capsys.readouterr()
        assert "en.wikipedia.org/wiki/Unix_shell" in captured.out

    def test_rich_includes_title(self) -> None:
        output = _capture(render.render_article, SAMPLE_DATA)
        assert "Unix shell" in output

    def test_rich_includes_extract(self) -> None:
        output = _capture(render.render_article, SAMPLE_DATA)
        assert "command-line interpreter" in output

    def test_missing_fields_do_not_raise(self, capsys) -> None:
        render.render_article({}, raw=True)
        captured = capsys.readouterr()
        # Should produce no output (empty dict), not raise
        assert captured.out == ""

    def test_rich_mode_missing_fields_do_not_raise(self) -> None:
        # The Rich rendering path must also handle missing/empty data gracefully
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
        # The URL may be word-wrapped by Rich's table column; check for a stable
        # fragment that will always be present regardless of wrapping.
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
        # Lead (empty title) should not contribute a blank title line
        assert "History" in output

    def test_sub_section_indented(self) -> None:
        output = _capture(render.render_section_list, SAMPLE_SECTIONS)
        lines = output.splitlines()
        history_line = next(line for line in lines if "History" in line)
        early_line = next(line for line in lines if "Early shells" in line)
        # Early shells (h3) should have more leading spaces than History (h2)
        assert len(early_line) - len(early_line.lstrip()) > len(history_line) - len(
            history_line.lstrip()
        )


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

    def test_rich_mode_includes_title(self) -> None:
        output = _capture(render.render_sections, SAMPLE_SECTIONS)
        assert "History" in output

    def test_rich_mode_includes_content(self) -> None:
        output = _capture(render.render_sections, SAMPLE_SECTIONS)
        assert "1970s" in output

    def test_empty_sections_shows_message(self) -> None:
        output = _capture(render.render_sections, [])
        assert "No sections" in output

    def test_missing_fields_do_not_raise(self, capsys) -> None:
        render.render_sections([{}], raw=True)
        capsys.readouterr()  # should not raise

    def test_rich_missing_fields_do_not_raise(self) -> None:
        _capture(render.render_sections, [{}])
