# Jobs Domain

Job board functionality for posting and managing Python job listings.

## Overview

The Jobs domain provides a complete job board system with:
- Job posting submission and management
- Review workflow (draft -> review -> approved/rejected)
- Job categorization by type and category
- Location-based search (city, region, country)
- Telecommuting filter
- Job expiration handling
- Review comments for moderation

## Models

### JobType
Categorizes jobs by type (e.g., Full-time, Part-time, Contract).
- `name`: Type name
- `slug`: URL-friendly identifier
- Many-to-many relationship with Jobs

### JobCategory
High-level job categorization (e.g., Backend, Frontend, Data Science).
- `name`: Category name
- `slug`: URL-friendly identifier
- One-to-many relationship with Jobs

### Job
Main job posting entity.
- `slug`: URL-friendly identifier
- `creator_id`: User who created the posting
- `company_name`: Hiring company
- `job_title`: Position title
- `city`, `region`, `country`: Location fields
- `description`: Full job description (Text)
- `requirements`: Job requirements (Text)
- `contact`: Contact information
- `url`: Application URL
- `email`: Contact email
- `status`: Current workflow status (JobStatus enum)
- `telecommuting`: Remote work flag
- `agencies`: Whether agencies can apply
- `expires`: Optional expiration date
- `category_id`: FK to JobCategory
- Relationships: creator (User), job_types (JobType), category (JobCategory), review_comments

### JobReviewComment
Comments from staff during job review process.
- `job_id`: FK to Job
- `comment`: Review comment text
- `creator_id`: Staff member who wrote comment
- Relationships: job, creator (User)

### JobStatus Enum
- `DRAFT`: Initial state, not visible publicly
- `REVIEW`: Submitted for moderation
- `APPROVED`: Published and visible
- `REJECTED`: Not approved for publication
- `ARCHIVED`: Removed from active listings
- `EXPIRED`: Past expiration date

## Workflow

1. User creates job posting (status: DRAFT)
2. User submits for review (status: REVIEW)
3. Staff reviews and either:
   - Approves (status: APPROVED) - visible on job board
   - Rejects (status: REJECTED) - not visible
   - Adds review comments for clarification
4. Jobs can be archived or expire automatically

## API Endpoints

### Job Types
- `GET /api/v1/job-types` - List all job types
- `GET /api/v1/job-types/{id}` - Get job type by ID
- `POST /api/v1/job-types` - Create job type
- `PUT /api/v1/job-types/{id}` - Update job type
- `DELETE /api/v1/job-types/{id}` - Delete job type

### Job Categories
- `GET /api/v1/job-categories` - List all categories
- `GET /api/v1/job-categories/{id}` - Get category by ID
- `POST /api/v1/job-categories` - Create category
- `PUT /api/v1/job-categories/{id}` - Update category
- `DELETE /api/v1/job-categories/{id}` - Delete category

### Jobs
- `POST /api/v1/jobs/search` - Search jobs with filters
- `GET /api/v1/jobs` - List all jobs (with status filter)
- `GET /api/v1/jobs/mine` - List current user's jobs
- `GET /api/v1/jobs/{id}` - Get job by ID
- `POST /api/v1/jobs` - Create job posting
- `PUT /api/v1/jobs/{id}` - Update job
- `PATCH /api/v1/jobs/{id}/submit` - Submit for review
- `PATCH /api/v1/jobs/{id}/approve` - Approve job (staff)
- `PATCH /api/v1/jobs/{id}/reject` - Reject job (staff)
- `PATCH /api/v1/jobs/{id}/archive` - Archive job
- `DELETE /api/v1/jobs/{id}` - Delete job

### Review Comments
- `GET /api/v1/jobs/{job_id}/review-comments` - List comments for job
- `GET /api/v1/review-comments/{id}` - Get comment by ID
- `POST /api/v1/jobs/{job_id}/review-comments` - Create comment (staff)
- `DELETE /api/v1/review-comments/{id}` - Delete comment

## HTML Routes

- `GET /jobs/` - Job board listing page
- `GET /jobs/{slug}` - Job detail page
- `GET /jobs/submit` - Job submission form
- `GET /jobs/mine` - User's job management page

## Search Filters

Use `POST /api/v1/jobs/search` with:
```json
{
  "city": "San Francisco",
  "region": "California",
  "country": "USA",
  "telecommuting": true,
  "category_id": "uuid",
  "job_type_ids": ["uuid1", "uuid2"],
  "status": "approved"
}
```

## Services

### JobTypeService
- `create_job_type()` - Create with auto-slug generation
- `get_by_slug()` - Retrieve by slug

### JobCategoryService
- `create_job_category()` - Create with auto-slug generation
- `get_by_slug()` - Retrieve by slug

### JobService
- `create_job()` - Create job with job types
- `get_by_slug()` - Retrieve by slug
- `get_by_creator()` - Get user's jobs
- `list_by_status()` - Filter by status
- `search_jobs()` - Advanced search with filters
- `submit_for_review()` - Change status to REVIEW
- `approve_job()` - Change status to APPROVED (staff)
- `reject_job()` - Change status to REJECTED (staff)
- `archive_job()` - Change status to ARCHIVED
- `mark_expired_jobs()` - Batch expire old jobs
- `update_job_types()` - Update many-to-many relationship

### JobReviewCommentService
- `create_comment()` - Add review comment
- `get_by_job()` - Get all comments for a job

## Dependencies

All services and repositories are provided via dependency injection:
```python
from pydotorg.domains.jobs import get_jobs_dependencies

dependencies = get_jobs_dependencies()
```

## Usage Examples

### Creating a Job
```python
job_data = JobCreate(
    company_name="Acme Corp",
    job_title="Senior Python Developer",
    country="USA",
    city="San Francisco",
    region="California",
    description="Join our team...",
    email="jobs@acme.com",
    telecommuting=True,
    category_id=backend_category_id,
    job_type_ids=[fulltime_type_id]
)
job = await job_service.create_job(job_data, creator_id=user.id)
```

### Searching Jobs
```python
filters = JobSearchFilters(
    country="USA",
    telecommuting=True,
    status=JobStatus.APPROVED
)
jobs = await job_service.search_jobs(filters, limit=50)
```

### Review Workflow
```python
await job_service.submit_for_review(job.id)

await comment_service.create_comment(
    job_id=job.id,
    comment="Please clarify salary range",
    creator_id=staff_user.id
)

await job_service.approve_job(job.id)
```

## Database Tables

- `job_types` - Job type definitions
- `job_categories` - Job category definitions
- `jobs` - Job postings
- `job_job_types` - Many-to-many association table
- `job_review_comments` - Review comments

## Notes

- All models use UUID primary keys
- Audit fields (created_at, updated_at) via AuditBase
- Slugs auto-generated from names (JobType, JobCategory)
- Job slugs generated from company + title
- Eager loading configured for common relationships (selectin)
- Expired jobs must be marked manually via `mark_expired_jobs()`
