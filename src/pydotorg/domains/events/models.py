"""Events domain models."""

from __future__ import annotations

import datetime
from enum import IntEnum
from uuid import UUID

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, YEARLY
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Interval, SmallInteger, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, ContentManageableMixin, NameSlugMixin


class RecurrenceFrequency(IntEnum):
    """Recurrence frequency for recurring events.

    Values match dateutil.rrule constants for compatibility.
    """

    YEARLY = YEARLY
    MONTHLY = MONTHLY
    WEEKLY = WEEKLY
    DAILY = DAILY

    @property
    def label(self) -> str:
        """Get human-readable label for frequency."""
        labels = {
            YEARLY: "year(s)",
            MONTHLY: "month(s)",
            WEEKLY: "week(s)",
            DAILY: "day(s)",
        }
        return labels[self.value]


event_event_categories = Table(
    "event_event_categories",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("event_categories.id", ondelete="CASCADE"), primary_key=True),
)


class Calendar(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "calendars"

    events: Mapped[list[Event]] = relationship(
        "Event",
        back_populates="calendar",
        cascade="all, delete-orphan",
        lazy="noload",
    )


class EventCategory(Base, NameSlugMixin):
    __tablename__ = "event_categories"

    calendar_id: Mapped[UUID] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"))

    calendar: Mapped[Calendar] = relationship("Calendar", lazy="selectin")
    events: Mapped[list[Event]] = relationship(
        "Event",
        secondary=event_event_categories,
        back_populates="categories",
        lazy="noload",
    )


class EventLocation(Base, NameSlugMixin):
    __tablename__ = "event_locations"

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    events: Mapped[list[Event]] = relationship("Event", back_populates="venue", lazy="noload")


class Event(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "events"

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    calendar_id: Mapped[UUID] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"))
    venue_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("event_locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    calendar: Mapped[Calendar] = relationship("Calendar", back_populates="events", lazy="selectin")
    venue: Mapped[EventLocation | None] = relationship("EventLocation", back_populates="events", lazy="selectin")
    categories: Mapped[list[EventCategory]] = relationship(
        "EventCategory",
        secondary=event_event_categories,
        back_populates="events",
        lazy="selectin",
    )
    occurrences: Mapped[list[EventOccurrence]] = relationship(
        "EventOccurrence",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recurring_rules: Mapped[list[RecurringRule]] = relationship(
        "RecurringRule",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EventOccurrence(Base):
    __tablename__ = "event_occurrences"

    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    dt_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    dt_end: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)

    event: Mapped[Event] = relationship("Event", back_populates="occurrences", lazy="selectin")


class RecurringRule(Base):
    """Recurring event rule using dateutil.rrule.

    Defines a pattern for repeating events (e.g., every week, every month).
    Uses dateutil.rrule internally to generate occurrence datetimes.
    """

    __tablename__ = "event_recurring_rules"

    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    begin: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    finish: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration: Mapped[datetime.timedelta] = mapped_column(Interval, default=datetime.timedelta(minutes=15))
    interval: Mapped[int] = mapped_column(SmallInteger, default=1)
    frequency: Mapped[int] = mapped_column(SmallInteger, default=WEEKLY)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)

    event: Mapped[Event] = relationship("Event", back_populates="recurring_rules", lazy="selectin")

    def to_rrule(self):
        """Convert to dateutil rrule object for occurrence generation.

        Returns:
            rrule: Configured dateutil rrule object
        """
        from dateutil.rrule import rrule as make_rrule

        return make_rrule(
            freq=self.frequency.value,
            interval=self.interval,
            dtstart=self.begin,
            until=self.finish,
        )

    @property
    def dt_start(self) -> datetime.datetime:
        """Get the next occurrence start time.

        Returns:
            Next occurrence datetime or current time if no more occurrences
        """
        now = datetime.datetime.now(tz=datetime.UTC)
        recurrence = self.to_rrule().after(now)
        return recurrence if recurrence else now

    @property
    def dt_end(self) -> datetime.datetime:
        """Get the next occurrence end time.

        Returns:
            Next occurrence end datetime (start + duration)
        """
        return self.dt_start + self.duration

    @property
    def single_day(self) -> bool:
        """Check if occurrence spans a single day.

        Returns:
            True if start and end are on the same date
        """
        return self.dt_start.date() == self.dt_end.date()

    @property
    def freq_interval_as_timedelta(self) -> datetime.timedelta:
        """Get the approximate timedelta between occurrences.

        Returns:
            Timedelta representing the recurrence interval
        """
        timedelta_frequencies = {
            YEARLY: datetime.timedelta(days=365),
            MONTHLY: datetime.timedelta(days=30),
            WEEKLY: datetime.timedelta(days=7),
            DAILY: datetime.timedelta(days=1),
        }
        return self.interval * timedelta_frequencies[self.frequency]

    @property
    def frequency_enum(self) -> RecurrenceFrequency:
        """Get frequency as enum for display purposes."""
        return RecurrenceFrequency(self.frequency)
