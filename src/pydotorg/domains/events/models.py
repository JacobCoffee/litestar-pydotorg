"""Events domain models."""

from __future__ import annotations

import datetime  # noqa: TC003 - needed for SQLAlchemy column type
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - needed for SQLAlchemy column type

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, ContentManageableMixin, NameSlugMixin

if TYPE_CHECKING:
    pass

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


class EventOccurrence(Base):
    __tablename__ = "event_occurrences"

    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    dt_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    dt_end: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)

    event: Mapped[Event] = relationship("Event", back_populates="occurrences", lazy="selectin")
