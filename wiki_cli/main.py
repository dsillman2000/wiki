"""Click CLI entry point for wiki-cli."""

from __future__ import annotations

import importlib
import sys

import click
import httpx

from wiki_cli import __version__, api, render


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
    "--check",
    "check_mode",
    is_flag=True,
    help="Check that required Python dependencies are importable.",
)
@click.version_option(version=__version__, prog_name="wiki")
def cli(query: tuple[str, ...], search_mode: bool, raw: bool, check_mode: bool) -> None:
    """Fetch a Wikipedia article and display it in the terminal.

    QUERY is the article title or search terms.  When QUERY looks like a
    URL (starts with http:// or https://) the page is fetched directly.

    Examples:

    \b
      wiki "Unix shell"
      wiki --search "shell programming"
      wiki --raw "Bash (Unix shell)"
    """
    if check_mode:
        _check_dependencies()
        return

    if not query:
        raise click.UsageError("QUERY is required unless --check is given.")

    query_str = " ".join(query)

    try:
        if search_mode:
            results = api.search(query_str)
            render.render_search_results(results, query=query_str)
        else:
            data = api.fetch_article(query_str)
            render.render_article(data, raw=raw)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise click.ClickException(
            f"HTTP error {exc.response.status_code} fetching article: {query_str!r}"
        ) from exc
    except httpx.RequestError as exc:
        raise click.ClickException(
            f"Network error fetching article: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

_REQUIRED_MODULES = ["click", "httpx", "rich"]


def _check_dependencies() -> None:
    """Print the status of each required Python package."""
    all_ok = True
    for module in _REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            click.echo(f"{module}: OK")
        except ImportError:
            click.echo(f"{module}: missing")
            all_ok = False

    if not all_ok:
        sys.exit(1)
