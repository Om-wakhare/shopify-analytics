"""
Data normalization layer.

Converts raw Shopify API payloads (REST webhook dicts or Bulk Operation
GraphQL nodes) into our internal NormalizedCustomer / NormalizedOrder DTOs.

Two sources have slightly different field shapes:
  • "rest"  — snake_case keys from REST webhook body
  • "bulk"  — camelCase keys from GraphQL Bulk Operation JSONL

Both are handled transparently here so downstream upsert code is source-agnostic.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from app.models.schemas import (
    NormalizedCustomer,
    NormalizedLineItem,
    NormalizedOrder,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def normalize_customer(raw: dict, source: str = "rest") -> NormalizedCustomer:
    """
    Convert a raw customer dict from REST webhook or Bulk JSONL into
    a NormalizedCustomer DTO.
    """
    if source == "bulk":
        return _normalize_customer_bulk(raw)
    return _normalize_customer_rest(raw)


def normalize_order(raw: dict, source: str = "rest") -> NormalizedOrder:
    """
    Convert a raw order dict from REST webhook or Bulk JSONL into
    a NormalizedOrder DTO.
    """
    if source == "bulk":
        return _normalize_order_bulk(raw)
    return _normalize_order_rest(raw)


# ---------------------------------------------------------------------------
# Customer — REST (snake_case webhook body)
# ---------------------------------------------------------------------------

def _normalize_customer_rest(raw: dict) -> NormalizedCustomer:
    tags_raw = raw.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    return NormalizedCustomer(
        shopify_customer_id=int(raw["id"]),
        email=raw.get("email"),
        phone=raw.get("phone"),
        total_spent=_decimal(raw.get("total_spent", "0")),
        orders_count=int(raw.get("orders_count", 0)),
        currency=raw.get("currency", "USD"),
        tags=tags,
        accepts_marketing=bool(raw.get("accepts_marketing", False)),
        verified_email=bool(raw.get("verified_email", False)),
        is_guest=False,
        shopify_created_at=_dt(raw.get("created_at")),
        shopify_updated_at=_dt(raw.get("updated_at")),
    )


# ---------------------------------------------------------------------------
# Customer — Bulk GraphQL (camelCase node)
# ---------------------------------------------------------------------------

def _normalize_customer_bulk(raw: dict) -> NormalizedCustomer:
    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    # total_spent may be { amount, currencyCode } or a flat string
    total_spent_raw = raw.get("amountSpent") or raw.get("totalSpentV2") or {}
    if isinstance(total_spent_raw, dict):
        total_spent = _decimal(total_spent_raw.get("amount", "0"))
        currency = total_spent_raw.get("currencyCode", "USD")
    else:
        total_spent = _decimal(str(total_spent_raw))
        currency = "USD"

    marketing_state = (raw.get("emailMarketingConsent") or {}).get("marketingState", "")
    accepts_marketing = marketing_state.upper() == "SUBSCRIBED"

    return NormalizedCustomer(
        shopify_customer_id=int(raw.get("legacyResourceId", 0)),
        email=raw.get("email"),
        phone=raw.get("phone"),
        total_spent=total_spent,
        orders_count=int(raw.get("numberOfOrders", 0)),
        currency=currency,
        tags=tags,
        accepts_marketing=accepts_marketing,
        verified_email=bool(raw.get("verifiedEmail", False)),
        is_guest=False,
        shopify_created_at=_dt(raw.get("createdAt")),
        shopify_updated_at=_dt(raw.get("updatedAt")),
    )


# ---------------------------------------------------------------------------
# Order — REST (snake_case webhook body)
# ---------------------------------------------------------------------------

def _normalize_order_rest(raw: dict) -> NormalizedOrder:
    customer_raw = raw.get("customer")
    norm_customer: Optional[NormalizedCustomer] = None
    is_guest = False
    guest_email: Optional[str] = None

    if customer_raw and customer_raw.get("id"):
        norm_customer = _normalize_customer_rest(customer_raw)
    else:
        # Guest checkout — no Shopify customer record
        is_guest = True
        guest_email = raw.get("email")

    line_items = [
        _normalize_line_item_rest(li) for li in raw.get("line_items", [])
    ]

    currency = raw.get("currency", "USD")
    total_price = _decimal(raw.get("total_price", "0"))

    return NormalizedOrder(
        shopify_order_id=int(raw["id"]),
        shopify_order_number=str(raw["order_number"]) if raw.get("order_number") else None,
        customer=norm_customer,
        line_items=line_items,
        total_price=total_price,
        subtotal_price=_decimal_opt(raw.get("subtotal_price")),
        total_tax=_decimal_opt(raw.get("total_tax")),
        total_discounts=_decimal_opt(raw.get("total_discounts")),
        currency=currency,
        total_price_usd=_to_usd(total_price, currency),
        financial_status=raw.get("financial_status"),
        fulfillment_status=raw.get("fulfillment_status"),
        cancel_reason=raw.get("cancel_reason"),
        cancelled_at=_dt(raw.get("cancelled_at")),
        source_name=raw.get("source_name"),
        landing_site=raw.get("landing_site"),
        referring_site=raw.get("referring_site"),
        is_guest_order=is_guest,
        guest_email=guest_email,
        shopify_created_at=_dt(raw["created_at"]),
        shopify_updated_at=_dt(raw.get("updated_at")),
        processed_at=_dt(raw.get("processed_at")),
    )


def _normalize_line_item_rest(raw: dict) -> NormalizedLineItem:
    return NormalizedLineItem(
        shopify_line_item_id=int(raw["id"]),
        shopify_product_id=_int_opt(raw.get("product_id")),
        shopify_variant_id=_int_opt(raw.get("variant_id")),
        title=raw.get("title"),
        sku=raw.get("sku"),
        vendor=raw.get("vendor"),
        product_type=raw.get("product_type"),
        quantity=int(raw.get("quantity", 1)),
        price=_decimal(raw.get("price", "0")),
        total_discount=_decimal(raw.get("total_discount", "0")),
        variant_title=raw.get("variant_title"),
        requires_shipping=raw.get("requires_shipping"),
        is_gift_card=bool(raw.get("gift_card", False)),
    )


# ---------------------------------------------------------------------------
# Order — Bulk GraphQL (camelCase node)
# ---------------------------------------------------------------------------

def _normalize_order_bulk(raw: dict) -> NormalizedOrder:
    customer_raw = raw.get("customer")
    norm_customer: Optional[NormalizedCustomer] = None
    is_guest = False
    guest_email: Optional[str] = None

    if customer_raw and customer_raw.get("legacyResourceId"):
        # Minimal customer stub from bulk order query
        norm_customer = NormalizedCustomer(
            shopify_customer_id=int(customer_raw["legacyResourceId"]),
            is_guest=False,
        )
    else:
        is_guest = True
        guest_email = raw.get("email")

    # Extract line items from the edges structure
    li_edges = (raw.get("lineItems") or {}).get("edges", [])
    line_items = [_normalize_line_item_bulk(edge["node"]) for edge in li_edges]

    # Money fields: { shopMoney: { amount, currencyCode } }
    def shop_money(field_name: str) -> Optional[dict]:
        return (raw.get(field_name) or {}).get("shopMoney")

    price_money = shop_money("currentTotalPriceSet") or {}
    currency = price_money.get("currencyCode", "USD")
    total_price = _decimal(price_money.get("amount", "0"))

    subtotal_money = shop_money("subtotalPriceSet") or {}
    tax_money = shop_money("totalTaxSet") or {}
    discount_money = shop_money("totalDiscountsSet") or {}

    return NormalizedOrder(
        shopify_order_id=int(raw.get("legacyResourceId", 0)),
        shopify_order_number=raw.get("name"),  # e.g. "#1001"
        customer=norm_customer,
        line_items=line_items,
        total_price=total_price,
        subtotal_price=_decimal_opt(subtotal_money.get("amount")),
        total_tax=_decimal_opt(tax_money.get("amount")),
        total_discounts=_decimal_opt(discount_money.get("amount")),
        currency=currency,
        total_price_usd=_to_usd(total_price, currency),
        financial_status=_camel_to_lower(raw.get("financialStatus")),
        fulfillment_status=_camel_to_lower(raw.get("fulfillmentStatus")),
        cancel_reason=_camel_to_lower(raw.get("cancelReason")),
        cancelled_at=_dt(raw.get("cancelledAt")),
        source_name=raw.get("sourceName"),
        landing_site=raw.get("landingSite"),
        referring_site=raw.get("referringSite"),
        is_guest_order=is_guest,
        guest_email=guest_email,
        shopify_created_at=_dt(raw["createdAt"]),
        shopify_updated_at=_dt(raw.get("updatedAt")),
        processed_at=_dt(raw.get("processedAt")),
    )


def _normalize_line_item_bulk(raw: dict) -> NormalizedLineItem:
    product = raw.get("product") or {}
    variant = raw.get("variant") or {}

    price_money = (raw.get("originalUnitPriceSet") or {}).get("shopMoney") or {}
    discount_money = (raw.get("totalDiscountSet") or {}).get("shopMoney") or {}

    return NormalizedLineItem(
        shopify_line_item_id=int(raw["id"].split("/")[-1]),  # GID → numeric
        shopify_product_id=_int_opt(product.get("legacyResourceId")),
        shopify_variant_id=_int_opt(variant.get("legacyResourceId")),
        title=raw.get("title"),
        sku=raw.get("sku"),
        vendor=raw.get("vendor"),
        product_type=product.get("productType"),
        quantity=int(raw.get("quantity", 1)),
        price=_decimal(price_money.get("amount", "0")),
        total_discount=_decimal(discount_money.get("amount", "0")),
        variant_title=raw.get("variantTitle"),
        requires_shipping=raw.get("requiresShipping"),
        is_gift_card=bool(raw.get("isGiftCard", False)),
    )


# ---------------------------------------------------------------------------
# Type coercion helpers
# ---------------------------------------------------------------------------

def _decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _decimal_opt(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def _int_opt(value) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dt(value) -> Optional[datetime]:
    """Parse an ISO-8601 string into a timezone-aware datetime."""
    if not value:
        return None
    try:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        logger.warning("Could not parse datetime: %r", value)
        return None


def _camel_to_lower(value: Optional[str]) -> Optional[str]:
    """Convert ENUM-style SHOPIFY_VALUE to lowercase shopify_value."""
    if value is None:
        return None
    return value.lower()


# ---------------------------------------------------------------------------
# Currency conversion
# ---------------------------------------------------------------------------
# Synchronous path (used during normalization before we have an async context):
# uses the static fallback table from FXService so they stay in sync.
# For async callers (bulk_sync, webhooks), pass an FXService instance instead.

from app.services.fx_service import _STATIC_RATES  # noqa: E402


def _to_usd(amount: Decimal, currency: str) -> Optional[Decimal]:
    """
    Convert amount to USD using the shared static rate table.
    For live rates, use FXService.convert_to_usd() in async contexts.
    """
    rate = _STATIC_RATES.get(currency.upper())
    if rate is None:
        return None
    return (amount * Decimal(str(rate))).quantize(Decimal("0.01"))
