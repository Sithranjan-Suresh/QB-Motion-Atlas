"""Upload deletion: on request (DELETE /uploads/{id}) and automatically after
UPLOAD_RETENTION_DAYS (default 7), swept by api/worker.py. Removes the
stored video and every DB row derived from it."""

from __future__ import annotations

import datetime
import logging
import os

from api.storage import get_storage
from db.base import get_session_factory
from db.models import AnalysisResult, LandmarkSequence, PhaseBoundaryRow, Upload

logger = logging.getLogger(__name__)


def retention_days() -> float:
    return float(os.environ.get("UPLOAD_RETENTION_DAYS", "7"))


def purge_upload(session, upload: Upload) -> None:
    """Deletes one upload's video and rows. Caller commits."""
    try:
        get_storage().delete(upload.video_path)
    except Exception:  # noqa: BLE001 -- a missing object shouldn't block deleting the rows
        logger.warning("could not delete stored video", extra={"upload_id": upload.id}, exc_info=True)
    session.query(AnalysisResult).filter_by(upload_id=upload.id).delete()
    session.query(PhaseBoundaryRow).filter_by(upload_id=upload.id).delete()
    session.query(LandmarkSequence).filter_by(upload_id=upload.id).delete()
    session.delete(upload)


def purge_expired_uploads() -> int:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days())
    session_factory = get_session_factory()
    with session_factory() as session:
        expired = (
            session.query(Upload)
            .filter(Upload.created_at < cutoff, Upload.validation_status != "processing")
            .limit(500)
            .all()
        )
        for upload in expired:
            purge_upload(session, upload)
        session.commit()
    if expired:
        logger.info("purged expired uploads", extra={"count": len(expired)})
    return len(expired)
