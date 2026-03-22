# Wiki CLI Skill

## Tool

- **Name:** wiki
- **Type:** CLI (bash script)
- **Purpose:** Fetch Wikipedia articles and convert to Markdown

## Usage

```bash
./wiki "Unix shell"              # Fetch article
./wiki -s History "Unix shell"   # Extract section
./wiki --search "rust"           # Search mode
./wiki -ls "article"             # List sections
```

## Key Features

- Section extraction with fuzzy title matching
- Pretty-printing (glow/mdcat/bat/less)
- Save to file with `-o`
- Raw Markdown output with `--raw`

## Invocation

From any shell, run:

```bash
./wiki "article name"
```

Or add to PATH for global access.
