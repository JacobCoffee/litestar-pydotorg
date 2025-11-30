"""Mailing domain controllers.

Provides API endpoints for email template management and email sending.
Admin endpoints are protected by staff/superuser guards.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from advanced_alchemy.exceptions import NotFoundError
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from pydotorg.core.auth.guards import require_admin, require_staff
from pydotorg.domains.mailing.models import EmailTemplate, EmailTemplateType
from pydotorg.domains.mailing.schemas import (
    BulkSendEmailRequest,
    BulkSendEmailResponse,
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


class EmailTemplateController(Controller):
    """Controller for email template management (admin only)."""

    path = "/api/admin/email-templates"
    tags = ["Admin"]
    guards = [require_staff]

    @get("/", status_code=HTTP_200_OK)
    async def list_templates(
        self,
        email_template_service: EmailTemplateService,
        template_type: EmailTemplateType | None = None,
        *,
        active_only: bool = False,
    ) -> list[EmailTemplateRead]:
        """List all email templates.

        Args:
            email_template_service: EmailTemplateService instance
            template_type: Optional filter by template type
            active_only: Only return active templates

        Returns:
            List of email templates
        """
        if active_only:
            templates = await email_template_service.list_active()
        elif template_type:
            templates = await email_template_service.list_by_type(template_type)
        else:
            templates = await email_template_service.list()

        return [EmailTemplateRead.model_validate(t) for t in templates]

    @get("/{template_id:uuid}", status_code=HTTP_200_OK)
    async def get_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> EmailTemplateRead:
        """Get a single email template by ID.

        Args:
            email_template_service: EmailTemplateService instance
            template_id: Template UUID

        Returns:
            Email template details

        Raises:
            NotFoundException: If template not found
        """
        try:
            template = await email_template_service.get(template_id)
        except NotFoundError as exc:
            raise NotFoundException(f"Email template {template_id} not found") from exc
        return EmailTemplateRead.model_validate(template)

    @get("/by-name/{internal_name:str}", status_code=HTTP_200_OK)
    async def get_template_by_name(
        self,
        email_template_service: EmailTemplateService,
        internal_name: str,
    ) -> EmailTemplateRead:
        """Get a single email template by internal name.

        Args:
            email_template_service: EmailTemplateService instance
            internal_name: Template internal name

        Returns:
            Email template details

        Raises:
            NotFoundException: If template not found
        """
        template = await email_template_service.get_by_internal_name(internal_name)
        if not template:
            raise NotFoundException(f"Email template '{internal_name}' not found")
        return EmailTemplateRead.model_validate(template)

    @post("/", status_code=HTTP_201_CREATED, guards=[require_admin])
    async def create_template(
        self,
        email_template_service: EmailTemplateService,
        data: Annotated[EmailTemplateCreate, Body(title="Email Template", description="Email template to create")],
    ) -> EmailTemplateRead:
        """Create a new email template.

        Args:
            email_template_service: EmailTemplateService instance
            data: Template creation data

        Returns:
            Created email template
        """
        template = await email_template_service.create(EmailTemplate(**data.model_dump()), auto_commit=True)
        return EmailTemplateRead.model_validate(template)

    @patch("/{template_id:uuid}", status_code=HTTP_200_OK, guards=[require_admin])
    async def update_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
        data: Annotated[EmailTemplateUpdate, Body(title="Email Template", description="Email template data to update")],
    ) -> EmailTemplateRead:
        """Update an existing email template.

        Args:
            email_template_service: EmailTemplateService instance
            template_id: Template UUID
            data: Template update data

        Returns:
            Updated email template

        Raises:
            NotFoundException: If template not found
        """
        try:
            template = await email_template_service.get(template_id)
        except NotFoundError as exc:
            raise NotFoundException(f"Email template {template_id} not found") from exc

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        await email_template_service.update(template, auto_commit=True)
        return EmailTemplateRead.model_validate(template)

    @delete("/{template_id:uuid}", status_code=HTTP_204_NO_CONTENT, guards=[require_admin])
    async def delete_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> None:
        """Delete an email template.

        Args:
            email_template_service: EmailTemplateService instance
            template_id: Template UUID

        Raises:
            NotFoundException: If template not found
        """
        try:
            await email_template_service.get(template_id)
        except NotFoundError as exc:
            raise NotFoundException(f"Email template {template_id} not found") from exc
        await email_template_service.delete(template_id, auto_commit=True)

    @post("/{template_id:uuid}/validate", status_code=HTTP_200_OK)
    async def validate_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> EmailTemplateValidation:
        """Validate a template's Jinja2 syntax.

        Args:
            email_template_service: EmailTemplateService instance
            template_id: Template UUID

        Returns:
            Validation result with any errors
        """
        errors = await email_template_service.validate_template(template_id)
        return EmailTemplateValidation(is_valid=len(errors) == 0, errors=errors)

    @post("/{template_id:uuid}/preview", status_code=HTTP_200_OK)
    async def preview_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
        data: Annotated[
            dict[str, Any] | None, Body(title="Context Data", description="Template context variables")
        ] = None,
    ) -> EmailTemplatePreview:
        """Preview a rendered email template.

        Args:
            email_template_service: EmailTemplateService instance
            template_id: Template UUID
            data: Optional context variables

        Returns:
            Rendered template preview
        """
        result = await email_template_service.preview_template(template_id, data)
        if "error" in result:
            raise NotFoundException(str(result["error"]))
        return EmailTemplatePreview(
            subject=result["subject"] or "",
            content_text=result["content_text"] or "",
            content_html=result.get("content_html"),
        )

    @post("/send", status_code=HTTP_200_OK)
    async def send_email(
        self,
        mailing_service: MailingService,
        data: Annotated[SendEmailRequest, Body(title="Email Request", description="Email send request data")],
    ) -> SendEmailResponse:
        """Send an email using a template.

        Args:
            mailing_service: MailingService instance
            data: Send email request data

        Returns:
            Send result with log ID
        """
        log = await mailing_service.send_email(
            template_name=data.template_name,
            to_email=data.to_email,
            context=data.context,
            cc=data.cc,
            bcc=data.bcc,
        )
        return SendEmailResponse(
            success=log.status == "sent",
            message=log.error_message or "Email sent successfully",
            log_id=log.id,
        )

    @post("/send-bulk", status_code=HTTP_200_OK, guards=[require_admin])
    async def send_bulk_email(
        self,
        mailing_service: MailingService,
        data: Annotated[
            BulkSendEmailRequest, Body(title="Bulk Email Request", description="Bulk email send request data")
        ],
    ) -> BulkSendEmailResponse:
        """Send bulk emails using a template.

        Args:
            mailing_service: MailingService instance
            data: Bulk send request data

        Returns:
            Bulk send result with statistics
        """
        logs = await mailing_service.send_bulk_email(
            template_name=data.template_name,
            recipients=data.recipients,
            context=data.context,
            per_recipient_context=data.per_recipient_context,
        )
        sent = sum(1 for log in logs if log.status == "sent")
        failed = sum(1 for log in logs if log.status == "failed")
        return BulkSendEmailResponse(
            total=len(logs),
            sent=sent,
            failed=failed,
            log_ids=[log.id for log in logs],
        )


class EmailLogController(Controller):
    """Controller for email log viewing (admin only)."""

    path = "/api/admin/email-logs"
    tags = ["Admin"]
    guards = [require_staff]

    @get("/", status_code=HTTP_200_OK)
    async def list_logs(
        self,
        email_log_service: EmailLogService,
        limit: int = 50,
        recipient: str | None = None,
        template_name: str | None = None,
        *,
        failed_only: bool = False,
    ) -> list[EmailLogRead]:
        """List email logs with optional filters.

        Args:
            email_log_service: EmailLogService instance
            limit: Maximum number of logs to return
            recipient: Filter by recipient email
            template_name: Filter by template name
            failed_only: Only return failed emails

        Returns:
            List of email logs
        """
        if recipient:
            logs = await email_log_service.list_by_recipient(recipient, limit=limit)
        elif template_name:
            logs = await email_log_service.list_by_template(template_name, limit=limit)
        elif failed_only:
            logs = await email_log_service.list_failed(limit=limit)
        else:
            logs = await email_log_service.list_recent(limit=limit)

        return [EmailLogRead.model_validate(log) for log in logs]

    @get("/{log_id:uuid}", status_code=HTTP_200_OK)
    async def get_log(
        self,
        email_log_service: EmailLogService,
        log_id: UUID,
    ) -> EmailLogRead:
        """Get a single email log entry.

        Args:
            email_log_service: EmailLogService instance
            log_id: Log UUID

        Returns:
            Email log details

        Raises:
            NotFoundException: If log not found
        """
        try:
            log = await email_log_service.get(log_id)
        except NotFoundError as exc:
            raise NotFoundException(f"Email log {log_id} not found") from exc
        return EmailLogRead.model_validate(log)
