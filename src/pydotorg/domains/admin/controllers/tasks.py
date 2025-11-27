"""Admin tasks controller for SAQ task monitoring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote

from litestar import Controller, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_admin
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.tasks import TaskAdminService  # noqa: TC001

if TYPE_CHECKING:
    from litestar import Request


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


class AdminTasksController(Controller):
    """Controller for admin task queue monitoring."""

    path = f"{urls.ADMIN}/tasks"
    tags = ["Admin"]
    guards = [require_admin]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def dashboard(
        self,
        task_admin_service: TaskAdminService,
        status: Annotated[str | None, Parameter(description="Filter by job status")] = None,
    ) -> Template:
        """Render task queue dashboard.

        Args:
            task_admin_service: Task admin service
            status: Optional job status filter

        Returns:
            Task dashboard template
        """
        stats = await task_admin_service.get_stats()
        queue_info = await task_admin_service.get_queue_info()
        available_tasks = await task_admin_service.get_available_tasks()
        jobs = await task_admin_service.get_all_jobs(status=status, limit=50)

        return Template(
            template_name="admin/tasks/dashboard.html.jinja2",
            context={
                "title": "Task Queue Dashboard",
                "description": "Monitor and manage background tasks",
                "stats": stats,
                "queue_info": queue_info,
                "available_tasks": available_tasks,
                "jobs": jobs,
                "current_status": status,
            },
        )

    @get("/jobs")
    async def list_jobs(
        self,
        task_admin_service: TaskAdminService,
        status: Annotated[str | None, Parameter(description="Filter by status")] = None,
        limit: Annotated[int, Parameter(ge=1, le=200, description="Page size")] = 50,
    ) -> Template:
        """Render job list with optional filtering.

        Args:
            task_admin_service: Task admin service
            status: Filter by job status
            limit: Maximum jobs to return

        Returns:
            Job list template or partial
        """
        jobs = await task_admin_service.get_all_jobs(status=status, limit=limit)

        return Template(
            template_name="admin/tasks/partials/job_list.html.jinja2",
            context={
                "jobs": jobs,
                "status_filter": status,
            },
        )

    @get("/jobs/{job_key:str}")
    async def get_job_detail(
        self,
        task_admin_service: TaskAdminService,
        job_key: str,
    ) -> Template | Response:
        """Render job detail page.

        Args:
            task_admin_service: Task admin service
            job_key: Job key/ID

        Returns:
            Job detail template or redirect if not found
        """
        job = await task_admin_service.get_job_info(job_key)
        if not job:
            return Redirect(f"{urls.ADMIN}/tasks")

        return Template(
            template_name="admin/tasks/job_detail.html.jinja2",
            context={
                "title": f"Job {job['function']} - Task Details",
                "description": f"View details for job {job_key}",
                "job": job,
            },
        )

    @get("/jobs/{job_key:str}/detail")
    async def get_job_preview(
        self,
        task_admin_service: TaskAdminService,
        job_key: str,
    ) -> Template | Response:
        """Render job detail modal partial.

        Args:
            task_admin_service: Task admin service
            job_key: Job key/ID

        Returns:
            Job detail partial or error response
        """
        job = await task_admin_service.get_job_info(job_key)
        if not job:
            return Response(content="Job not found", status_code=404)

        return Template(
            template_name="admin/tasks/partials/job_detail.html.jinja2",
            context={"job": job},
        )

    @post("/jobs/{job_key:str}/retry")
    async def retry_job(
        self,
        task_admin_service: TaskAdminService,
        job_key: str,
    ) -> Response:
        """Retry a failed job.

        Args:
            task_admin_service: Task admin service
            job_key: Job key/ID

        Returns:
            Success or error response with HX-Trigger
        """
        success = await task_admin_service.retry_job(job_key)

        if not success:
            return Response(content="Failed to retry job", status_code=400)

        return Response(
            content="Job queued for retry",
            status_code=200,
            headers={"HX-Trigger": "jobRetried"},
        )

    @post("/jobs/{job_key:str}/abort")
    async def abort_job(
        self,
        task_admin_service: TaskAdminService,
        job_key: str,
    ) -> Response:
        """Abort an active job.

        Args:
            task_admin_service: Task admin service
            job_key: Job key/ID

        Returns:
            Success or error response with HX-Trigger
        """
        success = await task_admin_service.abort_job(job_key)

        if not success:
            return Response(content="Failed to abort job", status_code=400)

        return Response(
            content="Job aborted",
            status_code=200,
            headers={"HX-Trigger": "jobAborted"},
        )

    @post("/enqueue/refresh-feeds")
    async def enqueue_refresh_feeds(
        self,
        task_admin_service: TaskAdminService,
    ) -> Response:
        """Manually trigger feed refresh task.

        Args:
            task_admin_service: Task admin service

        Returns:
            Success or error response with HX-Trigger
        """
        job_key = await task_admin_service.enqueue_task("refresh_all_feeds")

        if not job_key:
            return Response(content="Failed to enqueue task", status_code=400)

        return Response(
            content=f"Feed refresh task enqueued (Job: {job_key})",
            status_code=200,
            headers={"HX-Trigger": "taskEnqueued"},
        )

    @post("/enqueue/rebuild-indexes")
    async def enqueue_rebuild_indexes(
        self,
        task_admin_service: TaskAdminService,
    ) -> Response:
        """Manually trigger search index rebuild task.

        Args:
            task_admin_service: Task admin service

        Returns:
            Success or error response with HX-Trigger
        """
        job_key = await task_admin_service.enqueue_task("rebuild_search_index")

        if not job_key:
            return Response(content="Failed to enqueue task", status_code=400)

        return Response(
            content=f"Search index rebuild task enqueued (Job: {job_key})",
            status_code=200,
            headers={"HX-Trigger": "taskEnqueued"},
        )

    @get("/stats")
    async def get_stats(
        self,
        task_admin_service: TaskAdminService,
    ) -> Template:
        """Get queue statistics partial for live updates.

        Args:
            task_admin_service: Task admin service

        Returns:
            Stats partial template
        """
        stats = await task_admin_service.get_stats()
        queue_info = await task_admin_service.get_queue_info()

        return Template(
            template_name="admin/tasks/partials/stats.html.jinja2",
            context={
                "stats": stats,
                "queue_info": queue_info,
            },
        )
