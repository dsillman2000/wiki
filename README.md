# wiki

A command-line tool to fetch Wikipedia articles and display them in the terminal.

## Overview

`wiki` is a Python CLI that retrieves Wikipedia articles via the
[Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) and renders them with
[Rich](https://github.com/Textualize/rich) for a beautiful terminal experience.

## Features

- **Fetch articles** — Query Wikipedia by article title or search query
- **Search mode** — Show a ranked list of search results
- **Raw output** — Print plain text instead of Rich-formatted output
- **Dependency check** — Verify that all required Python packages are installed

## Requirements

- Python 3.10 or newer
- pip

The following Python packages are installed automatically:

| Package | Purpose |
| ------- | ------- |
| [click](https://click.palletsprojects.com/) | CLI argument parsing |
| [httpx](https://www.python-httpx.org/) | HTTP requests to the Wikipedia API |
| [rich](https://rich.readthedocs.io/) | Terminal formatting and rendering |

## Installation

```bash
# Clone the repository and install
git clone https://github.com/dsillman2000/wiki.git ~/.local/share/wiki-cli
pip install --user -e ~/.local/share/wiki-cli

# Or use the provided install script
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki/main/install.sh | sh
```

Make sure `~/.local/bin` is on your `$PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

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

### Version & Dependency Check

```bash
wiki --version
wiki --check
```

## Examples

```bash
# Get the Unix shell article
wiki "Unix shell"

# Search for shell-related articles
wiki --search "shell interpreters"

# Print raw text
wiki "Bash (Unix shell)" --raw
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
ruff check wiki_cli/ tests/
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

