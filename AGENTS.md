# AGENTS.md — wiki CLI Developer Guide

> This file provides onboarding and operational guidance for AI agents working on the wiki CLI project.

---

## Project Overview

- **Name:** wiki
- **Type:** CLI tool (bash script)
- **Purpose:** Fetch Wikipedia articles and convert them to Markdown format
- **Language:** Bash (POSIX-compliant)
- **Repository:** https://github.com/dsillman2000/wiki
- **Main entry point:** `wiki` (595 lines)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/dsillman2000/wiki.git
cd wiki

# Install dependencies
make install        # Runtime deps (curl, pandoc, shellcheck) — requires sudo
make install-dev    # Dev deps (prettier, husky, lint-staged) — npm required

# Verify setup
make check-deps    # Check all runtime deps are installed
make lint          # Run all linting checks

# Run the tool
./wiki "Unix shell"
./wiki -s History "Unix shell"
```

## Architecture

### Core Components

1. **wiki** — Main bash script
   - Parses CLI arguments
   - Fetches Wikipedia pages via curl
   - Extracts article content using htmlq
   - Converts HTML to GFM Markdown via pandoc
   - Renders output (pretty-print or raw)

2. **Makefile** — Build automation
   - Installation targets
   - Linting targets
   - Formatting targets

3. **lint.sh** — Wrapper script for running lint checks

4. **package.json** — NPM scripts and dev dependencies

### Data Flow

```
User query → URL resolution (search or direct URL)
  ↓
curl fetches HTML page
  ↓
htmlq extracts article body (main #mw-content-text .mw-parser-output)
  ↓
pandoc converts HTML → GFM Markdown
  ↓
Optional: section extraction (fuzzy match on headings)
  ↓
Optional: pretty-print (glow/mdcat/bat/less) or raw output
```

## Developer Setup

### Prerequisites

- Bash (4.0+)
- curl, pandoc, htmlq
- Node.js + npm (for dev dependencies)
- shellcheck (for linting)
- Optional: glow, mdcat, bat, less (for pretty-printing)

### Installation Commands

```bash
make install        # Runtime dependencies (requires sudo)
make install-dev    # Development dependencies (npm + husky)
```

### Verification

```bash
make check-deps    # Verify all dependencies installed
./wiki --check    # Same check via the tool itself
```

## Coding Conventions

### Bash Style Guide

- **Shebang:** `#!/usr/bin/env bash`
- **Strict mode:** `set -euo pipefail` at top of every script
- **Functions:** Lowercase with underscores (`function_name`)
- **Variables:** Lowercase with underscores; globals in ALL_CAPS
- **Local variables:** `local var_name` (always declare locals)
- **Error handling:** Use `die()` function for user-facing errors
- **Quotes:** Always double-quote variable expansions (`"$var"`, not `$var`)
- **Array syntax:** `("${array[@]}")` for word splitting
- **Command substitution:** `$(command)` not backticks

### Example Function

```bash
fetch() {
  local url="$1"
  local out="$2"

  curl -fsSL \
    -A 'wiki/0.1 (+https://wikipedia.org)' \
    -o "$out" \
    -w '%{url_effective}' \
    "$url"
}
```

### Linting

All bash scripts must pass shellcheck with no warnings:

```bash
make lint-shell    # Run shellcheck
shellcheck wiki    # Direct check
```

Common shellcheck rules to avoid:

- SC2086: Double quote to prevent globbing
- SC2002: Useless cat
- SC2034: Unused variables

### Markdown Formatting

All `.md` files must be formatted with prettier:

```bash
make format        # Format all markdown
make format-check # Check formatting without modifying
```

Prettier config (`.prettierrc`):

- Print width: 80
- Prose wrap: preserve
- Tab width: 2

## Git Workflow

### Branch Naming

- `main` — stable, deployable code
- Feature branches: `feature/short-description` or `fix/issue-number-description`
- Use lowercase and hyphens

### Commits

Follow conventional commits (not strictly enforced):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:

```
feat(section): Add support for fuzzy section matching

- Normalize headings to lowercase alphanumeric
- Use substring matching for flexible section selection
- Include parent sections when extracting nested subsections

Closes #2
```

### Pull Requests

- Open PRs against `main`
- Fill out PR template (if present)
- Ensure all CI checks pass
- Request review from repository owner

### Pre-commit Hooks

Husky automatically runs linting on `git commit`:

```bash
# What runs on commit:
npm run pre-commit  # → lint-staged → shellcheck + prettier --check
```

To bypass (use sparingly):

```bash
git commit --no-verify -m "message"
```

## Common Tasks

### Adding a New CLI Option

1. Add option parsing in `wiki` script (lines 364–436)
2. Add handler logic after parsing
3. Add to `usage()` function
4. Add example in usage text
5. Update tests (if any)
6. Run `make lint` to verify
7. Commit with appropriate message

### Adding a New Linting Target

1. Add target to `Makefile`
2. Add npm script to `package.json` (if applicable)
3. Update `lint.sh` if needed
4. Update `lint-staged` config in `package.json`
5. Update this AGENTS.md if relevant
6. Run `make lint` to verify
7. Commit

### Adding a New Dependency

Runtime dependencies (curl, pandoc, htmlq):

1. Update README.md requirements section
2. Update Makefile `install` target
3. Update SETUP.md

Development dependencies (prettier, husky):

1. Add to `package.json` devDependencies
2. Run `npm install`
3. Update relevant scripts/configs
4. Update README.md development section

### Testing the Tool Manually

```bash
# Basic fetch
./wiki "Bash"

# Section extraction
./wiki -s History "Unix shell"
./wiki -s "hist" "Unix shell"        # fuzzy match

# List sections
./wiki -ls "Unix shell"

# Search mode
./wiki --search "shell programming"

# Save to file
./wiki "Bash" -o bash.md

# Check dependencies
./wiki --check
./wiki --version
```

### Releasing a New Version

1. Update `version` variable in `wiki` script (line 4)
2. Update `version` field in `package.json`
3. Update CHANGELOG.md (create if not exists)
4. Commit with tag: `v0.x.0` (use semantic versioning)
5. Push: `git push origin main --tags`

## Project Structure

```
wiki/
├── .gitignore            # Git ignore patterns
├── .github/              # GitHub-specific files (workflows, etc.)
├── .husky/               # Git hooks
│   └── pre-commit        # Pre-commit hook (runs lint-staged)
├── .prettierrc           # Prettier configuration
├── .prettierignore       # Prettier ignore patterns
├── .shellcheckrc         # Shellcheck configuration
├── .vscode/              # VSCode settings (optional)
├── Makefile              # Build automation
├── README.md             # User-facing documentation
├── SETUP.md              # First-time setup guide
├── package.json          # NPM scripts and dev dependencies
├── lint.sh               # Linting wrapper script
└── wiki                  # Main CLI script
```

## Design Decisions

### Why Bash?

- Minimal dependencies (just shell + standard tools)
- Portable across Linux/macOS/WSL
- No compilation step
- Easy for users to read and modify

### Why htmlq + pandoc?

- `htmlq` — lightweight CSS selector tool (similar to jq for HTML)
- `pandoc` — robust HTML → Markdown conversion
- Both are single binaries, no complex dependency chains

### Why Glow/Mdcat/Bat/Less for Pretty-Printing?

- Graceful fallback chain (glow → mdcat → bat → less → cat)
- Uses whatever is available on the system
- Avoids imposing heavy dependencies

### Section Matching Logic

Sections are matched using fuzzy substring matching:

1. Headings are normalized (lowercase, alphanumeric only)
2. User input is normalized the same way
3. Substring match determines if section is selected
4. Parent sections are included automatically

This provides flexibility (e.g., `-s "hist"` matches "History").

## Environment Variables

None required. All configuration is via CLI flags.

## Exit Codes

- `0` — Success
- `1` — General error
- `2` — Invalid arguments or usage error
- `64` — Missing required arguments (EX_USAGE)

## Reporting Issues

When filing issues, include:

- Output of `wiki --version`
- Output of `wiki --check`
- The exact command that failed
- Expected vs actual behavior
- Any relevant output (`wiki --raw "query"` for debugging)

## Useful Resources

- [ShellCheck](https://www.shellcheck.net/) — Bash linter
- [Prettier](https://prettier.io/) — Code formatter
- [Husky](https://typicode.github.io/husky/) — Git hooks
- [Wikipedia API](https://en.wikipedia.org/w/api.php) — Underlying API
- [pandoc](https://pandoc.org/) — Document converter
- [htmlq](https://github.com/mgdm/htmlq) — HTML parser

## Notes for Agents

- **Always run `make lint` before committing bash changes.** No exceptions.
- **Sign off issues you create with "Written by OpenCode."** on its own line at the end of the body.
- **Test manually before committing.** Run the tool with your changes to verify it works.
- **Keep the tool POSIX-compliant.** Avoid bashisms unless necessary.
- **Update documentation** when changing behavior, adding features, or modifying the architecture.
- **Check existing issues** before creating new ones.
- **Use conventional commits** for clear changelog generation.
- **Verify CI passes** before merging PRs.
