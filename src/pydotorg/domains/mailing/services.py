"""Mailing domain services.

This module provides services for managing email templates and sending
emails through the template system. It integrates with the core EmailService
for actual SMTP delivery.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Any

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from jinja2 import TemplateSyntaxError, UndefinedError
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate, EmailTemplateType
from pydotorg.domains.mailing.repositories import EmailLogRepository, EmailTemplateRepository

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EmailTemplateService(SQLAlchemyAsyncRepositoryService[EmailTemplate]):
    """Service for managing email templates."""

    repository_type = EmailTemplateRepository

    async def get_by_internal_name(self, internal_name: str) -> EmailTemplate | None:
        """Get an email template by its internal name.

        Args:
            internal_name: The unique internal identifier

        Returns:
            EmailTemplate if found, None otherwise
        """
        result = await self.repository.session.execute(
            select(EmailTemplate).where(EmailTemplate.internal_name == internal_name)
        )
        return result.scalar_one_or_none()

    async def get_active_by_name(self, internal_name: str) -> EmailTemplate | None:
        """Get an active email template by internal name.

        Args:
            internal_name: The unique internal identifier

        Returns:
            Active EmailTemplate if found, None otherwise
        """
        result = await self.repository.session.execute(
            select(EmailTemplate).where(
                EmailTemplate.internal_name == internal_name,
                EmailTemplate.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_type(self, template_type: EmailTemplateType) -> Sequence[EmailTemplate]:
        """List all templates of a specific type.

        Args:
            template_type: The type of templates to list

        Returns:
            Sequence of matching EmailTemplates
        """
        result = await self.repository.session.execute(
            select(EmailTemplate)
            .where(EmailTemplate.template_type == template_type)
            .order_by(EmailTemplate.display_name)
        )
        return result.scalars().all()

    async def list_active(self) -> Sequence[EmailTemplate]:
        """List all active email templates.

        Returns:
            Sequence of active EmailTemplates
        """
        result = await self.repository.session.execute(
            select(EmailTemplate).where(EmailTemplate.is_active.is_(True)).order_by(EmailTemplate.display_name)
        )
        return result.scalars().all()

    async def validate_template(self, template_id: UUID) -> list[str]:
        """Validate a template's Jinja2 syntax.

        Args:
            template_id: The template ID to validate

        Returns:
            List of error messages (empty if valid)
        """
        template = await self.get(template_id)
        if not template:
            return ["Template not found"]
        return template.validate_templates()

    async def preview_template(
        self,
        template_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> dict[str, str | None]:
        """Preview a rendered template.

        Args:
            template_id: The template ID to preview
            context: Optional context variables for rendering

        Returns:
            Dict with rendered subject, content_text, content_html
        """
        template = await self.get(template_id)
        if not template:
            return {"error": "Template not found"}

        try:
            return {
                "subject": template.render_subject(context),
                "content_text": template.render_content_text(context),
                "content_html": template.render_content_html(context),
            }
        except (TemplateSyntaxError, UndefinedError) as e:
            return {"error": str(e)}


class EmailLogService(SQLAlchemyAsyncRepositoryService[EmailLog]):
    """Service for managing email logs."""

    repository_type = EmailLogRepository

    async def list_by_recipient(self, email: str, limit: int = 50) -> Sequence[EmailLog]:
        """List email logs for a specific recipient.

        Args:
            email: Recipient email address
            limit: Maximum number of logs to return

        Returns:
            Sequence of EmailLogs
        """
        result = await self.repository.session.execute(
            select(EmailLog).where(EmailLog.recipient_email == email).order_by(EmailLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def list_by_template(self, template_name: str, limit: int = 50) -> Sequence[EmailLog]:
        """List email logs for a specific template.

        Args:
            template_name: Internal template name
            limit: Maximum number of logs to return

        Returns:
            Sequence of EmailLogs
        """
        result = await self.repository.session.execute(
            select(EmailLog)
            .where(EmailLog.template_name == template_name)
            .order_by(EmailLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_failed(self, limit: int = 50) -> Sequence[EmailLog]:
        """List failed email logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            Sequence of failed EmailLogs
        """
        result = await self.repository.session.execute(
            select(EmailLog).where(EmailLog.status == "failed").order_by(EmailLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def list_recent(self, limit: int = 50) -> Sequence[EmailLog]:
        """List recent email logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            Sequence of recent EmailLogs
        """
        result = await self.repository.session.execute(
            select(EmailLog).order_by(EmailLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


class MailingService:
    """Service for sending emails using database templates.

    This service combines EmailTemplateService with actual email delivery,
    logging all sent emails to EmailLog.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.template_service = EmailTemplateService(session=session)
        self.log_service = EmailLogService(session=session)

        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls

    def _create_message(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> MIMEMultipart:
        """Create an email message.

        Args:
            to_email: Recipient email
            subject: Email subject
            text_content: Plain text content
            html_content: Optional HTML content
            cc: Optional CC recipients
            bcc: Optional BCC recipients

        Returns:
            MIMEMultipart message ready to send
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)

        msg.attach(MIMEText(text_content, "plain"))
        if html_content:
            msg.attach(MIMEText(html_content, "html"))

        return msg

    def _send_smtp(self, msg: MIMEMultipart, to_addrs: list[str]) -> None:
        """Send email via SMTP.

        Args:
            msg: The email message
            to_addrs: All recipient addresses (To, CC, BCC)

        Raises:
            smtplib.SMTPException: If sending fails
        """
        if self.use_tls:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

        if self.smtp_user and self.smtp_password:
            server.login(self.smtp_user, self.smtp_password)

        server.sendmail(self.from_email, to_addrs, msg.as_string())
        server.quit()

    async def send_email(
        self,
        template_name: str,
        to_email: str,
        context: dict[str, Any] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> EmailLog:
        """Send an email using a database template.

        Args:
            template_name: Internal name of the template
            to_email: Recipient email address
            context: Template context variables
            cc: Optional CC recipients
            bcc: Optional BCC recipients

        Returns:
            EmailLog entry for the sent email

        Raises:
            ValueError: If template not found or inactive
        """
        template = await self.template_service.get_active_by_name(template_name)
        if not template:
            return await self.log_service.create(
                EmailLog(
                    template_name=template_name,
                    recipient_email=to_email,
                    subject="[Template not found]",
                    status="failed",
                    error_message=f"Template '{template_name}' not found or inactive",
                ),
                auto_commit=True,
            )

        try:
            subject = template.render_subject(context) or "[No Subject]"
            text_content = template.render_content_text(context) or ""
            html_content = template.render_content_html(context)
        except (TemplateSyntaxError, UndefinedError) as e:
            return await self.log_service.create(
                EmailLog(
                    template_name=template_name,
                    recipient_email=to_email,
                    subject="[Render error]",
                    status="failed",
                    error_message=f"Template render error: {e}",
                ),
                auto_commit=True,
            )

        log = await self.log_service.create(
            EmailLog(
                template_name=template_name,
                recipient_email=to_email,
                subject=subject,
                status="pending",
            ),
            auto_commit=True,
        )

        try:
            msg = self._create_message(to_email, subject, text_content, html_content, cc, bcc)
            all_recipients = [to_email]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            self._send_smtp(msg, all_recipients)

            log.status = "sent"
            await self.log_service.update(log, auto_commit=True)
            logger.info("Email sent successfully to %s using template %s", to_email, template_name)

        except smtplib.SMTPException as e:
            log.status = "failed"
            log.error_message = f"SMTP error: {e}"
            await self.log_service.update(log, auto_commit=True)
            logger.exception("Failed to send email to %s", to_email)

        except OSError as e:
            log.status = "failed"
            log.error_message = f"Network error: {e}"
            await self.log_service.update(log, auto_commit=True)
            logger.exception("Network error sending email to %s", to_email)

        return log

    async def send_bulk_email(
        self,
        template_name: str,
        recipients: list[str],
        context: dict[str, Any] | None = None,
        per_recipient_context: dict[str, dict[str, Any]] | None = None,
    ) -> list[EmailLog]:
        """Send bulk emails using a database template.

        Args:
            template_name: Internal name of the template
            recipients: List of recipient email addresses
            context: Shared template context variables
            per_recipient_context: Per-recipient context overrides

        Returns:
            List of EmailLog entries
        """
        logs = []
        for recipient in recipients:
            recipient_context = dict(context or {})
            if per_recipient_context and recipient in per_recipient_context:
                recipient_context.update(per_recipient_context[recipient])

            log = await self.send_email(template_name, recipient, recipient_context)
            logs.append(log)

        return logs

    async def send_custom_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> EmailLog:
        """Send a custom email without using a template.

        Args:
            to_email: Recipient email address
            subject: Email subject
            text_content: Plain text content
            html_content: Optional HTML content
            cc: Optional CC recipients
            bcc: Optional BCC recipients

        Returns:
            EmailLog entry
        """
        log = await self.log_service.create(
            EmailLog(
                template_name="custom",
                recipient_email=to_email,
                subject=subject,
                status="pending",
            ),
            auto_commit=True,
        )

        try:
            msg = self._create_message(to_email, subject, text_content, html_content, cc, bcc)
            all_recipients = [to_email]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            self._send_smtp(msg, all_recipients)

            log.status = "sent"
            await self.log_service.update(log, auto_commit=True)
            logger.info("Custom email sent successfully to %s", to_email)

        except (smtplib.SMTPException, OSError) as e:
            log.status = "failed"
            log.error_message = str(e)
            await self.log_service.update(log, auto_commit=True)
            logger.exception("Failed to send custom email to %s", to_email)

        return log
