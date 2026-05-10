"""
Celery application factory.

Uses Redis as both broker and result backend.
Task routing separates high-priority webhook processing from
slower bulk sync operations so they don't block each other.
"""
from celery import Celery
from celery.utils.log import get_task_logger

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "shopify_analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    # ── Serialization ───────────────────────────────────────────────────
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # ── Timezone ────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,

    # ── Task behaviour ──────────────────────────────────────────────────
    task_acks_late=True,          # ack only after successful execution
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1, # fair dispatch for long-running tasks

    # ── Result expiry ───────────────────────────────────────────────────
    result_expires=3600,  # 1 hour

    # ── Retry defaults ──────────────────────────────────────────────────
    task_max_retries=settings.WEBHOOK_MAX_RETRIES,

    # ── Routing ─────────────────────────────────────────────────────────
    # Two queues:
    #   • webhooks  — fast, high-priority real-time events
    #   • bulk      — slow, large historical syncs
    task_routes={
        "app.workers.tasks.process_webhook_task": {"queue": "webhooks"},
        "app.workers.tasks.run_bulk_sync_task": {"queue": "bulk"},
        "app.workers.tasks.run_incremental_sync_task": {"queue": "bulk"},
        "app.workers.tasks.register_webhooks_task": {"queue": "webhooks"},
        "app.workers.tasks.trigger_initial_sync_task": {"queue": "bulk"},
    },
    task_default_queue="webhooks",

    # ── Beat schedule (incremental sync every hour) ──────────────────────
    beat_schedule={
        "incremental-sync-all-stores": {
            "task": "app.workers.tasks.incremental_sync_all_stores_task",
            "schedule": 3600.0,  # every hour
            "options": {"queue": "bulk"},
        },
    },
)
