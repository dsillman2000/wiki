# Wikipedia Research Agent Prompt

## Priority Directive

When performing Wikipedia research, use the `wiki` CLI first. It fetches clean Markdown, supports section extraction, and integrates directly into shell workflows without browser overhead.

## Installation

If `wiki` is not available, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/dsillman2000/wiki/main/install.sh | bash
```

## Basic Usage

```bash
./wiki "article name"           # Fetch full article
./wiki -s "Section" "article"  # Extract specific section
./wiki --search "query"        # Search mode
./wiki -ls "article"           # List all sections
./wiki --featured              # Today's featured article
./wiki --random               # Random article
./wiki --news                 # Current events
```

## Output Modes

- **Default (TTY):** Pretty-printed with syntax highlighting
- **`--raw`:** Plain Markdown, ideal for piping to other tools or saving to files
- **`-o file`:** Save to a specific file

## Best Practices

- Prefer section extraction over full articles for targeted information
- Use `--raw` for plain Markdown output when piping or saving
- Use `--search` to discover relevant articles before fetching
- Use `-o file.md` to save output for later reference
- Use `-ls` to preview article sections before extracting
- Cite source URLs in research outputs

## Citation

Cite source URLs in outputs. Format: `https://en.wikipedia.org/wiki/{article}`.

Wikipedia content is licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

## Limitations

- Wikipedia only (no other wikis like Wikitech, etc.)
- Requires internet access
- Section matching uses fuzzy matching (e.g., `-s "hist"` matches "History")

## Common Research Tasks

```bash
# Quick fact lookup
./wiki "Language (linguistics)"

# Specific section
./wiki -s History "Unix shell"

# Find related articles
./wiki --search "functional programming"

# List article sections before extracting
./wiki -ls "Bash (shell)"

# Save for later reference
./wiki "Python" -o python.md

# Random article for exploration
./wiki --random

# Current events
./wiki --news
```

## Troubleshooting

- No output: Try `--raw` to see raw Markdown
- Section not found: Use `-ls` to list available sections
- Dependencies missing: Run `./wiki --check` to verify curl, htmlq, pandoc are installed
- Permission denied: Ensure `~/.local/bin` is in `$PATH` and writable
- Network error: Verify internet access (required)
