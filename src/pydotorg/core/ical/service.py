"""iCalendar (RFC 5545) generation service for events."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydotorg.domains.events.models import Calendar, Event, EventOccurrence


class ICalendarService:
    """Service for generating iCalendar (RFC 5545) formatted data."""

    PRODID = "-//Python.org//Events Calendar//EN"
    VERSION = "2.0"
    CALSCALE = "GREGORIAN"
    METHOD = "PUBLISH"

    @staticmethod
    def _escape_text(text: str) -> str:
        """Escape special characters per RFC 5545.

        Characters that must be escaped: backslash, semicolon, comma, newline.
        """
        if not text:
            return ""
        return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n").replace("\r", "")

    @staticmethod
    def _fold_line(line: str, max_length: int = 75) -> str:
        """Fold long lines per RFC 5545 (max 75 octets per line)."""
        if len(line.encode("utf-8")) <= max_length:
            return line

        result = []
        current_line = ""

        for char in line:
            test_line = current_line + char
            if len(test_line.encode("utf-8")) > max_length:
                result.append(current_line)
                current_line = " " + char
            else:
                current_line = test_line

        if current_line:
            result.append(current_line)

        return "\r\n".join(result)

    @staticmethod
    def _format_datetime(dt: datetime.datetime, *, all_day: bool = False) -> str:
        """Format datetime for iCalendar.

        All-day events use DATE format (YYYYMMDD).
        Timed events use DATE-TIME format (YYYYMMDDTHHMMSSZ) in UTC.
        """
        if all_day:
            return dt.strftime("%Y%m%d")

        utc_dt = dt.astimezone(datetime.UTC) if dt.tzinfo is not None else dt.replace(tzinfo=datetime.UTC)
        return utc_dt.strftime("%Y%m%dT%H%M%SZ")

    @staticmethod
    def _format_timestamp() -> str:
        """Generate current timestamp for DTSTAMP."""
        return datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")

    def _generate_vevent(
        self,
        event: Event,
        occurrence: EventOccurrence,
        base_url: str = "https://www.python.org",
    ) -> list[str]:
        """Generate a VEVENT component for an event occurrence."""
        lines = ["BEGIN:VEVENT"]

        uid = f"{event.id}-{occurrence.id}@python.org"
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{self._format_timestamp()}")

        if occurrence.all_day:
            lines.append(f"DTSTART;VALUE=DATE:{self._format_datetime(occurrence.dt_start, all_day=True)}")
            if occurrence.dt_end:
                end_date = occurrence.dt_end + datetime.timedelta(days=1)
                lines.append(f"DTEND;VALUE=DATE:{self._format_datetime(end_date, all_day=True)}")
        else:
            lines.append(f"DTSTART:{self._format_datetime(occurrence.dt_start)}")
            if occurrence.dt_end:
                lines.append(f"DTEND:{self._format_datetime(occurrence.dt_end)}")

        lines.append(self._fold_line(f"SUMMARY:{self._escape_text(event.title)}"))

        if event.description:
            lines.append(self._fold_line(f"DESCRIPTION:{self._escape_text(event.description)}"))

        if event.venue:
            location_parts = [event.venue.name]
            if event.venue.address:
                location_parts.append(event.venue.address)
            location = ", ".join(location_parts)
            lines.append(self._fold_line(f"LOCATION:{self._escape_text(location)}"))

        if event.slug:
            lines.append(f"URL:{base_url}/events/{event.slug}/")

        if event.categories:
            category_names = [cat.name for cat in event.categories]
            lines.append(f"CATEGORIES:{','.join(self._escape_text(c) for c in category_names)}")

        lines.append("END:VEVENT")
        return lines

    def generate_event_ical(
        self,
        event: Event,
        base_url: str = "https://www.python.org",
    ) -> str:
        """Generate iCalendar data for a single event with all its occurrences.

        Each occurrence generates a separate VEVENT component with the same
        event details but different dates.
        """
        lines = [
            "BEGIN:VCALENDAR",
            f"VERSION:{self.VERSION}",
            f"PRODID:{self.PRODID}",
            f"CALSCALE:{self.CALSCALE}",
            f"METHOD:{self.METHOD}",
            f"X-WR-CALNAME:{self._escape_text(event.title)}",
        ]

        for occurrence in event.occurrences:
            lines.extend(self._generate_vevent(event, occurrence, base_url))

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    def generate_calendar_feed(
        self,
        calendar: Calendar,
        events: Sequence[Event],
        base_url: str = "https://www.python.org",
    ) -> str:
        """Generate iCalendar feed for an entire calendar with all events.

        Each event occurrence generates a separate VEVENT component.
        """
        cal_name = calendar.name if calendar else "Python Events"

        lines = [
            "BEGIN:VCALENDAR",
            f"VERSION:{self.VERSION}",
            f"PRODID:{self.PRODID}",
            f"CALSCALE:{self.CALSCALE}",
            f"METHOD:{self.METHOD}",
            f"X-WR-CALNAME:{self._escape_text(cal_name)}",
        ]

        if calendar and calendar.slug:
            lines.append(f"X-WR-CALDESC:Python community events from {cal_name}")

        for event in events:
            for occurrence in event.occurrences:
                lines.extend(self._generate_vevent(event, occurrence, base_url))

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    def generate_upcoming_feed(
        self,
        events: Sequence[Event],
        title: str = "Python Events",
        base_url: str = "https://www.python.org",
    ) -> str:
        """Generate iCalendar feed for upcoming events across all calendars."""
        lines = [
            "BEGIN:VCALENDAR",
            f"VERSION:{self.VERSION}",
            f"PRODID:{self.PRODID}",
            f"CALSCALE:{self.CALSCALE}",
            f"METHOD:{self.METHOD}",
            f"X-WR-CALNAME:{self._escape_text(title)}",
            "X-WR-CALDESC:Upcoming Python community events",
        ]

        for event in events:
            for occurrence in event.occurrences:
                lines.extend(self._generate_vevent(event, occurrence, base_url))

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)
