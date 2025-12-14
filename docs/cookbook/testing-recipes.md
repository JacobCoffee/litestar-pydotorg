# Testing Recipes

Common testing patterns and fixtures for litestar-pydotorg.

## Test Setup

### Pytest Configuration

```python
# tests/conftest.py
import pytest
from litestar.testing import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from pydotorg.core.database import Base
from pydotorg.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg_test",
        echo=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine):
    """Create a new database session for each test."""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app=app)
```

## Testing Controllers

### Basic Controller Test

```python
# tests/integration/domains/users/test_controllers.py
import pytest
from litestar.testing import TestClient

class TestUserController:
    def test_list_users(self, client: TestClient):
        response = client.get("/api/v1/users/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_user_not_found(self, client: TestClient):
        response = client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_user(self, client: TestClient):
        response = client.post(
            "/api/v1/users/",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
```

### Authenticated Controller Test

```python
@pytest.fixture
def auth_client(client: TestClient):
    """Create authenticated test client."""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "authuser",
            "email": "auth@example.com",
            "password": "SecurePass123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "username": "authuser",
            "password": "SecurePass123!",
        },
    )

    tokens = response.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


class TestProtectedEndpoints:
    def test_get_profile(self, auth_client: TestClient):
        response = auth_client.post("/api/auth/me")

        assert response.status_code == 200
        assert response.json()["username"] == "authuser"

    def test_unauthorized_access(self, client: TestClient):
        response = client.post("/api/auth/me")

        assert response.status_code == 401
```

## Testing Services

### Service with Mock Session

```python
# tests/unit/domains/users/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from pydotorg.domains.users.services import UserService
from pydotorg.domains.users.schemas import UserCreate
from pydotorg.domains.users.models import User


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def user_service(mock_session):
    return UserService(mock_session)


class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user(self, user_service, mock_session):
        data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="SecurePass123!",
        )

        result = await user_service.create(data)

        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_get_by_id(self, user_service, mock_session):
        user_id = uuid4()
        expected_user = User(id=user_id, username="test")
        mock_session.get.return_value = expected_user

        result = await user_service.get_by_id(user_id)

        assert result == expected_user
        mock_session.get.assert_called_once_with(User, user_id)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_service, mock_session):
        mock_session.get.return_value = None

        result = await user_service.get_by_id(uuid4())

        assert result is None
```

## Testing with Database

### Integration Test with Real Database

```python
# tests/integration/domains/users/test_user_service.py
import pytest
from pydotorg.domains.users.services import UserService
from pydotorg.domains.users.schemas import UserCreate


class TestUserServiceIntegration:
    @pytest.mark.asyncio
    async def test_create_and_retrieve_user(self, db_session):
        service = UserService(db_session)

        # Create user
        data = UserCreate(
            username="dbuser",
            email="db@example.com",
            password="SecurePass123!",
        )
        created = await service.create(data)
        await db_session.commit()

        # Retrieve user
        retrieved = await service.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.username == "dbuser"
        assert retrieved.email == "db@example.com"

    @pytest.mark.asyncio
    async def test_update_user(self, db_session):
        service = UserService(db_session)

        # Create user
        user = await service.create(
            UserCreate(
                username="updateuser",
                email="update@example.com",
                password="SecurePass123!",
            )
        )
        await db_session.commit()

        # Update user
        from pydotorg.domains.users.schemas import UserUpdate
        updated = await service.update(
            user,
            UserUpdate(first_name="Updated"),
        )
        await db_session.commit()

        assert updated.first_name == "Updated"
```

## Test Factories

### Factory Pattern

```python
# tests/factories.py
import factory
from uuid import uuid4
from datetime import datetime

from pydotorg.domains.users.models import User
from pydotorg.domains.products.models import Product


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.LazyFunction(uuid4)
    name = factory.Faker("product_name")
    description = factory.Faker("paragraph")
    price = factory.Faker("pyfloat", min_value=1, max_value=1000, right_digits=2)
    is_active = True
    owner_id = factory.LazyFunction(uuid4)
```

### Using Factories

```python
from tests.factories import UserFactory, ProductFactory


class TestWithFactories:
    def test_create_user(self):
        user = UserFactory()

        assert user.username.startswith("user")
        assert user.is_active is True

    def test_create_admin_user(self):
        admin = UserFactory(is_staff=True, is_superuser=True)

        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_create_product_with_owner(self):
        user = UserFactory()
        product = ProductFactory(owner_id=user.id)

        assert product.owner_id == user.id
```

## Mocking External Services

### Mock HTTP Requests

```python
import pytest
from unittest.mock import patch, AsyncMock
import httpx


@pytest.mark.asyncio
async def test_external_api_call():
    mock_response = AsyncMock()
    mock_response.json.return_value = {"data": "mocked"}
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        from mymodule import fetch_external_data

        result = await fetch_external_data()

        assert result == {"data": "mocked"}
```

### Mock Redis

```python
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.mark.asyncio
async def test_caching(mock_redis):
    from pydotorg.lib.cache import CacheService

    cache = CacheService(mock_redis)

    await cache.set("key", "value", ttl=300)

    mock_redis.set.assert_called_once()
    mock_redis.expire.assert_called_once_with("key", 300)
```

### Mock Email Service

```python
@pytest.fixture
def mock_email_service():
    with patch("pydotorg.lib.email.send_email", new_callable=AsyncMock) as mock:
        mock.return_value = True
        yield mock


@pytest.mark.asyncio
async def test_send_verification_email(mock_email_service):
    from pydotorg.domains.users.services import send_verification

    await send_verification("user@example.com", "token123")

    mock_email_service.assert_called_once()
    call_args = mock_email_service.call_args
    assert call_args[0][0] == "user@example.com"
    assert "verification" in call_args[0][1].lower()
```

## Testing Feature Flags

```python
import pytest
from litestar import Litestar, get
from litestar.testing import TestClient

from pydotorg.core.features import FeatureFlags, require_feature


class TestFeatureFlags:
    def test_feature_enabled(self):
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

    def test_feature_disabled(self):
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
```

## Snapshot Testing

```python
import pytest
import json


@pytest.fixture
def snapshot_json(snapshot):
    """Custom snapshot for JSON responses."""
    def check(data):
        snapshot.assert_match(json.dumps(data, indent=2, default=str))
    return check


def test_api_response_structure(client: TestClient, snapshot_json):
    response = client.get("/api/v1/releases/latest")

    # First run creates snapshot, subsequent runs compare
    snapshot_json(response.json())
```

## Performance Testing

```python
import pytest
import time


@pytest.mark.slow
def test_list_users_performance(client: TestClient):
    start = time.perf_counter()

    response = client.get("/api/v1/users/?limit=100")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < 0.1  # Should respond in under 100ms


@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_requests(client: TestClient):
    import asyncio

    async def make_request():
        return client.get("/api/v1/users/")

    tasks = [make_request() for _ in range(10)]

    start = time.perf_counter()
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    assert all(r.status_code == 200 for r in responses)
    assert elapsed < 1.0  # 10 requests in under 1 second
```

## Parametrized Tests

```python
import pytest


@pytest.mark.parametrize("username,expected_status", [
    ("validuser", 201),
    ("ab", 422),  # Too short
    ("a" * 256, 422),  # Too long
    ("user@name", 422),  # Invalid characters
])
def test_username_validation(client: TestClient, username, expected_status):
    response = client.post(
        "/api/v1/users/",
        json={
            "username": username,
            "email": "test@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == expected_status


@pytest.mark.parametrize("email", [
    "valid@example.com",
    "user.name@domain.org",
    "user+tag@example.co.uk",
])
def test_valid_email_formats(client: TestClient, email):
    response = client.post(
        "/api/v1/users/",
        json={
            "username": f"user_{email.split('@')[0]}",
            "email": email,
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 201
```

## See Also

- [Testing Guide](../guides/testing.md) - Full testing documentation
- [Domain Patterns](domain-patterns.md) - Testing domain code
- [Debugging Guide](../guides/debugging.md) - Debug failing tests
