# Wiki CLI Skill

## Tool

- **Name:** wiki
- **Type:** CLI (bash script)
- **Purpose:** Fetch Wikipedia articles and convert to Markdown

## Usage

```bash
wiki "article"                       # Fetch article
wiki -s "Section" "article"          # Extract section
wiki -ls "article"                  # List all sections
wiki --search "query"               # Search Wikipedia
wiki --featured                     # Today's featured article
wiki --random                       # Random article
wiki --news                         # Current events
wiki --check                        # Verify dependencies
wiki --version                      # Show version
wiki "article" -o file.md          # Save to file
wiki "article" --raw               # Raw Markdown (no pretty-print)
```

## Key Features

- **Section extraction** - Fuzzy title matching (e.g., `-s "hist"` matches "History")
- **Search mode** - Discover articles before fetching
- **Special modes** - Featured article, random article, current news
- **Output** - Pretty-printed (default) or raw Markdown
- **Save** - Write to file with `-o`

## Requirements

- curl, pandoc, htmlq
- If missing: `curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki/main/install.sh | bash`

## Examples

```bash
# Get a specific section
wiki -s History "Unix shell"

# List sections before extracting
wiki -ls "Bash (Unix shell)"

# Save for later
wiki "Python" -o python.md

# Debug or pipe to other tools
wiki "article" --raw | grep "keyword"
```
