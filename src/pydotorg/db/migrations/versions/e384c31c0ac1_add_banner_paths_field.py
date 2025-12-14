"""add_banner_paths_field

Revision ID: e384c31c0ac1
Revises: a54615e2a02f
Create Date: 2025-12-01 03:14:54.237523

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "e384c31c0ac1"
down_revision: str | None = "a54615e2a02f"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("banners", sa.Column("paths", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("banners", "paths")
