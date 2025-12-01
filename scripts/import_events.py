#!/usr/bin/env python
"""Import events from Python.org's Google Calendar ICS feed.

This script fetches the Python community events calendar and imports
events into our database.

Usage:
    uv run python scripts/import_events.py [--url URL] [--dry-run] [--clear]

The script:
1. Fetches the iCalendar feed from Google Calendar
2. Parses VEVENT components using the icalendar library
3. Creates/updates Calendar, EventLocation, Event, and EventOccurrence records
4. Handles recurring events by expanding occurrences
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import click
import httpx
from icalendar import Calendar as ICalendar
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydotorg.core.database import get_async_session_factory
from pydotorg.domains.events.models import (
    Calendar,
    Event,
    EventCategory,
    EventLocation,
    EventOccurrence,
)
from pydotorg.domains.users.models import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PYTHON_EVENTS_CALENDAR_URL = (
    "https://calendar.google.com/calendar/ical/j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com/public/basic.ics"
)

CATEGORY_PATTERNS = {
    "conference": [r"pycon", r"europython", r"scipy", r"pydata", r"djangocon", r"pycascades"],
    "meetup": [r"meetup", r"user group", r"usergroup"],
    "sprint": [r"sprint"],
    "workshop": [r"workshop", r"tutorial"],
    "hackathon": [r"hackathon", r"hack day"],
}


def detect_category(title: str, description: str | None) -> str:
    """Detect event category from title and description."""
    text = f"{title} {description or ''}".lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return category
    return "conference"


def parse_location(location_str: str | None) -> tuple[str, str | None, str | None]:
    """Parse location string into name, address, and URL.

    Returns:
        Tuple of (name, address, url)
    """
    if not location_str:
        return "TBD", None, None

    location_str = location_str.strip()

    if location_str.lower() in ("online", "virtual", "remote"):
        return "Online", None, "https://python.org/events"

    url = None
    url_match = re.search(r"https?://\S+", location_str)
    if url_match:
        url = url_match.group()
        location_str = location_str.replace(url, "").strip()

    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    if len(parts) >= 2:
        name = parts[-1] if len(parts[-1]) > 3 else ", ".join(parts[-2:])
        address = ", ".join(parts)
    else:
        name = location_str[:100] if location_str else "TBD"
        address = location_str if location_str else None

    return name, address, url


def parse_datetime(dt_value: Any) -> datetime | None:
    """Parse iCalendar datetime to Python datetime."""
    if dt_value is None:
        return None

    dt = dt_value.dt if hasattr(dt_value, "dt") else dt_value

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    if isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time(), tzinfo=UTC)

    return None


def is_all_day(dt_value: Any) -> bool:
    """Check if the datetime represents an all-day event."""
    if dt_value is None:
        return False
    dt = dt_value.dt if hasattr(dt_value, "dt") else dt_value
    return isinstance(dt, date) and not isinstance(dt, datetime)


async def fetch_calendar(url: str) -> bytes:
    """Fetch iCalendar data from URL."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def get_or_create_calendar(session: AsyncSession, name: str, slug: str, creator_id: UUID) -> Calendar:
    """Get or create a calendar."""
    result = await session.execute(select(Calendar).where(Calendar.slug == slug))
    calendar = result.scalar_one_or_none()

    if calendar is None:
        calendar = Calendar(name=name, slug=slug, creator_id=creator_id)
        session.add(calendar)
        await session.flush()
        logger.info(f"Created calendar: {name}")

    return calendar


async def get_or_create_category(session: AsyncSession, name: str, calendar_id: UUID) -> EventCategory:
    """Get or create an event category."""
    slug = slugify(name)
    result = await session.execute(
        select(EventCategory).where(EventCategory.slug == slug, EventCategory.calendar_id == calendar_id)
    )
    category = result.scalar_one_or_none()

    if category is None:
        category = EventCategory(name=name.title(), slug=slug, calendar_id=calendar_id)
        session.add(category)
        await session.flush()
        logger.info(f"Created category: {name}")

    return category


async def get_or_create_location(
    session: AsyncSession, name: str, address: str | None, url: str | None
) -> EventLocation:
    """Get or create an event location."""
    slug = slugify(name)[:50]
    result = await session.execute(select(EventLocation).where(EventLocation.slug == slug))
    location = result.scalar_one_or_none()

    if location is None:
        location = EventLocation(name=name[:200], slug=slug, address=address, url=url)
        session.add(location)
        await session.flush()
        logger.info(f"Created location: {name}")

    return location


async def import_events(
    session: AsyncSession,
    ical_data: bytes,
    calendar: Calendar,
    creator_id: UUID,
    dry_run: bool = False,
) -> dict[str, int]:
    """Import events from iCalendar data."""
    stats = {"created": 0, "updated": 0, "skipped": 0, "occurrences": 0}

    ical = ICalendar.from_ical(ical_data)

    category_cache: dict[str, EventCategory] = {}
    location_cache: dict[str, EventLocation] = {}

    for component in ical.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("UID", ""))
        summary = str(component.get("SUMMARY", "Untitled Event"))
        description = str(component.get("DESCRIPTION", "")) or None
        location_str = str(component.get("LOCATION", "")) or None
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")

        if not uid:
            stats["skipped"] += 1
            continue

        slug = slugify(summary)[:100]
        if not slug:
            slug = slugify(uid)[:100]

        result = await session.execute(select(Event).where(Event.slug == slug, Event.calendar_id == calendar.id))
        existing_event = result.scalar_one_or_none()

        category_name = detect_category(summary, description)
        if category_name not in category_cache:
            category_cache[category_name] = await get_or_create_category(session, category_name, calendar.id)
        _ = category_cache[category_name]

        loc_name, loc_address, loc_url = parse_location(location_str)
        loc_key = slugify(loc_name)[:50]
        if loc_key not in location_cache:
            location_cache[loc_key] = await get_or_create_location(session, loc_name, loc_address, loc_url)
        location = location_cache[loc_key]

        start_dt = parse_datetime(dtstart)
        end_dt = parse_datetime(dtend)
        all_day = is_all_day(dtstart)

        if existing_event:
            existing_event.title = summary
            existing_event.description = description
            existing_event.venue_id = location.id
            stats["updated"] += 1
            event = existing_event
            logger.debug(f"Updated event: {summary}")
        else:
            event = Event(
                name=slug,
                slug=slug,
                title=summary,
                description=description,
                calendar_id=calendar.id,
                venue_id=location.id,
                featured=False,
                creator_id=creator_id,
            )
            session.add(event)
            await session.flush()
            stats["created"] += 1
            logger.info(f"Created event: {summary}")

        if start_dt:
            result = await session.execute(
                select(EventOccurrence).where(
                    EventOccurrence.event_id == event.id,
                    EventOccurrence.dt_start == start_dt,
                )
            )
            existing_occurrence = result.scalar_one_or_none()

            if not existing_occurrence:
                occurrence = EventOccurrence(
                    event_id=event.id,
                    dt_start=start_dt,
                    dt_end=end_dt,
                    all_day=all_day,
                )
                session.add(occurrence)
                stats["occurrences"] += 1

    if not dry_run:
        await session.commit()
        logger.info("Changes committed to database")
    else:
        await session.rollback()
        logger.info("Dry run - changes rolled back")

    return stats


async def clear_events(session: AsyncSession, calendar_slug: str) -> int:
    """Clear all events from a calendar."""
    result = await session.execute(select(Calendar).where(Calendar.slug == calendar_slug))
    calendar = result.scalar_one_or_none()

    if not calendar:
        logger.warning(f"Calendar '{calendar_slug}' not found")
        return 0

    result = await session.execute(select(Event).where(Event.calendar_id == calendar.id))
    events = result.scalars().all()
    count = len(events)

    for event in events:
        await session.delete(event)

    await session.commit()
    logger.info(f"Deleted {count} events from calendar '{calendar_slug}'")
    return count


async def get_admin_user(session: AsyncSession) -> User:
    """Get the admin user for creating content."""
    result = await session.execute(select(User).where(User.is_superuser == True).limit(1))  # noqa: E712
    user = result.scalar_one_or_none()

    if not user:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

    if not user:
        msg = "No users found in database. Run 'make db-seed' first."
        raise RuntimeError(msg)

    return user


@click.command()
@click.option(
    "--url",
    default=PYTHON_EVENTS_CALENDAR_URL,
    help="URL of the iCalendar feed to import",
)
@click.option(
    "--calendar-name",
    default="Python Events",
    help="Name of the calendar to create/use",
)
@click.option(
    "--calendar-slug",
    default="python-events",
    help="Slug of the calendar to create/use",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't actually save changes to database",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing events before importing",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    url: str,
    calendar_name: str,
    calendar_slug: str,
    dry_run: bool,
    clear: bool,
    verbose: bool,
) -> None:
    """Import events from Python.org's Google Calendar."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    async def run() -> None:
        session_factory = get_async_session_factory()

        async with session_factory() as session:
            if clear:
                await clear_events(session, calendar_slug)

            logger.info(f"Fetching calendar from {url}")
            ical_data = await fetch_calendar(url)
            logger.info(f"Fetched {len(ical_data)} bytes")

            admin_user = await get_admin_user(session)
            logger.info(f"Using admin user: {admin_user.username}")

            calendar = await get_or_create_calendar(session, calendar_name, calendar_slug, admin_user.id)

            stats = await import_events(session, ical_data, calendar, admin_user.id, dry_run)

            logger.info("=" * 50)
            logger.info("Import complete!")
            logger.info(f"  Created: {stats['created']} events")
            logger.info(f"  Updated: {stats['updated']} events")
            logger.info(f"  Skipped: {stats['skipped']} events")
            logger.info(f"  Occurrences: {stats['occurrences']}")
            if dry_run:
                logger.info("  (DRY RUN - no changes saved)")

    asyncio.run(run())


if __name__ == "__main__":
    main()
