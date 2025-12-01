"""Add download statistics table.

Revision ID: 004_add_download_statistics
Revises: 003_add_mailing_domain
Create Date: 2025-11-30

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.types import GUID
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "004_add_download_statistics"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "download_statistics",
        sa.Column("id", GUID(length=16), nullable=False),
        sa.Column("release_file_id", GUID(length=16), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("download_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["release_file_id"],
            ["release_files.id"],
            name="fk_download_statistics_release_file_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_download_statistics"),
        sa.UniqueConstraint("release_file_id", "date", name="uq_download_stats_file_date"),
    )
    op.create_index("ix_download_stats_date", "download_statistics", ["date"])
    op.create_index("ix_download_stats_file_id", "download_statistics", ["release_file_id"])


def downgrade() -> None:
    op.drop_index("ix_download_stats_file_id", table_name="download_statistics")
    op.drop_index("ix_download_stats_date", table_name="download_statistics")
    op.drop_table("download_statistics")
