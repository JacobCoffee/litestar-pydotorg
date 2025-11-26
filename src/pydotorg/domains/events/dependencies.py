"""Events domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_calendar_repository(db_session: AsyncSession) -> AsyncGenerator[CalendarRepository, None]:
    """Provide a CalendarRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A CalendarRepository instance.
    """
    async with CalendarRepository(session=db_session) as repo:
        yield repo


async def provide_calendar_service(
    calendar_repository: CalendarRepository,
) -> AsyncGenerator[CalendarService, None]:
    """Provide a CalendarService instance.

    Args:
        calendar_repository: The calendar repository.

    Yields:
        A CalendarService instance.
    """
    async with CalendarService(repository=calendar_repository) as service:
        yield service


async def provide_event_category_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[EventCategoryRepository, None]:
    """Provide an EventCategoryRepository instance.

    Args:
        db_session: The database session.

    Yields:
        An EventCategoryRepository instance.
    """
    async with EventCategoryRepository(session=db_session) as repo:
        yield repo


async def provide_event_category_service(
    event_category_repository: EventCategoryRepository,
) -> AsyncGenerator[EventCategoryService, None]:
    """Provide an EventCategoryService instance.

    Args:
        event_category_repository: The event category repository.

    Yields:
        An EventCategoryService instance.
    """
    async with EventCategoryService(repository=event_category_repository) as service:
        yield service


async def provide_event_location_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[EventLocationRepository, None]:
    """Provide an EventLocationRepository instance.

    Args:
        db_session: The database session.

    Yields:
        An EventLocationRepository instance.
    """
    async with EventLocationRepository(session=db_session) as repo:
        yield repo


async def provide_event_location_service(
    event_location_repository: EventLocationRepository,
) -> AsyncGenerator[EventLocationService, None]:
    """Provide an EventLocationService instance.

    Args:
        event_location_repository: The event location repository.

    Yields:
        An EventLocationService instance.
    """
    async with EventLocationService(repository=event_location_repository) as service:
        yield service


async def provide_event_repository(db_session: AsyncSession) -> AsyncGenerator[EventRepository, None]:
    """Provide an EventRepository instance.

    Args:
        db_session: The database session.

    Yields:
        An EventRepository instance.
    """
    async with EventRepository(session=db_session) as repo:
        yield repo


async def provide_event_service(
    event_repository: EventRepository,
) -> AsyncGenerator[EventService, None]:
    """Provide an EventService instance.

    Args:
        event_repository: The event repository.

    Yields:
        An EventService instance.
    """
    async with EventService(repository=event_repository) as service:
        yield service


async def provide_event_occurrence_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[EventOccurrenceRepository, None]:
    """Provide an EventOccurrenceRepository instance.

    Args:
        db_session: The database session.

    Yields:
        An EventOccurrenceRepository instance.
    """
    async with EventOccurrenceRepository(session=db_session) as repo:
        yield repo


async def provide_event_occurrence_service(
    event_occurrence_repository: EventOccurrenceRepository,
) -> AsyncGenerator[EventOccurrenceService, None]:
    """Provide an EventOccurrenceService instance.

    Args:
        event_occurrence_repository: The event occurrence repository.

    Yields:
        An EventOccurrenceService instance.
    """
    async with EventOccurrenceService(repository=event_occurrence_repository) as service:
        yield service


def get_events_dependencies() -> dict:
    """Get all events domain dependency providers.

    Returns:
        Dictionary of dependency providers for the events domain.
    """
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
