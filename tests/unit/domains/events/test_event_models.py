"""Unit tests for Event models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence


class TestCalendarModel:
    def test_create_calendar(self) -> None:
        calendar = Calendar(name="Python Events", slug="python-events")
        assert calendar.name == "Python Events"
        assert calendar.slug == "python-events"


class TestEventCategoryModel:
    def test_create_event_category(self) -> None:
        calendar_id = uuid4()
        category = EventCategory(
            name="Conference",
            slug="conference",
            calendar_id=calendar_id,
        )
        assert category.name == "Conference"
        assert category.slug == "conference"
        assert category.calendar_id == calendar_id


class TestEventLocationModel:
    def test_create_event_location(self) -> None:
        location = EventLocation(
            name="Convention Center",
            slug="convention-center",
        )
        assert location.name == "Convention Center"
        assert location.slug == "convention-center"

    def test_event_location_with_address(self) -> None:
        location = EventLocation(
            name="Convention Center",
            slug="convention-center",
            address="123 Main St, City, ST 12345",
        )
        assert location.address == "123 Main St, City, ST 12345"

    def test_event_location_with_url(self) -> None:
        location = EventLocation(
            name="Convention Center",
            slug="convention-center",
            url="https://conventioncenter.com",
        )
        assert location.url == "https://conventioncenter.com"

    def test_event_location_with_all_fields(self) -> None:
        location = EventLocation(
            name="Tech Hub",
            slug="tech-hub",
            address="456 Tech Blvd, Tech City, TC 67890",
            url="https://techhub.com",
        )
        assert location.name == "Tech Hub"
        assert location.address == "456 Tech Blvd, Tech City, TC 67890"
        assert location.url == "https://techhub.com"


class TestEventModel:
    def test_create_event(self) -> None:
        calendar_id = uuid4()
        event = Event(
            title="PyCon 2024",
            slug="pycon-2024",
            calendar_id=calendar_id,
        )
        assert event.title == "PyCon 2024"
        assert event.slug == "pycon-2024"
        assert event.calendar_id == calendar_id

    def test_event_with_explicit_defaults(self) -> None:
        event = Event(
            title="Test Event",
            slug="test-event",
            calendar_id=uuid4(),
            featured=False,
        )
        assert event.description is None
        assert event.venue_id is None
        assert event.featured is False

    def test_event_with_description(self) -> None:
        event = Event(
            title="PyCon 2024",
            slug="pycon-2024",
            calendar_id=uuid4(),
            description="The largest annual gathering for the Python community",
        )
        assert event.description == "The largest annual gathering for the Python community"

    def test_event_with_venue(self) -> None:
        calendar_id = uuid4()
        venue_id = uuid4()
        event = Event(
            title="Local Meetup",
            slug="local-meetup",
            calendar_id=calendar_id,
            venue_id=venue_id,
        )
        assert event.venue_id == venue_id

    def test_event_featured(self) -> None:
        event = Event(
            title="Featured Event",
            slug="featured-event",
            calendar_id=uuid4(),
            featured=True,
        )
        assert event.featured is True

    def test_event_with_all_fields(self) -> None:
        calendar_id = uuid4()
        venue_id = uuid4()
        event = Event(
            title="Django Workshop",
            slug="django-workshop",
            description="Learn Django from scratch",
            calendar_id=calendar_id,
            venue_id=venue_id,
            featured=True,
        )
        assert event.title == "Django Workshop"
        assert event.description == "Learn Django from scratch"
        assert event.calendar_id == calendar_id
        assert event.venue_id == venue_id
        assert event.featured is True


class TestEventOccurrenceModel:
    def test_create_event_occurrence(self) -> None:
        event_id = uuid4()
        start_time = datetime(2024, 6, 1, 9, 0, tzinfo=UTC)
        occurrence = EventOccurrence(
            event_id=event_id,
            dt_start=start_time,
        )
        assert occurrence.event_id == event_id
        assert occurrence.dt_start == start_time

    def test_event_occurrence_with_explicit_defaults(self) -> None:
        occurrence = EventOccurrence(
            event_id=uuid4(),
            dt_start=datetime(2024, 6, 1, 9, 0, tzinfo=UTC),
            all_day=False,
        )
        assert occurrence.dt_end is None
        assert occurrence.all_day is False

    def test_event_occurrence_with_end_time(self) -> None:
        start_time = datetime(2024, 6, 1, 9, 0, tzinfo=UTC)
        end_time = datetime(2024, 6, 1, 17, 0, tzinfo=UTC)
        occurrence = EventOccurrence(
            event_id=uuid4(),
            dt_start=start_time,
            dt_end=end_time,
        )
        assert occurrence.dt_start == start_time
        assert occurrence.dt_end == end_time

    def test_event_occurrence_all_day(self) -> None:
        occurrence = EventOccurrence(
            event_id=uuid4(),
            dt_start=datetime(2024, 6, 1, 0, 0, tzinfo=UTC),
            all_day=True,
        )
        assert occurrence.all_day is True

    def test_event_occurrence_multi_day(self) -> None:
        start_time = datetime(2024, 6, 1, 9, 0, tzinfo=UTC)
        end_time = datetime(2024, 6, 3, 17, 0, tzinfo=UTC)
        occurrence = EventOccurrence(
            event_id=uuid4(),
            dt_start=start_time,
            dt_end=end_time,
        )
        assert occurrence.dt_start == start_time
        assert occurrence.dt_end == end_time
        duration = occurrence.dt_end - occurrence.dt_start
        assert duration.days == 2
