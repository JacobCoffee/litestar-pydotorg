"""Jobs domain URL constants."""

from typing import Final

JOB_TYPES: Final[str] = "/api/v1/job-types"
JOB_TYPE_BY_ID: Final[str] = "/api/v1/job-types/{job_type_id:uuid}"

JOB_CATEGORIES: Final[str] = "/api/v1/job-categories"
JOB_CATEGORY_BY_ID: Final[str] = "/api/v1/job-categories/{job_category_id:uuid}"

JOBS: Final[str] = "/api/v1/jobs"
JOB_BY_ID: Final[str] = "/api/v1/jobs/{job_id:uuid}"
JOB_SEARCH: Final[str] = "/api/v1/jobs/search"
MY_JOBS: Final[str] = "/api/v1/jobs/mine"

JOB_SUBMIT: Final[str] = "/api/v1/jobs/{job_id:uuid}/submit"
JOB_APPROVE: Final[str] = "/api/v1/jobs/{job_id:uuid}/approve"
JOB_REJECT: Final[str] = "/api/v1/jobs/{job_id:uuid}/reject"
JOB_ARCHIVE: Final[str] = "/api/v1/jobs/{job_id:uuid}/archive"

JOB_REVIEW_COMMENTS: Final[str] = "/api/v1/jobs/{job_id:uuid}/review-comments"
REVIEW_COMMENT_BY_ID: Final[str] = "/api/v1/review-comments/{comment_id:uuid}"

JOBS_HTML: Final[str] = "/jobs"
JOB_HTML: Final[str] = "/jobs/{slug:str}"
JOB_SUBMIT_HTML: Final[str] = "/jobs/submit"
MY_JOBS_HTML: Final[str] = "/jobs/mine"
