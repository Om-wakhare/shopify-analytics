"""Initial schema — all core tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # ── shopify_stores ─────────────────────────────────────────────────────
    op.create_table(
        "shopify_stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("shop_domain", sa.Text(), nullable=False, unique=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("shopify_plan", sa.Text()),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("timezone", sa.Text()),
        sa.Column("installed_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deactivated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )

    # ── sync_logs ──────────────────────────────────────────────────────────
    op.create_table(
        "sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sync_type", sa.Text(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("shopify_bulk_op_id", sa.Text()),
        sa.Column("records_fetched", sa.Integer(), server_default="0"),
        sa.Column("records_upserted", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("cursor_value", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_sync_logs_store_status", "sync_logs", ["store_id", "status"])

    # ── customers ──────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shopify_customer_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("total_spent", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("orders_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("tags", postgresql.ARRAY(sa.Text())),
        sa.Column("accepts_marketing", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_email", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_guest", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("shopify_created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("shopify_updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("store_id", "shopify_customer_id", name="uq_customer_per_store"),
    )
    op.create_index("idx_customers_store_created", "customers", ["store_id", "shopify_created_at"])
    op.create_index("idx_customers_first_seen", "customers", ["store_id", "first_seen_at"])
    op.execute(
        "CREATE INDEX idx_customers_email_trgm ON customers USING GIN (email gin_trgm_ops)"
    )

    # ── orders ─────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("shopify_order_id", sa.BigInteger(), nullable=False),
        sa.Column("shopify_order_number", sa.Text()),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("subtotal_price", sa.Numeric(12, 2)),
        sa.Column("total_tax", sa.Numeric(12, 2)),
        sa.Column("total_discounts", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("total_price_usd", sa.Numeric(12, 2)),
        sa.Column("financial_status", sa.Text()),
        sa.Column("fulfillment_status", sa.Text()),
        sa.Column("cancel_reason", sa.Text()),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("source_name", sa.Text()),
        sa.Column("landing_site", sa.Text()),
        sa.Column("referring_site", sa.Text()),
        sa.Column("is_guest_order", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("guest_email", sa.Text()),
        sa.Column("shopify_created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("shopify_updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("store_id", "shopify_order_id", name="uq_order_per_store"),
    )
    op.create_index("idx_orders_store_created", "orders", ["store_id", "shopify_created_at"])
    op.create_index("idx_orders_customer_created", "orders", ["customer_id", "shopify_created_at"])
    op.create_index("idx_orders_financial_status", "orders", ["store_id", "financial_status"])

    # ── order_items ────────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shopify_line_item_id", sa.BigInteger(), nullable=False),
        sa.Column("shopify_product_id", sa.BigInteger()),
        sa.Column("shopify_variant_id", sa.BigInteger()),
        sa.Column("title", sa.Text()),
        sa.Column("sku", sa.Text()),
        sa.Column("vendor", sa.Text()),
        sa.Column("product_type", sa.Text()),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_discount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("variant_title", sa.Text()),
        sa.Column("requires_shipping", sa.Boolean()),
        sa.Column("is_gift_card", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("order_id", "shopify_line_item_id", name="uq_line_item_per_order"),
    )
    op.create_index("idx_order_items_order", "order_items", ["order_id"])
    op.create_index("idx_order_items_product", "order_items", ["store_id", "shopify_product_id"])

    # ── webhook_events ─────────────────────────────────────────────────────
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("shopify_event_id", sa.Text()),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("received_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("store_id", "shopify_event_id", name="uq_shopify_event"),
    )
    op.create_index("idx_webhook_events_status", "webhook_events", ["status", "received_at"])
    op.create_index("idx_webhook_events_store_topic", "webhook_events", ["store_id", "topic"])

    # ── updated_at trigger ─────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION trigger_set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$
    """)
    for tbl in ("shopify_stores", "customers", "orders"):
        op.execute(f"""
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at()
        """)


def downgrade() -> None:
    for tbl in ("shopify_stores", "customers", "orders"):
        op.execute(f"DROP TRIGGER IF EXISTS set_updated_at ON {tbl}")
    op.execute("DROP FUNCTION IF EXISTS trigger_set_updated_at()")
    op.drop_table("webhook_events")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("sync_logs")
    op.drop_table("shopify_stores")
