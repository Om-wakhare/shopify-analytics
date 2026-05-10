"""
Integration tests for webhook endpoints.
Uses the AsyncClient fixture from conftest.py — real DB, real FastAPI routing.
"""
import base64
import hashlib
import hmac
import json
import uuid

import pytest
import pytest_asyncio

WEBHOOK_SECRET = "test_api_secret_abc123"


def _sign_body(body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _webhook_headers(body: bytes, shop: str, topic: str, event_id: str = None) -> dict:
    return {
        "X-Shopify-Hmac-Sha256": _sign_body(body),
        "X-Shopify-Shop-Domain": shop,
        "X-Shopify-Topic": topic,
        "X-Shopify-Event-Id": event_id or str(uuid.uuid4()),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_webhook_invalid_hmac(client, store):
    """Requests with a bad HMAC must be rejected with 401."""
    body = json.dumps({"id": 1}).encode()
    resp = await client.post(
        "/webhooks/orders_create",
        content=body,
        headers={
            "X-Shopify-Hmac-Sha256": "badsignature==",
            "X-Shopify-Shop-Domain": store.shop_domain,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Event-Id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_unknown_topic(client, store):
    """Unknown topics return 404."""
    body = json.dumps({"id": 1}).encode()
    resp = await client.post(
        "/webhooks/unknown_topic",
        content=body,
        headers=_webhook_headers(body, store.shop_domain, "unknown/topic"),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_webhook_unknown_shop(client):
    """Webhook for a shop we don't know about is acknowledged but ignored."""
    body = json.dumps({"id": 1}).encode()
    resp = await client.post(
        "/webhooks/orders_create",
        content=body,
        headers=_webhook_headers(body, "unknown-shop.myshopify.com", "orders/create"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ignored"


@pytest.mark.asyncio
async def test_webhook_valid_order_create(client, store, monkeypatch):
    """
    Valid orders/create webhook is accepted and queued.
    We mock Celery task dispatch to avoid needing a real broker.
    """
    from unittest.mock import MagicMock, patch

    order_payload = {
        "id": 99887766,
        "order_number": 1099,
        "email": "new@example.com",
        "customer": None,
        "line_items": [],
        "total_price": "79.99",
        "currency": "USD",
        "financial_status": "paid",
        "fulfillment_status": None,
        "created_at": "2024-03-01T12:00:00Z",
    }
    body = json.dumps(order_payload).encode()

    with patch("app.workers.tasks.process_webhook_task") as mock_task:
        mock_task.delay = MagicMock()
        resp = await client.post(
            "/webhooks/orders_create",
            content=body,
            headers=_webhook_headers(body, store.shop_domain, "orders/create"),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "event_id" in data
    mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_idempotent(client, store, monkeypatch):
    """Sending the same event_id twice only processes it once."""
    from unittest.mock import MagicMock, patch

    event_id = str(uuid.uuid4())
    body = json.dumps({"id": 55544433, "created_at": "2024-03-01T12:00:00Z",
                       "total_price": "10.00", "currency": "USD",
                       "financial_status": "paid", "line_items": []}).encode()
    headers = _webhook_headers(body, store.shop_domain, "orders/create", event_id)

    with patch("app.workers.tasks.process_webhook_task") as mock_task:
        mock_task.delay = MagicMock()
        resp1 = await client.post("/webhooks/orders_create", content=body, headers=headers)
        resp2 = await client.post("/webhooks/orders_create", content=body, headers=headers)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # second call is a duplicate
    assert resp2.json().get("duplicate") is True
    # task dispatched only once
    assert mock_task.delay.call_count == 1
