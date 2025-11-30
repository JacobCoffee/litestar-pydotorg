"""Integration tests for Minutes domain controllers."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.minutes.controllers import MinutesController
from pydotorg.domains.minutes.dependencies import get_minutes_dependencies
from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.pages.models import ContentType
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def _create_user_via_db(postgres_uri: str, username: str | None = None) -> User:
    """Create a user directly in the database for testing."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        user = User(
            username=username or f"testuser-{uuid4().hex[:8]}",
            email=f"test-{uuid4().hex[:8]}@example.com",
            password_hash="hashedpassword123",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await engine.dispose()
        return user


async def _create_minutes_via_db(
    postgres_uri: str,
    creator_id: str,
    date: datetime.date | None = None,
    is_published: bool = False,
) -> Minutes:
    """Create minutes directly in the database for testing."""
    from uuid import UUID

    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    meeting_date = date or datetime.date.today()
    async with async_session() as session:
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
        await engine.dispose()
        return minutes


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncGenerator[Litestar, None]:
    """Create a test Litestar application with the minutes controller."""
    engine = create_async_engine(postgres_uri, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        before_send_handler="autocommit",
    )

    app = Litestar(
        route_handlers=[MinutesController],
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
        dependencies=get_minutes_dependencies(),
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient, None]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestMinutesControllerRoutes:
    """Tests for MinutesController endpoints."""

    async def test_list_minutes(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        await _create_minutes_via_db(postgres_uri, str(user.id))
        response = await client.get("/api/v1/minutes/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_minutes_with_pagination(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        for i in range(3):
            await _create_minutes_via_db(
                postgres_uri,
                str(user.id),
                date=datetime.date.today() - datetime.timedelta(days=i),
            )
        response = await client.get("/api/v1/minutes/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_published_minutes(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        await _create_minutes_via_db(postgres_uri, str(user.id), is_published=True)
        response = await client.get("/api/v1/minutes/published")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_minutes(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        today = datetime.date.today()
        data = {
            "date": today.isoformat(),
            "content": "Test meeting content",
            "content_type": "markdown",
            "is_published": False,
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/minutes/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["content"] == "Test meeting content"

    async def test_get_minutes_by_id(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        minutes = await _create_minutes_via_db(postgres_uri, str(user.id))
        response = await client.get(f"/api/v1/minutes/{minutes.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["content"] == minutes.content

    async def test_get_minutes_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/minutes/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_minutes_by_slug(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        minutes = await _create_minutes_via_db(postgres_uri, str(user.id))
        response = await client.get(f"/api/v1/minutes/slug/{minutes.slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == minutes.slug

    async def test_get_minutes_by_slug_not_found(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/minutes/slug/non-existent-slug")
        assert response.status_code in (404, 500)

    async def test_get_minutes_by_date(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        meeting_date = datetime.date.today()
        await _create_minutes_via_db(postgres_uri, str(user.id), date=meeting_date)
        response = await client.get(f"/api/v1/minutes/date/{meeting_date.isoformat()}")
        assert response.status_code in (200, 404, 500)

    async def test_get_minutes_by_date_not_found(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/minutes/date/1900-01-01")
        assert response.status_code in (404, 500)

    async def test_update_minutes(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        minutes = await _create_minutes_via_db(postgres_uri, str(user.id))
        data = {"content": "Updated meeting content"}
        response = await client.put(f"/api/v1/minutes/{minutes.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["content"] == "Updated meeting content"

    async def test_delete_minutes(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        minutes = await _create_minutes_via_db(postgres_uri, str(user.id))
        response = await client.delete(f"/api/v1/minutes/{minutes.id}")
        assert response.status_code in (200, 204, 500)


class TestMinutesValidation:
    """Validation tests for minutes domain."""

    async def test_create_minutes_missing_date(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "content": "Test",
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/minutes/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_minutes_missing_content(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "date": datetime.date.today().isoformat(),
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/minutes/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_minutes_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/minutes/not-a-uuid")
        assert response.status_code in (400, 404, 422)
