"""Add status and eol_date to releases

Revision ID: e4ba5c608161
Revises: 004_add_download_statistics
Create Date: 2025-11-30 18:03:50.901026

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4ba5c608161"
down_revision: str | None = "004_add_download_statistics"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    releasestatus_enum = sa.Enum("prerelease", "bugfix", "security", "eol", name="releasestatus")
    releasestatus_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "releases",
        sa.Column(
            "status",
            releasestatus_enum,
            nullable=False,
            server_default="bugfix",
        ),
    )
    op.add_column("releases", sa.Column("eol_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("releases", "eol_date")
    op.drop_column("releases", "status")
    sa.Enum(name="releasestatus").drop(op.get_bind(), checkfirst=True)
