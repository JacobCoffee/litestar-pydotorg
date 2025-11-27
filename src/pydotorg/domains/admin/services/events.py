"""Admin event management service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from pydotorg.domains.events.models import Calendar, Event, EventOccurrence
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EventAdminService:
    """Service for admin event management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_events(
        self,
        limit: int = 20,
        offset: int = 0,
        calendar_id: UUID | None = None,
        *,
        featured: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Event], int]:
        """List events with filtering and pagination.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            calendar_id: Filter by calendar ID
            featured: Filter by featured status
            search: Search query for event name/title/description

        Returns:
            Tuple of (events list, total count)
        """
        query = select(Event).options(
            selectinload(Event.calendar),
            selectinload(Event.venue),
            selectinload(Event.categories),
            selectinload(Event.occurrences),
        )

        if calendar_id:
            query = query.where(Event.calendar_id == calendar_id)

        if featured is not None:
            query = query.where(Event.featured == featured)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Event.name.ilike(search_term),
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Event.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        events = list(result.scalars().all())

        return events, total

    async def list_calendars(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> tuple[list[Calendar], int]:
        """List calendars with filtering and pagination.

        Args:
            limit: Maximum number of calendars to return
            offset: Number of calendars to skip
            search: Search query for calendar name

        Returns:
            Tuple of (calendars list, total count)
        """
        query = select(Calendar)

        if search:
            search_term = f"%{search}%"
            query = query.where(Calendar.name.ilike(search_term))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Calendar.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        calendars = list(result.scalars().all())

        return calendars, total

    async def get_event(self, event_id: UUID) -> Event | None:
        """Get an event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event if found, None otherwise
        """
        query = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                selectinload(Event.calendar),
                selectinload(Event.venue),
                selectinload(Event.categories),
                selectinload(Event.occurrences),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_calendar(self, calendar_id: UUID) -> Calendar | None:
        """Get a calendar by ID.

        Args:
            calendar_id: Calendar ID

        Returns:
            Calendar if found, None otherwise
        """
        query = select(Calendar).where(Calendar.id == calendar_id).options(selectinload(Calendar.events))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def feature_event(self, event_id: UUID) -> Event | None:
        """Feature an event.

        Features the event and triggers search indexing to update
        the featured status in search results.

        Args:
            event_id: Event ID

        Returns:
            Updated event if found, None otherwise
        """
        event = await self.get_event(event_id)
        if not event:
            return None

        event.featured = True
        await self.session.commit()
        await self.session.refresh(event)

        index_key = await enqueue_task("index_event", event_id=str(event.id))
        if not index_key:
            logger.warning(f"Failed to enqueue search indexing for event {event.id}")

        return event

    async def unfeature_event(self, event_id: UUID) -> Event | None:
        """Unfeature an event.

        Unfeatures the event and triggers search indexing to update
        the featured status in search results.

        Args:
            event_id: Event ID

        Returns:
            Updated event if found, None otherwise
        """
        event = await self.get_event(event_id)
        if not event:
            return None

        event.featured = False
        await self.session.commit()
        await self.session.refresh(event)

        index_key = await enqueue_task("index_event", event_id=str(event.id))
        if not index_key:
            logger.warning(f"Failed to enqueue search indexing for event {event.id}")

        return event

    async def get_stats(self) -> dict:
        """Get event statistics.

        Returns:
            Dictionary with event stats
        """
        total_events_query = select(func.count()).select_from(Event)
        total_events_result = await self.session.execute(total_events_query)
        total_events = total_events_result.scalar() or 0

        total_calendars_query = select(func.count()).select_from(Calendar)
        total_calendars_result = await self.session.execute(total_calendars_query)
        total_calendars = total_calendars_result.scalar() or 0

        featured_query = select(func.count()).where(Event.featured)
        featured_result = await self.session.execute(featured_query)
        featured_events = featured_result.scalar() or 0

        now = datetime.now(tz=UTC)
        upcoming_query = select(func.count(func.distinct(EventOccurrence.event_id))).where(
            EventOccurrence.dt_start >= now
        )
        upcoming_result = await self.session.execute(upcoming_query)
        upcoming_events = upcoming_result.scalar() or 0

        return {
            "total_events": total_events,
            "total_calendars": total_calendars,
            "featured_events": featured_events,
            "upcoming_events": upcoming_events,
        }
