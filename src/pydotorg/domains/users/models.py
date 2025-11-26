"""User domain models."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from pydotorg.domains.sponsors.models import Sponsorship

VOTE_AFFIRMATION_DAYS = 365


class SearchVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


class EmailPrivacy(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    NEVER = "never"


class MembershipType(StrEnum):
    BASIC = "basic"
    SUPPORTING = "supporting"
    SPONSOR = "sponsor"
    MANAGING = "managing"
    CONTRIBUTING = "contributing"
    FELLOW = "fellow"


class UserGroupType(StrEnum):
    MEETUP = "meetup"
    DISTRIBUTION_LIST = "distribution_list"
    OTHER = "other"


class User(UUIDAuditBase):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(150), default="")
    last_name: Mapped[str] = mapped_column(String(150), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    date_joined: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    last_login: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    bio: Mapped[str] = mapped_column(Text, default="")
    search_visibility: Mapped[SearchVisibility] = mapped_column(
        Enum(SearchVisibility, values_callable=lambda x: [e.value for e in x]),
        default=SearchVisibility.PUBLIC,
    )
    email_privacy: Mapped[EmailPrivacy] = mapped_column(
        Enum(EmailPrivacy, values_callable=lambda x: [e.value for e in x]),
        default=EmailPrivacy.PRIVATE,
    )
    public_profile: Mapped[bool] = mapped_column(Boolean, default=True)

    membership: Mapped[Membership | None] = relationship(
        "Membership",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    sponsorships: Mapped[list[Sponsorship]] = relationship(
        "Sponsorship",
        foreign_keys="[Sponsorship.submitted_by_id]",
        back_populates="submitted_by",
        lazy="noload",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_membership(self) -> bool:
        return self.membership is not None


class Membership(UUIDAuditBase):
    __tablename__ = "memberships"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    membership_type: Mapped[MembershipType] = mapped_column(
        Enum(MembershipType, values_callable=lambda x: [e.value for e in x]),
        default=MembershipType.BASIC,
    )
    legal_name: Mapped[str] = mapped_column(String(255), default="")
    preferred_name: Mapped[str] = mapped_column(String(255), default="")
    email_address: Mapped[str] = mapped_column(String(254), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    region: Mapped[str] = mapped_column(String(100), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    postal_code: Mapped[str] = mapped_column(String(20), default="")
    psf_code_of_conduct: Mapped[bool] = mapped_column(Boolean, default=False)
    psf_announcements: Mapped[bool] = mapped_column(Boolean, default=False)
    votes: Mapped[bool] = mapped_column(Boolean, default=False)
    last_vote_affirmation: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="membership")

    @property
    def higher_level_member(self) -> bool:
        return self.membership_type != MembershipType.BASIC

    @property
    def needs_vote_affirmation(self) -> bool:
        if not self.last_vote_affirmation:
            return True
        today = datetime.datetime.now(tz=datetime.UTC).date()
        days_since = (today - self.last_vote_affirmation).days
        return days_since > VOTE_AFFIRMATION_DAYS


class UserGroup(UUIDAuditBase):
    __tablename__ = "user_groups"

    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    url_type: Mapped[UserGroupType] = mapped_column(
        Enum(UserGroupType, values_callable=lambda x: [e.value for e in x]),
        default=UserGroupType.OTHER,
    )
    start_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted: Mapped[bool] = mapped_column(Boolean, default=False)
