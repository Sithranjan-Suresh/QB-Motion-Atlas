"""add pgvector extension and embedding_vector column

Revision ID: d7f66e4e50ea
Revises: c9b4dcb4a006
Create Date: 2026-09-25 17:57:44.628717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'd7f66e4e50ea'
down_revision: Union[str, Sequence[str], None] = 'c9b4dcb4a006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Autogenerate produced an ALTER COLUMN TYPE from JSON to VECTOR, but
    Postgres has no built-in cast between those two types -- and there's no
    real embedding_vector data to preserve yet anyway (V1 never populated
    it), so drop-and-recreate the column is simpler and correct here.
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.drop_column('qb_reference_features', 'embedding_vector')
    op.add_column('qb_reference_features', sa.Column('embedding_vector', Vector(8), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('qb_reference_features', 'embedding_vector')
    op.add_column('qb_reference_features', sa.Column('embedding_vector', sa.JSON(), nullable=True))
    # Not dropping the vector extension -- another table/migration could
    # depend on it, and CREATE EXTENSION IF NOT EXISTS makes re-upgrading safe either way.
