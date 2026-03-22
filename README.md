# wiki

A command-line tool to fetch Wikipedia articles and convert them to Markdown format.

## Overview

`wiki` is a lightweight bash script that retrieves Wikipedia articles and converts them to clean, readable Markdown. It supports section extraction, search functionality, and pretty-printing in the terminal.

## Features

- **Fetch articles** - Query Wikipedia by article name or direct URL
- **Section extraction** - Extract specific sections using fuzzy title matching
- **Table of contents** - List all sections in an article
- **Search mode** - Show search results instead of auto-selecting
- **Special modes** - Fetch featured articles, random articles, or current news topics
- **Format control** - Output raw Markdown, pretty-print to terminal, or save to file
- **Pretty printing** - Automatically uses available renderers (glow, mdcat, bat, less)

## Requirements

### Required

- `curl` - For fetching web content
- `htmlq` - For HTML parsing
- `pandoc` - For HTML to Markdown conversion

### Optional (for pretty-printing)

- `glow` - Markdown renderer (preferred)
- `mdcat` - Markdown renderer with syntax highlighting
- `bat` - Code syntax highlighter
- `less` - Pager for large content

Install all dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install curl pandoc

# For htmlq, grab a release from https://github.com/mgdm/htmlq/releases
wget https://github.com/mgdm/htmlq/releases/download/0.4.0/htmlq-0.4.0-x86_64-unknown-linux-gnu.zip
unzip htmlq-0.4.0-x86_64-unknown-linux-gnu.zip
sudo mv htmlq /usr/local/bin/

# Optional renderers
sudo apt-get install glow mdcat bat
```

### Docker

A Docker image is available on GitHub Container Registry (GHCR) with all
dependencies pre-installed:

```bash
# Pull the image
docker pull ghcr.io/dsillman2000/wiki:latest

# Run a query
docker run --rm ghcr.io/dsillman2000/wiki:latest "Unix shell"

# Extract specific section
docker run --rm ghcr.io/dsillman2000/wiki:latest -s History "Bash"

# List sections
docker run --rm ghcr.io/dsillman2000/wiki:latest -ls "Python"

# Save output to file (mount current directory)
docker run --rm -v "$(pwd)":/home/wiki ghcr.io/dsillman2000/wiki:latest \
  "Operating system" -o os.md
```

**Advantages:**

- No local dependency installation required
- Consistent environment across systems
- Easy integration into CI/CD pipelines
- Lightweight multi-stage build (~311MB)

## Usage

### Basic Queries

```bash
# Fetch an article
wiki "Unix shell"

# Fetch from URL
wiki "https://en.wikipedia.org/wiki/Bash_(Unix_shell)"

# Show Markdown without pretty-printing
wiki "Unix shell" --raw
```

### Section Extraction

```bash
# List all sections in an article
wiki -ls "Unix shell"

# Extract specific sections (repeatable, uses fuzzy matching)
wiki -s History "Unix shell"
wiki -s "Bourne shell" -s "C shell" "Unix shell"

# Fuzzy matching works on partial titles
wiki -s "hist" "Unix shell"  # matches "History"
```

### Search & Special Modes

```bash
# Show search results
wiki --search "shell programming"

# Fetch today's featured article
wiki --featured

# Fetch a random article
wiki --random

# Show topics in the news
wiki --news
```

### Output Options

```bash
# Save to file
wiki "Bash" -o bash.md

# Save specific sections to file
wiki "Unix shell" -s History -o history.md

# Combine options
wiki "Python" --raw -o python.md
```

## Examples

```bash
# Get the History section of Bash
wiki -s History "Bash"

# List sections of Operating systems article
wiki --list-sections "Operating system"

# Fetch featured article and save it
wiki --featured -o today.md

# Search for shell-related articles
wiki --search "shell interpreters"

# Get History and Types sections from Operating systems
wiki "Operating system" -s History -s Types
```

## How It Works

1. **Query parsing** - Accepts search queries or Wikipedia URLs
2. **Fetching** - Uses curl to retrieve the page (with proper User-Agent)
3. **Extraction** - Uses htmlq to extract article body from HTML
4. **Conversion** - Uses pandoc to convert HTML to GFM Markdown
5. **Rendering** - Pretty-prints using available renderers or outputs raw Markdown

### Section Matching

Section titles are matched using fuzzy substring matching on normalized (lowercase, alphanumeric-only) headings. Parent sections are automatically included when extracting nested subsections.

## Development

### Quick Start

Use Make to manage development tasks:

```bash
# View all available tasks
make help

# Install development dependencies
make install-dev

# Run linting checks
make lint

# Format code
make format
```

### Installation

Install runtime dependencies (requires sudo):

```bash
make install
```

Install development dependencies via npm:

```bash
make install-dev
```

This will:

- Install npm dependencies (prettier, husky, lint-staged)
- Configure git pre-commit hooks via husky
- Enable automatic linting on every commit

### Linting & Formatting

The project uses:

- **shellcheck** - Bash script validation
- **prettier** - Markdown formatting
- **husky** - Git hooks for automated linting
- **lint-staged** - Run linters only on changed files

Available make targets:

```bash
make lint              # Run all linting checks
make lint-shell        # Run shellcheck only
make lint-markdown     # Check markdown formatting
make format            # Format markdown files
make format-check      # Check if formatting is needed
make check-deps        # Verify runtime dependencies
```

Or use npm scripts directly:

```bash
npm run lint           # Run all linting
npm run lint:shellcheck
npm run lint:markdown
npm run format         # Format code
npm run format:check   # Check formatting
npm run pre-commit     # Manual pre-commit hook
```

### Git Hooks

When you run `make install-dev`, husky automatically configures a pre-commit hook that:

1. Lints bash scripts with shellcheck
2. Formats markdown with prettier (check mode)

Linting will run automatically on `git commit`. To skip it:

```bash
git commit --no-verify
```

## Version

0.1.0

## License

MIT
