"""Mailing domain Pydantic schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from pydotorg.domains.mailing.models import EmailTemplateType


class EmailTemplateBase(BaseModel):
    """Base schema for email templates."""

    internal_name: str = Field(..., min_length=1, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    template_type: EmailTemplateType = EmailTemplateType.TRANSACTIONAL
    subject: str = Field(..., min_length=1, max_length=255)
    content_text: str = Field(..., min_length=1)
    content_html: str | None = None
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating an email template."""


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template."""

    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    template_type: EmailTemplateType | None = None
    subject: str | None = Field(None, min_length=1, max_length=255)
    content_text: str | None = Field(None, min_length=1)
    content_html: str | None = None
    is_active: bool | None = None


class EmailTemplateRead(EmailTemplateBase):
    """Schema for reading an email template."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class EmailTemplatePreview(BaseModel):
    """Schema for previewing rendered email template."""

    subject: str
    content_text: str
    content_html: str | None = None


class EmailTemplateValidation(BaseModel):
    """Schema for template validation results."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class EmailLogBase(BaseModel):
    """Base schema for email logs."""

    template_name: str
    recipient_email: EmailStr
    subject: str
    status: str = "pending"
    error_message: str | None = None


class EmailLogCreate(EmailLogBase):
    """Schema for creating an email log entry."""


class EmailLogRead(EmailLogBase):
    """Schema for reading an email log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class SendEmailRequest(BaseModel):
    """Schema for sending an email via template."""

    template_name: str = Field(..., description="Internal name of the email template")
    to_email: EmailStr = Field(..., description="Recipient email address")
    context: dict[str, Any] = Field(default_factory=dict, description="Template context variables")
    cc: list[EmailStr] | None = Field(None, description="CC recipients")
    bcc: list[EmailStr] | None = Field(None, description="BCC recipients")


class SendEmailResponse(BaseModel):
    """Schema for send email response."""

    success: bool
    message: str
    log_id: UUID | None = None


class BulkSendEmailRequest(BaseModel):
    """Schema for sending bulk emails."""

    template_name: str = Field(..., description="Internal name of the email template")
    recipients: list[EmailStr] = Field(..., min_length=1, description="List of recipient emails")
    context: dict[str, Any] = Field(default_factory=dict, description="Shared template context")
    per_recipient_context: dict[str, dict[str, Any]] | None = Field(
        None,
        description="Per-recipient context overrides (keyed by email)",
    )


class BulkSendEmailResponse(BaseModel):
    """Schema for bulk send email response."""

    total: int
    sent: int
    failed: int
    log_ids: list[UUID]
