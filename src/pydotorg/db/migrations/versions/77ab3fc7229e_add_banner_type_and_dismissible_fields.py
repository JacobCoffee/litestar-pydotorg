"""add_banner_type_and_dismissible_fields

Revision ID: 77ab3fc7229e
Revises: 3cc860d76dbf
Create Date: 2025-12-01 02:36:12.738484

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "77ab3fc7229e"
down_revision: str | None = "3cc860d76dbf"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("banners", sa.Column("link_text", sa.String(length=255), nullable=True))
    op.add_column("banners", sa.Column("banner_type", sa.String(length=20), server_default="info", nullable=False))
    op.add_column("banners", sa.Column("is_dismissible", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("banners", sa.Column("is_sitewide", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.create_index(op.f("ix_banners_banner_type"), "banners", ["banner_type"], unique=False)
    op.create_index(op.f("ix_banners_is_sitewide"), "banners", ["is_sitewide"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_banners_is_sitewide"), table_name="banners")
    op.drop_index(op.f("ix_banners_banner_type"), table_name="banners")
    op.drop_column("banners", "is_sitewide")
    op.drop_column("banners", "is_dismissible")
    op.drop_column("banners", "banner_type")
    op.drop_column("banners", "link_text")
