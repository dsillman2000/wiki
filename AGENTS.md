# AGENTS.md — wiki CLI Developer Guide

> This file provides onboarding and operational guidance for AI agents working on the wiki CLI project.

---

## Project Overview

- **Name:** wiki
- **Type:** CLI tool (Python Click application)
- **Purpose:** Fetch Wikipedia articles and display them in the terminal
- **Language:** Python (3.10+)
- **Repository:** https://github.com/dsillman2000/wiki-client
- **Main entry point:** `wiki` command (via `uvx wiki-client` or installed)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/dsillman2000/wiki-client.git
cd wiki

# Install dependencies
uv sync              # Install all dependencies (recommended)
pip install -e .     # Alternative: install in editable mode

# Verify setup
python -m pytest    # Run tests
ruff check           # Run linter

# Run the tool
wiki "Unix shell"
wiki -s History "Unix shell"
```

## Architecture

### Core Components

1. **wiki_cli/main.py** — Click CLI entry point
   - Parses CLI arguments with Click framework
   - Handles search, section extraction, and output modes
   - Routes to appropriate API and rendering functions

2. **wiki_cli/api.py** — Wikipedia API client
   - Fetches articles via Wikipedia REST API (HTTPX)
   - Parses HTML with BeautifulSoup
   - Handles search, URL resolution, and section extraction

3. **wiki_cli/render.py** — Terminal rendering
   - Rich-formatted output for terminal
   - Markdown output for raw/file mode
   - Table rendering for Wikipedia tables

4. **pyproject.toml** — Project configuration
   - Dependencies: click, httpx, rich, beautifulsoup4
   - Dev dependencies: ruff, pytest, pytest-httpx

### Data Flow

```
User query → URL resolution (search, direct URL, or Wikipedia URL)
  ↓
Wikipedia REST API via HTTPX
  ↓
BeautifulSoup parses HTML sections and tables
  ↓
Optional: section filtering (fuzzy match)
  ↓
Rich rendering (TTY) or Markdown (--raw, -o)
```

## Developer Setup

### Prerequisites

- Python 3.10+
- UV package manager (recommended) or pip
- Git

### Installation Commands

```bash
uv sync               # Install all dependencies (recommended)
pip install -e .     # Install in editable mode
pip install -e ".[dev]"  # Install with dev dependencies
```

### Verification

```bash
python -m pytest     # Run test suite (89 tests)
ruff check          # Run linter
ruff format --check # Check formatting
```

## Coding Conventions

### Python Style Guide

- **Type hints:** Use for all function parameters and return values
- **Imports:** Use `from __future__ import annotations` for forward references
- **Docstrings:** Google-style docstrings for public functions
- **Line length:** 88 characters (ruff default)

### Example Function

```python
from __future__ import annotations

def fetch_article(query: str) -> dict[str, Any]:
    """Fetch a Wikipedia article by title or URL.

    Args:
        query: Article title, search terms, or Wikipedia URL.

    Returns:
        Article dict with title, sections, content_urls, etc.

    Raises:
        ValueError: If no article found.
    """
    # implementation
```

### Linting

All Python code must pass ruff with no warnings:

```bash
ruff check           # Run linter
ruff format          # Format code
ruff check tests/    # Lint tests
```

### Testing

```bash
python -m pytest                    # Run all tests
python -m pytest tests/test_api.py  # Run specific test file
python -m pytest -v                 # Verbose output
```

Test conventions:

- Use `pytest.mark.parametrize` for similar test cases
- Use `HTTPXMock` for mocking HTTP requests
- Aim for ≤100 tests while maintaining 100% coverage

## Git Workflow

### Branch Naming

- `main` — stable, deployable code
- Feature branches: `feature/short-description` or `fix/issue-number-description`
- Use lowercase and hyphens
- Copilot work: `copilot/migrate-bash-to-python-click-cli`

### Commits

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:

```
feat(section): Add support for fuzzy section matching

- Normalize headings to lowercase alphanumeric
- Use substring matching for flexible section selection
- Include parent sections when extracting nested subsections

Closes #2
```

### Pull Requests

- Open PRs against `main`
- Ensure all CI checks pass
- Request review from repository owner
- All 89 tests must pass

## Common Tasks

### Adding a New CLI Option

1. Add option to `@click.option` decorator in `main.py`
2. Add parameter to `cli()` function signature
3. Add handler logic in `_run()` function
4. Update docstring examples
5. Add tests for new option
6. Run `ruff check` and `python -m pytest`
7. Commit with appropriate message

### Adding a New API Function

1. Add function to `api.py`
2. Add tests in `tests/test_api.py`
3. If public function, add to module `__all__` if needed
4. Update docstrings and type hints
5. Run full test suite

### Adding a New Rendering Feature

1. Add function to `render.py`
2. Add tests in `tests/test_render.py`
3. Test both raw and rich output modes
4. Update docstrings
5. Run tests to verify

### Testing the Tool Manually

```bash
# Basic fetch
wiki "Bash"

# Section extraction
wiki -s History "Unix shell"
wiki -s "hist" "Unix shell"        # fuzzy match

# List sections
wiki -ls "Unix shell"

# Search mode
wiki --search "shell programming"

# Raw output
wiki --raw "Bash"

# Save to file
wiki "Bash" -o bash.md

# Direct URL
wiki "https://en.wikipedia.org/wiki/Unix_shell"

# Check version
wiki --version
```

## Project Structure

```
wiki/
├── .github/              # GitHub workflows
│   └── workflows/         # CI/CD pipelines
├── .vscode/              # VSCode settings (optional)
├── agents/               # Agent prompts and guides
│   └── Wikipedia.md      # Wikipedia research agent prompt
├── tests/                # Test suite
│   ├── test_api.py       # API tests (59 tests)
│   └── test_render.py    # Render tests (30 tests)
├── wiki_cli/             # Main package
│   ├── __init__.py       # Package init
│   ├── __version__.py    # Version info
│   ├── api.py            # Wikipedia API client
│   ├── main.py           # Click CLI entry point
│   └── render.py         # Terminal rendering
├── AGENTS.md             # This file
├── pyproject.toml        # Project configuration
└── SKILL.md              # Tool skill description
```

## Design Decisions

### Why Python + Click?

- **Click**: Battle-tested CLI framework with built-in argument parsing, help generation, and shell completion
- **Rich**: Beautiful terminal output with tables, progress bars, and markdown rendering
- **HTTPX**: Modern async-capable HTTP client with excellent error handling
- **BeautifulSoup4**: Robust HTML parsing for Wikipedia HTML structure
- **Ruff**: Extremely fast Python linter (10-100x faster than traditional linters)

### Why Wikipedia REST API?

Instead of scraping HTML with htmlq, we use the Wikipedia REST API:

```
https://en.wikipedia.org/api/rest_v1/page/summary/{title}
https://en.wikipedia.org/api/rest_v1/page/html/{title}
```

Benefits:

- Returns structured JSON for metadata
- Returns clean HTML for content
- No need for htmlq or pandoc
- More reliable than HTML scraping

### Why BeautifulSoup?

- Handles Wikipedia's complex HTML structure
- CSS selectors for extracting sections and tables
- Proper handling of nested tags
- More maintainable than regex parsing

## CLI Options

| Option                  | Description                                     |
| ----------------------- | ----------------------------------------------- |
| `QUERY`                 | Article title, search terms, or Wikipedia URL   |
| `-s, --section SECTION` | Extract matching sections (fuzzy, repeatable)   |
| `-ls, --list-sections`  | List all sections in article                    |
| `--search`              | Show search results instead of fetching         |
| `--raw`                 | Plain text/Markdown output (no Rich formatting) |
| `-o, --output FILE`     | Write output to FILE                            |
| `--version`             | Show version                                    |
| `-h, --help`            | Show help                                       |

## Exit Codes

- `0` — Success
- `1` — General error
- `2` — Click usage error

## Reporting Issues

When filing issues, include:

- Output of `wiki --version`
- The exact command that failed
- Expected vs actual behavior
- Any relevant output (`wiki --raw "query"` for debugging)

## Notes for Agents

- **Run tests before committing.** `python -m pytest` must pass.
- **Run linter before committing.** `ruff check .` must pass.
- **Sign off all GitHub communications** written via `gh` CLI with "_Written by OpenCode._" on its own line. This applies to:
  - PR descriptions and titles
  - PR comments and reviews
  - Issue titles and descriptions
  - Issue comments
- **Test manually before committing** when possible.
- **Update documentation** when changing behavior, adding features, or modifying architecture.
- **Check existing issues** before creating new ones.
- **Use conventional commits** for clear changelog generation.
- **Maintain test coverage** at 100% while keeping test count ≤100.
- **Verify CI passes** before merging PRs.
