"""Unit tests for EventAdminService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.events import EventAdminService
from pydotorg.domains.events.models import Calendar, Event


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_event() -> Mock:
    """Create a mock event."""
    event = Mock(spec=Event)
    event.id = uuid4()
    event.title = "Test Event"
    event.name = "test-event"
    event.description = "A test event description"
    event.calendar_id = uuid4()
    event.venue_id = uuid4()
    event.featured = False
    event.calendar = Mock()
    event.venue = Mock()
    event.categories = []
    event.occurrences = []
    event.created_at = datetime.now(tz=UTC)
    return event


@pytest.fixture
def mock_calendar() -> Mock:
    """Create a mock calendar."""
    calendar = Mock(spec=Calendar)
    calendar.id = uuid4()
    calendar.name = "Test Calendar"
    calendar.slug = "test-calendar"
    calendar.events = []
    calendar.created_at = datetime.now(tz=UTC)
    return calendar


@pytest.fixture
def service(mock_session: AsyncMock) -> EventAdminService:
    """Create an EventAdminService instance with mock session."""
    return EventAdminService(session=mock_session)


class TestListEvents:
    """Tests for EventAdminService.list_events."""

    async def test_list_events_returns_events_and_count(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test that list_events returns events and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = [mock_event]

        mock_session.execute.side_effect = [mock_count_result, mock_events_result]

        events, total = await service.list_events()

        assert total == 1
        assert len(events) == 1
        assert events[0] == mock_event

    async def test_list_events_with_calendar_id_filter(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test list_events with calendar_id filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = [mock_event]

        mock_session.execute.side_effect = [mock_count_result, mock_events_result]

        calendar_id = uuid4()
        _events, total = await service.list_events(calendar_id=calendar_id)

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_events_with_featured_filter(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test list_events with featured filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = [mock_event]

        mock_session.execute.side_effect = [mock_count_result, mock_events_result]

        _events, total = await service.list_events(featured=True)

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_events_with_search(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test list_events with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = [mock_event]

        mock_session.execute.side_effect = [mock_count_result, mock_events_result]

        _events, total = await service.list_events(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_events_with_pagination(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test list_events with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = [mock_event]

        mock_session.execute.side_effect = [mock_count_result, mock_events_result]

        events, total = await service.list_events(limit=10, offset=20)

        assert total == 100
        assert len(events) == 1

    async def test_list_events_empty_result(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_events with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_events_result]

        events, total = await service.list_events()

        assert total == 0
        assert len(events) == 0


class TestListCalendars:
    """Tests for EventAdminService.list_calendars."""

    async def test_list_calendars_returns_calendars_and_count(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_calendar: Mock,
    ) -> None:
        """Test that list_calendars returns calendars and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_calendars_result = MagicMock()
        mock_calendars_result.scalars.return_value.all.return_value = [mock_calendar]

        mock_session.execute.side_effect = [mock_count_result, mock_calendars_result]

        calendars, total = await service.list_calendars()

        assert total == 1
        assert len(calendars) == 1
        assert calendars[0] == mock_calendar

    async def test_list_calendars_with_search(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_calendar: Mock,
    ) -> None:
        """Test list_calendars with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_calendars_result = MagicMock()
        mock_calendars_result.scalars.return_value.all.return_value = [mock_calendar]

        mock_session.execute.side_effect = [mock_count_result, mock_calendars_result]

        _calendars, total = await service.list_calendars(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_calendars_with_pagination(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_calendar: Mock,
    ) -> None:
        """Test list_calendars with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        mock_calendars_result = MagicMock()
        mock_calendars_result.scalars.return_value.all.return_value = [mock_calendar]

        mock_session.execute.side_effect = [mock_count_result, mock_calendars_result]

        calendars, total = await service.list_calendars(limit=10, offset=5)

        assert total == 50
        assert len(calendars) == 1

    async def test_list_calendars_empty_result(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_calendars with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_calendars_result = MagicMock()
        mock_calendars_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_calendars_result]

        calendars, total = await service.list_calendars()

        assert total == 0
        assert len(calendars) == 0


class TestGetEvent:
    """Tests for EventAdminService.get_event."""

    async def test_get_event_found(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test get_event returns event when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_event
        mock_session.execute.return_value = mock_result

        event = await service.get_event(mock_event.id)

        assert event == mock_event

    async def test_get_event_not_found(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_event returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        event = await service.get_event(uuid4())

        assert event is None


class TestGetCalendar:
    """Tests for EventAdminService.get_calendar."""

    async def test_get_calendar_found(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_calendar: Mock,
    ) -> None:
        """Test get_calendar returns calendar when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_calendar
        mock_session.execute.return_value = mock_result

        calendar = await service.get_calendar(mock_calendar.id)

        assert calendar == mock_calendar

    async def test_get_calendar_not_found(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_calendar returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        calendar = await service.get_calendar(uuid4())

        assert calendar is None


class TestFeatureEvent:
    """Tests for EventAdminService.feature_event."""

    async def test_feature_event_success(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test featuring an existing event."""
        mock_event.featured = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_event
        mock_session.execute.return_value = mock_result

        event = await service.feature_event(mock_event.id)

        assert event.featured is True
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_event)

    async def test_feature_event_not_found(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test featuring non-existent event returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        event = await service.feature_event(uuid4())

        assert event is None
        mock_session.commit.assert_not_called()


class TestUnfeatureEvent:
    """Tests for EventAdminService.unfeature_event."""

    async def test_unfeature_event_success(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
        mock_event: Mock,
    ) -> None:
        """Test unfeaturing an existing event."""
        mock_event.featured = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_event
        mock_session.execute.return_value = mock_result

        event = await service.unfeature_event(mock_event.id)

        assert event.featured is False
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_event)

    async def test_unfeature_event_not_found(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test unfeaturing non-existent event returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        event = await service.unfeature_event(uuid4())

        assert event is None
        mock_session.commit.assert_not_called()


class TestGetStats:
    """Tests for EventAdminService.get_stats."""

    async def test_get_stats_returns_all_counts(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats returns all event statistics."""
        mock_total_events = MagicMock()
        mock_total_events.scalar.return_value = 150

        mock_total_calendars = MagicMock()
        mock_total_calendars.scalar.return_value = 10

        mock_featured = MagicMock()
        mock_featured.scalar.return_value = 25

        mock_upcoming = MagicMock()
        mock_upcoming.scalar.return_value = 50

        mock_session.execute.side_effect = [
            mock_total_events,
            mock_total_calendars,
            mock_featured,
            mock_upcoming,
        ]

        stats = await service.get_stats()

        assert stats["total_events"] == 150
        assert stats["total_calendars"] == 10
        assert stats["featured_events"] == 25
        assert stats["upcoming_events"] == 50
        assert mock_session.execute.call_count == 4

    async def test_get_stats_empty_database(
        self,
        service: EventAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats with no events or calendars."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0

        mock_session.execute.return_value = mock_result

        stats = await service.get_stats()

        assert stats["total_events"] == 0
        assert stats["total_calendars"] == 0
        assert stats["featured_events"] == 0
        assert stats["upcoming_events"] == 0
