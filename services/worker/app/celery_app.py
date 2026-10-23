import os

from celery import Celery

valkey_url = os.environ.get("VALKEY_URL", "redis://localhost:6379/0")

celery_app = Celery("fdr_worker", broker=valkey_url, backend=valkey_url)
celery_app.conf.beat_schedule = {}


@celery_app.task(name="worker.ping")
def ping() -> str:
    return "pong"
