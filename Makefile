.DEFAULT_GOAL := help
SHELL := /bin/bash
UV := uv
PYTHON := $(UV) run python
PROJECT_DIR := src/pydotorg
TESTS_DIR := tests

.PHONY: help
help: ## Show this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

# ============================================================================
# Development Environment
# ============================================================================

##@ Development

.PHONY: install
install: ## Install all dependencies
	$(UV) sync --all-extras

.PHONY: install-dev
install-dev: ## Install dev dependencies only
	$(UV) sync --extra dev

.PHONY: update
update: ## Update dependencies
	$(UV) lock --upgrade
	$(UV) sync --all-extras

.PHONY: clean
clean: ## Clean build artifacts and caches
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies (Node.js packages)
	npm install

# ============================================================================
# Code Quality
# ============================================================================

##@ Code Quality

.PHONY: lint
lint: ## Run linter (ruff check)
	$(UV) run ruff check $(PROJECT_DIR) $(TESTS_DIR)

.PHONY: lint-fix
lint-fix: ## Run linter with auto-fix
	$(UV) run ruff check --fix $(PROJECT_DIR) $(TESTS_DIR)

.PHONY: fmt
fmt: ## Format code (ruff format)
	$(UV) run ruff format $(PROJECT_DIR) $(TESTS_DIR)

.PHONY: fmt-check
fmt-check: ## Check code formatting
	$(UV) run ruff format --check $(PROJECT_DIR) $(TESTS_DIR)

.PHONY: type-check
type-check: ## Run type checker (ty)
	$(UV) run ty check $(PROJECT_DIR)

.PHONY: ci
ci: lint fmt-check type-check test ## Run all CI checks (lint + fmt + type-check + test)

# ============================================================================
# Testing
# ============================================================================

##@ Testing

.PHONY: test
test: ## Run tests
	$(UV) run pytest $(TESTS_DIR) -v

.PHONY: test-fast
test-fast: ## Run tests in parallel
	$(UV) run pytest $(TESTS_DIR) -v -n auto

.PHONY: test-cov
test-cov: ## Run tests with coverage
	$(UV) run pytest $(TESTS_DIR) --cov=$(PROJECT_DIR) --cov-report=term-missing --cov-report=html

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	$(UV) run pytest-watch -- $(TESTS_DIR) -v

# ============================================================================
# Database
# ============================================================================

##@ Database Management

.PHONY: db-migrate
db-migrate: ## Run database migrations
	$(UV) run alembic upgrade head

.PHONY: db-revision
db-revision: ## Create a new migration revision
	@read -p "Migration message: " msg; \
	$(UV) run alembic revision --autogenerate -m "$$msg"

.PHONY: db-downgrade
db-downgrade: ## Downgrade database by one revision
	$(UV) run alembic downgrade -1

.PHONY: db-reset
db-reset: ## Reset database (dangerous!)
	$(UV) run alembic downgrade base
	$(UV) run alembic upgrade head

.PHONY: db-seed
db-seed: ## Seed database with development data
	$(PYTHON) -m pydotorg.db.seed

.PHONY: db-clear
db-clear: ## Clear all data from database
	$(PYTHON) -m pydotorg.db.seed clear

.PHONY: db-init
db-init: db-migrate db-seed ## Initialize database (migrate + seed)

# ============================================================================
# Application
# ============================================================================

##@ App Management

.PHONY: serve
serve: ## Run development server
	$(UV) run granian --interface asgi --reload pydotorg.main:app --host 0.0.0.0 --port 8000

.PHONY: serve-prod
serve-prod: ## Run production server
	$(UV) run granian --interface asgi pydotorg.main:app --host 0.0.0.0 --port 8000 --workers 4

.PHONY: worker
worker: ## Run SAQ worker
	$(UV) run saq pydotorg.tasks.worker:settings

.PHONY: shell
shell: ## Run Python shell with app context
	$(UV) run python -i -c "from pydotorg.main import app; print('App loaded')"

# ============================================================================
# Git Worktree Management
# ============================================================================

##@ Git Worktree Things

WORKTREE_DIR := ../.worktrees/litestar-pydotorg

.PHONY: worktree
worktree: ## Create a new worktree for a feature branch (NAME=feature-name)
ifndef NAME
	$(error NAME is required. Usage: make worktree NAME=feature-name)
endif
	@mkdir -p $(WORKTREE_DIR)
	git worktree add $(WORKTREE_DIR)/$(NAME) -b $(NAME)
	@echo "Worktree created at $(WORKTREE_DIR)/$(NAME)"
	@echo "cd $(WORKTREE_DIR)/$(NAME) && make install"

.PHONY: worktree-list
worktree-list: ## List all worktrees
	git worktree list

.PHONY: worktree-remove
worktree-remove: ## Remove a worktree (NAME=feature-name)
ifndef NAME
	$(error NAME is required. Usage: make worktree-remove NAME=feature-name)
endif
	git worktree remove $(WORKTREE_DIR)/$(NAME)

# ============================================================================
# Frontend Assets
# ============================================================================

##@ Frontend

.PHONY: css
css: ## Build TailwindCSS (production)
	npm run build

.PHONY: css-watch
css-watch: ## Build TailwindCSS in watch mode (development)
	npm run watch

.PHONY: css-dev
css-dev: css-watch ## Alias for css-watch

# ============================================================================
# Documentation
# ============================================================================

##@ Documentation

.PHONY: docs
docs: ## Build documentation
	$(UV) run sphinx-build -b html docs docs/_build/html

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	$(UV) run python -m http.server -d docs/_build/html 8080

# ============================================================================
# Utilities
# ============================================================================

##@ Utils

.PHONY: hooks
hooks: ## Install git hooks with prek
	$(UV) run prek install

.PHONY: pre-commit
pre-commit: lint fmt type-check ## Run pre-commit checks

.PHONY: version
version: ## Show version info
	@echo "Python: $$($(PYTHON) --version)"
	@echo "UV: $$($(UV) --version)"
	@echo "Project: $$($(UV) run python -c 'import tomllib; print(tomllib.load(open(\"pyproject.toml\", \"rb\"))[\"project\"][\"version\"])')"
