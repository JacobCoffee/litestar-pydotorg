"""Unit tests for Job models."""

from __future__ import annotations

import datetime
from datetime import date, timedelta
from uuid import uuid4

import time_machine

from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobStatus, JobType


class TestJobStatusEnum:
    def test_enum_values(self) -> None:
        assert JobStatus.DRAFT.value == "draft"
        assert JobStatus.REVIEW.value == "review"
        assert JobStatus.APPROVED.value == "approved"
        assert JobStatus.REJECTED.value == "rejected"
        assert JobStatus.ARCHIVED.value == "archived"
        assert JobStatus.EXPIRED.value == "expired"

    def test_enum_members(self) -> None:
        members = list(JobStatus)
        assert len(members) == 6
        assert JobStatus.DRAFT in members
        assert JobStatus.REVIEW in members
        assert JobStatus.APPROVED in members
        assert JobStatus.REJECTED in members
        assert JobStatus.ARCHIVED in members
        assert JobStatus.EXPIRED in members


class TestJobTypeModel:
    def test_create_job_type(self) -> None:
        job_type = JobType(name="Full-time", slug="full-time")
        assert job_type.name == "Full-time"
        assert job_type.slug == "full-time"


class TestJobCategoryModel:
    def test_create_job_category(self) -> None:
        category = JobCategory(name="Backend Development", slug="backend-development")
        assert category.name == "Backend Development"
        assert category.slug == "backend-development"


class TestJobModel:
    def test_create_job(self) -> None:
        creator_id = uuid4()
        job = Job(
            slug="python-developer-acme",
            creator_id=creator_id,
            company_name="ACME Corp",
            job_title="Python Developer",
            country="USA",
            description="Looking for a Python developer",
            email="jobs@acme.com",
        )
        assert job.slug == "python-developer-acme"
        assert job.creator_id == creator_id
        assert job.company_name == "ACME Corp"
        assert job.job_title == "Python Developer"
        assert job.country == "USA"
        assert job.description == "Looking for a Python developer"
        assert job.email == "jobs@acme.com"

    def test_job_with_explicit_defaults(self) -> None:
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test description",
            email="test@example.com",
            status=JobStatus.DRAFT,
            telecommuting=False,
            agencies=False,
        )
        assert job.city is None
        assert job.region is None
        assert job.requirements is None
        assert job.contact is None
        assert job.url is None
        assert job.status == JobStatus.DRAFT
        assert job.telecommuting is False
        assert job.agencies is False
        assert job.expires is None
        assert job.category_id is None

    def test_job_with_all_fields(self) -> None:
        creator_id = uuid4()
        category_id = uuid4()
        expires = date.today() + timedelta(days=30)
        job = Job(
            slug="senior-python-engineer",
            creator_id=creator_id,
            company_name="Tech Startup",
            job_title="Senior Python Engineer",
            city="San Francisco",
            region="California",
            country="USA",
            description="We're looking for a senior Python engineer",
            requirements="5+ years Python experience",
            contact="hiring@techstartup.com",
            url="https://techstartup.com/careers",
            email="jobs@techstartup.com",
            status=JobStatus.APPROVED,
            telecommuting=True,
            agencies=False,
            expires=expires,
            category_id=category_id,
        )
        assert job.city == "San Francisco"
        assert job.region == "California"
        assert job.requirements == "5+ years Python experience"
        assert job.contact == "hiring@techstartup.com"
        assert job.url == "https://techstartup.com/careers"
        assert job.status == JobStatus.APPROVED
        assert job.telecommuting is True
        assert job.agencies is False
        assert job.expires == expires
        assert job.category_id == category_id

    def test_is_expired_no_expiry_date(self) -> None:
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test",
            email="test@example.com",
        )
        assert job.is_expired is False

    def test_is_expired_future_date(self) -> None:
        future_date = date.today() + timedelta(days=30)
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test",
            email="test@example.com",
            expires=future_date,
        )
        assert job.is_expired is False

    @time_machine.travel(datetime.datetime(2024, 6, 15, 12, 0, 0, tzinfo=datetime.UTC))
    def test_is_expired_today(self) -> None:
        today = datetime.datetime.now(tz=datetime.UTC).date()
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test",
            email="test@example.com",
            expires=today,
        )
        assert job.is_expired is False

    def test_is_expired_past_date(self) -> None:
        past_date = date.today() - timedelta(days=1)
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test",
            email="test@example.com",
            expires=past_date,
        )
        assert job.is_expired is True

    def test_job_status_progression(self) -> None:
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test",
            email="test@example.com",
            status=JobStatus.DRAFT,
        )
        assert job.status == JobStatus.DRAFT

        job.status = JobStatus.REVIEW
        assert job.status == JobStatus.REVIEW

        job.status = JobStatus.APPROVED
        assert job.status == JobStatus.APPROVED

    def test_job_telecommuting_flag(self) -> None:
        job = Job(
            slug="remote-job",
            creator_id=uuid4(),
            company_name="Remote Co",
            job_title="Remote Python Dev",
            country="USA",
            description="Remote position",
            email="jobs@remote.com",
            telecommuting=True,
        )
        assert job.telecommuting is True

    def test_job_agencies_flag(self) -> None:
        job = Job(
            slug="test-job",
            creator_id=uuid4(),
            company_name="Test Co",
            job_title="Test Job",
            country="USA",
            description="Test",
            email="test@example.com",
            agencies=True,
        )
        assert job.agencies is True


class TestJobReviewCommentModel:
    def test_create_review_comment(self) -> None:
        job_id = uuid4()
        creator_id = uuid4()
        comment = JobReviewComment(
            job_id=job_id,
            comment="Please add more details to the job description",
            creator_id=creator_id,
        )
        assert comment.job_id == job_id
        assert comment.comment == "Please add more details to the job description"
        assert comment.creator_id == creator_id
