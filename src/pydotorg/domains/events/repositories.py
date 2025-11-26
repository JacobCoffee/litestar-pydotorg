"""Events domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import and_, select

from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class CalendarRepository(SQLAlchemyAsyncRepository[Calendar]):
    """Repository for Calendar database operations."""

    model_type = Calendar

    async def get_by_slug(self, slug: str) -> Calendar | None:
        """Get a calendar by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The calendar if found, None otherwise.
        """
        statement = select(Calendar).where(Calendar.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class EventCategoryRepository(SQLAlchemyAsyncRepository[EventCategory]):
    """Repository for EventCategory database operations."""

    model_type = EventCategory

    async def get_by_slug(self, slug: str) -> EventCategory | None:
        """Get an event category by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The event category if found, None otherwise.
        """
        statement = select(EventCategory).where(EventCategory.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_calendar_id(self, calendar_id: UUID) -> list[EventCategory]:
        """Get all categories for a calendar.

        Args:
            calendar_id: The calendar ID to search for.

        Returns:
            List of event categories.
        """
        statement = select(EventCategory).where(EventCategory.calendar_id == calendar_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class EventLocationRepository(SQLAlchemyAsyncRepository[EventLocation]):
    """Repository for EventLocation database operations."""

    model_type = EventLocation

    async def get_by_slug(self, slug: str) -> EventLocation | None:
        """Get an event location by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The event location if found, None otherwise.
        """
        statement = select(EventLocation).where(EventLocation.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class EventRepository(SQLAlchemyAsyncRepository[Event]):
    """Repository for Event database operations."""

    model_type = Event

    async def get_by_slug(self, slug: str) -> Event | None:
        """Get an event by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The event if found, None otherwise.
        """
        statement = select(Event).where(Event.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_calendar_id(self, calendar_id: UUID, limit: int = 100) -> list[Event]:
        """Get all events for a calendar.

        Args:
            calendar_id: The calendar ID to search for.
            limit: Maximum number of events to return.

        Returns:
            List of events.
        """
        statement = select(Event).where(Event.calendar_id == calendar_id).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_featured(self, calendar_id: UUID | None = None, limit: int = 10) -> list[Event]:
        """Get featured events.

        Args:
            calendar_id: Optional calendar ID to filter by.
            limit: Maximum number of events to return.

        Returns:
            List of featured events.
        """
        statement = select(Event).where(Event.featured.is_(True))

        if calendar_id:
            statement = statement.where(Event.calendar_id == calendar_id)

        statement = statement.limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_category_id(self, category_id: UUID, limit: int = 100) -> list[Event]:
        """Get all events for a category.

        Args:
            category_id: The category ID to search for.
            limit: Maximum number of events to return.

        Returns:
            List of events.
        """
        statement = select(Event).join(Event.categories).where(EventCategory.id == category_id).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        calendar_id: UUID | None = None,
        start_date: datetime.datetime | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get upcoming events based on their next occurrence.

        Args:
            calendar_id: Optional calendar ID to filter by.
            start_date: Optional start date to filter occurrences.
            limit: Maximum number of events to return.

        Returns:
            List of upcoming events.
        """
        statement = select(Event).join(Event.occurrences)

        conditions = []
        if start_date:
            conditions.append(EventOccurrence.dt_start >= start_date)
        if calendar_id:
            conditions.append(Event.calendar_id == calendar_id)

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = statement.order_by(EventOccurrence.dt_start).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class EventOccurrenceRepository(SQLAlchemyAsyncRepository[EventOccurrence]):
    """Repository for EventOccurrence database operations."""

    model_type = EventOccurrence

    async def get_by_event_id(self, event_id: UUID) -> list[EventOccurrence]:
        """Get all occurrences for an event.

        Args:
            event_id: The event ID to search for.

        Returns:
            List of event occurrences.
        """
        statement = (
            select(EventOccurrence).where(EventOccurrence.event_id == event_id).order_by(EventOccurrence.dt_start)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_next_occurrence(
        self,
        event_id: UUID,
        after: datetime.datetime | None = None,
    ) -> EventOccurrence | None:
        """Get the next occurrence for an event.

        Args:
            event_id: The event ID to search for.
            after: Optional datetime to search after.

        Returns:
            The next occurrence if found, None otherwise.
        """
        statement = select(EventOccurrence).where(EventOccurrence.event_id == event_id)

        if after:
            statement = statement.where(EventOccurrence.dt_start >= after)

        statement = statement.order_by(EventOccurrence.dt_start).limit(1)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        calendar_id: UUID | None = None,
    ) -> list[EventOccurrence]:
        """Get occurrences within a date range.

        Args:
            start_date: The start of the date range.
            end_date: The end of the date range.
            calendar_id: Optional calendar ID to filter by.

        Returns:
            List of event occurrences.
        """
        statement = (
            select(EventOccurrence)
            .join(EventOccurrence.event)
            .where(
                and_(
                    EventOccurrence.dt_start >= start_date,
                    EventOccurrence.dt_start <= end_date,
                )
            )
        )

        if calendar_id:
            statement = statement.where(Event.calendar_id == calendar_id)

        statement = statement.order_by(EventOccurrence.dt_start)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
