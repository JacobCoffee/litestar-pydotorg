"""add_banner_target_field

Revision ID: a54615e2a02f
Revises: 77ab3fc7229e
Create Date: 2025-12-01 03:00:23.906332

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "a54615e2a02f"
down_revision: str | None = "77ab3fc7229e"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add target column with server default for existing rows
    op.add_column("banners", sa.Column("target", sa.String(length=20), nullable=False, server_default="frontend"))
    op.create_index(op.f("ix_banners_target"), "banners", ["target"], unique=False)
    # Remove server default after data migration
    op.alter_column("banners", "target", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_banners_target"), table_name="banners")
    op.drop_column("banners", "target")
