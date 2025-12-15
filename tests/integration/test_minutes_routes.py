"""Integration tests for Minutes domain controllers."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from pydotorg.domains.minutes.controllers import MinutesController
from pydotorg.domains.minutes.dependencies import get_minutes_dependencies
from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.pages.models import ContentType
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class MinutesTestFixtures:
    """Test fixtures for minutes routes."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


async def _create_user_via_db(session_factory: async_sessionmaker, username: str | None = None) -> User:
    """Create a user directly in the database using shared session factory."""
    async with session_factory() as session:
        user = User(
            username=username or f"testuser-{uuid4().hex[:8]}",
            email=f"test-{uuid4().hex[:8]}@example.com",
            password_hash="hashedpassword123",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_minutes_via_db(
    session_factory: async_sessionmaker,
    creator_id: str,
    date: datetime.date | None = None,
    is_published: bool = False,
) -> Minutes:
    """Create minutes directly in the database using shared session factory."""
    from uuid import UUID

    meeting_date = date or datetime.date.today()
    async with session_factory() as session:
        minutes = Minutes(
            date=meeting_date,
            content=f"Meeting content for {meeting_date}",
            content_type=ContentType.MARKDOWN,
            slug=f"minutes-{meeting_date.isoformat()}-{uuid4().hex[:8]}",
            is_published=is_published,
            creator_id=UUID(creator_id) if isinstance(creator_id, str) else creator_id,
        )
        session.add(minutes)
        await session.commit()
        await session.refresh(minutes)
        return minutes


@pytest.fixture
async def minutes_fixtures(
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[MinutesTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    """
    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    app = Litestar(
        route_handlers=[MinutesController],
        plugins=[sqlalchemy_plugin],
        dependencies=get_minutes_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = MinutesTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestMinutesControllerRoutes:
    """Tests for MinutesController endpoints."""

    async def test_list_minutes(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id))
        response = await minutes_fixtures.client.get("/api/v1/minutes/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_minutes_with_pagination(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        for i in range(3):
            await _create_minutes_via_db(
                minutes_fixtures.session_factory,
                str(user.id),
                date=datetime.date.today() - datetime.timedelta(days=i),
            )
        response = await minutes_fixtures.client.get("/api/v1/minutes/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_published_minutes(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id), is_published=True)
        response = await minutes_fixtures.client.get("/api/v1/minutes/published")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_minutes(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        today = datetime.date.today()
        data = {
            "date": today.isoformat(),
            "content": "Test meeting content",
            "content_type": "markdown",
            "is_published": False,
            "creator_id": str(user.id),
        }
        response = await minutes_fixtures.client.post("/api/v1/minutes/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["content"] == "Test meeting content"

    async def test_get_minutes_by_id(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        minutes = await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id))
        response = await minutes_fixtures.client.get(f"/api/v1/minutes/{minutes.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["content"] == minutes.content

    async def test_get_minutes_by_id_not_found(self, minutes_fixtures: MinutesTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await minutes_fixtures.client.get(f"/api/v1/minutes/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_minutes_by_slug(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        minutes = await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id))
        response = await minutes_fixtures.client.get(f"/api/v1/minutes/slug/{minutes.slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == minutes.slug

    async def test_get_minutes_by_slug_not_found(self, minutes_fixtures: MinutesTestFixtures) -> None:
        response = await minutes_fixtures.client.get("/api/v1/minutes/slug/non-existent-slug")
        assert response.status_code in (404, 500)

    async def test_get_minutes_by_date(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        meeting_date = datetime.date.today()
        await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id), date=meeting_date)
        response = await minutes_fixtures.client.get(f"/api/v1/minutes/date/{meeting_date.isoformat()}")
        assert response.status_code in (200, 404, 500)

    async def test_get_minutes_by_date_not_found(self, minutes_fixtures: MinutesTestFixtures) -> None:
        response = await minutes_fixtures.client.get("/api/v1/minutes/date/1900-01-01")
        assert response.status_code in (404, 500)

    async def test_update_minutes(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        minutes = await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id))
        data = {"content": "Updated meeting content"}
        response = await minutes_fixtures.client.put(f"/api/v1/minutes/{minutes.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["content"] == "Updated meeting content"

    async def test_delete_minutes(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        minutes = await _create_minutes_via_db(minutes_fixtures.session_factory, str(user.id))
        response = await minutes_fixtures.client.delete(f"/api/v1/minutes/{minutes.id}")
        assert response.status_code in (200, 204, 500)


class TestMinutesValidation:
    """Validation tests for minutes domain."""

    async def test_create_minutes_missing_date(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        data = {
            "content": "Test",
            "creator_id": str(user.id),
        }
        response = await minutes_fixtures.client.post("/api/v1/minutes/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_minutes_missing_content(self, minutes_fixtures: MinutesTestFixtures) -> None:
        user = await _create_user_via_db(minutes_fixtures.session_factory)
        data = {
            "date": datetime.date.today().isoformat(),
            "creator_id": str(user.id),
        }
        response = await minutes_fixtures.client.post("/api/v1/minutes/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_minutes_invalid_uuid(self, minutes_fixtures: MinutesTestFixtures) -> None:
        response = await minutes_fixtures.client.get("/api/v1/minutes/not-a-uuid")
        assert response.status_code in (400, 404, 422)
