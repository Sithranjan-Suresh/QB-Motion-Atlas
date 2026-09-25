"""FastAPI app entry point (task 68). Endpoints are added incrementally in
tasks 69-76; this is the scaffold: app instance + a health check.

Run locally: uvicorn api.main:app --reload
"""

from __future__ import annotations

import uuid

from fastapi import BackgroundTasks, FastAPI, UploadFile

from api.schemas import UploadCreatedResponse
from api.storage import save_upload
from db.base import get_session_factory
from db.models import Upload
from pipeline.orchestrator import run_pipeline_for_upload

app = FastAPI(title="QB Motion Atlas API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/uploads", response_model=UploadCreatedResponse, status_code=201)
async def create_upload(file: UploadFile, background_tasks: BackgroundTasks) -> UploadCreatedResponse:
    """Task 69: accept a multipart video upload, save it to local storage,
    and create the `uploads` row. Task 70: trigger the full pipeline
    (pipeline/orchestrator.py) as a background job -- it writes the
    validation outcome or AnalysisResult (tasks 71-72) back to the DB itself
    once it finishes, asynchronously to this response. Request validation
    (file type/size/duration, task 76) is added on top of this separately.
    """
    upload_id = str(uuid.uuid4())
    contents = await file.read()
    video_path = save_upload(upload_id, file.filename or "upload.mp4", contents)

    session_factory = get_session_factory()
    with session_factory() as session:
        upload = Upload(id=upload_id, video_path=str(video_path), validation_status="processing")
        session.add(upload)
        session.commit()

    background_tasks.add_task(run_pipeline_for_upload, upload_id)

    return UploadCreatedResponse(upload_id=upload_id, status="processing")
