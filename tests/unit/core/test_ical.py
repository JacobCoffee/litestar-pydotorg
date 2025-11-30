"""Unit tests for iCalendar service."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from pydotorg.core.ical.service import ICalendarService


class TestICalendarServiceEscaping:
    """Tests for text escaping per RFC 5545."""

    def test_escape_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert ICalendarService._escape_text("") == ""

    def test_escape_plain_text(self) -> None:
        """Plain text without special chars returns unchanged."""
        assert ICalendarService._escape_text("Hello World") == "Hello World"

    def test_escape_backslash(self) -> None:
        """Backslashes are escaped."""
        assert ICalendarService._escape_text("path\\to\\file") == "path\\\\to\\\\file"

    def test_escape_semicolon(self) -> None:
        """Semicolons are escaped."""
        assert ICalendarService._escape_text("a;b;c") == "a\\;b\\;c"

    def test_escape_comma(self) -> None:
        """Commas are escaped."""
        assert ICalendarService._escape_text("one,two,three") == "one\\,two\\,three"

    def test_escape_newline(self) -> None:
        """Newlines are converted to \\n."""
        assert ICalendarService._escape_text("line1\nline2") == "line1\\nline2"

    def test_escape_carriage_return_removed(self) -> None:
        """Carriage returns are removed."""
        assert ICalendarService._escape_text("line1\r\nline2") == "line1\\nline2"

    def test_escape_multiple_special_chars(self) -> None:
        """Multiple special characters are all escaped."""
        result = ICalendarService._escape_text("a;b,c\\d\ne")
        assert result == "a\\;b\\,c\\\\d\\ne"


class TestICalendarServiceLineFolding:
    """Tests for line folding per RFC 5545."""

    def test_short_line_unchanged(self) -> None:
        """Lines under 75 octets are unchanged."""
        line = "SHORT LINE"
        assert ICalendarService._fold_line(line) == line

    def test_exactly_75_octets_unchanged(self) -> None:
        """Line exactly 75 octets is unchanged."""
        line = "A" * 75
        assert ICalendarService._fold_line(line) == line

    def test_long_line_folded(self) -> None:
        """Lines over 75 octets are folded with CRLF+space."""
        line = "A" * 100
        result = ICalendarService._fold_line(line)
        assert "\r\n " in result
        lines = result.split("\r\n ")
        assert len(lines) == 2

    def test_very_long_line_multiple_folds(self) -> None:
        """Very long lines have multiple folds."""
        line = "A" * 200
        result = ICalendarService._fold_line(line)
        assert result.count("\r\n ") >= 2


class TestICalendarServiceDateFormatting:
    """Tests for datetime formatting."""

    def test_format_timed_event(self) -> None:
        """Timed events use DATE-TIME format with Z suffix."""
        dt = datetime.datetime(2025, 12, 15, 14, 30, 0, tzinfo=datetime.UTC)
        result = ICalendarService._format_datetime(dt)
        assert result == "20251215T143000Z"

    def test_format_all_day_event(self) -> None:
        """All-day events use DATE format without time."""
        dt = datetime.datetime(2025, 12, 15, 0, 0, 0, tzinfo=datetime.UTC)
        result = ICalendarService._format_datetime(dt, all_day=True)
        assert result == "20251215"

    def test_format_naive_datetime(self) -> None:
        """Naive datetimes are treated as UTC."""
        dt = datetime.datetime(2025, 6, 1, 10, 0, 0)
        result = ICalendarService._format_datetime(dt)
        assert result == "20250601T100000Z"

    def test_format_non_utc_timezone(self) -> None:
        """Non-UTC timezones are converted to UTC."""
        from zoneinfo import ZoneInfo

        dt = datetime.datetime(2025, 6, 1, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        result = ICalendarService._format_datetime(dt)
        assert result == "20250601T140000Z"


class TestICalendarServiceEventGeneration:
    """Tests for VEVENT generation."""

    @pytest.fixture
    def mock_event(self) -> MagicMock:
        """Create a mock event."""
        event = MagicMock()
        event.id = uuid4()
        event.title = "PyCon US 2025"
        event.description = "Annual Python conference"
        event.slug = "pycon-us-2025"
        event.venue = None
        event.categories = []
        event.occurrences = []
        return event

    @pytest.fixture
    def mock_occurrence(self) -> MagicMock:
        """Create a mock occurrence."""
        occurrence = MagicMock()
        occurrence.id = uuid4()
        occurrence.dt_start = datetime.datetime(2025, 5, 14, 9, 0, 0, tzinfo=datetime.UTC)
        occurrence.dt_end = datetime.datetime(2025, 5, 14, 17, 0, 0, tzinfo=datetime.UTC)
        occurrence.all_day = False
        return occurrence

    def test_generate_event_ical_basic(self, mock_event: MagicMock, mock_occurrence: MagicMock) -> None:
        """Basic event generates valid iCalendar."""
        mock_event.occurrences = [mock_occurrence]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result
        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result
        assert "VERSION:2.0" in result
        assert "PRODID:-//Python.org//Events Calendar//EN" in result
        assert "SUMMARY:PyCon US 2025" in result

    def test_generate_event_ical_with_description(self, mock_event: MagicMock, mock_occurrence: MagicMock) -> None:
        """Event description is included."""
        mock_event.occurrences = [mock_occurrence]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert "DESCRIPTION:Annual Python conference" in result

    def test_generate_event_ical_with_venue(self, mock_event: MagicMock, mock_occurrence: MagicMock) -> None:
        """Event venue is included as LOCATION."""
        venue = MagicMock()
        venue.name = "Convention Center"
        venue.address = "123 Main St, Pittsburgh, PA"
        mock_event.venue = venue
        mock_event.occurrences = [mock_occurrence]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert "LOCATION:Convention Center\\, 123 Main St\\, Pittsburgh\\, PA" in result

    def test_generate_event_ical_with_categories(self, mock_event: MagicMock, mock_occurrence: MagicMock) -> None:
        """Event categories are included."""
        cat1 = MagicMock()
        cat1.name = "Conference"
        cat2 = MagicMock()
        cat2.name = "Python"
        mock_event.categories = [cat1, cat2]
        mock_event.occurrences = [mock_occurrence]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert "CATEGORIES:Conference,Python" in result

    def test_generate_event_ical_multiple_occurrences(self, mock_event: MagicMock) -> None:
        """Multiple occurrences generate multiple VEVENTs."""
        occ1 = MagicMock()
        occ1.id = uuid4()
        occ1.dt_start = datetime.datetime(2025, 5, 14, 9, 0, 0, tzinfo=datetime.UTC)
        occ1.dt_end = datetime.datetime(2025, 5, 14, 17, 0, 0, tzinfo=datetime.UTC)
        occ1.all_day = False

        occ2 = MagicMock()
        occ2.id = uuid4()
        occ2.dt_start = datetime.datetime(2025, 5, 15, 9, 0, 0, tzinfo=datetime.UTC)
        occ2.dt_end = datetime.datetime(2025, 5, 15, 17, 0, 0, tzinfo=datetime.UTC)
        occ2.all_day = False

        mock_event.occurrences = [occ1, occ2]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert result.count("BEGIN:VEVENT") == 2
        assert result.count("END:VEVENT") == 2

    def test_generate_event_ical_all_day(self, mock_event: MagicMock) -> None:
        """All-day events use DATE format."""
        occ = MagicMock()
        occ.id = uuid4()
        occ.dt_start = datetime.datetime(2025, 5, 14, 0, 0, 0, tzinfo=datetime.UTC)
        occ.dt_end = datetime.datetime(2025, 5, 14, 23, 59, 59, tzinfo=datetime.UTC)
        occ.all_day = True
        mock_event.occurrences = [occ]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert "DTSTART;VALUE=DATE:20250514" in result

    def test_generate_event_ical_includes_url(self, mock_event: MagicMock, mock_occurrence: MagicMock) -> None:
        """Event URL is included."""
        mock_event.occurrences = [mock_occurrence]

        service = ICalendarService()
        result = service.generate_event_ical(mock_event)

        assert "URL:https://www.python.org/events/pycon-us-2025/" in result


class TestICalendarServiceCalendarFeed:
    """Tests for calendar feed generation."""

    @pytest.fixture
    def mock_calendar(self) -> MagicMock:
        """Create a mock calendar."""
        calendar = MagicMock()
        calendar.name = "Python Conferences"
        calendar.slug = "conferences"
        return calendar

    def test_generate_calendar_feed_empty(self, mock_calendar: MagicMock) -> None:
        """Empty calendar generates valid iCalendar."""
        service = ICalendarService()
        result = service.generate_calendar_feed(mock_calendar, [])

        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result
        assert "X-WR-CALNAME:Python Conferences" in result
        assert "BEGIN:VEVENT" not in result

    def test_generate_calendar_feed_with_events(self, mock_calendar: MagicMock) -> None:
        """Calendar with events includes all VEVENTs."""
        event = MagicMock()
        event.id = uuid4()
        event.title = "PyConf"
        event.description = None
        event.slug = "pyconf"
        event.venue = None
        event.categories = []

        occ = MagicMock()
        occ.id = uuid4()
        occ.dt_start = datetime.datetime(2025, 6, 1, 9, 0, 0, tzinfo=datetime.UTC)
        occ.dt_end = None
        occ.all_day = False
        event.occurrences = [occ]

        service = ICalendarService()
        result = service.generate_calendar_feed(mock_calendar, [event])

        assert "BEGIN:VEVENT" in result
        assert "SUMMARY:PyConf" in result

    def test_generate_upcoming_feed(self) -> None:
        """Upcoming feed generates valid iCalendar."""
        service = ICalendarService()
        result = service.generate_upcoming_feed([], title="Test Events")

        assert "BEGIN:VCALENDAR" in result
        assert "X-WR-CALNAME:Test Events" in result
        assert "X-WR-CALDESC:Upcoming Python community events" in result


class TestICalendarServiceRFC5545Compliance:
    """Tests for RFC 5545 compliance."""

    @pytest.fixture
    def service(self) -> ICalendarService:
        """Create service instance."""
        return ICalendarService()

    def test_line_endings_crlf(self, service: ICalendarService) -> None:
        """iCalendar uses CRLF line endings."""
        event = MagicMock()
        event.id = uuid4()
        event.title = "Test"
        event.description = None
        event.slug = "test"
        event.venue = None
        event.categories = []
        event.occurrences = []

        result = service.generate_event_ical(event)
        assert "\r\n" in result

    def test_dtstamp_present(self, service: ICalendarService) -> None:
        """DTSTAMP is required and present in VEVENTs."""
        event = MagicMock()
        event.id = uuid4()
        event.title = "Test"
        event.description = None
        event.slug = "test"
        event.venue = None
        event.categories = []

        occ = MagicMock()
        occ.id = uuid4()
        occ.dt_start = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)
        occ.dt_end = None
        occ.all_day = False
        event.occurrences = [occ]

        result = service.generate_event_ical(event)
        assert "DTSTAMP:" in result

    def test_uid_unique_per_occurrence(self, service: ICalendarService) -> None:
        """Each occurrence has a unique UID."""
        event = MagicMock()
        event.id = uuid4()
        event.title = "Test"
        event.description = None
        event.slug = "test"
        event.venue = None
        event.categories = []

        occ1 = MagicMock()
        occ1.id = uuid4()
        occ1.dt_start = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)
        occ1.dt_end = None
        occ1.all_day = False

        occ2 = MagicMock()
        occ2.id = uuid4()
        occ2.dt_start = datetime.datetime(2025, 1, 2, 0, 0, 0, tzinfo=datetime.UTC)
        occ2.dt_end = None
        occ2.all_day = False

        event.occurrences = [occ1, occ2]

        result = service.generate_event_ical(event)

        uid_lines = [line for line in result.split("\r\n") if line.startswith("UID:")]
        assert len(uid_lines) == 2
        assert uid_lines[0] != uid_lines[1]
