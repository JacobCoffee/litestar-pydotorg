"""Mailing domain repositories."""

from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from pydotorg.domains.mailing.models import EmailLog, EmailTemplate


class EmailTemplateRepository(SQLAlchemyAsyncRepository[EmailTemplate]):
    """Repository for EmailTemplate model."""

    model_type = EmailTemplate


class EmailLogRepository(SQLAlchemyAsyncRepository[EmailLog]):
    """Repository for EmailLog model."""

    model_type = EmailLog
