"""Admin job moderation service."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from pydotorg.config import settings
from pydotorg.domains.jobs.models import Job, JobReviewComment, JobStatus
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class JobAdminService:
    """Service for admin job moderation operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Job], int]:
        """List jobs with filtering and pagination.

        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            status: Filter by job status
            search: Search query for job title or company name

        Returns:
            Tuple of (jobs list, total count)
        """
        query = select(Job).options(
            selectinload(Job.creator),
            selectinload(Job.category),
            selectinload(Job.job_types),
        )

        if status:
            status_enum = JobStatus(status)
            query = query.where(Job.status == status_enum)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Job.job_title.ilike(search_term),
                    Job.company_name.ilike(search_term),
                    Job.description.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        jobs = list(result.scalars().all())

        return jobs, total

    async def get_job(self, job_id: UUID) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job if found, None otherwise
        """
        query = (
            select(Job)
            .where(Job.id == job_id)
            .options(
                selectinload(Job.creator),
                selectinload(Job.category),
                selectinload(Job.job_types),
                selectinload(Job.review_comments).selectinload(JobReviewComment.creator),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def submit_for_review(self, job_id: UUID) -> Job | None:
        """Submit a draft job for review.

        Transitions the job from DRAFT to REVIEW status.

        Args:
            job_id: Job ID

        Returns:
            Updated job if found and was in draft status, None otherwise
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        if job.status != JobStatus.DRAFT:
            return job

        job.status = JobStatus.REVIEW
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def approve_job(self, job_id: UUID) -> Job | None:
        """Approve a job.

        Approves the job, enqueues email notification to creator, and
        triggers search indexing.

        Args:
            job_id: Job ID

        Returns:
            Updated job if found, None otherwise
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        job.status = JobStatus.APPROVED
        await self.session.commit()
        await self.session.refresh(job)

        job_url = f"{settings.oauth_redirect_base_url}/jobs/{job.slug}/"
        email_key = await enqueue_task(
            "send_job_approved_email",
            to_email=job.creator.email,
            job_title=job.job_title,
            company_name=job.company_name,
            job_url=job_url,
        )
        if not email_key:
            logger.warning(f"Failed to enqueue approval email for job {job.id}")

        index_key = await enqueue_task("index_job", job_id=str(job.id))
        if not index_key:
            logger.warning(f"Failed to enqueue search indexing for job {job.id}")

        return job

    async def reject_job(
        self,
        job_id: UUID,
        reason: str = "Your job posting did not meet our guidelines.",
    ) -> Job | None:
        """Reject a job.

        Rejects the job and enqueues email notification to creator with
        the rejection reason.

        Args:
            job_id: Job ID
            reason: Rejection reason to send to job creator

        Returns:
            Updated job if found, None otherwise
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        job.status = JobStatus.REJECTED
        await self.session.commit()
        await self.session.refresh(job)

        email_key = await enqueue_task(
            "send_job_rejected_email",
            to_email=job.creator.email,
            job_title=job.job_title,
            company_name=job.company_name,
            reason=reason,
        )
        if not email_key:
            logger.warning(f"Failed to enqueue rejection email for job {job.id}")

        return job

    async def add_review_comment(self, job_id: UUID, comment: str, reviewer_id: UUID) -> JobReviewComment | None:
        """Add a review comment to a job.

        Args:
            job_id: Job ID
            comment: Review comment text
            reviewer_id: ID of the reviewer

        Returns:
            Created review comment if job found, None otherwise
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        review_comment = JobReviewComment(
            job_id=job_id,
            comment=comment,
            creator_id=reviewer_id,
        )
        self.session.add(review_comment)
        await self.session.commit()
        await self.session.refresh(review_comment)
        return review_comment

    async def get_stats(self) -> dict:
        """Get job moderation statistics.

        Returns:
            Dictionary with job stats
        """
        total_query = select(func.count()).select_from(Job)
        total_result = await self.session.execute(total_query)
        total_jobs = total_result.scalar() or 0

        pending_query = select(func.count()).where(Job.status == JobStatus.REVIEW)
        pending_result = await self.session.execute(pending_query)
        pending_jobs = pending_result.scalar() or 0

        approved_query = select(func.count()).where(Job.status == JobStatus.APPROVED)
        approved_result = await self.session.execute(approved_query)
        approved_jobs = approved_result.scalar() or 0

        rejected_query = select(func.count()).where(Job.status == JobStatus.REJECTED)
        rejected_result = await self.session.execute(rejected_query)
        rejected_jobs = rejected_result.scalar() or 0

        return {
            "total_jobs": total_jobs,
            "pending_jobs": pending_jobs,
            "approved_jobs": approved_jobs,
            "rejected_jobs": rejected_jobs,
        }

    async def delete_job(self, job_id: UUID) -> bool:
        """Delete a job.

        Args:
            job_id: Job ID

        Returns:
            True if job was deleted, False if not found
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        await self.session.delete(job)
        await self.session.commit()
        return True

    async def toggle_featured(self, job_id: UUID) -> Job | None:
        """Toggle the featured status of a job.

        Args:
            job_id: Job ID

        Returns:
            Updated job if found, None otherwise
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        job.is_featured = not job.is_featured
        await self.session.commit()
        await self.session.refresh(job)
        return job
