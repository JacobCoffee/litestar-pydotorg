"""Admin email management service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
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
        status: str | None = None,
        template_type: str | None = None,
    ) -> tuple[list[EmailTemplate], int]:
        """List email templates with filtering and pagination.

        Args:
            limit: Maximum number of templates to return
            offset: Number of templates to skip
            search: Search query for template name or display name
            status: Filter by status (active, inactive)
            template_type: Filter by template type

        Returns:
            Tuple of (templates list, total count)
        """
        query = select(EmailTemplate)

        if status == "active":
            query = query.where(EmailTemplate.is_active.is_(True))
        elif status == "inactive":
            query = query.where(EmailTemplate.is_active.is_(False))

        if template_type:
            query = query.where(EmailTemplate.template_type == template_type)

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
        status: str | None = None,
        template_name: str | None = None,
        recipient: str | None = None,
        time_range: str | None = None,
    ) -> tuple[list[EmailLog], int]:
        """List email logs with filtering and pagination.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            status: Filter by status (sent, failed, bounced, pending)
            template_name: Filter by template internal name
            recipient: Filter by recipient email
            time_range: Time range filter (24h, 7d, 30d, all)

        Returns:
            Tuple of (logs list, total count)
        """
        query = select(EmailLog)

        if status:
            query = query.where(EmailLog.status == status)

        if template_name:
            query = query.where(EmailLog.template_name == template_name)

        if recipient:
            search_term = f"%{recipient}%"
            query = query.where(EmailLog.recipient_email.ilike(search_term))

        if time_range and time_range != "all":
            now = datetime.now(tz=UTC)
            if time_range == "24h":
                cutoff = now - timedelta(hours=24)
            elif time_range == "7d":
                cutoff = now - timedelta(days=7)
            elif time_range == "30d":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = None
            if cutoff:
                query = query.where(EmailLog.created_at >= cutoff)

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

    async def get_log_stats(self) -> dict:
        """Get email log statistics for the logs page.

        Returns:
            Dictionary with log counts by status
        """
        total_logs_query = select(func.count()).select_from(EmailLog)
        total_logs_result = await self.session.execute(total_logs_query)
        total_logs = total_logs_result.scalar() or 0

        sent_query = select(func.count()).where(EmailLog.status == "sent")
        sent_result = await self.session.execute(sent_query)
        sent_logs = sent_result.scalar() or 0

        failed_query = select(func.count()).where(EmailLog.status == "failed")
        failed_result = await self.session.execute(failed_query)
        failed_logs = failed_result.scalar() or 0

        bounced_query = select(func.count()).where(EmailLog.status == "bounced")
        bounced_result = await self.session.execute(bounced_query)
        bounced_logs = bounced_result.scalar() or 0

        pending_query = select(func.count()).where(EmailLog.status == "pending")
        pending_result = await self.session.execute(pending_query)
        pending_logs = pending_result.scalar() or 0

        return {
            "total_logs": total_logs,
            "sent_logs": sent_logs,
            "failed_logs": failed_logs,
            "bounced_logs": bounced_logs,
            "pending_logs": pending_logs,
        }

    async def get_template_stats(self) -> dict:
        """Get email template statistics for the templates page.

        Returns:
            Dictionary with template counts by status
        """
        total_query = select(func.count()).select_from(EmailTemplate)
        total_result = await self.session.execute(total_query)
        total_templates = total_result.scalar() or 0

        active_query = select(func.count()).where(EmailTemplate.is_active.is_(True))
        active_result = await self.session.execute(active_query)
        active_templates = active_result.scalar() or 0

        inactive_templates = total_templates - active_templates

        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "inactive_templates": inactive_templates,
        }
