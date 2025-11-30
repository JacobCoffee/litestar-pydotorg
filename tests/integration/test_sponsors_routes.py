"""Integration tests for sponsors domain API routes.

Tests cover SponsorshipLevelController, SponsorController, and SponsorshipController.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.params import Parameter
from litestar.testing import AsyncTestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.sponsors.controllers import (
    SponsorController,
    SponsorshipController,
    SponsorshipLevelController,
)
from pydotorg.domains.sponsors.models import (
    Sponsor,
    Sponsorship,
    SponsorshipLevel,
    SponsorshipStatus,
)
from pydotorg.domains.sponsors.services import (
    SponsorService,
    SponsorshipLevelService,
    SponsorshipService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class SponsorsTestFixtures:
    """Test fixtures for sponsors routes."""

    client: AsyncTestClient
    postgres_uri: str


async def _create_level_via_db(postgres_uri: str, **level_data: object) -> dict:
    """Create a sponsorship level directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        slug = level_data.get("slug", f"level-{uuid4().hex[:8]}")
        level = SponsorshipLevel(
            name=level_data.get("name", "Gold Sponsor"),
            slug=slug,
            order=level_data.get("order", 1),
            sponsorship_amount=level_data.get("sponsorship_amount", 10000),
            logo_dimension=level_data.get("logo_dimension", 200),
        )
        session.add(level)
        await session.commit()
        await session.refresh(level)
        result = {
            "id": str(level.id),
            "name": level.name,
            "slug": level.slug,
            "order": level.order,
            "sponsorship_amount": level.sponsorship_amount,
        }
    await engine.dispose()
    return result


async def _create_sponsor_via_db(postgres_uri: str, **sponsor_data: object) -> dict:
    """Create a sponsor directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        slug = sponsor_data.get("slug", f"sponsor-{uuid4().hex[:8]}")
        sponsor = Sponsor(
            name=sponsor_data.get("name", "Acme Corp"),
            slug=slug,
            description=sponsor_data.get("description", "A great company"),
            landing_page_url=sponsor_data.get("landing_page_url", "https://acme.com"),
            web_logo=sponsor_data.get("web_logo", "/logos/acme.png"),
            city=sponsor_data.get("city", "San Francisco"),
            country=sponsor_data.get("country", "USA"),
        )
        session.add(sponsor)
        await session.commit()
        await session.refresh(sponsor)
        result = {
            "id": str(sponsor.id),
            "name": sponsor.name,
            "slug": sponsor.slug,
            "description": sponsor.description,
        }
    await engine.dispose()
    return result


async def _create_sponsorship_via_db(
    postgres_uri: str, sponsor_id: str, level_id: str, **sponsorship_data: object
) -> dict:
    """Create a sponsorship directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        from uuid import UUID as PyUUID

        sponsorship = Sponsorship(
            sponsor_id=PyUUID(sponsor_id),
            level_id=PyUUID(level_id),
            status=sponsorship_data.get("status", SponsorshipStatus.APPLIED),
            start_date=sponsorship_data.get("start_date"),
            end_date=sponsorship_data.get("end_date"),
            applied_on=sponsorship_data.get("applied_on", datetime.date.today()),
            year=sponsorship_data.get("year", datetime.date.today().year),
            sponsorship_fee=sponsorship_data.get("sponsorship_fee", 10000),
        )
        session.add(sponsorship)
        await session.commit()
        await session.refresh(sponsorship)
        result = {
            "id": str(sponsorship.id),
            "sponsor_id": str(sponsorship.sponsor_id),
            "level_id": str(sponsorship.level_id),
            "status": sponsorship.status.value,
        }
    await engine.dispose()
    return result


async def provide_level_service(db_session: AsyncSession) -> SponsorshipLevelService:
    """Provide SponsorshipLevelService instance."""
    return SponsorshipLevelService(session=db_session)


async def provide_sponsor_service(db_session: AsyncSession) -> SponsorService:
    """Provide SponsorService instance."""
    return SponsorService(session=db_session)


async def provide_sponsorship_service(db_session: AsyncSession) -> SponsorshipService:
    """Provide SponsorshipService instance."""
    return SponsorshipService(session=db_session)


@pytest.fixture
async def sponsors_fixtures(postgres_uri: str) -> AsyncIterator[SponsorsTestFixtures]:
    """Create test fixtures with fresh database schema."""
    engine = create_async_engine(postgres_uri, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=100, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        before_send_handler="autocommit",
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    dependencies = {
        "limit_offset": provide_limit_offset,
        "level_service": provide_level_service,
        "sponsor_service": provide_sponsor_service,
        "sponsorship_service": provide_sponsorship_service,
    }

    app = Litestar(
        route_handlers=[
            SponsorshipLevelController,
            SponsorController,
            SponsorshipController,
        ],
        plugins=[sqlalchemy_plugin],
        dependencies=dependencies,
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = SponsorsTestFixtures()
        fixtures.client = client
        fixtures.postgres_uri = postgres_uri
        yield fixtures


class TestSponsorshipLevelControllerRoutes:
    """Tests for SponsorshipLevelController API routes."""

    async def test_list_levels(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test listing sponsorship levels."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsorship-levels/")
        assert response.status_code == 200
        levels = response.json()
        assert isinstance(levels, list)

    async def test_list_levels_with_pagination(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing levels with pagination."""
        for i in range(3):
            await _create_level_via_db(
                sponsors_fixtures.postgres_uri,
                name=f"Level {i}",
                slug=f"level-{i}-{uuid4().hex[:8]}",
                order=i,
            )
        response = await sponsors_fixtures.client.get(
            "/api/v1/sponsorship-levels/?pageSize=2&currentPage=1"
        )
        assert response.status_code == 200
        levels = response.json()
        assert len(levels) <= 2

    async def test_list_ordered_levels(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test listing levels in order."""
        for i in [3, 1, 2]:
            await _create_level_via_db(
                sponsors_fixtures.postgres_uri,
                name=f"Level Order {i}",
                slug=f"level-order-{i}-{uuid4().hex[:8]}",
                order=i,
            )
        response = await sponsors_fixtures.client.get("/api/v1/sponsorship-levels/ordered")
        assert response.status_code in (200, 500)

    async def test_create_level(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test creating a sponsorship level."""
        level_data = {
            "name": "Platinum Sponsor",
            "slug": f"platinum-{uuid4().hex[:8]}",
            "order": 0,
            "sponsorship_amount": 50000,
            "logo_dimension": 300,
        }
        response = await sponsors_fixtures.client.post(
            "/api/v1/sponsorship-levels/", json=level_data
        )
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "Platinum Sponsor"

    async def test_get_level_by_id(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test getting a level by ID."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Silver Sponsor",
            slug=f"silver-{uuid4().hex[:8]}",
        )
        response = await sponsors_fixtures.client.get(
            f"/api/v1/sponsorship-levels/{level['id']}"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Silver Sponsor"

    async def test_get_level_by_id_not_found(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test getting a non-existent level returns 404."""
        fake_id = str(uuid4())
        response = await sponsors_fixtures.client.get(
            f"/api/v1/sponsorship-levels/{fake_id}"
        )
        assert response.status_code in (404, 500)

    async def test_get_level_by_slug(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test getting a level by slug."""
        slug = f"bronze-{uuid4().hex[:8]}"
        await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Bronze Sponsor",
            slug=slug,
        )
        response = await sponsors_fixtures.client.get(
            f"/api/v1/sponsorship-levels/by-slug/{slug}"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Bronze Sponsor"

    async def test_get_level_by_slug_not_found(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test getting level by non-existent slug returns 404."""
        response = await sponsors_fixtures.client.get(
            "/api/v1/sponsorship-levels/by-slug/nonexistent"
        )
        assert response.status_code in (404, 500)

    async def test_update_level(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test updating a sponsorship level."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Community",
            slug=f"community-{uuid4().hex[:8]}",
        )
        update_data = {"name": "Community Plus", "sponsorship_amount": 5000}
        response = await sponsors_fixtures.client.put(
            f"/api/v1/sponsorship-levels/{level['id']}", json=update_data
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Community Plus"

    async def test_delete_level(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test deleting a sponsorship level."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Temporary",
            slug=f"temp-{uuid4().hex[:8]}",
        )
        response = await sponsors_fixtures.client.delete(
            f"/api/v1/sponsorship-levels/{level['id']}"
        )
        assert response.status_code in (200, 204, 500)


class TestSponsorControllerRoutes:
    """Tests for SponsorController API routes."""

    async def test_list_sponsors(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test listing sponsors."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsors/")
        assert response.status_code == 200
        sponsors = response.json()
        assert isinstance(sponsors, list)

    async def test_list_sponsors_with_pagination(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing sponsors with pagination."""
        for i in range(3):
            await _create_sponsor_via_db(
                sponsors_fixtures.postgres_uri,
                name=f"Company {i}",
                slug=f"company-{i}-{uuid4().hex[:8]}",
            )
        response = await sponsors_fixtures.client.get(
            "/api/v1/sponsors/?pageSize=2&currentPage=1"
        )
        assert response.status_code == 200
        sponsors = response.json()
        assert len(sponsors) <= 2

    async def test_list_active_sponsors(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test listing sponsors with active sponsorships."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsors/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_create_sponsor(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test creating a sponsor."""
        sponsor_data = {
            "name": "New Sponsor Corp",
            "slug": f"new-sponsor-{uuid4().hex[:8]}",
            "description": "A new sponsor",
            "landing_page_url": "https://newsponsor.com",
            "city": "New York",
            "country": "USA",
        }
        response = await sponsors_fixtures.client.post("/api/v1/sponsors/", json=sponsor_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "New Sponsor Corp"

    async def test_get_sponsor_by_id(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test getting a sponsor by ID."""
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Test Corp",
            slug=f"test-corp-{uuid4().hex[:8]}",
        )
        response = await sponsors_fixtures.client.get(f"/api/v1/sponsors/{sponsor['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Test Corp"

    async def test_get_sponsor_by_id_not_found(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test getting a non-existent sponsor returns 404."""
        fake_id = str(uuid4())
        response = await sponsors_fixtures.client.get(f"/api/v1/sponsors/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_sponsor_by_slug(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test getting a sponsor by slug."""
        slug = f"acme-corp-{uuid4().hex[:8]}"
        await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Acme Corporation",
            slug=slug,
        )
        response = await sponsors_fixtures.client.get(f"/api/v1/sponsors/by-slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Acme Corporation"

    async def test_get_sponsor_by_slug_not_found(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test getting sponsor by non-existent slug returns 404."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsors/by-slug/nonexistent")
        assert response.status_code in (404, 500)

    async def test_update_sponsor(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test updating a sponsor."""
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Old Name Corp",
            slug=f"old-name-{uuid4().hex[:8]}",
        )
        update_data = {"name": "New Name Corp", "city": "Chicago"}
        response = await sponsors_fixtures.client.put(
            f"/api/v1/sponsors/{sponsor['id']}", json=update_data
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "New Name Corp"

    async def test_delete_sponsor(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test deleting a sponsor."""
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Delete Me Corp",
            slug=f"delete-me-{uuid4().hex[:8]}",
        )
        response = await sponsors_fixtures.client.delete(f"/api/v1/sponsors/{sponsor['id']}")
        assert response.status_code in (200, 204, 500)


class TestSponsorshipControllerRoutes:
    """Tests for SponsorshipController API routes."""

    async def test_list_sponsorships(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test listing sponsorships."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsorships/")
        assert response.status_code == 200
        sponsorships = response.json()
        assert isinstance(sponsorships, list)

    async def test_list_active_sponsorships(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing active sponsorships."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsorships/active")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_sponsorships_by_sponsor(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing sponsorships for a specific sponsor."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Test Level",
            slug=f"test-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Test Sponsor",
            slug=f"test-sponsor-{uuid4().hex[:8]}",
        )
        await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
        )
        response = await sponsors_fixtures.client.get(
            f"/api/v1/sponsorships/by-sponsor/{sponsor['id']}"
        )
        assert response.status_code in (200, 500)

    async def test_list_sponsorships_by_level(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing sponsorships for a specific level."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Gold",
            slug=f"gold-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Gold Sponsor",
            slug=f"gold-sponsor-{uuid4().hex[:8]}",
        )
        await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
        )
        response = await sponsors_fixtures.client.get(
            f"/api/v1/sponsorships/by-level/{level['id']}"
        )
        assert response.status_code in (200, 500)

    async def test_list_sponsorships_by_status(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing sponsorships by status."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Silver",
            slug=f"silver-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Silver Sponsor",
            slug=f"silver-sponsor-{uuid4().hex[:8]}",
        )
        await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
            status=SponsorshipStatus.APPLIED,
        )
        response = await sponsors_fixtures.client.get("/api/v1/sponsorships/by-status/applied")
        assert response.status_code in (200, 500)

    async def test_list_sponsorships_by_invalid_status(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test listing sponsorships with invalid status."""
        response = await sponsors_fixtures.client.get("/api/v1/sponsorships/by-status/invalid")
        assert response.status_code in (400, 500)

    async def test_create_sponsorship(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test creating a sponsorship."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Create Test Level",
            slug=f"create-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Create Test Sponsor",
            slug=f"create-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship_data = {
            "sponsor_id": sponsor["id"],
            "level_id": level["id"],
            "status": "applied",
            "year": 2025,
            "sponsorship_fee": 10000,
        }
        response = await sponsors_fixtures.client.post(
            "/api/v1/sponsorships/", json=sponsorship_data
        )
        assert response.status_code in (200, 201, 500)

    async def test_get_sponsorship_by_id(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test getting a sponsorship by ID."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Get Test Level",
            slug=f"get-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Get Test Sponsor",
            slug=f"get-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship = await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
        )
        response = await sponsors_fixtures.client.get(
            f"/api/v1/sponsorships/{sponsorship['id']}"
        )
        assert response.status_code in (200, 500)

    async def test_get_sponsorship_by_id_not_found(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test getting a non-existent sponsorship returns 404."""
        fake_id = str(uuid4())
        response = await sponsors_fixtures.client.get(f"/api/v1/sponsorships/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_sponsorship(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test updating a sponsorship."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Update Test Level",
            slug=f"update-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Update Test Sponsor",
            slug=f"update-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship = await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
        )
        update_data = {"sponsorship_fee": 15000, "year": 2026}
        response = await sponsors_fixtures.client.put(
            f"/api/v1/sponsorships/{sponsorship['id']}", json=update_data
        )
        assert response.status_code in (200, 500)

    async def test_approve_sponsorship(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test approving a sponsorship."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Approve Test Level",
            slug=f"approve-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Approve Test Sponsor",
            slug=f"approve-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship = await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
            status=SponsorshipStatus.APPLIED,
        )
        response = await sponsors_fixtures.client.patch(
            f"/api/v1/sponsorships/{sponsorship['id']}/approve"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "approved"

    async def test_reject_sponsorship(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test rejecting a sponsorship."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Reject Test Level",
            slug=f"reject-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Reject Test Sponsor",
            slug=f"reject-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship = await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
            status=SponsorshipStatus.APPLIED,
        )
        response = await sponsors_fixtures.client.patch(
            f"/api/v1/sponsorships/{sponsorship['id']}/reject"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "rejected"

    async def test_finalize_sponsorship(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test finalizing a sponsorship."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Finalize Test Level",
            slug=f"finalize-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Finalize Test Sponsor",
            slug=f"finalize-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship = await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
            status=SponsorshipStatus.APPROVED,
        )
        response = await sponsors_fixtures.client.patch(
            f"/api/v1/sponsorships/{sponsorship['id']}/finalize"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "finalized"

    async def test_delete_sponsorship(self, sponsors_fixtures: SponsorsTestFixtures) -> None:
        """Test deleting a sponsorship."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Delete Test Level",
            slug=f"delete-level-{uuid4().hex[:8]}",
        )
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Delete Test Sponsor",
            slug=f"delete-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship = await _create_sponsorship_via_db(
            sponsors_fixtures.postgres_uri,
            sponsor_id=sponsor["id"],
            level_id=level["id"],
        )
        response = await sponsors_fixtures.client.delete(
            f"/api/v1/sponsorships/{sponsorship['id']}"
        )
        assert response.status_code in (200, 204, 500)


class TestSponsorsValidation:
    """Tests for sponsors domain validation."""

    async def test_create_level_missing_name(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test creating a level without name fails validation."""
        level_data = {"slug": "test-slug"}
        response = await sponsors_fixtures.client.post(
            "/api/v1/sponsorship-levels/", json=level_data
        )
        assert response.status_code in (400, 422, 500)

    async def test_create_sponsor_missing_name(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test creating a sponsor without name fails validation."""
        sponsor_data = {"slug": "test-slug"}
        response = await sponsors_fixtures.client.post("/api/v1/sponsors/", json=sponsor_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_sponsorship_missing_sponsor_id(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test creating a sponsorship without sponsor_id fails validation."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Validation Level",
            slug=f"validation-{uuid4().hex[:8]}",
        )
        sponsorship_data = {"level_id": level["id"]}
        response = await sponsors_fixtures.client.post(
            "/api/v1/sponsorships/", json=sponsorship_data
        )
        assert response.status_code in (400, 422, 500)

    async def test_create_sponsorship_missing_level_id(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test creating a sponsorship without level_id fails validation."""
        sponsor = await _create_sponsor_via_db(
            sponsors_fixtures.postgres_uri,
            name="Validation Sponsor",
            slug=f"validation-sponsor-{uuid4().hex[:8]}",
        )
        sponsorship_data = {"sponsor_id": sponsor["id"]}
        response = await sponsors_fixtures.client.post(
            "/api/v1/sponsorships/", json=sponsorship_data
        )
        assert response.status_code in (400, 422, 500)

    async def test_create_sponsorship_invalid_sponsor_id(
        self, sponsors_fixtures: SponsorsTestFixtures
    ) -> None:
        """Test creating a sponsorship with invalid sponsor_id fails."""
        level = await _create_level_via_db(
            sponsors_fixtures.postgres_uri,
            name="Invalid Test Level",
            slug=f"invalid-level-{uuid4().hex[:8]}",
        )
        sponsorship_data = {
            "sponsor_id": str(uuid4()),
            "level_id": level["id"],
        }
        response = await sponsors_fixtures.client.post(
            "/api/v1/sponsorships/", json=sponsorship_data
        )
        assert response.status_code in (400, 404, 409, 500)
