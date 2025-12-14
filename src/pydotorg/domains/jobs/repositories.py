"""Jobs domain repositories for database access."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobStatus, JobType

if TYPE_CHECKING:
    from uuid import UUID


class JobTypeRepository(SQLAlchemyAsyncRepository[JobType]):
    """Repository for JobType database operations."""

    model_type = JobType

    async def get_by_slug(self, slug: str) -> JobType | None:
        """Get a job type by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The job type if found, None otherwise.
        """
        statement = select(JobType).where(JobType.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class JobCategoryRepository(SQLAlchemyAsyncRepository[JobCategory]):
    """Repository for JobCategory database operations."""

    model_type = JobCategory

    async def get_by_slug(self, slug: str) -> JobCategory | None:
        """Get a job category by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The job category if found, None otherwise.
        """
        statement = select(JobCategory).where(JobCategory.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class JobRepository(SQLAlchemyAsyncRepository[Job]):
    """Repository for Job database operations."""

    model_type = Job

    async def get_by_slug(self, slug: str) -> Job | None:
        """Get a job by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The job if found, None otherwise.
        """
        statement = select(Job).where(Job.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_creator(
        self,
        creator_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Get jobs by creator.

        Args:
            creator_id: The creator user ID.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip.

        Returns:
            List of jobs created by the user.
        """
        statement = (
            select(Job).where(Job.creator_id == creator_id).order_by(Job.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: JobStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs by status.

        Args:
            status: The job status to filter by.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip.

        Returns:
            List of jobs with the specified status.
        """
        statement = select(Job).where(Job.status == status).order_by(Job.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def search_jobs(
        self,
        status: JobStatus = JobStatus.APPROVED,
        city: str | None = None,
        region: str | None = None,
        country: str | None = None,
        *,
        telecommuting: bool | None = None,
        category_id: UUID | None = None,
        job_type_ids: list[UUID] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Search jobs with filters.

        Args:
            status: Filter by job status.
            city: Filter by city.
            region: Filter by region.
            country: Filter by country.
            telecommuting: Filter by telecommuting availability.
            category_id: Filter by job category.
            job_type_ids: Filter by job type IDs.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip.

        Returns:
            List of jobs matching the filters.
        """
        statement = select(Job).where(Job.status == status)

        if city:
            statement = statement.where(Job.city == city)
        if region:
            statement = statement.where(Job.region == region)
        if country:
            statement = statement.where(Job.country == country)
        if telecommuting is not None:
            statement = statement.where(Job.telecommuting == telecommuting)
        if category_id:
            statement = statement.where(Job.category_id == category_id)

        statement = statement.order_by(Job.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(statement)
        jobs = list(result.scalars().all())

        if job_type_ids:
            jobs = [job for job in jobs if any(jt.id in job_type_ids for jt in job.job_types)]

        return jobs

    async def list_expired(self, before_date: datetime.date | None = None) -> list[Job]:
        """List expired jobs.

        Args:
            before_date: Optional date to check expiration against. Defaults to today.

        Returns:
            List of expired jobs.
        """
        if before_date is None:
            before_date = datetime.datetime.now(tz=datetime.UTC).date()

        statement = select(Job).where(
            Job.expires.isnot(None),
            Job.expires < before_date,
            Job.status != JobStatus.EXPIRED,
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_featured(self, limit: int = 5) -> list[Job]:
        """Get featured job listings.

        Args:
            limit: Maximum number of featured jobs to return.

        Returns:
            List of featured approved jobs.
        """
        statement = (
            select(Job)
            .where(Job.is_featured.is_(True), Job.status == JobStatus.APPROVED)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class JobReviewCommentRepository(SQLAlchemyAsyncRepository[JobReviewComment]):
    """Repository for JobReviewComment database operations."""

    model_type = JobReviewComment

    async def get_by_job(
        self,
        job_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobReviewComment]:
        """Get review comments for a job.

        Args:
            job_id: The job ID.
            limit: Maximum number of comments to return.
            offset: Number of comments to skip.

        Returns:
            List of review comments for the job.
        """
        statement = (
            select(JobReviewComment)
            .where(JobReviewComment.job_id == job_id)
            .order_by(JobReviewComment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
