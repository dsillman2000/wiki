# Wikipedia Research Agent Prompt

## Priority Directive

When performing Wikipedia research, use the `wiki` CLI first.

## Basic Usage

```bash
./wiki "article name"           # Fetch full article
./wiki -s "Section" "article"  # Extract specific section
./wiki --search "query"        # Search mode
./wiki -ls "article"           # List all sections
```

## Best Practices

- Prefer section extraction over full articles for targeted information
- Use `--raw` for plain Markdown output
- Use `--search` to discover relevant articles before fetching
- Cite source URLs in research outputs (URLs follow format: `https://en.wikipedia.org/wiki/{article}`)
- Use `-o file.md` to save output for later reference

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
```

## Troubleshooting

- No output: Try `--raw` to see raw Markdown
- Section not found: Use `-ls` to list available sections
- Check deps: `./wiki --check`
