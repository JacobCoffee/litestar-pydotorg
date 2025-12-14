"""Sponsors domain models."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, ContentManageableMixin, NameSlugMixin

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User


class SponsorshipStatus(StrEnum):
    APPLIED = "applied"
    REJECTED = "rejected"
    APPROVED = "approved"
    FINALIZED = "finalized"


class ContractStatus(StrEnum):
    """Contract workflow status."""

    DRAFT = "draft"
    OUTDATED = "outdated"
    AWAITING_SIGNATURE = "awaiting_signature"
    EXECUTED = "executed"
    NULLIFIED = "nullified"


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

    @property
    def tier(self) -> str:
        """Get the tier name from the sponsor's active sponsorship.

        Returns the level slug from the first finalized sponsorship,
        or 'community' as a default if no active sponsorship exists.
        """
        for sponsorship in self.sponsorships:
            if sponsorship.status == SponsorshipStatus.FINALIZED and sponsorship.level:
                return sponsorship.level.slug
        return "community"


class Sponsorship(AuditBase, ContentManageableMixin):
    __tablename__ = "sponsorships"

    sponsor_id: Mapped[UUID] = mapped_column(ForeignKey("sponsors.id", ondelete="CASCADE"))
    level_id: Mapped[UUID] = mapped_column(ForeignKey("sponsorship_levels.id", ondelete="CASCADE"))
    submitted_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[SponsorshipStatus] = mapped_column(
        Enum(SponsorshipStatus, values_callable=lambda x: [e.value for e in x]),
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

    contract: Mapped[Contract | None] = relationship(
        "Contract",
        back_populates="sponsorship",
        uselist=False,
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        if not self.start_date or not self.end_date:
            return False
        today = datetime.datetime.now(tz=datetime.UTC).date()
        return self.status == SponsorshipStatus.FINALIZED and self.start_date <= today <= self.end_date


class LegalClause(Base, NameSlugMixin):
    """Legal clauses applied to sponsor contracts.

    Clauses define terms and conditions that can be attached to contracts.
    """

    __tablename__ = "sponsor_legal_clauses"

    clause_text: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Contract(AuditBase):
    """Contract for officializing a sponsorship.

    Tracks the contract document lifecycle from draft through execution.
    """

    __tablename__ = "sponsor_contracts"

    VALID_TRANSITIONS: dict[str, list[str]] = {
        ContractStatus.DRAFT: [ContractStatus.AWAITING_SIGNATURE, ContractStatus.EXECUTED],
        ContractStatus.OUTDATED: [],
        ContractStatus.AWAITING_SIGNATURE: [ContractStatus.EXECUTED, ContractStatus.NULLIFIED],
        ContractStatus.EXECUTED: [],
        ContractStatus.NULLIFIED: [ContractStatus.DRAFT],
    }

    sponsorship_id: Mapped[UUID] = mapped_column(
        ForeignKey("sponsorships.id", ondelete="CASCADE"),
        unique=True,
    )
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, values_callable=lambda x: [e.value for e in x]),
        default=ContractStatus.DRAFT,
        index=True,
    )
    revision: Mapped[int] = mapped_column(SmallInteger, default=0)

    document_pdf: Mapped[str] = mapped_column(String(500), default="")
    document_docx: Mapped[str] = mapped_column(String(500), default="")
    signed_document: Mapped[str] = mapped_column(String(500), default="")

    sponsor_info: Mapped[str] = mapped_column(Text, default="")
    sponsor_contact: Mapped[str] = mapped_column(Text, default="")
    benefits_list: Mapped[str] = mapped_column(Text, default="")
    legal_clauses_text: Mapped[str] = mapped_column(Text, default="")

    sent_on: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    executed_on: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    sponsorship: Mapped[Sponsorship] = relationship(
        "Sponsorship",
        back_populates="contract",
        lazy="selectin",
    )

    @property
    def is_draft(self) -> bool:
        """Check if contract is in draft status."""
        return self.status == ContractStatus.DRAFT

    @property
    def is_awaiting_signature(self) -> bool:
        """Check if contract is awaiting signature."""
        return self.status == ContractStatus.AWAITING_SIGNATURE

    @property
    def is_executed(self) -> bool:
        """Check if contract has been executed."""
        return self.status == ContractStatus.EXECUTED

    @property
    def can_send(self) -> bool:
        """Check if contract can be sent for signature."""
        return ContractStatus.AWAITING_SIGNATURE in self.VALID_TRANSITIONS.get(self.status, [])

    @property
    def can_execute(self) -> bool:
        """Check if contract can be executed."""
        return ContractStatus.EXECUTED in self.VALID_TRANSITIONS.get(self.status, [])

    @property
    def can_nullify(self) -> bool:
        """Check if contract can be nullified."""
        return ContractStatus.NULLIFIED in self.VALID_TRANSITIONS.get(self.status, [])

    @property
    def next_statuses(self) -> list[ContractStatus]:
        """Get valid next statuses for current state."""
        return [ContractStatus(s) for s in self.VALID_TRANSITIONS.get(self.status, [])]
