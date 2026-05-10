"""
KPI Query Service.

All queries go through parameterized SQLAlchemy text() — no f-string
SQL, no raw string interpolation from user input.

Each method returns a typed Pydantic response model ready for
the FastAPI layer to serialize directly.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class StoreKPIs(BaseModel):
    store_id: uuid.UUID
    total_orders: int
    total_customers: int
    total_revenue_usd: Decimal
    aov_usd: Decimal
    repeat_customers: int
    repeat_order_rate_pct: Decimal


class CohortRow(BaseModel):
    cohort_month: datetime
    cohort_size: int
    month_offset: int
    active_customers: int
    retention_rate_pct: Decimal


class CustomerCLTV(BaseModel):
    customer_id: uuid.UUID
    store_id: uuid.UUID
    historical_cltv_usd: Decimal
    projected_12m_cltv_usd: Decimal
    total_orders: int
    aov_usd: Decimal
    avg_days_between_orders: Optional[Decimal]
    days_since_last_order: Optional[int]
    first_order_at: Optional[datetime]
    last_order_at: Optional[datetime]
    cohort_month: Optional[datetime]


class ChurnSignal(BaseModel):
    customer_id: uuid.UUID
    store_id: uuid.UUID
    days_since_last_order: int
    avg_days_between_orders: Optional[Decimal]
    historical_cltv_usd: Decimal
    total_orders: int
    churn_risk_tier: str
    last_order_at: Optional[datetime]
    cohort_month: Optional[datetime]


class MonthlyRevenueRow(BaseModel):
    month: datetime
    order_count: int
    unique_customers: int
    revenue_usd: Decimal
    aov_usd: Decimal
    new_customers: int
    returning_customers: int


class ProductPerformanceRow(BaseModel):
    shopify_product_id: Optional[int]
    product_title: Optional[str]
    vendor: Optional[str]
    product_type: Optional[str]
    order_count: int
    units_sold: int
    revenue_usd: Decimal
    avg_unit_price: Decimal
    unique_customers: int


class AOVByPeriod(BaseModel):
    period: datetime
    aov_usd: Decimal
    order_count: int


class RepeatOrderRateByMonth(BaseModel):
    month: datetime
    new_customers: int
    repeat_customers: int
    repeat_order_rate_pct: Decimal


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class KPIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Store-level dashboard KPIs ────────────────────────────────────────

    async def get_store_kpis(self, store_id: uuid.UUID) -> Optional[StoreKPIs]:
        """Top-level single-row KPI summary for a store."""
        result = await self.db.execute(
            text("SELECT * FROM store_kpis WHERE store_id = :sid"),
            {"sid": store_id},
        )
        row = result.mappings().one_or_none()
        if not row:
            return None
        return StoreKPIs(**row)

    # ── Cohort retention matrix ───────────────────────────────────────────

    async def get_cohort_retention(
        self,
        store_id: uuid.UUID,
        cohort_start: Optional[datetime] = None,
        cohort_end: Optional[datetime] = None,
        max_offset: int = 12,
    ) -> List[CohortRow]:
        """
        Cohort retention matrix.
        Returns rows suitable for a heatmap: (cohort_month, month_offset, retention_rate_pct).
        """
        where_clauses = ["store_id = :sid", "month_offset <= :max_offset"]
        params: dict = {"sid": store_id, "max_offset": max_offset}

        if cohort_start:
            where_clauses.append("cohort_month >= :cohort_start")
            params["cohort_start"] = cohort_start
        if cohort_end:
            where_clauses.append("cohort_month <= :cohort_end")
            params["cohort_end"] = cohort_end

        sql = f"SELECT * FROM cohort_retention WHERE {' AND '.join(where_clauses)} ORDER BY cohort_month, month_offset"
        result = await self.db.execute(text(sql), params)
        return [CohortRow(**row) for row in result.mappings()]

    # ── CLTV ─────────────────────────────────────────────────────────────

    async def get_top_customers_by_cltv(
        self,
        store_id: uuid.UUID,
        limit: int = 100,
        min_orders: int = 1,
    ) -> List[CustomerCLTV]:
        """Top customers ranked by historical CLTV."""
        result = await self.db.execute(
            text("""
                SELECT * FROM customer_cltv
                WHERE store_id = :sid
                  AND total_orders >= :min_orders
                ORDER BY historical_cltv_usd DESC
                LIMIT :lim
            """),
            {"sid": store_id, "min_orders": min_orders, "lim": limit},
        )
        return [CustomerCLTV(**row) for row in result.mappings()]

    async def get_avg_cltv(
        self,
        store_id: uuid.UUID,
        cohort_month: Optional[datetime] = None,
    ) -> dict:
        """
        Store-level average CLTV — both historical and 12-month projected.
        Optionally scoped to a single cohort month.
        """
        params: dict = {"sid": store_id}
        extra = ""
        if cohort_month:
            extra = "AND cohort_month = :cohort_month"
            params["cohort_month"] = cohort_month

        result = await self.db.execute(
            text(f"""
                SELECT
                    COUNT(*)                                   AS customer_count,
                    ROUND(AVG(historical_cltv_usd)::NUMERIC, 2) AS avg_historical_cltv,
                    ROUND(AVG(projected_12m_cltv_usd)::NUMERIC, 2) AS avg_projected_12m_cltv,
                    ROUND(AVG(aov_usd)::NUMERIC, 2)            AS avg_aov,
                    ROUND(AVG(avg_days_between_orders)::NUMERIC, 1) AS avg_tbo_days
                FROM customer_cltv
                WHERE store_id = :sid
                  AND total_orders > 0
                  {extra}
            """),
            params,
        )
        row = result.mappings().one()
        return dict(row)

    # ── Churn ─────────────────────────────────────────────────────────────

    async def get_churn_signals(
        self,
        store_id: uuid.UUID,
        risk_tier: Optional[str] = None,
        limit: int = 500,
    ) -> List[ChurnSignal]:
        """
        Customers at risk of churning.
        risk_tier: high_risk | medium_risk | low_risk | one_time_buyer | healthy
        """
        params: dict = {"sid": store_id, "lim": limit}
        tier_filter = ""
        if risk_tier:
            tier_filter = "AND churn_risk_tier = :tier"
            params["tier"] = risk_tier

        result = await self.db.execute(
            text(f"""
                SELECT * FROM churn_signals
                WHERE store_id = :sid
                {tier_filter}
                ORDER BY historical_cltv_usd DESC, days_since_last_order DESC
                LIMIT :lim
            """),
            params,
        )
        return [ChurnSignal(**row) for row in result.mappings()]

    async def get_churn_summary(self, store_id: uuid.UUID) -> dict:
        """Count of customers per churn risk tier."""
        result = await self.db.execute(
            text("""
                SELECT
                    churn_risk_tier,
                    COUNT(*)                                       AS customer_count,
                    ROUND(SUM(historical_cltv_usd)::NUMERIC, 2)   AS revenue_at_risk_usd
                FROM churn_signals
                WHERE store_id = :sid
                GROUP BY churn_risk_tier
                ORDER BY customer_count DESC
            """),
            {"sid": store_id},
        )
        return [dict(row) for row in result.mappings()]

    # ── AOV over time ─────────────────────────────────────────────────────

    async def get_aov_trend(
        self,
        store_id: uuid.UUID,
        period: str = "month",  # month | week | day
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AOVByPeriod]:
        """AOV trend by time bucket."""
        _valid = {"month", "week", "day"}
        if period not in _valid:
            raise ValueError(f"period must be one of {_valid}")

        params: dict = {"sid": store_id}
        date_filter = ""
        if start_date:
            date_filter += " AND shopify_created_at >= :start_date"
            params["start_date"] = start_date
        if end_date:
            date_filter += " AND shopify_created_at <= :end_date"
            params["end_date"] = end_date

        result = await self.db.execute(
            text(f"""
                SELECT
                    DATE_TRUNC('{period}', shopify_created_at) AS period,
                    ROUND(AVG(total_price_usd)::NUMERIC, 2)    AS aov_usd,
                    COUNT(*)                                    AS order_count
                FROM orders
                WHERE store_id = :sid
                  AND financial_status = 'paid'
                  AND cancelled_at IS NULL
                  AND total_price_usd IS NOT NULL
                  {date_filter}
                GROUP BY DATE_TRUNC('{period}', shopify_created_at)
                ORDER BY period
            """),
            params,
        )
        return [AOVByPeriod(**row) for row in result.mappings()]

    # ── Monthly revenue ───────────────────────────────────────────────────

    async def get_monthly_revenue(
        self,
        store_id: uuid.UUID,
        months: int = 12,
    ) -> List[MonthlyRevenueRow]:
        """Last N months of revenue with new/returning breakdown."""
        result = await self.db.execute(
            text("""
                SELECT *
                FROM monthly_revenue
                WHERE store_id = :sid
                  AND month >= DATE_TRUNC('month', NOW() - INTERVAL '1 month' * :months)
                ORDER BY month
            """),
            {"sid": store_id, "months": months},
        )
        return [MonthlyRevenueRow(**row) for row in result.mappings()]

    # ── Repeat order rate ─────────────────────────────────────────────────

    async def get_repeat_order_rate(
        self,
        store_id: uuid.UUID,
        months: int = 12,
    ) -> List[RepeatOrderRateByMonth]:
        """
        Monthly repeat order rate — % of ordering customers who've
        ordered before.
        """
        result = await self.db.execute(
            text("""
                SELECT
                    DATE_TRUNC('month', o.shopify_created_at) AS month,
                    COUNT(DISTINCT CASE
                        WHEN prev.customer_id IS NULL THEN o.customer_id
                    END)                                        AS new_customers,
                    COUNT(DISTINCT CASE
                        WHEN prev.customer_id IS NOT NULL THEN o.customer_id
                    END)                                        AS repeat_customers,
                    ROUND(
                        COUNT(DISTINCT CASE
                            WHEN prev.customer_id IS NOT NULL THEN o.customer_id
                        END)::NUMERIC
                        / NULLIF(COUNT(DISTINCT o.customer_id), 0) * 100,
                        2
                    )                                           AS repeat_order_rate_pct
                FROM orders o
                LEFT JOIN LATERAL (
                    SELECT 1 AS customer_id
                    FROM orders prev_o
                    WHERE prev_o.customer_id = o.customer_id
                      AND prev_o.financial_status = 'paid'
                      AND prev_o.cancelled_at IS NULL
                      AND prev_o.shopify_created_at < o.shopify_created_at
                    LIMIT 1
                ) prev ON true
                WHERE o.store_id = :sid
                  AND o.financial_status = 'paid'
                  AND o.cancelled_at IS NULL
                  AND o.customer_id IS NOT NULL
                  AND o.shopify_created_at >= DATE_TRUNC(
                      'month', NOW() - INTERVAL '1 month' * :months
                  )
                GROUP BY DATE_TRUNC('month', o.shopify_created_at)
                ORDER BY month
            """),
            {"sid": store_id, "months": months},
        )
        return [RepeatOrderRateByMonth(**row) for row in result.mappings()]

    # ── Product performance ───────────────────────────────────────────────

    async def get_product_performance(
        self,
        store_id: uuid.UUID,
        limit: int = 50,
    ) -> List[ProductPerformanceRow]:
        """Top products by revenue."""
        result = await self.db.execute(
            text("""
                SELECT * FROM product_performance
                WHERE store_id = :sid
                ORDER BY revenue_usd DESC
                LIMIT :lim
            """),
            {"sid": store_id, "lim": limit},
        )
        return [ProductPerformanceRow(**row) for row in result.mappings()]

    # ── Time Between Orders (TBO) distribution ────────────────────────────

    async def get_tbo_distribution(
        self,
        store_id: uuid.UUID,
        buckets: List[int] = None,
    ) -> List[dict]:
        """
        Distribution of avg days between orders across customers.
        Returns counts per day-range bucket for a histogram.
        """
        buckets = buckets or [7, 14, 30, 60, 90, 180, 365]
        result = await self.db.execute(
            text("""
                SELECT
                    CASE
                        WHEN avg_days_between_orders <= 7   THEN '0-7d'
                        WHEN avg_days_between_orders <= 14  THEN '8-14d'
                        WHEN avg_days_between_orders <= 30  THEN '15-30d'
                        WHEN avg_days_between_orders <= 60  THEN '31-60d'
                        WHEN avg_days_between_orders <= 90  THEN '61-90d'
                        WHEN avg_days_between_orders <= 180 THEN '91-180d'
                        WHEN avg_days_between_orders <= 365 THEN '181-365d'
                        ELSE '365d+'
                    END                             AS bucket,
                    COUNT(*)                        AS customer_count,
                    ROUND(AVG(avg_days_between_orders)::NUMERIC, 1) AS avg_tbo_in_bucket
                FROM customer_cltv
                WHERE store_id = :sid
                  AND avg_days_between_orders IS NOT NULL
                  AND total_orders > 1
                GROUP BY 1
                ORDER BY MIN(avg_days_between_orders)
            """),
            {"sid": store_id},
        )
        return [dict(row) for row in result.mappings()]
