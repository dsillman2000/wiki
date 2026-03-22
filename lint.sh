#!/usr/bin/env bash
# Linting script for the wiki project

set -euo pipefail

echo "Running shellcheck on bash scripts..."
shellcheck wiki
echo "✓ Shellcheck passed"

echo ""
echo "Checking if prettier is installed..."
if command -v prettier >/dev/null 2>&1; then
  echo "Running prettier on Markdown..."
  prettier --check README.md
  echo "✓ Prettier check passed"
else
  echo "⚠ prettier not installed. To check Markdown formatting:"
  echo "  npm install -g prettier"
  echo "  prettier --check README.md"
fi

echo ""
echo "All linting checks passed!"
