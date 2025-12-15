# Development Guide

This guide covers development workflows, code standards, and best practices for contributing to litestar-pydotorg.

## Development Environment

### Prerequisites

Ensure you have completed the [Installation](../getting-started/installation.md) guide.

### IDE Setup

#### VS Code

Install the recommended extensions:
- Python
- Pylance
- Ruff
- Even Better TOML
- REST Client

Workspace settings are provided in `.vscode/settings.json`.

#### PyCharm

1. Set Python interpreter to `.venv/bin/python`
2. Mark `src` as Sources Root
3. Enable pytest as test runner
4. Configure Ruff as external tool

## Code Standards

### Style Guide

We follow these conventions:

- **PEP 8** - Python style guide
- **PEP 484** - Type hints
- **Google Style** - Docstrings
- **Ruff** - Linting and formatting

### Type Hints

All code must have complete type annotations:

```python
from typing import Any
from collections.abc import Sequence

async def get_users(
    limit: int = 100,
    offset: int = 0,
    active_only: bool = True,
) -> Sequence[User]:
    """Retrieve users with pagination.

    Args:
        limit: Maximum number of users to return.
        offset: Number of users to skip.
        active_only: Filter to active users only.

    Returns:
        A sequence of User objects.
    """
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def process_data(
    data: dict[str, Any],
    validate: bool = True,
) -> ProcessedResult:
    """Process input data with optional validation.

    Args:
        data: Input data dictionary containing:
            - 'input': Raw data to process
            - 'options': Processing options (optional)
        validate: If True, validates data before processing.

    Returns:
        Processed result object with status and output.

    Raises:
        ValueError: If input data is invalid.
        ProcessingError: If processing fails.

    Example:
        >>> result = process_data({"input": "test"})
        >>> print(result.status)
        'success'
    """
    ...
```

### Import Organization

Organize imports in this order:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.users.models import User
from pydotorg.domains.users.schemas import UserRead

if TYPE_CHECKING:
    from collections.abc import Sequence
```

## Project Structure

### Domain Module Pattern

Each domain follows a consistent structure:

```
domains/example/
├── __init__.py          # Public exports
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── services.py          # Business logic
├── controllers.py       # HTTP handlers
├── repositories.py      # Data access (optional)
├── dependencies.py      # Domain-specific DI
└── guards.py            # Domain-specific guards
```

### Creating a New Domain

1. Create the domain directory structure
2. Define models with SQLAlchemy
3. Create Pydantic schemas for input/output
4. Implement service layer for business logic
5. Build controllers for HTTP endpoints
6. Register routes in the main application
7. Write tests

Example domain creation:

```python
# domains/example/models.py
from sqlalchemy.orm import Mapped, mapped_column
from pydotorg.core.database import Base, TimestampMixin

class Example(Base, TimestampMixin):
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
```

```python
# domains/example/schemas.py
from pydantic import BaseModel, ConfigDict, Field

class ExampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None

class ExampleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
```

```python
# domains/example/services.py
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Example
from .schemas import ExampleCreate

class ExampleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ExampleCreate) -> Example:
        example = Example(**data.model_dump())
        self.session.add(example)
        await self.session.flush()
        return example
```

```python
# domains/example/controllers.py
from litestar import Controller, get, post
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import ExampleRead, ExampleCreate
from .services import ExampleService

class ExampleController(Controller):
    path = "/examples"

    @get("/")
    async def list_examples(self, db_session: AsyncSession) -> list[ExampleRead]:
        service = ExampleService(db_session)
        return await service.list_all()

    @post("/")
    async def create_example(
        self,
        data: ExampleCreate,
        db_session: AsyncSession,
    ) -> ExampleRead:
        service = ExampleService(db_session)
        return await service.create(data)
```

## Git Workflow

### Branch Naming

Use descriptive branch names:

- `feature/add-user-registration` - New features
- `fix/login-validation-error` - Bug fixes
- `refactor/user-service-cleanup` - Code refactoring
- `docs/update-api-guide` - Documentation updates
- `chore/upgrade-dependencies` - Maintenance tasks

### Commit Messages

Follow the conventional commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:

```
feat(users): add password reset functionality

Implement password reset flow with email verification.
Includes token generation, email sending, and reset endpoint.

Closes #123
```

```
fix(auth): correct token expiration validation

The JWT validation was using local time instead of UTC,
causing tokens to appear expired in different timezones.
```

### Pull Request Process

1. Create a feature branch from `main`
2. Implement changes with tests
3. Run quality checks: `make ci`
4. Push and create a pull request
5. Address review feedback
6. Squash and merge when approved

## Quality Checks

### Running Checks

```bash
# Run all CI checks
make ci

# Individual checks
make lint        # Ruff linting
make fmt         # Ruff formatting
make type-check  # ty type checking
make test        # pytest
```

### Pre-commit Hooks

We use prek for git hooks. Install with:

```bash
make install
```

This automatically runs checks before each commit.

### Continuous Integration

All pull requests must pass:

- Linting (Ruff)
- Type checking (ty)
- Tests (pytest)
- Coverage threshold

## Database Migrations

### Creating Migrations

When you modify models, create a migration:

```bash
# Auto-generate from model changes
make litestar-db-make

# Review the generated migration file
# migrations/versions/xxxx_your_message.py
```

### Applying Migrations

```bash
# Apply all pending migrations
make litestar-db-upgrade

# Rollback one migration
make litestar-db-downgrade

# Show migration history
make litestar-db-history
```

### Migration Best Practices

- Always review auto-generated migrations
- Include both upgrade and downgrade
- Test migrations in development first
- Use descriptive message names
- Keep migrations atomic

## Debugging

### Enable Debug Mode

Set in `.env`:

```bash
DEBUG=true
DATABASE_ECHO=true  # Log SQL queries
```

### Using Breakpoints

```python
# Python built-in debugger
breakpoint()

# Or IPython debugger
import ipdb; ipdb.set_trace()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

## Performance Considerations

### Async Best Practices

- Use `async/await` for all I/O operations
- Avoid blocking calls in async code
- Use connection pooling for databases
- Cache expensive computations

### Query Optimization

- Use `select_in_loading` for relationships
- Avoid N+1 queries
- Use pagination for large datasets
- Profile slow queries

## Getting Help

- Check existing documentation
- Search GitHub issues
- Ask in team Slack channel
- Create a detailed issue if needed
