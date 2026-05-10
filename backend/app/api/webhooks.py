"""
Webhook receiver endpoints.

Security: Every request is verified using HMAC-SHA256 before any
processing takes place. The raw body is read before Pydantic parsing
because HMAC must be computed on the exact bytes Shopify sent.

Idempotency: The shopify_event_id (X-Shopify-Event-Id header) is
stored in webhook_events. Duplicate deliveries are silently skipped.

Processing: Webhooks are acknowledged immediately (HTTP 200) and
processed asynchronously by a Celery task. This prevents Shopify
from retrying due to slow processing.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db_models import ShopifyStore, WebhookEvent
from app.utils.crypto import verify_webhook_signature

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

SUPPORTED_TOPICS = {
    "orders_create",
    "orders_updated",
    "customers_create",
    "customers_update",
    "app_uninstalled",
}


# ---------------------------------------------------------------------------
# Generic webhook receiver — one endpoint per topic
# ---------------------------------------------------------------------------

@router.post("/{topic}")
async def receive_webhook(
    topic: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_shopify_hmac_sha256: str = Header(...),
    x_shopify_shop_domain: str = Header(...),
    x_shopify_topic: str = Header(...),
    x_shopify_event_id: str = Header(default=""),
):
    """
    Unified webhook receiver.
    URL path topic: orders_create, orders_updated, customers_create, etc.
    """
    if topic not in SUPPORTED_TOPICS:
        raise HTTPException(status_code=404, detail=f"Unsupported webhook topic: {topic}")

    # ── 1. Read raw body for HMAC verification ────────────────────────────
    raw_body = await request.body()

    # ── 2. Verify HMAC ────────────────────────────────────────────────────
    if not verify_webhook_signature(raw_body, x_shopify_hmac_sha256, settings.SHOPIFY_API_SECRET):
        logger.warning(
            "Webhook HMAC verification failed for shop=%s topic=%s event_id=%s",
            x_shopify_shop_domain,
            x_shopify_topic,
            x_shopify_event_id,
        )
        raise HTTPException(status_code=401, detail="HMAC verification failed")

    # ── 3. Look up store ──────────────────────────────────────────────────
    store = await _get_store(db, x_shopify_shop_domain)
    if not store:
        # Store may have been uninstalled. Acknowledge but don't process.
        logger.warning("Received webhook for unknown shop: %s", x_shopify_shop_domain)
        return {"status": "ignored", "reason": "unknown_shop"}

    # ── 4. Idempotency check ──────────────────────────────────────────────
    if x_shopify_event_id:
        existing = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.store_id == store.id,
                WebhookEvent.shopify_event_id == x_shopify_event_id,
            )
        )
        if existing.scalar_one_or_none():
            logger.debug("Duplicate webhook event %s — skipping", x_shopify_event_id)
            return {"status": "ok", "duplicate": True}

    # ── 5. Parse JSON payload ─────────────────────────────────────────────
    try:
        import json
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # ── 6. Persist to webhook_events (dead-letter queue) ──────────────────
    event = await _persist_webhook_event(
        db,
        store_id=store.id,
        topic=x_shopify_topic,
        event_id=x_shopify_event_id,
        payload=payload,
    )

    # ── 7. Dispatch to Celery for async processing ─────────────────────────
    from app.workers.tasks import process_webhook_task

    process_webhook_task.delay(str(event.id))

    # Always return 200 quickly to prevent Shopify retries
    return {"status": "ok", "event_id": str(event.id)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_store(db: AsyncSession, shop_domain: str) -> ShopifyStore | None:
    result = await db.execute(
        select(ShopifyStore).where(
            ShopifyStore.shop_domain == shop_domain,
            ShopifyStore.deactivated_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _persist_webhook_event(
    db: AsyncSession,
    store_id,
    topic: str,
    event_id: str,
    payload: dict,
) -> WebhookEvent:
    stmt = (
        pg_insert(WebhookEvent)
        .values(
            store_id=store_id,
            topic=topic,
            shopify_event_id=event_id or None,
            payload=payload,
            status="pending",
            received_at=datetime.now(timezone.utc),
        )
        .on_conflict_do_nothing(constraint="uq_shopify_event")
        .returning(WebhookEvent.id)
    )
    result = await db.execute(stmt)
    row = result.fetchone()
    if row is None:
        # Conflict — already existed (race condition)
        existing = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.store_id == store_id,
                WebhookEvent.shopify_event_id == event_id,
            )
        )
        return existing.scalar_one()

    await db.flush()
    event = await db.get(WebhookEvent, row[0])
    return event
