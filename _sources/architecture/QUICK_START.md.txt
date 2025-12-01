# Litestar Python.org Quick Start Guide

## For Developers

This guide helps you get started with the Litestar python.org project quickly.

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- uv (Python package manager)
- Git

## Initial Setup

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone Repository

```bash
git clone https://github.com/python/litestar-pydotorg.git
cd litestar-pydotorg
```

### 3. Set Up Python Environment

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Minimum required:
# - DATABASE_URL
# - REDIS_URL
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 5. Start Services (Docker Compose)

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Optionally start Meilisearch
docker-compose up -d meilisearch
```

### 6. Database Setup

```bash
# Run migrations
alembic upgrade head

# Optionally load fixtures
uv run python scripts/load_fixtures.py
```

### 7. Run Development Server

```bash
# Start Litestar development server
litestar run --reload

# Server will be available at http://localhost:8000
```

### 8. Access Documentation

- API Docs: http://localhost:8000/schema
- Swagger UI: http://localhost:8000/schema/swagger
- ReDoc: http://localhost:8000/schema/redoc

## Project Structure at a Glance

```
litestar-pydotorg/
├── src/pydotorg/          # Main application code
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration
│   ├── core/              # Core infrastructure
│   ├── domains/           # Business domains (users, pages, etc.)
│   ├── lib/               # Shared utilities
│   └── tasks/             # Background tasks
├── migrations/            # Alembic migrations
├── templates/             # Jinja2 templates
├── static/                # Static assets
└── tests/                 # Test suite
```

## Common Development Tasks

### Create a New Domain

```bash
# Use the domain template generator
uv run python scripts/create_domain.py my_domain

# This creates:
# - src/pydotorg/domains/my_domain/
# - migrations/versions/xxxx_create_my_domain.py
# - tests/unit/domains/my_domain/
```

### Create a Database Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to User"

# Review the generated migration in migrations/versions/

# Apply migration
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/domains/users/test_models.py

# Run with coverage
pytest --cov=pydotorg --cov-report=html

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration
```

### Code Quality Checks

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type check
mypy src/pydotorg
```

### Background Tasks

```bash
# Start SAQ worker in separate terminal
uv run python -m saq worker pydotorg.tasks.base.worker

# Enqueue a task manually
uv run python scripts/enqueue_task.py update_download_boxes
```

### Database Shell

```bash
# PostgreSQL shell
psql $DATABASE_URL

# Python shell with app context
uv run python scripts/shell.py
```

## Development Workflow

### Adding a New Feature

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write Models**
   ```python
   # src/pydotorg/domains/my_domain/models.py
   from pydotorg.core.database import Base, TimestampMixin

   class MyModel(Base, TimestampMixin):
       __tablename__ = "my_models"
       # ... fields
   ```

3. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "Add MyModel"
   alembic upgrade head
   ```

4. **Write Schemas**
   ```python
   # src/pydotorg/domains/my_domain/schemas.py
   from pydantic import BaseModel

   class MyModelRead(BaseModel):
       # ... fields
   ```

5. **Implement Service**
   ```python
   # src/pydotorg/domains/my_domain/services.py
   class MyModelService:
       async def create(self, data: MyModelCreate) -> MyModel:
           # ... logic
   ```

6. **Create Controller**
   ```python
   # src/pydotorg/domains/my_domain/controllers.py
   from litestar import Controller, get, post

   class MyModelController(Controller):
       path = "/my-models"
       # ... endpoints
   ```

7. **Write Tests**
   ```python
   # tests/unit/domains/my_domain/test_services.py
   async def test_create_my_model(db_session):
       # ... test
   ```

8. **Run Tests & Quality Checks**
   ```bash
   pytest
   ruff check .
   mypy src/pydotorg
   ```

9. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   git push origin feature/my-feature
   ```

10. **Create Pull Request**
    - Go to GitHub
    - Create PR from your branch
    - Fill out PR template
    - Request review

## Debugging

### Enable Debug Mode

```bash
# In .env
DEBUG=true

# This enables:
# - Detailed error pages
# - SQL query logging
# - Debug toolbar (if installed)
```

### Debug Logging

```python
# In your code
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### IPython Debugger

```python
# Add breakpoint in code
import ipdb; ipdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Database Query Logging

```bash
# In .env
DATABASE_ECHO=true

# All SQL queries will be logged to console
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql $DATABASE_URL -c "SELECT 1"

# Reset database (CAUTION: destroys data)
alembic downgrade base
alembic upgrade head
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -u $REDIS_URL ping
```

### Migration Conflicts

```bash
# If you have migration conflicts
alembic heads  # Show multiple heads

# Merge migrations
alembic merge heads -m "merge migrations"
```

### Import Errors

```bash
# Reinstall dependencies
uv pip install -e ".[dev]" --force-reinstall

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## IDE Setup

### VS Code

Install recommended extensions:
- Python
- Pylance
- Ruff
- Even Better TOML
- REST Client

Workspace settings are in `.vscode/settings.json`

### PyCharm

1. Set Python interpreter to `.venv/bin/python`
2. Mark `src` as Sources Root
3. Enable pytest as test runner
4. Configure Ruff as external tool

## Docker Development

### Full Docker Development Environment

```bash
# Build and start all services
docker-compose up --build

# The app will be available at http://localhost:8000
```

### Update Dependencies in Docker

```bash
# Rebuild after dependency changes
docker-compose build web
docker-compose up web
```

## Useful Commands Reference

```bash
# Development server
litestar run --reload

# Run tests
pytest
pytest -v                    # Verbose
pytest -x                    # Stop on first failure
pytest --lf                  # Run last failed
pytest -k "test_user"        # Run matching tests

# Database
alembic upgrade head         # Apply migrations
alembic downgrade -1         # Rollback one
alembic history              # Show migration history
alembic current              # Show current revision

# Code quality
ruff format .                # Format code
ruff check .                 # Lint code
mypy src/pydotorg           # Type check

# Dependencies
uv pip list                  # List installed packages
uv pip install package       # Install package
uv pip install -e ".[dev]"  # Install in editable mode

# Background tasks
saq worker pydotorg.tasks.base.worker
```

## Getting Help

- Documentation: `/docs/`
- API Reference: http://localhost:8000/schema
- GitHub Issues: https://github.com/python/litestar-pydotorg/issues
- Mailing List: pydotorg-www@python.org

## Next Steps

1. Read the [Architecture Document](./ARCHITECTURE.md)
2. Review [Database Schema](./DATABASE_SCHEMA.md)
3. Look at example implementations in `src/pydotorg/domains/`
4. Start with a small feature or bug fix

---

**Document Path**: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/architecture/QUICK_START.md`
