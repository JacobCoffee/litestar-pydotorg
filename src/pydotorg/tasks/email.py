"""Background tasks for sending emails via SAQ."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydotorg.core.email.service import EmailService

if TYPE_CHECKING:
    from saq import Context

logger = logging.getLogger(__name__)


async def send_verification_email(
    ctx: Context,
    *,
    to_email: str,
    username: str,
    verification_link: str,
) -> dict[str, Any]:
    """Send email verification email.

    Args:
        ctx: SAQ job context
        to_email: Recipient email address
        username: User's username
        verification_link: Verification URL

    Returns:
        Dict with success status and metadata
    """
    logger.info("Sending verification email", extra={"to_email": to_email, "username": username})

    try:
        email_service = EmailService()
        email_service.send_verification_email(to_email, username, verification_link)

        logger.info("Verification email sent successfully", extra={"to_email": to_email})
        return {"success": True, "to_email": to_email, "email_type": "verification"}

    except Exception as e:
        logger.exception("Failed to send verification email", extra={"to_email": to_email, "error": str(e)})
        return {"success": False, "to_email": to_email, "email_type": "verification", "error": str(e)}


async def send_password_reset_email(
    ctx: Context,
    *,
    to_email: str,
    username: str,
    reset_link: str,
) -> dict[str, Any]:
    """Send password reset email.

    Args:
        ctx: SAQ job context
        to_email: Recipient email address
        username: User's username
        reset_link: Password reset URL

    Returns:
        Dict with success status and metadata
    """
    logger.info("Sending password reset email", extra={"to_email": to_email, "username": username})

    try:
        email_service = EmailService()
        email_service.send_password_reset_email(to_email, username, reset_link)

        logger.info("Password reset email sent successfully", extra={"to_email": to_email})
        return {"success": True, "to_email": to_email, "email_type": "password_reset"}

    except Exception as e:
        logger.exception("Failed to send password reset email", extra={"to_email": to_email, "error": str(e)})
        return {"success": False, "to_email": to_email, "email_type": "password_reset", "error": str(e)}


async def send_job_submitted_email(
    ctx: Context,
    *,
    to_email: str,
    job_title: str,
    company_name: str,
    job_id: str,
    admin_url: str,
) -> dict[str, Any]:
    """Send job submission notification email to administrators.

    Args:
        ctx: SAQ job context
        to_email: Admin email address
        job_title: Title of submitted job posting
        company_name: Company name
        job_id: Job ID for reference
        admin_url: URL to admin job review page

    Returns:
        Dict with success status and metadata
    """
    logger.info(
        "Sending job submitted email",
        extra={"to_email": to_email, "job_title": job_title, "company_name": company_name},
    )

    try:
        email_service = EmailService()
        subject = f"New Job Posting Requires Review - {company_name}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Job Posting - Python.org</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #306998; margin-top: 0;">New Job Posting Submitted</h1>
        <p>A new job posting has been submitted and requires review:</p>
        <div style="background-color: #e7f3ff; border-left: 4px solid #306998; padding: 15px; margin: 20px 0;">
            <h2 style="margin: 0 0 10px 0; color: #306998;">{job_title}</h2>
            <p style="margin: 0;"><strong>Company:</strong> {company_name}</p>
            <p style="margin: 0; font-size: 12px; color: #666;">Job ID: {job_id}</p>
        </div>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{admin_url}"
               style="background-color: #306998; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                Review Job Posting
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">
            Please review this job posting and either approve or reject it.
        </p>
    </div>
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <p>&copy; Python Software Foundation</p>
    </div>
</body>
</html>
"""

        text_content = f"""
New Job Posting Submitted

A new job posting has been submitted and requires review:

Title: {job_title}
Company: {company_name}
Job ID: {job_id}

Review the job posting: {admin_url}

Please review this job posting and either approve or reject it.

---
Python Software Foundation
"""

        msg = email_service._create_message(to_email, subject, text_content, html_content)
        email_service._send_email(msg)

        logger.info("Job submitted email sent successfully", extra={"to_email": to_email, "job_title": job_title})
        return {
            "success": True,
            "to_email": to_email,
            "email_type": "job_submitted",
            "job_title": job_title,
        }

    except Exception as e:
        logger.exception("Failed to send job submitted email", extra={"to_email": to_email, "error": str(e)})
        return {
            "success": False,
            "to_email": to_email,
            "email_type": "job_submitted",
            "error": str(e),
        }


async def send_job_approved_email(
    ctx: Context,
    *,
    to_email: str,
    job_title: str,
    company_name: str,
    job_url: str,
) -> dict[str, Any]:
    """Send job approval notification email.

    Args:
        ctx: SAQ job context
        to_email: Recipient email address
        job_title: Title of approved job posting
        company_name: Company name
        job_url: URL to view the job posting

    Returns:
        Dict with success status and metadata
    """
    logger.info(
        "Sending job approved email",
        extra={"to_email": to_email, "job_title": job_title, "company_name": company_name},
    )

    try:
        email_service = EmailService()
        subject = f"Your Job Posting Has Been Approved - {job_title}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Posting Approved - Python.org</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #306998; margin-top: 0;">Job Posting Approved!</h1>
        <p>Congratulations!</p>
        <p>Your job posting <strong>"{job_title}"</strong> at <strong>{company_name}</strong> has been approved and is now live on Python.org Jobs.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{job_url}"
               style="background-color: #306998; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                View Job Posting
            </a>
        </div>
        <p>Your posting will be visible to thousands of Python developers looking for opportunities.</p>
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            Thank you for supporting the Python community!
        </p>
    </div>
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <p>&copy; Python Software Foundation</p>
    </div>
</body>
</html>
"""

        text_content = f"""
Job Posting Approved!

Congratulations!

Your job posting "{job_title}" at {company_name} has been approved and is now live on Python.org Jobs.

View your posting: {job_url}

Your posting will be visible to thousands of Python developers looking for opportunities.

Thank you for supporting the Python community!

---
Python Software Foundation
"""

        msg = email_service._create_message(to_email, subject, text_content, html_content)
        email_service._send_email(msg)

        logger.info("Job approved email sent successfully", extra={"to_email": to_email, "job_title": job_title})
        return {
            "success": True,
            "to_email": to_email,
            "email_type": "job_approved",
            "job_title": job_title,
        }

    except Exception as e:
        logger.exception("Failed to send job approved email", extra={"to_email": to_email, "error": str(e)})
        return {
            "success": False,
            "to_email": to_email,
            "email_type": "job_approved",
            "error": str(e),
        }


async def send_job_rejected_email(
    ctx: Context,
    *,
    to_email: str,
    job_title: str,
    company_name: str,
    reason: str,
) -> dict[str, Any]:
    """Send job rejection notification email.

    Args:
        ctx: SAQ job context
        to_email: Recipient email address
        job_title: Title of rejected job posting
        company_name: Company name
        reason: Reason for rejection

    Returns:
        Dict with success status and metadata
    """
    logger.info(
        "Sending job rejected email",
        extra={"to_email": to_email, "job_title": job_title, "company_name": company_name},
    )

    try:
        email_service = EmailService()
        subject = f"Job Posting Update - {job_title}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Posting Update - Python.org</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #306998; margin-top: 0;">Job Posting Update</h1>
        <p>Hello,</p>
        <p>We've reviewed your job posting <strong>"{job_title}"</strong> at <strong>{company_name}</strong>.</p>
        <p>Unfortunately, we're unable to approve this posting at this time for the following reason:</p>
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; color: #856404;">{reason}</p>
        </div>
        <p>If you have questions or would like to resubmit your posting with modifications, please contact us.</p>
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            Thank you for your interest in the Python community.
        </p>
    </div>
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <p>&copy; Python Software Foundation</p>
    </div>
</body>
</html>
"""

        text_content = f"""
Job Posting Update

Hello,

We've reviewed your job posting "{job_title}" at {company_name}.

Unfortunately, we're unable to approve this posting at this time for the following reason:

{reason}

If you have questions or would like to resubmit your posting with modifications, please contact us.

Thank you for your interest in the Python community.

---
Python Software Foundation
"""

        msg = email_service._create_message(to_email, subject, text_content, html_content)
        email_service._send_email(msg)

        logger.info("Job rejected email sent successfully", extra={"to_email": to_email, "job_title": job_title})
        return {
            "success": True,
            "to_email": to_email,
            "email_type": "job_rejected",
            "job_title": job_title,
        }

    except Exception as e:
        logger.exception("Failed to send job rejected email", extra={"to_email": to_email, "error": str(e)})
        return {
            "success": False,
            "to_email": to_email,
            "email_type": "job_rejected",
            "error": str(e),
        }


async def send_event_reminder_email(
    ctx: Context,
    *,
    to_email: str,
    event_title: str,
    event_date: str,
    event_url: str,
) -> dict[str, Any]:
    """Send event reminder notification email.

    Args:
        ctx: SAQ job context
        to_email: Recipient email address
        event_title: Title of the event
        event_date: Formatted date string for the event
        event_url: URL to event details

    Returns:
        Dict with success status and metadata
    """
    logger.info(
        "Sending event reminder email",
        extra={"to_email": to_email, "event_title": event_title, "event_date": event_date},
    )

    try:
        email_service = EmailService()
        subject = f"Reminder: {event_title} - {event_date}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Reminder - Python.org</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #306998; margin-top: 0;">Event Reminder</h1>
        <p>Hello,</p>
        <p>This is a friendly reminder about an upcoming Python event you're registered for:</p>
        <div style="background-color: #e7f3ff; border-left: 4px solid #306998; padding: 15px; margin: 20px 0;">
            <h2 style="margin: 0 0 10px 0; color: #306998;">{event_title}</h2>
            <p style="margin: 0; font-size: 16px;"><strong>Date:</strong> {event_date}</p>
        </div>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{event_url}"
               style="background-color: #306998; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                View Event Details
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">
            We look forward to seeing you there!
        </p>
    </div>
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <p>&copy; Python Software Foundation</p>
    </div>
</body>
</html>
"""

        text_content = f"""
Event Reminder

Hello,

This is a friendly reminder about an upcoming Python event you're registered for:

{event_title}
Date: {event_date}

View event details: {event_url}

We look forward to seeing you there!

---
Python Software Foundation
"""

        msg = email_service._create_message(to_email, subject, text_content, html_content)
        email_service._send_email(msg)

        logger.info(
            "Event reminder email sent successfully",
            extra={"to_email": to_email, "event_title": event_title},
        )
        return {
            "success": True,
            "to_email": to_email,
            "email_type": "event_reminder",
            "event_title": event_title,
        }

    except Exception as e:
        logger.exception("Failed to send event reminder email", extra={"to_email": to_email, "error": str(e)})
        return {
            "success": False,
            "to_email": to_email,
            "email_type": "event_reminder",
            "error": str(e),
        }


async def send_bulk_email(
    ctx: Context,
    *,
    recipients: list[str],
    subject: str,
    template: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Send same email to multiple recipients.

    Args:
        ctx: SAQ job context
        recipients: List of recipient email addresses
        subject: Email subject line
        template: Email template identifier or raw content
        context: Template context variables

    Returns:
        Dict with success status and metadata
    """
    logger.info("Sending bulk email", extra={"recipient_count": len(recipients), "subject": subject})

    email_service = EmailService()
    sent_count = 0
    failed_count = 0
    errors: list[str] = []

    for to_email in recipients:
        try:
            html_content = template.format(**context)
            text_content = html_content

            msg = email_service._create_message(to_email, subject, text_content, html_content)
            email_service._send_email(msg)

            sent_count += 1
            logger.debug("Bulk email sent to recipient", extra={"to_email": to_email})

        except Exception as e:
            failed_count += 1
            error_msg = f"{to_email}: {e!s}"
            errors.append(error_msg)
            logger.exception("Failed to send bulk email to recipient", extra={"to_email": to_email, "error": str(e)})

    logger.info(
        "Bulk email task completed",
        extra={"total": len(recipients), "sent": sent_count, "failed": failed_count},
    )

    return {
        "success": failed_count == 0,
        "email_type": "bulk",
        "subject": subject,
        "total": len(recipients),
        "sent": sent_count,
        "failed": failed_count,
        "errors": errors,
    }
