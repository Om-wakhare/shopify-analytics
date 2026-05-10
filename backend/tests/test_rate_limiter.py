"""
Tests for the Shopify rate limiter / call-limit header parsing.
Pure unit tests — no HTTP calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.rate_limiter import _parse_call_limit, handle_rate_limit_response


class MockResponse:
    def __init__(self, status_code: int, headers: dict):
        self.status_code = status_code
        self.headers = headers


@pytest.mark.asyncio
async def test_no_rate_limit_returns_none():
    resp = MockResponse(200, {"X-Shopify-Shop-Api-Call-Limit": "5/40"})
    result = await handle_rate_limit_response(resp)
    assert result is None


@pytest.mark.asyncio
async def test_80_percent_bucket_triggers_slow_down():
    resp = MockResponse(200, {"X-Shopify-Shop-Api-Call-Limit": "33/40"})  # 82.5%
    result = await handle_rate_limit_response(resp)
    assert result == 0.5


@pytest.mark.asyncio
async def test_429_with_retry_after():
    resp = MockResponse(429, {"Retry-After": "4.0"})
    result = await handle_rate_limit_response(resp)
    assert result == 4.0


@pytest.mark.asyncio
async def test_429_without_retry_after_uses_default():
    resp = MockResponse(429, {})
    result = await handle_rate_limit_response(resp, retry_after_default=2.0)
    assert result == 2.0


def test_parse_call_limit_standard():
    used, max_ = _parse_call_limit("35/40")
    assert used == 35
    assert max_ == 40


def test_parse_call_limit_full():
    used, max_ = _parse_call_limit("40/40")
    assert used == 40
    assert max_ == 40


def test_parse_call_limit_empty_returns_defaults():
    used, max_ = _parse_call_limit("")
    assert used == 0
    assert max_ == 40
