"""Sponsors domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from pydotorg.domains.sponsors.models import SponsorshipStatus

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class SponsorshipLevelBase(BaseModel):
    """Base sponsorship level schema."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    order: int = 0
    sponsorship_amount: int = 0
    logo_dimension: int | None = None


class SponsorshipLevelCreate(BaseModel):
    """Schema for creating a new sponsorship level."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    order: int = 0
    sponsorship_amount: int = 0
    logo_dimension: int | None = None


class SponsorshipLevelUpdate(BaseModel):
    """Schema for updating a sponsorship level."""

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    slug: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    order: int | None = None
    sponsorship_amount: int | None = None
    logo_dimension: int | None = None


class SponsorshipLevelRead(SponsorshipLevelBase):
    """Schema for reading sponsorship level data."""

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SponsorBase(BaseModel):
    """Base sponsor schema."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]
    description: str = ""
    landing_page_url: Annotated[str, Field(max_length=500)] = ""
    twitter_handle: Annotated[str, Field(max_length=100)] = ""
    linked_in_page_url: Annotated[str, Field(max_length=500)] = ""
    web_logo: Annotated[str, Field(max_length=500)] = ""
    print_logo: Annotated[str, Field(max_length=500)] = ""
    primary_phone: Annotated[str, Field(max_length=50)] = ""
    mailing_address_line_1: Annotated[str, Field(max_length=255)] = ""
    mailing_address_line_2: Annotated[str, Field(max_length=255)] = ""
    city: Annotated[str, Field(max_length=100)] = ""
    state: Annotated[str, Field(max_length=100)] = ""
    postal_code: Annotated[str, Field(max_length=20)] = ""
    country: Annotated[str, Field(max_length=100)] = ""
    country_of_incorporation: Annotated[str, Field(max_length=100)] = ""
    state_of_incorporation: Annotated[str, Field(max_length=100)] = ""


class SponsorCreate(BaseModel):
    """Schema for creating a new sponsor."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: str = ""
    landing_page_url: Annotated[str, Field(max_length=500)] = ""
    twitter_handle: Annotated[str, Field(max_length=100)] = ""
    linked_in_page_url: Annotated[str, Field(max_length=500)] = ""
    web_logo: Annotated[str, Field(max_length=500)] = ""
    print_logo: Annotated[str, Field(max_length=500)] = ""
    primary_phone: Annotated[str, Field(max_length=50)] = ""
    mailing_address_line_1: Annotated[str, Field(max_length=255)] = ""
    mailing_address_line_2: Annotated[str, Field(max_length=255)] = ""
    city: Annotated[str, Field(max_length=100)] = ""
    state: Annotated[str, Field(max_length=100)] = ""
    postal_code: Annotated[str, Field(max_length=20)] = ""
    country: Annotated[str, Field(max_length=100)] = ""
    country_of_incorporation: Annotated[str, Field(max_length=100)] = ""
    state_of_incorporation: Annotated[str, Field(max_length=100)] = ""
    creator_id: UUID | None = None


class SponsorUpdate(BaseModel):
    """Schema for updating a sponsor."""

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    slug: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: str | None = None
    landing_page_url: Annotated[str, Field(max_length=500)] | None = None
    twitter_handle: Annotated[str, Field(max_length=100)] | None = None
    linked_in_page_url: Annotated[str, Field(max_length=500)] | None = None
    web_logo: Annotated[str, Field(max_length=500)] | None = None
    print_logo: Annotated[str, Field(max_length=500)] | None = None
    primary_phone: Annotated[str, Field(max_length=50)] | None = None
    mailing_address_line_1: Annotated[str, Field(max_length=255)] | None = None
    mailing_address_line_2: Annotated[str, Field(max_length=255)] | None = None
    city: Annotated[str, Field(max_length=100)] | None = None
    state: Annotated[str, Field(max_length=100)] | None = None
    postal_code: Annotated[str, Field(max_length=20)] | None = None
    country: Annotated[str, Field(max_length=100)] | None = None
    country_of_incorporation: Annotated[str, Field(max_length=100)] | None = None
    state_of_incorporation: Annotated[str, Field(max_length=100)] | None = None
    last_modified_by_id: UUID | None = None


class SponsorRead(SponsorBase):
    """Schema for reading sponsor data."""

    id: UUID
    created: datetime.datetime
    updated: datetime.datetime
    creator_id: UUID | None
    last_modified_by_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


class SponsorPublic(BaseModel):
    """Public sponsor schema."""

    id: UUID
    name: str
    slug: str
    description: str
    landing_page_url: str
    twitter_handle: str
    linked_in_page_url: str
    web_logo: str
    print_logo: str

    model_config = ConfigDict(from_attributes=True)


class SponsorshipBase(BaseModel):
    """Base sponsorship schema."""

    sponsor_id: UUID
    level_id: UUID
    status: SponsorshipStatus = SponsorshipStatus.APPLIED
    locked: bool = False
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    applied_on: datetime.date | None = None
    approved_on: datetime.date | None = None
    rejected_on: datetime.date | None = None
    finalized_on: datetime.date | None = None
    year: int | None = None
    sponsorship_fee: int = 0
    for_modified_package: bool = False
    renewal: bool = False


class SponsorshipCreate(BaseModel):
    """Schema for creating a new sponsorship."""

    sponsor_id: UUID
    level_id: UUID
    status: SponsorshipStatus = SponsorshipStatus.APPLIED
    locked: bool = False
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    applied_on: datetime.date | None = None
    year: int | None = None
    sponsorship_fee: int = 0
    for_modified_package: bool = False
    renewal: bool = False
    submitted_by_id: UUID | None = None
    creator_id: UUID | None = None


class SponsorshipUpdate(BaseModel):
    """Schema for updating a sponsorship."""

    sponsor_id: UUID | None = None
    level_id: UUID | None = None
    status: SponsorshipStatus | None = None
    locked: bool | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    applied_on: datetime.date | None = None
    approved_on: datetime.date | None = None
    rejected_on: datetime.date | None = None
    finalized_on: datetime.date | None = None
    year: int | None = None
    sponsorship_fee: int | None = None
    for_modified_package: bool | None = None
    renewal: bool | None = None
    last_modified_by_id: UUID | None = None


class SponsorshipRead(SponsorshipBase):
    """Schema for reading sponsorship data."""

    id: UUID
    submitted_by_id: UUID | None
    created: datetime.datetime
    updated: datetime.datetime
    creator_id: UUID | None
    last_modified_by_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


class SponsorshipPublic(BaseModel):
    """Public sponsorship schema."""

    id: UUID
    sponsor_id: UUID
    level_id: UUID
    status: SponsorshipStatus
    start_date: datetime.date | None
    end_date: datetime.date | None
    year: int | None

    model_config = ConfigDict(from_attributes=True)
