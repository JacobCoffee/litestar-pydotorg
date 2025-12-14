"""add_sa_orm_sentinel_to_download_statistics

Revision ID: 380becc88f99
Revises: db342d0879cb
Create Date: 2025-12-14 09:31:20.538917

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '380becc88f99'
down_revision: str | None = 'db342d0879cb'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('download_statistics')]
    if 'sa_orm_sentinel' not in columns:
        op.add_column(
            'download_statistics',
            sa.Column('sa_orm_sentinel', sa.Integer(), nullable=True, default=0)
        )


def downgrade() -> None:
    op.drop_column('download_statistics', 'sa_orm_sentinel')
