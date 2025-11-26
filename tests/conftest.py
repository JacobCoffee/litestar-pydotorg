"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient, TestClient
from sqlalchemy.ext.asyncio import create_async_engine

import pydotorg.domains  # noqa: F401 - ensure all models are loaded
from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from pytest_databases.docker.postgres import PostgresService

pytest_plugins = ["pytest_databases.docker.postgres"]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def postgres_uri(postgres_service: PostgresService) -> str:
    """Build async PostgreSQL connection string from pytest-databases service."""
    return (
        f"postgresql+asyncpg://{postgres_service.user}:{postgres_service.password}"
        f"@{postgres_service.host}:{postgres_service.port}/{postgres_service.database}"
    )


@pytest.fixture
def test_client() -> TestClient:
    """Simple test client for unit tests that don't need database."""
    app = Litestar(route_handlers=[])
    return TestClient(app=app)


@pytest.fixture
async def client(postgres_uri: str) -> AsyncIterator[AsyncTestClient]:
    """Async test client with PostgreSQL database for integration tests.

    Each test gets a fresh database with tables created. Tables are truncated
    before each test to ensure isolation.
    """
    from pydotorg.domains.users.auth_controller import AuthController
    from pydotorg.main import health_check

    engine = create_async_engine(postgres_uri, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.drop_all)
        await conn.run_sync(AuditBase.metadata.create_all)

    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    test_app = Litestar(
        route_handlers=[health_check, AuthController],
        plugins=[sqlalchemy_plugin],
        middleware=[JWTAuthMiddleware],
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        yield test_client
