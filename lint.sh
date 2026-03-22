#!/usr/bin/env bash
# Linting script for the wiki-client project

set -euo pipefail

echo "Running ruff on Python code..."
ruff check wiki_client/ tests/
echo "✓ Ruff check passed"

echo ""
echo "Checking ruff format..."
ruff format --check wiki_client/ tests/
echo "✓ Ruff format check passed"

echo ""
echo "All linting checks passed!"
