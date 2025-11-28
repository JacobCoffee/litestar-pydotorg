"""Jobs domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

from pydotorg.domains.jobs.models import JobStatus
from pydotorg.domains.jobs.schemas import (
    JobCategoryCreate,
    JobCategoryRead,
    JobCategoryUpdate,
    JobCreate,
    JobPublic,
    JobRead,
    JobReviewCommentCreate,
    JobReviewCommentRead,
    JobSearchFilters,
    JobTypeCreate,
    JobTypeRead,
    JobTypeUpdate,
    JobUpdate,
)
from pydotorg.domains.jobs.services import (
    JobCategoryService,
    JobReviewCommentService,
    JobService,
    JobTypeService,
)


class JobTypeController(Controller):
    """Controller for JobType CRUD operations."""

    path = "/api/v1/job-types"
    tags = ["Jobs"]

    @get("/")
    async def list_job_types(
        self,
        job_type_service: JobTypeService,
        limit_offset: LimitOffset,
    ) -> list[JobTypeRead]:
        """List all job types with pagination."""
        job_types, _total = await job_type_service.list_and_count(limit_offset)
        return [JobTypeRead.model_validate(jt) for jt in job_types]

    @get("/{job_type_id:uuid}")
    async def get_job_type(
        self,
        job_type_service: JobTypeService,
        job_type_id: Annotated[UUID, Parameter(title="Job Type ID", description="The job type ID")],
    ) -> JobTypeRead:
        """Get a job type by ID."""
        job_type = await job_type_service.get(job_type_id)
        return JobTypeRead.model_validate(job_type)

    @post("/")
    async def create_job_type(
        self,
        job_type_service: JobTypeService,
        data: JobTypeCreate,
    ) -> JobTypeRead:
        """Create a new job type."""
        job_type = await job_type_service.create_job_type(data.name, data.slug)
        return JobTypeRead.model_validate(job_type)

    @put("/{job_type_id:uuid}")
    async def update_job_type(
        self,
        job_type_service: JobTypeService,
        data: JobTypeUpdate,
        job_type_id: Annotated[UUID, Parameter(title="Job Type ID", description="The job type ID")],
    ) -> JobTypeRead:
        """Update a job type."""
        update_data = data.model_dump(exclude_unset=True)
        job_type = await job_type_service.update(job_type_id, update_data)
        return JobTypeRead.model_validate(job_type)

    @delete("/{job_type_id:uuid}")
    async def delete_job_type(
        self,
        job_type_service: JobTypeService,
        job_type_id: Annotated[UUID, Parameter(title="Job Type ID", description="The job type ID")],
    ) -> None:
        """Delete a job type."""
        await job_type_service.delete(job_type_id)


class JobCategoryController(Controller):
    """Controller for JobCategory CRUD operations."""

    path = "/api/v1/job-categories"
    tags = ["Jobs"]

    @get("/")
    async def list_job_categories(
        self,
        job_category_service: JobCategoryService,
        limit_offset: LimitOffset,
    ) -> list[JobCategoryRead]:
        """List all job categories with pagination."""
        job_categories, _total = await job_category_service.list_and_count(limit_offset)
        return [JobCategoryRead.model_validate(jc) for jc in job_categories]

    @get("/{job_category_id:uuid}")
    async def get_job_category(
        self,
        job_category_service: JobCategoryService,
        job_category_id: Annotated[UUID, Parameter(title="Job Category ID", description="The job category ID")],
    ) -> JobCategoryRead:
        """Get a job category by ID."""
        job_category = await job_category_service.get(job_category_id)
        return JobCategoryRead.model_validate(job_category)

    @post("/")
    async def create_job_category(
        self,
        job_category_service: JobCategoryService,
        data: JobCategoryCreate,
    ) -> JobCategoryRead:
        """Create a new job category."""
        job_category = await job_category_service.create_job_category(data.name, data.slug)
        return JobCategoryRead.model_validate(job_category)

    @put("/{job_category_id:uuid}")
    async def update_job_category(
        self,
        job_category_service: JobCategoryService,
        data: JobCategoryUpdate,
        job_category_id: Annotated[UUID, Parameter(title="Job Category ID", description="The job category ID")],
    ) -> JobCategoryRead:
        """Update a job category."""
        update_data = data.model_dump(exclude_unset=True)
        job_category = await job_category_service.update(job_category_id, update_data)
        return JobCategoryRead.model_validate(job_category)

    @delete("/{job_category_id:uuid}")
    async def delete_job_category(
        self,
        job_category_service: JobCategoryService,
        job_category_id: Annotated[UUID, Parameter(title="Job Category ID", description="The job category ID")],
    ) -> None:
        """Delete a job category."""
        await job_category_service.delete(job_category_id)


class JobController(Controller):
    """Controller for Job CRUD operations."""

    path = "/api/v1/jobs"
    tags = ["Jobs"]

    @post("/search")
    async def search_jobs(
        self,
        job_service: JobService,
        filters: JobSearchFilters,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[JobPublic]:
        """Search jobs with filters."""
        jobs = await job_service.search_jobs(filters, limit=limit, offset=offset)
        return [JobPublic.model_validate(job) for job in jobs]

    @get("/")
    async def list_jobs(
        self,
        job_service: JobService,
        limit_offset: LimitOffset,
        status: Annotated[JobStatus | None, Parameter(description="Filter by job status")] = None,
    ) -> list[JobRead]:
        """List all jobs with pagination."""
        if status:
            jobs = await job_service.list_by_status(status, limit=limit_offset.limit, offset=limit_offset.offset)
            return [JobRead.model_validate(job) for job in jobs]

        jobs, _total = await job_service.list_and_count(limit_offset)
        return [JobRead.model_validate(job) for job in jobs]

    @get("/mine")
    async def list_my_jobs(
        self,
        job_service: JobService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[JobRead]:
        """List jobs created by the current user."""
        msg = "Authentication not implemented"
        raise NotImplementedError(msg)

    @get("/{job_id:uuid}")
    async def get_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Get a job by ID."""
        job = await job_service.get(job_id)
        return JobRead.model_validate(job)

    @post("/")
    async def create_job(
        self,
        job_service: JobService,
        data: JobCreate,
    ) -> JobRead:
        """Create a new job posting."""
        msg = "Authentication not implemented"
        raise NotImplementedError(msg)

    @put("/{job_id:uuid}")
    async def update_job(
        self,
        job_service: JobService,
        data: JobUpdate,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Update a job."""
        update_data = data.model_dump(exclude_unset=True, exclude={"job_type_ids"})

        if data.job_type_ids is not None:
            job = await job_service.update_job_types(job_id, data.job_type_ids)
            if update_data:
                job = await job_service.update(job_id, update_data)
        else:
            job = await job_service.update(job_id, update_data)

        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/submit")
    async def submit_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Submit a job for review."""
        job = await job_service.submit_for_review(job_id)
        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/approve")
    async def approve_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Approve a job posting (staff only)."""
        job = await job_service.approve_job(job_id)
        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/reject")
    async def reject_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Reject a job posting (staff only)."""
        job = await job_service.reject_job(job_id)
        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/archive")
    async def archive_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Archive a job posting."""
        job = await job_service.archive_job(job_id)
        return JobRead.model_validate(job)

    @delete("/{job_id:uuid}")
    async def delete_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> None:
        """Delete a job."""
        await job_service.delete(job_id)


class JobRenderController(Controller):
    """Controller for rendering jobs as HTML."""

    path = "/jobs"
    include_in_schema = False

    @get("/")
    async def list_jobs_html(
        self,
        job_service: JobService,
        job_type_service: JobTypeService,
        job_category_service: JobCategoryService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 50,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> Template:
        """Render jobs listing page."""
        jobs = await job_service.list_by_status(JobStatus.APPROVED, limit=limit, offset=offset)
        job_types, _ = await job_type_service.list_and_count()
        job_categories, _ = await job_category_service.list_and_count()

        return Template(
            template_name="jobs/index.html.jinja2",
            context={
                "jobs": jobs,
                "job_types": job_types,
                "job_categories": job_categories,
                "title": "Job Board",
                "description": "Browse available Python jobs",
            },
        )

    @get("/{slug:str}")
    async def get_job_html(
        self,
        job_service: JobService,
        slug: Annotated[str, Parameter(title="Job Slug", description="The job URL slug")],
    ) -> Template:
        """Render job detail page."""
        job = await job_service.get_by_slug(slug)

        if not job or job.status != JobStatus.APPROVED:
            msg = "Job not found"
            raise NotFoundException(msg)

        related_jobs = await job_service.list_by_status(JobStatus.APPROVED, limit=5, offset=0)

        return Template(
            template_name="jobs/detail.html.jinja2",
            context={
                "job": job,
                "related_jobs": [j for j in related_jobs if j.id != job.id][:5],
                "title": f"{job.job_title} at {job.company_name}",
                "description": job.description[:200] if job.description else "",
            },
        )

    @get("/submit")
    async def submit_job_form(
        self,
        job_type_service: JobTypeService,
        job_category_service: JobCategoryService,
    ) -> Template:
        """Render job submission form."""
        job_types, _ = await job_type_service.list_and_count()
        job_categories, _ = await job_category_service.list_and_count()

        return Template(
            template_name="jobs/submit.html.jinja2",
            context={
                "job_types": job_types,
                "job_categories": job_categories,
                "title": "Submit a Job",
                "description": "Post a Python job opportunity",
            },
        )

    @get("/mine")
    async def my_jobs_html(self) -> Template:
        """Render user's jobs page (requires authentication)."""
        msg = "Authentication not implemented"
        raise NotImplementedError(msg)


class JobReviewCommentController(Controller):
    """Controller for JobReviewComment CRUD operations."""

    path = "/api/v1"
    tags = ["Jobs"]

    @get("/jobs/{job_id:uuid}/review-comments")
    async def list_job_review_comments(
        self,
        job_review_comment_service: JobReviewCommentService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[JobReviewCommentRead]:
        """List review comments for a job."""
        comments = await job_review_comment_service.get_by_job(job_id, limit=limit, offset=offset)
        return [JobReviewCommentRead.model_validate(comment) for comment in comments]

    @get("/review-comments/{comment_id:uuid}")
    async def get_review_comment(
        self,
        job_review_comment_service: JobReviewCommentService,
        comment_id: Annotated[UUID, Parameter(title="Comment ID", description="The review comment ID")],
    ) -> JobReviewCommentRead:
        """Get a review comment by ID."""
        comment = await job_review_comment_service.get(comment_id)
        return JobReviewCommentRead.model_validate(comment)

    @post("/jobs/{job_id:uuid}/review-comments")
    async def create_review_comment(
        self,
        job_review_comment_service: JobReviewCommentService,
        data: JobReviewCommentCreate,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobReviewCommentRead:
        """Create a review comment for a job (staff only)."""
        msg = "Authentication not implemented"
        raise NotImplementedError(msg)

    @delete("/review-comments/{comment_id:uuid}")
    async def delete_review_comment(
        self,
        job_review_comment_service: JobReviewCommentService,
        comment_id: Annotated[UUID, Parameter(title="Comment ID", description="The review comment ID")],
    ) -> None:
        """Delete a review comment."""
        await job_review_comment_service.delete(comment_id)
