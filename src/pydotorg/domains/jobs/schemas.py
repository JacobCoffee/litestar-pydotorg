"""Jobs domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from pydotorg.domains.jobs.models import JobStatus

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class JobTypeBase(BaseModel):
    """Base job type schema."""

    name: Annotated[str, Field(max_length=200)]


class JobTypeCreate(JobTypeBase):
    """Schema for creating a new job type."""

    slug: Annotated[str, Field(max_length=200)] | None = None


class JobTypeUpdate(BaseModel):
    """Schema for updating a job type."""

    name: Annotated[str, Field(max_length=200)] | None = None
    slug: Annotated[str, Field(max_length=200)] | None = None


class JobTypeRead(JobTypeBase):
    """Schema for reading job type data."""

    id: UUID
    slug: str

    model_config = ConfigDict(from_attributes=True)


class JobCategoryBase(BaseModel):
    """Base job category schema."""

    name: Annotated[str, Field(max_length=200)]


class JobCategoryCreate(JobCategoryBase):
    """Schema for creating a new job category."""

    slug: Annotated[str, Field(max_length=200)] | None = None


class JobCategoryUpdate(BaseModel):
    """Schema for updating a job category."""

    name: Annotated[str, Field(max_length=200)] | None = None
    slug: Annotated[str, Field(max_length=200)] | None = None


class JobCategoryRead(JobCategoryBase):
    """Schema for reading job category data."""

    id: UUID
    slug: str

    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    """Base job schema with common fields."""

    company_name: Annotated[str, Field(max_length=200)]
    job_title: Annotated[str, Field(max_length=200)]
    city: Annotated[str, Field(max_length=100)] | None = None
    region: Annotated[str, Field(max_length=100)] | None = None
    country: Annotated[str, Field(max_length=100)]
    description: str
    requirements: str | None = None
    contact: Annotated[str, Field(max_length=200)] | None = None
    url: HttpUrl | str | None = None
    email: EmailStr
    telecommuting: bool = False
    agencies: bool = False
    expires: datetime.date | None = None


class JobCreate(JobBase):
    """Schema for creating a new job."""

    category_id: UUID | None = None
    job_type_ids: list[UUID] = []


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    company_name: Annotated[str, Field(max_length=200)] | None = None
    job_title: Annotated[str, Field(max_length=200)] | None = None
    city: Annotated[str, Field(max_length=100)] | None = None
    region: Annotated[str, Field(max_length=100)] | None = None
    country: Annotated[str, Field(max_length=100)] | None = None
    description: str | None = None
    requirements: str | None = None
    contact: Annotated[str, Field(max_length=200)] | None = None
    url: HttpUrl | str | None = None
    email: EmailStr | None = None
    telecommuting: bool | None = None
    agencies: bool | None = None
    expires: datetime.date | None = None
    category_id: UUID | None = None
    job_type_ids: list[UUID] | None = None
    status: JobStatus | None = None


class JobRead(JobBase):
    """Schema for reading job data."""

    id: UUID
    slug: str
    creator_id: UUID
    status: JobStatus
    category_id: UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    job_types: list[JobTypeRead] = []
    category: JobCategoryRead | None = None

    model_config = ConfigDict(from_attributes=True)


class JobPublic(BaseModel):
    """Public job schema for job listings."""

    id: UUID
    slug: str
    company_name: str
    job_title: str
    city: str | None
    region: str | None
    country: str
    description: str
    requirements: str | None
    contact: str | None
    url: str | None
    telecommuting: bool
    agencies: bool
    expires: datetime.date | None
    category: JobCategoryRead | None
    job_types: list[JobTypeRead] = []
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class JobReviewCommentBase(BaseModel):
    """Base job review comment schema."""

    comment: str


class JobReviewCommentCreate(JobReviewCommentBase):
    """Schema for creating a new job review comment."""

    job_id: UUID


class JobReviewCommentUpdate(BaseModel):
    """Schema for updating a job review comment."""

    comment: str | None = None


class JobReviewCommentRead(JobReviewCommentBase):
    """Schema for reading job review comment data."""

    id: UUID
    job_id: UUID
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class JobSearchFilters(BaseModel):
    """Schema for job search filters."""

    city: str | None = None
    region: str | None = None
    country: str | None = None
    telecommuting: bool | None = None
    category_id: UUID | None = None
    job_type_ids: list[UUID] | None = None
    status: JobStatus = JobStatus.APPROVED
