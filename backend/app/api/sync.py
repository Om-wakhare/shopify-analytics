"""
Manual sync endpoints — used to trigger initial or incremental syncs
from the admin UI or via an internal cron job.
"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import ShopifyStore, SyncLog
from app.models.schemas import BulkSyncRequest, BulkSyncResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/bulk", response_model=BulkSyncResponse)
async def trigger_bulk_sync(
    body: BulkSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Kick off a full historical sync using Shopify's Bulk Operations API.
    The actual work runs in a Celery task; this endpoint returns immediately.
    """
    store = await _get_active_store(db, body.shop_domain)

    # Create a pending SyncLog so the caller can track progress
    sync_log = SyncLog(
        store_id=store.id,
        sync_type="bulk_initial",
        entity=body.entity,
        status="pending",
    )
    db.add(sync_log)
    await db.flush()

    from app.workers.tasks import run_bulk_sync_task

    run_bulk_sync_task.delay(str(store.id), body.entity, str(sync_log.id))

    return BulkSyncResponse(
        sync_log_id=sync_log.id,
        message=f"Bulk sync for '{body.entity}' queued. Track via sync_log_id.",
    )


@router.post("/incremental/{shop_domain}", response_model=BulkSyncResponse)
async def trigger_incremental_sync(
    shop_domain: str,
    entity: str = "all",
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger an incremental sync using the cursor stored in the last SyncLog.
    Falls back to full bulk sync if no prior cursor exists.
    """
    store = await _get_active_store(db, shop_domain)

    # Find the last successful sync cursor
    result = await db.execute(
        select(SyncLog)
        .where(
            SyncLog.store_id == store.id,
            SyncLog.status == "completed",
            SyncLog.cursor_value.is_not(None),
        )
        .order_by(SyncLog.completed_at.desc())
        .limit(1)
    )
    last_log = result.scalar_one_or_none()
    cursor = last_log.cursor_value if last_log else None

    sync_log = SyncLog(
        store_id=store.id,
        sync_type="incremental" if cursor else "bulk_initial",
        entity=entity,
        status="pending",
        cursor_value=cursor,
    )
    db.add(sync_log)
    await db.flush()

    from app.workers.tasks import run_incremental_sync_task

    run_incremental_sync_task.delay(str(store.id), entity, str(sync_log.id))

    return BulkSyncResponse(
        sync_log_id=sync_log.id,
        message=f"Incremental sync queued from cursor={cursor}.",
    )


@router.get("/status/{sync_log_id}")
async def get_sync_status(
    sync_log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the current status of a sync job."""
    log = await db.get(SyncLog, sync_log_id)
    if not log:
        raise HTTPException(status_code=404, detail="SyncLog not found")
    return {
        "id": str(log.id),
        "sync_type": log.sync_type,
        "entity": log.entity,
        "status": log.status,
        "records_upserted": log.records_upserted,
        "error_message": log.error_message,
        "started_at": log.started_at,
        "completed_at": log.completed_at,
    }


async def _get_active_store(db: AsyncSession, shop_domain: str) -> ShopifyStore:
    result = await db.execute(
        select(ShopifyStore).where(
            ShopifyStore.shop_domain == shop_domain,
            ShopifyStore.deactivated_at.is_(None),
        )
    )
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail=f"Store '{shop_domain}' not found or inactive")
    return store
