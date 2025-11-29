"""Mailing domain dependency providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.mailing.services import EmailLogService, EmailTemplateService, MailingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_email_template_service(db_session: AsyncSession) -> EmailTemplateService:
    """Provide EmailTemplateService instance.

    Args:
        db_session: Database session from dependency injection

    Returns:
        EmailTemplateService instance
    """
    return EmailTemplateService(session=db_session)


async def provide_email_log_service(db_session: AsyncSession) -> EmailLogService:
    """Provide EmailLogService instance.

    Args:
        db_session: Database session from dependency injection

    Returns:
        EmailLogService instance
    """
    return EmailLogService(session=db_session)


async def provide_mailing_service(db_session: AsyncSession) -> MailingService:
    """Provide MailingService instance.

    Args:
        db_session: Database session from dependency injection

    Returns:
        MailingService instance
    """
    return MailingService(session=db_session)


def get_mailing_dependencies() -> dict:
    """Get all mailing domain dependency providers.

    Returns:
        Dictionary mapping dependency names to provider functions
    """
    return {
        "email_template_service": provide_email_template_service,
        "email_log_service": provide_email_log_service,
        "mailing_service": provide_mailing_service,
    }
