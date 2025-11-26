"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.extensions.litestar import async_autocommit_before_send_handler
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import pydotorg.domains  # noqa: F401 - ensure all models are loaded
from pydotorg.core.database.base import AuditBase
from pydotorg.main import app

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
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncTestClient]:
    async def get_db_session_override() -> AsyncSession:
        return db_session

    app.state.db_session = db_session

    async with AsyncTestClient(
        app=app,
        base_url="http://testserver",
        before_send_handler=async_autocommit_before_send_handler,
    ) as client:
        yield client
