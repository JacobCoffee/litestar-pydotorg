"""Jobs domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.jobs.repositories import (
    JobCategoryRepository,
    JobRepository,
    JobReviewCommentRepository,
    JobTypeRepository,
)
from pydotorg.domains.jobs.services import (
    JobCategoryService,
    JobReviewCommentService,
    JobService,
    JobTypeService,
)


async def provide_job_type_repository(db_session: AsyncSession) -> JobTypeRepository:
    """Provide a JobTypeRepository instance."""
    return JobTypeRepository(session=db_session)


async def provide_job_type_service(db_session: AsyncSession) -> JobTypeService:
    """Provide a JobTypeService instance."""
    return JobTypeService(session=db_session)


async def provide_job_category_repository(db_session: AsyncSession) -> JobCategoryRepository:
    """Provide a JobCategoryRepository instance."""
    return JobCategoryRepository(session=db_session)


async def provide_job_category_service(db_session: AsyncSession) -> JobCategoryService:
    """Provide a JobCategoryService instance."""
    return JobCategoryService(session=db_session)


async def provide_job_repository(db_session: AsyncSession) -> JobRepository:
    """Provide a JobRepository instance."""
    return JobRepository(session=db_session)


async def provide_job_service(db_session: AsyncSession) -> JobService:
    """Provide a JobService instance."""
    return JobService(session=db_session)


async def provide_job_review_comment_repository(db_session: AsyncSession) -> JobReviewCommentRepository:
    """Provide a JobReviewCommentRepository instance."""
    return JobReviewCommentRepository(session=db_session)


async def provide_job_review_comment_service(db_session: AsyncSession) -> JobReviewCommentService:
    """Provide a JobReviewCommentService instance."""
    return JobReviewCommentService(session=db_session)


def get_jobs_dependencies() -> dict:
    """Get all jobs domain dependency providers."""
    return {
        "job_type_repository": provide_job_type_repository,
        "job_type_service": provide_job_type_service,
        "job_category_repository": provide_job_category_repository,
        "job_category_service": provide_job_category_service,
        "job_repository": provide_job_repository,
        "job_service": provide_job_service,
        "job_review_comment_repository": provide_job_review_comment_repository,
        "job_review_comment_service": provide_job_review_comment_service,
    }
