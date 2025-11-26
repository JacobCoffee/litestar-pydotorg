"""Code Samples domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.codesamples.repositories import CodeSampleRepository
from pydotorg.domains.codesamples.services import CodeSampleService


async def provide_code_sample_repository(db_session: AsyncSession) -> CodeSampleRepository:
    """Provide a CodeSampleRepository instance."""
    return CodeSampleRepository(session=db_session)


async def provide_code_sample_service(db_session: AsyncSession) -> CodeSampleService:
    """Provide a CodeSampleService instance."""
    return CodeSampleService(session=db_session)


def get_codesamples_dependencies() -> dict:
    """Get all code samples domain dependency providers."""
    return {
        "code_sample_repository": provide_code_sample_repository,
        "code_sample_service": provide_code_sample_service,
    }
