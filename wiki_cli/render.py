"""Rich-based terminal rendering for wiki-cli."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

console = Console()


def render_article(data: dict, *, raw: bool = False) -> None:
    """Render a Wikipedia article to the terminal.

    Renders the title, description, all section content (from ``data["sections"]``),
    and a Source link.  Falls back to the short ``extract`` field when no
    sections are present (e.g. if the HTML fetch failed).

    Args:
        data: Article dict returned by :func:`~wiki_cli.api.fetch_article`.
        raw:  When *True*, emit plain text instead of Rich markup.
    """
    title = data.get("title", "")
    description = data.get("description", "")
    extract = data.get("extract", "")
    sections = data.get("sections", [])
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

    if raw:
        if title:
            print(f"# {title}")
            print()
        if description:
            print(description)
            print()
        if sections:
            _render_section_tree_raw(sections)
        elif extract:
            print(extract)
        if page_url:
            print()
            print(f"Source: <{page_url}>")
        return

    # Rich mode — render title/description header
    md_parts: list[str] = []
    if title:
        md_parts.append(f"# {title}")
        if description:
            md_parts.append(f"*{description}*")
        md_parts.append("")
    if md_parts:
        console.print(Markdown("\n".join(md_parts)))

    if sections:
        _render_section_tree_rich(sections)
    elif extract:
        console.print(Markdown(extract))

    if page_url:
        console.print(Markdown(f"*Source: <{page_url}>*"))


def _render_section_tree_raw(sections: list[dict]) -> None:
    """Recursively render a hierarchical section tree as plain text.

    Args:
        sections: List of section dicts (may include ``subsections``).
    """
    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")
        level = section.get("level", 2)
        subsections = section.get("subsections", [])

        if title:
            print(f"{'#' * level} {title}")
            print()
        if content:
            print(content)
            print()
        _render_section_tree_raw(subsections)


def _render_section_tree_rich(sections: list[dict]) -> None:
    """Recursively render a hierarchical section tree with Rich Markdown.

    Args:
        sections: List of section dicts (may include ``subsections``).
    """
    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")
        level = section.get("level", 2)
        subsections = section.get("subsections", [])

        md_parts: list[str] = []
        if title:
            md_parts.append(f"{'#' * level} {title}")
            md_parts.append("")
        if content:
            md_parts.append(content)
        if md_parts:
            console.print(Markdown("\n".join(md_parts)))
            console.print()

        _render_section_tree_rich(subsections)


def render_search_results(results: list[dict], query: str) -> None:
    """Render Wikipedia search results as a Rich table.

    Args:
        results: List of result dicts (title, snippet, url).
        query:   Original search query string, used in the heading.
    """
    if not results:
        console.print(f'[yellow]No results found for:[/yellow] "{query}"')
        return

    table = Table(
        title=f'Search results for "{query}"',
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Title", style="bold", min_width=20)
    table.add_column("Snippet", overflow="fold")
    table.add_column("URL", style="blue underline", overflow="fold")

    for idx, result in enumerate(results, start=1):
        table.add_row(
            str(idx),
            result.get("title", ""),
            result.get("snippet", ""),
            result.get("url", ""),
        )

    console.print(table)


def render_section_list(sections: list[dict], *, page_url: str = "") -> None:
    """Render a numbered list of article section titles (table of contents).

    The lead section (empty title) is omitted.  Sub-sections are indented
    according to their heading level.

    Args:
        sections: Flat list of section dicts (``title``, ``level``).
        page_url: Optional article URL to show as a Source link at the bottom.
    """
    named = [s for s in sections if s.get("title")]
    if not named:
        console.print("[yellow]No sections found.[/yellow]")
        return

    for section in named:
        indent = "  " * max(0, section["level"] - 2)
        console.print(f"{indent}[bold]{section['title']}[/bold]")

    if page_url:
        console.print()
        console.print(Markdown(f"*Source: <{page_url}>*"))


def render_sections(
    sections: list[dict], *, raw: bool = False, page_url: str = ""
) -> None:
    """Render the content of one or more article sections.

    Args:
        sections: Flat list of section dicts to display.
        raw:      When *True*, emit plain text instead of Rich markup.
        page_url: Optional article URL to show as a Source link at the bottom.
    """
    if not sections:
        console.print("[yellow]No sections to display.[/yellow]")
        return

    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")
        level = section.get("level", 2)

        if raw:
            if title:
                print(f"{'#' * level} {title}")
                print()
            if content:
                print(content)
                print()
        else:
            md_parts: list[str] = []
            if title:
                md_parts.append(f"{'#' * level} {title}")
                md_parts.append("")
            if content:
                md_parts.append(content)
            if md_parts:
                console.print(Markdown("\n".join(md_parts)))
                console.print()

    if page_url:
        if raw:
            print()
            print(f"Source: <{page_url}>")
        else:
            console.print(Markdown(f"*Source: <{page_url}>*"))
