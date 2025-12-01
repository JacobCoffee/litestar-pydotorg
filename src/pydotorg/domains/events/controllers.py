"""Events domain API and page controllers."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, Request, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.openapi import ResponseSpec
from litestar.params import Body, Parameter
from litestar.response import Response, Template

from pydotorg.core.ical import ICalendarService
from pydotorg.domains.events.schemas import (
    CalendarCreate,
    CalendarRead,
    CalendarUpdate,
    EventCategoryCreate,
    EventCategoryRead,
    EventCreate,
    EventList,
    EventLocationCreate,
    EventLocationRead,
    EventLocationUpdate,
    EventOccurrenceCreate,
    EventOccurrenceRead,
    EventOccurrenceUpdate,
    EventRead,
    EventUpdate,
    EventWithRelations,
)
from pydotorg.domains.events.services import (
    CalendarService,
    EventCategoryService,
    EventLocationService,
    EventOccurrenceService,
    EventService,
)


class CalendarController(Controller):
    """Controller for Calendar CRUD operations."""

    path = "/api/v1/calendars"
    tags = ["Events"]

    @get("/")
    async def list_calendars(
        self,
        calendar_service: CalendarService,
        limit_offset: LimitOffset,
    ) -> list[CalendarRead]:
        """List all event calendars with pagination.

        Retrieves a paginated list of calendars used to organize events by
        community or topic (e.g., Python Conferences, Local Meetups).

        Args:
            calendar_service: Service for calendar database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of calendars with their names and descriptions.
        """
        calendars, _total = await calendar_service.list_and_count(limit_offset)
        return [CalendarRead.model_validate(calendar) for calendar in calendars]

    @get(
        "/{calendar_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Calendar not found"),
        },
    )
    async def get_calendar(
        self,
        calendar_service: CalendarService,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> CalendarRead:
        """Retrieve a specific calendar by its unique identifier.

        Fetches complete calendar information including name, description,
        and associated metadata.

        Args:
            calendar_service: Service for calendar database operations.
            calendar_id: The unique UUID identifier of the calendar.

        Returns:
            Complete calendar details.

        Raises:
            NotFoundException: If no calendar with the given ID exists.
        """
        calendar = await calendar_service.get(calendar_id)
        return CalendarRead.model_validate(calendar)

    @get("/slug/{slug:str}")
    async def get_calendar_by_slug(
        self,
        calendar_service: CalendarService,
        slug: Annotated[str, Parameter(title="Slug", description="The calendar slug")],
    ) -> CalendarRead:
        """Look up a calendar by its URL slug.

        Searches for a calendar with the specified slug and returns its details.
        Slugs are URL-friendly identifiers used in calendar page URLs.

        Args:
            calendar_service: Service for calendar database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete calendar details.

        Raises:
            NotFoundException: If no calendar with the given slug exists.
        """
        calendar = await calendar_service.get_by_slug(slug)
        if not calendar:
            raise NotFoundException(f"Calendar with slug {slug} not found")
        return CalendarRead.model_validate(calendar)

    @post("/")
    async def create_calendar(
        self,
        calendar_service: CalendarService,
        data: Annotated[CalendarCreate, Body(title="Calendar", description="Calendar to create")],
    ) -> CalendarRead:
        """Create a new event calendar.

        Creates a new calendar for organizing related events. Calendars can
        be used to group events by community, topic, or region.

        Args:
            calendar_service: Service for calendar database operations.
            data: Calendar creation payload with name and description.

        Returns:
            The newly created calendar.

        Raises:
            ConflictError: If a calendar with the same slug exists.
        """
        calendar = await calendar_service.create(data.model_dump())
        return CalendarRead.model_validate(calendar)

    @put("/{calendar_id:uuid}")
    async def update_calendar(
        self,
        calendar_service: CalendarService,
        data: Annotated[CalendarUpdate, Body(title="Calendar", description="Calendar data to update")],
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> CalendarRead:
        """Update an existing calendar.

        Modifies calendar fields with the provided values. Changes to name
        or description are immediately reflected.

        Args:
            calendar_service: Service for calendar database operations.
            data: Partial calendar update payload with fields to modify.
            calendar_id: The unique UUID identifier of the calendar to update.

        Returns:
            The updated calendar with all current fields.

        Raises:
            NotFoundException: If no calendar with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        calendar = await calendar_service.update(calendar_id, update_data)
        return CalendarRead.model_validate(calendar)

    @delete("/{calendar_id:uuid}")
    async def delete_calendar(
        self,
        calendar_service: CalendarService,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> None:
        """Delete an event calendar.

        Permanently removes a calendar and disassociates its events. Events
        are not deleted but will need to be reassigned to another calendar.

        Args:
            calendar_service: Service for calendar database operations.
            calendar_id: The unique UUID identifier of the calendar to delete.

        Raises:
            NotFoundException: If no calendar with the given ID exists.
        """
        await calendar_service.delete(calendar_id)


class EventCategoryController(Controller):
    """Controller for EventCategory CRUD operations."""

    path = "/api/v1/event-categories"
    tags = ["Events"]

    @get("/")
    async def list_categories(
        self,
        event_category_service: EventCategoryService,
        limit_offset: LimitOffset,
    ) -> list[EventCategoryRead]:
        """List all event categories with pagination.

        Retrieves a paginated list of event categories used to classify
        events by type (e.g., Conference, Workshop, Meetup).

        Args:
            event_category_service: Service for event category operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of event categories with their names and slugs.
        """
        categories, _total = await event_category_service.list_and_count(limit_offset)
        return [EventCategoryRead.model_validate(category) for category in categories]

    @get("/{category_id:uuid}")
    async def get_category(
        self,
        event_category_service: EventCategoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> EventCategoryRead:
        """Retrieve a specific event category by its unique identifier.

        Fetches complete event category information including name and
        associated calendar.

        Args:
            event_category_service: Service for event category operations.
            category_id: The unique UUID identifier of the category.

        Returns:
            Complete event category details.

        Raises:
            NotFoundException: If no category with the given ID exists.
        """
        category = await event_category_service.get(category_id)
        return EventCategoryRead.model_validate(category)

    @get("/slug/{slug:str}")
    async def get_category_by_slug(
        self,
        event_category_service: EventCategoryService,
        slug: Annotated[str, Parameter(title="Slug", description="The category slug")],
    ) -> EventCategoryRead:
        """Look up an event category by its URL slug.

        Searches for a category with the specified slug and returns its details.
        Slugs are URL-friendly identifiers used in category URLs.

        Args:
            event_category_service: Service for event category operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete event category details.

        Raises:
            NotFoundException: If no category with the given slug exists.
        """
        category = await event_category_service.get_by_slug(slug)
        if not category:
            raise NotFoundException(f"Category with slug {slug} not found")
        return EventCategoryRead.model_validate(category)

    @get("/calendar/{calendar_id:uuid}")
    async def list_categories_by_calendar(
        self,
        event_category_service: EventCategoryService,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> list[EventCategoryRead]:
        """List all event categories for a specific calendar.

        Retrieves categories that are associated with the specified calendar.
        Useful for filtering events within a calendar context.

        Args:
            event_category_service: Service for event category operations.
            calendar_id: The unique UUID identifier of the calendar.

        Returns:
            List of event categories for the specified calendar.
        """
        categories = await event_category_service.get_by_calendar_id(calendar_id)
        return [EventCategoryRead.model_validate(category) for category in categories]

    @post("/")
    async def create_category(
        self,
        event_category_service: EventCategoryService,
        data: Annotated[EventCategoryCreate, Body(title="Event Category", description="Event category to create")],
    ) -> EventCategoryRead:
        """Create a new event category.

        Creates a new category for classifying events within a calendar.
        Categories help users filter and find relevant events.

        Args:
            event_category_service: Service for event category operations.
            data: Event category creation payload with name and calendar ID.

        Returns:
            The newly created event category.

        Raises:
            ConflictError: If a category with the same slug exists.
        """
        category = await event_category_service.create(data.model_dump())
        return EventCategoryRead.model_validate(category)

    @delete("/{category_id:uuid}")
    async def delete_category(
        self,
        event_category_service: EventCategoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> None:
        """Delete an event category.

        Permanently removes an event category from the system. Events using
        this category will be disassociated but not deleted.

        Args:
            event_category_service: Service for event category operations.
            category_id: The unique UUID identifier of the category to delete.

        Raises:
            NotFoundException: If no category with the given ID exists.
        """
        await event_category_service.delete(category_id)


class EventLocationController(Controller):
    """Controller for EventLocation CRUD operations."""

    path = "/api/v1/event-locations"
    tags = ["Events"]

    @get("/")
    async def list_locations(
        self,
        event_location_service: EventLocationService,
        limit_offset: LimitOffset,
    ) -> list[EventLocationRead]:
        """List all event locations with pagination.

        Retrieves a paginated list of venues and locations where events
        are held. Includes both physical and virtual venue information.

        Args:
            event_location_service: Service for event location operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of event locations with addresses and details.
        """
        locations, _total = await event_location_service.list_and_count(limit_offset)
        return [EventLocationRead.model_validate(location) for location in locations]

    @get(
        "/{location_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Event location not found"),
        },
    )
    async def get_location(
        self,
        event_location_service: EventLocationService,
        location_id: Annotated[UUID, Parameter(title="Location ID", description="The location ID")],
    ) -> EventLocationRead:
        """Retrieve a specific event location by its unique identifier.

        Fetches complete location information including name, address,
        coordinates, and capacity details.

        Args:
            event_location_service: Service for event location operations.
            location_id: The unique UUID identifier of the location.

        Returns:
            Complete event location details.

        Raises:
            NotFoundException: If no location with the given ID exists.
        """
        location = await event_location_service.get(location_id)
        return EventLocationRead.model_validate(location)

    @get("/slug/{slug:str}")
    async def get_location_by_slug(
        self,
        event_location_service: EventLocationService,
        slug: Annotated[str, Parameter(title="Slug", description="The location slug")],
    ) -> EventLocationRead:
        """Look up an event location by its URL slug.

        Searches for a location with the specified slug and returns its details.
        Slugs are URL-friendly identifiers used in location URLs.

        Args:
            event_location_service: Service for event location operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete event location details.

        Raises:
            NotFoundException: If no location with the given slug exists.
        """
        location = await event_location_service.get_by_slug(slug)
        if not location:
            raise NotFoundException(f"Location with slug {slug} not found")
        return EventLocationRead.model_validate(location)

    @post("/")
    async def create_location(
        self,
        event_location_service: EventLocationService,
        data: Annotated[EventLocationCreate, Body(title="Event Location", description="Event location to create")],
    ) -> EventLocationRead:
        """Create a new event location.

        Creates a new venue or location record for hosting events. Supports
        both physical venues with addresses and virtual event locations.

        Args:
            event_location_service: Service for event location operations.
            data: Event location creation payload with name and address.

        Returns:
            The newly created event location.

        Raises:
            ConflictError: If a location with the same slug exists.
        """
        location = await event_location_service.create(data.model_dump())
        return EventLocationRead.model_validate(location)

    @put("/{location_id:uuid}")
    async def update_location(
        self,
        event_location_service: EventLocationService,
        data: Annotated[EventLocationUpdate, Body(title="Event Location", description="Event location data to update")],
        location_id: Annotated[UUID, Parameter(title="Location ID", description="The location ID")],
    ) -> EventLocationRead:
        """Update an existing event location.

        Modifies location fields with the provided values. Can update name,
        address, coordinates, and capacity information.

        Args:
            event_location_service: Service for event location operations.
            data: Partial location update payload with fields to modify.
            location_id: The unique UUID identifier of the location to update.

        Returns:
            The updated location with all current fields.

        Raises:
            NotFoundException: If no location with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        location = await event_location_service.update(location_id, update_data)
        return EventLocationRead.model_validate(location)

    @delete("/{location_id:uuid}")
    async def delete_location(
        self,
        event_location_service: EventLocationService,
        location_id: Annotated[UUID, Parameter(title="Location ID", description="The location ID")],
    ) -> None:
        """Delete an event location.

        Permanently removes an event location from the system. Events using
        this location will be disassociated but not deleted.

        Args:
            event_location_service: Service for event location operations.
            location_id: The unique UUID identifier of the location to delete.

        Raises:
            NotFoundException: If no location with the given ID exists.
        """
        await event_location_service.delete(location_id)


class EventController(Controller):
    """Controller for Event CRUD operations."""

    path = "/api/v1/events"
    tags = ["Events"]

    @get("/")
    async def list_events(
        self,
        event_service: EventService,
        limit_offset: LimitOffset,
    ) -> list[EventList]:
        """List all events with pagination.

        Retrieves a paginated list of events across all calendars. Returns
        summary information suitable for listing views.

        Args:
            event_service: Service for event database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of events with summary information.
        """
        events, _total = await event_service.list_and_count(limit_offset)
        return [EventList.model_validate(event) for event in events]

    @get(
        "/{event_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Event not found"),
        },
    )
    async def get_event(
        self,
        event_service: EventService,
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> EventRead:
        """Retrieve a specific event by its unique identifier.

        Fetches complete event information including title, description,
        dates, location, and organizer details.

        Args:
            event_service: Service for event database operations.
            event_id: The unique UUID identifier of the event.

        Returns:
            Complete event details.

        Raises:
            NotFoundException: If no event with the given ID exists.
        """
        event = await event_service.get(event_id)
        return EventRead.model_validate(event)

    @get("/slug/{slug:str}")
    async def get_event_by_slug(
        self,
        event_service: EventService,
        slug: Annotated[str, Parameter(title="Slug", description="The event slug")],
    ) -> EventWithRelations:
        """Look up an event by its URL slug with all relations.

        Fetches complete event information including related calendar,
        categories, occurrences, and venue details.

        Args:
            event_service: Service for event database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete event details with all related entities.

        Raises:
            NotFoundException: If no event with the given slug exists.
        """
        event = await event_service.get_by_slug(slug)
        if not event:
            raise NotFoundException(f"Event with slug {slug} not found")
        return EventWithRelations.model_validate(event)

    @get("/calendar/{calendar_id:uuid}")
    async def list_events_by_calendar(
        self,
        event_service: EventService,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[EventList]:
        """List all events for a specific calendar.

        Retrieves events associated with the specified calendar. Useful for
        displaying events within a single calendar context.

        Args:
            event_service: Service for event database operations.
            calendar_id: The unique UUID identifier of the calendar.
            limit: Maximum number of events to return (1-1000).

        Returns:
            List of events for the specified calendar.
        """
        events = await event_service.get_by_calendar_id(calendar_id, limit=limit)
        return [EventList.model_validate(event) for event in events]

    @get("/category/{category_id:uuid}")
    async def list_events_by_category(
        self,
        event_service: EventService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[EventList]:
        """List all events for a specific category.

        Retrieves events classified under the specified category. Useful for
        filtering events by type (e.g., conferences, workshops).

        Args:
            event_service: Service for event database operations.
            category_id: The unique UUID identifier of the category.
            limit: Maximum number of events to return (1-1000).

        Returns:
            List of events for the specified category.
        """
        events = await event_service.get_by_category_id(category_id, limit=limit)
        return [EventList.model_validate(event) for event in events]

    @get("/featured")
    async def list_featured_events(
        self,
        event_service: EventService,
        calendar_id: Annotated[UUID | None, Parameter(title="Calendar ID")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100)] = 10,
    ) -> list[EventWithRelations]:
        """List featured events for homepage display.

        Retrieves events marked as featured for promotional display. Can be
        filtered by calendar for context-specific featuring.

        Args:
            event_service: Service for event database operations.
            calendar_id: Optional calendar filter for featured events.
            limit: Maximum number of events to return (1-100).

        Returns:
            List of featured events with full details.
        """
        events = await event_service.get_featured(calendar_id=calendar_id, limit=limit)
        return [EventWithRelations.model_validate(event) for event in events]

    @get("/upcoming")
    async def list_upcoming_events(
        self,
        event_service: EventService,
        calendar_id: Annotated[UUID | None, Parameter(title="Calendar ID")] = None,
        start_date: Annotated[datetime.datetime | None, Parameter(title="Start date")] = None,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[EventWithRelations]:
        """List upcoming events from the current date.

        Retrieves events with occurrences in the future, sorted by start date.
        Can be filtered by calendar and custom start date.

        Args:
            event_service: Service for event database operations.
            calendar_id: Optional calendar filter for upcoming events.
            start_date: Custom start date for the upcoming window.
            limit: Maximum number of events to return (1-1000).

        Returns:
            List of upcoming events with full details.
        """
        events = await event_service.get_upcoming(
            calendar_id=calendar_id,
            start_date=start_date,
            limit=limit,
        )
        return [EventWithRelations.model_validate(event) for event in events]

    @post("/")
    async def create_event(
        self,
        event_service: EventService,
        data: Annotated[EventCreate, Body(title="Event", description="Event to create")],
    ) -> EventRead:
        """Create a new event with occurrences.

        Creates a new event with the specified details, including title,
        description, calendar assignment, categories, and occurrence dates.

        Args:
            event_service: Service for event database operations.
            data: Event creation payload with all event details.

        Returns:
            The newly created event.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        event_data = data.model_dump(exclude={"category_ids", "occurrences"})
        event = await event_service.create(event_data)

        if data.category_ids:
            await event_service.add_categories(event.id, data.category_ids)

        for occurrence_data in data.occurrences:
            await event_service.add_occurrence(
                event_id=event.id,
                dt_start=occurrence_data.dt_start,
                dt_end=occurrence_data.dt_end,
                all_day=occurrence_data.all_day,
            )

        return EventRead.model_validate(event)

    @put("/{event_id:uuid}")
    async def update_event(
        self,
        event_service: EventService,
        data: Annotated[EventUpdate, Body(title="Event", description="Event data to update")],
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> EventRead:
        """Update an existing event.

        Modifies event fields with the provided values. Can update title,
        description, categories, and other event details.

        Args:
            event_service: Service for event database operations.
            data: Partial event update payload with fields to modify.
            event_id: The unique UUID identifier of the event to update.

        Returns:
            The updated event with all current fields.

        Raises:
            NotFoundException: If no event with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True, exclude={"category_ids"})
        event = await event_service.update(event_id, update_data)

        if data.category_ids is not None:
            await event_service.add_categories(event_id, data.category_ids)

        return EventRead.model_validate(event)

    @delete("/{event_id:uuid}")
    async def delete_event(
        self,
        event_service: EventService,
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> None:
        """Permanently delete an event.

        Removes an event and all its occurrences from the system.
        This action is irreversible.

        Args:
            event_service: Service for event database operations.
            event_id: The unique UUID identifier of the event to delete.

        Raises:
            NotFoundException: If no event with the given ID exists.
        """
        await event_service.delete(event_id)


class EventOccurrenceController(Controller):
    """Controller for EventOccurrence CRUD operations."""

    path = "/api/v1/event-occurrences"
    tags = ["Events"]

    @get("/")
    async def list_occurrences(
        self,
        event_occurrence_service: EventOccurrenceService,
        limit_offset: LimitOffset,
    ) -> list[EventOccurrenceRead]:
        """List all event occurrences with pagination.

        Retrieves a paginated list of event occurrences. Occurrences represent
        specific dates/times when an event takes place.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of event occurrences with date and time details.
        """
        occurrences, _total = await event_occurrence_service.list_and_count(limit_offset)
        return [EventOccurrenceRead.model_validate(occurrence) for occurrence in occurrences]

    @get(
        "/{occurrence_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Event occurrence not found"),
        },
    )
    async def get_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        occurrence_id: Annotated[UUID, Parameter(title="Occurrence ID", description="The occurrence ID")],
    ) -> EventOccurrenceRead:
        """Retrieve a specific event occurrence by its unique identifier.

        Fetches complete occurrence information including start time, end time,
        and all-day flag.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            occurrence_id: The unique UUID identifier of the occurrence.

        Returns:
            Complete event occurrence details.

        Raises:
            NotFoundException: If no occurrence with the given ID exists.
        """
        occurrence = await event_occurrence_service.get(occurrence_id)
        return EventOccurrenceRead.model_validate(occurrence)

    @get("/event/{event_id:uuid}")
    async def list_occurrences_by_event(
        self,
        event_occurrence_service: EventOccurrenceService,
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> list[EventOccurrenceRead]:
        """List all occurrences for a specific event.

        Retrieves all date/time occurrences for an event. Useful for events
        that repeat on multiple dates.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            event_id: The unique UUID identifier of the event.

        Returns:
            List of occurrences for the specified event.
        """
        occurrences = await event_occurrence_service.get_by_event_id(event_id)
        return [EventOccurrenceRead.model_validate(occurrence) for occurrence in occurrences]

    @get("/range")
    async def list_occurrences_by_date_range(
        self,
        event_occurrence_service: EventOccurrenceService,
        start_date: Annotated[datetime.datetime, Parameter(title="Start date")],
        end_date: Annotated[datetime.datetime, Parameter(title="End date")],
        calendar_id: Annotated[UUID | None, Parameter(title="Calendar ID")] = None,
    ) -> list[EventOccurrenceRead]:
        """List event occurrences within a date range.

        Retrieves occurrences falling within the specified date range. Useful
        for calendar views and date-based filtering.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).
            calendar_id: Optional calendar filter.

        Returns:
            List of occurrences within the specified date range.
        """
        occurrences = await event_occurrence_service.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            calendar_id=calendar_id,
        )
        return [EventOccurrenceRead.model_validate(occurrence) for occurrence in occurrences]

    @post("/")
    async def create_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        data: Annotated[
            EventOccurrenceCreate, Body(title="Event Occurrence", description="Event occurrence to create")
        ],
    ) -> EventOccurrenceRead:
        """Create a new event occurrence.

        Adds a new date/time occurrence to an existing event. Useful for
        adding additional dates to repeating events.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            data: Event occurrence creation payload with date/time details.

        Returns:
            The newly created event occurrence.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        occurrence = await event_occurrence_service.create(data.model_dump())
        return EventOccurrenceRead.model_validate(occurrence)

    @put("/{occurrence_id:uuid}")
    async def update_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        data: Annotated[
            EventOccurrenceUpdate, Body(title="Event Occurrence", description="Event occurrence data to update")
        ],
        occurrence_id: Annotated[UUID, Parameter(title="Occurrence ID", description="The occurrence ID")],
    ) -> EventOccurrenceRead:
        """Update an existing event occurrence.

        Modifies occurrence fields with the provided values. Can update
        start time, end time, and all-day status.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            data: Partial occurrence update payload with fields to modify.
            occurrence_id: The unique UUID identifier of the occurrence to update.

        Returns:
            The updated occurrence with all current fields.

        Raises:
            NotFoundException: If no occurrence with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        occurrence = await event_occurrence_service.update(occurrence_id, update_data)
        return EventOccurrenceRead.model_validate(occurrence)

    @delete("/{occurrence_id:uuid}")
    async def delete_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        occurrence_id: Annotated[UUID, Parameter(title="Occurrence ID", description="The occurrence ID")],
    ) -> None:
        """Delete an event occurrence.

        Permanently removes an event occurrence from the system. The parent
        event remains intact with its other occurrences.

        Args:
            event_occurrence_service: Service for event occurrence operations.
            occurrence_id: The unique UUID identifier of the occurrence to delete.

        Raises:
            NotFoundException: If no occurrence with the given ID exists.
        """
        await event_occurrence_service.delete(occurrence_id)


class EventsPageController(Controller):
    """Controller for events HTML pages."""

    path = "/events"
    include_in_schema = False

    @get("/")
    async def events_index(
        self,
        request: Request,
        event_service: EventService,
        calendar_service: CalendarService,
        event_category_service: EventCategoryService,
    ) -> Template:
        """Render the main events page."""
        upcoming_events = await event_service.get_upcoming(limit=20)
        featured_events = await event_service.get_featured(limit=5)
        calendars, _total = await calendar_service.list_and_count()

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"

        context = {
            "upcoming_events": upcoming_events,
            "featured_events": featured_events,
            "calendars": calendars,
        }

        if is_htmx and not is_boosted:
            return Template(
                template_name="events/partials/events_content.html.jinja2",
                context=context,
            )

        return Template(
            template_name="events/index.html.jinja2",
            context=context,
        )

    @get("/calendar/")
    async def events_calendar_list(
        self,
        request: Request,
        calendar_service: CalendarService,
        event_service: EventService,
    ) -> Template:
        """Render the calendars list page."""
        calendars, _total = await calendar_service.list_and_count()

        calendars_with_counts = []
        for calendar_obj in calendars:
            events = await event_service.get_by_calendar_id(calendar_obj.id, limit=1000)
            calendars_with_counts.append(
                {
                    "calendar": calendar_obj,
                    "event_count": len(events),
                }
            )

        context = {
            "calendars": calendars_with_counts,
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"
        if is_htmx and not is_boosted:
            return Template(
                template_name="events/partials/calendar_list_content.html.jinja2",
                context=context,
            )

        return Template(
            template_name="events/calendar_list.html.jinja2",
            context=context,
        )

    @get("/calendar/{slug:str}/")
    async def events_calendar_detail(
        self,
        request: Request,
        slug: str,
        calendar_service: CalendarService,
        event_service: EventService,
        event_category_service: EventCategoryService,
        event_occurrence_service: EventOccurrenceService,
        date: Annotated[str | None, Parameter(description="Date to view (YYYY-MM-DD)")] = None,
        view: Annotated[str | None, Parameter(description="View type (month/week/list)")] = None,
    ) -> Template:
        """Render a specific calendar's events with calendar grid."""
        import calendar as cal  # noqa: PLC0415

        calendar_obj = await calendar_service.get_by_slug(slug)
        if not calendar_obj:
            raise NotFoundException(f"Calendar {slug} not found")

        now = datetime.datetime.now(tz=datetime.UTC)
        if date:
            try:
                current_date = datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=datetime.UTC)
            except ValueError:
                current_date = now
        else:
            current_date = now

        events = await event_service.get_by_calendar_id(calendar_obj.id)
        featured_events = await event_service.get_featured(calendar_id=calendar_obj.id)
        categories = await event_category_service.get_by_calendar_id(calendar_obj.id)

        first_day = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, days_in_month = cal.monthrange(current_date.year, current_date.month)
        last_day = first_day.replace(day=days_in_month, hour=23, minute=59, second=59)

        occurrences = await event_occurrence_service.get_by_date_range(
            start_date=first_day - datetime.timedelta(days=7),
            end_date=last_day + datetime.timedelta(days=7),
            calendar_id=calendar_obj.id,
        )

        events_by_date: dict[datetime.date, list] = {}
        for occ in occurrences:
            occ_date = occ.dt_start.date()
            if occ_date not in events_by_date:
                events_by_date[occ_date] = []
            events_by_date[occ_date].append(occ.event)

        calendar_data = []
        start_weekday = first_day.weekday()
        days_before = (start_weekday + 1) % 7

        for i in range(days_before):
            d = first_day - datetime.timedelta(days=days_before - i)
            day_events = events_by_date.get(d.date(), [])
            calendar_data.append(
                {
                    "date": d,
                    "is_today": d.date() == now.date(),
                    "in_month": False,
                    "events": day_events,
                    "event_count": len(day_events),
                }
            )

        for day in range(1, days_in_month + 1):
            d = first_day.replace(day=day)
            day_events = events_by_date.get(d.date(), [])
            calendar_data.append(
                {
                    "date": d,
                    "is_today": d.date() == now.date(),
                    "in_month": True,
                    "events": day_events,
                    "event_count": len(day_events),
                }
            )

        remaining = (7 - len(calendar_data) % 7) % 7
        for i in range(1, remaining + 1):
            d = last_day + datetime.timedelta(days=i)
            day_events = events_by_date.get(d.date(), [])
            calendar_data.append(
                {
                    "date": d,
                    "is_today": d.date() == now.date(),
                    "in_month": False,
                    "events": day_events,
                    "event_count": len(day_events),
                }
            )

        week_data = []
        days_since_sunday = (current_date.weekday() + 1) % 7
        week_start = current_date - datetime.timedelta(days=days_since_sunday)

        for i in range(7):
            d = week_start + datetime.timedelta(days=i)
            day_events = events_by_date.get(d.date(), [])
            week_data.append(
                {
                    "date": d,
                    "is_today": d.date() == now.date(),
                    "events": day_events,
                    "event_count": len(day_events),
                }
            )

        context = {
            "calendar": calendar_obj,
            "events": events,
            "featured_events": featured_events,
            "categories": categories,
            "current_date": current_date,
            "timedelta": datetime.timedelta,
            "calendar_data": calendar_data,
            "week_data": week_data,
            "view": view or "month",
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"

        if is_htmx and not is_boosted:
            return Template(
                template_name="events/partials/calendar_view.html.jinja2",
                context=context,
            )

        return Template(
            template_name="events/calendar.html.jinja2",
            context=context,
        )

    @get("/{slug:str}/")
    async def event_detail(
        self,
        slug: str,
        event_service: EventService,
        calendar_service: CalendarService,
    ) -> Template:
        """Render the event detail page."""
        event = await event_service.get_by_slug(slug)
        if not event:
            raise NotFoundException(f"Event {slug} not found")

        calendar = await calendar_service.get(event.calendar_id)
        related_events = await event_service.get_by_calendar_id(event.calendar_id, limit=5)

        return Template(
            template_name="events/detail.html.jinja2",
            context={
                "event": event,
                "calendar": calendar,
                "related_events": related_events,
            },
        )

    @get("/submit/")
    async def event_submit(self) -> Template:
        """Render the event submission form."""
        return Template(
            template_name="events/submit.html.jinja2",
            context={},
        )

    @get("/{slug:str}/ical/")
    async def event_icalendar(
        self,
        slug: str,
        event_service: EventService,
    ) -> Response[bytes]:
        """Download iCalendar (.ics) file for a single event.

        Generates an RFC 5545 compliant iCalendar file containing all occurrences
        of the specified event. Can be imported into calendar applications.
        """
        event = await event_service.get_by_slug(slug)
        if not event:
            raise NotFoundException(f"Event {slug} not found")

        ical_service = ICalendarService()
        ical_data = ical_service.generate_event_ical(event)

        filename = f"{event.slug or 'event'}.ics"
        return Response(
            content=ical_data.encode("utf-8"),
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    @get("/calendar.ics")
    async def calendar_feed(
        self,
        event_service: EventService,
    ) -> Response[bytes]:
        """Download iCalendar feed for all upcoming events.

        Generates an RFC 5545 compliant iCalendar feed containing upcoming
        Python community events. Subscribe to this feed in your calendar app.
        """
        events = await event_service.get_upcoming(limit=500)

        ical_service = ICalendarService()
        ical_data = ical_service.generate_upcoming_feed(
            events=events,
            title="Python Community Events",
        )

        return Response(
            content=ical_data.encode("utf-8"),
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="python-events.ics"',
            },
        )

    @get("/calendar/{slug:str}/calendar.ics")
    async def calendar_specific_feed(
        self,
        slug: str,
        calendar_service: CalendarService,
        event_service: EventService,
    ) -> Response[bytes]:
        """Download iCalendar feed for a specific calendar.

        Generates an RFC 5545 compliant iCalendar feed containing events
        from the specified calendar. Subscribe to this feed in your calendar app.
        """
        calendar = await calendar_service.get_by_slug(slug)
        if not calendar:
            raise NotFoundException(f"Calendar {slug} not found")

        events = await event_service.get_by_calendar_id(calendar.id, limit=500)

        ical_service = ICalendarService()
        ical_data = ical_service.generate_calendar_feed(
            calendar=calendar,
            events=events,
        )

        filename = f"{calendar.slug or 'calendar'}-events.ics"
        return Response(
            content=ical_data.encode("utf-8"),
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
