"""Nominations domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from pydotorg.domains.nominations.models import ElectionStatus  # noqa: TC001 - used at runtime

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class ElectionBase(BaseModel):
    """Base election schema."""

    name: Annotated[str, Field(max_length=200)]
    description: str | None = None
    nominations_open: datetime.date
    nominations_close: datetime.date
    voting_open: datetime.date
    voting_close: datetime.date


class ElectionCreate(ElectionBase):
    """Schema for creating a new election."""

    slug: Annotated[str, Field(max_length=200)] | None = None


class ElectionUpdate(BaseModel):
    """Schema for updating an election."""

    name: Annotated[str, Field(max_length=200)] | None = None
    description: str | None = None
    nominations_open: datetime.date | None = None
    nominations_close: datetime.date | None = None
    voting_open: datetime.date | None = None
    voting_close: datetime.date | None = None
    slug: Annotated[str, Field(max_length=200)] | None = None


class ElectionRead(ElectionBase):
    """Schema for reading election data."""

    id: UUID
    slug: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: ElectionStatus

    model_config = ConfigDict(from_attributes=True)


class NomineeBase(BaseModel):
    """Base nominee schema."""

    election_id: UUID
    user_id: UUID


class NomineeCreate(NomineeBase):
    """Schema for creating a new nominee."""


class NomineeUpdate(BaseModel):
    """Schema for updating a nominee."""

    accepted: bool | None = None


class NomineeRead(NomineeBase):
    """Schema for reading nominee data."""

    id: UUID
    accepted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class NominationBase(BaseModel):
    """Base nomination schema."""

    nominee_id: UUID
    endorsement: str | None = None


class NominationCreate(NominationBase):
    """Schema for creating a new nomination."""


class NominationUpdate(BaseModel):
    """Schema for updating a nomination."""

    endorsement: str | None = None


class NominationRead(NominationBase):
    """Schema for reading nomination data."""

    id: UUID
    nominator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ElectionPublic(BaseModel):
    """Public election schema for listings."""

    id: UUID
    slug: str
    name: str
    description: str | None
    nominations_open: datetime.date
    nominations_close: datetime.date
    voting_open: datetime.date
    voting_close: datetime.date
    status: ElectionStatus

    model_config = ConfigDict(from_attributes=True)


class NomineePublic(BaseModel):
    """Public nominee schema for listings."""

    id: UUID
    election_id: UUID
    user_id: UUID
    accepted: bool

    model_config = ConfigDict(from_attributes=True)
