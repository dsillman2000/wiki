# Setup Guide

## First-time Setup

### 1. Install Runtime Dependencies

```bash
make install
```

This installs:

- `curl` - HTTP client
- `pandoc` - Document converter
- `shellcheck` - Bash script linter

**Note:** `htmlq` must be installed manually. Follow the instructions printed after `make install`.

### 2. Install Development Dependencies

```bash
make install-dev
```

This installs:

- `prettier` - Code formatter
- `husky` - Git hooks
- `lint-staged` - Run linters on staged files

Husky automatically configures git pre-commit hooks.

### 3. Verify Setup

```bash
make check-deps
```

All dependencies should show "OK" (except optional ones like `mdcat`, `bat`).

## Daily Development

### Run Linting Before Committing

```bash
make lint
```

Or let git hooks do it automatically:

```bash
git add .
git commit -m "Your message"  # linting runs automatically
```

### Format Code

```bash
make format
```

### Run Specific Checks

```bash
make lint-shell       # Just check bash
make lint-markdown    # Just check markdown
```

## Troubleshooting

### Git hooks not running?

Reinstall husky:

```bash
make clean
make install-dev
```

### Node/npm not installed?

Install Node.js from https://nodejs.org/

### Permission denied on shellcheck?

```bash
chmod +x wiki
```

### Prettier says "file not found"?

Run from project root:

```bash
cd /path/to/wiki-cli
make format
```
