"""Jobs domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from slugify import slugify

from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobStatus, JobType
from pydotorg.domains.jobs.repositories import (
    JobCategoryRepository,
    JobRepository,
    JobReviewCommentRepository,
    JobTypeRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from pydotorg.domains.jobs.schemas import JobCreate, JobSearchFilters


class JobTypeService(SQLAlchemyAsyncRepositoryService[JobType]):
    """Service for JobType business logic."""

    repository_type = JobTypeRepository
    match_fields = ["slug"]

    async def create_job_type(self, name: str, slug: str | None = None) -> JobType:
        """Create a new job type.

        Args:
            name: The name of the job type.
            slug: Optional slug. Auto-generated from name if not provided.

        Returns:
            The created job type instance.
        """
        if not slug:
            slug = slugify(name, max_length=200)

        return await self.create({"name": name, "slug": slug})

    async def get_by_slug(self, slug: str) -> JobType | None:
        """Get a job type by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The job type if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)


class JobCategoryService(SQLAlchemyAsyncRepositoryService[JobCategory]):
    """Service for JobCategory business logic."""

    repository_type = JobCategoryRepository
    match_fields = ["slug"]

    async def create_job_category(self, name: str, slug: str | None = None) -> JobCategory:
        """Create a new job category.

        Args:
            name: The name of the job category.
            slug: Optional slug. Auto-generated from name if not provided.

        Returns:
            The created job category instance.
        """
        if not slug:
            slug = slugify(name, max_length=200)

        return await self.create({"name": name, "slug": slug})

    async def get_by_slug(self, slug: str) -> JobCategory | None:
        """Get a job category by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The job category if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)


class JobService(SQLAlchemyAsyncRepositoryService[Job]):
    """Service for Job business logic."""

    repository_type = JobRepository
    match_fields = ["slug"]

    async def create_job(self, data: JobCreate, creator_id: UUID) -> Job:
        """Create a new job posting.

        Args:
            data: Job creation data.
            creator_id: ID of the user creating the job.

        Returns:
            The created job instance.
        """
        job_data = data.model_dump(exclude={"job_type_ids"})
        job_data["creator_id"] = creator_id
        job_data["slug"] = slugify(f"{data.company_name}-{data.job_title}", max_length=200)
        job_data["status"] = JobStatus.DRAFT

        job = await self.create(job_data)

        if data.job_type_ids:
            job_types = []
            for job_type_id in data.job_type_ids:
                job_type = await self.repository.session.get(JobType, job_type_id)
                if job_type:
                    job_types.append(job_type)
            job.job_types = job_types
            await self.repository.session.commit()
            await self.repository.session.refresh(job)

        return job

    async def get_by_slug(self, slug: str) -> Job | None:
        """Get a job by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The job if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

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
        return await self.repository.get_by_creator(creator_id, limit, offset)

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
        return await self.repository.list_by_status(status, limit, offset)

    async def search_jobs(self, filters: JobSearchFilters, limit: int = 100, offset: int = 0) -> list[Job]:
        """Search jobs with filters.

        Args:
            filters: Search filters.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip.

        Returns:
            List of jobs matching the filters.
        """
        return await self.repository.search_jobs(
            status=filters.status,
            city=filters.city,
            region=filters.region,
            country=filters.country,
            telecommuting=filters.telecommuting,
            category_id=filters.category_id,
            job_type_ids=filters.job_type_ids,
            limit=limit,
            offset=offset,
        )

    async def submit_for_review(self, job_id: UUID) -> Job:
        """Submit a job for review.

        Args:
            job_id: The ID of the job to submit.

        Returns:
            The updated job instance.

        Raises:
            ValueError: If job is not in DRAFT status.
        """
        job = await self.get(job_id)
        if job.status != JobStatus.DRAFT:
            msg = f"Job must be in DRAFT status to submit for review. Current status: {job.status}"
            raise ValueError(msg)

        return await self.update(job_id, {"status": JobStatus.REVIEW})

    async def approve_job(self, job_id: UUID) -> Job:
        """Approve a job posting.

        Args:
            job_id: The ID of the job to approve.

        Returns:
            The updated job instance.

        Raises:
            ValueError: If job is not in REVIEW status.
        """
        job = await self.get(job_id)
        if job.status != JobStatus.REVIEW:
            msg = f"Job must be in REVIEW status to approve. Current status: {job.status}"
            raise ValueError(msg)

        return await self.update(job_id, {"status": JobStatus.APPROVED})

    async def reject_job(self, job_id: UUID) -> Job:
        """Reject a job posting.

        Args:
            job_id: The ID of the job to reject.

        Returns:
            The updated job instance.

        Raises:
            ValueError: If job is not in REVIEW status.
        """
        job = await self.get(job_id)
        if job.status != JobStatus.REVIEW:
            msg = f"Job must be in REVIEW status to reject. Current status: {job.status}"
            raise ValueError(msg)

        return await self.update(job_id, {"status": JobStatus.REJECTED})

    async def archive_job(self, job_id: UUID) -> Job:
        """Archive a job posting.

        Args:
            job_id: The ID of the job to archive.

        Returns:
            The updated job instance.
        """
        return await self.update(job_id, {"status": JobStatus.ARCHIVED})

    async def mark_expired_jobs(self) -> list[Job]:
        """Mark all expired jobs as EXPIRED.

        Returns:
            List of jobs that were marked as expired.
        """
        expired_jobs = await self.repository.list_expired()
        updated_jobs = []

        for job in expired_jobs:
            updated_job = await self.update(job.id, {"status": JobStatus.EXPIRED})
            updated_jobs.append(updated_job)

        return updated_jobs

    async def get_featured(self, limit: int = 5) -> list[Job]:
        """Get featured job listings.

        Args:
            limit: Maximum number of featured jobs to return.

        Returns:
            List of featured approved jobs.
        """
        return await self.repository.get_featured(limit=limit)

    async def update_job_types(self, job_id: UUID, job_type_ids: list[UUID]) -> Job:
        """Update job types for a job.

        Args:
            job_id: The ID of the job.
            job_type_ids: List of job type IDs to associate.

        Returns:
            The updated job instance.
        """
        job = await self.get(job_id)

        job_types = []
        for job_type_id in job_type_ids:
            job_type = await self.repository.session.get(JobType, job_type_id)
            if job_type:
                job_types.append(job_type)

        job.job_types = job_types
        await self.repository.session.commit()
        await self.repository.session.refresh(job)

        return job


class JobReviewCommentService(SQLAlchemyAsyncRepositoryService[JobReviewComment]):
    """Service for JobReviewComment business logic."""

    repository_type = JobReviewCommentRepository

    async def create_comment(self, job_id: UUID, comment: str, creator_id: UUID) -> JobReviewComment:
        """Create a review comment for a job.

        Args:
            job_id: The ID of the job.
            comment: The comment text.
            creator_id: ID of the user creating the comment.

        Returns:
            The created comment instance.
        """
        return await self.create(
            {
                "job_id": job_id,
                "comment": comment,
                "creator_id": creator_id,
            }
        )

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
        return await self.repository.get_by_job(job_id, limit, offset)
