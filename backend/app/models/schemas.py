"""
Pydantic v2 schemas for request/response validation and internal DTOs.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------
class OAuthStartResponse(BaseModel):
    redirect_url: str


class OAuthCallbackParams(BaseModel):
    shop: str
    code: str
    state: str
    hmac: str
    timestamp: str


class StoreConnectedResponse(BaseModel):
    store_id: uuid.UUID
    shop_domain: str
    scopes: str
    message: str = "Store connected successfully"


# ---------------------------------------------------------------------------
# Shopify raw payloads (inbound webhook bodies)
# ---------------------------------------------------------------------------
class ShopifyAddress(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address1: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    zip: Optional[str] = None


class ShopifyCustomerPayload(BaseModel):
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    total_spent: Decimal = Decimal("0")
    orders_count: int = 0
    currency: str = "USD"
    tags: str = ""  # Shopify returns tags as comma-separated string
    accepts_marketing: bool = False
    verified_email: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: str) -> str:
        return v or ""


class ShopifyLineItemPayload(BaseModel):
    id: int
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    title: Optional[str] = None
    sku: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    quantity: int = 1
    price: Decimal = Decimal("0")
    total_discount: Decimal = Decimal("0")
    variant_title: Optional[str] = None
    requires_shipping: Optional[bool] = None
    gift_card: bool = False


class ShopifyOrderPayload(BaseModel):
    id: int
    order_number: Optional[int] = None
    email: Optional[str] = None
    customer: Optional[ShopifyCustomerPayload] = None
    line_items: List[ShopifyLineItemPayload] = Field(default_factory=list)

    total_price: Decimal = Decimal("0")
    subtotal_price: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_discounts: Optional[Decimal] = None
    currency: str = "USD"

    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None

    source_name: Optional[str] = None
    landing_site: Optional[str] = None
    referring_site: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None




# ---------------------------------------------------------------------------
# Internal normalized DTOs (what our service layer works with)
# ---------------------------------------------------------------------------
class NormalizedCustomer(BaseModel):
    shopify_customer_id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    total_spent: Decimal = Decimal("0")
    orders_count: int = 0
    currency: str = "USD"
    tags: List[str] = Field(default_factory=list)
    accepts_marketing: bool = False
    verified_email: bool = False
    is_guest: bool = False
    shopify_created_at: Optional[datetime] = None
    shopify_updated_at: Optional[datetime] = None


class NormalizedLineItem(BaseModel):
    shopify_line_item_id: int
    shopify_product_id: Optional[int] = None
    shopify_variant_id: Optional[int] = None
    title: Optional[str] = None
    sku: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    quantity: int = 1
    price: Decimal = Decimal("0")
    total_discount: Decimal = Decimal("0")
    variant_title: Optional[str] = None
    requires_shipping: Optional[bool] = None
    is_gift_card: bool = False


class NormalizedOrder(BaseModel):
    shopify_order_id: int
    shopify_order_number: Optional[str] = None
    customer: Optional[NormalizedCustomer] = None
    line_items: List[NormalizedLineItem] = Field(default_factory=list)

    total_price: Decimal = Decimal("0")
    subtotal_price: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_discounts: Optional[Decimal] = None
    currency: str = "USD"
    total_price_usd: Optional[Decimal] = None

    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None

    source_name: Optional[str] = None
    landing_site: Optional[str] = None
    referring_site: Optional[str] = None

    is_guest_order: bool = False
    guest_email: Optional[str] = None

    shopify_created_at: datetime
    shopify_updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------
class BulkSyncRequest(BaseModel):
    shop_domain: str
    entity: str = "all"  # all | customers | orders


class BulkSyncResponse(BaseModel):
    sync_log_id: uuid.UUID
    bulk_op_id: Optional[str] = None
    message: str


# ---------------------------------------------------------------------------
# API response wrappers
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
