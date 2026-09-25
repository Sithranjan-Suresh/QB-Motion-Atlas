"""add hnsw index on embedding_vector

Revision ID: ca94f21a0da3
Revises: d7f66e4e50ea
Create Date: 2026-09-25 17:58:22.122663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca94f21a0da3'
down_revision: Union[str, Sequence[str], None] = 'd7f66e4e50ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_qb_reference_features_embedding_vector_hnsw"


def upgrade() -> None:
    """HNSW over IVFFlat (task 114's either/or): HNSW gives good recall
    without needing to pre-know the row count to size lists around (IVFFlat's
    tuning knob), which matters for a reference set that's still small and
    growing (task 99). vector_cosine_ops matches
    pipeline/similarity_v2.py::embedding_similarity()'s cosine-distance
    metric -- an index built on a different distance function wouldn't be
    used by a cosine-distance query.
    """
    op.execute(
        f"CREATE INDEX {INDEX_NAME} ON qb_reference_features "
        f"USING hnsw (embedding_vector vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
