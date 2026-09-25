"""FastAPI app entry point (task 68). Endpoints are added incrementally in
tasks 69-76; this is the scaffold: app instance + a health check.

Run locally: uvicorn api.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="QB Motion Atlas API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
