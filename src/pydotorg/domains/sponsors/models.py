"""Sponsors domain models."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - needed for SQLAlchemy column type

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, ContentManageableMixin, NameSlugMixin

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User


class SponsorshipStatus(StrEnum):
    APPLIED = "applied"
    REJECTED = "rejected"
    APPROVED = "approved"
    FINALIZED = "finalized"


class SponsorshipLevel(AuditBase, NameSlugMixin):
    __tablename__ = "sponsorship_levels"

    order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    sponsorship_amount: Mapped[int] = mapped_column(Integer, default=0)
    logo_dimension: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sponsorships: Mapped[list[Sponsorship]] = relationship(
        "Sponsorship",
        back_populates="level",
        lazy="noload",
    )


class Sponsor(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "sponsors"

    description: Mapped[str] = mapped_column(Text, default="")
    landing_page_url: Mapped[str] = mapped_column(String(500), default="")
    twitter_handle: Mapped[str] = mapped_column(String(100), default="")
    linked_in_page_url: Mapped[str] = mapped_column(String(500), default="")
    web_logo: Mapped[str] = mapped_column(String(500), default="")
    print_logo: Mapped[str] = mapped_column(String(500), default="")
    primary_phone: Mapped[str] = mapped_column(String(50), default="")
    mailing_address_line_1: Mapped[str] = mapped_column(String(255), default="")
    mailing_address_line_2: Mapped[str] = mapped_column(String(255), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    state: Mapped[str] = mapped_column(String(100), default="")
    postal_code: Mapped[str] = mapped_column(String(20), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    country_of_incorporation: Mapped[str] = mapped_column(String(100), default="")
    state_of_incorporation: Mapped[str] = mapped_column(String(100), default="")

    sponsorships: Mapped[list[Sponsorship]] = relationship(
        "Sponsorship",
        back_populates="sponsor",
        lazy="noload",
    )

    @property
    def full_address(self) -> str:
        parts = [
            self.mailing_address_line_1,
            self.mailing_address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(p for p in parts if p)


class Sponsorship(AuditBase, ContentManageableMixin):
    __tablename__ = "sponsorships"

    sponsor_id: Mapped[UUID] = mapped_column(ForeignKey("sponsors.id", ondelete="CASCADE"))
    level_id: Mapped[UUID] = mapped_column(ForeignKey("sponsorship_levels.id", ondelete="CASCADE"))
    submitted_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[SponsorshipStatus] = mapped_column(
        Enum(SponsorshipStatus),
        default=SponsorshipStatus.APPLIED,
        index=True,
    )
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    start_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    applied_on: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    approved_on: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    rejected_on: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    finalized_on: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sponsorship_fee: Mapped[int] = mapped_column(Numeric(10, 2), default=0)
    for_modified_package: Mapped[bool] = mapped_column(Boolean, default=False)
    renewal: Mapped[bool] = mapped_column(Boolean, default=False)

    sponsor: Mapped[Sponsor] = relationship("Sponsor", back_populates="sponsorships", lazy="selectin")
    level: Mapped[SponsorshipLevel] = relationship("SponsorshipLevel", back_populates="sponsorships", lazy="selectin")
    submitted_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[submitted_by_id],
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        if not self.start_date or not self.end_date:
            return False
        today = datetime.datetime.now(tz=datetime.UTC).date()
        return self.status == SponsorshipStatus.FINALIZED and self.start_date <= today <= self.end_date
