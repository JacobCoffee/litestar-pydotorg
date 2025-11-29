"""Add mailing domain tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-27 00:00:00.000000

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "003"
down_revision: str = "002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # ==================== EMAIL TEMPLATES ====================
    op.create_table(
        "email_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("internal_name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "template_type",
            sa.Enum(
                "transactional",
                "notification",
                "newsletter",
                "marketing",
                "system",
                name="emailtemplatetype",
            ),
            nullable=False,
            server_default="transactional",
        ),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("internal_name"),
    )
    op.create_index(
        op.f("ix_email_templates_internal_name"),
        "email_templates",
        ["internal_name"],
        unique=True,
    )
    op.create_index(
        op.f("ix_email_templates_template_type"),
        "email_templates",
        ["template_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_templates_is_active"),
        "email_templates",
        ["is_active"],
        unique=False,
    )

    # ==================== EMAIL LOGS ====================
    op.create_table(
        "email_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("template_name", sa.String(length=128), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_logs_template_name"),
        "email_logs",
        ["template_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_logs_recipient_email"),
        "email_logs",
        ["recipient_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_logs_status"),
        "email_logs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    # ==================== EMAIL LOGS ====================
    op.drop_index(op.f("ix_email_logs_status"), table_name="email_logs")
    op.drop_index(op.f("ix_email_logs_recipient_email"), table_name="email_logs")
    op.drop_index(op.f("ix_email_logs_template_name"), table_name="email_logs")
    op.drop_table("email_logs")

    # ==================== EMAIL TEMPLATES ====================
    op.drop_index(op.f("ix_email_templates_is_active"), table_name="email_templates")
    op.drop_index(op.f("ix_email_templates_template_type"), table_name="email_templates")
    op.drop_index(op.f("ix_email_templates_internal_name"), table_name="email_templates")
    op.drop_table("email_templates")

    op.execute("DROP TYPE IF EXISTS emailtemplatetype")
