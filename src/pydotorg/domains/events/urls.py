"""Events domain URL constants."""

from typing import Final

CALENDARS: Final[str] = "/api/v1/calendars"
CALENDAR_BY_ID: Final[str] = "/api/v1/calendars/{calendar_id:uuid}"
CALENDAR_BY_SLUG: Final[str] = "/api/v1/calendars/slug/{slug:str}"

EVENT_CATEGORIES: Final[str] = "/api/v1/event-categories"
EVENT_CATEGORY_BY_ID: Final[str] = "/api/v1/event-categories/{category_id:uuid}"
EVENT_CATEGORY_BY_SLUG: Final[str] = "/api/v1/event-categories/slug/{slug:str}"
CATEGORIES_BY_CALENDAR: Final[str] = "/api/v1/calendars/{calendar_id:uuid}/categories"

EVENT_LOCATIONS: Final[str] = "/api/v1/event-locations"
EVENT_LOCATION_BY_ID: Final[str] = "/api/v1/event-locations/{location_id:uuid}"
EVENT_LOCATION_BY_SLUG: Final[str] = "/api/v1/event-locations/slug/{slug:str}"

EVENTS: Final[str] = "/api/v1/events"
EVENT_BY_ID: Final[str] = "/api/v1/events/{event_id:uuid}"
EVENT_BY_SLUG: Final[str] = "/api/v1/events/slug/{slug:str}"
EVENTS_BY_CALENDAR: Final[str] = "/api/v1/calendars/{calendar_id:uuid}/events"
EVENTS_BY_CATEGORY: Final[str] = "/api/v1/event-categories/{category_id:uuid}/events"
FEATURED_EVENTS: Final[str] = "/api/v1/events/featured"
UPCOMING_EVENTS: Final[str] = "/api/v1/events/upcoming"

EVENT_OCCURRENCES: Final[str] = "/api/v1/event-occurrences"
EVENT_OCCURRENCE_BY_ID: Final[str] = "/api/v1/event-occurrences/{occurrence_id:uuid}"
OCCURRENCES_BY_EVENT: Final[str] = "/api/v1/events/{event_id:uuid}/occurrences"
OCCURRENCES_BY_DATE_RANGE: Final[str] = "/api/v1/event-occurrences/range"

EVENTS_INDEX: Final[str] = "/events/"
EVENTS_CALENDAR: Final[str] = "/events/calendar/"
EVENTS_CALENDAR_BY_SLUG: Final[str] = "/events/calendar/{slug:str}/"
EVENT_DETAIL: Final[str] = "/events/{slug:str}/"
EVENT_SUBMIT: Final[str] = "/events/submit/"
EVENT_ICALENDAR: Final[str] = "/events/{slug:str}/ical/"
