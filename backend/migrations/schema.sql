-- =============================================================================
--  Shopify Analytics Platform – Database Schema
--  Engine: PostgreSQL 15+
--
--  Design principles:
--   • Shopify IDs stored as BIGINT (they exceed 32-bit range)
--   • All monetary values stored as NUMERIC(12,2) in original currency
--   • Idempotency via ON CONFLICT DO UPDATE (upsert)
--   • Soft-delete pattern on stores (deactivated_at)
--   • Composite indexes to support cohort / time-series queries
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- fuzzy email search

-- ---------------------------------------------------------------------------
-- 1. shopify_stores
--    One row per connected Shopify shop.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shopify_stores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_domain     TEXT NOT NULL UNIQUE,          -- e.g. my-store.myshopify.com
    access_token    TEXT NOT NULL,
    scopes          TEXT NOT NULL,                 -- comma-separated scope list
    shopify_plan    TEXT,                          -- basic / shopify / advanced …
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    timezone        TEXT,
    installed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_at  TIMESTAMPTZ,                   -- NULL = active
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 2. sync_logs
--    Tracks every ingestion run (bulk or incremental).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id        UUID NOT NULL REFERENCES shopify_stores(id) ON DELETE CASCADE,
    sync_type       TEXT NOT NULL CHECK (sync_type IN ('bulk_initial', 'incremental', 'webhook')),
    entity          TEXT NOT NULL CHECK (entity IN ('customers', 'orders', 'all')),
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    shopify_bulk_op_id  TEXT,              -- Shopify bulk operation GID
    records_fetched     INT DEFAULT 0,
    records_upserted    INT DEFAULT 0,
    error_message       TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    -- Incremental cursor: resume from last processed created_at
    cursor_value    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_store_status
    ON sync_logs(store_id, status);

-- ---------------------------------------------------------------------------
-- 3. customers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id            UUID NOT NULL REFERENCES shopify_stores(id) ON DELETE CASCADE,

    -- Shopify identifiers
    shopify_customer_id BIGINT NOT NULL,
    email               TEXT,
    phone               TEXT,

    -- Shopify aggregates (denormalized for fast KPI reads)
    total_spent         NUMERIC(12, 2) NOT NULL DEFAULT 0,
    orders_count        INT NOT NULL DEFAULT 0,
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',

    -- Segmentation helpers
    tags                TEXT[],
    accepts_marketing   BOOLEAN NOT NULL DEFAULT FALSE,
    verified_email      BOOLEAN NOT NULL DEFAULT FALSE,
    is_guest            BOOLEAN NOT NULL DEFAULT FALSE,   -- no shopify_customer_id

    -- Timestamps
    shopify_created_at  TIMESTAMPTZ,
    shopify_updated_at  TIMESTAMPTZ,
    first_seen_at       TIMESTAMPTZ,                     -- set on first order
    last_seen_at        TIMESTAMPTZ,                     -- set on latest order
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_customer_per_store UNIQUE (store_id, shopify_customer_id)
);

-- KPI: cohort assignment (month of first purchase)
CREATE INDEX IF NOT EXISTS idx_customers_store_created
    ON customers(store_id, shopify_created_at);

CREATE INDEX IF NOT EXISTS idx_customers_email_trgm
    ON customers USING GIN (email gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_customers_first_seen
    ON customers(store_id, first_seen_at);

-- ---------------------------------------------------------------------------
-- 4. orders
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id            UUID NOT NULL REFERENCES shopify_stores(id) ON DELETE CASCADE,
    customer_id         UUID REFERENCES customers(id) ON DELETE SET NULL,

    -- Shopify identifiers
    shopify_order_id    BIGINT NOT NULL,
    shopify_order_number TEXT,                           -- human-readable #1001

    -- Financials
    total_price         NUMERIC(12, 2) NOT NULL,
    subtotal_price      NUMERIC(12, 2),
    total_tax           NUMERIC(12, 2),
    total_discounts     NUMERIC(12, 2),
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    total_price_usd     NUMERIC(12, 2),                  -- converted for cross-store KPIs

    -- Status
    financial_status    TEXT,   -- pending / paid / refunded / voided
    fulfillment_status  TEXT,   -- null / partial / fulfilled
    cancel_reason       TEXT,
    cancelled_at        TIMESTAMPTZ,

    -- Attribution
    source_name         TEXT,   -- web / pos / mobile_app
    landing_site        TEXT,
    referring_site      TEXT,

    -- Guest checkout flag
    is_guest_order      BOOLEAN NOT NULL DEFAULT FALSE,
    guest_email         TEXT,

    -- Timestamps
    shopify_created_at  TIMESTAMPTZ NOT NULL,
    shopify_updated_at  TIMESTAMPTZ,
    processed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_order_per_store UNIQUE (store_id, shopify_order_id)
);

-- KPI: time-series aggregations
CREATE INDEX IF NOT EXISTS idx_orders_store_created
    ON orders(store_id, shopify_created_at);

-- KPI: per-customer order history (repeat rate, TBO)
CREATE INDEX IF NOT EXISTS idx_orders_customer_created
    ON orders(customer_id, shopify_created_at);

-- KPI: filter by financial status
CREATE INDEX IF NOT EXISTS idx_orders_financial_status
    ON orders(store_id, financial_status);

-- ---------------------------------------------------------------------------
-- 5. order_items  (line items)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    store_id            UUID NOT NULL REFERENCES shopify_stores(id) ON DELETE CASCADE,

    shopify_line_item_id BIGINT NOT NULL,
    shopify_product_id   BIGINT,
    shopify_variant_id   BIGINT,

    title               TEXT,
    sku                 TEXT,
    vendor              TEXT,
    product_type        TEXT,

    quantity            INT NOT NULL DEFAULT 1,
    price               NUMERIC(12, 2) NOT NULL,
    total_discount      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    line_total          NUMERIC(12, 2)
        GENERATED ALWAYS AS ((price * quantity) - total_discount) STORED,

    -- Variants
    variant_title       TEXT,
    requires_shipping   BOOLEAN,
    is_gift_card        BOOLEAN NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_line_item_per_order UNIQUE (order_id, shopify_line_item_id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON order_items(order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product
    ON order_items(store_id, shopify_product_id);

-- ---------------------------------------------------------------------------
-- 6. webhook_events
--    Dead-letter queue + audit trail for incoming webhooks.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhook_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id        UUID NOT NULL REFERENCES shopify_stores(id) ON DELETE CASCADE,
    topic           TEXT NOT NULL,      -- orders/create, customers/update …
    shopify_event_id TEXT,              -- X-Shopify-Event-Id header (idempotency)
    payload         JSONB NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processed', 'failed', 'skipped')),
    attempts        INT NOT NULL DEFAULT 0,
    error_message   TEXT,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,

    CONSTRAINT uq_shopify_event UNIQUE (store_id, shopify_event_id)
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_status
    ON webhook_events(status, received_at);

CREATE INDEX IF NOT EXISTS idx_webhook_events_store_topic
    ON webhook_events(store_id, topic);

-- ---------------------------------------------------------------------------
-- Helper: auto-update updated_at columns
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['shopify_stores','customers','orders']
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS set_updated_at ON %I;
             CREATE TRIGGER set_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();',
            tbl, tbl
        );
    END LOOP;
END;
$$;
