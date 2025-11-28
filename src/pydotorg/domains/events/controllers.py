"""Events domain API and page controllers."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

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
        """List all calendars with pagination."""
        calendars, _total = await calendar_service.list_and_count(limit_offset)
        return [CalendarRead.model_validate(calendar) for calendar in calendars]

    @get("/{calendar_id:uuid}")
    async def get_calendar(
        self,
        calendar_service: CalendarService,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> CalendarRead:
        """Get a calendar by ID."""
        calendar = await calendar_service.get(calendar_id)
        return CalendarRead.model_validate(calendar)

    @get("/slug/{slug:str}")
    async def get_calendar_by_slug(
        self,
        calendar_service: CalendarService,
        slug: Annotated[str, Parameter(title="Slug", description="The calendar slug")],
    ) -> CalendarRead:
        """Get a calendar by slug."""
        calendar = await calendar_service.get_by_slug(slug)
        if not calendar:
            raise NotFoundException(f"Calendar with slug {slug} not found")
        return CalendarRead.model_validate(calendar)

    @post("/")
    async def create_calendar(
        self,
        calendar_service: CalendarService,
        data: CalendarCreate,
    ) -> CalendarRead:
        """Create a new calendar."""
        calendar = await calendar_service.create(data.model_dump())
        return CalendarRead.model_validate(calendar)

    @put("/{calendar_id:uuid}")
    async def update_calendar(
        self,
        calendar_service: CalendarService,
        data: CalendarUpdate,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> CalendarRead:
        """Update a calendar."""
        update_data = data.model_dump(exclude_unset=True)
        calendar = await calendar_service.update(calendar_id, update_data)
        return CalendarRead.model_validate(calendar)

    @delete("/{calendar_id:uuid}")
    async def delete_calendar(
        self,
        calendar_service: CalendarService,
        calendar_id: Annotated[UUID, Parameter(title="Calendar ID", description="The calendar ID")],
    ) -> None:
        """Delete a calendar."""
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
        """List all event categories with pagination."""
        categories, _total = await event_category_service.list_and_count(limit_offset)
        return [EventCategoryRead.model_validate(category) for category in categories]

    @get("/{category_id:uuid}")
    async def get_category(
        self,
        event_category_service: EventCategoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> EventCategoryRead:
        """Get an event category by ID."""
        category = await event_category_service.get(category_id)
        return EventCategoryRead.model_validate(category)

    @get("/slug/{slug:str}")
    async def get_category_by_slug(
        self,
        event_category_service: EventCategoryService,
        slug: Annotated[str, Parameter(title="Slug", description="The category slug")],
    ) -> EventCategoryRead:
        """Get an event category by slug."""
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
        """List all categories for a calendar."""
        categories = await event_category_service.get_by_calendar_id(calendar_id)
        return [EventCategoryRead.model_validate(category) for category in categories]

    @post("/")
    async def create_category(
        self,
        event_category_service: EventCategoryService,
        data: EventCategoryCreate,
    ) -> EventCategoryRead:
        """Create a new event category."""
        category = await event_category_service.create(data.model_dump())
        return EventCategoryRead.model_validate(category)

    @delete("/{category_id:uuid}")
    async def delete_category(
        self,
        event_category_service: EventCategoryService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
    ) -> None:
        """Delete an event category."""
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
        """List all event locations with pagination."""
        locations, _total = await event_location_service.list_and_count(limit_offset)
        return [EventLocationRead.model_validate(location) for location in locations]

    @get("/{location_id:uuid}")
    async def get_location(
        self,
        event_location_service: EventLocationService,
        location_id: Annotated[UUID, Parameter(title="Location ID", description="The location ID")],
    ) -> EventLocationRead:
        """Get an event location by ID."""
        location = await event_location_service.get(location_id)
        return EventLocationRead.model_validate(location)

    @get("/slug/{slug:str}")
    async def get_location_by_slug(
        self,
        event_location_service: EventLocationService,
        slug: Annotated[str, Parameter(title="Slug", description="The location slug")],
    ) -> EventLocationRead:
        """Get an event location by slug."""
        location = await event_location_service.get_by_slug(slug)
        if not location:
            raise NotFoundException(f"Location with slug {slug} not found")
        return EventLocationRead.model_validate(location)

    @post("/")
    async def create_location(
        self,
        event_location_service: EventLocationService,
        data: EventLocationCreate,
    ) -> EventLocationRead:
        """Create a new event location."""
        location = await event_location_service.create(data.model_dump())
        return EventLocationRead.model_validate(location)

    @put("/{location_id:uuid}")
    async def update_location(
        self,
        event_location_service: EventLocationService,
        data: EventLocationUpdate,
        location_id: Annotated[UUID, Parameter(title="Location ID", description="The location ID")],
    ) -> EventLocationRead:
        """Update an event location."""
        update_data = data.model_dump(exclude_unset=True)
        location = await event_location_service.update(location_id, update_data)
        return EventLocationRead.model_validate(location)

    @delete("/{location_id:uuid}")
    async def delete_location(
        self,
        event_location_service: EventLocationService,
        location_id: Annotated[UUID, Parameter(title="Location ID", description="The location ID")],
    ) -> None:
        """Delete an event location."""
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
        """List all events with pagination."""
        events, _total = await event_service.list_and_count(limit_offset)
        return [EventList.model_validate(event) for event in events]

    @get("/{event_id:uuid}")
    async def get_event(
        self,
        event_service: EventService,
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> EventRead:
        """Get an event by ID."""
        event = await event_service.get(event_id)
        return EventRead.model_validate(event)

    @get("/slug/{slug:str}")
    async def get_event_by_slug(
        self,
        event_service: EventService,
        slug: Annotated[str, Parameter(title="Slug", description="The event slug")],
    ) -> EventWithRelations:
        """Get an event by slug with all relations."""
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
        """List all events for a calendar."""
        events = await event_service.get_by_calendar_id(calendar_id, limit=limit)
        return [EventList.model_validate(event) for event in events]

    @get("/category/{category_id:uuid}")
    async def list_events_by_category(
        self,
        event_service: EventService,
        category_id: Annotated[UUID, Parameter(title="Category ID", description="The category ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[EventList]:
        """List all events for a category."""
        events = await event_service.get_by_category_id(category_id, limit=limit)
        return [EventList.model_validate(event) for event in events]

    @get("/featured")
    async def list_featured_events(
        self,
        event_service: EventService,
        calendar_id: Annotated[UUID | None, Parameter(title="Calendar ID")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100)] = 10,
    ) -> list[EventWithRelations]:
        """List featured events."""
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
        """List upcoming events."""
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
        data: EventCreate,
    ) -> EventRead:
        """Create a new event."""
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
        data: EventUpdate,
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> EventRead:
        """Update an event."""
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
        """Delete an event."""
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
        """List all event occurrences with pagination."""
        occurrences, _total = await event_occurrence_service.list_and_count(limit_offset)
        return [EventOccurrenceRead.model_validate(occurrence) for occurrence in occurrences]

    @get("/{occurrence_id:uuid}")
    async def get_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        occurrence_id: Annotated[UUID, Parameter(title="Occurrence ID", description="The occurrence ID")],
    ) -> EventOccurrenceRead:
        """Get an event occurrence by ID."""
        occurrence = await event_occurrence_service.get(occurrence_id)
        return EventOccurrenceRead.model_validate(occurrence)

    @get("/event/{event_id:uuid}")
    async def list_occurrences_by_event(
        self,
        event_occurrence_service: EventOccurrenceService,
        event_id: Annotated[UUID, Parameter(title="Event ID", description="The event ID")],
    ) -> list[EventOccurrenceRead]:
        """List all occurrences for an event."""
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
        """List occurrences within a date range."""
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
        data: EventOccurrenceCreate,
    ) -> EventOccurrenceRead:
        """Create a new event occurrence."""
        occurrence = await event_occurrence_service.create(data.model_dump())
        return EventOccurrenceRead.model_validate(occurrence)

    @put("/{occurrence_id:uuid}")
    async def update_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        data: EventOccurrenceUpdate,
        occurrence_id: Annotated[UUID, Parameter(title="Occurrence ID", description="The occurrence ID")],
    ) -> EventOccurrenceRead:
        """Update an event occurrence."""
        update_data = data.model_dump(exclude_unset=True)
        occurrence = await event_occurrence_service.update(occurrence_id, update_data)
        return EventOccurrenceRead.model_validate(occurrence)

    @delete("/{occurrence_id:uuid}")
    async def delete_occurrence(
        self,
        event_occurrence_service: EventOccurrenceService,
        occurrence_id: Annotated[UUID, Parameter(title="Occurrence ID", description="The occurrence ID")],
    ) -> None:
        """Delete an event occurrence."""
        await event_occurrence_service.delete(occurrence_id)


class EventsPageController(Controller):
    """Controller for events HTML pages."""

    path = "/events"
    include_in_schema = False

    @get("/")
    async def events_index(
        self,
        event_service: EventService,
        calendar_service: CalendarService,
        event_category_service: EventCategoryService,
    ) -> Template:
        """Render the main events page."""
        upcoming_events = await event_service.get_upcoming(limit=20)
        featured_events = await event_service.get_featured(limit=5)
        calendars, _total = await calendar_service.list_and_count()

        return Template(
            template_name="events/index.html.jinja2",
            context={
                "upcoming_events": upcoming_events,
                "featured_events": featured_events,
                "calendars": calendars,
            },
        )

    @get("/calendar/")
    async def events_calendar_list(
        self,
        calendar_service: CalendarService,
    ) -> Template:
        """Render the calendars list page."""
        calendars, _total = await calendar_service.list_and_count()

        return Template(
            template_name="events/calendar_list.html.jinja2",
            context={
                "calendars": calendars,
            },
        )

    @get("/calendar/{slug:str}/")
    async def events_calendar_detail(
        self,
        slug: str,
        calendar_service: CalendarService,
        event_service: EventService,
        event_category_service: EventCategoryService,
    ) -> Template:
        """Render a specific calendar's events."""
        calendar = await calendar_service.get_by_slug(slug)
        if not calendar:
            raise NotFoundException(f"Calendar {slug} not found")

        events = await event_service.get_by_calendar_id(calendar.id)
        featured_events = await event_service.get_featured(calendar_id=calendar.id)
        categories = await event_category_service.get_by_calendar_id(calendar.id)

        return Template(
            template_name="events/calendar.html.jinja2",
            context={
                "calendar": calendar,
                "events": events,
                "featured_events": featured_events,
                "categories": categories,
            },
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
    ) -> str:
        """Generate iCalendar export for an event."""
        event = await event_service.get_by_slug(slug)
        if not event:
            raise NotFoundException(f"Event {slug} not found")

        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Python.org//Events//EN",
            "BEGIN:VEVENT",
            f"UID:{event.id}@python.org",
            f"SUMMARY:{event.title}",
        ]

        if event.description:
            ical_lines.append(f"DESCRIPTION:{event.description}")

        if event.venue:
            ical_lines.append(f"LOCATION:{event.venue.name}")

        for occurrence in event.occurrences:
            dt_start = occurrence.dt_start.strftime("%Y%m%dT%H%M%SZ")
            ical_lines.append(f"DTSTART:{dt_start}")

            if occurrence.dt_end:
                dt_end = occurrence.dt_end.strftime("%Y%m%dT%H%M%SZ")
                ical_lines.append(f"DTEND:{dt_end}")

        ical_lines.extend(["END:VEVENT", "END:VCALENDAR"])

        return "\r\n".join(ical_lines)
