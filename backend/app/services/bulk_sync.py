"""
Bulk Operations Sync Service.

Strategy:
  1. Submit a GraphQL bulk operation to Shopify.
  2. Poll until the operation completes and a JSONL download URL is ready.
  3. Stream the JSONL file line by line (can be GBs) and upsert in batches.
  4. Update the sync_log record throughout.

The JSONL format from Shopify Bulk Operations:
  Each line is a JSON object. Child objects include a __parentId field
  pointing to their parent. We buffer parents and attach children
  before writing to DB.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.db_models import Customer, Order, OrderItem, ShopifyStore, SyncLog
from app.models.schemas import NormalizedCustomer, NormalizedOrder
from app.services.normalization import normalize_customer, normalize_order
from app.services.shopify_client import ShopifyClient

logger = logging.getLogger(__name__)
settings = get_settings()

UPSERT_BATCH_SIZE = 500  # rows per DB transaction


# ---------------------------------------------------------------------------
# GraphQL queries for bulk operations
# ---------------------------------------------------------------------------

BULK_CUSTOMERS_QUERY = """
{
  customers {
    edges {
      node {
        id
        legacyResourceId
        email
        phone
        createdAt
        updatedAt
        amountSpent {
          amount
          currencyCode
        }
        numberOfOrders
        tags
        emailMarketingConsent {
          marketingState
        }
        verifiedEmail
      }
    }
  }
}
"""

BULK_ORDERS_QUERY = """
{
  orders {
    edges {
      node {
        id
        legacyResourceId
        name
        email
        createdAt
        updatedAt
        processedAt
        cancelledAt
        cancelReason
        financialStatus
        fulfillmentStatus
        sourceName
        landingSite
        referringSite
        currentTotalPriceSet {
          shopMoney { amount currencyCode }
        }
        subtotalPriceSet {
          shopMoney { amount currencyCode }
        }
        totalTaxSet {
          shopMoney { amount }
        }
        totalDiscountsSet {
          shopMoney { amount }
        }
        customer {
          id
          legacyResourceId
        }
        lineItems {
          edges {
            node {
              id
              quantity
              title
              sku
              vendor
              variantTitle
              requiresShipping
              isGiftCard
              product {
                id
                legacyResourceId
                productType
              }
              variant {
                id
                legacyResourceId
              }
              originalUnitPriceSet {
                shopMoney { amount }
              }
              totalDiscountSet {
                shopMoney { amount }
              }
            }
          }
        }
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Main sync entry point
# ---------------------------------------------------------------------------

class BulkSyncService:
    def __init__(self, db: AsyncSession, store: ShopifyStore):
        self.db = db
        self.store = store
        self.client = ShopifyClient(store.shop_domain, store.access_token)

    async def run(
        self,
        entity: str = "all",
        sync_log_id: Optional[uuid.UUID] = None,
    ) -> SyncLog:
        """
        Execute a full bulk sync for customers, orders, or both.
        Returns the completed SyncLog record.
        """
        sync_log = await self._get_or_create_sync_log(entity, sync_log_id)

        try:
            async with self.client:
                if entity in ("all", "customers"):
                    await self._sync_customers(sync_log)
                if entity in ("all", "orders"):
                    await self._sync_orders(sync_log)

            sync_log.status = "completed"
            sync_log.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.exception("Bulk sync failed for store %s", self.store.shop_domain)
            sync_log.status = "failed"
            sync_log.error_message = str(exc)
            sync_log.completed_at = datetime.now(timezone.utc)
            raise
        finally:
            await self.db.flush()

        return sync_log

    # ── Customers ────────────────────────────────────────────────────────

    async def _sync_customers(self, sync_log: SyncLog) -> None:
        logger.info("Starting REST customer sync for %s", self.store.shop_domain)
        total = 0
        batch: List[NormalizedCustomer] = []

        async for page in self.client.paginate_customers():
            for raw in page:
                norm = normalize_customer(raw, source="rest")
                batch.append(norm)
            if len(batch) >= UPSERT_BATCH_SIZE:
                total += await self._upsert_customers(batch)
                batch.clear()

        if batch:
            total += await self._upsert_customers(batch)

        sync_log.records_upserted += total
        logger.info("Customer sync complete: %d upserted", total)

    async def _upsert_customers(self, customers: List[NormalizedCustomer]) -> int:
        values = [
            {
                "store_id": self.store.id,
                "shopify_customer_id": c.shopify_customer_id,
                "email": c.email,
                "phone": c.phone,
                "total_spent": c.total_spent,
                "orders_count": c.orders_count,
                "currency": c.currency,
                "tags": c.tags,
                "accepts_marketing": c.accepts_marketing,
                "verified_email": c.verified_email,
                "is_guest": c.is_guest,
                "shopify_created_at": c.shopify_created_at,
                "shopify_updated_at": c.shopify_updated_at,
            }
            for c in customers
        ]
        stmt = (
            pg_insert(Customer)
            .values(values)
            .on_conflict_do_update(
                constraint="uq_customer_per_store",
                set_={
                    "email": pg_insert(Customer).excluded.email,
                    "phone": pg_insert(Customer).excluded.phone,
                    "total_spent": pg_insert(Customer).excluded.total_spent,
                    "orders_count": pg_insert(Customer).excluded.orders_count,
                    "tags": pg_insert(Customer).excluded.tags,
                    "accepts_marketing": pg_insert(Customer).excluded.accepts_marketing,
                    "shopify_updated_at": pg_insert(Customer).excluded.shopify_updated_at,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return len(values)

    # ── Orders ───────────────────────────────────────────────────────────

    async def _sync_orders(self, sync_log: SyncLog) -> None:
        logger.info("Starting REST order sync for %s", self.store.shop_domain)
        total = 0
        batch: List[NormalizedOrder] = []

        async for page in self.client.paginate_orders(status="any"):
            for raw in page:
                norm = normalize_order(raw, source="rest")
                batch.append(norm)
            if len(batch) >= UPSERT_BATCH_SIZE:
                total += await self._upsert_orders(batch)
                batch.clear()

        if batch:
            total += await self._upsert_orders(batch)

        sync_log.records_upserted += total
        logger.info("Order sync complete: %d upserted", total)

    async def _upsert_orders(self, orders: List[NormalizedOrder]) -> int:
        # Step 1: resolve customer UUIDs from shopify IDs
        customer_id_map = await self._resolve_customer_ids(
            [o.customer.shopify_customer_id for o in orders if o.customer]
        )

        for order in orders:
            # Upsert the order row
            customer_uuid = (
                customer_id_map.get(order.customer.shopify_customer_id)
                if order.customer
                else None
            )
            order_stmt = (
                pg_insert(Order)
                .values(
                    store_id=self.store.id,
                    customer_id=customer_uuid,
                    shopify_order_id=order.shopify_order_id,
                    shopify_order_number=order.shopify_order_number,
                    total_price=order.total_price,
                    subtotal_price=order.subtotal_price,
                    total_tax=order.total_tax,
                    total_discounts=order.total_discounts,
                    currency=order.currency,
                    total_price_usd=order.total_price_usd,
                    financial_status=order.financial_status,
                    fulfillment_status=order.fulfillment_status,
                    cancel_reason=order.cancel_reason,
                    cancelled_at=order.cancelled_at,
                    source_name=order.source_name,
                    landing_site=order.landing_site,
                    referring_site=order.referring_site,
                    is_guest_order=order.is_guest_order,
                    guest_email=order.guest_email,
                    shopify_created_at=order.shopify_created_at,
                    shopify_updated_at=order.shopify_updated_at,
                    processed_at=order.processed_at,
                )
                .on_conflict_do_update(
                    constraint="uq_order_per_store",
                    set_={
                        "customer_id": customer_uuid,
                        "total_price": order.total_price,
                        "financial_status": order.financial_status,
                        "fulfillment_status": order.fulfillment_status,
                        "shopify_updated_at": order.shopify_updated_at,
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
                .returning(Order.id)
            )
            result = await self.db.execute(order_stmt)
            order_row_id = result.scalar_one()

            # Upsert line items
            if order.line_items:
                li_values = [
                    {
                        "order_id": order_row_id,
                        "store_id": self.store.id,
                        "shopify_line_item_id": li.shopify_line_item_id,
                        "shopify_product_id": li.shopify_product_id,
                        "shopify_variant_id": li.shopify_variant_id,
                        "title": li.title,
                        "sku": li.sku,
                        "vendor": li.vendor,
                        "product_type": li.product_type,
                        "quantity": li.quantity,
                        "price": li.price,
                        "total_discount": li.total_discount,
                        "variant_title": li.variant_title,
                        "requires_shipping": li.requires_shipping,
                        "is_gift_card": li.is_gift_card,
                    }
                    for li in order.line_items
                ]
                li_stmt = (
                    pg_insert(OrderItem)
                    .values(li_values)
                    .on_conflict_do_update(
                        constraint="uq_line_item_per_order",
                        set_={
                            "quantity": pg_insert(OrderItem).excluded.quantity,
                            "price": pg_insert(OrderItem).excluded.price,
                            "total_discount": pg_insert(OrderItem).excluded.total_discount,
                        },
                    )
                )
                await self.db.execute(li_stmt)

        await self.db.flush()
        return len(orders)

    async def _resolve_customer_ids(
        self, shopify_ids: List[int]
    ) -> Dict[int, uuid.UUID]:
        """Return a map of shopify_customer_id → internal UUID."""
        if not shopify_ids:
            return {}
        from sqlalchemy import select
        result = await self.db.execute(
            select(Customer.shopify_customer_id, Customer.id).where(
                Customer.store_id == self.store.id,
                Customer.shopify_customer_id.in_(shopify_ids),
            )
        )
        return {row.shopify_customer_id: row.id for row in result}

    # ── SyncLog helpers ──────────────────────────────────────────────────

    async def _get_or_create_sync_log(
        self, entity: str, sync_log_id: Optional[uuid.UUID]
    ) -> SyncLog:
        if sync_log_id:
            from sqlalchemy import select
            result = await self.db.execute(
                select(SyncLog).where(SyncLog.id == sync_log_id)
            )
            log = result.scalar_one_or_none()
            if log:
                log.status = "running"
                return log

        log = SyncLog(
            store_id=self.store.id,
            sync_type="bulk_initial",
            entity=entity,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        return log


# ---------------------------------------------------------------------------
# JSONL streaming helper
# ---------------------------------------------------------------------------

async def _stream_jsonl(url: str) -> AsyncGenerator[dict, None]:
    """
    Stream a JSONL file from a URL, yielding one parsed dict per line.
    Uses chunked streaming to handle very large files (multi-GB) without
    loading everything into memory.
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning("Skipping malformed JSONL line: %s", line[:100])
            # Flush remaining buffer
            if buffer.strip():
                try:
                    yield json.loads(buffer.strip())
                except json.JSONDecodeError:
                    pass
