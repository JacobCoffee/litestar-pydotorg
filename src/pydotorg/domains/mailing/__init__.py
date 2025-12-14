"""Mailing domain.

This domain provides database-driven email templates and email sending
functionality. Templates support Jinja2 syntax for dynamic content.

Key Components:
    - EmailTemplate: Database model for email templates
    - EmailLog: Audit log for sent emails
    - MailingService: Service for sending emails via templates
    - EmailTemplateController: Admin API for template management
    - EmailLogController: Admin API for viewing email logs

Example::

    from pydotorg.domains.mailing import (
        EmailTemplate,
        EmailLog,
        MailingService,
        EmailTemplateController,
        EmailLogController,
    )
"""

from pydotorg.domains.mailing.controllers import EmailLogController, EmailTemplateController
from pydotorg.domains.mailing.dependencies import get_mailing_dependencies
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate, EmailTemplateType
from pydotorg.domains.mailing.repositories import EmailLogRepository, EmailTemplateRepository
from pydotorg.domains.mailing.schemas import (
    BulkSendEmailRequest,
    BulkSendEmailResponse,
    EmailLogCreate,
    EmailLogRead,
    EmailTemplateCreate,
    EmailTemplatePreview,
    EmailTemplateRead,
    EmailTemplateUpdate,
    EmailTemplateValidation,
    SendEmailRequest,
    SendEmailResponse,
)
from pydotorg.domains.mailing.services import EmailLogService, EmailTemplateService, MailingService

__all__ = [
    "BulkSendEmailRequest",
    "BulkSendEmailResponse",
    "EmailLog",
    "EmailLogController",
    "EmailLogCreate",
    "EmailLogRead",
    "EmailLogRepository",
    "EmailLogService",
    "EmailTemplate",
    "EmailTemplateController",
    "EmailTemplateCreate",
    "EmailTemplatePreview",
    "EmailTemplateRead",
    "EmailTemplateRepository",
    "EmailTemplateService",
    "EmailTemplateType",
    "EmailTemplateUpdate",
    "EmailTemplateValidation",
    "MailingService",
    "SendEmailRequest",
    "SendEmailResponse",
    "get_mailing_dependencies",
]
