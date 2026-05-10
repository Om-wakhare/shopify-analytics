"""
Tests for the normalization layer.
Covers both REST webhook shape and Bulk Operation GraphQL shape.
No DB or network required.
"""
from decimal import Decimal

import pytest

from app.services.normalization import normalize_customer, normalize_order


# ---------------------------------------------------------------------------
# Fixtures — raw payloads
# ---------------------------------------------------------------------------

REST_CUSTOMER = {
    "id": 987654321,
    "email": "jane@example.com",
    "phone": "+1-555-000-0000",
    "created_at": "2023-01-15T10:00:00-05:00",
    "updated_at": "2024-03-01T12:00:00Z",
    "total_spent": "349.95",
    "orders_count": 4,
    "currency": "USD",
    "tags": "vip, wholesale",
    "accepts_marketing": True,
    "verified_email": True,
}

REST_ORDER = {
    "id": 111222333,
    "order_number": 1042,
    "email": "jane@example.com",
    "customer": REST_CUSTOMER,
    "line_items": [
        {
            "id": 555666,
            "product_id": 100,
            "variant_id": 200,
            "title": "Blue Widget",
            "sku": "BW-001",
            "vendor": "Acme",
            "product_type": "Widget",
            "quantity": 2,
            "price": "49.99",
            "total_discount": "5.00",
            "variant_title": "Blue",
            "requires_shipping": True,
            "gift_card": False,
        }
    ],
    "total_price": "94.98",
    "subtotal_price": "99.98",
    "total_tax": "8.50",
    "total_discounts": "5.00",
    "currency": "USD",
    "financial_status": "paid",
    "fulfillment_status": "fulfilled",
    "source_name": "web",
    "created_at": "2024-02-10T09:30:00Z",
    "updated_at": "2024-02-10T10:00:00Z",
}

BULK_CUSTOMER = {
    "id": "gid://shopify/Customer/987654321",
    "legacyResourceId": "987654321",
    "email": "jane@example.com",
    "phone": "+1-555-000-0000",
    "createdAt": "2023-01-15T15:00:00Z",
    "updatedAt": "2024-03-01T12:00:00Z",
    "totalSpentV2": {"amount": "349.95", "currencyCode": "USD"},
    "numberOfOrders": 4,
    "tags": ["vip", "wholesale"],
    "emailMarketingConsent": {"marketingState": "SUBSCRIBED"},
    "verifiedEmail": True,
}

BULK_ORDER = {
    "id": "gid://shopify/Order/111222333",
    "legacyResourceId": "111222333",
    "name": "#1042",
    "email": "jane@example.com",
    "createdAt": "2024-02-10T09:30:00Z",
    "updatedAt": "2024-02-10T10:00:00Z",
    "processedAt": "2024-02-10T09:31:00Z",
    "cancelledAt": None,
    "cancelReason": None,
    "financialStatus": "PAID",
    "fulfillmentStatus": "FULFILLED",
    "sourceName": "web",
    "landingSite": None,
    "referringSite": None,
    "currentTotalPriceSet": {"shopMoney": {"amount": "94.98", "currencyCode": "USD"}},
    "subtotalPriceSet": {"shopMoney": {"amount": "99.98", "currencyCode": "USD"}},
    "totalTaxSet": {"shopMoney": {"amount": "8.50", "currencyCode": "USD"}},
    "totalDiscountsSet": {"shopMoney": {"amount": "5.00", "currencyCode": "USD"}},
    "customer": {"id": "gid://shopify/Customer/987654321", "legacyResourceId": "987654321"},
    "lineItems": {
        "edges": [
            {
                "node": {
                    "id": "gid://shopify/LineItem/555666",
                    "quantity": 2,
                    "title": "Blue Widget",
                    "sku": "BW-001",
                    "vendor": "Acme",
                    "variantTitle": "Blue",
                    "requiresShipping": True,
                    "isGiftCard": False,
                    "product": {"id": "gid://shopify/Product/100", "legacyResourceId": "100", "productType": "Widget"},
                    "variant": {"id": "gid://shopify/ProductVariant/200", "legacyResourceId": "200"},
                    "originalUnitPriceSet": {"shopMoney": {"amount": "49.99"}},
                    "totalDiscountSet": {"shopMoney": {"amount": "5.00"}},
                }
            }
        ]
    },
}


# ---------------------------------------------------------------------------
# Customer normalization
# ---------------------------------------------------------------------------

class TestNormalizeCustomerREST:
    def test_basic_fields(self):
        c = normalize_customer(REST_CUSTOMER, source="rest")
        assert c.shopify_customer_id == 987654321
        assert c.email == "jane@example.com"
        assert c.total_spent == Decimal("349.95")
        assert c.orders_count == 4
        assert c.currency == "USD"
        assert c.accepts_marketing is True
        assert c.verified_email is True
        assert c.is_guest is False

    def test_tags_parsed_as_list(self):
        c = normalize_customer(REST_CUSTOMER, source="rest")
        assert "vip" in c.tags
        assert "wholesale" in c.tags

    def test_timestamps_are_utc(self):
        c = normalize_customer(REST_CUSTOMER, source="rest")
        assert c.shopify_created_at.tzinfo is not None
        assert c.shopify_updated_at.tzinfo is not None

    def test_missing_tags_defaults_to_empty(self):
        raw = {**REST_CUSTOMER, "tags": ""}
        c = normalize_customer(raw, source="rest")
        assert c.tags == []


class TestNormalizeCustomerBulk:
    def test_basic_fields(self):
        c = normalize_customer(BULK_CUSTOMER, source="bulk")
        assert c.shopify_customer_id == 987654321
        assert c.email == "jane@example.com"
        assert c.total_spent == Decimal("349.95")
        assert c.currency == "USD"
        assert c.accepts_marketing is True

    def test_tags_list_passthrough(self):
        c = normalize_customer(BULK_CUSTOMER, source="bulk")
        assert set(c.tags) == {"vip", "wholesale"}

    def test_unsubscribed_marketing(self):
        raw = {**BULK_CUSTOMER, "emailMarketingConsent": {"marketingState": "UNSUBSCRIBED"}}
        c = normalize_customer(raw, source="bulk")
        assert c.accepts_marketing is False


# ---------------------------------------------------------------------------
# Order normalization
# ---------------------------------------------------------------------------

class TestNormalizeOrderREST:
    def test_basic_financials(self):
        o = normalize_order(REST_ORDER, source="rest")
        assert o.shopify_order_id == 111222333
        assert o.total_price == Decimal("94.98")
        assert o.financial_status == "paid"
        assert o.is_guest_order is False

    def test_customer_attached(self):
        o = normalize_order(REST_ORDER, source="rest")
        assert o.customer is not None
        assert o.customer.shopify_customer_id == 987654321

    def test_line_items(self):
        o = normalize_order(REST_ORDER, source="rest")
        assert len(o.line_items) == 1
        li = o.line_items[0]
        assert li.shopify_line_item_id == 555666
        assert li.quantity == 2
        assert li.price == Decimal("49.99")
        assert li.total_discount == Decimal("5.00")

    def test_usd_conversion_same_currency(self):
        o = normalize_order(REST_ORDER, source="rest")
        assert o.total_price_usd == Decimal("94.98")  # USD → USD rate=1.0

    def test_guest_order_no_customer(self):
        raw = {**REST_ORDER, "customer": None, "email": "guest@example.com"}
        o = normalize_order(raw, source="rest")
        assert o.is_guest_order is True
        assert o.guest_email == "guest@example.com"
        assert o.customer is None


class TestNormalizeOrderBulk:
    def test_basic_financials(self):
        o = normalize_order(BULK_ORDER, source="bulk")
        assert o.shopify_order_id == 111222333
        assert o.total_price == Decimal("94.98")
        assert o.financial_status == "paid"   # lowercased from PAID
        assert o.fulfillment_status == "fulfilled"

    def test_order_number(self):
        o = normalize_order(BULK_ORDER, source="bulk")
        assert o.shopify_order_number == "#1042"

    def test_line_items(self):
        o = normalize_order(BULK_ORDER, source="bulk")
        assert len(o.line_items) == 1
        li = o.line_items[0]
        assert li.shopify_line_item_id == 555666  # extracted from GID
        assert li.shopify_product_id == 100
        assert li.shopify_variant_id == 200
        assert li.quantity == 2


# ---------------------------------------------------------------------------
# Currency conversion
# ---------------------------------------------------------------------------

class TestCurrencyConversion:
    def test_eur_to_usd(self):
        from app.services.normalization import _to_usd
        result = _to_usd(Decimal("100.00"), "EUR")
        assert result is not None
        assert result > Decimal("100")  # EUR > USD

    def test_unknown_currency_returns_none(self):
        from app.services.normalization import _to_usd
        result = _to_usd(Decimal("100.00"), "XYZ")
        assert result is None

    def test_usd_passthrough(self):
        from app.services.normalization import _to_usd
        result = _to_usd(Decimal("55.99"), "USD")
        assert result == Decimal("55.99")
