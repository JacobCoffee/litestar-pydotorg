"""Admin jobs controller for job moderation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID  # noqa: TC003

from litestar import Controller, delete, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.jobs import JobAdminService  # noqa: TC001

if TYPE_CHECKING:
    from litestar import Request

    from pydotorg.domains.users.models import User


def _admin_auth_exception_handler(request: Request, exc: NotAuthorizedException) -> Response:
    """Redirect to login page when user is not authenticated."""
    next_url = quote(str(request.url), safe="")
    return Redirect(f"/auth/login?next={next_url}")


def _admin_permission_exception_handler(request: Request, exc: PermissionDeniedException) -> Response:
    """Show 403 template when user lacks permissions."""
    return Template(
        template_name="errors/403.html.jinja2",
        context={
            "title": "Access Denied",
            "message": str(exc.detail) if exc.detail else "You do not have permission to access this page.",
        },
        status_code=403,
    )


class AdminJobsController(Controller):
    """Controller for admin job moderation."""

    path = urls.ADMIN_JOBS
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_jobs(
        self,
        request: Request,
        job_admin_service: JobAdminService,
        status: Annotated[str | None, Parameter(description="Filter by status")] = None,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render job moderation list page.

        Args:
            request: HTTP request
            job_admin_service: Job admin service
            status: Filter by job status
            q: Search query
            limit: Maximum jobs per page
            offset: Pagination offset

        Returns:
            Job list template
        """
        status_filter = None
        if status == "pending":
            status_filter = "review"
        elif status in ("approved", "rejected"):
            status_filter = status

        jobs, total = await job_admin_service.list_jobs(
            limit=limit,
            offset=offset,
            status=status_filter,
            search=q,
        )
        stats = await job_admin_service.get_stats()

        context = {
            "title": "Job Moderation",
            "description": "Review and approve job postings",
            "jobs": jobs,
            "stats": stats,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"
        if is_htmx and not is_boosted:
            return Template(
                template_name="admin/jobs/partials/jobs_list.html.jinja2",
                context=context,
            )

        return Template(
            template_name="admin/jobs/list.html.jinja2",
            context=context,
        )

    @get("/{job_id:uuid}")
    async def get_job_detail(
        self,
        job_admin_service: JobAdminService,
        job_id: UUID,
    ) -> Template | Response:
        """Render job detail page for moderation.

        Args:
            job_admin_service: Job admin service
            job_id: Job ID

        Returns:
            Job detail template or redirect if not found
        """
        job = await job_admin_service.get_job(job_id)
        if not job:
            return Redirect("/admin/jobs")

        return Template(
            template_name="admin/jobs/detail.html.jinja2",
            context={
                "title": f"{job.job_title} - Job Review",
                "description": f"Review job: {job.job_title}",
                "job": job,
            },
        )

    @get("/{job_id:uuid}/preview")
    async def get_job_preview(
        self,
        job_admin_service: JobAdminService,
        job_id: UUID,
    ) -> Template | Response:
        """Render job preview partial for modal.

        Args:
            job_admin_service: Job admin service
            job_id: Job ID

        Returns:
            Job preview partial or error response
        """
        job = await job_admin_service.get_job(job_id)
        if not job:
            return Response(content="Job not found", status_code=404)

        return Template(
            template_name="admin/jobs/partials/job_preview.html.jinja2",
            context={"job": job},
        )

    @post("/{job_id:uuid}/approve")
    async def approve_job(
        self,
        request: Request,
        job_admin_service: JobAdminService,
        job_id: UUID,
    ) -> Template | Response:
        """Approve a job.

        Args:
            request: HTTP request
            job_admin_service: Job admin service
            job_id: Job ID

        Returns:
            Updated job row partial or error response
        """
        job = await job_admin_service.approve_job(job_id)
        if not job:
            return Response(content="Job not found", status_code=404)

        return Template(
            template_name="admin/jobs/partials/job_row.html.jinja2",
            context={"job": job},
        )

    @post("/{job_id:uuid}/reject")
    async def reject_job(
        self,
        request: Request,
        job_admin_service: JobAdminService,
        job_id: UUID,
    ) -> Template | Response:
        """Reject a job.

        Args:
            request: HTTP request
            job_admin_service: Job admin service
            job_id: Job ID

        Returns:
            Updated job row partial or error response
        """
        form_data = await request.form()
        reason = form_data.get("reason", "Your job posting did not meet our guidelines.")

        job = await job_admin_service.reject_job(job_id, reason=str(reason))
        if not job:
            return Response(content="Job not found", status_code=404)

        return Template(
            template_name="admin/jobs/partials/job_row.html.jinja2",
            context={"job": job},
        )

    @post("/{job_id:uuid}/comment")
    async def add_comment(
        self,
        request: Request,
        job_admin_service: JobAdminService,
        job_id: UUID,
    ) -> Response:
        """Add a review comment to a job.

        Args:
            request: HTTP request
            job_admin_service: Job admin service
            job_id: Job ID

        Returns:
            Success or error response
        """
        user: User = request.user
        form_data = await request.form()
        comment_text = form_data.get("comment", "")

        if not comment_text:
            return Response(content="Comment is required", status_code=400)

        comment = await job_admin_service.add_review_comment(
            job_id=job_id,
            comment=str(comment_text),
            reviewer_id=user.id,
        )

        if not comment:
            return Response(content="Job not found", status_code=404)

        return Response(
            content="Comment added",
            status_code=200,
            headers={"HX-Trigger": "commentAdded"},
        )

    @delete("/{job_id:uuid}", status_code=200)
    async def delete_job(
        self,
        job_admin_service: JobAdminService,
        job_id: UUID,
    ) -> Response:
        """Delete a job.

        Args:
            job_admin_service: Job admin service
            job_id: Job ID

        Returns:
            Empty response on success, 404 if not found
        """
        deleted = await job_admin_service.delete_job(job_id)
        if not deleted:
            return Response(content="Job not found", status_code=404)

        return Response(content="Deleted", status_code=200)
