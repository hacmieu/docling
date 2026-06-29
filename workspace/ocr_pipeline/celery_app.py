"""Celery application for OCR pipeline background jobs."""

from __future__ import annotations

import os

from celery import Celery

from workspace.ocr_pipeline.db_postgres import load_dotenv

load_dotenv()

broker = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", broker)

app = Celery(
    "ocr_pipeline",
    broker=broker,
    backend=result_backend,
    include=["workspace.ocr_pipeline.tasks.vision_tasks"],
)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_routes={
        "workspace.ocr_pipeline.tasks.vision_tasks.vision_ocr_document": {"queue": "vision"},
    },
    task_default_queue="default",
)
