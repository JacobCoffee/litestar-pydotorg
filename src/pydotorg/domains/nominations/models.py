"""Nominations domain models."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - needed for SQLAlchemy column type

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, SlugMixin

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User


class ElectionStatus(StrEnum):
    UPCOMING = "upcoming"
    NOMINATIONS_OPEN = "nominations_open"
    VOTING_OPEN = "voting_open"
    CLOSED = "closed"


class Election(AuditBase, SlugMixin):
    __tablename__ = "elections"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    nominations_open: Mapped[datetime.date] = mapped_column(Date, index=True)
    nominations_close: Mapped[datetime.date] = mapped_column(Date, index=True)
    voting_open: Mapped[datetime.date] = mapped_column(Date, index=True)
    voting_close: Mapped[datetime.date] = mapped_column(Date, index=True)

    nominees: Mapped[list[Nominee]] = relationship(
        "Nominee",
        back_populates="election",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def status(self) -> ElectionStatus:
        today = datetime.datetime.now(tz=datetime.UTC).date()
        if today < self.nominations_open:
            return ElectionStatus.UPCOMING
        if today <= self.nominations_close:
            return ElectionStatus.NOMINATIONS_OPEN
        if today < self.voting_open:
            return ElectionStatus.UPCOMING
        if today <= self.voting_close:
            return ElectionStatus.VOTING_OPEN
        return ElectionStatus.CLOSED


class Nominee(AuditBase):
    __tablename__ = "nominees"

    election_id: Mapped[UUID] = mapped_column(ForeignKey("elections.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    election: Mapped[Election] = relationship("Election", back_populates="nominees", lazy="selectin")
    user: Mapped[User] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    nominations: Mapped[list[Nomination]] = relationship(
        "Nomination",
        back_populates="nominee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Nomination(AuditBase):
    __tablename__ = "nominations"

    nominee_id: Mapped[UUID] = mapped_column(ForeignKey("nominees.id", ondelete="CASCADE"))
    nominator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    endorsement: Mapped[str | None] = mapped_column(Text, nullable=True)

    nominee: Mapped[Nominee] = relationship("Nominee", back_populates="nominations", lazy="selectin")
    nominator: Mapped[User] = relationship("User", foreign_keys=[nominator_id], lazy="selectin")
