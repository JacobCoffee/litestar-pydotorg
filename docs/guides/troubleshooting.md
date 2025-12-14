# Troubleshooting Guide

This guide covers common issues you may encounter when developing, deploying, or running the pydotorg application, along with their solutions.

---

## Table of Contents

1. [Setup Issues](#setup-issues)
   - [Database Connection Problems](#database-connection-problems)
   - [Redis Connection Issues](#redis-connection-issues)
   - [Port Conflicts](#port-conflicts)
2. [Development Issues](#development-issues)
   - [Migration Errors](#migration-errors)
   - [Type Checking Failures](#type-checking-failures)
   - [Test Failures](#test-failures)
3. [Runtime Issues](#runtime-issues)
   - [MissingGreenlet Errors](#missinggreenlet-errors)
   - [Session Management Problems](#session-management-problems)
   - [Background Task Failures](#background-task-failures)
4. [Performance Issues](#performance-issues)
   - [Slow Database Queries](#slow-database-queries)
   - [Memory Usage](#memory-usage)
5. [Deployment Issues](#deployment-issues)
6. [FAQ](#faq)

---

## Setup Issues

### Database Connection Problems

#### Symptom: "Connection refused" on startup

```
DATABASE CONNECTION FAILED
PostgreSQL is not running.
```

**Cause**: PostgreSQL is not running or not accessible on the expected port.

**Solution**:

```bash
# Start the infrastructure containers (PostgreSQL, Redis, etc.)
make infra-up

# Verify PostgreSQL is running
docker compose ps postgres

# Check logs if there are issues
docker compose logs postgres
```

#### Symptom: "password authentication failed"

```
Database authentication failed.
```

**Cause**: The DATABASE_URL credentials do not match the PostgreSQL configuration.

**Solution**:

1. Check your `.env` file for the correct DATABASE_URL:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg
   ```

2. If using Docker, ensure the postgres container environment matches:
   ```yaml
   # docker-compose.yml
   postgres:
     environment:
       POSTGRES_USER: postgres
       POSTGRES_PASSWORD: postgres
       POSTGRES_DB: pydotorg
   ```

3. Reset the database if needed:
   ```bash
   make infra-reset
   make litestar-db-upgrade
   ```

#### Symptom: "database does not exist"

```
Database does not exist.
```

**Cause**: The database has not been created or migrations have not been run.

**Solution**:

```bash
# Create and migrate the database
make litestar-db-upgrade

# Or reset and reseed
make db-reset
make db-seed
```

---

### Redis Connection Issues

#### Symptom: "Connection refused" to Redis

**Cause**: Redis is not running or is on a different port.

**Solution**:

```bash
# Start Redis with infrastructure
make infra-up

# Verify Redis is running
docker compose ps redis

# Test Redis connection
docker exec -it $(docker compose ps -q redis) redis-cli ping
# Should return: PONG
```

#### Symptom: SAQ worker fails to connect

```
Could not connect to Redis at localhost:6379
```

**Cause**: The REDIS_URL in your environment does not match the running Redis instance.

**Solution**:

1. Check your `.env` file:
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

2. If Redis is running in Docker, ensure port mapping is correct:
   ```yaml
   redis:
     ports:
       - "6379:6379"
   ```

---

### Port Conflicts

#### Symptom: "Address already in use" on port 8000

**Cause**: Another process is using port 8000.

**Solution**:

```bash
# Find what's using the port
lsof -i :8000

# Kill the process if needed
kill -9 <PID>

# Or use a different port
UV_RUN_PORT=8001 make serve
```

#### Symptom: PostgreSQL port conflict (5432)

**Cause**: Another PostgreSQL instance is running on port 5432.

**Solution**:

1. Stop the local PostgreSQL:
   ```bash
   brew services stop postgresql  # macOS
   sudo systemctl stop postgresql  # Linux
   ```

2. Or use a different port in docker-compose:
   ```yaml
   postgres:
     ports:
       - "5433:5432"
   ```
   Then update DATABASE_URL accordingly.

---

## Development Issues

### Migration Errors

#### Symptom: "Target database is not up to date"

**Cause**: There are pending migrations that need to be applied.

**Solution**:

```bash
# Check current revision
make litestar-db-current

# Apply pending migrations
make litestar-db-upgrade

# View migration history
make litestar-db-history
```

#### Symptom: "Can't locate revision" or migration conflicts

**Cause**: Migration files are out of sync, possibly due to branch switching.

**Solution**:

```bash
# Check database status
make litestar-db-check

# If stuck, downgrade and re-upgrade
make litestar-db-downgrade
make litestar-db-upgrade

# For severe conflicts, reset the database (WARNING: data loss)
make db-reset
```

#### Symptom: "No changes detected" when creating migration

**Cause**: Alembic cannot detect model changes, possibly due to import issues.

**Solution**:

1. Ensure all models are imported in `src/pydotorg/db/migrations/env.py`
2. Check that model changes are properly annotated with `Mapped[]`
3. Run with verbose output:
   ```bash
   LITESTAR_APP=pydotorg.main:app uv run litestar database make-migrations -m "description"
   ```

---

### Type Checking Failures

#### Symptom: ty (or mypy) errors with Pydantic models

**Cause**: Missing type annotations or incorrect Pydantic schema definitions.

**Solution**:

1. Ensure all Pydantic models have proper type hints:
   ```python
   from pydantic import BaseModel

   class UserSchema(BaseModel):
       id: UUID
       username: str
       email: str | None = None  # Use | None, not Optional
   ```

2. For SQLAlchemy models, use `Mapped[]`:
   ```python
   class User(Base):
       id: Mapped[UUID] = mapped_column(primary_key=True)
       username: Mapped[str] = mapped_column(String(150))
   ```

3. Run type checking:
   ```bash
   make type-check
   ```

#### Symptom: TYPE_CHECKING import errors

**Cause**: Circular imports or incorrect conditional imports.

**Solution**:

Use `from __future__ import annotations` and TYPE_CHECKING properly:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User

def get_user() -> User:  # Works due to PEP 563
    ...
```

---

### Test Failures

#### Symptom: Tests fail with database errors

**Cause**: Test database is not set up or fixtures are missing.

**Solution**:

```bash
# Ensure test infrastructure is running
make infra-up

# Run unit tests only (no external deps)
make test

# Run integration tests (requires DB)
make test-integration
```

#### Symptom: "fixture not found" errors

**Cause**: Missing conftest.py or incorrect fixture scope.

**Solution**:

1. Ensure `conftest.py` exists in the test directory
2. Check fixture imports and scope:
   ```python
   # tests/conftest.py
   import pytest
   from pydotorg.main import app

   @pytest.fixture(scope="function")
   async def test_client():
       async with app.test_client() as client:
           yield client
   ```

#### Symptom: Async test failures

**Cause**: Missing pytest-asyncio configuration.

**Solution**:

Ensure `pyproject.toml` has:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## Runtime Issues

### MissingGreenlet Errors

This was a HIGH priority issue that was fixed in the project.

#### Symptom: "MissingGreenlet: greenlet_spawn has not been called"

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here.
```

**Cause**: Accessing lazy-loaded relationships outside of an async context, typically in background tasks.

**Solution (Applied Fix)**:

Add eager loading with `selectinload()` to queries that access relationships:

```python
from sqlalchemy.orm import selectinload

# Before (causes MissingGreenlet):
stmt = select(Event).where(Event.id == event_id)

# After (fixed):
stmt = (
    select(Event)
    .where(Event.id == event_id)
    .options(
        selectinload(Event.venue),
        selectinload(Event.occurrences),
        selectinload(Event.categories),
    )
)
```

**Reference**: This fix was applied to:
- `EventRepository.get_upcoming()` and `get_featured()`
- `tasks/search.py` for `index_event()` and `index_all_events()`
- `tasks/cache.py` for `warm_homepage_cache()`

---

### Session Management Problems

#### Symptom: Session not persisting across requests

**Cause**: Session cookie configuration or CSRF issues.

**Solution**:

1. Check session configuration in `config.py`:
   ```python
   session_secret_key: str = "change-me-in-production-session"
   session_expire_minutes: int = 60 * 24 * 7  # 7 days
   session_cookie_name: str = "session_id"
   ```

2. Ensure CSRF is properly configured:
   ```python
   # API routes should be excluded from CSRF
   csrf_exclude_routes = ["/api/*", "/health"]
   ```

3. For development, check that cookies are being set:
   ```bash
   curl -c cookies.txt -b cookies.txt http://localhost:8000/auth/login
   ```

#### Symptom: "Invalid or expired session"

**Cause**: Session has expired or secret key changed.

**Solution**:

1. Clear browser cookies
2. Restart the server with consistent secret keys
3. For Redis session store issues, flush the Redis database:
   ```bash
   docker exec -it $(docker compose ps -q redis) redis-cli FLUSHDB
   ```

---

### Background Task Failures

#### Symptom: SAQ tasks not executing

**Cause**: Worker not running or queue misconfiguration.

**Solution**:

1. Ensure the worker is running:
   ```bash
   make worker
   ```

2. Check worker logs for errors:
   ```bash
   # If using tmux
   tmux attach -t pydotorg
   # Switch to worker window

   # Or check log files
   tail -f logs/worker.log
   ```

3. Verify Redis connectivity:
   ```bash
   docker exec -it $(docker compose ps -q redis) redis-cli
   > KEYS saq:*
   ```

#### Symptom: Task fails with "session_maker not in context"

**Cause**: The SAQ context is not properly configured with database session.

**Solution**:

Ensure the worker context includes session_maker:

```python
# tasks/worker.py
async def startup(ctx: dict) -> None:
    from pydotorg.main import sqlalchemy_config
    ctx["session_maker"] = sqlalchemy_config.create_session_maker()

async def shutdown(ctx: dict) -> None:
    pass

saq_settings = {
    "queue": queue,
    "functions": get_task_functions(),
    "startup": startup,
    "shutdown": shutdown,
}
```

#### Symptom: Meilisearch indexing fails

**Cause**: Meilisearch is not running or API key is incorrect.

**Solution**:

1. Start Meilisearch:
   ```bash
   make infra-up  # Includes meilisearch
   ```

2. Check configuration:
   ```bash
   # .env
   MEILISEARCH_URL=http://127.0.0.1:7700
   MEILISEARCH_API_KEY=  # Empty for development
   ```

3. Verify Meilisearch is accessible:
   ```bash
   curl http://localhost:7700/health
   # Should return: {"status":"available"}
   ```

---

## Performance Issues

### Slow Database Queries

#### Symptom: Page loads are slow

**Cause**: N+1 query problems or missing database indexes.

**Solution**:

1. Enable SQL logging to identify slow queries:
   ```python
   # In development, set in .env
   DATABASE_ECHO=true
   ```

2. Add eager loading for relationships:
   ```python
   stmt = (
       select(Job)
       .options(
           selectinload(Job.job_types),
           selectinload(Job.categories),
       )
       .limit(20)
   )
   ```

3. Ensure proper indexes exist:
   ```python
   class Job(Base):
       __tablename__ = "jobs"

       status: Mapped[str] = mapped_column(index=True)
       created_at: Mapped[datetime] = mapped_column(index=True)

       __table_args__ = (
           Index('ix_jobs_status_created', 'status', 'created_at'),
       )
   ```

4. Use pagination for large result sets:
   ```python
   @get("/jobs")
   async def list_jobs(
       limit_offset: LimitOffset,  # Pagination dependency
       job_service: JobService,
   ) -> OffsetPagination[JobRead]:
       ...
   ```

#### Symptom: Connection pool exhaustion

```
QueuePool limit reached
```

**Cause**: Too many concurrent database connections.

**Solution**:

1. Adjust pool settings in `config.py`:
   ```python
   database_pool_size: int = 20  # Default connections
   database_max_overflow: int = 10  # Extra connections when needed
   ```

2. Ensure connections are properly released:
   ```python
   async with session_maker() as session:
       # Work with session
       ...
   # Connection automatically released
   ```

---

### Memory Usage

#### Symptom: High memory usage in production

**Cause**: Large result sets loaded into memory or memory leaks.

**Solution**:

1. Use streaming for large queries:
   ```python
   async for job in await session.stream_scalars(stmt):
       yield job
   ```

2. Limit result set sizes:
   ```python
   stmt = select(BlogEntry).limit(100).offset(page * 100)
   ```

3. Monitor with:
   ```bash
   # Check process memory
   ps aux | grep granian

   # Or use docker stats
   docker stats
   ```

---

## Deployment Issues

### Symptom: Production validation fails

```
SECRET_KEY must be changed in prod environment
```

**Cause**: Default/insecure secrets are being used in production.

**Solution**:

Generate secure secrets for production:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set in environment:
```bash
SECRET_KEY=your-generated-secret-key-here
SESSION_SECRET_KEY=another-generated-secret-key
CSRF_SECRET=yet-another-secret-key
```

### Symptom: Static files not loading

**Cause**: Static files not built or path misconfiguration.

**Solution**:

1. Build frontend assets:
   ```bash
   make assets-build
   # Or legacy:
   make css
   ```

2. Check static file configuration:
   ```python
   static_url: str = "/static"
   static_dir: Path = BASE_DIR / "static"
   ```

3. Verify files exist:
   ```bash
   ls -la static/css/tailwind.css
   ```

### Symptom: CORS errors in production

**Cause**: CORS not configured for production domain.

**Solution**:

Update allowed hosts in `config.py`:

```python
allowed_hosts: list[str] = [
    "localhost",
    "127.0.0.1",
    "python.org",
    "*.python.org",
    "your-domain.com",
]
```

---

## FAQ

### How do I reset everything and start fresh?

```bash
# Stop all containers
make docker-down
make infra-down

# Clean up
make clean
docker volume prune -f

# Start fresh
make infra-up
make litestar-db-upgrade
make db-seed
make serve
```

### How do I run the full development environment?

The easiest way is with tmux:

```bash
make dev-tmux
tmux attach -t pydotorg
```

This starts three windows:
- `server`: Litestar web server
- `worker`: SAQ background worker
- `css`: TailwindCSS watcher

### How do I check if my configuration is correct?

Start the server and check the startup banner:

```bash
make serve
```

The banner shows:
- Environment (dev/staging/prod)
- Database connection status
- Redis connection
- Feature flags
- Any configuration warnings

### How do I debug a specific route?

1. Add debug logging:
   ```python
   import logging
   logger = logging.getLogger(__name__)

   @get("/my-route")
   async def my_route() -> dict:
       logger.debug("Entering my_route")
       ...
   ```

2. Run with debug logging:
   ```bash
   make serve-debug
   ```

3. Check logs:
   ```bash
   tail -f logs/dev.log
   ```

### Why are my templates not updating?

1. Check you are running with reload enabled:
   ```bash
   make serve  # Uses --reload flag
   ```

2. Clear browser cache or hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

3. Template changes should hot-reload, but if not:
   ```bash
   # Restart the server
   # Ctrl+C then:
   make serve
   ```

### How do I test email sending locally?

The project uses MailDev for local email testing:

1. Ensure MailDev is running:
   ```bash
   make infra-up  # Includes maildev
   ```

2. Access the web interface:
   ```
   http://localhost:1080
   ```

3. Configure SMTP in `.env`:
   ```bash
   SMTP_HOST=localhost
   SMTP_PORT=1025
   ```

4. All emails sent locally will appear in the MailDev interface.

### How do I add a new domain/feature?

1. Create the domain structure:
   ```
   src/pydotorg/domains/myfeature/
   |-- __init__.py
   |-- models.py
   |-- schemas.py
   |-- repositories.py
   |-- services.py
   |-- controllers.py
   |-- dependencies.py
   ```

2. Create migrations:
   ```bash
   make litestar-db-make
   ```

3. Register controllers in `main.py`

4. Add tests in `tests/unit/domains/myfeature/`

5. Run CI to verify:
   ```bash
   make ci
   ```

---

## Getting Help

If you encounter an issue not covered here:

1. Check the [PLAN.md](/PLAN.md) for known issues and fixes
2. Search existing GitHub issues
3. Check the [Architecture Documentation](/docs/architecture/ARCHITECTURE.md)
4. Review the [API Documentation](/docs/api-getting-started.md)

For bugs, please file an issue with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Relevant log output
