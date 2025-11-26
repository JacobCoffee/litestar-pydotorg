"""Add remaining domain models

Revision ID: 002
Revises: 001
Create Date: 2025-11-26 00:00:00.000000

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "002"
down_revision: str = "001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:  # noqa: PLR0915
    # ==================== BLOGS ====================
    op.create_table(
        "feeds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=False),
        sa.Column("feed_url", sa.String(length=500), nullable=False),
        sa.Column("last_fetched", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feed_url"),
    )
    op.create_index(op.f("ix_feeds_is_active"), "feeds", ["is_active"], unique=False)

    op.create_table(
        "blog_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("feed_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("pub_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("guid", sa.String(length=500), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["feed_id"], ["feeds.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("guid", name="uq_blog_entry_guid"),
    )
    op.create_index(op.f("ix_blog_entries_pub_date"), "blog_entries", ["pub_date"], unique=False)

    op.create_table(
        "feed_aggregates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_feed_aggregates_slug"), "feed_aggregates", ["slug"], unique=False)

    op.create_table(
        "feed_aggregate_feeds",
        sa.Column("feed_aggregate_id", sa.UUID(), nullable=False),
        sa.Column("feed_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["feed_aggregate_id"], ["feed_aggregates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feed_id"], ["feeds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("feed_aggregate_id", "feed_id"),
    )

    op.create_table(
        "related_blogs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("blog_name", sa.String(length=255), nullable=False),
        sa.Column("blog_website", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ==================== EVENTS ====================
    op.create_table(
        "calendars",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_calendars_slug"), "calendars", ["slug"], unique=False)
    op.create_index(op.f("ix_calendars_created"), "calendars", ["created"], unique=False)

    op.create_table(
        "event_locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_event_locations_slug"), "event_locations", ["slug"], unique=False)

    op.create_table(
        "event_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("calendar_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["calendar_id"], ["calendars.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_event_categories_slug"), "event_categories", ["slug"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("calendar_id", sa.UUID(), nullable=False),
        sa.Column("venue_id", sa.UUID(), nullable=True),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["calendar_id"], ["calendars.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venue_id"], ["event_locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_events_slug"), "events", ["slug"], unique=False)
    op.create_index(op.f("ix_events_featured"), "events", ["featured"], unique=False)
    op.create_index(op.f("ix_events_created"), "events", ["created"], unique=False)

    op.create_table(
        "event_event_categories",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["event_categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id", "category_id"),
    )

    op.create_table(
        "event_occurrences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("dt_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dt_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_event_occurrences_dt_start"), "event_occurrences", ["dt_start"], unique=False)

    # ==================== JOBS ====================
    op.create_table(
        "job_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_job_categories_slug"), "job_categories", ["slug"], unique=False)

    op.create_table(
        "job_types",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_job_types_slug"), "job_types", ["slug"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("job_title", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("contact", sa.String(length=200), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "review", "approved", "rejected", "archived", "expired", name="jobstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("telecommuting", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("agencies", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires", sa.Date(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["category_id"], ["job_categories.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_jobs_slug"), "jobs", ["slug"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)

    op.create_table(
        "job_job_types",
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("job_type_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_type_id"], ["job_types.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id", "job_type_id"),
    )

    op.create_table(
        "job_review_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
    )

    # ==================== MINUTES ====================
    op.create_table(
        "minutes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum("markdown", "restructuredtext", "html", name="contenttype", create_type=False),
            nullable=False,
        ),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_minutes_slug"), "minutes", ["slug"], unique=False)
    op.create_index(op.f("ix_minutes_date"), "minutes", ["date"], unique=False)
    op.create_index(op.f("ix_minutes_is_published"), "minutes", ["is_published"], unique=False)

    # ==================== NOMINATIONS ====================
    op.create_table(
        "elections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("nominations_open", sa.Date(), nullable=False),
        sa.Column("nominations_close", sa.Date(), nullable=False),
        sa.Column("voting_open", sa.Date(), nullable=False),
        sa.Column("voting_close", sa.Date(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_elections_slug"), "elections", ["slug"], unique=False)
    op.create_index(op.f("ix_elections_nominations_open"), "elections", ["nominations_open"], unique=False)
    op.create_index(op.f("ix_elections_nominations_close"), "elections", ["nominations_close"], unique=False)
    op.create_index(op.f("ix_elections_voting_open"), "elections", ["voting_open"], unique=False)
    op.create_index(op.f("ix_elections_voting_close"), "elections", ["voting_close"], unique=False)

    op.create_table(
        "nominees",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("election_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["election_id"], ["elections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_nominees_accepted"), "nominees", ["accepted"], unique=False)

    op.create_table(
        "nominations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nominee_id", sa.UUID(), nullable=False),
        sa.Column("nominator_id", sa.UUID(), nullable=False),
        sa.Column("endorsement", sa.Text(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["nominee_id"], ["nominees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["nominator_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ==================== SUCCESS STORIES ====================
    op.create_table(
        "story_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_story_categories_slug"), "story_categories", ["slug"], unique=False)

    op.create_table(
        "success_stories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("company_url", sa.String(length=500), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum("markdown", "restructuredtext", "html", name="contenttype", create_type=False),
            nullable=False,
        ),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["category_id"], ["story_categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_success_stories_slug"), "success_stories", ["slug"], unique=False)
    op.create_index(op.f("ix_success_stories_is_published"), "success_stories", ["is_published"], unique=False)
    op.create_index(op.f("ix_success_stories_featured"), "success_stories", ["featured"], unique=False)

    # ==================== WORK GROUPS ====================
    op.create_table(
        "work_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_work_groups_slug"), "work_groups", ["slug"], unique=False)
    op.create_index(op.f("ix_work_groups_active"), "work_groups", ["active"], unique=False)

    # ==================== CODE SAMPLES ====================
    op.create_table(
        "code_samples",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_code_samples_slug"), "code_samples", ["slug"], unique=False)
    op.create_index(op.f("ix_code_samples_is_published"), "code_samples", ["is_published"], unique=False)

    # ==================== COMMUNITY ====================
    op.create_table(
        "community_posts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum("markdown", "restructuredtext", "html", name="contenttype", create_type=False),
            nullable=False,
        ),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_community_posts_slug"), "community_posts", ["slug"], unique=False)
    op.create_index(op.f("ix_community_posts_is_published"), "community_posts", ["is_published"], unique=False)

    op.create_table(
        "community_photos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=True),
        sa.Column("image", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.String(length=500), nullable=True),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "community_videos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "community_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ==================== BANNERS ====================
    op.create_table(
        "banners",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_banners_is_active"), "banners", ["is_active"], unique=False)
    op.create_index(op.f("ix_banners_start_date"), "banners", ["start_date"], unique=False)
    op.create_index(op.f("ix_banners_end_date"), "banners", ["end_date"], unique=False)


def downgrade() -> None:  # noqa: PLR0915
    # ==================== BANNERS ====================
    op.drop_index(op.f("ix_banners_end_date"), table_name="banners")
    op.drop_index(op.f("ix_banners_start_date"), table_name="banners")
    op.drop_index(op.f("ix_banners_is_active"), table_name="banners")
    op.drop_table("banners")

    # ==================== COMMUNITY ====================
    op.drop_table("community_links")
    op.drop_table("community_videos")
    op.drop_table("community_photos")
    op.drop_index(op.f("ix_community_posts_is_published"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_slug"), table_name="community_posts")
    op.drop_table("community_posts")

    # ==================== CODE SAMPLES ====================
    op.drop_index(op.f("ix_code_samples_is_published"), table_name="code_samples")
    op.drop_index(op.f("ix_code_samples_slug"), table_name="code_samples")
    op.drop_table("code_samples")

    # ==================== WORK GROUPS ====================
    op.drop_index(op.f("ix_work_groups_active"), table_name="work_groups")
    op.drop_index(op.f("ix_work_groups_slug"), table_name="work_groups")
    op.drop_table("work_groups")

    # ==================== SUCCESS STORIES ====================
    op.drop_index(op.f("ix_success_stories_featured"), table_name="success_stories")
    op.drop_index(op.f("ix_success_stories_is_published"), table_name="success_stories")
    op.drop_index(op.f("ix_success_stories_slug"), table_name="success_stories")
    op.drop_table("success_stories")
    op.drop_index(op.f("ix_story_categories_slug"), table_name="story_categories")
    op.drop_table("story_categories")

    # ==================== NOMINATIONS ====================
    op.drop_table("nominations")
    op.drop_index(op.f("ix_nominees_accepted"), table_name="nominees")
    op.drop_table("nominees")
    op.drop_index(op.f("ix_elections_voting_close"), table_name="elections")
    op.drop_index(op.f("ix_elections_voting_open"), table_name="elections")
    op.drop_index(op.f("ix_elections_nominations_close"), table_name="elections")
    op.drop_index(op.f("ix_elections_nominations_open"), table_name="elections")
    op.drop_index(op.f("ix_elections_slug"), table_name="elections")
    op.drop_table("elections")

    # ==================== MINUTES ====================
    op.drop_index(op.f("ix_minutes_is_published"), table_name="minutes")
    op.drop_index(op.f("ix_minutes_date"), table_name="minutes")
    op.drop_index(op.f("ix_minutes_slug"), table_name="minutes")
    op.drop_table("minutes")

    # ==================== JOBS ====================
    op.drop_table("job_review_comments")
    op.drop_table("job_job_types")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_slug"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_job_types_slug"), table_name="job_types")
    op.drop_table("job_types")
    op.drop_index(op.f("ix_job_categories_slug"), table_name="job_categories")
    op.drop_table("job_categories")

    op.execute("DROP TYPE IF EXISTS jobstatus")

    # ==================== EVENTS ====================
    op.drop_index(op.f("ix_event_occurrences_dt_start"), table_name="event_occurrences")
    op.drop_table("event_occurrences")
    op.drop_table("event_event_categories")
    op.drop_index(op.f("ix_events_created"), table_name="events")
    op.drop_index(op.f("ix_events_featured"), table_name="events")
    op.drop_index(op.f("ix_events_slug"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_event_categories_slug"), table_name="event_categories")
    op.drop_table("event_categories")
    op.drop_index(op.f("ix_event_locations_slug"), table_name="event_locations")
    op.drop_table("event_locations")
    op.drop_index(op.f("ix_calendars_created"), table_name="calendars")
    op.drop_index(op.f("ix_calendars_slug"), table_name="calendars")
    op.drop_table("calendars")

    # ==================== BLOGS ====================
    op.drop_table("related_blogs")
    op.drop_table("feed_aggregate_feeds")
    op.drop_index(op.f("ix_feed_aggregates_slug"), table_name="feed_aggregates")
    op.drop_table("feed_aggregates")
    op.drop_index(op.f("ix_blog_entries_pub_date"), table_name="blog_entries")
    op.drop_table("blog_entries")
    op.drop_index(op.f("ix_feeds_is_active"), table_name="feeds")
    op.drop_table("feeds")
