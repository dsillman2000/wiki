.PHONY: install install-dev lint lint-shell lint-markdown format format-check help clean

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
	@echo "  make install          Install runtime dependencies (requires sudo)"
	@echo "  make install-dev      Install development dependencies (npm/node required)"
	@echo ""
	@echo "$(GREEN)Linting & Formatting:$(NC)"
	@echo "  make lint             Run all linting checks"
	@echo "  make lint-shell       Run shellcheck on bash scripts"
	@echo "  make lint-markdown    Check markdown formatting with prettier"
	@echo "  make format           Format markdown files with prettier"
	@echo "  make format-check     Check if formatting is needed"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make clean            Remove node_modules and caches"
	@echo "  make help             Show this help message"
	@echo ""

## Installation targets

install: ## Install runtime dependencies (requires sudo)
	@echo "$(BLUE)Installing runtime dependencies...$(NC)"
	sudo apt-get update
	sudo apt-get install -y curl pandoc shellcheck
	@echo "$(GREEN)✓ Runtime dependencies installed$(NC)"
	@echo ""
	@echo "$(YELLOW)Note: htmlq must be installed manually:$(NC)"
	@echo "  wget https://github.com/mgdm/htmlq/releases/download/0.4.0/htmlq-0.4.0-x86_64-unknown-linux-gnu.zip"
	@echo "  unzip htmlq-0.4.0-x86_64-unknown-linux-gnu.zip"
	@echo "  sudo mv htmlq /usr/local/bin/"

install-dev: ## Install development dependencies via npm
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@if ! command -v node >/dev/null 2>&1; then \
		echo "$(YELLOW)Node.js is not installed. Please install Node.js first:$(NC)"; \
		echo "  https://nodejs.org/"; \
		exit 1; \
	fi
	npm install
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"
	@echo "$(GREEN)✓ Husky git hooks configured$(NC)"

## Linting targets

lint: lint-shell lint-markdown ## Run all linting checks
	@echo "$(GREEN)✓ All linting checks passed$(NC)"

lint-shell: ## Run shellcheck on bash scripts
	@echo "$(BLUE)Running shellcheck...$(NC)"
	shellcheck wiki
	@echo "$(GREEN)✓ Shellcheck passed$(NC)"

lint-markdown: ## Check markdown formatting with prettier
	@echo "$(BLUE)Checking markdown formatting...$(NC)"
	npx prettier --check README.md
	@echo "$(GREEN)✓ Markdown formatting check passed$(NC)"

## Formatting targets

format: ## Format markdown files with prettier
	@echo "$(BLUE)Formatting markdown files...$(NC)"
	npx prettier --write README.md
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check if formatting is needed
	@echo "$(BLUE)Checking formatting...$(NC)"
	npx prettier --check README.md
	@echo "$(GREEN)✓ All files properly formatted$(NC)"

## Utility targets

clean: ## Remove node_modules and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf node_modules
	rm -rf .husky
	rm -f package-lock.json
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

check-deps: ## Check if required dependencies are installed
	@echo "$(BLUE)Checking dependencies...$(NC)"
	./wiki --check
