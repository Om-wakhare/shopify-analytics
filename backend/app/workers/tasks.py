"""
Celery tasks for Shopify data pipeline.

All tasks that touch the database run their own sync SQLAlchemy session
(Celery workers are NOT async — they use the sync engine).
Tasks use exponential back-off retries for transient failures.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from celery import Task
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


# ---------------------------------------------------------------------------
# Helper: run an async function inside a Celery (sync) task
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Execute an async coroutine from a synchronous Celery task."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Task: Process a single webhook event
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,  # base back-off in seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name="app.workers.tasks.process_webhook_task",
)
def process_webhook_task(self: Task, webhook_event_id: str) -> dict:
    """
    Process a single WebhookEvent record.
    Dispatches to the appropriate handler based on topic.
    Marks the event as processed or failed.
    """
    return _run_async(_process_webhook_async(webhook_event_id))


async def _process_webhook_async(webhook_event_id: str) -> dict:
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.db_models import WebhookEvent, ShopifyStore
    from app.services.normalization import normalize_customer, normalize_order
    from app.services.bulk_sync import BulkSyncService

    async with AsyncSessionLocal() as db:
        # Fetch event
        event = await db.get(WebhookEvent, uuid.UUID(webhook_event_id))
        if not event:
            logger.error("WebhookEvent %s not found", webhook_event_id)
            return {"status": "not_found"}

        if event.status == "processed":
            return {"status": "already_processed"}

        event.attempts += 1

        try:
            store = await db.get(ShopifyStore, event.store_id)
            if not store:
                event.status = "skipped"
                event.error_message = "Store not found"
                await db.commit()
                return {"status": "skipped"}

            topic = event.topic
            payload = event.payload

            if topic in ("orders/create", "orders/updated"):
                await _handle_order_webhook(db, store, payload)
            elif topic in ("customers/create", "customers/update"):
                await _handle_customer_webhook(db, store, payload)
            elif topic == "app/uninstalled":
                await _handle_uninstall(db, store)
            else:
                logger.warning("No handler for topic: %s", topic)

            event.status = "processed"
            event.processed_at = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "processed", "topic": topic}

        except Exception as exc:
            event.status = "failed"
            event.error_message = str(exc)[:500]
            await db.commit()
            raise  # re-raise so Celery can retry


async def _handle_order_webhook(db, store, payload: dict) -> None:
    from app.services.normalization import normalize_order
    from app.services.bulk_sync import BulkSyncService

    norm = normalize_order(payload, source="rest")
    svc = BulkSyncService(db, store)

    # Upsert customer first if present
    if norm.customer and not norm.is_guest_order:
        await svc._upsert_customers([norm.customer])

    await svc._upsert_orders([norm])


async def _handle_customer_webhook(db, store, payload: dict) -> None:
    from app.services.normalization import normalize_customer
    from app.services.bulk_sync import BulkSyncService

    norm = normalize_customer(payload, source="rest")
    svc = BulkSyncService(db, store)
    await svc._upsert_customers([norm])


async def _handle_uninstall(db, store) -> None:
    from datetime import datetime, timezone

    store.deactivated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("Store %s marked as uninstalled", store.shop_domain)


# ---------------------------------------------------------------------------
# Task: Register webhooks for a store
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="app.workers.tasks.register_webhooks_task",
)
def register_webhooks_task(self: Task, store_id: str) -> dict:
    return _run_async(_register_webhooks_async(store_id))


async def _register_webhooks_async(store_id: str) -> dict:
    from app.database import AsyncSessionLocal
    from app.models.db_models import ShopifyStore
    from app.services.shopify_client import ShopifyClient
    from app.config import get_settings

    settings = get_settings()
    async with AsyncSessionLocal() as db:
        store = await db.get(ShopifyStore, uuid.UUID(store_id))
        if not store:
            return {"status": "store_not_found"}

        async with ShopifyClient(store.shop_domain, store.access_token) as client:
            results = await client.register_webhooks(settings.APP_BASE_URL)

    logger.info("Registered %d webhooks for %s", len(results), store.shop_domain)
    return {"status": "ok", "registered": len(results)}


# ---------------------------------------------------------------------------
# Task: Trigger initial bulk sync after OAuth
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name="app.workers.tasks.trigger_initial_sync_task",
)
def trigger_initial_sync_task(self: Task, store_id: str) -> dict:
    """Queue a full bulk sync immediately after a store connects."""
    run_bulk_sync_task.delay(store_id, "all", None)
    return {"status": "queued"}


# ---------------------------------------------------------------------------
# Task: Run bulk (initial) sync
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    name="app.workers.tasks.run_bulk_sync_task",
    time_limit=7200,   # 2 hour hard limit
    soft_time_limit=6900,
)
def run_bulk_sync_task(
    self: Task,
    store_id: str,
    entity: str = "all",
    sync_log_id: str | None = None,
) -> dict:
    return _run_async(
        _run_bulk_sync_async(
            store_id,
            entity,
            uuid.UUID(sync_log_id) if sync_log_id else None,
        )
    )


async def _run_bulk_sync_async(
    store_id: str,
    entity: str,
    sync_log_id: uuid.UUID | None,
) -> dict:
    from app.config import get_settings
    from app.models.db_models import ShopifyStore
    from app.services.bulk_sync import BulkSyncService
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    settings = get_settings()
    engine = create_async_engine(settings.async_database_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with SessionLocal() as db:
            store = await db.get(ShopifyStore, uuid.UUID(store_id))
            if not store:
                return {"status": "store_not_found"}

            svc = BulkSyncService(db, store)
            log = await svc.run(entity=entity, sync_log_id=sync_log_id)
            await db.commit()
    finally:
        await engine.dispose()

    return {
        "status": log.status,
        "sync_log_id": str(log.id),
        "records_upserted": log.records_upserted,
    }


# ---------------------------------------------------------------------------
# Task: Incremental sync for one store
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    name="app.workers.tasks.run_incremental_sync_task",
    time_limit=3600,
)
def run_incremental_sync_task(
    self: Task,
    store_id: str,
    entity: str = "all",
    sync_log_id: str | None = None,
) -> dict:
    return _run_async(
        _run_incremental_sync_async(
            store_id,
            entity,
            uuid.UUID(sync_log_id) if sync_log_id else None,
        )
    )


async def _run_incremental_sync_async(
    store_id: str,
    entity: str,
    sync_log_id: uuid.UUID | None,
) -> dict:
    """
    Incremental REST-based sync using updated_at_min cursor.
    Falls back to bulk if no cursor is found.
    """
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.db_models import ShopifyStore, SyncLog, Customer, Order
    from app.services.shopify_client import ShopifyClient
    from app.services.normalization import normalize_customer, normalize_order
    from app.services.bulk_sync import BulkSyncService

    async with AsyncSessionLocal() as db:
        store = await db.get(ShopifyStore, uuid.UUID(store_id))
        if not store:
            return {"status": "store_not_found"}

        # Find cursor
        log = None
        if sync_log_id:
            log = await db.get(SyncLog, sync_log_id)

        cursor = log.cursor_value if log else None
        cursor_str = cursor.isoformat() if cursor else None

        total_customers = 0
        total_orders = 0
        svc = BulkSyncService(db, store)

        async with ShopifyClient(store.shop_domain, store.access_token) as client:
            if entity in ("all", "customers"):
                async for page in client.paginate_customers(updated_at_min=cursor_str):
                    norms = [normalize_customer(c, source="rest") for c in page]
                    total_customers += await svc._upsert_customers(norms)

            if entity in ("all", "orders"):
                async for page in client.paginate_orders(updated_at_min=cursor_str):
                    norms = [normalize_order(o, source="rest") for o in page]
                    total_orders += await svc._upsert_orders(norms)

        # Update sync log
        if log:
            log.status = "completed"
            log.records_upserted = total_customers + total_orders
            log.cursor_value = datetime.now(timezone.utc)
            log.completed_at = datetime.now(timezone.utc)

        await db.commit()

    return {
        "status": "completed",
        "customers_synced": total_customers,
        "orders_synced": total_orders,
    }


# ---------------------------------------------------------------------------
# Beat task: trigger incremental sync for ALL active stores
# ---------------------------------------------------------------------------

@celery_app.task(name="app.workers.tasks.incremental_sync_all_stores_task")
def incremental_sync_all_stores_task() -> dict:
    return _run_async(_incremental_sync_all_stores_async())


async def _incremental_sync_all_stores_async() -> dict:
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.db_models import ShopifyStore

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ShopifyStore).where(ShopifyStore.deactivated_at.is_(None))
        )
        stores = result.scalars().all()

    for store in stores:
        run_incremental_sync_task.delay(str(store.id), "all")

    logger.info("Queued incremental sync for %d stores", len(stores))
    return {"queued": len(stores)}
