"""Admin email management service."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select

from pydotorg.domains.mailing.models import EmailLog, EmailTemplate

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EmailAdminService:
    """Service for admin email template and log management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_templates(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        *,
        active_only: bool = False,
    ) -> tuple[list[EmailTemplate], int]:
        """List email templates with filtering and pagination.

        Args:
            limit: Maximum number of templates to return
            offset: Number of templates to skip
            search: Search query for template name or display name
            active_only: Only return active templates

        Returns:
            Tuple of (templates list, total count)
        """
        query = select(EmailTemplate)

        if active_only:
            query = query.where(EmailTemplate.is_active.is_(True))

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    EmailTemplate.internal_name.ilike(search_term),
                    EmailTemplate.display_name.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(EmailTemplate.display_name).limit(limit).offset(offset)
        result = await self.session.execute(query)
        templates = list(result.scalars().all())

        return templates, total

    async def get_template(self, template_id: UUID) -> EmailTemplate | None:
        """Get a template by ID.

        Args:
            template_id: The template UUID

        Returns:
            EmailTemplate if found, None otherwise
        """
        result = await self.session.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
        return result.scalar_one_or_none()

    async def list_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        *,
        failed_only: bool = False,
    ) -> tuple[list[EmailLog], int]:
        """List email logs with filtering and pagination.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            search: Search query for recipient email
            failed_only: Only return failed emails

        Returns:
            Tuple of (logs list, total count)
        """
        query = select(EmailLog)

        if failed_only:
            query = query.where(EmailLog.status == "failed")

        if search:
            search_term = f"%{search}%"
            query = query.where(EmailLog.recipient_email.ilike(search_term))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(EmailLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def get_log(self, log_id: UUID) -> EmailLog | None:
        """Get an email log by ID.

        Args:
            log_id: The log UUID

        Returns:
            EmailLog if found, None otherwise
        """
        result = await self.session.execute(select(EmailLog).where(EmailLog.id == log_id))
        return result.scalar_one_or_none()

    async def get_dashboard_stats(self) -> dict:
        """Get email dashboard statistics.

        Returns:
            Dictionary with email stats including template count,
            recent sends, and failed count
        """
        template_count_query = select(func.count()).select_from(EmailTemplate)
        template_result = await self.session.execute(template_count_query)
        template_count = template_result.scalar() or 0

        recent_sends_query = select(func.count()).where(EmailLog.status == "sent")
        recent_sends_result = await self.session.execute(recent_sends_query)
        recent_sends_count = recent_sends_result.scalar() or 0

        failed_count_query = select(func.count()).where(EmailLog.status == "failed")
        failed_result = await self.session.execute(failed_count_query)
        failed_count = failed_result.scalar() or 0

        pending_count_query = select(func.count()).where(EmailLog.status == "pending")
        pending_result = await self.session.execute(pending_count_query)
        pending_count = pending_result.scalar() or 0

        total_logs_query = select(func.count()).select_from(EmailLog)
        total_logs_result = await self.session.execute(total_logs_query)
        total_logs = total_logs_result.scalar() or 0

        return {
            "template_count": template_count,
            "recent_sends_count": recent_sends_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "total_logs": total_logs,
        }
