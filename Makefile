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
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

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
install-frontend: ## Install frontend dependencies using bun
	bunx --bun install

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

.PHONY: test-unit
test-unit: ## Run unit tests only (no Docker required)
	$(UV) run pytest $(TESTS_DIR)/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests (requires Docker: make infra-up)
	$(UV) run pytest $(TESTS_DIR)/integration -v

.PHONY: test-e2e
test-e2e: ## Run E2E Playwright tests (requires: uv run playwright install chromium)
	$(UV) run pytest $(TESTS_DIR)/e2e -v

.PHONY: test-full
test-full: ## Run all tests (unit + integration + e2e)
	$(UV) run pytest $(TESTS_DIR) -v

.PHONY: playwright-install
playwright-install: ## Install Playwright browsers for E2E testing
	$(UV) run playwright install chromium

# ============================================================================
# Infrastructure
# ============================================================================

##@ Infrastructure

.PHONY: infra-up
infra-up: ## Start PostgreSQL and Redis containers
	docker compose up -d postgres redis

.PHONY: infra-down
infra-down: ## Stop infrastructure containers
	docker compose down

.PHONY: infra-logs
infra-logs: ## Follow infrastructure container logs
	docker compose logs -f postgres redis

.PHONY: infra-reset
infra-reset: infra-down ## Reset infrastructure (stop and remove volumes)
	docker compose down -v
	docker compose up -d postgres redis

.PHONY: docker-up
docker-up: ## Start all services (app + worker + postgres + redis) with dev profile
	docker compose --profile dev up -d

.PHONY: docker-down
docker-down: ## Stop all Docker services
	docker compose --profile dev down

.PHONY: docker-logs
docker-logs: ## Follow logs for all services
	docker compose --profile dev logs -f

.PHONY: docker-build
docker-build: ## Build Docker images
	docker compose --profile dev build

.PHONY: docker-rebuild
docker-rebuild: ## Rebuild Docker images without cache
	docker compose --profile dev build --no-cache

.PHONY: docker-full
docker-full: ## Start all services including Meilisearch (full profile)
	docker compose --profile full up -d

.PHONY: docker-reset
docker-reset: ## Stop and remove all containers, volumes, and images
	docker compose --profile full down -v --rmi local

.PHONY: docker-shell
docker-shell: ## Open shell in running app container
	docker exec -it pydotorg-app /bin/bash

.PHONY: docker-prod-up
docker-prod-up: ## Start production stack (requires .env.prod)
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile dev up -d

.PHONY: docker-prod-down
docker-prod-down: ## Stop production stack
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile dev down

# ============================================================================
# Docker
# ============================================================================

##@ Docker

.PHONY: docker-build
docker-build: ## Build Docker image
	docker build -t pydotorg:latest .

.PHONY: docker-build-nc
docker-build-nc: ## Build Docker image (no cache)
	docker build --no-cache -t pydotorg:latest .

.PHONY: docker-up
docker-up: ## Start all services (app + infra) in development mode
	docker compose up -d

.PHONY: docker-up-build
docker-up-build: ## Build and start all services
	docker compose up -d --build

.PHONY: docker-down
docker-down: ## Stop all Docker services
	docker compose down

.PHONY: docker-logs
docker-logs: ## Follow all Docker logs
	docker compose logs -f

.PHONY: docker-logs-app
docker-logs-app: ## Follow app container logs only
	docker compose logs -f app

.PHONY: docker-shell
docker-shell: ## Open shell in app container
	docker compose exec app /bin/bash

.PHONY: docker-prod
docker-prod: ## Start production stack
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

.PHONY: docker-clean
docker-clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi local

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
	$(UV) run granian --interface asgi --reload --reload-paths src pydotorg.main:app --host 0.0.0.0 --port 8000

.PHONY: serve-log
serve-log: ## Run dev server with rotating log file (logs/dev.log, max 5MB)
	@mkdir -p logs
	@> logs/dev.log
	$(UV) run granian --interface asgi --reload --reload-paths src pydotorg.main:app --host 0.0.0.0 --port 8000 2>&1 | tee >(head -c 5242880 > logs/dev.log) &
	@echo "Server running. Logs at logs/dev.log (max 5MB, truncated on restart)"
	@echo "View logs: tail -f logs/dev.log"
	@wait

.PHONY: serve-debug
serve-debug: ## Run dev server with debug logging to file
	@mkdir -p logs
	@if [ -f logs/dev.log ] && [ $$(stat -f%z logs/dev.log 2>/dev/null || stat -c%s logs/dev.log 2>/dev/null) -gt 5242880 ]; then \
		mv logs/dev.log logs/dev.log.old; \
		tail -c 1048576 logs/dev.log.old > logs/dev.log; \
		rm logs/dev.log.old; \
	fi
	PYDOTORG_LOG_LEVEL=DEBUG $(UV) run granian --interface asgi --reload --reload-paths src pydotorg.main:app --host 0.0.0.0 --port 8000 2>&1 | tee -a logs/dev.log

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

.PHONY: frontend-install
frontend-install: ## Install frontend dependencies using bun
	bunx --bun install

.PHONY: frontend-dev
frontend-dev: ## Run Vite dev server with HMR
	bunx --bun vite

.PHONY: frontend-build
frontend-build: ## Build frontend assets for production
	bunx --bun vite build

.PHONY: frontend-preview
frontend-preview: ## Preview production build
	bunx --bun vite preview

.PHONY: frontend-lint
frontend-lint: ## Lint frontend code with biome
	bunx --bun biome check .

.PHONY: frontend-lint-fix
frontend-lint-fix: ## Fix frontend code with biome
	bunx --bun biome check --write .

.PHONY: frontend-format
frontend-format: ## Format frontend code with biome
	bunx --bun biome format --write .

.PHONY: css
css: ## Build TailwindCSS (production)
	bunx --bun tailwindcss -i ./resources/css/input.css -o ./static/css/tailwind.css --minify

.PHONY: css-watch
css-watch: ## Build TailwindCSS in watch mode (development)
	bunx --bun tailwindcss -i ./resources/css/input.css -o ./static/css/tailwind.css --watch

.PHONY: css-dev
css-dev: css-watch ## Alias for css-watch

.PHONY: dev
dev: ## Run both backend server and CSS watcher (use with tmux/separate terminals)
	@echo "Run in separate terminals:"
	@echo "  Terminal 1: make serve"
	@echo "  Terminal 2: make css-watch"

# ============================================================================
# Documentation
# ============================================================================

##@ Documentation

DOCS_DIR := docs

.PHONY: docs
docs: ## Build documentation
	$(UV) run sphinx-build -b html $(DOCS_DIR) $(DOCS_DIR)/_build/html

.PHONY: docs-serve
docs-serve: ## Serve documentation locally (with auto-rebuild)
	$(UV) run sphinx-autobuild $(DOCS_DIR) $(DOCS_DIR)/_build/html --open-browser --port 8080

.PHONY: docs-clean
docs-clean: ## Clean documentation build
	rm -rf $(DOCS_DIR)/_build

.PHONY: docs-linkcheck
docs-linkcheck: ## Check documentation links
	$(UV) run sphinx-build -b linkcheck $(DOCS_DIR) $(DOCS_DIR)/_build/linkcheck

.PHONY: changelog
changelog: ## Generate changelog with git-cliff
	$(UV) run git-cliff -o $(DOCS_DIR)/changelog.md

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
