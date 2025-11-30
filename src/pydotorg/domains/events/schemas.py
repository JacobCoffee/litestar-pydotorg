"""Events domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CalendarBase(BaseModel):
    """Base calendar schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]


class CalendarCreate(CalendarBase):
    """Schema for creating a new calendar."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Python Events", "slug": "python-events", "creator_id": None}}
    )

    creator_id: UUID | None = None


class CalendarUpdate(BaseModel):
    """Schema for updating a calendar."""

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Python Community Events"}})

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None


class CalendarRead(CalendarBase):
    """Schema for reading calendar data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440100",
                "name": "Python Events",
                "slug": "python-events",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "created": "2025-01-01T00:00:00Z",
                "updated": "2025-11-30T12:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-11-30T12:00:00Z",
            }
        },
    )

    id: UUID
    creator_id: UUID | None
    created: datetime.datetime
    updated: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime


class EventCategoryBase(BaseModel):
    """Base event category schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]


class EventCategoryCreate(EventCategoryBase):
    """Schema for creating a new event category."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Conferences",
                "slug": "conferences",
                "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
            }
        }
    )

    calendar_id: UUID


class EventCategoryRead(EventCategoryBase):
    """Schema for reading event category data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440300",
                "name": "Conferences",
                "slug": "conferences",
                "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
            }
        },
    )

    id: UUID
    calendar_id: UUID


class EventLocationBase(BaseModel):
    """Base event location schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    address: str | None = None
    url: str | None = None


class EventLocationCreate(EventLocationBase):
    """Schema for creating a new event location."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Pittsburgh Convention Center",
                "slug": "pittsburgh-convention-center",
                "address": "1000 Fort Duquesne Blvd, Pittsburgh, PA 15222",
                "url": "https://pittsburghcc.com",
            }
        }
    )


class EventLocationUpdate(BaseModel):
    """Schema for updating an event location."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "David L. Lawrence Convention Center",
                "address": "1000 Fort Duquesne Blvd, Pittsburgh, PA 15222",
            }
        }
    )

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    address: str | None = None
    url: str | None = None


class EventLocationRead(EventLocationBase):
    """Schema for reading event location data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440200",
                "name": "David L. Lawrence Convention Center",
                "slug": "david-l-lawrence-convention-center",
                "address": "1000 Fort Duquesne Blvd, Pittsburgh, PA 15222",
                "url": "https://pittsburghcc.com",
            }
        },
    )

    id: UUID


class EventOccurrenceBase(BaseModel):
    """Base event occurrence schema with common fields."""

    dt_start: datetime.datetime
    dt_end: datetime.datetime | None = None
    all_day: bool = False


class EventOccurrenceCreate(EventOccurrenceBase):
    """Schema for creating a new event occurrence."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dt_start": "2025-05-15T09:00:00Z",
                "dt_end": "2025-05-18T17:00:00Z",
                "all_day": False,
                "event_id": "550e8400-e29b-41d4-a716-446655440500",
            }
        }
    )

    event_id: UUID


class EventOccurrenceUpdate(BaseModel):
    """Schema for updating an event occurrence."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dt_start": "2025-05-16T09:00:00Z",
                "dt_end": "2025-05-19T17:00:00Z",
            }
        }
    )

    dt_start: datetime.datetime | None = None
    dt_end: datetime.datetime | None = None
    all_day: bool | None = None


class EventOccurrenceRead(EventOccurrenceBase):
    """Schema for reading event occurrence data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440600",
                "event_id": "550e8400-e29b-41d4-a716-446655440500",
                "dt_start": "2025-05-15T09:00:00Z",
                "dt_end": "2025-05-18T17:00:00Z",
                "all_day": False,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        },
    )

    id: UUID
    event_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


class EventBase(BaseModel):
    """Base event schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    description: str | None = None
    featured: bool = False


class EventCreate(EventBase):
    """Schema for creating a new event."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "PyCon US 2025",
                "slug": "pycon-us-2025",
                "title": "PyCon US 2025 - The Premier Python Conference",
                "description": "Join the largest annual gathering for the Python community! PyCon US 2025 features talks, tutorials, sprints, and networking opportunities for Python developers of all skill levels.",
                "featured": True,
                "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
                "venue_id": "550e8400-e29b-41d4-a716-446655440200",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "category_ids": [
                    "550e8400-e29b-41d4-a716-446655440300",
                    "550e8400-e29b-41d4-a716-446655440301",
                ],
                "occurrences": [
                    {
                        "dt_start": "2025-05-15T09:00:00Z",
                        "dt_end": "2025-05-18T17:00:00Z",
                        "all_day": False,
                    }
                ],
            }
        }
    )

    calendar_id: UUID
    venue_id: UUID | None = None
    creator_id: UUID | None = None
    category_ids: list[UUID] = []
    occurrences: list[EventOccurrenceBase] = []


class EventUpdate(BaseModel):
    """Schema for updating an event."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "PyCon US 2025 - The Premier Python Conference (Updated)",
                "description": "Updated description for the largest annual gathering for the Python community!",
                "featured": True,
            }
        }
    )

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    description: str | None = None
    venue_id: UUID | None = None
    featured: bool | None = None
    category_ids: list[UUID] | None = None


class EventRead(EventBase):
    """Schema for reading event data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440500",
                "name": "PyCon US 2025",
                "slug": "pycon-us-2025",
                "title": "PyCon US 2025 - The Premier Python Conference",
                "description": "Join the largest annual gathering for the Python community! PyCon US 2025 features talks, tutorials, sprints, and networking opportunities for Python developers of all skill levels.",
                "featured": True,
                "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
                "venue_id": "550e8400-e29b-41d4-a716-446655440200",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "created": "2025-01-15T10:00:00Z",
                "updated": "2025-11-20T14:30:00Z",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-11-20T14:30:00Z",
            }
        },
    )

    id: UUID
    calendar_id: UUID
    venue_id: UUID | None
    creator_id: UUID | None
    created: datetime.datetime
    updated: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime


class EventWithRelations(EventRead):
    """Schema for event with all relations loaded."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440500",
                "name": "PyCon US 2025",
                "slug": "pycon-us-2025",
                "title": "PyCon US 2025 - The Premier Python Conference",
                "description": "Join the largest annual gathering for the Python community!",
                "featured": True,
                "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
                "venue_id": "550e8400-e29b-41d4-a716-446655440200",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "created": "2025-01-15T10:00:00Z",
                "updated": "2025-11-20T14:30:00Z",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-11-20T14:30:00Z",
                "venue": {
                    "id": "550e8400-e29b-41d4-a716-446655440200",
                    "name": "David L. Lawrence Convention Center",
                    "slug": "david-l-lawrence-convention-center",
                    "address": "1000 Fort Duquesne Blvd, Pittsburgh, PA 15222",
                    "url": "https://pittsburghcc.com",
                },
                "categories": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440300",
                        "name": "Conferences",
                        "slug": "conferences",
                        "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
                    }
                ],
                "occurrences": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440600",
                        "event_id": "550e8400-e29b-41d4-a716-446655440500",
                        "dt_start": "2025-05-15T09:00:00Z",
                        "dt_end": "2025-05-18T17:00:00Z",
                        "all_day": False,
                        "created_at": "2025-01-15T10:00:00Z",
                        "updated_at": "2025-01-15T10:00:00Z",
                    }
                ],
            }
        },
    )

    venue: EventLocationRead | None = None
    categories: list[EventCategoryRead] = []
    occurrences: list[EventOccurrenceRead] = []


class EventList(BaseModel):
    """Schema for event list items."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440500",
                "name": "PyCon US 2025",
                "slug": "pycon-us-2025",
                "title": "PyCon US 2025 - The Premier Python Conference",
                "featured": True,
                "calendar_id": "550e8400-e29b-41d4-a716-446655440100",
                "next_occurrence": "2025-05-15T09:00:00Z",
            }
        },
    )

    id: UUID
    name: str
    slug: str
    title: str
    featured: bool
    calendar_id: UUID
    next_occurrence: datetime.datetime | None = None


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
