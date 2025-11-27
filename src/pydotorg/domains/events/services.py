"""Events domain services for business logic."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence
from pydotorg.domains.events.repositories import (
    CalendarRepository,
    EventCategoryRepository,
    EventLocationRepository,
    EventOccurrenceRepository,
    EventRepository,
)
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    import datetime
    from uuid import UUID

logger = logging.getLogger(__name__)


class CalendarService(SQLAlchemyAsyncRepositoryService[Calendar]):
    """Service for Calendar business logic."""

    repository_type = CalendarRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> Calendar | None:
        """Get a calendar by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The calendar if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)


class EventCategoryService(SQLAlchemyAsyncRepositoryService[EventCategory]):
    """Service for EventCategory business logic."""

    repository_type = EventCategoryRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> EventCategory | None:
        """Get an event category by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The event category if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_by_calendar_id(self, calendar_id: UUID) -> list[EventCategory]:
        """Get all categories for a calendar.

        Args:
            calendar_id: The calendar ID to search for.

        Returns:
            List of event categories.
        """
        return await self.repository.get_by_calendar_id(calendar_id)


class EventLocationService(SQLAlchemyAsyncRepositoryService[EventLocation]):
    """Service for EventLocation business logic."""

    repository_type = EventLocationRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> EventLocation | None:
        """Get an event location by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The event location if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)


class EventService(SQLAlchemyAsyncRepositoryService[Event]):
    """Service for Event business logic."""

    repository_type = EventRepository
    match_fields = ["slug"]

    async def create(self, data: dict | Event) -> Event:
        """Create an event and enqueue search indexing.

        Args:
            data: Event data dictionary or Event instance

        Returns:
            Created event
        """
        event = await super().create(data)
        await self.repository.session.commit()

        index_key = await enqueue_task("index_event", event_id=str(event.id))
        if not index_key:
            logger.warning(f"Failed to enqueue search indexing for event {event.id}")

        return event

    async def update(
        self,
        data: dict | Event,
        item_id: UUID | None = None,
        **kwargs,
    ) -> Event:
        """Update an event and enqueue search indexing.

        Args:
            data: Event data dictionary or Event instance
            item_id: Event ID to update
            **kwargs: Additional keyword arguments

        Returns:
            Updated event
        """
        event = await super().update(data, item_id=item_id, **kwargs)
        await self.repository.session.commit()

        index_key = await enqueue_task("index_event", event_id=str(event.id))
        if not index_key:
            logger.warning(f"Failed to enqueue search indexing for event {event.id}")

        return event

    async def get_by_slug(self, slug: str) -> Event | None:
        """Get an event by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The event if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_by_calendar_id(self, calendar_id: UUID, limit: int = 100) -> list[Event]:
        """Get all events for a calendar.

        Args:
            calendar_id: The calendar ID to search for.
            limit: Maximum number of events to return.

        Returns:
            List of events.
        """
        return await self.repository.get_by_calendar_id(calendar_id, limit=limit)

    async def get_featured(self, calendar_id: UUID | None = None, limit: int = 10) -> list[Event]:
        """Get featured events.

        Args:
            calendar_id: Optional calendar ID to filter by.
            limit: Maximum number of events to return.

        Returns:
            List of featured events.
        """
        return await self.repository.get_featured(calendar_id=calendar_id, limit=limit)

    async def get_by_category_id(self, category_id: UUID, limit: int = 100) -> list[Event]:
        """Get all events for a category.

        Args:
            category_id: The category ID to search for.
            limit: Maximum number of events to return.

        Returns:
            List of events.
        """
        return await self.repository.get_by_category_id(category_id, limit=limit)

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
        return await self.repository.get_upcoming(
            calendar_id=calendar_id,
            start_date=start_date,
            limit=limit,
        )

    async def add_occurrence(
        self,
        event_id: UUID,
        dt_start: datetime.datetime,
        dt_end: datetime.datetime | None = None,
        *,
        all_day: bool = False,
    ) -> EventOccurrence:
        """Add an occurrence to an event.

        Args:
            event_id: The event ID.
            dt_start: The start datetime.
            dt_end: Optional end datetime.
            all_day: Whether this is an all-day event.

        Returns:
            The created occurrence.
        """
        async with EventOccurrenceRepository(session=self.repository.session) as occurrence_repo:
            occurrence = await occurrence_repo.add(
                EventOccurrence(
                    event_id=event_id,
                    dt_start=dt_start,
                    dt_end=dt_end,
                    all_day=all_day,
                )
            )
            await occurrence_repo.session.commit()
            return occurrence

    async def add_categories(self, event_id: UUID, category_ids: list[UUID]) -> Event:
        """Add categories to an event.

        Args:
            event_id: The event ID.
            category_ids: List of category IDs to add.

        Returns:
            The updated event.
        """
        event = await self.get(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        async with EventCategoryRepository(session=self.repository.session) as category_repo:
            categories = []
            for category_id in category_ids:
                category = await category_repo.get(category_id)
                if category:
                    categories.append(category)

            event.categories.extend(categories)
            await self.repository.session.commit()
            await self.repository.session.refresh(event)

        return event


class EventOccurrenceService(SQLAlchemyAsyncRepositoryService[EventOccurrence]):
    """Service for EventOccurrence business logic."""

    repository_type = EventOccurrenceRepository

    async def get_by_event_id(self, event_id: UUID) -> list[EventOccurrence]:
        """Get all occurrences for an event.

        Args:
            event_id: The event ID to search for.

        Returns:
            List of event occurrences.
        """
        return await self.repository.get_by_event_id(event_id)

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
        return await self.repository.get_next_occurrence(event_id, after=after)

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
        return await self.repository.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            calendar_id=calendar_id,
        )
