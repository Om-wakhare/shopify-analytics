"""
SQLAlchemy ORM models — mirror the SQL schema exactly.
Use mapped_column() (SQLAlchemy 2.0 style) for type-safe column declarations.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    ARRAY,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# ShopifyStore
# ---------------------------------------------------------------------------
class ShopifyStore(Base):
    __tablename__ = "shopify_stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    shop_domain: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    shopify_plan: Mapped[Optional[str]] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    timezone: Mapped[Optional[str]] = mapped_column(Text)
    installed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # relationships
    customers: Mapped[List["Customer"]] = relationship(back_populates="store")
    orders: Mapped[List["Order"]] = relationship(back_populates="store")
    sync_logs: Mapped[List["SyncLog"]] = relationship(back_populates="store")
    webhook_events: Mapped[List["WebhookEvent"]] = relationship(back_populates="store")


# ---------------------------------------------------------------------------
# SyncLog
# ---------------------------------------------------------------------------
class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False
    )
    sync_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    shopify_bulk_op_id: Mapped[Optional[str]] = mapped_column(Text)
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_upserted: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    cursor_value: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    store: Mapped["ShopifyStore"] = relationship(back_populates="sync_logs")


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("store_id", "shopify_customer_id", name="uq_customer_per_store"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False
    )
    shopify_customer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)

    total_spent: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    orders_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    accepts_marketing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    shopify_created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    shopify_updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    store: Mapped["ShopifyStore"] = relationship(back_populates="customers")
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------
class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("store_id", "shopify_order_id", name="uq_order_per_store"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL")
    )

    shopify_order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shopify_order_number: Mapped[Optional[str]] = mapped_column(Text)

    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    total_tax: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    total_discounts: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    total_price_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    financial_status: Mapped[Optional[str]] = mapped_column(Text)
    fulfillment_status: Mapped[Optional[str]] = mapped_column(Text)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    source_name: Mapped[Optional[str]] = mapped_column(Text)
    landing_site: Mapped[Optional[str]] = mapped_column(Text)
    referring_site: Mapped[Optional[str]] = mapped_column(Text)

    is_guest_order: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guest_email: Mapped[Optional[str]] = mapped_column(Text)

    shopify_created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    shopify_updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    processed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    store: Mapped["ShopifyStore"] = relationship(back_populates="orders")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="orders")
    line_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# OrderItem
# ---------------------------------------------------------------------------
class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "shopify_line_item_id", name="uq_line_item_per_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False
    )

    shopify_line_item_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shopify_product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    shopify_variant_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    title: Mapped[Optional[str]] = mapped_column(Text)
    sku: Mapped[Optional[str]] = mapped_column(Text)
    vendor: Mapped[Optional[str]] = mapped_column(Text)
    product_type: Mapped[Optional[str]] = mapped_column(Text)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    variant_title: Mapped[Optional[str]] = mapped_column(Text)
    requires_shipping: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_gift_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    order: Mapped["Order"] = relationship(back_populates="line_items")


# ---------------------------------------------------------------------------
# WebhookEvent
# ---------------------------------------------------------------------------
class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("store_id", "shopify_event_id", name="uq_shopify_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    shopify_event_id: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    store: Mapped["ShopifyStore"] = relationship(back_populates="webhook_events")


# ---------------------------------------------------------------------------
# PlatformUser
# ---------------------------------------------------------------------------
class PlatformUser(Base):
    __tablename__ = "platform_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    email: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(Text)

    subscription_status: Mapped[str] = mapped_column(Text, nullable=False, default="trial")
    subscription_plan: Mapped[Optional[str]] = mapped_column(Text)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    subscribed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    shopify_charge_id: Mapped[Optional[int]] = mapped_column(Integer)
    shopify_charge_status: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    store: Mapped["ShopifyStore"] = relationship()
