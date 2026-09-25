"""Query qb_reference_features' pgvector HNSW index for nearest neighbors
by embedding (task 115) -- replaces pulling every reference row into
Python and scoring them in a loop (what pipeline/orchestrator.py's V0/V1
layer still does for compare_features, since that operates on the JSON
feature_vector, not a DB-indexable type) with a single indexed SQL query.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import QBReferenceFeature


def find_nearest_by_embedding(
    session: Session,
    phase_name: str,
    query_embedding: list[float],
    limit: int = 5,
) -> list[QBReferenceFeature]:
    """Returns up to `limit` QBReferenceFeature rows for `phase_name`,
    ordered by ascending cosine distance to `query_embedding` (nearest
    first) -- uses the HNSW index (task 114) via pgvector's `<=>` operator
    rather than fetching every row and computing distance in Python.
    """
    return (
        session.query(QBReferenceFeature)
        .filter(QBReferenceFeature.phase_name == phase_name)
        .filter(QBReferenceFeature.embedding_vector.isnot(None))
        .order_by(QBReferenceFeature.embedding_vector.cosine_distance(query_embedding))
        .limit(limit)
        .all()
    )
