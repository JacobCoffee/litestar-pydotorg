"""Email service for sending emails via SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from pydotorg.config import settings
from pydotorg.core.email.templates import (
    get_password_reset_email_html,
    get_password_reset_email_text,
    get_verification_email_html,
    get_verification_email_text,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from email.message import Message


class EmailService:
    def __init__(self) -> None:
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
        html_content: str,
    ) -> Message:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        msg.attach(part1)
        msg.attach(part2)

        return msg

    def _send_email(self, msg: Message) -> None:
        if not self.smtp_user or not self.smtp_password:
            return

        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.send_message(msg)
            server.quit()
        except smtplib.SMTPException:
            logger.exception("Failed to send email via SMTP")
        except OSError:
            logger.exception("Network error while sending email")

    def send_verification_email(
        self,
        to_email: str,
        username: str,
        verification_link: str,
    ) -> None:
        subject = "Verify Your Email - Python.org"
        html_content = get_verification_email_html(username, verification_link)
        text_content = get_verification_email_text(username, verification_link)

        msg = self._create_message(to_email, subject, text_content, html_content)
        self._send_email(msg)

    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        reset_link: str,
    ) -> None:
        subject = "Password Reset Request - Python.org"
        html_content = get_password_reset_email_html(username, reset_link)
        text_content = get_password_reset_email_text(username, reset_link)

        msg = self._create_message(to_email, subject, text_content, html_content)
        self._send_email(msg)


email_service = EmailService()
