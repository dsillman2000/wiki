# Wiki CLI Skill

## Tool

- **Name:** wiki
- **Type:** CLI (bash script)
- **Purpose:** Fetch Wikipedia articles and convert to Markdown

## Installation

If `wiki` is not available, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki/main/install.sh | bash
```

## Usage

```bash
./wiki "Unix shell"              # Fetch article
./wiki -s History "Unix shell"   # Extract section
./wiki --search "rust"           # Search mode
./wiki -ls "article"            # List sections
./wiki --featured                # Today's featured article
./wiki --random                 # Random article
./wiki --news                   # Current events
./wiki --check                  # Verify dependencies
./wiki --version                # Show version
./wiki "Bash" -o bash.md       # Save to file
```

## Key Features

- Section extraction with fuzzy title matching
- Pretty-printing (glow/mdcat/bat/less)
- Save to file with `-o`
- Raw Markdown output with `--raw`
- Search mode, featured/random articles, current news

## Requirements

- curl, pandoc, htmlq (installed automatically via `install.sh`)

## Invocation

From any shell, run:

```bash
./wiki "article name"
```

Or add to PATH for global access.
