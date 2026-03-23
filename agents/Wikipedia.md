# Wikipedia Research Agent Prompt

## Priority Directive

When performing Wikipedia research, use the `wiki` CLI first. It fetches clean content, supports section extraction, and integrates directly into shell workflows without browser overhead.

## Requirements

- `wiki` must be on PATH (installed via `pip install wiki-client` or `uvx wiki-client`)

## Basic Usage

```bash
wiki "article name"           # Fetch full article
wiki -s "Section" "article"  # Extract specific section
wiki --search "query"        # Search mode
wiki --random                # Fetch random article
wiki --featured              # Fetch today's featured article
wiki --featured-date DATE    # Fetch featured article for specific date
wiki -ls "article"           # List all sections
wiki --raw "article"         # Raw Markdown output
wiki "article" -o file.md    # Save to file
wiki "https://en.wikipedia.org/wiki/..." # Direct URL
```

## Output Modes

- **Default (TTY):** Rich-formatted with tables and styling
- **`--raw`:** Plain Markdown, ideal for piping to other tools or saving to files
- **`-o file`:** Save to a specific file

## Best Practices

- Prefer section extraction over full articles for targeted information
- Use `--raw` for plain Markdown output when piping or saving
- Use `--search` to discover relevant articles before fetching
- Use `--random` for serendipitous discovery or testing
- Use `--featured` for Wikipedia's daily featured article
- Use `-o file.md` to save output for later reference
- Use `-ls` to preview article sections before extracting
- Cite source URLs in research outputs
- Pass Wikipedia URLs directly when available

## Citation

Cite source URLs in outputs. Format: `https://en.wikipedia.org/wiki/{article}`.

Wikipedia content is licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

## Limitations

- Wikipedia only (no other wikis like Wikitech, etc.)
- Requires internet access
- Section matching uses fuzzy matching (e.g., `-s "hist"` matches "History")
- `--featured` mode now available for daily featured articles
- `--news` mode not yet implemented

## Common Research Tasks

```bash
# Quick fact lookup
wiki "Language (linguistics)"

# Specific section
wiki -s History "Unix shell"

# Find related articles
wiki --search "functional programming"

# Get random article for serendipitous discovery
wiki --random
wiki --random --raw
wiki --random -o random_article.md

# Get today's featured article
wiki --featured
wiki --featured --ls
wiki --featured -o featured.md
wiki --featured-date 2025-03-23  # Fetch for specific date

# List article sections before extracting
wiki -ls "Bash (shell)"

# Save for later reference
wiki "Python" -o python.md

# Direct Wikipedia URL
wiki "https://en.wikipedia.org/wiki/Python_(programming_language)"
```

## Troubleshooting

- No output: Try `--raw` to see raw Markdown
- Section not found: Use `-ls` to list available sections
- `wiki` not found: Run `pip install wiki-client` or `uvx wiki-client`
- Network error: Verify internet access (required)
- Wrong article: Try `--search` first to find the correct article title
