"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
import socket
from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.config import EngineConfig
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import (
    SQLAlchemyAsyncConfig,
    autocommit_before_send_handler,
)
from litestar import Litestar
from litestar.testing import AsyncTestClient, TestClient
from pytest_databases.docker.postgres import PostgresService
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import pydotorg.domains  # noqa: F401 - ensure all models are loaded
from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Generator

    from pytest_databases._service import DockerService
    from pytest_databases.types import XdistIsolationLevel


def _is_port_open(host: str, port: int) -> bool:
    """Check if a port is open on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


def _ensure_test_database(host: str, port: int, user: str, password: str, database: str) -> None:
    """Create the test database if it doesn't exist."""
    import psycopg

    conn_str = f"dbname=postgres user={user} host={host} port={port} password={password}"
    with psycopg.connect(conn_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{database}"')


@pytest.fixture(scope="session")
def postgres_service(
    docker_service: DockerService,
    postgres_image: str,
    xdist_postgres_isolation_level: XdistIsolationLevel,
    postgres_host: str,
    postgres_user: str,
    postgres_password: str,
) -> Generator[PostgresService]:
    """Override postgres_service to use existing dev container when available.

    In local development, pydotorg-postgres runs on port 5432.
    In CI or when no container exists, pytest-databases spins up a fresh one.
    """
    dev_host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    dev_port = int(os.environ.get("POSTGRES_PORT", "5432"))
    dev_user = os.environ.get("POSTGRES_USER", "postgres")
    dev_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    dev_database = os.environ.get("POSTGRES_DB", "pydotorg_test")

    if _is_port_open(dev_host, dev_port):
        _ensure_test_database(dev_host, dev_port, dev_user, dev_password, dev_database)
        yield PostgresService(
            host=dev_host,
            port=dev_port,
            user=dev_user,
            password=dev_password,
            database=dev_database,
        )
    else:
        from pytest_databases.docker.postgres import _provide_postgres_service

        with _provide_postgres_service(
            docker_service,
            image=postgres_image,
            name="postgres",
            xdist_postgres_isolate=xdist_postgres_isolation_level,
            host=postgres_host,
            user=postgres_user,
            password=postgres_password,
        ) as service:
            yield service


pytest_plugins = ["pytest_databases.docker.postgres"]


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


@pytest.fixture(scope="session")
async def async_engine(postgres_uri: str) -> AsyncIterator[AsyncEngine]:
    """Session-scoped async engine for integration tests.

    Provides a single engine instance to prevent connection pool exhaustion.
    Creates tables once at the start of the session.
    """
    from sqlalchemy import text

    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        # Drop all tables with CASCADE to handle FK dependencies
        for table in reversed(AuditBase.metadata.sorted_tables):
            await conn.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE'))
        await conn.run_sync(AuditBase.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def _module_sqlalchemy_config(postgres_uri: str) -> SQLAlchemyAsyncConfig:
    """Session-scoped SQLAlchemy config to prevent creating engines per module.

    Uses autocommit_before_send_handler to ensure transactions are committed
    before closing sessions, which fixes the issue where data created in one
    request isn't visible in subsequent requests.
    """
    return SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        engine_config=EngineConfig(poolclass=NullPool),
        before_send_handler=autocommit_before_send_handler,
    )


@pytest.fixture(scope="session")
def async_session_factory(async_engine: AsyncEngine):
    """Session-scoped async session factory using shared engine.

    Provides a consistent way to create sessions without spawning new engines.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    return async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture
async def truncate_tables(async_engine: AsyncEngine) -> None:
    """Truncate all tables before each test for isolation."""
    from sqlalchemy import text

    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result.fetchall()}

        for table in reversed(AuditBase.metadata.sorted_tables):
            if table.name in existing_tables:
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))


@pytest.fixture(scope="session")
async def client(
    async_engine: AsyncEngine,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[AsyncTestClient]:
    """Session-scoped async test client with PostgreSQL database.

    Uses session-scoped engine. Test isolation is handled by the
    truncate_tables fixture which tests should use via autouse or explicit dependency.
    """
    from litestar.middleware.session.client_side import CookieBackendConfig

    from pydotorg.config import settings
    from pydotorg.domains.users.auth_controller import AuthController
    from pydotorg.main import _derive_session_secret, health_check

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    session_config = CookieBackendConfig(
        secret=_derive_session_secret(settings.session_secret_key),
        max_age=settings.session_expire_minutes * 60,
    )

    test_app = Litestar(
        route_handlers=[health_check, AuthController],
        plugins=[sqlalchemy_plugin],
        middleware=[session_config.middleware, JWTAuthMiddleware],
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        yield test_client
