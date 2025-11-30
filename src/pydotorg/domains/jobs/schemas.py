"""Jobs domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from pydotorg.domains.jobs.models import JobStatus


class JobTypeBase(BaseModel):
    """Base job type schema."""

    name: Annotated[str, Field(max_length=200)]


class JobTypeCreate(JobTypeBase):
    """Schema for creating a new job type."""

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Full-time", "slug": "full-time"}})

    slug: Annotated[str, Field(max_length=200)] | None = None


class JobTypeUpdate(BaseModel):
    """Schema for updating a job type."""

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Full-time Remote", "slug": "full-time-remote"}})

    name: Annotated[str, Field(max_length=200)] | None = None
    slug: Annotated[str, Field(max_length=200)] | None = None


class JobTypeRead(JobTypeBase):
    """Schema for reading job type data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "name": "Full-time",
                "slug": "full-time",
            }
        },
    )

    id: UUID
    slug: str


class JobCategoryBase(BaseModel):
    """Base job category schema."""

    name: Annotated[str, Field(max_length=200)]


class JobCategoryCreate(JobCategoryBase):
    """Schema for creating a new job category."""

    model_config = ConfigDict(json_schema_extra={"example": {"name": "Engineering", "slug": "engineering"}})

    slug: Annotated[str, Field(max_length=200)] | None = None


class JobCategoryUpdate(BaseModel):
    """Schema for updating a job category."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Software Engineering", "slug": "software-engineering"}}
    )

    name: Annotated[str, Field(max_length=200)] | None = None
    slug: Annotated[str, Field(max_length=200)] | None = None


class JobCategoryRead(JobCategoryBase):
    """Schema for reading job category data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Engineering",
                "slug": "engineering",
            }
        },
    )

    id: UUID
    slug: str


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_name": "Python Software Foundation",
                "job_title": "Senior Python Developer",
                "city": "Remote",
                "region": "California",
                "country": "USA",
                "description": "We are seeking an experienced Python developer to work on core Python infrastructure and tooling. You will collaborate with the PSF team to improve Python packaging, distribution, and developer experience.",
                "requirements": "5+ years Python experience\nExperience with async/await patterns\nKnowledge of CPython internals preferred\nOpen source contributions welcome",
                "contact": "Jane Smith, Engineering Manager",
                "url": "https://python.org/jobs/senior-python-dev",
                "email": "jobs@python.org",
                "telecommuting": True,
                "agencies": False,
                "expires": "2025-12-31",
                "category_id": "550e8400-e29b-41d4-a716-446655440001",
                "job_type_ids": [
                    "550e8400-e29b-41d4-a716-446655440010",
                    "550e8400-e29b-41d4-a716-446655440011",
                ],
            }
        }
    )

    category_id: UUID | None = None
    job_type_ids: list[UUID] = []


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated: We are seeking an experienced Python developer to work on core Python infrastructure, tooling, and community projects. You will collaborate with the PSF team to improve Python packaging, distribution, and developer experience.",
                "requirements": "5+ years Python experience\nExperience with async/await patterns\nKnowledge of CPython internals preferred\nOpen source contributions required\nExcellent communication skills",
                "telecommuting": True,
                "expires": "2026-01-31",
                "status": "approved",
            }
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440020",
                "slug": "senior-python-developer-psf",
                "company_name": "Python Software Foundation",
                "job_title": "Senior Python Developer",
                "city": "Remote",
                "region": "California",
                "country": "USA",
                "description": "We are seeking an experienced Python developer to work on core Python infrastructure and tooling.",
                "requirements": "5+ years Python experience\nExperience with async/await patterns\nKnowledge of CPython internals preferred",
                "contact": "Jane Smith, Engineering Manager",
                "url": "https://python.org/jobs/senior-python-dev",
                "email": "jobs@python.org",
                "telecommuting": True,
                "agencies": False,
                "expires": "2025-12-31",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "approved",
                "category_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2025-11-01T10:00:00Z",
                "updated_at": "2025-11-15T14:30:00Z",
                "job_types": [
                    {"id": "550e8400-e29b-41d4-a716-446655440010", "name": "Full-time", "slug": "full-time"},
                    {"id": "550e8400-e29b-41d4-a716-446655440011", "name": "Remote", "slug": "remote"},
                ],
                "category": {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Engineering",
                    "slug": "engineering",
                },
            }
        },
    )

    id: UUID
    slug: str
    creator_id: UUID
    status: JobStatus
    category_id: UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    job_types: list[JobTypeRead] = []
    category: JobCategoryRead | None = None


class JobPublic(BaseModel):
    """Public job schema for job listings."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440020",
                "slug": "senior-python-developer-psf",
                "company_name": "Python Software Foundation",
                "job_title": "Senior Python Developer",
                "city": "Remote",
                "region": "California",
                "country": "USA",
                "description": "We are seeking an experienced Python developer...",
                "requirements": "5+ years Python experience",
                "contact": "Jane Smith",
                "url": "https://python.org/jobs/senior-python-dev",
                "telecommuting": True,
                "agencies": False,
                "expires": "2025-12-31",
                "category": {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Engineering",
                    "slug": "engineering",
                },
                "job_types": [{"id": "550e8400-e29b-41d4-a716-446655440010", "name": "Full-time", "slug": "full-time"}],
                "created_at": "2025-11-01T10:00:00Z",
            }
        },
    )

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


class JobReviewCommentBase(BaseModel):
    """Base job review comment schema."""

    comment: str


class JobReviewCommentCreate(JobReviewCommentBase):
    """Schema for creating a new job review comment."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": "Please update the job description to include salary range.",
                "job_id": "550e8400-e29b-41d4-a716-446655440020",
            }
        }
    )

    job_id: UUID


class JobReviewCommentUpdate(BaseModel):
    """Schema for updating a job review comment."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"comment": "Updated: The salary range has been added. Approved."}}
    )

    comment: str | None = None


class JobReviewCommentRead(JobReviewCommentBase):
    """Schema for reading job review comment data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440030",
                "job_id": "550e8400-e29b-41d4-a716-446655440020",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "comment": "Please update the job description to include salary range.",
                "created_at": "2025-11-15T10:00:00Z",
                "updated_at": "2025-11-15T10:00:00Z",
            }
        },
    )

    id: UUID
    job_id: UUID
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


class JobSearchFilters(BaseModel):
    """Schema for job search filters."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "country": "USA",
                "telecommuting": True,
                "category_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "approved",
            }
        }
    )

    city: str | None = None
    region: str | None = None
    country: str | None = None
    telecommuting: bool | None = None
    category_id: UUID | None = None
    job_type_ids: list[UUID] | None = None
    status: JobStatus = JobStatus.APPROVED
