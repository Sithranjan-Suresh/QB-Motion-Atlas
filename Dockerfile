# QB Motion Atlas API + upload worker. Runs on Hugging Face Spaces (Docker
# SDK, port 7860), Render, Fly, or any container host: PORT is honored.
# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=7860 \
    JOB_RUNNER=worker

# ffmpeg: reference-clip trimming. libgl/libegl/libgles: MediaPipe + OpenCV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libgl1 libegl1 libgles2 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces run the container as uid 1000; match it everywhere.
RUN useradd --create-home --uid 1000 app
WORKDIR /home/app/app

# The optional `extra_ca` build secret is only for building behind a
# TLS-intercepting proxy (docker build --secret id=extra_ca,src=ca.crt);
# it's never written into the image, and hosts build fine without it.
COPY --chown=app:app requirements-prod.txt .
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi \
    && pip install -r requirements-prod.txt

# MediaPipe pose model (gitignored in the repo, ~5.6 MB).
RUN --mount=type=secret,id=extra_ca,required=false \
    CA_ARG=""; if [ -f /run/secrets/extra_ca ]; then CA_ARG="--cacert /run/secrets/extra_ca"; fi \
    && mkdir -p models \
    && curl -fsSL $CA_ARG -o models/pose_landmarker_lite.task \
       https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task

COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app api ./api
COPY --chown=app:app db ./db
COPY --chown=app:app models ./models
COPY --chown=app:app pipeline ./pipeline
COPY --chown=app:app assets ./assets
COPY --chown=app:app data/provenance.csv ./data/provenance.csv
COPY --chown=app:app scripts/start.sh ./scripts/start.sh
RUN chown -R app:app /home/app/app

USER app
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD curl -fs "http://localhost:${PORT}/health" || exit 1
CMD ["bash", "scripts/start.sh"]
