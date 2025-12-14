"""Unit tests for event recurrence utilities."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest
from dateutil.rrule import DAILY, MONTHLY, WEEKLY, YEARLY

from pydotorg.domains.events.recurrence import (
    Frequency,
    create_rrule,
    frequency_interval_as_timedelta,
    get_occurrences,
    next_occurrence,
    timedelta_format,
    timedelta_parse,
)

if TYPE_CHECKING:
    pass


class TestTimedeltaParse:
    """Tests for timedelta_parse function."""

    def test_parse_minutes(self) -> None:
        """Test parsing minutes format."""
        result = timedelta_parse("15 min")
        assert result == datetime.timedelta(minutes=15)

    def test_parse_hours(self) -> None:
        """Test parsing hours format."""
        result = timedelta_parse("2 hours")
        assert result == datetime.timedelta(hours=2)

    def test_parse_days(self) -> None:
        """Test parsing days format."""
        result = timedelta_parse("3 days")
        assert result == datetime.timedelta(days=3)

    def test_parse_weeks(self) -> None:
        """Test parsing weeks format."""
        result = timedelta_parse("1 week")
        assert result == datetime.timedelta(weeks=1)

    def test_parse_combined(self) -> None:
        """Test parsing combined format."""
        result = timedelta_parse("1d 2h 30m")
        assert result == datetime.timedelta(days=1, hours=2, minutes=30)

    def test_parse_postgres_format(self) -> None:
        """Test parsing PostgreSQL format."""
        result = timedelta_parse("02:30:00")
        assert result == datetime.timedelta(hours=2, minutes=30)

    def test_parse_postgres_days_format(self) -> None:
        """Test parsing PostgreSQL days format."""
        result = timedelta_parse("3 days, 04:30:00")
        assert result == datetime.timedelta(days=3, hours=4, minutes=30)

    def test_parse_empty_raises(self) -> None:
        """Test that empty string raises TypeError."""
        with pytest.raises(TypeError):
            timedelta_parse("")

    def test_parse_invalid_raises(self) -> None:
        """Test that invalid string raises TypeError."""
        with pytest.raises(TypeError):
            timedelta_parse("not a time")


class TestTimedeltaFormat:
    """Tests for timedelta_format function."""

    def test_format_minutes_long(self) -> None:
        """Test formatting minutes in long format."""
        td = datetime.timedelta(minutes=15)
        assert timedelta_format(td) == "15 minutes"

    def test_format_minutes_short(self) -> None:
        """Test formatting minutes in short format."""
        td = datetime.timedelta(minutes=15)
        assert timedelta_format(td, display="short") == "15 min"

    def test_format_minutes_minimal(self) -> None:
        """Test formatting minutes in minimal format."""
        td = datetime.timedelta(minutes=15)
        assert timedelta_format(td, display="minimal") == "15m"

    def test_format_hours_singular(self) -> None:
        """Test formatting singular hour."""
        td = datetime.timedelta(hours=1)
        assert timedelta_format(td) == "1 hour"

    def test_format_combined(self) -> None:
        """Test formatting combined duration."""
        td = datetime.timedelta(days=2, hours=3, minutes=30)
        assert timedelta_format(td) == "2 days, 3 hours, 30 minutes"

    def test_format_weeks(self) -> None:
        """Test formatting weeks."""
        td = datetime.timedelta(weeks=2, days=1)
        assert timedelta_format(td) == "2 weeks, 1 day"

    def test_format_zero(self) -> None:
        """Test formatting zero duration."""
        td = datetime.timedelta()
        assert timedelta_format(td) == "0 seconds"

    def test_format_non_timedelta_raises(self) -> None:
        """Test that non-timedelta raises TypeError."""
        with pytest.raises(TypeError):
            timedelta_format("not a timedelta")


class TestFrequency:
    """Tests for Frequency enum."""

    def test_frequency_values(self) -> None:
        """Test frequency values match dateutil constants."""
        assert Frequency.YEARLY == YEARLY
        assert Frequency.MONTHLY == MONTHLY
        assert Frequency.WEEKLY == WEEKLY
        assert Frequency.DAILY == DAILY


class TestCreateRrule:
    """Tests for create_rrule function."""

    def test_create_weekly_rule(self) -> None:
        """Test creating a weekly rule."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        until = datetime.datetime(2025, 2, 1, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.WEEKLY, dtstart=dtstart, until=until)

        occurrences = list(rule)
        assert len(occurrences) == 5
        assert occurrences[0] == dtstart

    def test_create_daily_rule_with_count(self) -> None:
        """Test creating a daily rule with count limit."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.DAILY, dtstart=dtstart, count=7)

        occurrences = list(rule)
        assert len(occurrences) == 7

    def test_create_monthly_rule_with_interval(self) -> None:
        """Test creating a monthly rule with interval."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.MONTHLY, interval=2, dtstart=dtstart, count=6)

        occurrences = list(rule)
        assert len(occurrences) == 6
        assert occurrences[1].month == 3


class TestGetOccurrences:
    """Tests for get_occurrences function."""

    def test_get_occurrences_between(self) -> None:
        """Test getting occurrences between two dates."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.DAILY, dtstart=dtstart, count=30)

        after = datetime.datetime(2025, 1, 10, 0, 0, tzinfo=datetime.UTC)
        before = datetime.datetime(2025, 1, 20, 0, 0, tzinfo=datetime.UTC)

        occurrences = list(get_occurrences(rule, after, before))
        # Jan 10-19 at 10:00 (10 occurrences) - Jan 10 10:00 is after Jan 10 00:00
        assert len(occurrences) == 10

    def test_get_occurrences_after(self) -> None:
        """Test getting next occurrence after a date."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.WEEKLY, dtstart=dtstart, count=10)

        # After Jan 15 00:00, next weekly occurrence is Jan 15 10:00 (same day, later time)
        after = datetime.datetime(2025, 1, 15, 0, 0, tzinfo=datetime.UTC)
        occurrences = list(get_occurrences(rule, after=after))

        assert len(occurrences) == 1
        assert occurrences[0] == datetime.datetime(2025, 1, 15, 10, 0, tzinfo=datetime.UTC)


class TestNextOccurrence:
    """Tests for next_occurrence function."""

    def test_next_occurrence(self) -> None:
        """Test getting next occurrence."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.WEEKLY, dtstart=dtstart, count=52)

        after = datetime.datetime(2025, 1, 10, 0, 0, tzinfo=datetime.UTC)
        result = next_occurrence(rule, after=after)

        assert result == datetime.datetime(2025, 1, 15, 10, 0, tzinfo=datetime.UTC)

    def test_next_occurrence_none_when_finished(self) -> None:
        """Test that None is returned when no more occurrences."""
        dtstart = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)
        until = datetime.datetime(2025, 1, 15, 10, 0, tzinfo=datetime.UTC)
        rule = create_rrule(Frequency.WEEKLY, dtstart=dtstart, until=until)

        after = datetime.datetime(2025, 2, 1, 0, 0, tzinfo=datetime.UTC)
        result = next_occurrence(rule, after=after)

        assert result is None


class TestFrequencyIntervalAsTimedelta:
    """Tests for frequency_interval_as_timedelta function."""

    def test_daily_interval(self) -> None:
        """Test daily interval conversion."""
        result = frequency_interval_as_timedelta(Frequency.DAILY, 3)
        assert result == datetime.timedelta(days=3)

    def test_weekly_interval(self) -> None:
        """Test weekly interval conversion."""
        result = frequency_interval_as_timedelta(Frequency.WEEKLY, 2)
        assert result == datetime.timedelta(days=14)

    def test_monthly_interval(self) -> None:
        """Test monthly interval conversion."""
        result = frequency_interval_as_timedelta(Frequency.MONTHLY, 1)
        assert result == datetime.timedelta(days=30)

    def test_yearly_interval(self) -> None:
        """Test yearly interval conversion."""
        result = frequency_interval_as_timedelta(Frequency.YEARLY, 1)
        assert result == datetime.timedelta(days=365)
