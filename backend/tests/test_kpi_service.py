"""
Tests for KPI service — uses real DB via the db fixture.
Seeds minimal order/customer data and verifies KPI calculations.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.db_models import Customer, Order, OrderItem
from app.services.kpi_service import KPIService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(days_ago: int = 0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


async def _seed_paid_order(
    db,
    store_id,
    customer_id,
    total_usd: float,
    days_ago: int = 0,
) -> Order:
    o = Order(
        store_id=store_id,
        customer_id=customer_id,
        shopify_order_id=abs(hash((customer_id, total_usd, days_ago))) % 10**9,
        total_price=total_usd,
        total_price_usd=total_usd,
        currency="USD",
        financial_status="paid",
        shopify_created_at=_utc(days_ago),
    )
    db.add(o)
    await db.flush()
    return o


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_store_kpis_empty(db, store):
    """No orders → no KPI row."""
    svc = KPIService(db)
    result = await svc.get_store_kpis(store.id)
    assert result is None


@pytest.mark.asyncio
async def test_store_kpis_basic(db, store, customer):
    """Two orders from the same customer."""
    await _seed_paid_order(db, store.id, customer.id, 100.00, days_ago=60)
    await _seed_paid_order(db, store.id, customer.id, 50.00, days_ago=30)

    svc = KPIService(db)
    kpis = await svc.get_store_kpis(store.id)

    assert kpis is not None
    assert kpis.total_orders == 2
    assert kpis.total_customers == 1
    assert kpis.total_revenue_usd == Decimal("150.00")
    assert kpis.aov_usd == Decimal("75.00")
    # One customer with 2 orders → repeat customer
    assert kpis.repeat_customers == 1
    assert kpis.repeat_order_rate_pct == Decimal("100.00")


@pytest.mark.asyncio
async def test_repeat_order_rate_mixed(db, store):
    """Two customers: one repeat, one single purchase."""
    c1 = Customer(store_id=store.id, shopify_customer_id=2001,
                  email="repeat@ex.com", total_spent=200, orders_count=2, currency="USD")
    c2 = Customer(store_id=store.id, shopify_customer_id=2002,
                  email="once@ex.com", total_spent=50, orders_count=1, currency="USD")
    db.add_all([c1, c2])
    await db.flush()

    await _seed_paid_order(db, store.id, c1.id, 100.00, days_ago=90)
    await _seed_paid_order(db, store.id, c1.id, 100.00, days_ago=45)
    await _seed_paid_order(db, store.id, c2.id, 50.00, days_ago=30)

    svc = KPIService(db)
    kpis = await svc.get_store_kpis(store.id)

    assert kpis.total_customers == 2
    assert kpis.repeat_customers == 1
    assert kpis.repeat_order_rate_pct == Decimal("50.00")


@pytest.mark.asyncio
async def test_monthly_revenue_returns_data(db, store, customer):
    """Monthly revenue should return at least 1 row when orders exist."""
    await _seed_paid_order(db, store.id, customer.id, 120.00, days_ago=15)

    svc = KPIService(db)
    rows = await svc.get_monthly_revenue(store.id, months=3)

    assert len(rows) >= 1
    assert rows[-1].revenue_usd == Decimal("120.00")
    assert rows[-1].order_count == 1


@pytest.mark.asyncio
async def test_aov_trend_single_bucket(db, store, customer):
    await _seed_paid_order(db, store.id, customer.id, 200.00, days_ago=10)
    await _seed_paid_order(db, store.id, customer.id, 100.00, days_ago=5)

    svc = KPIService(db)
    rows = await svc.get_aov_trend(store.id, period="month")

    assert len(rows) >= 1
    current_month = rows[-1]
    assert current_month.order_count == 2
    assert current_month.aov_usd == Decimal("150.00")


@pytest.mark.asyncio
async def test_top_customers_by_cltv(db, store):
    """Customers ranked highest-first by revenue."""
    c_high = Customer(store_id=store.id, shopify_customer_id=3001,
                      email="high@ex.com", total_spent=500, orders_count=5, currency="USD")
    c_low = Customer(store_id=store.id, shopify_customer_id=3002,
                     email="low@ex.com", total_spent=50, orders_count=1, currency="USD")
    db.add_all([c_high, c_low])
    await db.flush()

    for _ in range(5):
        await _seed_paid_order(db, store.id, c_high.id, 100.00, days_ago=30)
    await _seed_paid_order(db, store.id, c_low.id, 50.00, days_ago=10)

    svc = KPIService(db)
    rows = await svc.get_top_customers_by_cltv(store.id, limit=10)

    assert len(rows) >= 2
    assert rows[0].historical_cltv_usd >= rows[1].historical_cltv_usd


@pytest.mark.asyncio
async def test_churn_signals_appear_after_inactivity(db, store, customer):
    """Customer with no recent orders should appear in churn signals."""
    # Two orders 120 and 60 days ago → avg TBO = 60 days
    # Last order 60 days ago → 60 days since last order = 1× TBO → low_risk
    await _seed_paid_order(db, store.id, customer.id, 80.00, days_ago=120)
    await _seed_paid_order(db, store.id, customer.id, 80.00, days_ago=60)

    svc = KPIService(db)
    signals = await svc.get_churn_signals(store.id)

    # Should be present (dormant > 30 days)
    customer_ids = [str(s.customer_id) for s in signals]
    assert str(customer.id) in customer_ids


@pytest.mark.asyncio
async def test_tbo_distribution(db, store):
    """TBO distribution returns non-empty when repeat buyers exist."""
    c = Customer(store_id=store.id, shopify_customer_id=4001,
                 email="repeat@tbo.com", total_spent=300, orders_count=3, currency="USD")
    db.add(c)
    await db.flush()

    await _seed_paid_order(db, store.id, c.id, 100.00, days_ago=90)
    await _seed_paid_order(db, store.id, c.id, 100.00, days_ago=45)
    await _seed_paid_order(db, store.id, c.id, 100.00, days_ago=0)

    svc = KPIService(db)
    buckets = await svc.get_tbo_distribution(store.id)

    assert len(buckets) >= 1
    total_customers = sum(b["customer_count"] for b in buckets)
    assert total_customers >= 1
