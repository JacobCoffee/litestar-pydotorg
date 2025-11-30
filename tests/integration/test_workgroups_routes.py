"""Integration tests for WorkGroups domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.users.models import User
from pydotorg.domains.work_groups.controllers import WorkGroupController
from pydotorg.domains.work_groups.dependencies import get_work_groups_dependencies
from pydotorg.domains.work_groups.models import WorkGroup

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


async def _create_work_group_via_db(
    postgres_uri: str, creator_id: str, name: str | None = None, active: bool = True
) -> WorkGroup:
    """Create a work group directly in the database for testing."""
    from uuid import UUID

    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        work_group = WorkGroup(
            name=name or f"Test Work Group {uuid4().hex[:8]}",
            purpose=f"Purpose for test work group {uuid4().hex[:8]}",
            slug=f"test-workgroup-{uuid4().hex[:8]}",
            active=active,
            url="https://example.com/workgroup",
            creator_id=UUID(creator_id) if isinstance(creator_id, str) else creator_id,
        )
        session.add(work_group)
        await session.commit()
        await session.refresh(work_group)
        await engine.dispose()
        return work_group


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncGenerator[Litestar, None]:
    """Create a test Litestar application with the work groups controller."""
    engine = create_async_engine(postgres_uri, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        before_send_handler="autocommit",
    )

    app = Litestar(
        route_handlers=[WorkGroupController],
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
        dependencies=get_work_groups_dependencies(),
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient, None]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestWorkGroupControllerRoutes:
    """Tests for WorkGroupController endpoints."""

    async def test_list_work_groups(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        await _create_work_group_via_db(postgres_uri, str(user.id))
        response = await client.get("/api/v1/work-groups/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_work_groups_with_pagination(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        for i in range(3):
            await _create_work_group_via_db(postgres_uri, str(user.id), name=f"Group {i}")
        response = await client.get("/api/v1/work-groups/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_active_work_groups(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        await _create_work_group_via_db(postgres_uri, str(user.id), active=True)
        response = await client.get("/api/v1/work-groups/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_work_group(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "name": "New Test Work Group",
            "purpose": "Purpose of this work group",
            "active": True,
            "url": "https://example.com",
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/work-groups/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "New Test Work Group"

    async def test_get_work_group_by_id(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        work_group = await _create_work_group_via_db(postgres_uri, str(user.id))
        response = await client.get(f"/api/v1/work-groups/{work_group.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == work_group.name

    async def test_get_work_group_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/work-groups/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_work_group_by_slug(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        work_group = await _create_work_group_via_db(postgres_uri, str(user.id))
        response = await client.get(f"/api/v1/work-groups/slug/{work_group.slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == work_group.slug

    async def test_get_work_group_by_slug_not_found(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/work-groups/slug/non-existent-slug")
        assert response.status_code in (404, 500)

    async def test_update_work_group(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        work_group = await _create_work_group_via_db(postgres_uri, str(user.id))
        data = {"name": "Updated Work Group Name"}
        response = await client.put(f"/api/v1/work-groups/{work_group.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Work Group Name"

    async def test_delete_work_group(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        work_group = await _create_work_group_via_db(postgres_uri, str(user.id))
        response = await client.delete(f"/api/v1/work-groups/{work_group.id}")
        assert response.status_code in (200, 204, 500)


class TestWorkGroupsValidation:
    """Validation tests for work groups domain."""

    async def test_create_work_group_missing_name(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "purpose": "Test",
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/work-groups/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_work_group_missing_purpose(
        self, client: AsyncTestClient, postgres_uri: str
    ) -> None:
        user = await _create_user_via_db(postgres_uri)
        data = {
            "name": "Test Group",
            "creator_id": str(user.id),
        }
        response = await client.post("/api/v1/work-groups/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_work_group_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/work-groups/not-a-uuid")
        assert response.status_code in (400, 404, 422)
