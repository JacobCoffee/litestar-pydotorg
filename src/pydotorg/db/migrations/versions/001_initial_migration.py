"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-11-25 18:30:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=150), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_staff", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("date_joined", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("search_visibility", sa.Enum("PUBLIC", "PRIVATE", name="searchvisibility"), nullable=False),
        sa.Column("email_privacy", sa.Enum("PUBLIC", "PRIVATE", "NEVER", name="emailprivacy"), nullable=False),
        sa.Column("public_profile", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("membership_type", sa.Enum("BASIC", "SUPPORTING", "SPONSOR", "MANAGING", "CONTRIBUTING", "FELLOW", name="membershiptype"), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("preferred_name", sa.String(length=255), nullable=False),
        sa.Column("email_address", sa.String(length=254), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("psf_code_of_conduct", sa.Boolean(), nullable=False),
        sa.Column("psf_announcements", sa.Boolean(), nullable=False),
        sa.Column("votes", sa.Boolean(), nullable=False),
        sa.Column("last_vote_affirmation", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "user_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("url_type", sa.Enum("MEETUP", "DISTRIBUTION_LIST", "OTHER", name="usergrouptype"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("trusted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("keywords", sa.String(length=1000), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Enum("MARKDOWN", "RESTRUCTUREDTEXT", "HTML", name="contenttype"), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("path"),
    )
    op.create_index(op.f("ix_pages_path"), "pages", ["path"], unique=False)
    op.create_index(op.f("ix_pages_is_published"), "pages", ["is_published"], unique=False)
    op.create_index(op.f("ix_pages_created"), "pages", ["created"], unique=False)

    op.create_table(
        "page_images",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("page_id", sa.UUID(), nullable=False),
        sa.Column("image", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "page_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("page_id", sa.UUID(), nullable=False),
        sa.Column("document", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "download_os",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_download_os_slug"), "download_os", ["slug"], unique=False)
    op.create_index(op.f("ix_download_os_created"), "download_os", ["created"], unique=False)

    op.create_table(
        "releases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("version", sa.Enum("1", "2", "3", "manager", name="pythonversion"), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("pre_release", sa.Boolean(), nullable=False),
        sa.Column("show_on_download_page", sa.Boolean(), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("release_page_id", sa.UUID(), nullable=True),
        sa.Column("release_notes_url", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["release_page_id"], ["pages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_releases_slug"), "releases", ["slug"], unique=False)
    op.create_index(op.f("ix_releases_is_latest"), "releases", ["is_latest"], unique=False)
    op.create_index(op.f("ix_releases_is_published"), "releases", ["is_published"], unique=False)
    op.create_index(op.f("ix_releases_created"), "releases", ["created"], unique=False)

    op.create_table(
        "release_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("release_id", sa.UUID(), nullable=False),
        sa.Column("os_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_source", sa.Boolean(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("gpg_signature_file", sa.String(length=500), nullable=False),
        sa.Column("sigstore_signature_file", sa.String(length=500), nullable=False),
        sa.Column("sigstore_cert_file", sa.String(length=500), nullable=False),
        sa.Column("sigstore_bundle_file", sa.String(length=500), nullable=False),
        sa.Column("sbom_spdx2_file", sa.String(length=500), nullable=False),
        sa.Column("md5_sum", sa.String(length=200), nullable=False),
        sa.Column("filesize", sa.BigInteger(), nullable=False),
        sa.Column("download_button", sa.Boolean(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["os_id"], ["download_os.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint("release_id", "os_id", "download_button", name="uq_release_os_download_button"),
    )
    op.create_index(op.f("ix_release_files_slug"), "release_files", ["slug"], unique=False)
    op.create_index(op.f("ix_release_files_created"), "release_files", ["created"], unique=False)

    op.create_table(
        "sponsors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("landing_page_url", sa.String(length=500), nullable=False),
        sa.Column("twitter_handle", sa.String(length=100), nullable=False),
        sa.Column("linked_in_page_url", sa.String(length=500), nullable=False),
        sa.Column("web_logo", sa.String(length=500), nullable=False),
        sa.Column("print_logo", sa.String(length=500), nullable=False),
        sa.Column("primary_phone", sa.String(length=50), nullable=False),
        sa.Column("mailing_address_line_1", sa.String(length=255), nullable=False),
        sa.Column("mailing_address_line_2", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("country_of_incorporation", sa.String(length=100), nullable=False),
        sa.Column("state_of_incorporation", sa.String(length=100), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_sponsors_created"), "sponsors", ["created"], unique=False)

    op.create_table(
        "sponsorships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sponsor_id", sa.UUID(), nullable=False),
        sa.Column("submitted_by_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.Enum("APPLIED", "REJECTED", "APPROVED", "FINALIZED", name="sponsorshipstatus"), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("applied_on", sa.Date(), nullable=True),
        sa.Column("approved_on", sa.Date(), nullable=True),
        sa.Column("rejected_on", sa.Date(), nullable=True),
        sa.Column("finalized_on", sa.Date(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("sponsorship_fee", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("for_modified_package", sa.Boolean(), nullable=False),
        sa.Column("renewal", sa.Boolean(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("last_modified_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["sponsor_id"], ["sponsors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_modified_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_sponsorships_status"), "sponsorships", ["status"], unique=False)
    op.create_index(op.f("ix_sponsorships_created"), "sponsorships", ["created"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sponsorships_created"), table_name="sponsorships")
    op.drop_index(op.f("ix_sponsorships_status"), table_name="sponsorships")
    op.drop_table("sponsorships")

    op.drop_index(op.f("ix_sponsors_created"), table_name="sponsors")
    op.drop_table("sponsors")

    op.drop_index(op.f("ix_release_files_created"), table_name="release_files")
    op.drop_index(op.f("ix_release_files_slug"), table_name="release_files")
    op.drop_table("release_files")

    op.drop_index(op.f("ix_releases_created"), table_name="releases")
    op.drop_index(op.f("ix_releases_is_published"), table_name="releases")
    op.drop_index(op.f("ix_releases_is_latest"), table_name="releases")
    op.drop_index(op.f("ix_releases_slug"), table_name="releases")
    op.drop_table("releases")

    op.drop_index(op.f("ix_download_os_created"), table_name="download_os")
    op.drop_index(op.f("ix_download_os_slug"), table_name="download_os")
    op.drop_table("download_os")

    op.drop_table("page_documents")
    op.drop_table("page_images")

    op.drop_index(op.f("ix_pages_created"), table_name="pages")
    op.drop_index(op.f("ix_pages_is_published"), table_name="pages")
    op.drop_index(op.f("ix_pages_path"), table_name="pages")
    op.drop_table("pages")

    op.drop_table("user_groups")
    op.drop_table("memberships")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS sponsorshipstatus")
    op.execute("DROP TYPE IF EXISTS pythonversion")
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS usergrouptype")
    op.execute("DROP TYPE IF EXISTS membershiptype")
    op.execute("DROP TYPE IF EXISTS emailprivacy")
    op.execute("DROP TYPE IF EXISTS searchvisibility")
