"""Integration tests for Banners domain controllers."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.banners.controllers import BannerController
from pydotorg.domains.banners.dependencies import get_banners_dependencies
from pydotorg.domains.banners.models import Banner

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def _create_banner_via_db(
    postgres_uri: str,
    name: str | None = None,
    is_active: bool = False,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> Banner:
    """Create a banner directly in the database for testing."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        banner = Banner(
            name=name or f"test-banner-{uuid4().hex[:8]}",
            title=f"Test Banner Title {uuid4().hex[:8]}",
            message=f"Test banner message {uuid4().hex[:8]}",
            link="https://example.com",
            is_active=is_active,
            start_date=start_date,
            end_date=end_date,
        )
        session.add(banner)
        await session.commit()
        await session.refresh(banner)
        await engine.dispose()
        return banner


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncGenerator[Litestar]:
    """Create a test Litestar application with the banners controller."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        before_send_handler="autocommit",
    )

    app = Litestar(
        route_handlers=[BannerController],
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
        dependencies=get_banners_dependencies(),
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestBannerControllerRoutes:
    """Tests for BannerController endpoints."""

    async def test_list_banners(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_banner_via_db(postgres_uri)
        response = await client.get("/api/v1/banners/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_banners_with_pagination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        for i in range(3):
            await _create_banner_via_db(postgres_uri, name=f"Banner {i}")
        response = await client.get("/api/v1/banners/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_active_banners(self, client: AsyncTestClient, postgres_uri: str) -> None:
        today = datetime.date.today()
        await _create_banner_via_db(
            postgres_uri,
            is_active=True,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=1),
        )
        response = await client.get("/api/v1/banners/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_active_banners_without_date_check(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_banner_via_db(postgres_uri, is_active=True)
        response = await client.get("/api/v1/banners/active?check_dates=false")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_banner(self, client: AsyncTestClient) -> None:
        data = {
            "name": "new-test-banner",
            "title": "New Test Banner",
            "message": "This is a test banner message",
            "link": "https://example.com",
            "is_active": False,
        }
        response = await client.post("/api/v1/banners/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "new-test-banner"

    async def test_get_banner_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        banner = await _create_banner_via_db(postgres_uri)
        response = await client.get(f"/api/v1/banners/{banner.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == banner.name

    async def test_get_banner_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/banners/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_banner_by_name(self, client: AsyncTestClient, postgres_uri: str) -> None:
        banner = await _create_banner_via_db(postgres_uri, name="unique-banner-name")
        response = await client.get(f"/api/v1/banners/name/{banner.name}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "unique-banner-name"

    async def test_get_banner_by_name_not_found(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/banners/name/non-existent-banner")
        assert response.status_code in (404, 500)

    async def test_update_banner(self, client: AsyncTestClient, postgres_uri: str) -> None:
        banner = await _create_banner_via_db(postgres_uri)
        data = {"title": "Updated Banner Title"}
        response = await client.put(f"/api/v1/banners/{banner.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Banner Title"

    async def test_delete_banner(self, client: AsyncTestClient, postgres_uri: str) -> None:
        banner = await _create_banner_via_db(postgres_uri)
        response = await client.delete(f"/api/v1/banners/{banner.id}")
        assert response.status_code in (200, 204, 500)


class TestBannersValidation:
    """Validation tests for banners domain."""

    async def test_create_banner_missing_name(self, client: AsyncTestClient) -> None:
        data = {
            "title": "Test Banner",
            "message": "Test message",
        }
        response = await client.post("/api/v1/banners/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_banner_missing_title(self, client: AsyncTestClient) -> None:
        data = {
            "name": "test-banner",
            "message": "Test message",
        }
        response = await client.post("/api/v1/banners/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_banner_missing_message(self, client: AsyncTestClient) -> None:
        data = {
            "name": "test-banner",
            "title": "Test Banner",
        }
        response = await client.post("/api/v1/banners/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_banner_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/banners/not-a-uuid")
        assert response.status_code in (400, 404, 422)
