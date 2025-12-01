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
test: ## Run unit tests only (fast, no external deps)
	$(UV) run pytest $(TESTS_DIR)/unit $(TESTS_DIR)/core -v

.PHONY: test-all
test-all: ## Run all tests (unit + integration, skips E2E if no server)
	$(UV) run pytest $(TESTS_DIR) -v

.PHONY: test-fast
test-fast: ## Run unit tests in parallel
	$(UV) run pytest $(TESTS_DIR)/unit $(TESTS_DIR)/core -v -n auto

.PHONY: test-cov
test-cov: ## Run all tests with coverage
	$(UV) run pytest $(TESTS_DIR) --cov=$(PROJECT_DIR) --cov-report=term-missing --cov-report=html

.PHONY: test-watch
test-watch: ## Run unit tests in watch mode
	$(UV) run pytest-watch -- $(TESTS_DIR)/unit $(TESTS_DIR)/core -v

.PHONY: test-unit
test-unit: ## Run unit tests only (alias for 'make test')
	$(UV) run pytest $(TESTS_DIR)/unit $(TESTS_DIR)/core -v

.PHONY: test-integration
test-integration: ## Run integration tests (requires: make infra-up)
	$(UV) run pytest $(TESTS_DIR)/integration -v

.PHONY: test-e2e
test-e2e: ## Run E2E Playwright tests (requires: make serve + playwright)
	$(UV) run pytest $(TESTS_DIR)/e2e -v

.PHONY: test-full
test-full: ## Run all tests including E2E (requires server running)
	$(UV) run pytest $(TESTS_DIR) -v

.PHONY: playwright-install
playwright-install: ## Install Playwright browsers for E2E testing
	$(UV) run playwright install chromium

# ============================================================================
# Infrastructure
# ============================================================================

##@ Infrastructure

.PHONY: infra-up
infra-up: ## Start PostgreSQL, Redis, Meilisearch, and MailDev containers
	docker compose up -d postgres redis meilisearch maildev

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

# ============================================================================
# Docker
# ============================================================================

##@ Docker

.PHONY: docker-build
docker-build: ## Build Docker images (dev profile)
	docker compose --profile dev build

.PHONY: docker-build-nc
docker-build-nc: ## Build Docker images without cache
	docker compose --profile dev build --no-cache

.PHONY: docker-up
docker-up: ## Start all services (app + worker + postgres + redis + maildev)
	docker compose --profile dev up -d

.PHONY: docker-up-build
docker-up-build: ## Build and start all services
	docker compose --profile dev up -d --build

.PHONY: docker-down
docker-down: ## Stop all Docker services
	docker compose --profile dev down

.PHONY: docker-logs
docker-logs: ## Follow all Docker logs
	docker compose --profile dev logs -f

.PHONY: docker-logs-app
docker-logs-app: ## Follow app container logs only
	docker compose logs -f app

.PHONY: docker-shell
docker-shell: ## Open shell in app container
	docker exec -it pydotorg-app /bin/bash

.PHONY: docker-full
docker-full: ## Start all services including Meilisearch (full profile)
	docker compose --profile full up -d

.PHONY: docker-prod
docker-prod: ## Start production stack
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile dev up -d

.PHONY: docker-prod-down
docker-prod-down: ## Stop production stack
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile dev down

.PHONY: docker-clean
docker-clean: ## Remove all containers, volumes, and images
	docker compose --profile full down -v --rmi local

# ============================================================================
# Litestar CLI
# ============================================================================

##@ Litestar CLI

LITESTAR := LITESTAR_APP=pydotorg.main:app $(UV) run litestar

.PHONY: litestar
litestar: ## Run Litestar CLI (usage: make litestar ARGS="--help")
	$(LITESTAR) $(ARGS)

.PHONY: litestar-info
litestar-info: ## Show Litestar application info
	$(LITESTAR) info

.PHONY: litestar-routes
litestar-routes: ## Show all application routes
	$(LITESTAR) routes

.PHONY: litestar-schema
litestar-schema: ## Export OpenAPI schema to JSON
	$(LITESTAR) schema openapi --output openapi.json

.PHONY: litestar-db
litestar-db: ## Show database commands (usage: make litestar-db ARGS="--help")
	$(LITESTAR) database $(ARGS)

.PHONY: litestar-db-make
litestar-db-make: ## Create new migration via Litestar CLI (preferred)
	$(LITESTAR) database make-migrations

.PHONY: litestar-db-upgrade
litestar-db-upgrade: ## Upgrade database to latest via Litestar CLI (preferred)
	$(LITESTAR) database upgrade

.PHONY: litestar-db-downgrade
litestar-db-downgrade: ## Downgrade database by one revision via Litestar CLI
	$(LITESTAR) database downgrade -1

.PHONY: litestar-db-current
litestar-db-current: ## Show current database revision
	$(LITESTAR) database show-current-revision

.PHONY: litestar-db-history
litestar-db-history: ## Show migration history
	$(LITESTAR) database history

.PHONY: litestar-db-check
litestar-db-check: ## Check if database is up to date
	$(LITESTAR) database check

# ============================================================================
# Database (Legacy Alembic - prefer Litestar CLI commands above)
# ============================================================================

##@ Database Management (Legacy)

.PHONY: db-migrate
db-migrate: ## Run database migrations (prefer: make litestar-db-upgrade)
	$(UV) run alembic upgrade head

.PHONY: db-revision
db-revision: ## Create a new migration revision (prefer: make litestar-db-make)
	@read -p "Migration message: " msg; \
	$(UV) run alembic revision --autogenerate -m "$$msg"

.PHONY: db-downgrade
db-downgrade: ## Downgrade database by one revision (prefer: make litestar-db-downgrade)
	$(UV) run alembic downgrade -1

.PHONY: db-reset
db-reset: ## Reset database (dangerous!)
	$(LITESTAR) database downgrade base
	$(LITESTAR) database upgrade

.PHONY: db-seed
db-seed: ## Seed database with development data
	$(PYTHON) -m pydotorg.db.seed

.PHONY: db-clear
db-clear: ## Clear all data from database
	$(PYTHON) -m pydotorg.db.seed clear

.PHONY: db-reseed
db-reseed: db-clear db-seed ## Clear and reseed database

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
worker: ## Run SAQ background task worker
	$(UV) run saq pydotorg.tasks.worker.saq_settings

.PHONY: shell
shell: ## Run Python shell with app context
	$(UV) run python -i -c "from pydotorg.main import app; print('App loaded')"

# ============================================================================
# Git Worktree Management
# ============================================================================

##@ Git Worktree Things

.PHONY: wt worktree wt-ls worktree-list wt-rm worktree-remove worktree-prune

wt: worktree ## Alias for worktree
worktree: ## Create a new worktree for a feature branch (NAME=feature-name)
ifndef NAME
	$(error NAME is required. Usage: make wt NAME=feature-name)
endif
	@mkdir -p .worktrees
	@git worktree add .worktrees/$(NAME) -b $(NAME)
	@echo "Worktree created at .worktrees/$(NAME)"

wt-ls: worktree-list ## Alias for worktree-list
worktree-list: ## List all worktrees
	@git worktree list

wt-rm: worktree-remove ## Alias for worktree-remove
worktree-remove: ## Remove a worktree (NAME=feature-name)
ifndef NAME
	$(error NAME is required. Usage: make wt-rm NAME=feature-name)
endif
	@git worktree remove .worktrees/$(NAME)

worktree-prune: ## Clean up stale git worktrees
	@git worktree prune -v

# ============================================================================
# Frontend Assets (Litestar Vite - PREFERRED)
# ============================================================================

##@ Frontend (Litestar Vite)

.PHONY: assets-install
assets-install: ## Install frontend dependencies via Litestar CLI (preferred)
	$(LITESTAR) assets install

.PHONY: assets-serve
assets-serve: ## Run Vite dev server with HMR via Litestar CLI (preferred)
	$(LITESTAR) assets serve

.PHONY: assets-build
assets-build: ## Build frontend assets for production via Litestar CLI (preferred)
	$(LITESTAR) assets build

.PHONY: assets-init
assets-init: ## Initialize Vite for project (one-time setup)
	$(LITESTAR) assets init

.PHONY: assets-routes
assets-routes: ## Generate route configuration JSON for frontend
	$(LITESTAR) assets generate-routes

# ============================================================================
# Frontend Assets (Legacy - prefer Litestar CLI above)
# ============================================================================

##@ Frontend (Legacy)

.PHONY: frontend-install
frontend-install: ## Install frontend dependencies using bun (prefer: make assets-install)
	bunx --bun install

.PHONY: frontend-dev
frontend-dev: ## Run Vite dev server with HMR (prefer: make assets-serve)
	bunx --bun vite

.PHONY: frontend-build
frontend-build: ## Build frontend assets for production (prefer: make assets-build)
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
dev: infra-up ## Full development environment: infra + worker + server (requires tmux or separate terminals)
	@echo "Starting development environment..."
	@echo ""
	@echo "Infrastructure started (postgres, redis, meilisearch)"
	@echo ""
	@echo "Run in separate terminals:"
	@echo "  Terminal 1: make serve        # Litestar web server"
	@echo "  Terminal 2: make worker       # SAQ background worker"
	@echo "  Terminal 3: make css-watch    # TailwindCSS (optional)"
	@echo ""
	@echo "Or use 'make dev-all' to run server + worker in one terminal (logs interleaved)"

.PHONY: dev-all
dev-all: infra-up ## Start infra + server + worker in background (logs to files)
	@echo "Starting full development stack..."
	@mkdir -p logs
	@echo "[DEV] Starting SAQ worker in background..."
	$(UV) run saq pydotorg.tasks.worker.saq_settings > logs/worker.log 2>&1 &
	@echo "[DEV] Worker PID: $$!"
	@echo "[DEV] Worker logs: logs/worker.log"
	@echo "[DEV] Starting Litestar server..."
	@echo ""
	$(UV) run granian --interface asgi --reload --reload-paths src pydotorg.main:app --host 0.0.0.0 --port 8000 2>&1 | sed 's/^/[SERVER] /'

.PHONY: dev-tmux
dev-tmux: infra-up ## Start dev environment in tmux session (recommended)
	@command -v tmux >/dev/null 2>&1 || { echo "tmux not installed. Use 'make dev' instead."; exit 1; }
	@tmux new-session -d -s pydotorg -n server '$(UV) run granian --interface asgi --reload --reload-paths src pydotorg.main:app --host 0.0.0.0 --port 8000'
	@tmux new-window -t pydotorg -n worker '$(UV) run saq pydotorg.tasks.worker.saq_settings'
	@tmux new-window -t pydotorg -n css 'bunx --bun tailwindcss -i ./resources/css/input.css -o ./static/css/tailwind.css --watch'
	@echo "tmux session 'pydotorg' started with 3 windows:"
	@echo "  - server: Litestar web server"
	@echo "  - worker: SAQ background worker"
	@echo "  - css: TailwindCSS watcher"
	@echo ""
	@echo "Attach with: tmux attach -t pydotorg"

.PHONY: dev-stop
dev-stop: ## Stop background worker and any dev processes
	@echo "Stopping background processes..."
	@pkill -f "saq pydotorg.tasks.worker" 2>/dev/null || true
	@pkill -f "granian.*pydotorg.main" 2>/dev/null || true
	@echo "Done. Use 'make infra-down' to stop containers."

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
