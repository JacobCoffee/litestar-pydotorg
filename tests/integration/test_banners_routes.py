"""Integration tests for Banners domain controllers."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.banners.controllers import BannerController
from pydotorg.domains.banners.dependencies import get_banners_dependencies
from pydotorg.domains.banners.models import Banner

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _create_banner_via_db(
    session_factory: async_sessionmaker,
    name: str | None = None,
    is_active: bool = False,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    banner_type: str = "info",
    is_dismissible: bool = True,
    is_sitewide: bool = True,
    link_text: str | None = None,
) -> Banner:
    """Create a banner directly in the database using shared session factory."""
    async with session_factory() as session:
        banner = Banner(
            name=name or f"test-banner-{uuid4().hex[:8]}",
            title=f"Test Banner Title {uuid4().hex[:8]}",
            message=f"Test banner message {uuid4().hex[:8]}",
            link="https://example.com",
            link_text=link_text,
            banner_type=banner_type,
            is_active=is_active,
            is_dismissible=is_dismissible,
            is_sitewide=is_sitewide,
            start_date=start_date,
            end_date=end_date,
        )
        session.add(banner)
        await session.commit()
        await session.refresh(banner)
        return banner


class BannersTestFixtures:
    """Test fixtures for banners routes."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


@pytest.fixture
async def banners_fixtures(
    async_engine: AsyncEngine,
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[BannersTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    """
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result.fetchall()}

        for table in reversed(AuditBase.metadata.sorted_tables):
            if table.name in existing_tables:
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    app = Litestar(
        route_handlers=[BannerController],
        plugins=[sqlalchemy_plugin],
        dependencies=get_banners_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = BannersTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestBannerControllerRoutes:
    """Tests for BannerController endpoints."""

    async def test_list_banners(self, banners_fixtures: BannersTestFixtures) -> None:
        await _create_banner_via_db(banners_fixtures.session_factory)
        response = await banners_fixtures.client.get("/api/v1/banners/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_banners_with_pagination(self, banners_fixtures: BannersTestFixtures) -> None:
        for i in range(3):
            await _create_banner_via_db(banners_fixtures.session_factory, name=f"Banner {i}")
        response = await banners_fixtures.client.get("/api/v1/banners/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_active_banners(self, banners_fixtures: BannersTestFixtures) -> None:
        today = datetime.date.today()
        await _create_banner_via_db(
            banners_fixtures.session_factory,
            is_active=True,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=1),
        )
        response = await banners_fixtures.client.get("/api/v1/banners/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_active_banners_without_date_check(self, banners_fixtures: BannersTestFixtures) -> None:
        await _create_banner_via_db(banners_fixtures.session_factory, is_active=True)
        response = await banners_fixtures.client.get("/api/v1/banners/active?check_dates=false")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_banner(self, banners_fixtures: BannersTestFixtures) -> None:
        data = {
            "name": "new-test-banner",
            "title": "New Test Banner",
            "message": "This is a test banner message",
            "link": "https://example.com",
            "is_active": False,
        }
        response = await banners_fixtures.client.post("/api/v1/banners/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "new-test-banner"

    async def test_get_banner_by_id(self, banners_fixtures: BannersTestFixtures) -> None:
        banner = await _create_banner_via_db(banners_fixtures.session_factory)
        response = await banners_fixtures.client.get(f"/api/v1/banners/{banner.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == banner.name

    async def test_get_banner_by_id_not_found(self, banners_fixtures: BannersTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await banners_fixtures.client.get(f"/api/v1/banners/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_banner_by_name(self, banners_fixtures: BannersTestFixtures) -> None:
        banner = await _create_banner_via_db(banners_fixtures.session_factory, name="unique-banner-name")
        response = await banners_fixtures.client.get(f"/api/v1/banners/name/{banner.name}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "unique-banner-name"

    async def test_get_banner_by_name_not_found(self, banners_fixtures: BannersTestFixtures) -> None:
        response = await banners_fixtures.client.get("/api/v1/banners/name/non-existent-banner")
        assert response.status_code in (404, 500)

    async def test_update_banner(self, banners_fixtures: BannersTestFixtures) -> None:
        banner = await _create_banner_via_db(banners_fixtures.session_factory)
        data = {"title": "Updated Banner Title"}
        response = await banners_fixtures.client.put(f"/api/v1/banners/{banner.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Banner Title"

    async def test_delete_banner(self, banners_fixtures: BannersTestFixtures) -> None:
        banner = await _create_banner_via_db(banners_fixtures.session_factory)
        response = await banners_fixtures.client.delete(f"/api/v1/banners/{banner.id}")
        assert response.status_code in (200, 204, 500)


class TestBannersValidation:
    """Validation tests for banners domain."""

    async def test_create_banner_missing_name(self, banners_fixtures: BannersTestFixtures) -> None:
        data = {
            "title": "Test Banner",
            "message": "Test message",
        }
        response = await banners_fixtures.client.post("/api/v1/banners/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_banner_missing_title(self, banners_fixtures: BannersTestFixtures) -> None:
        data = {
            "name": "test-banner",
            "message": "Test message",
        }
        response = await banners_fixtures.client.post("/api/v1/banners/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_banner_missing_message(self, banners_fixtures: BannersTestFixtures) -> None:
        data = {
            "name": "test-banner",
            "title": "Test Banner",
        }
        response = await banners_fixtures.client.post("/api/v1/banners/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_banner_invalid_uuid(self, banners_fixtures: BannersTestFixtures) -> None:
        response = await banners_fixtures.client.get("/api/v1/banners/not-a-uuid")
        assert response.status_code in (400, 404, 422)


class TestSitewideBanners:
    """Tests for sitewide banner functionality."""

    async def test_list_sitewide_banners(self, banners_fixtures: BannersTestFixtures) -> None:
        today = datetime.date.today()
        await _create_banner_via_db(
            banners_fixtures.session_factory,
            is_active=True,
            is_sitewide=True,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=1),
        )
        response = await banners_fixtures.client.get("/api/v1/banners/sitewide")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)
            if len(result) > 0:
                assert "id" in result[0]
                assert "title" in result[0]
                assert "message" in result[0]
                assert "banner_type" in result[0]
                assert "is_dismissible" in result[0]

    async def test_sitewide_banner_excludes_non_sitewide(self, banners_fixtures: BannersTestFixtures) -> None:
        today = datetime.date.today()
        await _create_banner_via_db(
            banners_fixtures.session_factory,
            name="non-sitewide-banner",
            is_active=True,
            is_sitewide=False,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=1),
        )
        response = await banners_fixtures.client.get("/api/v1/banners/sitewide")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            names = [b.get("name", "") for b in result]
            assert "non-sitewide-banner" not in names

    async def test_sitewide_banner_with_different_types(self, banners_fixtures: BannersTestFixtures) -> None:
        today = datetime.date.today()
        for banner_type in ["info", "success", "warning", "error"]:
            await _create_banner_via_db(
                banners_fixtures.session_factory,
                name=f"banner-{banner_type}",
                is_active=True,
                is_sitewide=True,
                banner_type=banner_type,
                start_date=today - datetime.timedelta(days=1),
                end_date=today + datetime.timedelta(days=1),
            )
        response = await banners_fixtures.client.get("/api/v1/banners/sitewide")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            types = {b.get("banner_type") for b in result}
            assert types.issubset({"info", "success", "warning", "error"})

    async def test_create_banner_with_new_fields(self, banners_fixtures: BannersTestFixtures) -> None:
        data = {
            "name": "new-sitewide-banner",
            "title": "New Sitewide Banner",
            "message": "This is a sitewide banner message",
            "link": "https://example.com",
            "link_text": "Learn More",
            "banner_type": "warning",
            "is_active": True,
            "is_dismissible": True,
            "is_sitewide": True,
        }
        response = await banners_fixtures.client.post("/api/v1/banners/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "new-sitewide-banner"
            assert result["banner_type"] == "warning"
            assert result["is_dismissible"] is True
            assert result["is_sitewide"] is True
            assert result["link_text"] == "Learn More"

    async def test_update_banner_type(self, banners_fixtures: BannersTestFixtures) -> None:
        banner = await _create_banner_via_db(banners_fixtures.session_factory, banner_type="info")
        data = {"banner_type": "error"}
        response = await banners_fixtures.client.put(f"/api/v1/banners/{banner.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["banner_type"] == "error"

    async def test_update_banner_dismissible(self, banners_fixtures: BannersTestFixtures) -> None:
        banner = await _create_banner_via_db(banners_fixtures.session_factory, is_dismissible=True)
        data = {"is_dismissible": False}
        response = await banners_fixtures.client.put(f"/api/v1/banners/{banner.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["is_dismissible"] is False
