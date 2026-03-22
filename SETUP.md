# Setup Guide

## First-time Setup

### 1. Install Python

Ensure you have Python 3.10 or later:

```bash
python --version  # Should be 3.10+
```

### 2. Install UV (Recommended)

UV is a fast Python package manager:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### 3. Install Dependencies

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e .
pip install -e ".[dev]"  # With development dependencies
```

### 4. Verify Setup

```bash
# Run tests
python -m pytest

# Run linter
ruff check .

# Check formatting
ruff format --check .
```

All tests should pass (89 tests).

## Daily Development

### Install Dev Dependencies Separately

```bash
uv sync --dev
```

### Run Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_api.py

# With verbose output
python -m pytest -v
```

### Run Linting

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Check both
ruff check . && ruff format --check .
```

### Git Pre-commit Hooks

No pre-commit hooks are configured by default. To add them:

```bash
# Install pre-commit (optional)
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check
        language: system
        types: [python]
      - id: ruff-format
        name: ruff-format
        entry: ruff format --check
        language: system
        types: [python]
EOF
```

## Troubleshooting

### Python version too old?

Install a newer Python version:

```bash
# Using pyenv (recommended)
pyenv install 3.12.0
pyenv local 3.12.0

# Or using uv
uv python install 3.12
uv python list
```

### UV not found?

```bash
# Source your shell config
source ~/.bashrc  # or ~/.zshrc

# Or reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Import errors?

Reinstall dependencies:

```bash
uv sync --refresh
```

### Tests failing?

Check that you're in the correct directory:

```bash
cd /path/to/wiki-cli
python -m pytest
```

### Linter errors?

Format and check:

```bash
ruff format .
ruff check . --fix
```
