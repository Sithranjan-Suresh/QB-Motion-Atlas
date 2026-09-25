"""add phase_results to analysis_results

Revision ID: 6c48217bf46f
Revises: ca94f21a0da3
Create Date: 2026-09-25 18:03:56.838302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c48217bf46f'
down_revision: Union[str, Sequence[str], None] = 'ca94f21a0da3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Autogenerate also proposed dropping ix_qb_reference_features_embedding_vector_hnsw
    -- a false positive, since that index was created via raw SQL (op.execute
    in the previous migration, task 114) rather than declared as an sa.Index
    on the model, so autogenerate's diff doesn't recognize it as matching
    anything and wants to drop it. Removed that from this migration; the
    index is untouched.
    """
    op.add_column('analysis_results', sa.Column('phase_results', sa.JSON(), nullable=False, server_default='{}'))
    op.alter_column('analysis_results', 'phase_results', server_default=None)


def downgrade() -> None:
    op.drop_column('analysis_results', 'phase_results')
