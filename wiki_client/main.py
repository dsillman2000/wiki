"""Click CLI entry point for wiki-client."""

from __future__ import annotations

import contextlib

import click
import httpx

from wiki_client import __version__, api, render


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("query", nargs=-1, metavar="QUERY")
@click.option(
    "--search",
    "search_mode",
    is_flag=True,
    help="Show search results instead of fetching the first match.",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Print plain text instead of Rich-formatted output.",
)
@click.option(
    "--list-sections",
    "--ls",
    "list_sections",
    is_flag=True,
    help="List all sections in the article.",
)
@click.option(
    "--section",
    "-s",
    "section_filter",
    multiple=True,
    metavar="SECTION",
    help="Extract sections whose title matches SECTION (fuzzy, repeatable).",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, dir_okay=False),
    default=None,
    metavar="FILE",
    help="Write output to FILE in plain-text/Markdown format.",
)
@click.option(
    "--random",
    is_flag=True,
    help="Fetch a random Wikipedia article.",
)
@click.version_option(version=__version__, prog_name="wiki")
def cli(
    query: tuple[str, ...],
    search_mode: bool,
    raw: bool,
    list_sections: bool,
    section_filter: tuple[str, ...],
    output: str | None,
    random: bool,
) -> None:
    """Fetch a Wikipedia article and display it in the terminal.

    QUERY is the article title, search terms, or a Wikipedia URL.

    Examples:

    \b
      wiki "Unix shell"
      wiki --search "shell programming"
      wiki --raw "Bash (Unix shell)"
      wiki --list-sections "Unix shell"
      wiki -s History "Unix shell"
      wiki "https://en.wikipedia.org/wiki/Unix_shell"
      wiki -o article.md "Unix shell"
      wiki --random
      wiki --random --raw
      wiki --random -o random_article.md
      wiki --random --ls
    """
    # Validate incompatible flag combinations
    if random and section_filter:
        raise click.UsageError("--random cannot be used with --section/-s")

    if random and query:
        raise click.UsageError("QUERY cannot be provided with --random")

    if not random and not query:
        raise click.UsageError("QUERY is required (or use --random).")

    query_str = " ".join(query)

    # When writing to a file, force plain-text (no ANSI escape codes)
    if output:
        raw = True

    def _run() -> None:
        try:
            if random:
                data = api.fetch_random_article()
                flat_sections = api.flatten_sections(data.get("sections", []))
                page_url = (
                    data.get("content_urls", {}).get("desktop", {}).get("page", "")
                )
                if list_sections:
                    render.render_section_list(flat_sections, page_url=page_url)
                else:
                    render.render_article(data, raw=raw)
            elif search_mode:
                results = api.search(query_str)
                render.render_search_results(results, query=query_str)
            elif list_sections or section_filter:
                # Both modes need the full article to get the canonical page URL
                data = api.fetch_article(query_str)
                flat_sections = api.flatten_sections(data.get("sections", []))
                page_url = (
                    data.get("content_urls", {}).get("desktop", {}).get("page", "")
                )
                if list_sections:
                    render.render_section_list(flat_sections, page_url=page_url)
                else:
                    matched = api.filter_sections(flat_sections, section_filter)
                    render.render_sections(matched, raw=raw, page_url=page_url)
            else:
                data = api.fetch_article(query_str)
                render.render_article(data, raw=raw)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            if random:
                raise click.ClickException(
                    f"HTTP error {exc.response.status_code} fetching random article"
                ) from exc
            else:
                raise click.ClickException(
                    f"HTTP error {exc.response.status_code} fetching article: "
                    f"{query_str!r}"
                ) from exc
        except httpx.RequestError as exc:
            if random:
                raise click.ClickException(
                    f"Network error fetching random article: {exc}"
                ) from exc
            else:
                raise click.ClickException(
                    f"Network error fetching article: {exc}"
                ) from exc

    if output:
        with open(output, "w") as fh:
            with contextlib.redirect_stdout(fh):
                _run()
    else:
        _run()
