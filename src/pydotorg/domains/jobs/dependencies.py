"""Jobs domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_job_type_repository(db_session: AsyncSession) -> AsyncGenerator[JobTypeRepository, None]:
    """Provide a JobTypeRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A JobTypeRepository instance.
    """
    async with JobTypeRepository(session=db_session) as repo:
        yield repo


async def provide_job_type_service(
    job_type_repository: JobTypeRepository,
) -> AsyncGenerator[JobTypeService, None]:
    """Provide a JobTypeService instance.

    Args:
        job_type_repository: The job type repository.

    Yields:
        A JobTypeService instance.
    """
    async with JobTypeService(repository=job_type_repository) as service:
        yield service


async def provide_job_category_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[JobCategoryRepository, None]:
    """Provide a JobCategoryRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A JobCategoryRepository instance.
    """
    async with JobCategoryRepository(session=db_session) as repo:
        yield repo


async def provide_job_category_service(
    job_category_repository: JobCategoryRepository,
) -> AsyncGenerator[JobCategoryService, None]:
    """Provide a JobCategoryService instance.

    Args:
        job_category_repository: The job category repository.

    Yields:
        A JobCategoryService instance.
    """
    async with JobCategoryService(repository=job_category_repository) as service:
        yield service


async def provide_job_repository(db_session: AsyncSession) -> AsyncGenerator[JobRepository, None]:
    """Provide a JobRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A JobRepository instance.
    """
    async with JobRepository(session=db_session) as repo:
        yield repo


async def provide_job_service(
    job_repository: JobRepository,
) -> AsyncGenerator[JobService, None]:
    """Provide a JobService instance.

    Args:
        job_repository: The job repository.

    Yields:
        A JobService instance.
    """
    async with JobService(repository=job_repository) as service:
        yield service


async def provide_job_review_comment_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[JobReviewCommentRepository, None]:
    """Provide a JobReviewCommentRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A JobReviewCommentRepository instance.
    """
    async with JobReviewCommentRepository(session=db_session) as repo:
        yield repo


async def provide_job_review_comment_service(
    job_review_comment_repository: JobReviewCommentRepository,
) -> AsyncGenerator[JobReviewCommentService, None]:
    """Provide a JobReviewCommentService instance.

    Args:
        job_review_comment_repository: The job review comment repository.

    Yields:
        A JobReviewCommentService instance.
    """
    async with JobReviewCommentService(repository=job_review_comment_repository) as service:
        yield service


def get_jobs_dependencies() -> dict:
    """Get all jobs domain dependency providers.

    Returns:
        Dictionary of dependency providers for the jobs domain.
    """
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
