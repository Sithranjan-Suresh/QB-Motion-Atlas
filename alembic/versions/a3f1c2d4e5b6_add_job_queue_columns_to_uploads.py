"""add job-queue columns to uploads

Revision ID: a3f1c2d4e5b6
Revises: 1ee8da853b35
Create Date: 2026-09-30 03:30:00.000000

uploads doubles as the job queue (api/worker.py): a row with
validation_status='processing' is a pending job. attempts/locked_at let a
worker claim a row with SELECT ... FOR UPDATE SKIP LOCKED and let a stale
claim (worker crashed or redeployed mid-job) be retried; last_error keeps
the failure for debugging. The index serves the worker's claim query.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1c2d4e5b6'
down_revision: Union[str, Sequence[str], None] = '1ee8da853b35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('uploads', sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('uploads', sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('uploads', sa.Column('last_error', sa.String(), nullable=True))
    op.create_index('ix_uploads_status_created_at', 'uploads', ['validation_status', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_uploads_status_created_at', table_name='uploads')
    op.drop_column('uploads', 'last_error')
    op.drop_column('uploads', 'locked_at')
    op.drop_column('uploads', 'attempts')
