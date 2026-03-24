.PHONY: install install-dev lint lint-python lint-shell lint-markdown \
        format format-check test help clean

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)wiki CLI - Development Tasks$(NC)"
	@echo ""
	@echo "$(GREEN)Installation:$(NC)"
	@echo "  make install          Install the Python package (pip install -e .)"
	@echo "  make install-dev      Install dev dependencies (pytest, ruff)"
	@echo ""
	@echo "$(GREEN)Linting & Formatting:$(NC)"
	@echo "  make lint             Run all linting checks"
	@echo "  make lint-python      Run ruff on Python source and tests"
	@echo "  make lint-shell       Run shellcheck on bash scripts"
	@echo "  make lint-markdown    Check markdown formatting with prettier"
	@echo "  make format           Format markdown files with prettier"
	@echo "  make format-check     Check if formatting is needed"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test             Run pytest"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make help             Show this help message"
	@echo ""

## Installation targets

install: ## Install the Python package in editable mode
	@echo "$(BLUE)Installing wiki-cli...$(NC)"
	pip install -e .
	@echo "$(GREEN)✓ wiki-cli installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install -e ".[dev]" 2>/dev/null || pip install -e . && pip install pytest pytest-httpx ruff
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

## Linting targets

lint: lint-python lint-shell lint-markdown ## Run all linting checks
	@echo "$(GREEN)✓ All linting checks passed$(NC)"

lint-python: ## Run ruff on Python source and tests
	@echo "$(BLUE)Running ruff...$(NC)"
	ruff check wiki_client/ tests/
	@echo "$(GREEN)✓ Ruff passed$(NC)"

lint-shell: ## Run shellcheck on bash scripts
	@echo "$(BLUE)Running shellcheck...$(NC)"
	shellcheck wiki install.sh uninstall.sh lint.sh
	@echo "$(GREEN)✓ Shellcheck passed$(NC)"

lint-markdown: ## Check markdown formatting with prettier
	@echo "$(BLUE)Checking markdown formatting...$(NC)"
	npx prettier --check "**/*.md"
	@echo "$(GREEN)✓ Markdown formatting check passed$(NC)"

## Testing targets

test: ## Run pytest
	@echo "$(BLUE)Running tests...$(NC)"
	python -m pytest tests/ -v
	@echo "$(GREEN)✓ Tests passed$(NC)"

## Formatting targets

format: ## Format markdown files with prettier
	@echo "$(BLUE)Formatting markdown files...$(NC)"
	npx prettier --write "**/*.md"
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check if formatting is needed
	@echo "$(BLUE)Checking formatting...$(NC)"
	npx prettier --check "**/*.md"
	@echo "$(GREEN)✓ All files properly formatted$(NC)"

## Utility targets

clean: ## Remove build artifacts and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf node_modules .husky package-lock.json
	rm -rf dist/ build/ *.egg-info wiki_client.egg-info
	rm -rf .pytest_cache __pycache__ wiki_client/__pycache__ tests/__pycache__
	rm -rf .ruff_cache
	@echo "$(GREEN)✓ Cleanup complete$(NC)"
