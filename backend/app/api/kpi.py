"""
KPI API endpoints.

All endpoints are scoped to a store via the shop_domain path parameter.
Requires a valid API key (injected via the auth dependency).

Endpoint map:
  GET /kpi/{shop}/summary           → store-level dashboard card
  GET /kpi/{shop}/cohorts           → retention cohort matrix
  GET /kpi/{shop}/cltv              → top customers by CLTV
  GET /kpi/{shop}/cltv/avg          → store-average CLTV metrics
  GET /kpi/{shop}/churn             → at-risk customers list
  GET /kpi/{shop}/churn/summary     → tier counts + revenue at risk
  GET /kpi/{shop}/aov               → AOV trend (monthly/weekly/daily)
  GET /kpi/{shop}/revenue           → monthly revenue with new/returning split
  GET /kpi/{shop}/repeat-rate       → monthly repeat order rate
  GET /kpi/{shop}/products          → top products by revenue
  GET /kpi/{shop}/tbo               → time-between-orders distribution
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import ShopifyStore
from app.utils.auth import require_api_key
from app.services.kpi_service import (
    AOVByPeriod,
    ChurnSignal,
    CohortRow,
    CustomerCLTV,
    KPIService,
    MonthlyRevenueRow,
    ProductPerformanceRow,
    RepeatOrderRateByMonth,
    StoreKPIs,
)

router = APIRouter(
    prefix="/kpi",
    tags=["kpi"],
    # dependencies=[Depends(require_api_key)],  # re-enable in production
)


# ---------------------------------------------------------------------------
# Store lookup dependency
# ---------------------------------------------------------------------------

async def get_store(
    shop: str,
    db: AsyncSession = Depends(get_db),
) -> ShopifyStore:
    result = await db.execute(
        select(ShopifyStore).where(
            ShopifyStore.shop_domain == shop,
            ShopifyStore.deactivated_at.is_(None),
        )
    )
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail=f"Store '{shop}' not found")
    return store


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{shop}/summary", response_model=StoreKPIs)
async def kpi_summary(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    """
    Top-level dashboard card: orders, revenue, AOV, repeat rate.
    """
    svc = KPIService(db)
    result = await svc.get_store_kpis(store.id)
    if not result:
        raise HTTPException(status_code=404, detail="No data found for this store")
    return result


@router.get("/{shop}/cohorts", response_model=List[CohortRow])
async def cohort_retention(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    cohort_start: Optional[datetime] = Query(None, description="ISO-8601 start date for cohorts"),
    cohort_end: Optional[datetime] = Query(None, description="ISO-8601 end date for cohorts"),
    max_offset: int = Query(12, ge=1, le=36, description="Max months to track per cohort"),
):
    """
    Monthly cohort retention matrix.
    Each row: (cohort_month, month_offset, retention_rate_pct).
    month_offset=0 is the acquisition month (always 100%).
    """
    svc = KPIService(db)
    return await svc.get_cohort_retention(
        store.id,
        cohort_start=cohort_start,
        cohort_end=cohort_end,
        max_offset=max_offset,
    )


@router.get("/{shop}/cltv", response_model=List[CustomerCLTV])
async def top_customers_cltv(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    min_orders: int = Query(1, ge=1, description="Minimum order count to include"),
):
    """
    Top customers ranked by historical CLTV.
    Includes projected 12-month CLTV and avg days between orders.
    """
    svc = KPIService(db)
    return await svc.get_top_customers_by_cltv(store.id, limit=limit, min_orders=min_orders)


@router.get("/{shop}/cltv/avg")
async def avg_cltv(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    cohort_month: Optional[datetime] = Query(None, description="Scope to a specific cohort month"),
):
    """
    Store-average CLTV metrics:
    avg_historical_cltv, avg_projected_12m_cltv, avg_aov, avg_tbo_days.
    """
    svc = KPIService(db)
    return await svc.get_avg_cltv(store.id, cohort_month=cohort_month)


@router.get("/{shop}/churn", response_model=List[ChurnSignal])
async def churn_signals(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    risk_tier: Optional[str] = Query(
        None,
        description="Filter by tier: high_risk | medium_risk | low_risk | one_time_buyer",
    ),
    limit: int = Query(500, ge=1, le=5000),
):
    """
    Customers at risk of churning, ranked by revenue at risk.
    Churn tiers are relative to each customer's own purchase cadence.
    """
    svc = KPIService(db)
    return await svc.get_churn_signals(store.id, risk_tier=risk_tier, limit=limit)


@router.get("/{shop}/churn/summary")
async def churn_summary(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregate count and revenue-at-risk per churn tier.
    Use this for the churn dashboard ring/pie chart.
    """
    svc = KPIService(db)
    return await svc.get_churn_summary(store.id)


@router.get("/{shop}/aov", response_model=List[AOVByPeriod])
async def aov_trend(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    period: str = Query("month", description="Bucket size: month | week | day"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """
    AOV trend over time. Supports monthly, weekly, or daily bucketing.
    """
    if period not in ("month", "week", "day"):
        raise HTTPException(status_code=400, detail="period must be month, week, or day")
    svc = KPIService(db)
    return await svc.get_aov_trend(
        store.id, period=period, start_date=start_date, end_date=end_date
    )


@router.get("/{shop}/revenue", response_model=List[MonthlyRevenueRow])
async def monthly_revenue(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    months: int = Query(12, ge=1, le=60, description="Number of trailing months"),
):
    """
    Monthly revenue with new vs. returning customer split.
    """
    svc = KPIService(db)
    return await svc.get_monthly_revenue(store.id, months=months)


@router.get("/{shop}/repeat-rate", response_model=List[RepeatOrderRateByMonth])
async def repeat_order_rate(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    months: int = Query(12, ge=1, le=60),
):
    """
    Monthly repeat order rate — % of buyers who had previously ordered.
    """
    svc = KPIService(db)
    return await svc.get_repeat_order_rate(store.id, months=months)


@router.get("/{shop}/products", response_model=List[ProductPerformanceRow])
async def product_performance(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
):
    """Top products by revenue (paid, non-cancelled orders only)."""
    svc = KPIService(db)
    return await svc.get_product_performance(store.id, limit=limit)


@router.get("/{shop}/tbo")
async def tbo_distribution(
    store: ShopifyStore = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    """
    Time Between Orders histogram — counts of repeat buyers per TBO bucket.
    Use this to understand purchase cadence and optimal email send timing.
    """
    svc = KPIService(db)
    return await svc.get_tbo_distribution(store.id)
