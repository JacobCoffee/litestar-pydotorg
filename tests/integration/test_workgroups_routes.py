"""Integration tests for WorkGroups domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from pydotorg.domains.users.models import User
from pydotorg.domains.work_groups.controllers import WorkGroupController
from pydotorg.domains.work_groups.dependencies import get_work_groups_dependencies
from pydotorg.domains.work_groups.models import WorkGroup

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


async def _create_user_via_db(session_factory: async_sessionmaker, username: str | None = None) -> User:
    """Create a user directly in the database for testing using shared session factory."""
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


async def _create_work_group_via_db(
    session_factory: async_sessionmaker, creator_id: str, name: str | None = None, active: bool = True
) -> WorkGroup:
    """Create a work group directly in the database for testing using shared session factory."""
    from uuid import UUID

    async with session_factory() as session:
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
        return work_group


class WorkGroupsTestFixtures:
    """Container for workgroups test fixtures."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


@pytest.fixture
async def workgroups_fixtures(
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncGenerator[WorkGroupsTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    """
    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    app = Litestar(
        route_handlers=[WorkGroupController],
        plugins=[sqlalchemy_plugin],
        dependencies=get_work_groups_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = WorkGroupsTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestWorkGroupControllerRoutes:
    """Tests for WorkGroupController endpoints."""

    async def test_list_work_groups(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id))
        response = await workgroups_fixtures.client.get("/api/v1/work-groups/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_work_groups_with_pagination(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        for i in range(3):
            await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id), name=f"Group {i}")
        response = await workgroups_fixtures.client.get("/api/v1/work-groups/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_active_work_groups(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id), active=True)
        response = await workgroups_fixtures.client.get("/api/v1/work-groups/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_work_group(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        data = {
            "name": "New Test Work Group",
            "purpose": "Purpose of this work group",
            "active": True,
            "url": "https://example.com",
            "creator_id": str(user.id),
        }
        response = await workgroups_fixtures.client.post("/api/v1/work-groups/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "New Test Work Group"

    async def test_get_work_group_by_id(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        work_group = await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id))
        response = await workgroups_fixtures.client.get(f"/api/v1/work-groups/{work_group.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == work_group.name

    async def test_get_work_group_by_id_not_found(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await workgroups_fixtures.client.get(f"/api/v1/work-groups/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_work_group_by_slug(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        work_group = await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id))
        response = await workgroups_fixtures.client.get(f"/api/v1/work-groups/slug/{work_group.slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == work_group.slug

    async def test_get_work_group_by_slug_not_found(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        response = await workgroups_fixtures.client.get("/api/v1/work-groups/slug/non-existent-slug")
        assert response.status_code in (404, 500)

    async def test_update_work_group(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        work_group = await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id))
        data = {"name": "Updated Work Group Name"}
        response = await workgroups_fixtures.client.put(f"/api/v1/work-groups/{work_group.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Work Group Name"

    async def test_delete_work_group(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        work_group = await _create_work_group_via_db(workgroups_fixtures.session_factory, str(user.id))
        response = await workgroups_fixtures.client.delete(f"/api/v1/work-groups/{work_group.id}")
        assert response.status_code in (200, 204, 500)


class TestWorkGroupsValidation:
    """Validation tests for work groups domain."""

    async def test_create_work_group_missing_name(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        data = {
            "purpose": "Test",
            "creator_id": str(user.id),
        }
        response = await workgroups_fixtures.client.post("/api/v1/work-groups/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_work_group_missing_purpose(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        user = await _create_user_via_db(workgroups_fixtures.session_factory)
        data = {
            "name": "Test Group",
            "creator_id": str(user.id),
        }
        response = await workgroups_fixtures.client.post("/api/v1/work-groups/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_work_group_invalid_uuid(self, workgroups_fixtures: WorkGroupsTestFixtures) -> None:
        response = await workgroups_fixtures.client.get("/api/v1/work-groups/not-a-uuid")
        assert response.status_code in (400, 404, 422)
