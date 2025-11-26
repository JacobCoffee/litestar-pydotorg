"""Events domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class CalendarBase(BaseModel):
    """Base calendar schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]


class CalendarCreate(CalendarBase):
    """Schema for creating a new calendar."""

    creator_id: UUID | None = None


class CalendarUpdate(BaseModel):
    """Schema for updating a calendar."""

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None


class CalendarRead(CalendarBase):
    """Schema for reading calendar data."""

    id: UUID
    creator_id: UUID | None
    created: datetime.datetime
    updated: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EventCategoryBase(BaseModel):
    """Base event category schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]


class EventCategoryCreate(EventCategoryBase):
    """Schema for creating a new event category."""

    calendar_id: UUID


class EventCategoryRead(EventCategoryBase):
    """Schema for reading event category data."""

    id: UUID
    calendar_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EventLocationBase(BaseModel):
    """Base event location schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    address: str | None = None
    url: str | None = None


class EventLocationCreate(EventLocationBase):
    """Schema for creating a new event location."""


class EventLocationUpdate(BaseModel):
    """Schema for updating an event location."""

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    address: str | None = None
    url: str | None = None


class EventLocationRead(EventLocationBase):
    """Schema for reading event location data."""

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EventOccurrenceBase(BaseModel):
    """Base event occurrence schema with common fields."""

    dt_start: datetime.datetime
    dt_end: datetime.datetime | None = None
    all_day: bool = False


class EventOccurrenceCreate(EventOccurrenceBase):
    """Schema for creating a new event occurrence."""

    event_id: UUID


class EventOccurrenceUpdate(BaseModel):
    """Schema for updating an event occurrence."""

    dt_start: datetime.datetime | None = None
    dt_end: datetime.datetime | None = None
    all_day: bool | None = None


class EventOccurrenceRead(EventOccurrenceBase):
    """Schema for reading event occurrence data."""

    id: UUID
    event_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EventBase(BaseModel):
    """Base event schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    description: str | None = None
    featured: bool = False


class EventCreate(EventBase):
    """Schema for creating a new event."""

    calendar_id: UUID
    venue_id: UUID | None = None
    creator_id: UUID | None = None
    category_ids: list[UUID] = []
    occurrences: list[EventOccurrenceBase] = []


class EventUpdate(BaseModel):
    """Schema for updating an event."""

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    description: str | None = None
    venue_id: UUID | None = None
    featured: bool | None = None
    category_ids: list[UUID] | None = None


class EventRead(EventBase):
    """Schema for reading event data."""

    id: UUID
    calendar_id: UUID
    venue_id: UUID | None
    creator_id: UUID | None
    created: datetime.datetime
    updated: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EventWithRelations(EventRead):
    """Schema for event with all relations loaded."""

    venue: EventLocationRead | None = None
    categories: list[EventCategoryRead] = []
    occurrences: list[EventOccurrenceRead] = []

    model_config = ConfigDict(from_attributes=True)


class EventList(BaseModel):
    """Schema for event list items."""

    id: UUID
    name: str
    slug: str
    title: str
    featured: bool
    calendar_id: UUID
    next_occurrence: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EventCalendarPageData(BaseModel):
    """Schema for events calendar page template data."""

    calendar: CalendarRead | None
    events: list[EventWithRelations]
    categories: list[EventCategoryRead]
    featured_events: list[EventWithRelations]


class EventDetailPageData(BaseModel):
    """Schema for event detail page template data."""

    event: EventWithRelations
    calendar: CalendarRead
    related_events: list[EventList] = []
