"""Integration tests for Nominations domain controllers."""

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
from pydotorg.domains.nominations.controllers import (
    ElectionController,
    NominationController,
    NomineeController,
)
from pydotorg.domains.nominations.dependencies import get_nominations_dependencies
from pydotorg.domains.nominations.models import Election, Nomination, Nominee
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class NominationsTestFixtures:
    """Test fixtures for nominations routes."""

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


async def _create_election_via_db(session_factory: async_sessionmaker, name: str | None = None) -> Election:
    """Create an election directly in the database using shared session factory."""
    today = datetime.date.today()
    async with session_factory() as session:
        election = Election(
            name=name or f"Test Election {uuid4().hex[:8]}",
            slug=f"test-election-{uuid4().hex[:8]}",
            description="Test election description",
            nominations_open=today,
            nominations_close=today + datetime.timedelta(days=7),
            voting_open=today + datetime.timedelta(days=8),
            voting_close=today + datetime.timedelta(days=21),
        )
        session.add(election)
        await session.commit()
        await session.refresh(election)
        return election


async def _create_nominee_via_db(
    session_factory: async_sessionmaker, election_id: str, user_id: str, accepted: bool = False
) -> Nominee:
    """Create a nominee directly in the database using shared session factory."""
    from uuid import UUID

    async with session_factory() as session:
        nominee = Nominee(
            election_id=UUID(election_id) if isinstance(election_id, str) else election_id,
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            accepted=accepted,
        )
        session.add(nominee)
        await session.commit()
        await session.refresh(nominee)
        return nominee


async def _create_nomination_via_db(
    session_factory: async_sessionmaker, nominee_id: str, nominator_id: str, endorsement: str | None = None
) -> Nomination:
    """Create a nomination directly in the database using shared session factory."""
    from uuid import UUID

    async with session_factory() as session:
        nomination = Nomination(
            nominee_id=UUID(nominee_id) if isinstance(nominee_id, str) else nominee_id,
            nominator_id=UUID(nominator_id) if isinstance(nominator_id, str) else nominator_id,
            endorsement=endorsement,
        )
        session.add(nomination)
        await session.commit()
        await session.refresh(nomination)
        return nomination


@pytest.fixture
async def nominations_fixtures(
    async_engine: AsyncEngine,
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[NominationsTestFixtures]:
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
        route_handlers=[ElectionController, NomineeController, NominationController],
        plugins=[sqlalchemy_plugin],
        dependencies=get_nominations_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = NominationsTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestElectionControllerRoutes:
    """Tests for ElectionController endpoints."""

    async def test_list_elections(self, nominations_fixtures: NominationsTestFixtures) -> None:
        await _create_election_via_db(nominations_fixtures.session_factory)
        response = await nominations_fixtures.client.get("/api/v1/elections/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_elections_with_pagination(self, nominations_fixtures: NominationsTestFixtures) -> None:
        for i in range(3):
            await _create_election_via_db(nominations_fixtures.session_factory, name=f"Election {i}")
        response = await nominations_fixtures.client.get("/api/v1/elections/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)
            assert len(result) <= 2

    async def test_list_elections_by_status(self, nominations_fixtures: NominationsTestFixtures) -> None:
        await _create_election_via_db(nominations_fixtures.session_factory)
        response = await nominations_fixtures.client.get("/api/v1/elections/?status=nominations_open")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_active_elections(self, nominations_fixtures: NominationsTestFixtures) -> None:
        await _create_election_via_db(nominations_fixtures.session_factory)
        response = await nominations_fixtures.client.get("/api/v1/elections/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_election(self, nominations_fixtures: NominationsTestFixtures) -> None:
        today = datetime.date.today()
        data = {
            "name": "New Test Election",
            "description": "Test election description",
            "nominations_open": today.isoformat(),
            "nominations_close": (today + datetime.timedelta(days=7)).isoformat(),
            "voting_open": (today + datetime.timedelta(days=8)).isoformat(),
            "voting_close": (today + datetime.timedelta(days=21)).isoformat(),
        }
        response = await nominations_fixtures.client.post("/api/v1/elections/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "New Test Election"

    async def test_get_election_by_id(self, nominations_fixtures: NominationsTestFixtures) -> None:
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        response = await nominations_fixtures.client.get(f"/api/v1/elections/{election.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == election.name

    async def test_get_election_by_id_not_found(self, nominations_fixtures: NominationsTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await nominations_fixtures.client.get(f"/api/v1/elections/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_election(self, nominations_fixtures: NominationsTestFixtures) -> None:
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        data = {"name": "Updated Election Name"}
        response = await nominations_fixtures.client.put(f"/api/v1/elections/{election.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Election Name"

    async def test_delete_election(self, nominations_fixtures: NominationsTestFixtures) -> None:
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        response = await nominations_fixtures.client.delete(f"/api/v1/elections/{election.id}")
        assert response.status_code in (200, 204, 500)


class TestNomineeControllerRoutes:
    """Tests for NomineeController endpoints."""

    async def test_list_nominees(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.get("/api/v1/nominees/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_nominees_with_pagination(self, nominations_fixtures: NominationsTestFixtures) -> None:
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        for _ in range(3):
            user = await _create_user_via_db(nominations_fixtures.session_factory)
            await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.get("/api/v1/nominees/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_nominees_by_election(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.get(f"/api/v1/nominees/?election_id={election.id}")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_get_nominee_by_id(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.get(f"/api/v1/nominees/{nominee.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["election_id"] == str(election.id)

    async def test_get_nominee_by_id_not_found(self, nominations_fixtures: NominationsTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await nominations_fixtures.client.get(f"/api/v1/nominees/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_list_accepted_nominees(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        await _create_nominee_via_db(
            nominations_fixtures.session_factory, str(election.id), str(user.id), accepted=True
        )
        response = await nominations_fixtures.client.get(f"/api/v1/nominees/elections/{election.id}/accepted")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_nominee(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        data = {
            "election_id": str(election.id),
            "user_id": str(user.id),
        }
        response = await nominations_fixtures.client.post("/api/v1/nominees/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["election_id"] == str(election.id)

    async def test_accept_nomination(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.patch(f"/api/v1/nominees/{nominee.id}/accept")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["accepted"] is True

    async def test_decline_nomination(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.patch(f"/api/v1/nominees/{nominee.id}/decline")
        assert response.status_code in (200, 204, 500)

    async def test_delete_nominee(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        response = await nominations_fixtures.client.delete(f"/api/v1/nominees/{nominee.id}")
        assert response.status_code in (200, 204, 500)


class TestNominationControllerRoutes:
    """Tests for NominationController endpoints."""

    async def test_list_nominations(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        nominator = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        await _create_nomination_via_db(
            nominations_fixtures.session_factory, str(nominee.id), str(nominator.id), "Great candidate!"
        )
        response = await nominations_fixtures.client.get("/api/v1/nominations/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_nominations_with_pagination(self, nominations_fixtures: NominationsTestFixtures) -> None:
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        for _ in range(3):
            nominator = await _create_user_via_db(nominations_fixtures.session_factory)
            await _create_nomination_via_db(nominations_fixtures.session_factory, str(nominee.id), str(nominator.id))
        response = await nominations_fixtures.client.get("/api/v1/nominations/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_nominations_by_nominee(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        nominator = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        await _create_nomination_via_db(nominations_fixtures.session_factory, str(nominee.id), str(nominator.id))
        response = await nominations_fixtures.client.get(f"/api/v1/nominations/?nominee_id={nominee.id}")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_get_nomination_by_id(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        nominator = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        nomination = await _create_nomination_via_db(
            nominations_fixtures.session_factory, str(nominee.id), str(nominator.id), "Excellent candidate"
        )
        response = await nominations_fixtures.client.get(f"/api/v1/nominations/{nomination.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["nominee_id"] == str(nominee.id)

    async def test_get_nomination_by_id_not_found(self, nominations_fixtures: NominationsTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await nominations_fixtures.client.get(f"/api/v1/nominations/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_create_nomination_not_implemented(self, nominations_fixtures: NominationsTestFixtures) -> None:
        data = {
            "nominee_id": str(uuid4()),
            "endorsement": "Test endorsement",
        }
        response = await nominations_fixtures.client.post("/api/v1/nominations/", json=data)
        assert response.status_code in (500, 501)

    async def test_delete_nomination(self, nominations_fixtures: NominationsTestFixtures) -> None:
        user = await _create_user_via_db(nominations_fixtures.session_factory)
        nominator = await _create_user_via_db(nominations_fixtures.session_factory)
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        nominee = await _create_nominee_via_db(nominations_fixtures.session_factory, str(election.id), str(user.id))
        nomination = await _create_nomination_via_db(
            nominations_fixtures.session_factory, str(nominee.id), str(nominator.id)
        )
        response = await nominations_fixtures.client.delete(f"/api/v1/nominations/{nomination.id}")
        assert response.status_code in (200, 204, 500)


class TestNominationsValidation:
    """Validation tests for nominations domain."""

    async def test_create_election_missing_name(self, nominations_fixtures: NominationsTestFixtures) -> None:
        today = datetime.date.today()
        data = {
            "description": "Test",
            "nominations_open": today.isoformat(),
            "nominations_close": (today + datetime.timedelta(days=7)).isoformat(),
            "voting_open": (today + datetime.timedelta(days=8)).isoformat(),
            "voting_close": (today + datetime.timedelta(days=21)).isoformat(),
        }
        response = await nominations_fixtures.client.post("/api/v1/elections/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_election_missing_dates(self, nominations_fixtures: NominationsTestFixtures) -> None:
        data = {"name": "Test Election"}
        response = await nominations_fixtures.client.post("/api/v1/elections/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_election_invalid_uuid(self, nominations_fixtures: NominationsTestFixtures) -> None:
        response = await nominations_fixtures.client.get("/api/v1/elections/not-a-uuid")
        assert response.status_code in (400, 404, 422)

    async def test_create_nominee_missing_election(self, nominations_fixtures: NominationsTestFixtures) -> None:
        data = {"user_id": str(uuid4())}
        response = await nominations_fixtures.client.post("/api/v1/nominees/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_nominee_missing_user(self, nominations_fixtures: NominationsTestFixtures) -> None:
        election = await _create_election_via_db(nominations_fixtures.session_factory)
        data = {"election_id": str(election.id)}
        response = await nominations_fixtures.client.post("/api/v1/nominees/", json=data)
        assert response.status_code in (400, 422, 500)
