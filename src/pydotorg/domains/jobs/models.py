"""Jobs domain models."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, NameSlugMixin, register_name_slug_listener

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User


class JobStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    EXPIRED = "expired"


job_job_types = Table(
    "job_job_types",
    Base.metadata,
    Column("job_id", ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("job_type_id", ForeignKey("job_types.id", ondelete="CASCADE"), primary_key=True),
)


class JobType(Base, NameSlugMixin):
    __tablename__ = "job_types"

    jobs: Mapped[list[Job]] = relationship(
        "Job",
        secondary=job_job_types,
        back_populates="job_types",
        lazy="noload",
    )


event_listener_added = False
if not event_listener_added:
    from sqlalchemy import event

    event.listen(JobType, "mapper_configured", register_name_slug_listener, propagate=True)
    event_listener_added = True


class JobCategory(Base, NameSlugMixin):
    __tablename__ = "job_categories"

    jobs: Mapped[list[Job]] = relationship(
        "Job",
        back_populates="category",
        lazy="noload",
    )


event_listener_added_category = False
if not event_listener_added_category:
    from sqlalchemy import event

    event.listen(JobCategory, "mapper_configured", register_name_slug_listener, propagate=True)
    event_listener_added_category = True


class Job(AuditBase):
    __tablename__ = "jobs"

    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    company_name: Mapped[str] = mapped_column(String(200))
    job_title: Mapped[str] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str] = mapped_column(String(254))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.DRAFT,
        index=True,
    )
    telecommuting: Mapped[bool] = mapped_column(Boolean, default=False)
    agencies: Mapped[bool] = mapped_column(Boolean, default=False)
    expires: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("job_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator: Mapped[User] = relationship("User", foreign_keys=[creator_id], lazy="selectin")
    job_types: Mapped[list[JobType]] = relationship(
        "JobType",
        secondary=job_job_types,
        back_populates="jobs",
        lazy="selectin",
    )
    category: Mapped[JobCategory | None] = relationship(
        "JobCategory",
        back_populates="jobs",
        lazy="selectin",
    )
    review_comments: Mapped[list[JobReviewComment]] = relationship(
        "JobReviewComment",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        if not self.expires:
            return False
        return datetime.datetime.now(tz=datetime.UTC).date() > self.expires


class JobReviewComment(AuditBase):
    __tablename__ = "job_review_comments"

    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    comment: Mapped[str] = mapped_column(Text)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    job: Mapped[Job] = relationship("Job", back_populates="review_comments")
    creator: Mapped[User] = relationship("User", foreign_keys=[creator_id], lazy="selectin")
