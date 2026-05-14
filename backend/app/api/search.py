"""
Global search endpoint — searches across customers, products, and orders.
Returns top 5 results per category.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, cast, Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Customer, Order, OrderItem, ShopifyStore
from app.utils.jwt import TokenPayload, get_current_user

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1, max_length=100),
    current: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search across customers, products and orders for a given store."""
    if not q or not q.strip():
        return {"customers": [], "products": [], "orders": []}

    term = f"%{q.strip().lower()}%"

    # ── Resolve store UUID ────────────────────────────────────────────────
    store_result = await db.execute(
        select(ShopifyStore.id).where(ShopifyStore.shop_domain == current.shop_domain)
    )
    store_id = store_result.scalar_one_or_none()
    if not store_id:
        return {"customers": [], "products": [], "orders": []}

    # ── Search customers by email ─────────────────────────────────────────
    cust_result = await db.execute(
        select(Customer.id, Customer.email, Customer.total_spent, Customer.orders_count)
        .where(
            Customer.store_id == store_id,
            Customer.email.ilike(term),
        )
        .limit(5)
    )
    customers = [
        {
            "id":           str(r.id),
            "email":        r.email,
            "total_spent":  float(r.total_spent or 0),
            "orders_count": r.orders_count,
            "type":         "customer",
        }
        for r in cust_result
    ]

    # ── Search products by title ──────────────────────────────────────────
    prod_result = await db.execute(
        select(
            OrderItem.shopify_product_id,
            OrderItem.title,
            OrderItem.vendor,
        )
        .where(
            OrderItem.store_id == store_id,
            OrderItem.title.ilike(term),
        )
        .distinct(OrderItem.shopify_product_id)
        .limit(5)
    )
    products = [
        {
            "id":     str(r.shopify_product_id),
            "title":  r.title,
            "vendor": r.vendor,
            "type":   "product",
        }
        for r in prod_result
    ]

    # ── Search orders by order number ─────────────────────────────────────
    order_result = await db.execute(
        select(Order.id, Order.shopify_order_number, Order.total_price, Order.financial_status, Order.shopify_created_at)
        .where(
            Order.store_id == store_id,
            Order.shopify_order_number.ilike(term),
        )
        .limit(5)
    )
    orders = [
        {
            "id":               str(r.id),
            "order_number":     r.shopify_order_number,
            "total_price":      float(r.total_price or 0),
            "financial_status": r.financial_status,
            "created_at":       r.shopify_created_at,
            "type":             "order",
        }
        for r in order_result
    ]

    return {
        "query":     q,
        "customers": customers,
        "products":  products,
        "orders":    orders,
    }
