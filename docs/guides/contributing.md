# Contribution Guide

Welcome to the Python.org Litestar rewrite project! We appreciate your interest in contributing. This guide will help you get started with development, understand our codebase architecture, and ensure your contributions meet our quality standards.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)
- [Domain Development Guide](#domain-development-guide)
- [API Development Patterns](#api-development-patterns)
- [Template Development](#template-development)

---

## Code of Conduct

This project follows the [Python Software Foundation Code of Conduct](https://www.python.org/psf/conduct/). We expect all contributors to:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Take responsibility and apologize for mistakes
- Prioritize community health over individual interests

---

## Development Environment Setup

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13+** - Required Python version
- **uv** - Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker & Docker Compose** - For running PostgreSQL, Redis, and other services
- **bun** - JavaScript runtime for frontend tooling (optional, for CSS builds)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/JacobCoffee/litestar-pydotorg.git
   cd litestar-pydotorg
   ```

2. **Install dependencies**

   ```bash
   make install
   ```

   This runs `uv sync --all-extras` to install all Python dependencies including dev tools.

3. **Start infrastructure services**

   ```bash
   make infra-up
   ```

   This starts PostgreSQL, Redis, Meilisearch, and MailDev containers.

4. **Run database migrations**

   ```bash
   make litestar-db-upgrade
   ```

5. **Seed development data** (optional)

   ```bash
   make db-seed
   ```

6. **Start the development server**

   ```bash
   make serve
   ```

   The application will be available at `http://localhost:8000`.

### Development Commands Reference

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make infra-up` | Start infrastructure (PostgreSQL, Redis, etc.) |
| `make serve` | Run development server with hot-reload |
| `make worker` | Run SAQ background task worker |
| `make ci` | Run all CI checks (lint + fmt + type-check + test) |
| `make test` | Run unit tests |
| `make test-all` | Run all tests (unit + integration) |
| `make lint` | Run linter (ruff check) |
| `make fmt` | Format code (ruff format) |
| `make type-check` | Run type checker (ty) |
| `make litestar-db-make` | Create new database migration |
| `make litestar-db-upgrade` | Apply pending migrations |
| `make docs-serve` | Build and serve documentation locally |

### Frontend Development

For CSS/JavaScript development:

```bash
# Install frontend dependencies
make assets-install

# Run Vite dev server with HMR
make assets-serve

# Or use TailwindCSS watch mode
make css-watch
```

### Using Docker for Full Stack

```bash
# Start all services (app + worker + infrastructure)
make docker-up

# View logs
make docker-logs

# Stop all services
make docker-down
```

---

## Project Structure

The project follows a domain-driven architecture:

```
litestar-pydotorg/
├── src/pydotorg/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   │
│   ├── core/                   # Core infrastructure
│   │   ├── auth/               # Authentication & authorization
│   │   ├── database/           # Database configuration & base models
│   │   ├── middleware/         # Custom middleware
│   │   └── templates/          # Template configuration
│   │
│   ├── lib/                    # Shared utilities
│   │   ├── guards/             # Route guards
│   │   ├── tasks/              # Task queue utilities
│   │   └── utils/              # Helper functions
│   │
│   ├── domains/                # Domain modules
│   │   ├── about/              # About pages
│   │   ├── banners/            # Banner management
│   │   ├── blogs/              # Blog aggregation
│   │   ├── codesamples/        # Code snippet repository
│   │   ├── community/          # Community posts/media
│   │   ├── downloads/          # Python releases & files
│   │   ├── events/             # Calendar events
│   │   ├── jobs/               # Job board
│   │   ├── mailing/            # Mailing lists
│   │   ├── minutes/            # Board meeting minutes
│   │   ├── nominations/        # PSF nominations
│   │   ├── pages/              # CMS pages
│   │   ├── search/             # Search functionality
│   │   ├── sponsors/           # Sponsorship management
│   │   ├── successstories/     # Success stories
│   │   ├── users/              # User management
│   │   └── work_groups/        # PSF working groups
│   │
│   └── tasks/                  # Background tasks
│       ├── worker.py           # SAQ worker configuration
│       └── [domain]_tasks.py   # Domain-specific tasks
│
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── unit/                   # Fast, isolated unit tests
│   ├── integration/            # Tests with database
│   └── e2e/                    # End-to-end Playwright tests
│
├── templates/                  # Jinja2 templates
├── static/                     # Static assets
└── docs/                       # Documentation
```

### Domain Module Structure

Each domain follows a consistent pattern:

```
domains/example/
├── __init__.py          # Domain exports
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── services.py          # Business logic
├── repositories.py      # Data access layer
├── controllers.py       # HTTP handlers (API & pages)
├── dependencies.py      # Dependency injection setup
└── templates/           # Domain-specific templates (if applicable)
```

---

## Coding Standards

### Style Guide (Ruff)

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting with the following configuration:

- **Line length**: 120 characters
- **Target Python**: 3.13
- **Quote style**: Double quotes
- **Indent style**: Spaces

Key linting rules enabled:

- **I** - isort (import sorting)
- **E/W** - pycodestyle
- **F** - pyflakes
- **UP** - pyupgrade
- **B** - flake8-bugbear
- **S** - flake8-bandit (security)
- **N** - pep8-naming
- **RUF** - Ruff-specific rules

Run formatting and linting:

```bash
# Format code
make fmt

# Check linting
make lint

# Auto-fix linting issues
make lint-fix
```

### Type Hints (ty)

We use [ty](https://github.com/astral-sh/ty) for type checking. All code should include type hints:

```python
# Good: Fully typed function
async def get_user_by_email(email: str) -> User | None:
    """Retrieve a user by email address."""
    return await self.repository.get_by_email(email)

# Good: Typed class attributes
class UserService(SQLAlchemyAsyncRepositoryService[User]):
    repository_type = UserRepository

# Good: Use Annotated for complex types
from typing import Annotated
from litestar.params import Parameter

async def list_items(
    limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
) -> list[Item]:
    ...
```

Run type checking:

```bash
make type-check
```

### Documentation Standards

#### Docstrings

Use Google-style docstrings for all public functions, classes, and modules:

```python
def process_feed(feed: Feed, options: FeedOptions | None = None) -> list[BlogEntry]:
    """Process an RSS/Atom feed and extract blog entries.

    Fetches the feed from the configured URL, parses the content,
    and creates or updates BlogEntry records in the database.

    Args:
        feed: The Feed model instance to process.
        options: Optional processing options. If not provided,
            default options will be used.

    Returns:
        A list of BlogEntry instances that were created or updated.

    Raises:
        FeedFetchError: If the feed URL is unreachable.
        FeedParseError: If the feed content is malformed.

    Example:
        >>> feed = await feed_service.get(feed_id)
        >>> entries = process_feed(feed)
        >>> print(f"Processed {len(entries)} entries")
    """
```

#### Code Comments

Keep comments minimal and meaningful. Code should be self-documenting:

```python
# Bad: Redundant comment
# Get the user
user = await get_user(user_id)

# Good: Explains WHY, not WHAT
# Cache bypass needed here due to eventual consistency issues with replicas
user = await get_user(user_id, bypass_cache=True)
```

---

## Testing Guidelines

### Test Categories

We maintain three categories of tests:

| Category | Location | Markers | Description |
|----------|----------|---------|-------------|
| **Unit** | `tests/unit/` | `@pytest.mark.unit` | Fast, isolated tests. No external dependencies. |
| **Integration** | `tests/integration/` | `@pytest.mark.integration` | Tests with database. Requires `make infra-up`. |
| **E2E** | `tests/e2e/` | `@pytest.mark.e2e` | Full application tests with Playwright. |

### Running Tests

```bash
# Run unit tests only (fast)
make test

# Run unit tests in parallel
make test-fast

# Run all tests (unit + integration)
make test-all

# Run integration tests only
make test-integration

# Run E2E tests (requires running server)
make test-e2e

# Run tests with coverage report
make test-cov

# Watch mode for TDD
make test-watch
```

### Writing Unit Tests

Unit tests should be fast and isolated:

```python
# tests/unit/domains/blogs/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from pydotorg.domains.blogs.services import FeedService

class TestFeedService:
    """Tests for FeedService business logic."""

    async def test_get_active_feeds_returns_only_active(self):
        """Verify only active feeds are returned."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.get_active_feeds.return_value = [
            MagicMock(id=1, name="Active Feed", is_active=True),
        ]
        service = FeedService(repository=mock_repo)

        # Act
        result = await service.get_active_feeds(limit=10)

        # Assert
        assert len(result) == 1
        assert result[0].is_active is True
        mock_repo.get_active_feeds.assert_called_once_with(limit=10)

    async def test_fetch_feed_handles_malformed_content(self):
        """Verify graceful handling of malformed feed content."""
        # Test implementation...
```

### Writing Integration Tests

Integration tests use real database connections:

```python
# tests/integration/domains/blogs/test_feed_repository.py
import pytest
from pydotorg.domains.blogs.models import Feed
from pydotorg.domains.blogs.repositories import FeedRepository

@pytest.mark.integration
class TestFeedRepository:
    """Integration tests for FeedRepository."""

    async def test_create_and_retrieve_feed(self, client):
        """Verify feed creation and retrieval."""
        # The client fixture provides a test client with database
        response = await client.post(
            "/api/v1/feeds",
            json={
                "name": "Test Feed",
                "website_url": "https://example.com",
                "feed_url": "https://example.com/feed.xml",
            },
        )
        assert response.status_code == 201

        feed_id = response.json()["id"]
        response = await client.get(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Feed"
```

### Writing E2E Tests

E2E tests use Playwright for browser automation:

```python
# tests/e2e/test_blogs_page.py
import pytest
from playwright.async_api import Page

@pytest.mark.e2e
class TestBlogsPage:
    """End-to-end tests for blogs functionality."""

    async def test_blogs_page_loads(self, page: Page):
        """Verify the blogs page loads correctly."""
        await page.goto("/blogs")
        await page.wait_for_selector("h1")

        title = await page.text_content("h1")
        assert "Blogs" in title

    async def test_filter_by_feed(self, page: Page):
        """Verify filtering blog entries by feed."""
        await page.goto("/blogs")
        await page.click("[data-testid='feed-filter']")
        await page.click("text=Python.org Blog")

        # Verify filtered results
        entries = await page.query_selector_all("[data-testid='blog-entry']")
        assert len(entries) > 0
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
@pytest.fixture
async def client(postgres_uri: str) -> AsyncIterator[AsyncTestClient]:
    """Async test client with PostgreSQL database."""
    # Creates fresh database tables for each test
    ...

@pytest.fixture
def test_client() -> TestClient:
    """Simple test client for unit tests without database."""
    ...
```

---

## Pull Request Process

### Before Submitting

1. **Run all checks locally**

   ```bash
   make ci
   ```

   This must pass before submitting a PR.

2. **Write or update tests** for your changes

3. **Update documentation** if adding new features

4. **Keep commits atomic** - each commit should represent one logical change

### PR Guidelines

1. **Title**: Use a clear, descriptive title following [commit conventions](#commit-message-conventions)

2. **Description**: Include:
   - Summary of changes
   - Related issue number(s)
   - Testing performed
   - Screenshots for UI changes

3. **Size**: Keep PRs focused. Large changes should be split into smaller PRs.

4. **Review**: Address all review comments. Reply with commit hash when fixed.

### PR Template

```markdown
## Summary

Brief description of what this PR does.

## Related Issues

Fixes #123

## Changes

- Added X feature
- Updated Y behavior
- Fixed Z bug

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots

(If applicable)
```

---

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear, automated changelogs:

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Maintenance (deps, config, etc.) |

### Scopes

Use the domain or component name:

- `blogs`, `downloads`, `events`, `jobs`, `users`, etc.
- `api`, `auth`, `db`, `tasks`, `templates`
- `deps`, `ci`, `docker`

### Examples

```bash
feat(blogs): add RSS feed aggregation

fix(downloads): correct file size calculation for large files

docs(contributing): add section on testing guidelines

refactor(users): extract password hashing to utility function

chore(deps): update litestar to 2.15.0
```

### Breaking Changes

For breaking changes, add `!` after the type/scope:

```bash
feat(api)!: change pagination format to cursor-based

BREAKING CHANGE: API responses now use cursor pagination instead of offset.
```

---

## Domain Development Guide

### Creating a New Domain

1. **Create the domain directory structure**

   ```bash
   mkdir -p src/pydotorg/domains/newdomain
   touch src/pydotorg/domains/newdomain/__init__.py
   touch src/pydotorg/domains/newdomain/models.py
   touch src/pydotorg/domains/newdomain/schemas.py
   touch src/pydotorg/domains/newdomain/repositories.py
   touch src/pydotorg/domains/newdomain/services.py
   touch src/pydotorg/domains/newdomain/controllers.py
   touch src/pydotorg/domains/newdomain/dependencies.py
   ```

2. **Define the model** (`models.py`)

   ```python
   """NewDomain models."""
   from __future__ import annotations

   from sqlalchemy import String, Text, Boolean
   from sqlalchemy.orm import Mapped, mapped_column

   from pydotorg.core.database.base import AuditBase, NameSlugMixin


   class NewEntity(AuditBase, NameSlugMixin):
       """A new entity in the system."""

       __tablename__ = "new_entities"

       description: Mapped[str | None] = mapped_column(Text, nullable=True)
       is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
   ```

3. **Create Pydantic schemas** (`schemas.py`)

   ```python
   """NewDomain Pydantic schemas."""
   from __future__ import annotations

   import datetime
   from typing import Annotated
   from uuid import UUID

   from pydantic import BaseModel, ConfigDict, Field


   class NewEntityBase(BaseModel):
       """Base schema with common fields."""

       name: Annotated[str, Field(min_length=1, max_length=255)]
       slug: Annotated[str, Field(min_length=1, max_length=255)]
       description: str | None = None
       is_active: bool = True


   class NewEntityCreate(NewEntityBase):
       """Schema for creating a new entity."""


   class NewEntityUpdate(BaseModel):
       """Schema for updating an entity."""

       name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
       description: str | None = None
       is_active: bool | None = None


   class NewEntityRead(NewEntityBase):
       """Schema for reading entity data."""

       id: UUID
       created_at: datetime.datetime
       updated_at: datetime.datetime

       model_config = ConfigDict(from_attributes=True)
   ```

4. **Implement the repository** (`repositories.py`)

   ```python
   """NewDomain repositories."""
   from __future__ import annotations

   from advanced_alchemy.repository import SQLAlchemyAsyncRepository

   from pydotorg.domains.newdomain.models import NewEntity


   class NewEntityRepository(SQLAlchemyAsyncRepository[NewEntity]):
       """Repository for NewEntity data access."""

       model_type = NewEntity

       async def get_active_entities(self, limit: int = 100) -> list[NewEntity]:
           """Get all active entities."""
           return await self.list(
               statement=self.statement.where(NewEntity.is_active == True).limit(limit)
           )
   ```

5. **Create the service layer** (`services.py`)

   ```python
   """NewDomain services."""
   from __future__ import annotations

   from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

   from pydotorg.domains.newdomain.models import NewEntity
   from pydotorg.domains.newdomain.repositories import NewEntityRepository


   class NewEntityService(SQLAlchemyAsyncRepositoryService[NewEntity]):
       """Service for NewEntity business logic."""

       repository_type = NewEntityRepository

       async def get_active_entities(self, limit: int = 100) -> list[NewEntity]:
           """Get all active entities."""
           return await self.repository.get_active_entities(limit=limit)
   ```

6. **Build the controller** (`controllers.py`)

   ```python
   """NewDomain controllers."""
   from __future__ import annotations

   from typing import Annotated
   from uuid import UUID

   from advanced_alchemy.filters import LimitOffset
   from litestar import Controller, delete, get, post, put
   from litestar.params import Body, Parameter

   from pydotorg.domains.newdomain.schemas import (
       NewEntityCreate,
       NewEntityRead,
       NewEntityUpdate,
   )
   from pydotorg.domains.newdomain.services import NewEntityService


   class NewEntityController(Controller):
       """Controller for NewEntity CRUD operations."""

       path = "/api/v1/new-entities"
       tags = ["NewDomain"]

       @get("/")
       async def list_entities(
           self,
           new_entity_service: NewEntityService,
           limit_offset: LimitOffset,
       ) -> list[NewEntityRead]:
           """List all entities with pagination."""
           entities, _total = await new_entity_service.list_and_count(limit_offset)
           return [NewEntityRead.model_validate(e) for e in entities]

       @get("/{entity_id:uuid}")
       async def get_entity(
           self,
           new_entity_service: NewEntityService,
           entity_id: Annotated[UUID, Parameter(description="Entity ID")],
       ) -> NewEntityRead:
           """Get an entity by ID."""
           entity = await new_entity_service.get(entity_id)
           return NewEntityRead.model_validate(entity)

       @post("/")
       async def create_entity(
           self,
           new_entity_service: NewEntityService,
           data: Annotated[NewEntityCreate, Body(description="Entity to create")],
       ) -> NewEntityRead:
           """Create a new entity."""
           entity = await new_entity_service.create(data.model_dump())
           return NewEntityRead.model_validate(entity)

       @put("/{entity_id:uuid}")
       async def update_entity(
           self,
           new_entity_service: NewEntityService,
           data: Annotated[NewEntityUpdate, Body(description="Update data")],
           entity_id: Annotated[UUID, Parameter(description="Entity ID")],
       ) -> NewEntityRead:
           """Update an entity."""
           entity = await new_entity_service.update(
               entity_id, data.model_dump(exclude_unset=True)
           )
           return NewEntityRead.model_validate(entity)

       @delete("/{entity_id:uuid}")
       async def delete_entity(
           self,
           new_entity_service: NewEntityService,
           entity_id: Annotated[UUID, Parameter(description="Entity ID")],
       ) -> None:
           """Delete an entity."""
           await new_entity_service.delete(entity_id)
   ```

7. **Set up dependencies** (`dependencies.py`)

   ```python
   """NewDomain dependencies."""
   from __future__ import annotations

   from typing import TYPE_CHECKING

   from pydotorg.domains.newdomain.repositories import NewEntityRepository
   from pydotorg.domains.newdomain.services import NewEntityService

   if TYPE_CHECKING:
       from sqlalchemy.ext.asyncio import AsyncSession


   async def provide_new_entity_service(
       db_session: AsyncSession,
   ) -> NewEntityService:
       """Provide NewEntityService instance."""
       return NewEntityService(session=db_session)
   ```

8. **Register the domain**

   Add to `src/pydotorg/domains/__init__.py`:

   ```python
   from pydotorg.domains.newdomain.models import NewEntity

   __all__ = [
       # ... existing exports
       "NewEntity",
   ]
   ```

   Register the controller in `src/pydotorg/main.py`.

9. **Create a migration**

   ```bash
   make litestar-db-make
   ```

10. **Write tests**

    ```bash
    mkdir -p tests/unit/domains/newdomain
    mkdir -p tests/integration/domains/newdomain
    ```

---

## API Development Patterns

### Response Formats

All API responses follow consistent patterns:

```python
# Single resource
{
    "id": "uuid",
    "name": "Example",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
}

# List with pagination
[
    {"id": "uuid", "name": "Example 1"},
    {"id": "uuid", "name": "Example 2"}
]
```

### Error Handling

Use Litestar's built-in exception handling:

```python
from litestar.exceptions import NotFoundException, ValidationException

@get("/{item_id:uuid}")
async def get_item(self, item_service: ItemService, item_id: UUID) -> ItemRead:
    """Get an item by ID."""
    item = await item_service.get(item_id)
    if not item:
        raise NotFoundException(f"Item with ID {item_id} not found")
    return ItemRead.model_validate(item)
```

### Authentication Guards

Protect routes with guards:

```python
from pydotorg.core.auth.guards import requires_authentication, requires_admin

class AdminController(Controller):
    """Admin-only controller."""

    path = "/api/v1/admin"
    guards = [requires_authentication, requires_admin]

    @get("/stats")
    async def get_stats(self) -> dict:
        """Get admin statistics."""
        ...
```

### API Versioning

APIs are versioned in the URL path:

- `/api/v1/...` - Current stable API
- `/api/v2/...` - Next version (when needed)

---

## Template Development

### Jinja2 Templates

Templates are located in `templates/` and organized by domain:

```
templates/
├── base.html.jinja2           # Base layout
├── components/                # Reusable components
│   ├── navigation.html.jinja2
│   ├── footer.html.jinja2
│   └── pagination.html.jinja2
├── blogs/                     # Domain templates
│   ├── index.html.jinja2
│   ├── feed.html.jinja2
│   └── partials/
│       └── blog_entries.html.jinja2
└── ...
```

### HTMX Integration

We use HTMX for dynamic updates:

```html
<!-- Load more entries -->
<button
    hx-get="/blogs?offset=20"
    hx-target="#entries-list"
    hx-swap="beforeend"
    class="btn btn-primary"
>
    Load More
</button>

<!-- Filter by feed -->
<select
    hx-get="/blogs"
    hx-target="#entries-list"
    hx-swap="innerHTML"
    name="feed_id"
>
    <option value="">All Feeds</option>
    {% for feed in feeds %}
    <option value="{{ feed.id }}">{{ feed.name }}</option>
    {% endfor %}
</select>
```

### Controllers for Pages

Page controllers return `Template` responses:

```python
from litestar.response import Template

class BlogsPageController(Controller):
    """Controller for blogs HTML pages."""

    path = "/blogs"
    include_in_schema = False  # Exclude from OpenAPI

    @get("/")
    async def blogs_index(
        self,
        request: Request,
        blog_entry_service: BlogEntryService,
    ) -> Template:
        """Render the main blogs page."""
        entries = await blog_entry_service.get_recent_entries(limit=20)

        # Handle HTMX partial requests
        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"

        if is_htmx and not is_boosted:
            return Template(
                template_name="blogs/partials/blog_entries.html.jinja2",
                context={"entries": entries},
            )

        return Template(
            template_name="blogs/index.html.jinja2",
            context={"entries": entries},
        )
```

### Tailwind CSS + DaisyUI

We use Tailwind CSS with DaisyUI for styling:

```html
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">{{ entry.title }}</h2>
        <p class="text-base-content/70">{{ entry.summary }}</p>
        <div class="card-actions justify-end">
            <a href="{{ entry.url }}" class="btn btn-primary">Read More</a>
        </div>
    </div>
</div>
```

Build CSS for production:

```bash
make css  # Minified production build
```

---

## Getting Help

- **Documentation**: Browse the `docs/` directory
- **Issues**: Check [GitHub Issues](https://github.com/JacobCoffee/litestar-pydotorg/issues) for existing discussions
- **Discussions**: Start a [GitHub Discussion](https://github.com/JacobCoffee/litestar-pydotorg/discussions) for questions

Thank you for contributing to the Python.org Litestar rewrite!
