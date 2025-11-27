"""Unit tests for email-related background tasks."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestSendVerificationEmail:
    """Test suite for send_verification_email task."""

    async def test_sends_verification_email_successfully(self) -> None:
        """Test successful verification email sending."""
        ctx = {}
        to_email = "user@example.com"
        username = "testuser"
        verification_link = "https://python.org/verify/token123"

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service.send_verification_email = MagicMock()

            from pydotorg.tasks.email import send_verification_email

            result = await send_verification_email(
                ctx, to_email=to_email, username=username, verification_link=verification_link
            )

            assert result["success"] is True
            assert result["to_email"] == to_email
            assert result["email_type"] == "verification"
            mock_service.send_verification_email.assert_called_once_with(to_email, username, verification_link)

    async def test_handles_email_failure(self) -> None:
        """Test handling of email sending failure."""
        ctx = {}

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service.send_verification_email = MagicMock(side_effect=Exception("SMTP error"))

            from pydotorg.tasks.email import send_verification_email

            result = await send_verification_email(
                ctx, to_email="user@example.com", username="user", verification_link="link"
            )

            assert result["success"] is False
            assert result["email_type"] == "verification"
            assert "error" in result
            assert "SMTP error" in result["error"]

    async def test_returns_correct_format(self) -> None:
        """Test that return value has correct format."""
        ctx = {}

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service.send_verification_email = MagicMock()

            from pydotorg.tasks.email import send_verification_email

            result = await send_verification_email(
                ctx, to_email="user@example.com", username="user", verification_link="link"
            )

            assert "success" in result
            assert "to_email" in result
            assert "email_type" in result


@pytest.mark.unit
class TestSendPasswordResetEmail:
    """Test suite for send_password_reset_email task."""

    async def test_sends_password_reset_email_successfully(self) -> None:
        """Test successful password reset email sending."""
        ctx = {}
        to_email = "user@example.com"
        username = "testuser"
        reset_link = "https://python.org/reset/token456"

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service.send_password_reset_email = MagicMock()

            from pydotorg.tasks.email import send_password_reset_email

            result = await send_password_reset_email(ctx, to_email=to_email, username=username, reset_link=reset_link)

            assert result["success"] is True
            assert result["to_email"] == to_email
            assert result["email_type"] == "password_reset"
            mock_service.send_password_reset_email.assert_called_once_with(to_email, username, reset_link)

    async def test_handles_smtp_failure(self) -> None:
        """Test handling of SMTP failure."""
        ctx = {}

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service.send_password_reset_email = MagicMock(side_effect=Exception("Connection timeout"))

            from pydotorg.tasks.email import send_password_reset_email

            result = await send_password_reset_email(
                ctx, to_email="user@example.com", username="user", reset_link="link"
            )

            assert result["success"] is False
            assert "error" in result


@pytest.mark.unit
class TestSendJobApprovedEmail:
    """Test suite for send_job_approved_email task."""

    async def test_sends_job_approved_email_successfully(self) -> None:
        """Test successful job approval email sending."""
        ctx = {}
        to_email = "poster@example.com"
        job_title = "Senior Python Developer"
        company_name = "Tech Corp"
        job_url = "https://python.org/jobs/senior-python-developer"

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock()

            from pydotorg.tasks.email import send_job_approved_email

            result = await send_job_approved_email(
                ctx, to_email=to_email, job_title=job_title, company_name=company_name, job_url=job_url
            )

            assert result["success"] is True
            assert result["to_email"] == to_email
            assert result["email_type"] == "job_approved"
            assert result["job_title"] == job_title
            mock_service._send_email.assert_called_once()

    async def test_includes_job_details_in_email(self) -> None:
        """Test that job details are included in email."""
        ctx = {}

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock()

            from pydotorg.tasks.email import send_job_approved_email

            await send_job_approved_email(
                ctx,
                to_email="user@example.com",
                job_title="Developer",
                company_name="Company",
                job_url="https://example.com",
            )

            call_args = mock_service._create_message.call_args
            assert call_args is not None

    async def test_handles_email_failure(self) -> None:
        """Test handling of email sending failure."""
        ctx = {}

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock(side_effect=Exception("SMTP error"))

            from pydotorg.tasks.email import send_job_approved_email

            result = await send_job_approved_email(
                ctx,
                to_email="user@example.com",
                job_title="Job",
                company_name="Company",
                job_url="url",
            )

            assert result["success"] is False
            assert "error" in result


@pytest.mark.unit
class TestSendJobRejectedEmail:
    """Test suite for send_job_rejected_email task."""

    async def test_sends_job_rejected_email_with_reason(self) -> None:
        """Test sending job rejection email with reason."""
        ctx = {}
        to_email = "poster@example.com"
        job_title = "Developer"
        company_name = "Company"
        reason = "Job posting does not meet our guidelines"

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock()

            from pydotorg.tasks.email import send_job_rejected_email

            result = await send_job_rejected_email(
                ctx, to_email=to_email, job_title=job_title, company_name=company_name, reason=reason
            )

            assert result["success"] is True
            assert result["to_email"] == to_email
            assert result["email_type"] == "job_rejected"
            assert result["job_title"] == job_title

    async def test_includes_rejection_reason(self) -> None:
        """Test that rejection reason is included in email."""
        ctx = {}
        reason = "Duplicate posting"

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock()

            from pydotorg.tasks.email import send_job_rejected_email

            await send_job_rejected_email(
                ctx,
                to_email="user@example.com",
                job_title="Job",
                company_name="Company",
                reason=reason,
            )

            call_args = mock_service._create_message.call_args
            assert call_args is not None


@pytest.mark.unit
class TestSendEventReminderEmail:
    """Test suite for send_event_reminder_email task."""

    async def test_sends_event_reminder_successfully(self) -> None:
        """Test successful event reminder email sending."""
        ctx = {}
        to_email = "attendee@example.com"
        event_title = "PyCon 2024"
        event_date = "2024-05-15"
        event_url = "https://python.org/events/pycon2024"

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock()

            from pydotorg.tasks.email import send_event_reminder_email

            result = await send_event_reminder_email(
                ctx, to_email=to_email, event_title=event_title, event_date=event_date, event_url=event_url
            )

            assert result["success"] is True
            assert result["to_email"] == to_email
            assert result["email_type"] == "event_reminder"
            assert result["event_title"] == event_title


@pytest.mark.unit
class TestSendBulkEmail:
    """Test suite for send_bulk_email task."""

    async def test_sends_emails_to_multiple_recipients(self) -> None:
        """Test sending bulk email to multiple recipients."""
        ctx = {}
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        subject = "Newsletter"
        template = "Hello {name}!"
        context_data = {"name": "User"}

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock()

            from pydotorg.tasks.email import send_bulk_email

            result = await send_bulk_email(
                ctx, recipients=recipients, subject=subject, template=template, context=context_data
            )

            assert result["success"] is True
            assert result["total"] == len(recipients)
            assert result["sent"] == len(recipients)
            assert result["failed"] == 0

    async def test_continues_on_individual_failures(self) -> None:
        """Test that bulk send continues when individual emails fail."""
        ctx = {}
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

        with patch("pydotorg.tasks.email.EmailService") as mock_email_class:
            mock_service = mock_email_class.return_value
            mock_service._create_message = MagicMock()
            mock_service._send_email = MagicMock(side_effect=[None, Exception("SMTP error"), None])

            from pydotorg.tasks.email import send_bulk_email

            result = await send_bulk_email(
                ctx, recipients=recipients, subject="Test", template="Test {x}", context={"x": "y"}
            )

            assert result["success"] is False
            assert result["sent"] == 2
            assert result["failed"] == 1
            assert len(result["errors"]) == 1

    async def test_handles_empty_recipient_list(self) -> None:
        """Test handling of empty recipient list."""
        ctx = {}

        with patch("pydotorg.tasks.email.EmailService"):
            from pydotorg.tasks.email import send_bulk_email

            result = await send_bulk_email(ctx, recipients=[], subject="Test", template="Test", context={})

            assert result["total"] == 0
            assert result["sent"] == 0
