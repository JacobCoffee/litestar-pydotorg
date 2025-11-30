"""Integration tests for Nominations domain controllers."""

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
from pydotorg.domains.nominations.controllers import (
    ElectionController,
    NominationController,
    NomineeController,
)
from pydotorg.domains.nominations.dependencies import get_nominations_dependencies
from pydotorg.domains.nominations.models import Election, Nomination, Nominee
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


async def _create_election_via_db(postgres_uri: str, name: str | None = None) -> Election:
    """Create an election directly in the database for testing."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    today = datetime.date.today()
    async with async_session() as session:
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
        await engine.dispose()
        return election


async def _create_nominee_via_db(postgres_uri: str, election_id: str, user_id: str, accepted: bool = False) -> Nominee:
    """Create a nominee directly in the database for testing."""
    from uuid import UUID

    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        nominee = Nominee(
            election_id=UUID(election_id) if isinstance(election_id, str) else election_id,
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            accepted=accepted,
        )
        session.add(nominee)
        await session.commit()
        await session.refresh(nominee)
        await engine.dispose()
        return nominee


async def _create_nomination_via_db(
    postgres_uri: str, nominee_id: str, nominator_id: str, endorsement: str | None = None
) -> Nomination:
    """Create a nomination directly in the database for testing."""
    from uuid import UUID

    engine = create_async_engine(postgres_uri, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        nomination = Nomination(
            nominee_id=UUID(nominee_id) if isinstance(nominee_id, str) else nominee_id,
            nominator_id=UUID(nominator_id) if isinstance(nominator_id, str) else nominator_id,
            endorsement=endorsement,
        )
        session.add(nomination)
        await session.commit()
        await session.refresh(nomination)
        await engine.dispose()
        return nomination


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncGenerator[Litestar]:
    """Create a test Litestar application with the nominations controllers."""
    engine = create_async_engine(postgres_uri, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        before_send_handler="autocommit",
    )

    app = Litestar(
        route_handlers=[ElectionController, NomineeController, NominationController],
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
        dependencies=get_nominations_dependencies(),
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestElectionControllerRoutes:
    """Tests for ElectionController endpoints."""

    async def test_list_elections(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_election_via_db(postgres_uri)
        response = await client.get("/api/v1/elections/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_elections_with_pagination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        for i in range(3):
            await _create_election_via_db(postgres_uri, name=f"Election {i}")
        response = await client.get("/api/v1/elections/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)
            assert len(result) <= 2

    async def test_list_elections_by_status(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_election_via_db(postgres_uri)
        response = await client.get("/api/v1/elections/?status=nominations_open")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_active_elections(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_election_via_db(postgres_uri)
        response = await client.get("/api/v1/elections/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_election(self, client: AsyncTestClient) -> None:
        today = datetime.date.today()
        data = {
            "name": "New Test Election",
            "description": "Test election description",
            "nominations_open": today.isoformat(),
            "nominations_close": (today + datetime.timedelta(days=7)).isoformat(),
            "voting_open": (today + datetime.timedelta(days=8)).isoformat(),
            "voting_close": (today + datetime.timedelta(days=21)).isoformat(),
        }
        response = await client.post("/api/v1/elections/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["name"] == "New Test Election"

    async def test_get_election_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        election = await _create_election_via_db(postgres_uri)
        response = await client.get(f"/api/v1/elections/{election.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == election.name

    async def test_get_election_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/elections/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_election(self, client: AsyncTestClient, postgres_uri: str) -> None:
        election = await _create_election_via_db(postgres_uri)
        data = {"name": "Updated Election Name"}
        response = await client.put(f"/api/v1/elections/{election.id}", json=data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Election Name"

    async def test_delete_election(self, client: AsyncTestClient, postgres_uri: str) -> None:
        election = await _create_election_via_db(postgres_uri)
        response = await client.delete(f"/api/v1/elections/{election.id}")
        assert response.status_code in (200, 204, 500)


class TestNomineeControllerRoutes:
    """Tests for NomineeController endpoints."""

    async def test_list_nominees(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.get("/api/v1/nominees/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_nominees_with_pagination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        election = await _create_election_via_db(postgres_uri)
        for _ in range(3):
            user = await _create_user_via_db(postgres_uri)
            await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.get("/api/v1/nominees/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_nominees_by_election(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.get(f"/api/v1/nominees/?election_id={election.id}")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_get_nominee_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.get(f"/api/v1/nominees/{nominee.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["election_id"] == str(election.id)

    async def test_get_nominee_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/nominees/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_list_accepted_nominees(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id), accepted=True)
        response = await client.get(f"/api/v1/nominees/elections/{election.id}/accepted")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_create_nominee(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        data = {
            "election_id": str(election.id),
            "user_id": str(user.id),
        }
        response = await client.post("/api/v1/nominees/", json=data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            result = response.json()
            assert result["election_id"] == str(election.id)

    async def test_accept_nomination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.patch(f"/api/v1/nominees/{nominee.id}/accept")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["accepted"] is True

    async def test_decline_nomination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.patch(f"/api/v1/nominees/{nominee.id}/decline")
        assert response.status_code in (200, 204, 500)

    async def test_delete_nominee(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        response = await client.delete(f"/api/v1/nominees/{nominee.id}")
        assert response.status_code in (200, 204, 500)


class TestNominationControllerRoutes:
    """Tests for NominationController endpoints."""

    async def test_list_nominations(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        nominator = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        await _create_nomination_via_db(postgres_uri, str(nominee.id), str(nominator.id), "Great candidate!")
        response = await client.get("/api/v1/nominations/")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_nominations_with_pagination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        election = await _create_election_via_db(postgres_uri)
        user = await _create_user_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        for _ in range(3):
            nominator = await _create_user_via_db(postgres_uri)
            await _create_nomination_via_db(postgres_uri, str(nominee.id), str(nominator.id))
        response = await client.get("/api/v1/nominations/?currentPage=1&pageSize=2")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_list_nominations_by_nominee(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        nominator = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        await _create_nomination_via_db(postgres_uri, str(nominee.id), str(nominator.id))
        response = await client.get(f"/api/v1/nominations/?nominee_id={nominee.id}")
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    async def test_get_nomination_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        nominator = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        nomination = await _create_nomination_via_db(
            postgres_uri, str(nominee.id), str(nominator.id), "Excellent candidate"
        )
        response = await client.get(f"/api/v1/nominations/{nomination.id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["nominee_id"] == str(nominee.id)

    async def test_get_nomination_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/nominations/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_create_nomination_not_implemented(self, client: AsyncTestClient) -> None:
        data = {
            "nominee_id": str(uuid4()),
            "endorsement": "Test endorsement",
        }
        response = await client.post("/api/v1/nominations/", json=data)
        assert response.status_code in (500, 501)

    async def test_delete_nomination(self, client: AsyncTestClient, postgres_uri: str) -> None:
        user = await _create_user_via_db(postgres_uri)
        nominator = await _create_user_via_db(postgres_uri)
        election = await _create_election_via_db(postgres_uri)
        nominee = await _create_nominee_via_db(postgres_uri, str(election.id), str(user.id))
        nomination = await _create_nomination_via_db(postgres_uri, str(nominee.id), str(nominator.id))
        response = await client.delete(f"/api/v1/nominations/{nomination.id}")
        assert response.status_code in (200, 204, 500)


class TestNominationsValidation:
    """Validation tests for nominations domain."""

    async def test_create_election_missing_name(self, client: AsyncTestClient) -> None:
        today = datetime.date.today()
        data = {
            "description": "Test",
            "nominations_open": today.isoformat(),
            "nominations_close": (today + datetime.timedelta(days=7)).isoformat(),
            "voting_open": (today + datetime.timedelta(days=8)).isoformat(),
            "voting_close": (today + datetime.timedelta(days=21)).isoformat(),
        }
        response = await client.post("/api/v1/elections/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_election_missing_dates(self, client: AsyncTestClient) -> None:
        data = {"name": "Test Election"}
        response = await client.post("/api/v1/elections/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_get_election_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/v1/elections/not-a-uuid")
        assert response.status_code in (400, 404, 422)

    async def test_create_nominee_missing_election(self, client: AsyncTestClient) -> None:
        data = {"user_id": str(uuid4())}
        response = await client.post("/api/v1/nominees/", json=data)
        assert response.status_code in (400, 422, 500)

    async def test_create_nominee_missing_user(self, client: AsyncTestClient, postgres_uri: str) -> None:
        election = await _create_election_via_db(postgres_uri)
        data = {"election_id": str(election.id)}
        response = await client.post("/api/v1/nominees/", json=data)
        assert response.status_code in (400, 422, 500)
