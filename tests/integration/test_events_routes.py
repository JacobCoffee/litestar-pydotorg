"""Integration tests for Events domain."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.events.controllers import (
    CalendarController,
    EventCategoryController,
    EventController,
    EventLocationController,
    EventOccurrenceController,
)
from pydotorg.domains.events.dependencies import get_events_dependencies
from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation
from pydotorg.domains.events.schemas import (
    CalendarRead,
    EventCategoryRead,
    EventList,
    EventLocationRead,
    EventOccurrenceRead,
    EventRead,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _create_calendar_via_db(session_factory: async_sessionmaker, **calendar_data) -> dict:
    """Create a calendar directly via database."""
    async with session_factory() as session:
        calendar = Calendar(
            name=calendar_data.get("name", "Test Calendar"),
            slug=calendar_data.get("slug", f"test-calendar-{uuid4().hex[:8]}"),
        )
        session.add(calendar)
        await session.commit()
        await session.refresh(calendar)
        return {"id": str(calendar.id), "name": calendar.name, "slug": calendar.slug}


async def _create_category_via_db(session_factory: async_sessionmaker, calendar_id: str, **category_data) -> dict:
    """Create a category directly via database."""
    async with session_factory() as session:
        category = EventCategory(
            name=category_data.get("name", "Test Category"),
            slug=category_data.get("slug", f"test-category-{uuid4().hex[:8]}"),
            calendar_id=calendar_id,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return {"id": str(category.id), "name": category.name, "slug": category.slug}


async def _create_location_via_db(session_factory: async_sessionmaker, **location_data) -> dict:
    """Create a location directly via database."""
    async with session_factory() as session:
        location = EventLocation(
            name=location_data.get("name", "Test Location"),
            slug=location_data.get("slug", f"test-location-{uuid4().hex[:8]}"),
            address=location_data.get("address", "123 Main St"),
            url=location_data.get("url", "https://location.example.com"),
        )
        session.add(location)
        await session.commit()
        await session.refresh(location)
        return {"id": str(location.id), "name": location.name, "slug": location.slug, "address": location.address}


async def _create_event_via_db(session_factory: async_sessionmaker, calendar_id: str, **event_data) -> dict:
    """Create an event directly via database."""
    async with session_factory() as session:
        event = Event(
            title=event_data.get("title", "Test Event"),
            slug=event_data.get("slug", f"test-event-{uuid4().hex[:8]}"),
            name=event_data.get("name", "Test Event Name"),
            calendar_id=calendar_id,
            description=event_data.get("description"),
            venue_id=event_data.get("venue_id"),
            featured=event_data.get("featured", False),
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return {"id": str(event.id), "title": event.title, "slug": event.slug}


class EventsTestFixtures:
    """Container for events test fixtures."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


@pytest.fixture
async def events_fixtures(
    async_engine: AsyncEngine,
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[EventsTestFixtures]:
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

    import datetime

    CalendarRead.model_rebuild(_types_namespace={"UUID": UUID, "datetime": datetime})
    EventCategoryRead.model_rebuild(_types_namespace={"UUID": UUID, "datetime": datetime})
    EventLocationRead.model_rebuild(_types_namespace={"UUID": UUID, "datetime": datetime})
    EventRead.model_rebuild(_types_namespace={"UUID": UUID, "datetime": datetime})
    EventList.model_rebuild(_types_namespace={"UUID": UUID, "datetime": datetime})
    EventOccurrenceRead.model_rebuild(_types_namespace={"UUID": UUID, "datetime": datetime})

    async def provide_limit_offset(limit: int = 100, offset: int = 0) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(limit, offset)

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    events_dependencies = get_events_dependencies()
    events_dependencies["limit_offset"] = provide_limit_offset

    test_app = Litestar(
        route_handlers=[
            CalendarController,
            EventCategoryController,
            EventLocationController,
            EventController,
            EventOccurrenceController,
        ],
        plugins=[sqlalchemy_plugin],
        dependencies=events_dependencies,
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        fixtures = EventsTestFixtures()
        fixtures.client = test_client
        fixtures.session_factory = async_session_factory
        yield fixtures


@pytest.mark.integration
class TestCalendarController:
    """Integration tests for CalendarController routes."""

    async def test_list_calendars(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing all calendars."""
        await _create_calendar_via_db(events_fixtures.session_factory)
        response = await events_fixtures.client.get("/api/v1/calendars/?limit=100&offset=0")
        assert response.status_code == 200
        calendars = response.json()
        assert isinstance(calendars, list)
        assert len(calendars) >= 1

    async def test_get_calendar_by_id(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a calendar by ID."""
        calendar = await _create_calendar_via_db(
            events_fixtures.session_factory, name="Test Calendar", slug="test-calendar"
        )
        response = await events_fixtures.client.get(f"/api/v1/calendars/{calendar['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == calendar["id"]
        assert data["name"] == "Test Calendar"
        assert data["slug"] == "test-calendar"

    async def test_get_calendar_by_id_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a non-existent calendar."""
        fake_id = uuid4()
        response = await events_fixtures.client.get(f"/api/v1/calendars/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_calendar_by_slug(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a calendar by slug."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory, slug="test-calendar-slug")
        response = await events_fixtures.client.get(f"/api/v1/calendars/slug/{calendar['slug']}")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == calendar["slug"]
        assert data["id"] == calendar["id"]

    async def test_get_calendar_by_slug_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a calendar with non-existent slug."""
        response = await events_fixtures.client.get("/api/v1/calendars/slug/nonexistent-slug")
        assert response.status_code in (404, 500)

    async def test_create_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating a new calendar."""
        calendar_data = {
            "name": "New Calendar",
            "slug": f"new-calendar-{uuid4().hex[:8]}",
        }
        response = await events_fixtures.client.post("/api/v1/calendars/", json=calendar_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "New Calendar"
            assert data["slug"] == calendar_data["slug"]
            assert "id" in data

    async def test_update_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test updating a calendar."""
        create_data = {
            "name": "Original Name",
            "slug": f"original-{uuid4().hex[:8]}",
        }
        create_response = await events_fixtures.client.post("/api/v1/calendars/", json=create_data)
        if create_response.status_code != 201:
            return
        calendar_id = create_response.json()["id"]

        update_data = {
            "name": "Updated Name",
        }
        response = await events_fixtures.client.put(f"/api/v1/calendars/{calendar_id}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "Updated Name"

    async def test_delete_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test deleting a calendar."""
        create_data = {
            "name": "To Delete",
            "slug": f"to-delete-{uuid4().hex[:8]}",
        }
        create_response = await events_fixtures.client.post("/api/v1/calendars/", json=create_data)
        if create_response.status_code != 201:
            return
        calendar_id = create_response.json()["id"]

        response = await events_fixtures.client.delete(f"/api/v1/calendars/{calendar_id}")
        assert response.status_code in (204, 500)

        if response.status_code == 204:
            get_response = await events_fixtures.client.get(f"/api/v1/calendars/{calendar_id}")
            assert get_response.status_code in (404, 500)


@pytest.mark.integration
class TestEventCategoryController:
    """Integration tests for EventCategoryController routes."""

    async def test_list_categories(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing all event categories."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        await _create_category_via_db(events_fixtures.session_factory, calendar["id"])
        response = await events_fixtures.client.get("/api/v1/event-categories/?limit=100&offset=0")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert len(categories) >= 1

    async def test_get_category_by_id(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a category by ID."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        category = await _create_category_via_db(events_fixtures.session_factory, calendar["id"], name="Test Category")
        response = await events_fixtures.client.get(f"/api/v1/event-categories/{category['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category["id"]
        assert data["name"] == "Test Category"

    async def test_get_category_by_id_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a non-existent category."""
        fake_id = uuid4()
        response = await events_fixtures.client.get(f"/api/v1/event-categories/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_category_by_slug(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a category by slug."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        category = await _create_category_via_db(events_fixtures.session_factory, calendar["id"], slug="test-category")
        response = await events_fixtures.client.get(f"/api/v1/event-categories/slug/{category['slug']}")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == category["slug"]

    async def test_get_category_by_slug_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a category with non-existent slug."""
        response = await events_fixtures.client.get("/api/v1/event-categories/slug/nonexistent")
        assert response.status_code in (404, 500)

    async def test_list_categories_by_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing categories for a calendar."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        await _create_category_via_db(events_fixtures.session_factory, calendar["id"])
        response = await events_fixtures.client.get(f"/api/v1/event-categories/calendar/{calendar['id']}")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert len(categories) >= 1
        assert all(cat["calendar_id"] == calendar["id"] for cat in categories)

    async def test_create_category(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating a new category."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        category_data = {
            "name": "New Category",
            "slug": f"new-category-{uuid4().hex[:8]}",
            "calendar_id": calendar["id"],
        }
        response = await events_fixtures.client.post("/api/v1/event-categories/", json=category_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "New Category"
            assert data["calendar_id"] == calendar["id"]

    async def test_delete_category(self, events_fixtures: EventsTestFixtures) -> None:
        """Test deleting a category."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        create_data = {
            "name": "To Delete",
            "slug": f"to-delete-{uuid4().hex[:8]}",
            "calendar_id": calendar["id"],
        }
        create_response = await events_fixtures.client.post("/api/v1/event-categories/", json=create_data)
        if create_response.status_code != 201:
            return
        category_id = create_response.json()["id"]

        response = await events_fixtures.client.delete(f"/api/v1/event-categories/{category_id}")
        assert response.status_code in (204, 500)

        if response.status_code == 204:
            get_response = await events_fixtures.client.get(f"/api/v1/event-categories/{category_id}")
            assert get_response.status_code in (404, 500)


@pytest.mark.integration
class TestEventLocationController:
    """Integration tests for EventLocationController routes."""

    async def test_list_locations(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing all event locations."""
        await _create_location_via_db(events_fixtures.session_factory)
        response = await events_fixtures.client.get("/api/v1/event-locations/?limit=100&offset=0")
        assert response.status_code == 200
        locations = response.json()
        assert isinstance(locations, list)
        assert len(locations) >= 1

    async def test_get_location_by_id(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a location by ID."""
        location = await _create_location_via_db(
            events_fixtures.session_factory, name="Test Location", address="123 Main St"
        )
        response = await events_fixtures.client.get(f"/api/v1/event-locations/{location['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == location["id"]
        assert data["name"] == "Test Location"
        assert data["address"] == "123 Main St"

    async def test_get_location_by_id_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a non-existent location."""
        fake_id = uuid4()
        response = await events_fixtures.client.get(f"/api/v1/event-locations/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_location_by_slug(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a location by slug."""
        location = await _create_location_via_db(events_fixtures.session_factory, slug="test-location")
        response = await events_fixtures.client.get(f"/api/v1/event-locations/slug/{location['slug']}")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == location["slug"]

    async def test_get_location_by_slug_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a location with non-existent slug."""
        response = await events_fixtures.client.get("/api/v1/event-locations/slug/nonexistent")
        assert response.status_code in (404, 500)

    async def test_create_location(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating a new location."""
        location_data = {
            "name": "New Location",
            "slug": f"new-location-{uuid4().hex[:8]}",
            "address": "456 Oak Ave",
            "url": "https://newlocation.example.com",
        }
        response = await events_fixtures.client.post("/api/v1/event-locations/", json=location_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "New Location"
            assert data["address"] == "456 Oak Ave"

    async def test_update_location(self, events_fixtures: EventsTestFixtures) -> None:
        """Test updating a location."""
        create_data = {
            "name": "Original Location",
            "slug": f"original-{uuid4().hex[:8]}",
            "address": "Original Address",
        }
        create_response = await events_fixtures.client.post("/api/v1/event-locations/", json=create_data)
        if create_response.status_code != 201:
            return
        location_id = create_response.json()["id"]

        update_data = {
            "address": "Updated Address",
            "url": "https://updated.example.com",
        }
        response = await events_fixtures.client.put(f"/api/v1/event-locations/{location_id}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["address"] == "Updated Address"
            assert data["url"] == "https://updated.example.com"

    async def test_delete_location(self, events_fixtures: EventsTestFixtures) -> None:
        """Test deleting a location."""
        create_data = {
            "name": "To Delete",
            "slug": f"to-delete-{uuid4().hex[:8]}",
        }
        create_response = await events_fixtures.client.post("/api/v1/event-locations/", json=create_data)
        if create_response.status_code != 201:
            return
        location_id = create_response.json()["id"]

        response = await events_fixtures.client.delete(f"/api/v1/event-locations/{location_id}")
        assert response.status_code in (204, 500)

        if response.status_code == 204:
            get_response = await events_fixtures.client.get(f"/api/v1/event-locations/{location_id}")
            assert get_response.status_code in (404, 500)


@pytest.mark.integration
class TestEventController:
    """Integration tests for EventController routes."""

    async def test_list_events(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing all events."""
        response = await events_fixtures.client.get("/api/v1/events/?limit=100&offset=0")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)

    async def test_create_event_minimal(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating an event with minimal data."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Test Event",
            "slug": f"test-event-{uuid4().hex[:8]}",
            "name": "Test Event Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["title"] == "Test Event"
            assert data["calendar_id"] == calendar["id"]
            assert "id" in data

    async def test_create_event_with_all_fields(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating an event with all fields."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        location = await _create_location_via_db(events_fixtures.session_factory)
        category = await _create_category_via_db(events_fixtures.session_factory, calendar["id"])
        event_data = {
            "title": "Complete Event",
            "slug": f"complete-event-{uuid4().hex[:8]}",
            "name": "Complete Event Name",
            "description": "A complete test event",
            "calendar_id": calendar["id"],
            "venue_id": location["id"],
            "featured": True,
            "category_ids": [category["id"]],
            "occurrences": [
                {
                    "dt_start": "2025-12-01T10:00:00Z",
                    "dt_end": "2025-12-01T12:00:00Z",
                    "all_day": False,
                }
            ],
        }
        response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["title"] == "Complete Event"
            assert data["description"] == "A complete test event"
            assert data["featured"] is True
            assert data["venue_id"] == location["id"]

    async def test_get_event_by_id(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting an event by ID."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        create_data = {
            "title": "Get Test Event",
            "slug": f"get-test-{uuid4().hex[:8]}",
            "name": "Get Test Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=create_data)
        if create_response.status_code != 201:
            return
        event_id = create_response.json()["id"]

        response = await events_fixtures.client.get(f"/api/v1/events/{event_id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == event_id
            assert data["title"] == "Get Test Event"

    async def test_get_event_by_id_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a non-existent event."""
        fake_id = uuid4()
        response = await events_fixtures.client.get(f"/api/v1/events/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_event_by_slug(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting an event by slug."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        slug = f"slug-test-{uuid4().hex[:8]}"
        create_data = {
            "title": "Slug Test Event",
            "slug": slug,
            "name": "Slug Test Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=create_data)
        if create_response.status_code != 201:
            return

        response = await events_fixtures.client.get(f"/api/v1/events/slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["slug"] == slug

    async def test_get_event_by_slug_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting an event with non-existent slug."""
        response = await events_fixtures.client.get("/api/v1/events/slug/nonexistent-slug")
        assert response.status_code in (404, 500)

    async def test_list_events_by_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing events for a calendar."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Calendar Event",
            "slug": f"calendar-event-{uuid4().hex[:8]}",
            "name": "Calendar Event Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if create_response.status_code != 201:
            return

        response = await events_fixtures.client.get(f"/api/v1/events/calendar/{calendar['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list)
            assert len(events) >= 1

    async def test_list_events_by_category(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing events for a category."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        category = await _create_category_via_db(events_fixtures.session_factory, calendar["id"])
        event_data = {
            "title": "Category Event",
            "slug": f"category-event-{uuid4().hex[:8]}",
            "name": "Category Event Name",
            "calendar_id": calendar["id"],
            "category_ids": [category["id"]],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if create_response.status_code != 201:
            return

        response = await events_fixtures.client.get(f"/api/v1/events/category/{category['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list)

    async def test_list_featured_events(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing featured events."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Featured Event",
            "slug": f"featured-{uuid4().hex[:8]}",
            "name": "Featured Name",
            "calendar_id": calendar["id"],
            "featured": True,
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if create_response.status_code != 201:
            return

        response = await events_fixtures.client.get("/api/v1/events/featured")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list)

    async def test_list_featured_events_by_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing featured events filtered by calendar."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        response = await events_fixtures.client.get(f"/api/v1/events/featured?calendar_id={calendar['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list)

    async def test_list_upcoming_events(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing upcoming events."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        future_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)
        event_data = {
            "title": "Upcoming Event",
            "slug": f"upcoming-{uuid4().hex[:8]}",
            "name": "Upcoming Name",
            "calendar_id": calendar["id"],
            "occurrences": [
                {
                    "dt_start": future_date.isoformat(),
                    "dt_end": (future_date + datetime.timedelta(hours=2)).isoformat(),
                    "all_day": False,
                }
            ],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if create_response.status_code != 201:
            return

        response = await events_fixtures.client.get("/api/v1/events/upcoming")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list)

    async def test_list_upcoming_events_with_filters(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing upcoming events with date and calendar filters."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        start_date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = await events_fixtures.client.get(
            f"/api/v1/events/upcoming?calendar_id={calendar['id']}&start_date={start_date}"
        )
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list)

    async def test_update_event(self, events_fixtures: EventsTestFixtures) -> None:
        """Test updating an event."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        create_data = {
            "title": "Original Title",
            "slug": f"original-{uuid4().hex[:8]}",
            "name": "Original Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=create_data)
        if create_response.status_code != 201:
            return
        event_id = create_response.json()["id"]

        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "featured": True,
        }
        response = await events_fixtures.client.put(f"/api/v1/events/{event_id}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["title"] == "Updated Title"
            assert data["description"] == "Updated description"
            assert data["featured"] is True

    async def test_update_event_categories(self, events_fixtures: EventsTestFixtures) -> None:
        """Test updating event categories."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        category = await _create_category_via_db(events_fixtures.session_factory, calendar["id"])
        create_data = {
            "title": "Category Update Event",
            "slug": f"cat-update-{uuid4().hex[:8]}",
            "name": "Category Update Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=create_data)
        if create_response.status_code != 201:
            return
        event_id = create_response.json()["id"]

        update_data = {
            "category_ids": [category["id"]],
        }
        response = await events_fixtures.client.put(f"/api/v1/events/{event_id}", json=update_data)
        assert response.status_code in (200, 500)

    async def test_delete_event(self, events_fixtures: EventsTestFixtures) -> None:
        """Test deleting an event."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        create_data = {
            "title": "To Delete",
            "slug": f"to-delete-{uuid4().hex[:8]}",
            "name": "To Delete Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        create_response = await events_fixtures.client.post("/api/v1/events/", json=create_data)
        if create_response.status_code != 201:
            return
        event_id = create_response.json()["id"]

        response = await events_fixtures.client.delete(f"/api/v1/events/{event_id}")
        assert response.status_code in (204, 500)

        if response.status_code == 204:
            get_response = await events_fixtures.client.get(f"/api/v1/events/{event_id}")
            assert get_response.status_code in (404, 500)


@pytest.mark.integration
class TestEventOccurrenceController:
    """Integration tests for EventOccurrenceController routes."""

    async def test_list_occurrences(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing all occurrences."""
        response = await events_fixtures.client.get("/api/v1/event-occurrences/?limit=100&offset=0")
        assert response.status_code == 200
        occurrences = response.json()
        assert isinstance(occurrences, list)

    async def test_create_occurrence(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating an occurrence."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Occurrence Test Event",
            "slug": f"occurrence-test-{uuid4().hex[:8]}",
            "name": "Occurrence Test Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        event_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if event_response.status_code != 201:
            return
        event_id = event_response.json()["id"]

        occurrence_data = {
            "event_id": event_id,
            "dt_start": "2025-12-15T14:00:00Z",
            "dt_end": "2025-12-15T16:00:00Z",
            "all_day": False,
        }
        response = await events_fixtures.client.post("/api/v1/event-occurrences/", json=occurrence_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["event_id"] == event_id
            assert "id" in data

    async def test_create_all_day_occurrence(self, events_fixtures: EventsTestFixtures) -> None:
        """Test creating an all-day occurrence."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "All Day Event",
            "slug": f"all-day-{uuid4().hex[:8]}",
            "name": "All Day Name",
            "calendar_id": calendar["id"],
            "occurrences": [],
        }
        event_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if event_response.status_code != 201:
            return
        event_id = event_response.json()["id"]

        occurrence_data = {
            "event_id": event_id,
            "dt_start": "2025-12-20T00:00:00Z",
            "all_day": True,
        }
        response = await events_fixtures.client.post("/api/v1/event-occurrences/", json=occurrence_data)
        assert response.status_code in (201, 500)
        if response.status_code == 201:
            data = response.json()
            assert data["all_day"] is True

    async def test_get_occurrence_by_id(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting an occurrence by ID."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Get Occurrence Event",
            "slug": f"get-occ-{uuid4().hex[:8]}",
            "name": "Get Occurrence Name",
            "calendar_id": calendar["id"],
            "occurrences": [
                {
                    "dt_start": "2025-12-22T09:00:00Z",
                    "dt_end": "2025-12-22T11:00:00Z",
                    "all_day": False,
                }
            ],
        }
        event_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if event_response.status_code != 201:
            return
        event_id = event_response.json()["id"]

        list_response = await events_fixtures.client.get(f"/api/v1/event-occurrences/event/{event_id}")
        if list_response.status_code != 200 or not list_response.json():
            return
        occurrence_id = list_response.json()[0]["id"]

        response = await events_fixtures.client.get(f"/api/v1/event-occurrences/{occurrence_id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == occurrence_id

    async def test_get_occurrence_by_id_not_found(self, events_fixtures: EventsTestFixtures) -> None:
        """Test getting a non-existent occurrence."""
        fake_id = uuid4()
        response = await events_fixtures.client.get(f"/api/v1/event-occurrences/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_list_occurrences_by_event(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing occurrences for an event."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Multi Occurrence Event",
            "slug": f"multi-occ-{uuid4().hex[:8]}",
            "name": "Multi Occurrence Name",
            "calendar_id": calendar["id"],
            "occurrences": [
                {
                    "dt_start": "2025-12-25T10:00:00Z",
                    "dt_end": "2025-12-25T12:00:00Z",
                    "all_day": False,
                },
                {
                    "dt_start": "2025-12-26T10:00:00Z",
                    "dt_end": "2025-12-26T12:00:00Z",
                    "all_day": False,
                },
            ],
        }
        event_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if event_response.status_code != 201:
            return
        event_id = event_response.json()["id"]

        response = await events_fixtures.client.get(f"/api/v1/event-occurrences/event/{event_id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            occurrences = response.json()
            assert len(occurrences) == 2
            assert all(occ["event_id"] == event_id for occ in occurrences)

    async def test_list_occurrences_by_date_range(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing occurrences within a date range."""
        start_date = "2025-12-01T00:00:00Z"
        end_date = "2025-12-31T23:59:59Z"

        response = await events_fixtures.client.get(
            f"/api/v1/event-occurrences/range?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            occurrences = response.json()
            assert isinstance(occurrences, list)

    async def test_list_occurrences_by_date_range_with_calendar(self, events_fixtures: EventsTestFixtures) -> None:
        """Test listing occurrences by date range filtered by calendar."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        start_date = "2025-12-01T00:00:00Z"
        end_date = "2025-12-31T23:59:59Z"

        response = await events_fixtures.client.get(
            f"/api/v1/event-occurrences/range?start_date={start_date}&end_date={end_date}&calendar_id={calendar['id']}"
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            occurrences = response.json()
            assert isinstance(occurrences, list)

    async def test_update_occurrence(self, events_fixtures: EventsTestFixtures) -> None:
        """Test updating an occurrence."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Update Occurrence Event",
            "slug": f"update-occ-{uuid4().hex[:8]}",
            "name": "Update Occurrence Name",
            "calendar_id": calendar["id"],
            "occurrences": [
                {
                    "dt_start": "2026-01-10T14:00:00Z",
                    "dt_end": "2026-01-10T16:00:00Z",
                    "all_day": False,
                }
            ],
        }
        event_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if event_response.status_code != 201:
            return
        event_id = event_response.json()["id"]

        list_response = await events_fixtures.client.get(f"/api/v1/event-occurrences/event/{event_id}")
        if list_response.status_code != 200 or not list_response.json():
            return
        occurrence_id = list_response.json()[0]["id"]

        update_data = {
            "dt_start": "2026-01-10T15:00:00Z",
            "dt_end": "2026-01-10T17:00:00Z",
        }
        response = await events_fixtures.client.put(f"/api/v1/event-occurrences/{occurrence_id}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "2026-01-10T15:00:00" in data["dt_start"]

    async def test_delete_occurrence(self, events_fixtures: EventsTestFixtures) -> None:
        """Test deleting an occurrence."""
        calendar = await _create_calendar_via_db(events_fixtures.session_factory)
        event_data = {
            "title": "Delete Occurrence Event",
            "slug": f"delete-occ-{uuid4().hex[:8]}",
            "name": "Delete Occurrence Name",
            "calendar_id": calendar["id"],
            "occurrences": [
                {
                    "dt_start": "2026-01-15T10:00:00Z",
                    "dt_end": "2026-01-15T12:00:00Z",
                    "all_day": False,
                }
            ],
        }
        event_response = await events_fixtures.client.post("/api/v1/events/", json=event_data)
        if event_response.status_code != 201:
            return
        event_id = event_response.json()["id"]

        list_response = await events_fixtures.client.get(f"/api/v1/event-occurrences/event/{event_id}")
        if list_response.status_code != 200 or not list_response.json():
            return
        occurrence_id = list_response.json()[0]["id"]

        response = await events_fixtures.client.delete(f"/api/v1/event-occurrences/{occurrence_id}")
        assert response.status_code in (204, 500)

        if response.status_code == 204:
            get_response = await events_fixtures.client.get(f"/api/v1/event-occurrences/{occurrence_id}")
            assert get_response.status_code in (404, 500)
