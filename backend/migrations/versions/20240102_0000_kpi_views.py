"""KPI analytics views — CLTV, AOV, Repeat Rate, Churn, TBO

Revision ID: 002_kpi_views
Revises: 001_initial
Create Date: 2024-01-02 00:00:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002_kpi_views"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # VIEW: customer_order_stats
    # Per-customer order metrics — foundation for all KPIs.
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW customer_order_stats AS
    SELECT
        c.id                                             AS customer_id,
        c.store_id,
        c.email,
        c.shopify_customer_id,
        c.shopify_created_at                             AS customer_since,
        COUNT(o.id)                                      AS total_orders,
        COALESCE(SUM(o.total_price_usd), 0)              AS total_revenue_usd,
        COALESCE(AVG(o.total_price_usd), 0)              AS avg_order_value_usd,
        MIN(o.shopify_created_at)                        AS first_order_at,
        MAX(o.shopify_created_at)                        AS last_order_at,
        -- Time Between Orders: avg days between consecutive purchases
        CASE WHEN COUNT(o.id) > 1 THEN
            EXTRACT(EPOCH FROM (
                MAX(o.shopify_created_at) - MIN(o.shopify_created_at)
            )) / 86400.0 / NULLIF(COUNT(o.id) - 1, 0)
        END                                              AS avg_days_between_orders,
        -- Repeat buyer flag
        (COUNT(o.id) > 1)                                AS is_repeat_buyer,
        DATE_TRUNC('month', MIN(o.shopify_created_at))  AS cohort_month
    FROM customers c
    LEFT JOIN orders o
        ON o.customer_id = c.id
        AND o.financial_status = 'paid'
        AND o.cancelled_at IS NULL
    GROUP BY
        c.id, c.store_id, c.email, c.shopify_customer_id,
        c.shopify_created_at
    """)

    # ------------------------------------------------------------------
    # VIEW: store_kpis
    # Single-row per store — top-level dashboard metrics.
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW store_kpis AS
    WITH paid_orders AS (
        SELECT
            store_id,
            customer_id,
            total_price_usd,
            shopify_created_at
        FROM orders
        WHERE financial_status = 'paid'
          AND cancelled_at IS NULL
          AND total_price_usd IS NOT NULL
    ),
    store_totals AS (
        SELECT
            store_id,
            COUNT(*)                       AS total_orders,
            COUNT(DISTINCT customer_id)    AS total_customers,
            SUM(total_price_usd)           AS total_revenue_usd,
            AVG(total_price_usd)           AS aov_usd
        FROM paid_orders
        GROUP BY store_id
    ),
    repeat_buyers AS (
        SELECT
            store_id,
            COUNT(DISTINCT customer_id) AS repeat_customer_count
        FROM paid_orders
        GROUP BY store_id, customer_id
        HAVING COUNT(*) > 1
    ),
    -- wrap to get store_id at top level
    repeat_agg AS (
        SELECT store_id, SUM(repeat_customer_count) AS repeat_customer_count
        FROM repeat_buyers
        GROUP BY store_id
    )
    SELECT
        st.store_id,
        st.total_orders,
        st.total_customers,
        ROUND(st.total_revenue_usd::NUMERIC, 2)       AS total_revenue_usd,
        ROUND(st.aov_usd::NUMERIC, 2)                 AS aov_usd,
        COALESCE(ra.repeat_customer_count, 0)          AS repeat_customers,
        -- Repeat Order Rate = repeat buyers / total buyers
        ROUND(
            COALESCE(ra.repeat_customer_count, 0)::NUMERIC
            / NULLIF(st.total_customers, 0) * 100,
            2
        )                                              AS repeat_order_rate_pct
    FROM store_totals st
    LEFT JOIN repeat_agg ra USING (store_id)
    """)

    # ------------------------------------------------------------------
    # VIEW: cohort_retention
    # Monthly cohort × month-offset retention matrix.
    # Used for: Cohort Retention, CLTV projection, Churn analysis.
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW cohort_retention AS
    WITH cohorts AS (
        -- Each customer's cohort = month of their first paid order
        SELECT
            c.store_id,
            c.id                                           AS customer_id,
            DATE_TRUNC('month', MIN(o.shopify_created_at)) AS cohort_month
        FROM customers c
        JOIN orders o
            ON o.customer_id = c.id
            AND o.financial_status = 'paid'
            AND o.cancelled_at IS NULL
        GROUP BY c.store_id, c.id
    ),
    activity AS (
        -- Every month a customer placed a paid order
        SELECT DISTINCT
            o.store_id,
            o.customer_id,
            DATE_TRUNC('month', o.shopify_created_at) AS activity_month
        FROM orders o
        WHERE o.financial_status = 'paid'
          AND o.cancelled_at IS NULL
    )
    SELECT
        c.store_id,
        c.cohort_month,
        COUNT(DISTINCT c.customer_id)                          AS cohort_size,
        -- Month offset 0 = acquisition month, 1 = month after, etc.
        EXTRACT(
            YEAR FROM AGE(a.activity_month, c.cohort_month)
        ) * 12
        + EXTRACT(
            MONTH FROM AGE(a.activity_month, c.cohort_month)
        )                                                      AS month_offset,
        COUNT(DISTINCT a.customer_id)                          AS active_customers,
        ROUND(
            COUNT(DISTINCT a.customer_id)::NUMERIC
            / NULLIF(COUNT(DISTINCT c.customer_id), 0) * 100,
            2
        )                                                      AS retention_rate_pct
    FROM cohorts c
    JOIN activity a
        ON a.customer_id = c.customer_id
        AND a.store_id = c.store_id
        AND a.activity_month >= c.cohort_month
    GROUP BY c.store_id, c.cohort_month, a.activity_month
    ORDER BY c.cohort_month, month_offset
    """)

    # ------------------------------------------------------------------
    # VIEW: customer_cltv
    # Historical CLTV per customer + simple 12-month projection.
    # Formula: CLTV = AOV × Purchase Frequency × Customer Lifespan
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW customer_cltv AS
    WITH stats AS (
        SELECT
            cos.customer_id,
            cos.store_id,
            cos.total_revenue_usd                              AS historical_revenue,
            cos.total_orders,
            cos.avg_order_value_usd                            AS aov,
            cos.avg_days_between_orders,
            cos.first_order_at,
            cos.last_order_at,
            cos.cohort_month,
            -- Purchase frequency: orders per 30-day period (since first order)
            CASE
                WHEN cos.first_order_at IS NOT NULL
                  AND cos.last_order_at > cos.first_order_at
                THEN cos.total_orders::FLOAT
                    / NULLIF(
                        EXTRACT(EPOCH FROM NOW() - cos.first_order_at) / 2592000.0,
                        0
                    )
            END                                                AS monthly_purchase_freq
        FROM customer_order_stats cos
        WHERE cos.total_orders > 0
    )
    SELECT
        customer_id,
        store_id,
        ROUND(historical_revenue::NUMERIC, 2)                 AS historical_cltv_usd,
        total_orders,
        ROUND(aov::NUMERIC, 2)                                AS aov_usd,
        ROUND(avg_days_between_orders::NUMERIC, 1)            AS avg_days_between_orders,
        monthly_purchase_freq,
        -- Projected 12-month CLTV = AOV × monthly_freq × 12
        ROUND(
            (aov * COALESCE(monthly_purchase_freq, 0) * 12)::NUMERIC,
            2
        )                                                     AS projected_12m_cltv_usd,
        first_order_at,
        last_order_at,
        cohort_month,
        -- Days since last order (recency)
        EXTRACT(DAY FROM NOW() - last_order_at)::INT          AS days_since_last_order
    FROM stats
    """)

    # ------------------------------------------------------------------
    # VIEW: churn_signals
    # Customers who haven't ordered in > 90 days (configurable).
    # Churn risk tiers based on recency vs. their personal TBO.
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW churn_signals AS
    SELECT
        cltv.customer_id,
        cltv.store_id,
        cltv.days_since_last_order,
        cltv.avg_days_between_orders,
        cltv.historical_cltv_usd,
        cltv.total_orders,
        -- Risk tier: compare recency to the customer's own purchase cadence
        CASE
            WHEN cltv.avg_days_between_orders IS NULL THEN 'one_time_buyer'
            WHEN cltv.days_since_last_order
                > cltv.avg_days_between_orders * 3   THEN 'high_risk'
            WHEN cltv.days_since_last_order
                > cltv.avg_days_between_orders * 2   THEN 'medium_risk'
            WHEN cltv.days_since_last_order
                > cltv.avg_days_between_orders * 1.5 THEN 'low_risk'
            ELSE 'healthy'
        END                                               AS churn_risk_tier,
        cltv.last_order_at,
        cltv.cohort_month
    FROM customer_cltv cltv
    WHERE cltv.days_since_last_order > 30  -- only show customers dormant > 30d
    """)

    # ------------------------------------------------------------------
    # VIEW: monthly_revenue
    # Time-series revenue aggregation for trend charts.
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW monthly_revenue AS
    SELECT
        store_id,
        DATE_TRUNC('month', shopify_created_at)        AS month,
        COUNT(*)                                        AS order_count,
        COUNT(DISTINCT customer_id)                     AS unique_customers,
        ROUND(SUM(total_price_usd)::NUMERIC, 2)         AS revenue_usd,
        ROUND(AVG(total_price_usd)::NUMERIC, 2)         AS aov_usd,
        -- New vs returning breakdown
        COUNT(DISTINCT CASE
            WHEN customer_id IN (
                SELECT customer_id
                FROM orders o2
                WHERE o2.financial_status = 'paid'
                  AND o2.cancelled_at IS NULL
                  AND o2.shopify_created_at
                    < DATE_TRUNC('month', orders.shopify_created_at)
            ) THEN customer_id
        END)                                            AS returning_customers,
        COUNT(DISTINCT CASE
            WHEN customer_id NOT IN (
                SELECT customer_id
                FROM orders o2
                WHERE o2.financial_status = 'paid'
                  AND o2.cancelled_at IS NULL
                  AND o2.shopify_created_at
                    < DATE_TRUNC('month', orders.shopify_created_at)
            ) THEN customer_id
        END)                                            AS new_customers
    FROM orders
    WHERE financial_status = 'paid'
      AND cancelled_at IS NULL
      AND total_price_usd IS NOT NULL
    GROUP BY store_id, DATE_TRUNC('month', shopify_created_at)
    ORDER BY month
    """)

    # ------------------------------------------------------------------
    # VIEW: product_performance
    # Per-product revenue + attach rate.
    # ------------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE VIEW product_performance AS
    SELECT
        oi.store_id,
        oi.shopify_product_id,
        oi.title                                            AS product_title,
        oi.vendor,
        oi.product_type,
        COUNT(DISTINCT oi.order_id)                         AS order_count,
        SUM(oi.quantity)                                    AS units_sold,
        ROUND(SUM((oi.price * oi.quantity) - oi.total_discount)::NUMERIC, 2) AS revenue_usd,
        ROUND(AVG(oi.price)::NUMERIC, 2)                    AS avg_unit_price,
        COUNT(DISTINCT o.customer_id)                       AS unique_customers
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    WHERE o.financial_status = 'paid'
      AND o.cancelled_at IS NULL
    GROUP BY oi.store_id, oi.shopify_product_id, oi.title, oi.vendor, oi.product_type
    """)


def downgrade() -> None:
    for view in (
        "product_performance",
        "monthly_revenue",
        "churn_signals",
        "customer_cltv",
        "cohort_retention",
        "store_kpis",
        "customer_order_stats",
    ):
        op.execute(f"DROP VIEW IF EXISTS {view} CASCADE")
