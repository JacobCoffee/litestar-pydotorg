"""Unit tests for RSS and Atom feed services."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from pydotorg.core.feeds import AtomFeedService, RSSFeedService

if TYPE_CHECKING:
    pass


def create_mock_event(
    title: str = "Test Event",
    slug: str = "test-event",
    description: str | None = "A test event description",
    with_occurrences: bool = True,
    with_categories: bool = False,
    with_venue: bool = False,
) -> MagicMock:
    """Create a mock Event object for testing."""
    event = MagicMock()
    event.id = uuid4()
    event.title = title
    event.slug = slug
    event.description = description

    if with_occurrences:
        occurrence = MagicMock()
        occurrence.dt_start = datetime.datetime(2025, 6, 15, 10, 0, tzinfo=datetime.UTC)
        occurrence.dt_end = datetime.datetime(2025, 6, 15, 18, 0, tzinfo=datetime.UTC)
        event.occurrences = [occurrence]
    else:
        event.occurrences = []

    if with_categories:
        category = MagicMock()
        category.name = "Conference"
        category.slug = "conference"
        event.categories = [category]
    else:
        event.categories = []

    if with_venue:
        venue = MagicMock()
        venue.name = "Test Venue"
        venue.address = "123 Test St"
        event.venue = venue
    else:
        event.venue = None

    return event


class TestRSSFeedService:
    """Tests for RSSFeedService."""

    def test_init_defaults(self) -> None:
        """Test default initialization values."""
        service = RSSFeedService()
        assert service.title == "Python Events"
        assert service.link == "https://www.python.org/events/"
        assert service.description == "Upcoming Python community events"
        assert service.language == "en-us"

    def test_init_custom(self) -> None:
        """Test custom initialization values."""
        service = RSSFeedService(
            title="Custom Events",
            link="https://example.com/events/",
            description="Custom description",
            language="de-de",
        )
        assert service.title == "Custom Events"
        assert service.link == "https://example.com/events/"
        assert service.description == "Custom description"
        assert service.language == "de-de"

    def test_generate_feed_empty(self) -> None:
        """Test generating feed with no events."""
        service = RSSFeedService()
        feed = service.generate_feed(events=[])

        assert '<?xml version="1.0" encoding="UTF-8"?>' in feed
        assert '<rss version="2.0"' in feed
        assert "<channel>" in feed
        assert "<title>Python Events</title>" in feed
        assert "</channel>" in feed
        assert "</rss>" in feed

    def test_generate_feed_with_event(self) -> None:
        """Test generating feed with an event."""
        service = RSSFeedService()
        event = create_mock_event()
        feed = service.generate_feed(events=[event])

        assert "<item>" in feed
        assert "<title>Test Event</title>" in feed
        assert "<link>https://www.python.org/events/test-event/</link>" in feed
        assert "<guid" in feed
        assert "</item>" in feed

    def test_generate_feed_with_description(self) -> None:
        """Test event description is included."""
        service = RSSFeedService()
        event = create_mock_event(description="Event description text")
        feed = service.generate_feed(events=[event])

        assert "<description>Event description text</description>" in feed

    def test_generate_feed_with_categories(self) -> None:
        """Test event categories are included."""
        service = RSSFeedService()
        event = create_mock_event(with_categories=True)
        feed = service.generate_feed(events=[event])

        assert "<category>Conference</category>" in feed

    def test_generate_feed_with_pubdate(self) -> None:
        """Test pubDate from occurrence."""
        service = RSSFeedService()
        event = create_mock_event()
        feed = service.generate_feed(events=[event])

        assert "<pubDate>" in feed
        assert "2025" in feed

    def test_generate_feed_custom_base_url(self) -> None:
        """Test custom base URL."""
        service = RSSFeedService()
        event = create_mock_event()
        feed = service.generate_feed(events=[event], base_url="https://custom.example.com")

        assert "https://custom.example.com/events/test-event/" in feed

    def test_generate_feed_with_feed_url(self) -> None:
        """Test self-referencing Atom link."""
        service = RSSFeedService()
        feed = service.generate_feed(
            events=[],
            feed_url="https://www.python.org/events/rss/",
        )

        assert 'rel="self"' in feed
        assert "application/rss+xml" in feed


class TestAtomFeedService:
    """Tests for AtomFeedService."""

    def test_init_defaults(self) -> None:
        """Test default initialization values."""
        service = AtomFeedService()
        assert service.title == "Python Events"
        assert service.subtitle == "Upcoming Python community events"
        assert service.author_name == "Python Software Foundation"
        assert service.author_email == "webmaster@python.org"

    def test_init_custom(self) -> None:
        """Test custom initialization values."""
        service = AtomFeedService(
            title="Custom Events",
            subtitle="Custom subtitle",
            author_name="Test Author",
            author_email="test@example.com",
        )
        assert service.title == "Custom Events"
        assert service.subtitle == "Custom subtitle"
        assert service.author_name == "Test Author"
        assert service.author_email == "test@example.com"

    def test_generate_feed_empty(self) -> None:
        """Test generating feed with no events."""
        service = AtomFeedService()
        feed = service.generate_feed(events=[])

        assert '<?xml version="1.0" encoding="UTF-8"?>' in feed
        assert '<feed xmlns="http://www.w3.org/2005/Atom"' in feed
        assert "<title>Python Events</title>" in feed
        assert "<subtitle>Upcoming Python community events</subtitle>" in feed
        assert "</feed>" in feed

    def test_generate_feed_with_event(self) -> None:
        """Test generating feed with an event."""
        service = AtomFeedService()
        event = create_mock_event()
        feed = service.generate_feed(events=[event])

        assert "<entry>" in feed
        assert "<title>Test Event</title>" in feed
        assert 'href="https://www.python.org/events/test-event/"' in feed
        assert "<id>tag:python.org,2025:events/" in feed
        assert "</entry>" in feed

    def test_generate_feed_with_description(self) -> None:
        """Test event content is included."""
        service = AtomFeedService()
        event = create_mock_event(description="Full event description")
        feed = service.generate_feed(events=[event])

        assert "<summary" in feed
        assert "<content" in feed
        assert "Full event description" in feed

    def test_generate_feed_with_categories(self) -> None:
        """Test event categories are included."""
        service = AtomFeedService()
        event = create_mock_event(with_categories=True)
        feed = service.generate_feed(events=[event])

        assert '<category term="conference" label="Conference"' in feed

    def test_generate_feed_author(self) -> None:
        """Test author information is included."""
        service = AtomFeedService()
        feed = service.generate_feed(events=[])

        assert "<author>" in feed
        assert "<name>Python Software Foundation</name>" in feed
        assert "<email>webmaster@python.org</email>" in feed

    def test_generate_feed_custom_feed_id(self) -> None:
        """Test custom feed ID."""
        service = AtomFeedService()
        feed = service.generate_feed(
            events=[],
            feed_id="tag:custom.example.com,2025:events",
        )

        assert "<id>tag:custom.example.com,2025:events</id>" in feed

    def test_generate_feed_with_feed_url(self) -> None:
        """Test self-referencing link."""
        service = AtomFeedService()
        feed = service.generate_feed(
            events=[],
            feed_url="https://www.python.org/events/atom/",
        )

        assert 'rel="self"' in feed
        assert "application/atom+xml" in feed

    def test_generate_feed_generator(self) -> None:
        """Test generator element."""
        service = AtomFeedService()
        feed = service.generate_feed(events=[])

        assert "<generator" in feed
        assert "Python.org Litestar" in feed


class TestFeedMultipleEvents:
    """Tests for feeds with multiple events."""

    def test_rss_multiple_events(self) -> None:
        """Test RSS feed with multiple events."""
        service = RSSFeedService()
        events = [
            create_mock_event(title="Event 1", slug="event-1"),
            create_mock_event(title="Event 2", slug="event-2"),
            create_mock_event(title="Event 3", slug="event-3"),
        ]
        feed = service.generate_feed(events=events)

        assert feed.count("<item>") == 3
        assert "Event 1" in feed
        assert "Event 2" in feed
        assert "Event 3" in feed

    def test_atom_multiple_events(self) -> None:
        """Test Atom feed with multiple events."""
        service = AtomFeedService()
        events = [
            create_mock_event(title="Event A", slug="event-a"),
            create_mock_event(title="Event B", slug="event-b"),
        ]
        feed = service.generate_feed(events=events)

        assert feed.count("<entry>") == 2
        assert "Event A" in feed
        assert "Event B" in feed
