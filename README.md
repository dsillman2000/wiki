# wiki-client

[![PyPI Version](https://img.shields.io/pypi/v/wiki-client)](https://pypi.org/project/wiki-client/)
[![Python Versions](https://img.shields.io/pypi/pyversions/wiki-client)](https://pypi.org/project/wiki-client/)

A command-line tool to fetch Wikipedia articles and display them in the terminal.

## Overview

`wiki` is a Python CLI that retrieves Wikipedia articles via the
[Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) and renders them with
[Rich](https://github.com/Textualize/rich) for a beautiful terminal experience.

## Features

- **Fetch articles** — Query Wikipedia by article title or search query
- **Search mode** — Show a ranked list of search results
- **Featured articles** — Fetch Wikipedia's daily featured article
- **Random articles** — Fetch random Wikipedia articles
- **Most-read articles** — Fetch Wikipedia's most-read articles for yesterday
- **Daily news** — Fetch Wikipedia's "In the news" stories
- **Raw output** — Print plain text instead of Rich-formatted output
- **AI Agent Skills** — Ready-to-use skill files for OpenCode, Copilot, Claude, Codex, Windsurf, Aider, and Cursor

## Requirements

- Python 3.10 or newer

The following Python packages are installed automatically:

| Package                                     | Purpose                            |
| ------------------------------------------- | ---------------------------------- |
| [click](https://click.palletsprojects.com/) | CLI argument parsing               |
| [httpx](https://www.python-httpx.org/)      | HTTP requests to the Wikipedia API |
| [rich](https://rich.readthedocs.io/)        | Terminal formatting and rendering  |

## Installation

### Recommended: `uvx` (no permanent install required)

The easiest way to run `wiki` is with
[`uvx`](https://docs.astral.sh/uv/guides/tools/) from the
[uv](https://docs.astral.sh/uv/) toolkit. This downloads and runs the tool in
an isolated environment without permanently installing it:

```bash
uvx --from wiki-client wiki "Unix shell"
```

Install `uv` (if you haven't already):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### `pip install` (permanent install)

Installing via pip places the `wiki` command on your `$PATH` directly:

```bash
pip install wiki-client
wiki "Unix shell"
```

### Install from source

```bash
git clone https://github.com/dsillman2000/wiki-client.git
cd wiki-client
pip install .
wiki "Unix shell"
```

Or use the provided install script:

```bash
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install.sh | sh
```

### Install AI Agent Skills

The wiki CLI includes skill files for various AI agents. Install them directly from GitHub without cloning the repository:

#### Remote Installation (Recommended)

Use the unified installer script with the `-a` flag to specify the agent:

```bash
# Install for OpenCode
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a opencode

# Install for GitHub Copilot
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a copilot

# Install for Claude
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a claude

# Install for Codex
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a codex

# Install for Windsurf (Codeium)
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a windsurf

# Install for Aider
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a aider

# Install for Cursor
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki-client/main/install/skill.sh | sh -s -- -a cursor
```

#### Local Installation

If you have cloned the repository, you can install locally:

```bash
# Install for OpenCode
./install/skill.sh -a opencode

# Install for GitHub Copilot
./install/skill.sh -a copilot

# Install for Claude
./install/skill.sh -a claude

# Install for Codex
./install/skill.sh -a codex

# Install for Windsurf (Codeium)
./install/skill.sh -a windsurf

# Install for Aider
./install/skill.sh -a aider

# Install for Cursor
./install/skill.sh -a cursor
```

Show help:

```bash
./install/skill.sh -h
```

### Docker

A Docker image is available on GitHub Container Registry (GHCR) with all
dependencies pre-installed:

```bash
# Pull the image
docker pull ghcr.io/dsillman2000/wiki-client:latest

# Run a query
docker run --rm ghcr.io/dsillman2000/wiki-client:latest "Unix shell"

# Extract specific section
docker run --rm ghcr.io/dsillman2000/wiki-client:latest -s History "Bash"

# List sections
docker run --rm ghcr.io/dsillman2000/wiki-client:latest --ls "Python"

# Save output to file (mount current directory)
docker run --rm -v "$(pwd)":/home/wiki ghcr.io/dsillman2000/wiki-client:latest \
  "Operating system" -o os.md
```

**Advantages:**

- No local dependency installation required
- Consistent environment across systems
- Easy integration into CI/CD pipelines
- Lightweight multi-stage build (~218MB)

## Usage

### Basic Queries

```bash
# Fetch an article
wiki "Unix shell"

# Print plain text (no Rich formatting)
wiki "Unix shell" --raw
```

### Search Mode

```bash
# Show search results instead of auto-fetching
wiki --search "shell programming"
```

### Section Listing & Filtering

```bash
# List all sections in an article
wiki --list-sections "Unix shell"
wiki --ls "Unix shell"          # shorthand

# Extract a specific section (fuzzy match)
wiki -s History "Unix shell"
wiki -s "early" "Unix shell"    # matches "Early shells", "Early history", etc.

# Multiple sections
wiki -s History -s "See also" "Unix shell"
```

### Featured & Random Articles

```bash
# Fetch today's featured Wikipedia article
wiki --featured

# Extract specific section from featured article
wiki --featured -s "Early life"

# Fetch featured article for specific date
wiki --featured --featured-date 2025-03-23
wiki --featured-date 2025-03-23  # --featured-date implies --featured

# Extract section from specific date's featured article
wiki --featured-date 2025-03-23 -s "Storyline"

# List sections of featured article
wiki --featured --ls

# Fetch a random Wikipedia article
wiki --random

# Save random article to file
wiki --random -o random_article.md
```

### Most-Read & News

```bash
# Fetch yesterday's most-read Wikipedia articles
wiki --most-read

# Extract specific article from most-read list
wiki --most-read -s "Eiffel Tower"

# Fetch most-read articles for specific date
wiki --most-read --most-read-date 2026-03-23
wiki --most-read-date 2026-03-23  # --most-read-date implies --most-read

# List most-read articles (compact view)
wiki --most-read --ls

# Save most-read to file
wiki --most-read -o most_read.md

# Fetch today's "In the news" stories
wiki --news
wiki --news --raw
wiki --news -o news.md
wiki --news --ls
```

### Version

```bash
wiki --version
```

## Examples

```bash
# Get the Unix shell article
wiki "Unix shell"

# Search for shell-related articles
wiki --search "shell interpreters"

# Print raw text
wiki "Bash (Unix shell)" --raw

# List all sections
wiki --ls "Unix shell"

# Read the History section
wiki -s History "Unix shell"
```

## Development

### Quick Start

```bash
# Install in editable mode with dev dependencies
pip install -e .
pip install pytest pytest-httpx ruff

# Or use Make
make install-dev
```

### Linting & Testing

```bash
make lint       # ruff + shellcheck + prettier
make lint-python  # ruff only
make test       # pytest
```

Or run directly:

```bash
ruff check wiki_client/ tests/
python -m pytest tests/ -v
```

### Available Make Targets

```bash
make help           # Show all targets
make install        # pip install -e .
make install-dev    # Install dev dependencies
make lint           # Run all linting checks
make lint-python    # ruff
make lint-shell     # shellcheck
make lint-markdown  # prettier
make test           # pytest
make format         # prettier --write README.md
make clean          # Remove build artifacts
```

## How It Works

1. **Query resolution** — Tries a direct Wikipedia REST API title lookup; falls
   back to a full-text search if the title returns 404.
2. **Rendering** — Uses Rich to render the article extract as formatted Markdown
   in the terminal. Pass `--raw` for plain-text output.

## Version

1.0.0

## License

MIT
