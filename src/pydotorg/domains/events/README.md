# Events Domain

The Events domain manages calendars, events, event categories, locations, and occurrences for the Python.org events system.

## Models

### Calendar
- Primary container for organizing events
- Has a creator (User) and multiple events
- Uses name/slug pattern for URL-friendly identification

### EventCategory
- Categorizes events within a calendar
- Supports many-to-many relationship with events
- Linked to specific calendar

### EventLocation
- Represents physical or virtual event venues
- Optional address and URL fields
- Reusable across multiple events

### Event
- Core event entity with title, description
- Belongs to one calendar
- Can have multiple categories
- Optional venue (location)
- Featured flag for highlighting
- Contains multiple occurrences

### EventOccurrence
- Represents specific date/time for an event
- Supports recurring events (multiple occurrences per event)
- Includes start/end datetime and all-day flag
- Cascade deletes with parent event

## Architecture

```
events/
├── __init__.py          # Public API exports
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── repositories.py      # Database access layer
├── services.py          # Business logic layer
├── dependencies.py      # Dependency injection
├── controllers.py       # API and HTML endpoints
├── urls.py              # URL constants
└── README.md            # This file
```

## API Endpoints

### Calendars
- `GET /api/v1/calendars` - List calendars
- `GET /api/v1/calendars/{id}` - Get calendar by ID
- `GET /api/v1/calendars/slug/{slug}` - Get calendar by slug
- `POST /api/v1/calendars` - Create calendar
- `PUT /api/v1/calendars/{id}` - Update calendar
- `DELETE /api/v1/calendars/{id}` - Delete calendar

### Event Categories
- `GET /api/v1/event-categories` - List categories
- `GET /api/v1/event-categories/{id}` - Get category by ID
- `GET /api/v1/event-categories/slug/{slug}` - Get category by slug
- `GET /api/v1/event-categories/calendar/{calendar_id}` - List categories by calendar
- `POST /api/v1/event-categories` - Create category
- `DELETE /api/v1/event-categories/{id}` - Delete category

### Event Locations
- `GET /api/v1/event-locations` - List locations
- `GET /api/v1/event-locations/{id}` - Get location by ID
- `GET /api/v1/event-locations/slug/{slug}` - Get location by slug
- `POST /api/v1/event-locations` - Create location
- `PUT /api/v1/event-locations/{id}` - Update location
- `DELETE /api/v1/event-locations/{id}` - Delete location

### Events
- `GET /api/v1/events` - List events
- `GET /api/v1/events/{id}` - Get event by ID
- `GET /api/v1/events/slug/{slug}` - Get event by slug
- `GET /api/v1/events/calendar/{calendar_id}` - List events by calendar
- `GET /api/v1/events/category/{category_id}` - List events by category
- `GET /api/v1/events/featured` - List featured events
- `GET /api/v1/events/upcoming` - List upcoming events
- `POST /api/v1/events` - Create event
- `PUT /api/v1/events/{id}` - Update event
- `DELETE /api/v1/events/{id}` - Delete event

### Event Occurrences
- `GET /api/v1/event-occurrences` - List occurrences
- `GET /api/v1/event-occurrences/{id}` - Get occurrence by ID
- `GET /api/v1/event-occurrences/event/{event_id}` - List occurrences by event
- `GET /api/v1/event-occurrences/range` - List occurrences by date range
- `POST /api/v1/event-occurrences` - Create occurrence
- `PUT /api/v1/event-occurrences/{id}` - Update occurrence
- `DELETE /api/v1/event-occurrences/{id}` - Delete occurrence

## HTML Pages

- `GET /events/` - Main events listing page
- `GET /events/calendar/` - Calendars list page
- `GET /events/calendar/{slug}/` - Calendar detail page with events
- `GET /events/{slug}/` - Event detail page
- `GET /events/submit/` - Event submission form
- `GET /events/{slug}/ical/` - iCalendar export for event

## Key Features

### Multiple Calendar Support
The system supports multiple event calendars, each with its own categories and events. This allows for organizing events by different communities or focus areas.

### Recurring Events
Events can have multiple occurrences, supporting both one-time and recurring events. Each occurrence has its own start/end datetime.

### Category Filtering
Events can be tagged with multiple categories, enabling filtering and organization within calendars.

### Featured Events
Events can be marked as featured for prominent display on listing pages.

### iCalendar Export
Individual events can be exported to iCalendar format for importing into calendar applications.

## Usage Examples

### Creating an Event with Occurrences

```python
event_data = EventCreate(
    name="Python Conference 2025",
    slug="python-conference-2025",
    title="Python Conference 2025",
    description="Annual Python conference",
    calendar_id=calendar_id,
    venue_id=venue_id,
    featured=True,
    category_ids=[category_id_1, category_id_2],
    occurrences=[
        EventOccurrenceBase(
            dt_start=datetime(2025, 6, 1, 9, 0),
            dt_end=datetime(2025, 6, 1, 17, 0),
            all_day=False,
        ),
        EventOccurrenceBase(
            dt_start=datetime(2025, 6, 2, 9, 0),
            dt_end=datetime(2025, 6, 2, 17, 0),
            all_day=False,
        ),
    ],
)
event = await event_service.create(event_data.model_dump())
```

### Querying Upcoming Events

```python
upcoming_events = await event_service.get_upcoming(
    calendar_id=calendar_id,
    start_date=datetime.now(),
    limit=10,
)
```

### Getting Events by Date Range

```python
occurrences = await event_occurrence_service.get_by_date_range(
    start_date=datetime(2025, 6, 1),
    end_date=datetime(2025, 6, 30),
    calendar_id=calendar_id,
)
```

## Database Schema

The events domain uses the following tables:
- `calendars` - Calendar definitions
- `event_categories` - Event category definitions
- `event_locations` - Location/venue definitions
- `events` - Event definitions
- `event_occurrences` - Specific event date/times
- `event_event_categories` - Many-to-many join table

All models use UUID primary keys and include audit timestamps (created_at, updated_at).
