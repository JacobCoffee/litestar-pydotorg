"""Mailing domain models.

This module provides database-driven email templates that can be rendered
with context variables using Jinja2. Templates can be managed via the admin
interface and used for newsletters, notifications, and transactional emails.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar

from jinja2 import Environment, TemplateSyntaxError, UndefinedError
from sqlalchemy import Boolean, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from collections.abc import Mapping


class EmailTemplateType(StrEnum):
    """Types of email templates."""

    TRANSACTIONAL = "transactional"
    NOTIFICATION = "notification"
    NEWSLETTER = "newsletter"
    MARKETING = "marketing"
    SYSTEM = "system"


class EmailTemplate(AuditBase):
    """Database-driven email template.

    Stores email templates with Jinja2 content that can be rendered
    with context variables. Supports both plain text and HTML content.

    Attributes:
        internal_name: Unique identifier used in code (e.g., "job_approved")
        display_name: Human-readable name for admin UI
        description: Description of when/how this template is used
        template_type: Category of email (transactional, newsletter, etc.)
        subject: Email subject (supports Jinja2 templating)
        content_text: Plain text email body (supports Jinja2 templating)
        content_html: HTML email body (supports Jinja2 templating, optional)
        is_active: Whether this template can be used
        default_context: Default context variables as JSON
    """

    __tablename__ = "email_templates"

    internal_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[EmailTemplateType] = mapped_column(
        SAEnum(EmailTemplateType, native_enum=False, length=32),
        default=EmailTemplateType.TRANSACTIONAL,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(255))
    content_text: Mapped[str] = mapped_column(Text)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    _jinja_env: ClassVar[Environment | None] = None

    @classmethod
    def _get_jinja_env(cls) -> Environment:
        """Get or create Jinja2 environment for template rendering."""
        if cls._jinja_env is None:
            cls._jinja_env = Environment(autoescape=True)
        return cls._jinja_env

    def render_subject(self, context: Mapping[str, Any] | None = None) -> str:
        """Render the email subject with context variables.

        Args:
            context: Dictionary of variables to use in template

        Returns:
            Rendered subject string

        Raises:
            TemplateSyntaxError: If template syntax is invalid
        """
        env = self._get_jinja_env()
        template = env.from_string(self.subject)
        return template.render(context or {})

    def render_content_text(self, context: Mapping[str, Any] | None = None) -> str:
        """Render plain text email content with context variables.

        Args:
            context: Dictionary of variables to use in template

        Returns:
            Rendered plain text content

        Raises:
            TemplateSyntaxError: If template syntax is invalid
        """
        if not self.content_text or self.content_text == "None":
            return ""
        env = self._get_jinja_env()
        template = env.from_string(self.content_text)
        return template.render(context or {})

    def render_content_html(self, context: Mapping[str, Any] | None = None) -> str | None:
        """Render HTML email content with context variables.

        Args:
            context: Dictionary of variables to use in template

        Returns:
            Rendered HTML content, or None if no HTML template

        Raises:
            TemplateSyntaxError: If template syntax is invalid
        """
        if not self.content_html or self.content_html == "None":
            return None
        env = self._get_jinja_env()
        template = env.from_string(self.content_html)
        return template.render(context or {})

    def validate_templates(self) -> list[str]:
        """Validate all template strings for syntax errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors: list[str] = []
        env = self._get_jinja_env()

        for field_name in ("subject", "content_text", "content_html"):
            content = getattr(self, field_name)
            if not content:
                continue
            try:
                template = env.from_string(content)
                template.render({})
            except TemplateSyntaxError as e:
                errors.append(f"{field_name}: Template syntax error - {e}")
            except UndefinedError:
                pass

        return errors

    def __repr__(self) -> str:
        return f"<EmailTemplate(internal_name={self.internal_name!r}, type={self.template_type.value!r})>"


class EmailLog(AuditBase):
    """Log of sent emails for audit and debugging.

    Tracks all emails sent through the system with their status,
    recipient, and template information.

    Attributes:
        template_name: Internal name of template used (or "custom")
        recipient_email: Email address of recipient
        subject: Actual rendered subject sent
        status: Delivery status (pending, sent, failed, bounced)
        error_message: Error details if failed
        sent_at: Timestamp when email was sent
        metadata: Additional metadata as JSON (e.g., user_id, context)
    """

    __tablename__ = "email_logs"

    template_name: Mapped[str] = mapped_column(String(128), index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<EmailLog(to={self.recipient_email!r}, template={self.template_name!r}, status={self.status!r})>"
