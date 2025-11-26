"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient, TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import pydotorg.domains  # noqa: F401 - ensure all models are loaded
from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client() -> TestClient:
    """Simple test client for unit tests that don't need database."""
    app = Litestar(route_handlers=[])
    return TestClient(app=app)


@pytest.fixture
async def client(engine) -> AsyncIterator[AsyncTestClient]:
    """Async test client with SQLite database for integration tests."""
    from pydotorg.domains.users.auth_controller import AuthController
    from pydotorg.main import health_check, index

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string="sqlite+aiosqlite:///:memory:",
        metadata=AuditBase.metadata,
        create_all=True,
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    test_app = Litestar(
        route_handlers=[index, health_check, AuthController],
        plugins=[sqlalchemy_plugin],
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        yield test_client
