# Testing Guide

This guide covers testing strategies and best practices for litestar-pydotorg.

## Overview

The project uses a comprehensive testing strategy with three levels:

- **Unit Tests** - Fast, isolated tests for individual components
- **Integration Tests** - Database and API tests
- **End-to-End Tests** - Full user journey tests

## Test Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   └── domains/
│       └── users/
│           ├── test_models.py
│           ├── test_services.py
│           └── test_schemas.py
├── integration/             # Database, API tests
│   └── domains/
│       └── users/
│           ├── test_controllers.py
│           └── test_repositories.py
└── e2e/                     # Full user journey tests
    └── test_user_registration.py
```

## Running Tests

### All Tests

```bash
make test

# Or directly
uv run pytest
```

### With Coverage

```bash
make coverage

# Or directly
uv run pytest --cov=pydotorg --cov-report=html
```

### Specific Tests

```bash
# Run specific test file
uv run pytest tests/unit/domains/users/test_models.py -v

# Run tests matching pattern
uv run pytest -k "test_user" -v

# Run only unit tests
uv run pytest tests/unit -v

# Run only integration tests
uv run pytest tests/integration -v

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf
```

## Writing Unit Tests

Unit tests should be fast and isolated.

### Testing Models

```python
# tests/unit/domains/users/test_models.py
import pytest
from pydotorg.domains.users.models import User

class TestUser:
    def test_create_user(self):
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_user_full_name(self):
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        assert user.full_name == "Test User"

    def test_user_str(self):
        user = User(username="testuser", email="test@example.com")
        assert str(user) == "testuser"
```

### Testing Services

```python
# tests/unit/domains/users/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from pydotorg.domains.users.services import UserService
from pydotorg.domains.users.schemas import UserCreate

class TestUserService:
    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return UserService(mock_session)

    @pytest.mark.asyncio
    async def test_create_user(self, service, mock_session):
        data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )

        user = await service.create(data)

        assert mock_session.add.called
        assert mock_session.flush.called
```

### Testing Schemas

```python
# tests/unit/domains/users/test_schemas.py
import pytest
from pydantic import ValidationError
from pydotorg.domains.users.schemas import UserCreate, UserRead

class TestUserCreate:
    def test_valid_user_create(self):
        data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        assert data.username == "testuser"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                password="SecurePass123!"
            )

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="a",
                email="test@example.com",
                password="SecurePass123!"
            )
```

## Writing Integration Tests

Integration tests use real database connections.

### Database Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pydotorg.core.database import Base

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg_test",
        echo=True
    )

@pytest.fixture
async def db_session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Testing Controllers

```python
# tests/integration/domains/users/test_controllers.py
import pytest
from litestar.testing import TestClient
from pydotorg.main import app

class TestUserController:
    @pytest.fixture
    def client(self):
        return TestClient(app=app)

    def test_list_users(self, client):
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_user_not_found(self, client):
        response = client.get("/api/v1/users/nonexistent-id")
        assert response.status_code == 404

    def test_create_user(self, client):
        response = client.post(
            "/api/v1/users/",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 201
        assert response.json()["username"] == "newuser"
```

### Testing with Authentication

```python
# tests/integration/domains/users/test_authenticated.py
import pytest
from litestar.testing import TestClient

class TestAuthenticatedEndpoints:
    @pytest.fixture
    def authenticated_client(self, client):
        # Login first
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass"}
        )
        tokens = response.json()

        # Add token to headers
        client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
        return client

    def test_get_current_user(self, authenticated_client):
        response = authenticated_client.post("/api/auth/me")
        assert response.status_code == 200
        assert "username" in response.json()

    def test_protected_endpoint_without_auth(self, client):
        response = client.post("/api/auth/me")
        assert response.status_code == 401
```

## Testing Feature Flags

```python
# tests/unit/core/test_features.py
import pytest
from litestar import Litestar, get
from litestar.testing import TestClient
from pydotorg.core.features import FeatureFlags, require_feature

class TestFeatureFlags:
    def test_feature_enabled(self):
        flags = FeatureFlags(enable_oauth=True)
        assert flags.is_enabled("enable_oauth") is True

    def test_feature_disabled(self):
        flags = FeatureFlags(enable_oauth=False)
        assert flags.is_enabled("enable_oauth") is False

    def test_require_feature_guard_blocks_disabled(self):
        @get("/test", guards=[require_feature("enable_oauth")])
        def handler() -> dict:
            return {"status": "ok"}

        def init_app(app: Litestar) -> None:
            app.state.feature_flags = FeatureFlags(enable_oauth=False)

        app = Litestar(
            route_handlers=[handler],
            on_app_init=[init_app],
        )

        client = TestClient(app=app)
        response = client.get("/test")
        assert response.status_code == 503

    def test_require_feature_guard_allows_enabled(self):
        @get("/test", guards=[require_feature("enable_oauth")])
        def handler() -> dict:
            return {"status": "ok"}

        def init_app(app: Litestar) -> None:
            app.state.feature_flags = FeatureFlags(enable_oauth=True)

        app = Litestar(
            route_handlers=[handler],
            on_app_init=[init_app],
        )

        client = TestClient(app=app)
        response = client.get("/test")
        assert response.status_code == 200
```

## Fixtures and Factories

### User Factory

```python
# tests/factories.py
import factory
from pydotorg.domains.users.models import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
```

### Using Factories

```python
# tests/unit/domains/users/test_with_factories.py
from tests.factories import UserFactory

class TestUserWithFactory:
    def test_create_user(self):
        user = UserFactory()
        assert user.username.startswith("user")
        assert "@example.com" in user.email

    def test_create_inactive_user(self):
        user = UserFactory(is_active=False)
        assert user.is_active is False
```

## Mocking

### Mocking External Services

```python
# tests/unit/test_external_services.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_send_email():
    with patch("pydotorg.lib.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        from pydotorg.lib.email import send_email
        result = await send_email("test@example.com", "Subject", "Body")

        assert result is True
        mock_send.assert_called_once_with("test@example.com", "Subject", "Body")
```

### Mocking Database

```python
# tests/unit/test_with_mock_db.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session
```

## Async Testing

Use `pytest-asyncio` for async tests:

```python
# tests/integration/test_async.py
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    from pydotorg.domains.users.services import UserService

    service = UserService(mock_session)
    result = await service.get_by_id("user-id")

    assert result is not None
```

## Performance Testing

```python
# tests/performance/test_api_performance.py
import pytest
import time

class TestAPIPerformance:
    def test_list_users_response_time(self, client):
        start = time.time()
        response = client.get("/api/v1/users/")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # Should respond in under 100ms
```

## Code Coverage

View coverage report:

```bash
# Generate HTML report
uv run pytest --cov=pydotorg --cov-report=html

# Open report
open htmlcov/index.html
```

Minimum coverage threshold is configured in `pyproject.toml`.

## Best Practices

1. **Test one thing per test** - Each test should verify a single behavior
2. **Use descriptive names** - Test names should describe what is being tested
3. **Follow AAA pattern** - Arrange, Act, Assert
4. **Mock external dependencies** - Isolate tests from external services
5. **Use fixtures** - Share common setup code
6. **Keep tests fast** - Unit tests should run in milliseconds
7. **Test edge cases** - Include boundary conditions and error cases
8. **Maintain test data** - Use factories for consistent test data
