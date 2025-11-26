"""Code Samples domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.codesamples.repositories import CodeSampleRepository
from pydotorg.domains.codesamples.services import CodeSampleService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_code_sample_repository(db_session: AsyncSession) -> AsyncGenerator[CodeSampleRepository, None]:
    """Provide a CodeSampleRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A CodeSampleRepository instance.
    """
    async with CodeSampleRepository(session=db_session) as repo:
        yield repo


async def provide_code_sample_service(
    code_sample_repository: CodeSampleRepository,
) -> AsyncGenerator[CodeSampleService, None]:
    """Provide a CodeSampleService instance.

    Args:
        code_sample_repository: The code sample repository.

    Yields:
        A CodeSampleService instance.
    """
    async with CodeSampleService(repository=code_sample_repository) as service:
        yield service


def get_codesamples_dependencies() -> dict:
    """Get all code samples domain dependency providers.

    Returns:
        Dictionary of dependency providers for the code samples domain.
    """
    return {
        "code_sample_repository": provide_code_sample_repository,
        "code_sample_service": provide_code_sample_service,
    }
