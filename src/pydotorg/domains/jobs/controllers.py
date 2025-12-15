"""Jobs domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, Request, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.openapi import ResponseSpec
from litestar.params import Body, Parameter
from litestar.response import Template
from litestar.status_codes import HTTP_200_OK

from pydotorg.core.auth.guards import require_authenticated, require_staff
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
        """List all job types with pagination.

        Retrieves a paginated list of job types used to categorize job postings
        by employment type (e.g., Full-time, Part-time, Contract, Remote).

        Args:
            job_type_service: Service for job type database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of job types with their names and slugs.
        """
        job_types, _total = await job_type_service.list_and_count(limit_offset)
        return [JobTypeRead.model_validate(jt) for jt in job_types]

    @get(
        "/{job_type_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Job type not found"),
        },
    )
    async def get_job_type(
        self,
        job_type_service: JobTypeService,
        job_type_id: Annotated[UUID, Parameter(title="Job Type ID", description="The job type ID")],
    ) -> JobTypeRead:
        """Retrieve a specific job type by its unique identifier.

        Fetches complete job type information including name and URL slug.
        Job types are used to filter and categorize job postings.

        Args:
            job_type_service: Service for job type database operations.
            job_type_id: The unique UUID identifier of the job type.

        Returns:
            Complete job type details.

        Raises:
            NotFoundException: If no job type with the given ID exists.
        """
        job_type = await job_type_service.get(job_type_id)
        return JobTypeRead.model_validate(job_type)

    @post("/")
    async def create_job_type(
        self,
        job_type_service: JobTypeService,
        data: Annotated[JobTypeCreate, Body(title="Job Type", description="Job type to create")],
    ) -> JobTypeRead:
        """Create a new job type classification.

        Adds a new job type to the system for categorizing job postings.
        Both name and slug must be unique across all job types.

        Args:
            job_type_service: Service for job type database operations.
            data: Job type creation payload with name and slug.

        Returns:
            The newly created job type.

        Raises:
            ConflictError: If a job type with the same name or slug exists.
        """
        job_type = await job_type_service.create_job_type(data.name, data.slug)
        return JobTypeRead.model_validate(job_type)

    @put("/{job_type_id:uuid}")
    async def update_job_type(
        self,
        job_type_service: JobTypeService,
        data: Annotated[JobTypeUpdate, Body(title="Job Type", description="Job type data to update")],
        job_type_id: Annotated[UUID, Parameter(title="Job Type ID", description="The job type ID")],
    ) -> JobTypeRead:
        """Update an existing job type.

        Modifies job type fields with the provided values. Changes affect
        how existing jobs are categorized and displayed.

        Args:
            job_type_service: Service for job type database operations.
            data: Partial job type update payload with fields to modify.
            job_type_id: The unique UUID identifier of the job type to update.

        Returns:
            The updated job type with all current fields.

        Raises:
            NotFoundException: If no job type with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        job_type = await job_type_service.update(update_data, item_id=job_type_id)
        return JobTypeRead.model_validate(job_type)

    @delete("/{job_type_id:uuid}")
    async def delete_job_type(
        self,
        job_type_service: JobTypeService,
        job_type_id: Annotated[UUID, Parameter(title="Job Type ID", description="The job type ID")],
    ) -> None:
        """Delete a job type classification.

        Permanently removes a job type from the system. Jobs using this type
        should be reassigned before deletion.

        Args:
            job_type_service: Service for job type database operations.
            job_type_id: The unique UUID identifier of the job type to delete.

        Raises:
            NotFoundException: If no job type with the given ID exists.
        """
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
        """List all job categories with pagination.

        Retrieves a paginated list of job categories used to classify job
        postings by field or specialty (e.g., Web Development, Data Science).

        Args:
            job_category_service: Service for job category database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of job categories with their names and slugs.
        """
        job_categories, _total = await job_category_service.list_and_count(limit_offset)
        return [JobCategoryRead.model_validate(jc) for jc in job_categories]

    @get(
        "/{job_category_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Job category not found"),
        },
    )
    async def get_job_category(
        self,
        job_category_service: JobCategoryService,
        job_category_id: Annotated[UUID, Parameter(title="Job Category ID", description="The job category ID")],
    ) -> JobCategoryRead:
        """Retrieve a specific job category by its unique identifier.

        Fetches complete job category information including name and URL slug.
        Job categories are used to filter and classify job postings by field.

        Args:
            job_category_service: Service for job category database operations.
            job_category_id: The unique UUID identifier of the job category.

        Returns:
            Complete job category details.

        Raises:
            NotFoundException: If no job category with the given ID exists.
        """
        job_category = await job_category_service.get(job_category_id)
        return JobCategoryRead.model_validate(job_category)

    @post("/")
    async def create_job_category(
        self,
        job_category_service: JobCategoryService,
        data: Annotated[JobCategoryCreate, Body(title="Job Category", description="Job category to create")],
    ) -> JobCategoryRead:
        """Create a new job category classification.

        Adds a new job category to the system for classifying job postings
        by field or specialty. Both name and slug must be unique.

        Args:
            job_category_service: Service for job category database operations.
            data: Job category creation payload with name and slug.

        Returns:
            The newly created job category.

        Raises:
            ConflictError: If a job category with the same name or slug exists.
        """
        job_category = await job_category_service.create_job_category(data.name, data.slug)
        return JobCategoryRead.model_validate(job_category)

    @put("/{job_category_id:uuid}")
    async def update_job_category(
        self,
        job_category_service: JobCategoryService,
        data: Annotated[JobCategoryUpdate, Body(title="Job Category", description="Job category data to update")],
        job_category_id: Annotated[UUID, Parameter(title="Job Category ID", description="The job category ID")],
    ) -> JobCategoryRead:
        """Update an existing job category.

        Modifies job category fields with the provided values. Changes affect
        how existing jobs are classified and displayed.

        Args:
            job_category_service: Service for job category database operations.
            data: Partial job category update payload with fields to modify.
            job_category_id: The unique UUID identifier of the job category to update.

        Returns:
            The updated job category with all current fields.

        Raises:
            NotFoundException: If no job category with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        job_category = await job_category_service.update(update_data, item_id=job_category_id)
        return JobCategoryRead.model_validate(job_category)

    @delete("/{job_category_id:uuid}")
    async def delete_job_category(
        self,
        job_category_service: JobCategoryService,
        job_category_id: Annotated[UUID, Parameter(title="Job Category ID", description="The job category ID")],
    ) -> None:
        """Delete a job category classification.

        Permanently removes a job category from the system. Jobs using this
        category should be reassigned before deletion.

        Args:
            job_category_service: Service for job category database operations.
            job_category_id: The unique UUID identifier of the job category to delete.

        Raises:
            NotFoundException: If no job category with the given ID exists.
        """
        await job_category_service.delete(job_category_id)


class JobController(Controller):
    """Controller for Job CRUD operations."""

    path = "/api/v1/jobs"
    tags = ["Jobs"]

    @post("/search", status_code=HTTP_200_OK)
    async def search_jobs(
        self,
        job_service: JobService,
        data: Annotated[JobSearchFilters, Body(title="Search Filters", description="Job search filters")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[JobPublic]:
        """Search jobs with advanced filters.

        Performs a filtered search across approved job postings using multiple
        criteria. Results can be filtered by location, job type, category,
        salary range, and keywords.

        Args:
            job_service: Service for job database operations.
            data: Search filters including keywords, location, type, and category.
            limit: Maximum number of jobs to return (1-1000).
            offset: Number of jobs to skip for pagination.

        Returns:
            List of public job postings matching the search criteria.
        """
        jobs = await job_service.search_jobs(data, limit=limit, offset=offset)
        return [JobPublic.model_validate(job) for job in jobs]

    @get("/")
    async def list_jobs(
        self,
        job_service: JobService,
        limit_offset: LimitOffset,
        status: Annotated[JobStatus | None, Parameter(description="Filter by job status")] = None,
    ) -> list[JobRead]:
        """List all jobs with pagination and optional status filter.

        Retrieves a paginated list of job postings. Can be filtered by status
        to show only draft, pending, approved, rejected, or archived jobs.

        Args:
            job_service: Service for job database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.
            status: Optional job status filter.

        Returns:
            List of job postings with full details.
        """
        if status:
            jobs = await job_service.list_by_status(status, limit=limit_offset.limit, offset=limit_offset.offset)
            return [JobRead.model_validate(job) for job in jobs]

        jobs, _total = await job_service.list_and_count(limit_offset)
        return [JobRead.model_validate(job) for job in jobs]

    @get("/mine", guards=[require_authenticated])
    async def list_my_jobs(
        self,
        request: Request,
        job_service: JobService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[JobRead]:
        """List jobs created by the authenticated user.

        Retrieves all job postings created by the currently authenticated user,
        including drafts and jobs in any status. Requires authentication.

        Args:
            request: The HTTP request containing user authentication.
            job_service: Service for job database operations.
            limit: Maximum number of jobs to return (1-1000).
            offset: Number of jobs to skip for pagination.

        Returns:
            List of the user's job postings with full details.
        """
        jobs = await job_service.get_by_creator(
            creator_id=request.user.id,
            limit=limit,
            offset=offset,
        )
        return [JobRead.model_validate(job) for job in jobs]

    @get(
        "/{job_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Job not found"),
        },
    )
    async def get_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Retrieve a specific job posting by its unique identifier.

        Fetches complete job information including title, description, company
        details, requirements, and current status.

        Args:
            job_service: Service for job database operations.
            job_id: The unique UUID identifier of the job.

        Returns:
            Complete job posting details.

        Raises:
            NotFoundException: If no job with the given ID exists.
        """
        job = await job_service.get(job_id)
        return JobRead.model_validate(job)

    @post(
        "/",
        guards=[require_authenticated],
        responses={
            401: ResponseSpec(None, description="Authentication required"),
            422: ResponseSpec(None, description="Validation error"),
        },
    )
    async def create_job(
        self,
        request: Request,
        job_service: JobService,
        data: Annotated[JobCreate, Body(title="Job", description="Job posting to create")],
    ) -> JobRead:
        """Create a new job posting.

        Creates a new job posting in draft status. The job must be submitted
        for review before it can be approved and published. Requires authentication.

        Args:
            request: The HTTP request containing user authentication.
            job_service: Service for job database operations.
            data: Job creation payload with title, description, and requirements.

        Returns:
            The newly created job posting in draft status.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        job = await job_service.create_job(data=data, creator_id=request.user.id)
        return JobRead.model_validate(job)

    @put(
        "/{job_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Job not found"),
            422: ResponseSpec(None, description="Validation error"),
        },
    )
    async def update_job(
        self,
        job_service: JobService,
        data: Annotated[JobUpdate, Body(title="Job", description="Job data to update")],
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Update an existing job posting.

        Modifies job posting fields with the provided values. Can update title,
        description, requirements, and job type associations. Status changes
        should use dedicated endpoints.

        Args:
            job_service: Service for job database operations.
            data: Partial job update payload with fields to modify.
            job_id: The unique UUID identifier of the job to update.

        Returns:
            The updated job posting with all current fields.

        Raises:
            NotFoundException: If no job with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True, exclude={"job_type_ids"})

        if data.job_type_ids is not None:
            job = await job_service.update_job_types(job_id, data.job_type_ids)
            if update_data:
                job = await job_service.update(update_data, item_id=job_id)
        else:
            job = await job_service.update(update_data, item_id=job_id)

        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/submit")
    async def submit_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Submit a job posting for review.

        Transitions a draft job to pending status, queuing it for staff review.
        Once approved, the job will be published and visible to job seekers.

        Args:
            job_service: Service for job database operations.
            job_id: The unique UUID identifier of the job to submit.

        Returns:
            The job posting with updated pending status.

        Raises:
            NotFoundException: If no job with the given ID exists.
            ValidationError: If the job is not in draft status.
        """
        job = await job_service.submit_for_review(job_id)
        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/approve")
    async def approve_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Approve a pending job posting for publication.

        Transitions a pending job to approved status, making it visible to
        job seekers on the public job board. Staff only operation.

        Args:
            job_service: Service for job database operations.
            job_id: The unique UUID identifier of the job to approve.

        Returns:
            The job posting with approved status.

        Raises:
            NotFoundException: If no job with the given ID exists.
            ValidationError: If the job is not in pending status.
        """
        job = await job_service.approve_job(job_id)
        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/reject")
    async def reject_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Reject a pending job posting.

        Transitions a pending job to rejected status with feedback for the
        submitter. The job can be edited and resubmitted. Staff only operation.

        Args:
            job_service: Service for job database operations.
            job_id: The unique UUID identifier of the job to reject.

        Returns:
            The job posting with rejected status.

        Raises:
            NotFoundException: If no job with the given ID exists.
            ValidationError: If the job is not in pending status.
        """
        job = await job_service.reject_job(job_id)
        return JobRead.model_validate(job)

    @patch("/{job_id:uuid}/archive")
    async def archive_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobRead:
        """Archive a job posting.

        Transitions a job to archived status, removing it from the public
        job board while preserving it for historical reference.

        Args:
            job_service: Service for job database operations.
            job_id: The unique UUID identifier of the job to archive.

        Returns:
            The job posting with archived status.

        Raises:
            NotFoundException: If no job with the given ID exists.
        """
        job = await job_service.archive_job(job_id)
        return JobRead.model_validate(job)

    @delete(
        "/{job_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Job not found"),
        },
    )
    async def delete_job(
        self,
        job_service: JobService,
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> None:
        """Permanently delete a job posting.

        Removes a job posting and all associated data from the system.
        This action is irreversible. Consider archiving instead.

        Args:
            job_service: Service for job database operations.
            job_id: The unique UUID identifier of the job to delete.

        Raises:
            NotFoundException: If no job with the given ID exists.
        """
        await job_service.delete(job_id)


class JobRenderController(Controller):
    """Controller for rendering jobs as HTML."""

    path = "/jobs"
    include_in_schema = False

    @get("/")
    async def list_jobs_html(
        self,
        request: Request,
        job_service: JobService,
        job_type_service: JobTypeService,
        job_category_service: JobCategoryService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 50,
        offset: Annotated[int, Parameter(ge=0)] = 0,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        remote: Annotated[str | None, Parameter(description="Remote only filter")] = None,
        location: Annotated[str | None, Parameter(description="Location filter")] = None,
        job_type: Annotated[list[str] | None, Parameter(description="Job type slugs")] = None,
        category: Annotated[list[str] | None, Parameter(description="Category slugs")] = None,
    ) -> Template:
        """Render jobs listing page."""
        job_types_all, _ = await job_type_service.list_and_count()
        job_categories_all, _ = await job_category_service.list_and_count()

        telecommuting_filter = remote == "true" if remote else None
        job_type_ids = None
        category_id = None

        if job_type:
            job_type_ids = [jt.id for jt in job_types_all if jt.slug in job_type]

        if category:
            for cat in job_categories_all:
                if cat.slug in category:
                    category_id = cat.id
                    break

        jobs = await job_service.search_jobs(
            filters=JobSearchFilters(
                telecommuting=telecommuting_filter,
                city=location if location else None,
                category_id=category_id,
                job_type_ids=job_type_ids if job_type_ids else None,
            ),
            limit=limit,
            offset=offset,
        )

        if q:
            q_lower = q.lower()
            jobs = [
                job
                for job in jobs
                if q_lower in job.job_title.lower()
                or q_lower in job.company_name.lower()
                or (job.description and q_lower in job.description.lower())
            ]

        featured_jobs = await job_service.get_featured(limit=5)

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"

        context = {
            "jobs": jobs,
            "featured_jobs": featured_jobs,
            "job_types": job_types_all,
            "job_categories": job_categories_all,
            "title": "Job Board",
            "description": "Browse available Python jobs",
        }

        if is_htmx and not is_boosted:
            return Template(
                template_name="jobs/partials/job_results.html.jinja2",
                context=context,
            )

        return Template(
            template_name="jobs/index.html.jinja2",
            context=context,
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

    @get("/mine", guards=[require_authenticated])
    async def my_jobs_html(
        self,
        request: Request,
        job_service: JobService,
    ) -> Template:
        """Render user's jobs page (requires authentication)."""
        jobs = await job_service.get_by_creator(creator_id=request.user.id, limit=100, offset=0)

        return Template(
            template_name="jobs/my_jobs.html.jinja2",
            context={
                "jobs": jobs,
                "title": "My Jobs",
                "description": "Manage your job postings",
            },
        )

    @post("/preview")
    async def preview_job(
        self,
        request: Request,
    ) -> Template:
        """Render job preview from form data."""
        form_data = await request.form()

        job_preview = {
            "job_title": form_data.get("job_title", ""),
            "company_name": form_data.get("company_name", ""),
            "company_url": form_data.get("company_url", ""),
            "description": form_data.get("description", ""),
            "requirements": form_data.get("requirements", ""),
            "city": form_data.get("city", ""),
            "region": form_data.get("region", ""),
            "country": form_data.get("country", ""),
            "telecommuting": form_data.get("telecommuting") == "on",
            "contact": form_data.get("contact", ""),
            "contact_name": form_data.get("contact_name", ""),
            "contact_email": form_data.get("contact_email", ""),
        }

        return Template(
            template_name="jobs/partials/preview.html.jinja2",
            context={"job": job_preview},
        )


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
        """List review comments for a specific job posting.

        Retrieves all staff review comments associated with a job posting.
        Comments provide feedback during the review process.

        Args:
            job_review_comment_service: Service for review comment operations.
            job_id: The unique UUID identifier of the job.
            limit: Maximum number of comments to return (1-1000).
            offset: Number of comments to skip for pagination.

        Returns:
            List of review comments with author and timestamp.
        """
        comments = await job_review_comment_service.get_by_job(job_id, limit=limit, offset=offset)
        return [JobReviewCommentRead.model_validate(comment) for comment in comments]

    @get(
        "/review-comments/{comment_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Review comment not found"),
        },
    )
    async def get_review_comment(
        self,
        job_review_comment_service: JobReviewCommentService,
        comment_id: Annotated[UUID, Parameter(title="Comment ID", description="The review comment ID")],
    ) -> JobReviewCommentRead:
        """Retrieve a specific review comment by its unique identifier.

        Fetches complete review comment information including the comment text,
        author, and creation timestamp.

        Args:
            job_review_comment_service: Service for review comment operations.
            comment_id: The unique UUID identifier of the review comment.

        Returns:
            Complete review comment details.

        Raises:
            NotFoundException: If no review comment with the given ID exists.
        """
        comment = await job_review_comment_service.get(comment_id)
        return JobReviewCommentRead.model_validate(comment)

    @post(
        "/jobs/{job_id:uuid}/review-comments",
        guards=[require_staff],
        responses={
            401: ResponseSpec(None, description="Authentication required"),
            403: ResponseSpec(None, description="Staff access required"),
            404: ResponseSpec(None, description="Job not found"),
        },
    )
    async def create_review_comment(
        self,
        request: Request,
        job_review_comment_service: JobReviewCommentService,
        data: Annotated[JobReviewCommentCreate, Body(title="Review Comment", description="Review comment to create")],
        job_id: Annotated[UUID, Parameter(title="Job ID", description="The job ID")],
    ) -> JobReviewCommentRead:
        """Create a review comment for a job posting.

        Adds a staff review comment to a job posting. Comments are used to
        provide feedback during the review process. Staff only operation.

        Args:
            request: The HTTP request containing user authentication.
            job_review_comment_service: Service for review comment operations.
            data: Review comment creation payload with comment text.
            job_id: The unique UUID identifier of the job to comment on.

        Returns:
            The newly created review comment.

        Raises:
            NotFoundException: If no job with the given ID exists.
            ForbiddenException: If the user is not a staff member.
        """
        comment = await job_review_comment_service.create_comment(
            job_id=job_id,
            comment=data.comment,
            creator_id=request.user.id,
        )
        return JobReviewCommentRead.model_validate(comment)

    @delete("/review-comments/{comment_id:uuid}")
    async def delete_review_comment(
        self,
        job_review_comment_service: JobReviewCommentService,
        comment_id: Annotated[UUID, Parameter(title="Comment ID", description="The review comment ID")],
    ) -> None:
        """Delete a review comment.

        Permanently removes a review comment from the system. This action
        is irreversible.

        Args:
            job_review_comment_service: Service for review comment operations.
            comment_id: The unique UUID identifier of the comment to delete.

        Raises:
            NotFoundException: If no review comment with the given ID exists.
        """
        await job_review_comment_service.delete(comment_id)
