"""Rich-based terminal rendering for wiki-cli."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

console = Console()


def render_article(data: dict, *, raw: bool = False) -> None:
    """Render a Wikipedia article summary to the terminal.

    Args:
        data: Summary dict returned by the Wikipedia REST API.
        raw:  When *True*, emit plain text instead of Rich markup.
    """
    title = data.get("title", "")
    description = data.get("description", "")
    extract = data.get("extract", "")
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

    if raw:
        if title:
            print(f"# {title}")
            print()
        if description:
            print(description)
            print()
        if extract:
            print(extract)
        if page_url:
            print()
            print(f"Source: <{page_url}>")
        return

    md_parts: list[str] = []
    if title:
        md_parts.append(f"# {title}")
        if description:
            md_parts.append(f"*{description}*")
        md_parts.append("")
    if extract:
        md_parts.append(extract)
    if page_url:
        md_parts.append("")
        md_parts.append(f"*Source: <{page_url}>*")

    console.print(Markdown("\n".join(md_parts)))


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
