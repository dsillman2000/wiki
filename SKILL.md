# Wiki CLI Skill

## Tool

- **Name:** wiki
- **Type:** CLI (Python Click application)
- **Purpose:** Fetch Wikipedia articles and display in terminal

## Usage

```bash
wiki "article"                       # Fetch article
wiki -s "Section" "article"          # Extract section (fuzzy match)
wiki -ls "article"                  # List all sections
wiki --search "query"               # Search Wikipedia
wiki --random                       # Fetch random article
wiki --featured                     # Fetch today's featured article
wiki --featured-date DATE           # Fetch featured article for specific date
wiki --raw "article"               # Raw Markdown output
wiki "article" -o file.md          # Save to file
wiki "https://wikipedia.org/wiki/..." # Direct Wikipedia URL
wiki --version                      # Show version
```

## Key Features

- **Section extraction** - Fuzzy title matching (e.g., `-s "hist"` matches "History")
- **Search mode** - Discover articles before fetching
- **Direct URLs** - Pass Wikipedia URLs directly
- **Output modes** - Pretty-printed (default) or raw Markdown
- **Save** - Write to file with `-o`

## Requirements

- Python 3.10+
- Install via: `pip install wiki-client` or `uvx wiki-client`

## Examples

```bash
# Get an article
wiki "Unix shell"

# Get a specific section
wiki -s History "Unix shell"

# List sections before extracting
wiki -ls "Bash (Unix shell)"

# Search for articles
wiki --search "functional programming"

# Get a random article
wiki --random
wiki --random --raw
wiki --random -o random_article.md

# Get today's featured article
wiki --featured
wiki --featured --ls
wiki --featured -o featured.md
wiki --featured-date 2025-03-23  # Fetch for specific date

# Save for later
wiki "Python" -o python.md

# Debug or pipe to other tools
wiki "article" --raw | grep "keyword"

# Direct Wikipedia URL
wiki "https://en.wikipedia.org/wiki/Python_(programming_language)"
```

## Output Modes

- **Default (TTY):** Rich-formatted with tables and styling
- **`--raw`:** Plain Markdown, ideal for piping or saving
- **`-o file`:** Save to a specific file

## Limitations

- Wikipedia only (English by default)
- Requires internet access
- Section matching uses fuzzy matching
- `--featured` mode now available for daily featured articles
- `--news` not yet implemented
