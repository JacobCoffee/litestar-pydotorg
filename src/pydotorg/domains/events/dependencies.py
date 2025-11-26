"""Events domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.events.repositories import (
    CalendarRepository,
    EventCategoryRepository,
    EventLocationRepository,
    EventOccurrenceRepository,
    EventRepository,
)
from pydotorg.domains.events.services import (
    CalendarService,
    EventCategoryService,
    EventLocationService,
    EventOccurrenceService,
    EventService,
)

if TYPE_CHECKING:
    pass


async def provide_calendar_repository(db_session: AsyncSession) -> CalendarRepository:
    """Provide a CalendarRepository instance."""
    return CalendarRepository(session=db_session)


async def provide_calendar_service(db_session: AsyncSession) -> CalendarService:
    """Provide a CalendarService instance."""
    return CalendarService(session=db_session)


async def provide_event_category_repository(db_session: AsyncSession) -> EventCategoryRepository:
    """Provide an EventCategoryRepository instance."""
    return EventCategoryRepository(session=db_session)


async def provide_event_category_service(db_session: AsyncSession) -> EventCategoryService:
    """Provide an EventCategoryService instance."""
    return EventCategoryService(session=db_session)


async def provide_event_location_repository(db_session: AsyncSession) -> EventLocationRepository:
    """Provide an EventLocationRepository instance."""
    return EventLocationRepository(session=db_session)


async def provide_event_location_service(db_session: AsyncSession) -> EventLocationService:
    """Provide an EventLocationService instance."""
    return EventLocationService(session=db_session)


async def provide_event_repository(db_session: AsyncSession) -> EventRepository:
    """Provide an EventRepository instance."""
    return EventRepository(session=db_session)


async def provide_event_service(db_session: AsyncSession) -> EventService:
    """Provide an EventService instance."""
    return EventService(session=db_session)


async def provide_event_occurrence_repository(db_session: AsyncSession) -> EventOccurrenceRepository:
    """Provide an EventOccurrenceRepository instance."""
    return EventOccurrenceRepository(session=db_session)


async def provide_event_occurrence_service(db_session: AsyncSession) -> EventOccurrenceService:
    """Provide an EventOccurrenceService instance."""
    return EventOccurrenceService(session=db_session)


def get_events_dependencies() -> dict:
    """Get all events domain dependency providers."""
    return {
        "calendar_repository": provide_calendar_repository,
        "calendar_service": provide_calendar_service,
        "event_category_repository": provide_event_category_repository,
        "event_category_service": provide_event_category_service,
        "event_location_repository": provide_event_location_repository,
        "event_location_service": provide_event_location_service,
        "event_repository": provide_event_repository,
        "event_service": provide_event_service,
        "event_occurrence_repository": provide_event_occurrence_repository,
        "event_occurrence_service": provide_event_occurrence_service,
    }
