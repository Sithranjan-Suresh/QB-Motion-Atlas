"""add landmark_sequences table

Revision ID: 1ee8da853b35
Revises: 6c48217bf46f
Create Date: 2026-09-25 21:06:02.764532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ee8da853b35'
down_revision: Union[str, Sequence[str], None] = '6c48217bf46f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Autogenerate again proposed dropping ix_qb_reference_features_embedding_vector_hnsw
    -- the same false positive as migration 6c48217bf46f (raw-SQL index, not
    an sa.Index on the model, so autogenerate's diff doesn't recognize it).
    Removed; the index is untouched.
    """
    op.create_table('landmark_sequences',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('upload_id', sa.String(), nullable=True),
    sa.Column('reference_clip_id', sa.String(), nullable=True),
    sa.Column('fps', sa.Float(), nullable=False),
    sa.Column('frames', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['reference_clip_id'], ['qb_reference_clips.clip_id'], ),
    sa.ForeignKeyConstraint(['upload_id'], ['uploads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('landmark_sequences')
